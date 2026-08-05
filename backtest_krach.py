#!/usr/bin/env python3
"""Moteur de backtest — ATTENDRE LE KRACH POUR INVESTIR ? Pilote Finance, « Le Test » ep. 2.

QUATRE robots, un capital de depart, un horizon de 10 ans :
  A    (temoin) : investit TOUT immediatement (lump sum). C'est le temoin de l'ep. 1.
  B10  : reste en cash REMUNERE, investit tout au premier repli de -10 % sous le dernier plus-haut.
  B20  : idem a -20 % (le « vrai krach » officiel, bear market).
  B30  : idem a -30 %.

PROTOCOLE FIGE AVANT LE CALCUL (PF_LeTest_Ep2_Krach_PROTOCOLE.md + CONTRAT_backtest_krach.md) :
  - TOUTES les fenetres de depart sont publiees. Jamais une seule. Jamais celle qui nous arrange.
  - Le cash qui attend est REMUNERE au taux court de SA DEVISE. Jamais 0 % dans le scenario principal.
  - Si le repli n'arrive JAMAIS : B reste en cash jusqu'au bout. C'est un RESULTAT, pas une exclusion.
  - Le « dernier plus-haut » est AMBIGU dans le protocole -> les DEUX lectures sont calculees
    et publiees (reference="ath" et reference="depuis_t0"). On ne tranche pas a la place d'Aleksandar.
  - Aucun resultat n'autorise a conclure sur le FUTUR.

Ce module REUTILISE le moteur de l'ep. 1 (charge / _serie / ecris / run) : un seul endroit
ou une donnee peut manquer, un seul jeu de garde-fous.

v2 — 04/08/2026, apres gate code-reviewer (verdict STOP sur la v1). Corriges :
  BLOQUANT 1 : le scenario « achat M+1 » n'etait PAS comparable au principal (les fenetres qui
               declenchent a t0 passaient d'egalites a victoires/defaites). -> pct_signal_a_t0
               publie partout + bloc restreint aux fenetres ou on a VRAIMENT attendu.
  BLOQUANT 2 : le §7.2 bis AFFIRMAIT une cause (« la moyenne mensuelle lisse les krachs ») sans
               l'avoir mesuree. -> mesure_biais_seuil.py, et le texte ne dit plus rien qui ne
               vienne pas de resultats/biais_seuil.json. Si la mesure manque : STOP affiche.
  BLOQUANT 3 : renvoi trompeur vers biais_lissage.json (qui mesure autre chose). Corrige.
  BLOQUANT 4 : conclusions editoriales pre-ecrites en dur dans le generateur (« c'est trop pour
               etre du bruit de methode »). Supprimees : le generateur CONSTATE, il ne conclut pas.
  IMPORTANT  : garde isfinite/valeurs>0, CSV ecrits via ecris(), metriques d'attente nettoyees
               des declenchements a t0, scenario JP_depuis_t0 ajoute, scenarios degeneres
               signales AUTOMATIQUEMENT, controles IPC/contiguite dans signal_dans_la_donnee.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import backtest as ep1
from build_data import DonneeManquante, horodatage

DONNEES_REELLES = True  # regle code.md §6 : jamais de valeur inventee

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # panne #8 : cp1252 sous Windows

HERE = Path(__file__).resolve().parent
OUT = HERE / "resultats"          # cree dans main(), PAS a l'import

SEUILS_PROTOCOLE = (0.10, 0.20, 0.30)
REFERENCES = ("ath", "depuis_t0")
TOL = 1e-12                       # un repli exactement a -20,000000 % doit compter

# ---------------------------------------------------------------------------------------------
# CONTROLE EXTERNE (protocole §5) — definitions EXACTES relevees dans le PDF.
# Source : Benjamin Felix, PWL Capital, « Dollar Cost Averaging vs. Lump Sum Investing »,
# juin 2020. PDF lu INTEGRALEMENT (ep. 1 le 13/07/2026 ; re-verifie pour l'ep. 2 le 04/08/2026).
# https://pwlcapital.com/wp-content/uploads/2024/08/Dollar-Cost-Averaging-vs-Lump-Sum-Investing.pdf
#
# ⚠️ PWL et notre B20 NE REPONDENT PAS A LA MEME QUESTION. Ils sont COMPLEMENTAIRES :
#     PWL  : le krach a EU LIEU, j'ai le capital en main -> je place tout d'un coup, ou j'etale ?
#     B20  : le krach n'a PAS eu lieu -> j'attends en cash qu'il arrive, ou je place tout de suite ?
# Les presenter comme un « ecart a expliquer » serait une faute de lecture.
PWL = {
    "etude": "Benjamin Felix, PWL Capital, « Dollar Cost Averaging vs. Lump Sum Investing », juin 2020",
    "url": "https://pwlcapital.com/wp-content/uploads/2024/08/"
           "Dollar-Cost-Averaging-vs-Lump-Sum-Investing.pdf",
    "table": "Table 7, p. 9",
    "indice_us": "CRSP 1-10, RENDEMENT TOTAL (pas un indice de prix)",
    "periode_us": "01/1926 -> 03/2020",
    "cash": "bons du Tresor US 1 MOIS",
    "devise": "USD",
    "regle": "LSI (tout d'un coup) vs DCA sur 12 MOIS, sur des fenetres demarrant LE MOIS SUIVANT "
             "une chute >= 20 % « from the previous peak » (mesuree en donnees MENSUELLES)",
    "us_pct": 50.00,
    "moyenne_6_marches_pct": 53.66,
    "avantage_annualise_LSI_pts": 0.25,
    "attribution_PWL": "PWL attribue lui-meme la faiblesse du chiffre americain aux annees 1930, "
                       "incluses dans sa periode (depuis 1926) et ABSENTES de la notre (depuis 1934, "
                       "faute de taux court US avant cette date).",
}


def etiquette(seuil: float) -> str:
    """0.20 -> 'B20'. Format stable : un seuil non entier reste lisible (0.155 -> 'B15.5')."""
    return f"B{seuil * 100:g}"


def _valide(seuils, reference: str, delai_execution: int) -> tuple[float, ...]:
    if reference not in REFERENCES:
        raise ValueError(f"reference={reference!r} inconnue (attendues : {REFERENCES}).")
    if isinstance(delai_execution, bool) or not isinstance(delai_execution, (int, np.integer)):
        raise ValueError(f"delai_execution={delai_execution!r} : un ENTIER de mois est attendu.")
    if delai_execution < 0:
        raise ValueError(f"delai_execution={delai_execution} : on n'achete pas AVANT le signal.")
    seuils = tuple(sorted({float(s) for s in seuils}))
    if not seuils:
        raise ValueError("seuils vide : il faut au moins un seuil de repli.")
    for s in seuils:
        if not 0.0 < s < 1.0:
            raise ValueError(
                f"seuil={s} : une FRACTION dans ]0, 1[ est attendue (0.20 = -20 %). "
                "La coquille classique est d'ecrire 20 : elle doit exploser, pas produire "
                "'le krach n'arrive jamais'."
            )
    return seuils


def _serie_indice(df: pd.DataFrame, marche: str, real: bool) -> pd.Series:
    """La serie d'indice COMPLETE (aucune troncature) — base du plus-haut historique."""
    if marche not in ep1.MARCHES:
        raise ValueError(f"marche inconnu : {marche} (attendus : {list(ep1.MARCHES)})")
    col, _, _ = ep1.MARCHES[marche]
    serie = df[col].dropna()
    if serie.empty:
        raise DonneeManquante(f"Serie {marche} vide -> STOP.")
    if real:
        if marche != "US":
            raise ValueError(f"real=True refuse pour {marche} : on n'a que l'IPC AMERICAIN.")
        ipc = df["us_ipc"].reindex(serie.index)
        if ipc.isna().any():
            raise DonneeManquante("IPC manquant sur la serie complete -> STOP.")
        if (ipc <= 0.0).any():
            raise DonneeManquante("IPC <= 0 -> STOP (la deflation partirait a l'infini en silence).")
        serie = serie / ipc
    return serie


def _controle_valeurs(valeurs: np.ndarray, quoi: str) -> None:
    """Un indice a zero ou negatif produirait des `inf` PUBLIES sans qu'aucun NaN ne le signale."""
    if not np.isfinite(valeurs).all():
        raise DonneeManquante(f"{quoi} : valeur non finie (inf/NaN) -> STOP, jamais un inf a l'ecran.")
    if (valeurs <= 0.0).any():
        raise DonneeManquante(f"{quoi} : valeur <= 0 -> STOP (un indice ne vaut pas zero, "
                              "et un ratio sur zero part a l'infini en silence).")


def _plus_haut_historique(df: pd.DataFrame, marche: str, real: bool, index_travail) -> np.ndarray:
    """Plus-haut REEL, calcule sur TOUTE la serie disponible, pas seulement depuis `debut`.

    Tronquer avant le cummax remettrait le plus-haut a zero en 1934 : en 1934 le marche est
    tres loin sous son pic de 1929, et une fenetre 1934 croirait a tort le marche au sommet.
    ⚠️ Le plus-haut ne remonte pas plus loin que le DEBUT DE LA SERIE (1871 pour le S&P 500,
    mais 1949 pour le Nikkei et 1999 pour les series en euros) : c'est publie, pas cache.
    """
    pic = _serie_indice(df, marche, real).cummax().reindex(index_travail)
    if pic.isna().any():
        raise DonneeManquante("Plus-haut historique non calculable sur la periode de travail -> STOP.")
    return pic.to_numpy(dtype=float)


def run_krach(df: pd.DataFrame, marche: str = "US", horizon_months: int = 120,
              seuils=SEUILS_PROTOCOLE, cash_rate: str = "taux_court", real: bool = False,
              annual_fee: float = 0.0, debut: str | None = "1934-01",
              reference: str = "ath", delai_execution: int = 0) -> pd.DataFrame:
    """UNE LIGNE PAR FENETRE DE DEPART. Jamais un chiffre unique. Contrat : CONTRAT_backtest_krach.md."""
    seuils = _valide(seuils, reference, delai_execution)
    if not 0.0 <= annual_fee < 0.1:
        raise ValueError(f"annual_fee={annual_fee} : une FRACTION (0.003 = 0,3 %), jamais un pourcentage. "
                         "Borne a 10 %/an pour attraper la coquille classique (0.3 = 30 %/an).")
    if horizon_months < 1:
        raise ValueError(f"horizon_months={horizon_months} : au moins 1 mois.")
    if delai_execution >= horizon_months:
        raise ValueError(f"delai_execution={delai_execution} >= horizon={horizon_months} : "
                         "l'achat tomberait hors de la fenetre. Refuse plutot que rabote en silence.")

    # Memes garde-fous que l'ep. 1 : devise du cash, contiguite des mois, refus explicites.
    idx, cash = ep1._serie(df, marche, cash_rate, real, debut)
    n = len(idx)
    if n <= horizon_months:
        raise DonneeManquante(f"{n} mois disponibles, {horizon_months + 1} requis pour {marche}.")

    valeurs = idx.to_numpy(dtype=float)
    taux = cash.to_numpy(dtype=float)
    _controle_valeurs(valeurs, f"indice {marche}")
    if not np.isfinite(taux).all():
        raise DonneeManquante(f"Taux de cash non fini pour {marche} -> STOP.")

    pic_global = _plus_haut_historique(df, marche, real, idx.index) if reference == "ath" else None
    debut_du_plus_haut = str(_serie_indice(df, marche, real).index.min())
    f = (1.0 - annual_fee) ** (1.0 / 12.0) if annual_fee else 1.0
    h, m, lignes = horizon_months, idx.index, []

    for i in range(n - h):
        fin = i + h
        sous = valeurs[i:fin + 1]
        c = sous[-1] / sous                                   # facteur de croissance de i+k -> fin
        r = taux[i:fin + 1]
        # Le cash accumule le rendement du mois j pour chaque mois ECOULE (meme convention
        # que le DCA auto-finance de l'ep. 1, qui lit r[k+1]). r[0] n'est jamais consomme.
        cash_cum = np.concatenate(([1.0], np.cumprod(1.0 + r[1:])))

        pic = pic_global[i:fin + 1] if reference == "ath" else np.maximum.accumulate(sous)
        drawdown = sous / pic - 1.0

        ligne = {
            "depart": str(m[i]), "fin": str(m[fin]),
            "A_final": float(c[0]) * f ** h,
            "drawdown_t0_pct": float(drawdown[0]) * 100.0,
        }
        for s in seuils:
            nom = etiquette(s)
            touche = drawdown <= -s + TOL
            if touche.any():
                k_signal = int(np.argmax(touche))
                k_achat = min(k_signal + delai_execution, h)   # panne #10 : signal au dernier mois
                final = float(cash_cum[k_achat]) * float(c[k_achat]) * f ** (h - k_achat)
                ligne[f"{nom}_declenche"] = True
                ligne[f"{nom}_mois_attente"] = k_signal
            else:
                final = float(cash_cum[h])                     # attente infinie : cash jusqu'au bout
                ligne[f"{nom}_declenche"] = False
                ligne[f"{nom}_mois_attente"] = pd.NA           # jamais 0, jamais -1 : ABSENT
            ligne[f"{nom}_final"] = final
            ligne[f"{nom}_ecart_pct"] = (final / ligne["A_final"] - 1.0) * 100.0
        lignes.append(ligne)

    res = pd.DataFrame(lignes)
    chiffres = res.select_dtypes(include=[float]).to_numpy(dtype=float)
    if not np.isfinite(chiffres).all():
        raise DonneeManquante("Resultat non fini (inf/NaN) dans le tableau -> STOP avant publication.")
    res.attrs["params"] = dict(marche=marche, horizon_months=h, seuils=list(seuils), cash_rate=cash_rate,
                               real=real, annual_fee=annual_fee, debut=debut, reference=reference,
                               delai_execution=delai_execution, plus_haut_remonte_a=debut_du_plus_haut)
    return res


# Fenetres citees NOMMEMENT a l'ecran ou dans le script. Chacune doit ressortir d'un CSV, avec
# son RANG : une fenetre illustrative n'est pas un extreme, et l'appeler « le pire cas » est un bug
# anti-fiction. (Origine : le 04/08/2026, « depart 2016-06 » a ete presente comme le pire cas —
# les chiffres etaient justes, le qualificatif faux : c'est la 183e pire sur 990.)
FENETRES_CITEES = ("2016-06",)


def fenetres_citees(r: pd.DataFrame, seuil_nom: str = "B20", departs=FENETRES_CITEES) -> list[dict]:
    """Sort la ligne EXACTE de chaque fenetre citee, avec son rang — jamais un chiffre de memoire."""
    col, out = f"{seuil_nom}_ecart_pct", []
    for d in departs:
        ligne = r[r["depart"] == d]
        if ligne.empty:
            raise DonneeManquante(f"Fenetre citee {d} absente du scenario -> STOP : on ne cite pas "
                                  "a l'ecran une fenetre qui n'est pas dans le CSV.")
        x = ligne.iloc[0]
        declenche = bool(x[f"{seuil_nom}_declenche"])
        out.append({
            "depart": d, "fin": x["fin"],
            "A_multiple": round(float(x["A_final"]), 2),
            f"{seuil_nom}_multiple": round(float(x[f"{seuil_nom}_final"]), 2),
            "ecart_pct": round(float(x[col]), 2),
            "le_signal_est_venu": declenche,
            "rang_parmi_les_pires": int((r[col] < x[col]).sum()) + 1,
            "fenetres_totales": int(len(r)),
            "AVERTISSEMENT": "Fenetre ILLUSTRATIVE, choisie pour sa lisibilite (elle est recente). "
                             "Ce n'est PAS le pire cas : voir le rang. Le pire cas est au §7.3.",
        })
    return out


def _extreme(r: pd.DataFrame, col: str, sens: str) -> dict:
    i = r[col].idxmax() if sens == "max" else r[col].idxmin()
    return {"multiple": round(float(r.loc[i, col]), 2), "depart": r.loc[i, "depart"]}


def resume_krach(r: pd.DataFrame) -> dict:
    """Toutes les metriques du protocole §4. AUCUNE selection : on publie tout, meme ce qui contredit."""
    if r.empty:
        raise DonneeManquante("Aucune fenetre -> rien a resumer.")
    if "params" not in r.attrs:
        raise DonneeManquante("Tableau sans ses parametres (relu depuis un CSV ?) -> STOP : "
                              "un resume sans sa periode ni ses regles n'est pas publiable.")
    p = r.attrs["params"]
    out = {
        **p, "fenetres": len(r),
        "periode": f"{r['depart'].iloc[0]} -> {r['fin'].iloc[-1]}",
        "A_multiple_median": round(float(r["A_final"].median()), 2),
        "A_pire": _extreme(r, "A_final", "min"),
        "A_meilleur": _extreme(r, "A_final", "max"),
        "strategies": {},
    }
    for s in p["seuils"]:
        nom = etiquette(s)
        e, decl = r[f"{nom}_ecart_pct"], r[f"{nom}_declenche"]
        mois = pd.to_numeric(r[f"{nom}_mois_attente"], errors="raise")
        a_t0 = decl & (mois == 0)              # le signal etait DEJA la : on n'a pas attendu
        a_attendu = decl & (mois > 0)          # les seules fenetres ou l'attente existe vraiment
        attente = mois[a_attendu]
        bloc = {
            "pct_fenetres_ou_B_bat_A": round(float((e > TOL).mean() * 100), 1),
            "pct_fenetres_egalite_stricte": round(float((e.abs() <= TOL).mean() * 100), 1),
            "pct_fenetres_ou_A_bat_B": round(float((e < -TOL).mean() * 100), 1),
            "ecart_median_pct": round(float(e.median()), 2),
            "ecart_moyen_pct": round(float(e.mean()), 2),
            "pct_fenetres_ou_le_krach_n_arrive_JAMAIS": round(float((~decl).mean() * 100), 1),
            "pct_fenetres_ou_le_signal_est_DEJA_LA_a_t0": round(float(a_t0.mean() * 100), 1),
            "attente_moyenne_mois_quand_on_attend": round(float(attente.mean()), 1) if len(attente) else None,
            "attente_mediane_mois_quand_on_attend": round(float(attente.median()), 1) if len(attente) else None,
            "attente_max_mois": int(attente.max()) if len(attente) else None,
            "pire": _extreme(r, f"{nom}_final", "min"),
            "meilleur": _extreme(r, f"{nom}_final", "max"),
            "ecart_pire_pct": round(float(e.min()), 2),
            "ecart_meilleur_pct": round(float(e.max()), 2),
        }
        # Contrat §4.5 : ce que donne l'attente quand le signal est venu APRES t0.
        # ⚠️ NE PAS appeler ca « quand on a vraiment attendu » : les fenetres ou le krach n'arrive
        # JAMAIS sont celles ou le robot a attendu 10 ANS ENTIERS, et elles sont EXCLUES d'ici.
        # C'est le sous-ensemble le plus FLATTEUR pour B du document : il se cite avec son
        # denominateur et le rappel de ce qui en est sorti, jamais seul.
        bloc["quand_le_signal_est_venu_APRES_t0"] = (
            {
                "fenetres": int(a_attendu.sum()),
                "fenetres_totales": int(len(r)),
                "fenetres_exclues_car_signal_JAMAIS_venu": int((~decl).sum()),
                "fenetres_exclues_car_signal_DEJA_LA_a_t0": int(a_t0.sum()),
                "pct_ou_B_bat_A": round(float((e[a_attendu] > TOL).mean() * 100), 1),
                "ecart_median_pct": round(float(e[a_attendu].median()), 2),
                "A_NE_JAMAIS_CITER_SEUL": "Ce pourcentage EXCLUT les fenetres ou le krach n'est "
                    "jamais venu — c'est-a-dire celles ou le robot a attendu 10 ans en cash sans "
                    "jamais investir. Le citer sans son denominateur ni cette exclusion, c'est "
                    "transformer une condition en resultat.",
            }
            if int(a_attendu.sum())
            else {"fenetres": 0, "fenetres_totales": int(len(r)),
                  "fenetres_exclues_car_signal_JAMAIS_venu": int((~decl).sum()),
                  "fenetres_exclues_car_signal_DEJA_LA_a_t0": int(a_t0.sum())}
        )
        if bloc["pct_fenetres_egalite_stricte"] >= 99.95:
            bloc["AVERTISSEMENT_SCENARIO_DEGENERE"] = (
                "Toutes les fenetres declenchent a t0 : B n'attend JAMAIS, il EST A. Ce scenario "
                "ne mesure RIEN sur l'attente. Ne pas le mettre en regard des scenarios qui mesurent."
            )
        out["strategies"][nom] = bloc
    return out


def replique_pwl(df: pd.DataFrame, seuil: float = 0.20,
                 debut: str = "1934-01", horizon_months: int = 120) -> dict:
    """La replique FIDELE du test PWL — qui repond a une AUTRE question que notre B20.

    Regle PWL relevee dans le PDF (Table 7, p. 9) : fenetres demarrant LE MOIS SUIVANT une chute
    >= 20 % depuis le plus-haut precedent ; sur ces fenetres, LSI (tout d'un coup) vs DCA 12 mois.
    -> on applique EXACTEMENT cette regle a nos donnees, avec le TEST A de l'ep. 1.

    ⚠️ Ce n'est PAS une mesure concurrente de B20 : PWL suppose le krach DEJA ARRIVE et demande
    comment placer ; B20 suppose le krach PAS ENCORE ARRIVE et demande s'il faut l'attendre.
    """
    a = ep1.run(df, marche="US", horizon_months=horizon_months, dca_months=12,
                cash_rate="taux_court", real=False, debut=debut)

    # Repli mesure sur TOUTE la serie (le plus-haut precedent peut etre anterieur a `debut`),
    # puis DECALE d'un mois : PWL fait demarrer la fenetre LE MOIS SUIVANT la chute constatee.
    serie = _serie_indice(df, "US", real=False)
    dd = (serie / serie.cummax() - 1.0) * 100.0
    mois_precedent = pd.PeriodIndex(a["depart"], freq="M") - 1
    dd_veille = dd.reindex(mois_precedent).to_numpy(dtype=float)
    # La TOUTE PREMIERE fenetre de la serie n'a legitimement pas de mois d'avant : elle est
    # INELIGIBLE (on ne peut pas constater une chute avant le debut des donnees), pas fatale.
    # En revanche un trou AILLEURS est une donnee manquante -> STOP.
    absents = np.isnan(dd_veille)
    if absents.any():
        premier = mois_precedent[0] < serie.index.min()
        if not (premier and absents.sum() == 1 and absents[0]):
            manquants = [str(m) for m, x in zip(mois_precedent, absents, strict=True) if x][:5]
            raise DonneeManquante(f"Repli du mois precedent introuvable pour {manquants} -> STOP "
                                  "(la regle PWL exige le mois AVANT le depart).")

    a = a.assign(repli_du_mois_precedent_pct=dd_veille)
    sous = a[a["repli_du_mois_precedent_pct"] <= -seuil * 100.0 + TOL]
    if sous.empty:
        raise DonneeManquante(f"Aucune fenetre demarrant apres un repli de -{seuil * 100:g} % -> "
                              "replique PWL impossible.")
    nous = round(float((sous["A_ecart_pct"] > 0).mean() * 100), 1)
    apres_1950, avant_1950 = sous[sous["depart"] >= "1950-01"], sous[sous["depart"] < "1950-01"]

    # Des fenetres consecutives eligibles decrivent le MEME krach a un mois d'intervalle : 181
    # fenetres ne sont pas 181 observations independantes. On compte les BLOCS CONTIGUS.
    # ⚠️ L'etat du mois AVANT la premiere fenetre compte : en 1933-12 le marche est a -58 %, donc
    # la fenetre 1934-01 est la QUEUE du krach de 1929, pas le debut d'un nouvel episode.
    # Demarrer le calcul a False inventerait un bloc — et il gonflerait le chiffre dans le sens
    # qui RASSURE, alors que cette metrique sert precisement a alerter.
    eligible = (a["repli_du_mois_precedent_pct"] <= -seuil * 100.0 + TOL).to_numpy()
    avant = dd.reindex([mois_precedent[0] - 1]).iloc[0]
    deja_en_krach = bool(pd.notna(avant) and avant <= -seuil * 100.0 + TOL)
    blocs = int(np.sum(eligible & ~np.concatenate(([deja_en_krach], eligible[:-1]))))
    return {
        "AVERTISSEMENT_LECTURE": "PWL et notre B20 sont COMPLEMENTAIRES, pas concurrents. PWL : "
            "« le krach a eu lieu, comment je place ? ». B20 : « le krach n'a pas eu lieu, "
            "faut-il l'attendre ? ». Presenter l'un comme un ecart a l'autre serait une FAUTE.",
        "ce_que_PWL_mesure": "Fenetres demarrant LE MOIS SUIVANT une chute >= 20 % depuis le "
                             "plus-haut precedent : le tout d'un coup bat-il le DCA sur 12 mois ?",
        "PWL": PWL,
        "notre_replique_pct": nous,
        "ecart_points": round(nous - PWL["us_pct"], 1),
        "fenetres_retenues": int(len(sous)),
        "blocs_de_fenetres_contigus": blocs,
        "CE_QUE_LES_BLOCS_NE_SONT_PAS": "Un bloc = une suite de fenetres eligibles qui se touchent. "
            "Ce n'est PAS un bear market distinct : un meme krach se recoupe en plusieurs blocs des "
            "que l'indice repasse un mois au-dessus du seuil (1937, 1987-88 et 2004 sont dans ce cas). "
            "Le nombre de krachs REELLEMENT distincts est donc encore PLUS PETIT que ce chiffre. "
            "L'erreur va dans le sens qui rassure — on la declare.",
        "fenetres_totales": int(len(a)),
        "meme_test_SANS_condition_de_repli_pct": round(float((a["A_ecart_pct"] > 0).mean() * 100), 1),
        "pourquoi_l_ecart": {
            "verdict": "ECART SIGNALE, PAS EXPLIQUE. La seule hypothese disponible est celle que PWL "
                       "avance lui-meme (ses annees 1926-1933) — et nous NE POUVONS PAS la tester.",
            "hypothese_de_PWL": PWL["attribution_PWL"],
            "notre_periode_commence_en": str(a["depart"].iloc[0]),
            "CE_QU_ON_NE_PEUT_PAS_FAIRE": "Rejouer PWL sur 1926-1933 chez nous : le taux court US "
                "(FRED TB3MS) commence en 1934-01. Sans lui, le cash du DCA serait a 0 %, ce qui "
                "FAVORISE mecaniquement le tout d'un coup — on ne reconstituerait donc pas le "
                "chiffre de PWL, on en fabriquerait un autre. On s'arrete et on le dit.",
            "diagnostic_decoupage_ex_post": {
                "⛔_AVERTISSEMENT": "Chiffres de DIAGNOSTIC pour le fact-check. INTERDITS A L'ECRAN "
                    "et INTERDITS dans SECTION_7.md : decouper la periode APRES avoir vu le "
                    "resultat, c'est exactement ce que le protocole interdit de publier.",
                "departs_1934_1949_pct":
                    round(float((avant_1950["A_ecart_pct"] > 0).mean() * 100), 1) if len(avant_1950) else None,
                "fenetres_1934_1949": int(len(avant_1950)),
                "departs_1950_et_apres_pct":
                    round(float((apres_1950["A_ecart_pct"] > 0).mean() * 100), 1) if len(apres_1950) else None,
                "fenetres_1950_et_apres": int(len(apres_1950)),
                "CE_QUE_CA_DIT_VRAIMENT": "Nos fenetres les plus ANCIENNES (1934-1949) sont les MOINS "
                    "favorables au tout d'un coup, pas les plus. L'intuition « nos fenetres post-krach "
                    "sont des sorties de crise gagnantes » est donc FAUSSE sur nos donnees : elle a ete "
                    "ecrite puis retiree le 05/08/2026 apres verification. Ce diagnostic ne dit PAS "
                    "d'ou vient l'ecart avec PWL — il dit seulement que cette explication-la ne tient pas.",
            },
        },
        "differences_declarees": [
            "Indice : S&P 500 dividendes reinvestis (Shiller) vs CRSP 1-10 (PWL). "
            "⚠️ LES DEUX sont des indices de RENDEMENT TOTAL : l'ecart ne vient PAS d'un choix "
            "prix vs dividendes reinvestis.",
            f"Periode : {a['depart'].iloc[0]} -> {a['fin'].iloc[-1]} vs {PWL['periode_us']} (PWL). "
            "C'est la difference principale : les annees 1930 sont chez eux, pas chez nous.",
            "Granularite : nos prix Shiller sont des MOYENNES MENSUELLES ; la chute de 20 % de PWL "
            "est elle aussi mesuree en donnees mensuelles.",
            f"Cash : bon du Tresor 3 mois (TB3MS) chez nous, {PWL['cash']} chez PWL.",
        ],
    }


def signal_dans_la_donnee(df: pd.DataFrame, marche: str = "US", real: bool = False,
                          debut: str | None = "1934-01", seuils=SEUILS_PROTOCOLE) -> dict:
    """OU sont les signaux DANS LA DONNEE ELLE-MEME (independamment des fenetres) ?

    Sert a repondre a la question que le Statisticien posera : « ou sont passes les krachs
    de 2020 et 2022 ? ». Ce module COMPTE. Il n'explique pas : l'explication est mesuree
    separement par mesure_biais_seuil.py (granularite vs rendement total).
    """
    seuils = _valide(seuils, "ath", 0)
    serie = _serie_indice(df, marche, real)
    attendu = pd.period_range(serie.index.min(), serie.index.max(), freq="M")
    if not serie.index.equals(attendu):
        manquants = attendu.difference(serie.index)[:5].tolist()
        raise DonneeManquante(f"Mois manquants dans {marche} : {manquants} -> STOP (meme exigence "
                              "que run_krach : les deux tableaux publies doivent parler des memes mois).")
    _controle_valeurs(serie.to_numpy(dtype=float), f"indice {marche}")

    dd = (serie / serie.cummax() - 1.0) * 100.0     # plus-haut historique reel, toute la serie
    if debut:
        dd = dd.loc[dd.index >= pd.Period(debut, freq="M")]
    if dd.empty:
        raise DonneeManquante(f"Aucun mois pour {marche} apres {debut} -> STOP.")

    out = {"marche": marche, "periode": f"{dd.index.min()} -> {dd.index.max()}",
           "plus_haut_remonte_a": str(serie.index.min()),
           "mois_observes": int(len(dd)), "seuils": {}}
    dernier_20 = None
    for s in seuils:
        nom, sous = etiquette(s), dd <= -s * 100.0 + TOL
        out["seuils"][nom] = {
            "mois_sous_le_seuil": int(sous.sum()),
            "pct_du_temps_sous_le_seuil": round(float(sous.mean() * 100), 1),
            "dernier_mois_sous_le_seuil": str(dd.index[sous][-1]) if sous.any() else None,
        }
        if s == 0.20 and sous.any():
            dernier_20 = dd.index[sous][-1]

    if dernier_20 is not None:
        depuis = dd.loc[dd.index > dernier_20]
        if not depuis.empty:
            par_an = depuis.groupby(depuis.index.year).min().sort_values()
            out["depuis_le_dernier_signal_-20pct"] = {
                "dernier_signal": str(dernier_20),
                "mois_ecoules_sans_signal": int(len(depuis)),
                "pire_repli_mensuel_depuis": round(float(depuis.min()), 2),
                "date_du_pire_repli": str(depuis.idxmin()),
                "3_pires_annees": [{"annee": int(a), "pire_repli_pct": round(float(v), 2)}
                                   for a, v in par_an.head(3).items()],
            }
    return out


# ARBITRAGE ALEKSANDAR, 04/08/2026 : la lecture PRINCIPALE du « dernier plus-haut » est
# « observe DEPUIS t0 » (l'investisseur regarde le marche a partir du jour ou il a l'argent).
# La lecture « plus-haut historique reel » reste PUBLIEE, en comparaison. Les deux restent au §7.
CLE_PRINCIPAL = "US_principal"
CLE_COMPARAISON_ATH = "US_plushaut_historique"

SCENARIOS = [
    # ---- PRINCIPAL : USA, 1934-01 -> 2026, cash remunere, plus-haut OBSERVE DEPUIS t0
    dict(cle=CLE_PRINCIPAL, marche="US", cash_rate="taux_court", debut="1934-01",
         reference="depuis_t0"),
    # ---- COMPARAISON : meme periode, meme regle, SEULE change la definition du plus-haut
    dict(cle=CLE_COMPARAISON_ATH, marche="US", cash_rate="taux_court", debut="1934-01",
         reference="ath"),
    # ---- Le signal est-il trop gentil ? achat le mois SUIVANT le signal (lecture principale)
    dict(cle="US_achat_M1", marche="US", cash_rate="taux_court", debut="1934-01",
         reference="depuis_t0", delai_execution=1),
    # ---- Combien pese la remuneration du cash ? (meme periode, cash a 0 %)
    dict(cle="US_cash_zero", marche="US", cash_rate="zero", debut="1934-01", reference="depuis_t0"),
    # ---- Vue LONGUE 1871+ : cash a 0 % obligatoire (aucun taux court avant 1934).
    #      PERIODE DIFFERENTE -> a ne JAMAIS comparer aux lignes ci-dessus.
    dict(cle="US_long_1871", marche="US", cash_rate="zero", debut=None, reference="depuis_t0"),
    # ---- L'investisseur en EUROS (1999+ : l'euro n'existe pas avant)
    dict(cle="US_EUR", marche="US_EUR", cash_rate="taux_court", debut=None, reference="depuis_t0"),
    # ---- LE TEMOIN JAPONAIS (biais de survie). Cash a 0 % : pas de taux court JPY avant 2002
    #      -> ca DEFAVORISE les robots B : leur chiffre japonais est un PLANCHER.
    dict(cle="JP", marche="JP", cash_rate="zero", debut=None, reference="depuis_t0"),
    # ---- Japon vu avec le plus-haut HISTORIQUE : le Nikkei reste sous son pic de 1989 pendant
    #      34 ans -> le robot n'attend jamais, il investit a t0. Publie pour montrer justement ca.
    dict(cle="JP_plushaut_historique", marche="JP", cash_rate="zero", debut=None, reference="ath"),
    # ---- Japon avec cash remunere : possible seulement sur 2002+ (la serie FRED commence la)
    dict(cle="JP_cash_remunere_2002", marche="JP", cash_rate="taux_court", debut=None,
         reference="depuis_t0"),
]

A_LIRE = {
    "le_protocole_etait_FIGE_avant_le_calcul": "Periode, regles et metriques sont verrouillees dans "
        "PF_LeTest_Ep2_Krach_PROTOCOLE.md AVANT que ce script tourne. Toutes les fenetres sont "
        "publiees, jamais une selection.",
    "PWL_et_B20_sont_COMPLEMENTAIRES_pas_concurrents": "PWL (Table 7 p. 9, 50,00 % aux USA) mesure : "
        "le krach A DEJA EU LIEU, je place tout d'un coup ou j'etale sur 12 mois ? Notre B20 mesure : "
        "le krach N'A PAS ENCORE EU LIEU, faut-il l'attendre en cash ? Ce sont DEUX QUESTIONS "
        "DIFFERENTES. Presenter l'une comme un 'ecart' a l'autre serait une faute de lecture. "
        "Fact-check du 04/08/2026 : les deux etudes utilisent des indices de RENDEMENT TOTAL — "
        "l'hypothese d'un ecart prix/dividendes est ECARTEE ; l'ecart vient de la PERIODE (PWL "
        "inclut les annees 1930, pas nous) et de l'INDICE (CRSP 1-10 vs S&P 500).",
    "le_plus_haut_ARBITRE_le_04_08_2026": "Le protocole ne disait pas si le plus-haut pouvait etre "
        "anterieur a t0. ARBITRAGE ALEKSANDAR : la lecture PRINCIPALE est 'depuis_t0' (le plus-haut "
        "observe depuis que l'investisseur a l'argent). La lecture 'ath' (plus-haut historique reel) "
        "reste PUBLIEE en comparaison — scenario US_plushaut_historique. Elles ne donnent PAS le meme "
        "chiffre : citer l'un sans dire lequel, c'est cacher la moitie du resultat.",
    "le_plus_haut_ne_remonte_pas_avant_le_debut_de_la_SERIE": "En mode 'ath', le plus-haut est le "
        "maximum depuis le PREMIER MOIS DISPONIBLE de la serie : 1871 pour le S&P 500, mais 1949 "
        "pour le Nikkei et 1999 pour les series en euros (champ 'plus_haut_remonte_a' de chaque "
        "scenario). Les toutes premieres fenetres de ces series voient donc un plus-haut tronque.",
    "les_egalites_ne_sont_PAS_des_defaites_EN_LECTURE_ath": "⚠️ NE CONCERNE PAS LE SCENARIO "
        "PRINCIPAL (lecture depuis_t0, ou il n'y a aucune egalite). En lecture 'ath', une fenetre "
        "qui demarre DEJA sous le seuil fait investir B des t0 : B est alors STRICTEMENT identique "
        "a A. Ces fenetres sont "
        "comptees a part (pct_fenetres_egalite_stricte). Les noyer dans 'A bat B' gonflerait "
        "artificiellement le score du temoin.",
    "comparer_achat_M1_au_principal_EST_LICITE_en_lecture_depuis_t0": "En lecture 'depuis_t0' "
        "(le scenario principal) aucune fenetre ne declenche a t0 : la comparaison brute entre "
        "US_principal et US_achat_M1 EST valide, le delai d'execution est la seule chose qui change. "
        "⚠️ En lecture 'ath' en revanche elle ne l'est PAS : les fenetres qui declenchaient a t0 "
        "cessent d'etre des egalites strictes et deviennent des victoires ou des defaites, donc le "
        "taux brut bouge pour une raison COMPTABLE. Pour ces scenarios-la, passer par le bloc "
        "'quand_le_signal_est_venu_APRES_t0'.",
    "le_repli_est_mesure_en_RENDEMENT_TOTAL_pas_en_prix": "Le protocole §3 fixe le S&P 500 dividendes "
        "REINVESTIS : le repli des robots B est donc calcule sur le rendement total, pas sur l'indice "
        "de prix dont parlent les medias quand ils annoncent un 'bear market'. Les dividendes "
        "reinvestis rabotent mecaniquement le repli. Effet MESURE (pas suppose) : biais_seuil.json.",
    "granularite_mensuelle": "Les prix Shiller sont des MOYENNES MENSUELLES de cours quotidiens : "
        "elles LISSENT les krachs. Effet MESURE sur le DECLENCHEMENT D'UN SEUIL : "
        "resultats/biais_seuil.json (section A, sur le Nikkei quotidien). "
        "⚠️ Ne PAS confondre avec resultats/biais_lissage.json (ep. 1), qui mesure l'effet du "
        "lissage sur l'ecart lump/DCA — une autre question.",
    "acheter_le_mois_du_signal_FLATTE_B": "Le scenario principal fait acheter B a la valeur du mois "
        "ou le repli est constate. Le scenario 'US_achat_M1' mesure un mois de reaction en plus — "
        "a lire via le bloc 'quand_le_signal_est_venu_APRES_t0', pas via le taux brut.",
    "le_Japon_avec_cash_a_0_est_un_PLANCHER_pour_B": "Le taux court japonais (FRED) commence en 2002 "
        "et ne couvre pas le krach de 1990 : le scenario japonais long fait donc attendre B a 0 %. "
        "Ca DEFAVORISE B. Son chiffre japonais est un plancher, pas une mesure exacte.",
    "le_Nikkei_est_SANS_DIVIDENDES": "FRED NIKKEI225 = PRIX SEUL. Le Japon est donc sous-estime pour "
        "TOUTES les strategies (A comme B). A dire a l'ecran.",
    "certains_scenarios_ne_mesurent_RIEN_EN_LECTURE_ath": "⚠️ NE CONCERNE QUE LES SCENARIOS EN LECTURE 'ath'. Quand 100 % des fenetres declenchent a t0 (le Nikkei "
        "post-2002 est sous son pic de 1989 pendant des decennies), B n'attend jamais : il EST A. "
        "Ces scenarios portent un champ 'AVERTISSEMENT_SCENARIO_DEGENERE'. Les aligner dans un "
        "tableau a cote de scenarios qui mesurent quelque chose serait trompeur.",
    "periodes_non_comparables": "Ne JAMAIS comparer deux scenarios dont le champ 'periode' differe "
        "(US_long_1871, US_EUR, JP, JP_cash_remunere_2002) : on comparerait des donnees, pas une hypothese.",
    "fenetres_chevauchantes": "Des fenetres de 10 ans a pas mensuel se recouvrent : elles ne sont PAS "
        "des observations independantes. Aucun test de significativite, aucune p-value n'est publiee. "
        "On DECRIT le passe, on n'infere rien.",
    "ecart_pct_n_est_PAS_une_perte": "L'ecart est RELATIF entre DEUX STRATEGIES. '-30 %' ne veut pas "
        "dire 'on perd 30 %' : ca veut dire que B finit 30 % sous A. A dire autrement a l'ecran.",
    "aucune_conclusion_sur_le_FUTUR": "Un backtest MESURE LE PASSE. Il ne predit RIEN. Interdiction "
        "de conclure « donc fais X » (protocole §6, compliance-finance v2).",
}


def _ligne_tableau(cle: str, res: dict, nom: str, periode_principal: str | None = None) -> str:
    b = res["strategies"][nom]
    att = b["attente_moyenne_mois_quand_on_attend"]
    degenere = " ⚠️" if "AVERTISSEMENT_SCENARIO_DEGENERE" in b else ""
    # Une periode differente = un scenario NON COMPARABLE au principal. Le marquer dans le tableau,
    # pas seulement en note : c'est la ligne qu'on citera de travers (US_EUR fait gagner l'attente).
    if periode_principal and res["periode"] != periode_principal:
        degenere += " 🕒"
    return (f"| {cle}{degenere} | {nom} | {b['pct_fenetres_ou_B_bat_A']} % | "
            f"{b['pct_fenetres_egalite_stricte']} % | {b['ecart_median_pct']:+.2f} % | "
            f"{b['pct_fenetres_ou_le_krach_n_arrive_JAMAIS']} % | {att if att is not None else '—'} | "
            f"{b['ecart_pire_pct']:+.2f} % | {b['ecart_meilleur_pct']:+.2f} % |")


def _encadre_2020_2022(biais: dict) -> list[str]:
    """L'encadre GRANULARITE destine a l'ECRAN (arbitrage Aleksandar : c'est un moment fort).

    Chaque chiffre vient d'un fichier de mesure. Le quotidien vient de FRED SP500 — il est
    MESURE, pas cite de memoire : c'est la regle anti-fiction, y compris pour un chiffre connu.
    """
    q = biais.get("C_sp500_quotidien")
    b = biais["B_prix_contre_rendement_total"]
    if not q:
        return ["", "⛔ **STOP — le S&P 500 quotidien n'a pas été mesuré** : relancer "
                    "`python mesure_biais_seuil.py`. Aucun chiffre journalier ne sera écrit "
                    "sans sa source.", ""]
    par_an_q = {x["annee"]: x for x in q["pire_repli_par_annee"]}
    par_an_m = {x["annee"]: x for x in b["pire_repli_par_annee_10_dernieres"]}
    lignes = [
        "",
        "---",
        "",
        "#### 📺 ENCADRÉ « GRANULARITÉ » — À DIRE À L'ÉCRAN",
        "",
        "*Arbitrage Aleksandar du 04/08/2026 : protocole INCHANGÉ, et ces chiffres sont dits, "
        "pas enterrés en note de bas de page.*",
        "",
        "| Krach | en cours **quotidiens** | en **moyenne mensuelle** (prix) | en **moyenne mensuelle** "
        "(dividendes réinvestis) | notre robot le voit ? |",
        "|---|---|---|---|---|",
    ]
    for an in (2020, 2022):
        qq, mm = par_an_q.get(an), par_an_m.get(an)
        if not qq or not mm:
            continue
        # Pas de gras DANS la variable : le f-string en rajoute et Markdown affiche ****NON****.
        vu_prix = "OUI" if mm["prix_seul_pct"] <= -20.0 else "NON"
        vu_tr = "OUI" if mm["rendement_total_pct"] <= -20.0 else "NON"
        lignes.append(f"| **{an}** | **{qq['pire_repli_quotidien_pct']:.2f} %** "
                      f"({qq['date']}) | {mm['prix_seul_pct']:.2f} % → {vu_prix} | "
                      f"{mm['rendement_total_pct']:.2f} % → {vu_tr} | **{vu_tr}** |")
    lignes += [
        "",
        f"> **Le Covid a fait −{abs(par_an_q[2020]['pire_repli_quotidien_pct']):.2f} % en cours de "
        f"séance. Dans notre donnée mensuelle, il vaut "
        f"−{abs(par_an_m[2020]['rendement_total_pct']):.2f} % : il n'a jamais atteint les −20 %. "
        "Notre robot « j'attends le krach » ne l'a même pas vu passer.**",
        "",
        f"Source du quotidien : {q['source']} ({q['url']}), {q['periode']}, {q['seances']} séances. "
        f"{q['LIMITE_prix_seul']} {q['LIMITE_serie_glissante']}",
        "",
        "---",
    ]
    return lignes


def _bloc_granularite(signal: dict, biais: dict | None) -> list[str]:
    """§7.2 bis — le constat brut, PUIS l'explication SEULEMENT si elle a ete mesuree."""
    lignes = [
        "### 7.2 bis — 🚨 OÙ SONT PASSÉS 2020 ET 2022 ? (tranché : protocole inchangé, chiffres dits)",
        "",
        f"Sur {signal['periode']} ({signal['mois_observes']} mois), le S&P 500 dividendes réinvestis "
        f"a passé, sous son plus-haut historique (calculé depuis {signal['plus_haut_remonte_a']}) :",
        "",
        "> ℹ️ **Ce tableau-ci est en lecture « plus-haut historique »**, pas en lecture « depuis t0 » "
        "(celle du §7.2). C'est volontaire : la question posée ici est « le marché a-t-il été 20 % "
        "sous son sommet ? », indépendamment de la date d'arrivée de l'investisseur. Le sens de "
        "l'écart est **conservateur** : un plus-haut observé depuis t0 est toujours ≤ le plus-haut "
        "historique, donc **en lecture principale les signaux sont encore plus rares** que ce que "
        "montre ce tableau.",
        "",
        "| Seuil | mois passés sous le seuil | % du temps | dernier mois sous le seuil |",
        "|---|---|---|---|",
    ]
    for nom, b in signal["seuils"].items():
        lignes.append(f"| {nom} | {b['mois_sous_le_seuil']} | {b['pct_du_temps_sous_le_seuil']} % | "
                      f"**{b['dernier_mois_sous_le_seuil'] or '—'}** |")
    d = signal.get("depuis_le_dernier_signal_-20pct")
    if d:
        pires = " · ".join(f"**{a['annee']} : {a['pire_repli_pct']:.2f} %**" for a in d["3_pires_annees"])
        lignes += [
            "",
            f"> ⚠️ **Le seuil des −20 % n'a plus été atteint depuis {d['dernier_signal']}** — soit "
            f"**{d['mois_ecoules_sans_signal']} mois** de suite. Sur toute cette période, le pire repli "
            f"mensuel mesuré est **{d['pire_repli_mensuel_depuis']:.2f} %** ({d['date_du_pire_repli']}). "
            f"Les trois pires années depuis : {pires}.",
        ]
    if biais is None:
        lignes += [
            "",
            "⛔ **STOP — mesure manquante.** L'explication de ce constat n'a pas été calculée : "
            "lancer `python mesure_biais_seuil.py`, puis relancer `backtest_krach.py`. "
            "**Écrire ici une cause non mesurée serait un bug anti-fiction.**",
            "",
        ]
        return lignes

    a, b = biais["A_granularite"], biais["B_prix_contre_rendement_total"]
    if "B20" not in a["quotidien_LA_VERITE"] or "B20" not in b["prix_seul"]:
        raise DonneeManquante("biais_seuil.json ne contient pas le seuil B20 -> STOP : le §7.2 bis "
                              "porte sur le seuil du protocole, pas sur un autre.")
    lignes += [
        "",
        f"**Pourquoi ? Deux suspects, MESURÉS séparément** (`mesure_biais_seuil.py` → "
        f"`resultats/biais_seuil.json`, généré le **{biais['genere_le']}**) — aucune cause n'est "
        "affirmée sans son chiffre :",
        "",
        f"**Suspect 1 — les dividendes réinvestis.** Mêmes mois, même règle, {b['periode']} : "
        f"seule change la définition de l'indice.",
        "",
        "| Indice | mois passés sous −20 % | % du temps | dernier mois sous −20 % |",
        "|---|---|---|---|",
        f"| **Prix seul** (celui dont parlent les médias) | {b['prix_seul']['B20']['mois_sous_le_seuil']} | "
        f"{b['prix_seul']['B20']['pct_du_temps']} % | **{b['prix_seul']['B20']['dernier_mois_sous_le_seuil']}** |",
        f"| **Rendement total** (ce que le protocole §3 impose) | "
        f"{b['rendement_total_CE_QUE_LE_MOTEUR_UTILISE']['B20']['mois_sous_le_seuil']} | "
        f"{b['rendement_total_CE_QUE_LE_MOTEUR_UTILISE']['B20']['pct_du_temps']} % | "
        f"**{b['rendement_total_CE_QUE_LE_MOTEUR_UTILISE']['B20']['dernier_mois_sous_le_seuil']}** |",
        "",
        "Pire repli de chaque année, dans les deux mondes :",
        "",
        "| Année | prix seul | rendement total |",
        "|---|---|---|",
    ]
    lignes += [f"| {x['annee']} | {x['prix_seul_pct']:.2f} % | {x['rendement_total_pct']:.2f} % |"
               for x in b["pire_repli_par_annee_10_dernieres"]]
    lignes += [
        "",
        f"**Suspect 2 — la granularité mensuelle.** Mesurée sur le Nikkei ({a['periode']}), seul marché "
        "dont on a le quotidien sur longue période. Même marché, même règle, seule change la finesse.",
        "",
        "⚠️ *Les deux colonnes ne comptent pas la même chose : en **quotidien**, un mois compte dès "
        "qu'**un seul jour** passe sous le seuil ; en **mensuel**, il compte si **la valeur du mois** "
        "est sous le seuil. C'est justement la comparaison qui nous intéresse — un robot qui "
        "surveillerait en quotidien verrait-il des signaux que le nôtre ne voit pas ?*",
        "",
        "| Granularité | mois où le signal −20 % existe | part des mois | dernier mois avec signal |",
        "|---|---|---|---|",
        f"| **Quotidien** (la vérité) | {a['quotidien_LA_VERITE']['B20']['mois_sous_le_seuil']} | "
        f"{a['quotidien_LA_VERITE']['B20']['pct_du_temps']} % | "
        f"{a['quotidien_LA_VERITE']['B20']['dernier_mois_sous_le_seuil']} |",
        f"| Fin de mois | {a['fin_de_mois']['B20']['mois_sous_le_seuil']} | "
        f"{a['fin_de_mois']['B20']['pct_du_temps']} % | "
        f"{a['fin_de_mois']['B20']['dernier_mois_sous_le_seuil']} |",
        f"| **Moyenne du mois** (méthode Shiller, la nôtre) | "
        f"{a['moyenne_du_mois_METHODE_SHILLER']['B20']['mois_sous_le_seuil']} | "
        f"{a['moyenne_du_mois_METHODE_SHILLER']['B20']['pct_du_temps']} % | "
        f"{a['moyenne_du_mois_METHODE_SHILLER']['B20']['dernier_mois_sous_le_seuil']} |",
        "",
        f"➡️ **La moyenne mensuelle rate {a['mois_rates_par_la_moyenne_du_mois']['B20']} mois de signal "
        f"sur les {a['quotidien_LA_VERITE']['B20']['mois_sous_le_seuil']} que voit le quotidien.** "
        "L'effet existe, il est réel — mais il est plus petit que celui du suspect 1.",
        "",
        f"*{a['LIMITE']}*",
        "",
    ]
    lignes += _encadre_2020_2022(biais)
    lignes += [
        "",
        "✅ **DÉCISION PRISE (Aleksandar, 04/08/2026) : PROTOCOLE INCHANGÉ.** S&P 500 dividendes "
        "réinvestis et granularité mensuelle restent tels quels — les deux étaient déjà déclarés "
        "au §3. En contrepartie, **ces chiffres sont dits à l'écran** : voir l'encadré ci-dessous. "
        "Aucune règle, aucune période, aucune métrique n'a été modifiée après le calcul.",
        "",
    ]
    return lignes


def _bloc_fenetres_citees(principal: dict) -> list[str]:
    """§7.3 bis — les fenetres nommees a l'ecran, avec leur RANG. Tracabilite d'un chiffre cite."""
    citees = principal.get("fenetres_citees")
    if not citees:
        return []
    lignes = [
        "### 7.3 bis — Les fenêtres citées nommément (traçabilité)",
        "",
        "> 🧾 **Ajouté le 05/08/2026.** Toute fenêtre nommée à l'écran ou dans le script doit "
        "ressortir d'un CSV **avec son rang**. Une fenêtre illustrative n'est pas un extrême, et "
        "l'appeler « le pire cas » est un bug anti-fiction — c'est arrivé une fois, ça ne se "
        "reproduit pas en silence.",
        "",
        "| Départ | Fin | Témoin A | B20 | écart | le krach est-il venu ? | rang parmi les pires |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in citees:
        lignes.append(
            f"| **{c['depart']}** | {c['fin']} | ×{c['A_multiple']} | ×{c['B20_multiple']} | "
            f"**{c['ecart_pct']:+.2f} %** | {'oui' if c['le_signal_est_venu'] else '**NON, jamais**'} | "
            f"{c['rang_parmi_les_pires']}ᵉ / {c['fenetres_totales']} |"
        )
    pire = principal["strategies"]["B20"]
    lignes += [
        "",
        f"⚠️ **Ces fenêtres sont ILLUSTRATIVES, pas extrêmes.** Le vrai pire cas de B20 est le "
        f"départ **{pire['pire']['depart']}** (×{pire['pire']['multiple']}, écart "
        f"{pire['ecart_pire_pct']:+.2f} %) — §7.3. Citer une fenêtre illustrative comme « le pire "
        "cas » serait faux.",
        "",
    ]
    return lignes


def section_7(tous: list[dict], pwl: dict, signal: dict, biais: dict | None, quand: str) -> str:
    """Le tableau du §7 du protocole, GENERE. Aucun chiffre n'est jamais tape a la main.

    ⚠️ Ce generateur CONSTATE. Il ne conclut pas : les conclusions appartiennent au fact-check
    et au panel, apres coup. Une phrase de conclusion ecrite ICI serait ecrite AVANT le calcul.
    """
    principal = next(t for t in tous if t["cle"] == CLE_PRINCIPAL)
    compar = next((t for t in tous if t["cle"] == CLE_COMPARAISON_ATH), None)
    lignes = [
        "## 7. RÉSULTATS (remplis PAR LE MOTEUR — `backtest_krach.py`, DONNEES_REELLES=True)",
        "",
        f"> Généré le **{quand}** par `backtest_krach.py` (dépôt `pilote-finance-dca-backtest`).",
        "> Données : S&P 500 dividendes réinvestis (Robert Shiller, shillerdata.com) + taux courts FRED, "
        "`data/marches.csv`. **En dollars, avant frais et avant impôt. Nominal.**",
        "> Chaque chiffre ci-dessous sort d'un fichier de résultats daté : §7.1 à §7.4 des "
        "`resultats/krach_*.csv`, §7.2 bis de `resultats/biais_seuil.json`, §7.5 de "
        "`resultats/synthese_krach.json`. **Aucun chiffre saisi à la main.**",
        "",
        f"**Scénario principal : {principal['periode']}, {principal['fenetres']} fenêtres de départ "
        f"mensuelles, horizon {principal['horizon_months'] // 12} ans, cash en attente rémunéré au "
        "bon du Trésor 3 mois (FRED TB3MS), plus-haut = **celui observé depuis t0** — "
        "l'investisseur regarde le marché à partir du jour où il a l'argent.**",
        "",
        "> 🔁 **Arbitrage Aleksandar, 04/08/2026 — le « dernier plus-haut ».** Le protocole ne "
        "tranchait pas entre deux lectures. La lecture retenue est **« observé depuis t0 »**. "
        "La lecture **« plus-haut historique réel »** (le pic peut être antérieur à t0, comme "
        "en 1934 où le marché est encore loin sous 1929) reste **publiée en comparaison** — "
        f"scénario `{CLE_COMPARAISON_ATH}` au §7.1."
        + (f" Sur le seuil des −20 %, l'écart entre les deux lectures est de "
           f"**{principal['strategies']['B20']['pct_fenetres_ou_B_bat_A']} %** (retenue) contre "
           f"**{compar['strategies']['B20']['pct_fenetres_ou_B_bat_A']} %** (comparative)."
           if compar else ""),
        "",
        "### 7.1 — Le tableau brut (tous les scénarios, toutes les fenêtres)",
        "",
        "| Scénario | Robot | B bat A | égalité stricte | écart médian | krach JAMAIS venu | "
        "attente moy. si on attend (mois) | pire écart | meilleur écart |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for t in tous:
        for nom in t["strategies"]:
            lignes.append(_ligne_tableau(t["cle"], t, nom, principal["periode"]))
    degeneres = [f"`{t['cle']}`" for t in tous
                 if any("AVERTISSEMENT_SCENARIO_DEGENERE" in b for b in t["strategies"].values())]
    autres_periodes = [f"`{t['cle']}` ({t['periode']})" for t in tous
                       if t["periode"] != principal["periode"]]
    lignes += [
        "",
        "*« B bat A » = % des fenêtres où attendre finit au-dessus d'investir tout de suite. "
        "« Égalité stricte » = fenêtres où le marché était **déjà** sous le seuil au départ : B investit "
        "à t0, il EST A. Ce ne sont ni des victoires ni des défaites.*",
    ]
    if degeneres:
        lignes += [
            "",
            f"⚠️ **Scénario(s) marqués : {', '.join(degeneres)}.** Toutes leurs fenêtres déclenchent à t0 : "
            "le robot n'attend jamais, il **est** le témoin. Ces lignes ne mesurent rien sur l'attente — "
            "ne pas les aligner avec les autres dans un graphique.",
        ]
    if autres_periodes:
        lignes += [
            "",
            f"🕒 **Périodes différentes du scénario principal ({principal['periode']}) : "
            f"{', '.join(autres_periodes)}.** Ces lignes ne se comparent PAS au principal ni entre "
            "elles : on comparerait des données, pas une hypothèse. En particulier `US_EUR` intègre "
            "l'effet de change et ne couvre que l'après-1999 — c'est le seul scénario où attendre "
            "ressort gagnant, et cette victoire n'est **pas** transposable au tableau principal.",
        ]
    lignes += [
        "",
        "### 7.2 — Le chiffre que le protocole exige : le krach qui n'arrive JAMAIS",
        "",
        "| Robot | % des fenêtres de 10 ans où le repli n'est JAMAIS venu | signal déjà là à t0 | "
        "attente médiane si le signal vient après t0 |",
        "|---|---|---|---|",
    ]
    for nom, b in principal["strategies"].items():
        med = b["attente_mediane_mois_quand_on_attend"]
        lignes.append(f"| {nom} | **{b['pct_fenetres_ou_le_krach_n_arrive_JAMAIS']} %** | "
                      f"{b['pct_fenetres_ou_le_signal_est_DEJA_LA_a_t0']} % | "
                      f"{med if med is not None else '—'} mois |")
    lignes += [
        "",
        f"*Scénario principal ({principal['periode']}, {principal['fenetres']} fenêtres). "
        "Dans les fenêtres « JAMAIS », le robot B a passé **10 ans entiers en cash** sans jamais investir.*",
        "",
    ]
    lignes += _bloc_granularite(signal, biais)
    lignes += [
        "### 7.3 — Le pire et le meilleur cas de chaque robot (fourchette honnête)",
        "",
        "| Robot | multiple final le PIRE (départ) | multiple final le MEILLEUR (départ) |",
        "|---|---|---|",
        f"| A (témoin) | ×{principal['A_pire']['multiple']} ({principal['A_pire']['depart']}) | "
        f"×{principal['A_meilleur']['multiple']} ({principal['A_meilleur']['depart']}) |",
    ]
    for nom, b in principal["strategies"].items():
        lignes.append(f"| {nom} | ×{b['pire']['multiple']} ({b['pire']['depart']}) | "
                      f"×{b['meilleur']['multiple']} ({b['meilleur']['depart']}) |")
    b20 = principal["strategies"]["B20"]
    attendu20 = b20["quand_le_signal_est_venu_APRES_t0"]
    lignes += [
        "",
        "*Multiple final du capital de départ, mêmes fenêtres, avant frais et avant impôt.*",
        "",
    ]
    lignes += _bloc_fenetres_citees(principal)
    lignes += [
        "### 7.4 — ⚠️ SOUS-ENSEMBLE : les fenêtres où le signal est venu APRÈS t0",
        "",
        "> 🚨 **Le chiffre le plus flatteur du document, et le plus facile à sortir de son contexte.** "
        "Cette section **exclut** les fenêtres où le krach n'est jamais venu — c'est-à-dire "
        "précisément celles où le robot a attendu **10 ans entiers en cash sans jamais investir**. "
        "Elle ne dit donc pas « ce que donne l'attente », elle dit « ce que donne l'attente **quand "
        "elle est récompensée** ». Interdiction de citer une de ces valeurs sans son dénominateur.",
        "",
        "| Robot | fenêtres retenues | exclues : signal jamais venu | exclues : signal déjà là à t0 | "
        "B bat A | écart médian |",
        "|---|---|---|---|---|---|",
    ]
    for nom, b in principal["strategies"].items():
        v = b["quand_le_signal_est_venu_APRES_t0"]
        # Quand rien n'est exclu, la ligne n'est PAS un sous-ensemble : le dire, sinon le titre
        # « ⚠️ SOUS-ENSEMBLE » fait douter d'un chiffre qui porte en fait sur toutes les fenetres.
        complet = " *(toutes les fenêtres — pas un sous-ensemble)*" if v["fenetres"] == v["fenetres_totales"] else ""
        lignes.append(
            f"| {nom} | **{v['fenetres']} / {v['fenetres_totales']}**{complet} | "
            f"{v['fenetres_exclues_car_signal_JAMAIS_venu']} | {v['fenetres_exclues_car_signal_DEJA_LA_a_t0']} | "
            f"{v.get('pct_ou_B_bat_A', '—')} % | {v.get('ecart_median_pct', '—')} % |"
        )
    lignes += [
        "",
        "*C'est la SEULE comparaison licite avec le scénario `US_achat_M1` : le taux brut du §7.1 "
        "bouge pour une raison comptable (les égalités disparaissent), pas économique.*",
        "",
        "### 7.5 — Le contrôle externe PWL 2020 : DEUX QUESTIONS COMPLÉMENTAIRES (protocole §5)",
        "",
        "> ✅ **Fact-check fait le 04/08/2026 : PDF PWL lu intégralement.** L'hypothèse « écart "
        "prix vs rendement total » est **écartée** — les deux études travaillent sur des indices "
        "de **rendement total**. Et surtout : **les deux tests ne posent pas la même question.** "
        "Ils ne se contredisent pas, ils se complètent.",
        "",
        "| | La question posée | Le chiffre |",
        "|---|---|---|",
        f"| **PWL / Felix 2020 (USA)** | Le krach **a déjà eu lieu**. J'ai le capital en main : "
        f"je place tout d'un coup, ou j'étale sur 12 mois ? | le tout d'un coup gagne "
        f"**{pwl['PWL']['us_pct']:.2f} %** du temps |",
        f"| **Notre réplique de leur test** | La même question, la même règle, sur nos données : "
        f"{pwl['fenetres_retenues']} fenêtres démarrant **le mois suivant** une chute ≥ 20 % "
        f"(= {pwl['blocs_de_fenetres_contigus']} blocs contigus, soit encore moins de krachs réels) | "
        f"**{pwl['notre_replique_pct']} %** |",
        f"| **Notre B20** | Le krach **n'a pas encore eu lieu**. J'attends en cash qu'il arrive, "
        f"ou je place tout de suite ? | attendre gagne **{b20['pct_fenetres_ou_B_bat_A']} %** du temps "
        f"(**{attendu20.get('pct_ou_B_bat_A', '—')} %** quand le signal finit par venir) |",
        "",
        f"**La méthode PWL, telle qu'écrite dans le PDF** : {pwl['PWL']['indice_us']} · "
        f"{pwl['PWL']['periode_us']} · cash = {pwl['PWL']['cash']} · {pwl['PWL']['devise']} · "
        f"{pwl['PWL']['regle']}. {pwl['PWL']['table']} : États-Unis **{pwl['PWL']['us_pct']:.2f} %**, "
        f"moyenne des 6 marchés **{pwl['PWL']['moyenne_6_marches_pct']:.2f} %**, avantage annualisé "
        f"du tout d'un coup **+{pwl['PWL']['avantage_annualise_LSI_pts']:.2f} pt/an**.",
        f"Source : {pwl['PWL']['etude']} — {pwl['PWL']['url']}",
        "",
        f"**Notre réplique donne {pwl['notre_replique_pct']} % contre {pwl['PWL']['us_pct']:.2f} % "
        f"({pwl['ecart_points']:+.1f} pt). Cet écart est SIGNALÉ, pas expliqué.** La seule piste "
        f"disponible est celle que **PWL avance lui-même** : {pwl['pourquoi_l_ecart']['hypothese_de_PWL']} "
        f"Notre série commence en **{pwl['pourquoi_l_ecart']['notre_periode_commence_en']}**.",
        "",
        f"⛔ **Et cette piste, nous ne pouvons pas la tester :** "
        f"{pwl['pourquoi_l_ecart']['CE_QU_ON_NE_PEUT_PAS_FAIRE']}",
        "",
        "> 🧾 **Note de méthode, ajoutée le 05/08/2026.** Une version antérieure de cette section "
        "écrivait que « nos fenêtres post-krach sont presque toutes des sorties de crise gagnantes ». "
        "**Vérification faite : c'est faux sur nos données** — nos fenêtres les plus anciennes sont "
        "les *moins* favorables au tout d'un coup, pas les plus. La phrase a été retirée. Le "
        "découpage de période qui l'accompagnait reste dans `synthese_krach.json` comme **diagnostic "
        "pour le fact-check**, et n'est pas publié ici : découper une période après avoir vu le "
        "résultat, c'est précisément ce que le protocole interdit de présenter comme un résultat.",
        "",
        f"⚠️ **{pwl['fenetres_retenues']} fenêtres ne sont pas {pwl['fenetres_retenues']} observations "
        f"indépendantes : elles ne forment que **{pwl['blocs_de_fenetres_contigus']} blocs contigus** "
        f"depuis {pwl['pourquoi_l_ecart']['notre_periode_commence_en']}.** Des fenêtres consécutives "
        "décrivent le même krach vu à un mois d'intervalle. Et le nombre de krachs **réellement "
        "distincts est encore plus petit** : un même bear market se recoupe en plusieurs blocs dès "
        "que l'indice repasse un mois au-dessus du seuil (1937, 1987-88, 2004). "
        f"{pwl['CE_QUE_LES_BLOCS_NE_SONT_PAS']} C'est la note « fenêtres chevauchantes » du §7.6, "
        "poussée à l'extrême.",
        "",
        f"*Repère : le même test **sans aucune condition de repli** donne "
        f"**{pwl['meme_test_SANS_condition_de_repli_pct']} %** sur les {pwl['fenetres_totales']} "
        "fenêtres — c'est le chiffre publié à l'ép. 1.*",
        "",
        "Différences de méthode déclarées :",
    ]
    lignes += [f"- {d}" for d in pwl["differences_declarees"]]
    lignes += ["", "### 7.6 — Ce que ces chiffres NE prouvent PAS", ""]
    lignes += [f"- **{k}** — {v}" for k, v in A_LIRE.items()]
    lignes += ["", "*(Fichiers sources : `resultats/synthese_krach.json`, `resultats/biais_seuil.json`, "
                   "`resultats/krach_*.csv`.)*", ""]
    return "\n".join(lignes)


SRC_SHILLER = "S&P 500 dividendes réinvestis — Robert Shiller, shillerdata.com"
SRC_FRED_TB3MS = "Taux du cash — bon du Trésor US 3 mois, FRED TB3MS"
SRC_FRED_SP500 = "S&P 500 cours quotidiens — FRED SP500"
SRC_FRED_NIKKEI = "Nikkei 225 — FRED (Nikkei Inc.), PRIX SEUL, sans dividendes"


def _carte(cid: str, titre: str, valeur, unite: str, sous_titre: str, source: str,
           fichier: str, quand: str) -> dict:
    """Une carte ecran = une valeur + SA SOURCE + SA DATE. Sans les trois, elle n'est pas publiable."""
    return {"id": cid, "titre": titre, "valeur": valeur, "unite": unite, "sous_titre": sous_titre,
            "source": source, "date_generation": quand, "fichier_source": fichier}


def cartes(tous: list[dict], pwl: dict, signal: dict, biais: dict | None, quand: str) -> dict:
    """Le JSON destine aux CARTES a l'ecran. Aucune valeur n'y est saisie a la main.

    Regle du studio (protocole §5) : source + date sur CHAQUE carte. Le generateur de cartes
    doit pouvoir refuser une carte sans source — il faut donc que la source voyage AVEC le chiffre.
    """
    p = next(t for t in tous if t["cle"] == CLE_PRINCIPAL)
    c = next((t for t in tous if t["cle"] == CLE_COMPARAISON_ATH), None)
    jp = next((t for t in tous if t["cle"] == "JP"), None)
    b10, b20, b30 = p["strategies"]["B10"], p["strategies"]["B20"], p["strategies"]["B30"]
    src = f"{SRC_SHILLER} · {SRC_FRED_TB3MS}"
    f_p = p["fichier"]
    liste = [
        _carte("perimetre", "Le test", p["fenetres"], "fenêtres",
               f"Départs mensuels, {p['periode']}, horizon {p['horizon_months'] // 12} ans. "
               "En dollars, avant frais et avant impôt.", src, f_p, quand),
        _carte("b20_bat_a", "Attendre −20 % bat investir tout de suite",
               b20["pct_fenetres_ou_B_bat_A"], "%",
               f"Sur les {p['fenetres']} fenêtres. Écart médian {b20['ecart_median_pct']:+.2f} %.",
               src, f_p, quand),
        _carte("b20_jamais", "Le krach de −20 % n'est JAMAIS venu",
               b20["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"], "%",
               "Des fenêtres de 10 ans où le robot est resté en cash du début à la fin.",
               src, f_p, quand),
        _carte("b30_jamais", "Le krach de −30 % n'est JAMAIS venu",
               b30["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"], "%",
               f"Écart médian de B30 sur l'ensemble : {b30['ecart_median_pct']:+.2f} %.",
               src, f_p, quand),
        # Formulee a l'ENDROIT : « 0 % de jamais » se lit mal a l'ecran, « 100 % » se lit tout seul.
        _carte("b10_toujours", "Un repli de −10 %, lui, finit TOUJOURS par arriver",
               round(100.0 - b10["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"], 1), "%",
               f"Sur les {p['fenetres']} fenêtres de 10 ans. Attente médiane : "
               f"{b10['attente_mediane_mois_quand_on_attend']} mois — et attendre reste perdant "
               f"({b10['ecart_median_pct']:+.2f} % en médiane).", src, f_p, quand),
        _carte("b20_attente", "Attente moyenne avant le signal −20 %",
               b20["attente_moyenne_mois_quand_on_attend"], "mois",
               f"Quand le signal finit par venir. Attente la plus longue observée avant un signal : "
               f"{b20['attente_max_mois']} mois — à ne pas confondre avec les fenêtres où il "
               f"n'est jamais venu ({b20['pct_fenetres_ou_le_krach_n_arrive_JAMAIS']} %).",
               src, f_p, quand),
        # Titre FACTUEL : 53 %, c'est pile ou face. Un titre qui tranche mentirait a l'ecran,
        # ou le spectateur lit le titre et pas le sous-titre.
        _carte("b20_si_signal", "Quand le krach vient, attendre finit devant… une fois sur deux",
               b20["quand_le_signal_est_venu_APRES_t0"].get("pct_ou_B_bat_A"), "%",
               f"⚠️ SOUS-ENSEMBLE : {b20['quand_le_signal_est_venu_APRES_t0']['fenetres']} fenêtres "
               f"sur {p['fenetres']}. Exclut les "
               f"{b20['quand_le_signal_est_venu_APRES_t0']['fenetres_exclues_car_signal_JAMAIS_venu']} "
               "fenêtres où le krach n'est jamais venu. NE JAMAIS afficher seul.", src, f_p, quand),
        _carte("temoin_pire", "Le témoin, dans sa pire fenêtre", p["A_pire"]["multiple"], "×",
               f"Départ {p['A_pire']['depart']}. Meilleure fenêtre : ×{p['A_meilleur']['multiple']} "
               f"(départ {p['A_meilleur']['depart']}).", src, f_p, quand),
        _carte("b20_pire", "Le robot « j'attends −20 % », dans sa pire fenêtre",
               b20["pire"]["multiple"], "×",
               f"Départ {b20['pire']['depart']}. Pire écart face au témoin : "
               f"{b20['ecart_pire_pct']:+.2f} %.", src, f_p, quand),
        _carte("pwl_us", "PWL Capital 2020 — le krach a DÉJÀ eu lieu", pwl["PWL"]["us_pct"], "%",
               "Le tout d'un coup bat l'étalement sur 12 mois. Question DIFFÉRENTE de la nôtre.",
               f"{pwl['PWL']['etude']} — {pwl['PWL']['table']}", "PDF PWL (lu le 04/08/2026)", quand),
        _carte("pwl_replique", "Le même test, nos données", pwl["notre_replique_pct"], "%",
               f"{pwl['fenetres_retenues']} fenêtres démarrant le mois suivant une chute ≥ 20 %, soit seulement "
               f"{pwl['blocs_de_fenetres_contigus']} blocs contigus — et encore moins de krachs réels. "
               f"Écart avec PWL ({pwl['ecart_points']:+.1f} pt) SIGNALÉ, pas expliqué : la seule piste "
               "est celle que PWL avance lui-même (ses années 1930), et nous ne pouvons pas la tester.",
               src, "synthese_krach.json", quand),
    ]
    if c:
        liste.append(_carte("lecture_comparative", "L'autre lecture du « dernier plus-haut »",
                            c["strategies"]["B20"]["pct_fenetres_ou_B_bat_A"], "%",
                            "Plus-haut historique réel (le pic peut être antérieur à t0), même "
                            f"période. Lecture retenue : {b20['pct_fenetres_ou_B_bat_A']} %.",
                            src, c["fichier"], quand))
    if jp:
        liste.append(_carte("japon", "Le témoin japonais — attendre −20 %",
                            jp["strategies"]["B20"]["pct_fenetres_ou_B_bat_A"], "%",
                            f"{jp['fenetres']} fenêtres, {jp['periode']}. Nikkei SANS dividendes "
                            "(Japon sous-estimé) et cash à 0 % (robot défavorisé) : c'est un plancher.",
                            SRC_FRED_NIKKEI, jp["fichier"], quand))
    if biais and biais.get("C_sp500_quotidien"):
        par_an = {x["annee"]: x for x in biais["C_sp500_quotidien"]["pire_repli_par_annee"]}
        mens = {x["annee"]: x for x in biais["B_prix_contre_rendement_total"]
                ["pire_repli_par_annee_10_dernieres"]}
        for an in (2020, 2022):
            if an in par_an and an in mens:
                # LES TROIS valeurs, jamais les deux extremes seules : le quotidien est un indice
                # de PRIX et le mensuel un rendement TOTAL. N'afficher que -33,92 % vs -18,92 %
                # attribuerait tout l'ecart a la granularite — ce que biais_seuil.json interdit.
                liste.append(_carte(
                    f"granularite_{an}", f"Le krach de {an}, vu de trois façons",
                    par_an[an]["pire_repli_quotidien_pct"], "%",
                    f"Cours quotidiens, prix ({par_an[an]['date']}) : "
                    f"{par_an[an]['pire_repli_quotidien_pct']:.2f} % — moyenne mensuelle, prix : "
                    f"{mens[an]['prix_seul_pct']:.2f} % — moyenne mensuelle, dividendes réinvestis "
                    f"(NOTRE donnée) : {mens[an]['rendement_total_pct']:.2f} %. "
                    "Les trois chiffres ensemble, jamais les deux extrêmes seuls : l'écart vient "
                    "de la granularité ET du choix de l'indice.",
                    f"{SRC_FRED_SP500} · {SRC_SHILLER}", "biais_seuil.json", quand))
    manquantes = [x["id"] for x in liste if x["valeur"] is None]
    if manquantes:
        raise DonneeManquante(f"Cartes sans valeur : {manquantes} -> STOP, une carte vide est un bug.")
    return {
        "genere_le": quand,
        "donnees_reelles": True,
        "episode": "PF « Le Test » ép. 2 — Attendre le krach pour investir ?",
        "convention_ecran": "en dollars, avant frais et avant impôt",
        "REGLE": "Chaque carte porte SA source et SA date. Une carte sans source ne se monte pas.",
        "INTERDICTIONS": [
            "Ne jamais afficher `b20_si_signal` sans son sous-titre : c'est un sous-ensemble.",
            "Ne jamais conclure « donc fais X » : le verdict est un constat historique (protocole §6).",
            "Ne jamais présenter PWL comme contredisant B20 : deux questions différentes.",
            "Ne jamais mélanger deux scénarios de périodes différentes sur une même carte.",
        ],
        "cartes": liste,
    }


def controle_orphelins(produits: set[str]) -> None:
    """Un CSV d'un run PRECEDENT qui traine = deux verdicts contradictoires dans le dossier publie.

    Vecu le 04/08/2026 : apres la bascule de la lecture principale, `resultats/` contenait DEUX
    fichiers nommes « US_principal » — l'ancien (plus-haut historique, B20 = 29,8 %) et le nouveau
    (plus-haut depuis t0, B20 = 36,1 %). Rien ne disait lequel etait le bon. Le depot est publie
    avec la video : on SIGNALE et on s'arrete. On ne supprime jamais en silence un fichier de
    resultats — c'est a un humain de trancher.
    """
    # Angle mort du controle : deux scenarios de meme cle ecriraient le MEME fichier, l'un
    # ecrasant l'autre, sans jamais apparaitre comme orphelin. On ferme la porte en amont.
    cles = [s["cle"] for s in SCENARIOS]
    if len(set(cles)) != len(cles):
        doublons = sorted({c for c in cles if cles.count(c) > 1})
        raise DonneeManquante(f"Cles de scenario en double : {doublons} -> STOP (un scenario en "
                              "ecraserait un autre en silence).")
    presents = {f.name for f in OUT.glob("krach_*.csv")}
    orphelins = sorted(presents - produits)
    if orphelins:
        raise DonneeManquante(
            f"{len(orphelins)} fichier(s) de resultats ORPHELIN(S) dans {OUT} — ils viennent d'un run "
            "precedent et ne correspondent a aucun scenario actuel :\n  - " + "\n  - ".join(orphelins) +
            "\n-> STOP. Les supprimer A LA MAIN apres verification, puis relancer. Publier un dossier "
            "qui contient deux verdicts pour le meme scenario est un bug anti-fiction."
        )


def charge_biais_seuil() -> dict | None:
    """La mesure granularite / rendement total. ABSENTE = on n'ecrit AUCUNE cause au §7.2 bis."""
    f = OUT / "biais_seuil.json"
    if not f.exists():
        return None
    try:
        biais = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise DonneeManquante(f"{f} illisible ({e}) -> STOP. Relancer `python mesure_biais_seuil.py` "
                              "plutot que publier un §7.2 bis muet.") from e
    manquant = [c for c in ("genere_le", "A_granularite", "B_prix_contre_rendement_total")
                if c not in biais]
    if manquant:
        raise DonneeManquante(f"{f} incomplet (manque {manquant}) -> STOP.")
    return biais


def controle_croise(signal: dict, biais: dict) -> dict:
    """DEUX CHEMINS INDEPENDANTS doivent donner le MEME chiffre — sinon on s'arrete.

    `signal_dans_la_donnee` lit data/marches.csv (l'indice deja construit).
    `mesure_biais_seuil` retelecharge le .xls Shiller et RECONSTRUIT le rendement total.
    Si les deux divergent, c'est que le CSV et la source ne disent plus la meme chose :
    publier les deux tableaux cote a cote serait publier une contradiction sans le voir.
    """
    ref = biais["B_prix_contre_rendement_total"]["rendement_total_CE_QUE_LE_MOTEUR_UTILISE"]
    ecarts = []
    for nom, a in signal["seuils"].items():
        if nom not in ref:
            continue
        b = ref[nom]
        if a["mois_sous_le_seuil"] != b["mois_sous_le_seuil"]:
            ecarts.append(f"{nom} : {a['mois_sous_le_seuil']} mois (marches.csv) "
                          f"vs {b['mois_sous_le_seuil']} (Shiller retelecharge)")
        if a["dernier_mois_sous_le_seuil"] != b["dernier_mois_sous_le_seuil"]:
            ecarts.append(f"{nom} : dernier mois {a['dernier_mois_sous_le_seuil']} "
                          f"vs {b['dernier_mois_sous_le_seuil']}")
    if ecarts:
        raise DonneeManquante(
            "CONTROLE CROISE EN ECHEC — data/marches.csv et la source Shiller ne disent plus la "
            "meme chose :\n  - " + "\n  - ".join(ecarts) +
            "\n-> STOP. Relancer build_data.py PUIS mesure_biais_seuil.py, dans cet ordre."
        )
    return {"verdict": "OK",
            "quoi": "Nombre de mois sous chaque seuil, calcule par DEUX chemins independants "
                    "(data/marches.csv vs .xls Shiller retelecharge). Identiques.",
            "seuils_verifies": [n for n in signal["seuils"] if n in ref],
            "genere_le_biais": biais["genere_le"]}


def main() -> int:
    if not DONNEES_REELLES:
        raise SystemExit("DONNEES_REELLES=False : refus de produire quoi que ce soit.")
    OUT.mkdir(exist_ok=True)
    df = ep1.charge()
    tous, produits = [], set()

    for s in SCENARIOS:
        cle = s["cle"]
        params = {k: v for k, v in s.items() if k != "cle"}
        r = run_krach(df, horizon_months=120, **params)
        nom_fichier = (f"krach_{cle}_{params['marche']}_{params['reference']}_{params['cash_rate']}"
                       f"_{params['debut'] or 'tout'}")
        ep1.ecris(OUT / f"{nom_fichier}.csv", r.to_csv(index=False))   # pannes #2/#3 : OneDrive, disque plein
        produits.add(f"{nom_fichier}.csv")
        res = resume_krach(r)
        res["cle"], res["fichier"] = cle, f"{nom_fichier}.csv"
        if cle == CLE_PRINCIPAL:
            res["fenetres_citees"] = fenetres_citees(r)
        tous.append(res)

        print(f"\n=== {cle}  ({res['fenetres']} fenetres, {res['periode']}, "
              f"plus-haut={params['reference']}, cash={params['cash_rate']}) ===")
        for nom, b in res["strategies"].items():
            v = b["quand_le_signal_est_venu_APRES_t0"]
            print(f"  {nom:5s} bat A dans {b['pct_fenetres_ou_B_bat_A']:5.1f} % des fenetres "
                  f"(egalite {b['pct_fenetres_egalite_stricte']:5.1f} %) | median {b['ecart_median_pct']:+8.2f} % "
                  f"| krach JAMAIS venu {b['pct_fenetres_ou_le_krach_n_arrive_JAMAIS']:5.1f} % "
                  f"| signal APRES t0 ({v['fenetres']:4d}/{v['fenetres_totales']} fen.) : "
                  f"{v.get('pct_ou_B_bat_A', '—')} %")
            if "AVERTISSEMENT_SCENARIO_DEGENERE" in b:
                print(f"        /!\\ {b['AVERTISSEMENT_SCENARIO_DEGENERE']}")

    if not any(t["cle"] == CLE_PRINCIPAL for t in tous):
        raise DonneeManquante(f"Scenario {CLE_PRINCIPAL} absent -> §7 impossible.")
    controle_orphelins(produits)
    pwl = replique_pwl(df)
    print(f"\n=== REPLIQUE PWL (LSI vs DCA 12 mois, depart le mois SUIVANT une chute >= 20 %, "
          f"{pwl['fenetres_retenues']} fenetres) ===")
    print(f"  nous {pwl['notre_replique_pct']} %  vs  PWL {pwl['PWL']['us_pct']} %  "
          f"-> ecart {pwl['ecart_points']:+.1f} pt SIGNALE (pas explique : la piste des annees 1930 "
          f"est celle de PWL, et on ne peut pas la tester)\n  {pwl['fenetres_retenues']} fenetres "
          f"= {pwl['blocs_de_fenetres_contigus']} blocs contigus (encore moins de krachs reels) "
          f"| sans condition : {pwl['meme_test_SANS_condition_de_repli_pct']} %")

    signal = signal_dans_la_donnee(df)
    d = signal.get("depuis_le_dernier_signal_-20pct")
    if d:
        print(f"\n=== LE SIGNAL DANS LA DONNEE ===\n  dernier -20 % : {d['dernier_signal']} "
              f"({d['mois_ecoules_sans_signal']} mois sans signal depuis) | pire repli mensuel depuis : "
              f"{d['pire_repli_mensuel_depuis']} % en {d['date_du_pire_repli']}")

    biais = charge_biais_seuil()
    croise = None
    if biais is None:
        print("\n/!\\ resultats/biais_seuil.json ABSENT : le §7.2 bis n'expliquera RIEN "
              "(lancer `python mesure_biais_seuil.py`).")
    else:
        croise = controle_croise(signal, biais)
        print(f"\n=== CONTROLE CROISE (2 chemins independants) : {croise['verdict']} "
              f"sur {', '.join(croise['seuils_verifies'])} ===")

    quand = horodatage()
    synthese = {
        "genere_le": quand,
        "donnees_reelles": True,
        "protocole": "PF_LeTest_Ep2_Krach_PROTOCOLE.md (FIGE avant le calcul)",
        "contrat": "CONTRAT_backtest_krach.md",
        "avertissement": "Un backtest MESURE LE PASSE. Il ne predit RIEN sur le futur.",
        "A_LIRE_AVANT_DE_CITER_UN_CHIFFRE": A_LIRE,
        "replique_pwl": pwl,
        "le_signal_dans_la_donnee": signal,
        "biais_du_seuil_mesure": "resultats/biais_seuil.json" if biais else "NON MESURE",
        "controle_croise": croise or "NON EFFECTUE (biais_seuil.json absent)",
        "scenarios": tous,
    }
    ep1.ecris(OUT / "synthese_krach.json", json.dumps(synthese, indent=2, ensure_ascii=False))
    ep1.ecris(OUT / "SECTION_7.md", section_7(tous, pwl, signal, biais, quand))
    jeu = cartes(tous, pwl, signal, biais, quand)
    ep1.ecris(OUT / "cartes_ep2.json", json.dumps(jeu, indent=2, ensure_ascii=False))
    print(f"\nOK -> {OUT / 'synthese_krach.json'}  ({len(tous)} scenarios)")
    print(f"OK -> {OUT / 'SECTION_7.md'}  (a coller tel quel dans le protocole §7)")
    print(f"OK -> {OUT / 'cartes_ep2.json'}  ({len(jeu['cartes'])} cartes, source+date sur chacune)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
