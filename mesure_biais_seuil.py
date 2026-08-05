#!/usr/bin/env python3
"""POURQUOI le robot B20 ne se declenche-t-il ni en 2020 ni en 2022 ? On le MESURE.

Le moteur de l'ep. 2 (backtest_krach.py) declenche B10/B20/B30 sur un repli de -10/-20/-30 %
sous le dernier plus-haut, mesure sur le S&P 500 en RENDEMENT TOTAL (dividendes reinvestis),
en donnees MENSUELLES (moyennes de cours quotidiens, methode Shiller).

Resultat brut : le seuil des -20 % n'a plus ete franchi depuis 2010-09. Ni le Covid ni 2022.
DEUX suspects, et il serait malhonnete d'en accuser un sans mesurer :
  (1) la GRANULARITE  — une moyenne mensuelle efface le creux d'un krach ;
  (2) le RENDEMENT TOTAL — les dividendes reinvestis remontent l'indice et rabotent le repli.

Ce module isole les deux, chacun avec UNE SEULE variable qui change :
  A. Granularite  -> Nikkei 225 (le seul marche dont on a le QUOTIDIEN sur 77 ans) :
                     quotidien vs fin de mois vs moyenne du mois. Meme marche, meme regle.
  B. Prix vs TR   -> S&P 500 Shiller : le meme mois, le meme plus-haut, deux definitions
                     de l'indice (prix seul P, et rendement total dividendes reinvestis).

On ne suppose rien. On compte les mois passes sous chaque seuil, dans chaque monde.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

from backtest import ecris
from build_data import (
    DonneeManquante,
    charge_shiller,
    horodatage,
    mois_en_cours,
    telecharge,
)

DONNEES_REELLES = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
OUT = HERE / "resultats"

URL_NIKKEI = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NIKKEI225"
URL_SP500_QUOTIDIEN = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500"
SEUILS = (0.10, 0.20, 0.30)


TOL = 1e-12   # meme tolerance que le moteur : -20,000000 % PILE doit compter


def _sous_les_seuils(drawdown: pd.Series, seuils=SEUILS) -> dict:
    """Combien de MOIS passes sous chaque seuil, et quand pour la derniere fois."""
    out = {}
    for s in seuils:
        sous = drawdown <= -s * 100.0 + TOL
        out[f"B{s * 100:g}"] = {
            "mois_sous_le_seuil": int(sous.sum()),
            "pct_du_temps": round(float(sous.mean() * 100), 1),
            "dernier_mois_sous_le_seuil": str(drawdown.index[sous][-1]) if sous.any() else None,
        }
    return out


def charge_nikkei_quotidien() -> pd.DataFrame:
    """Meme telechargement que build_data (retry compris) — pas une 2e implementation."""
    d = pd.read_csv(io.BytesIO(telecharge(URL_NIKKEI, 1_000)))
    if d.shape[1] != 2:
        raise DonneeManquante(f"FRED NIKKEI225 : format inattendu ({list(d.columns)})")
    d.columns = ["date", "v"]
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["v"] = pd.to_numeric(d["v"], errors="coerce")
    d = d.dropna()
    if len(d) < 10_000:
        raise DonneeManquante(f"NIKKEI225 : {len(d)} lignes, trop peu.")
    # Tri EXPLICITE : un cummax sur des dates desordonnees fabriquerait un faux plus-haut.
    # FRED renvoie trie aujourd'hui — on ne parie pas la justesse d'un chiffre publie la-dessus.
    d = d.sort_values("date").reset_index(drop=True)
    d["mois"] = d["date"].dt.to_period("M")
    return d[d["mois"] < mois_en_cours()]   # le mois en cours n'est pas un mois clos


def mesure_granularite() -> dict:
    """A. Une moyenne mensuelle FAIT-ELLE disparaitre des franchissements de seuil ?"""
    d = charge_nikkei_quotidien()

    # (1) LA VERITE : plus-haut et repli mesures au jour le jour. Un mois compte des qu'UN
    #     SEUL jour du mois passe sous le seuil.
    dd_jour = (d["v"] / d["v"].cummax() - 1.0) * 100.0
    mois_touches = dd_jour.groupby(d["mois"]).min()

    fin_de_mois = d.groupby("mois")["v"].last()
    moyenne_mois = d.groupby("mois")["v"].mean()
    attendu = pd.period_range(fin_de_mois.index.min(), fin_de_mois.index.max(), freq="M")
    if not fin_de_mois.index.equals(attendu):
        raise DonneeManquante(
            f"Mois manquants dans le Nikkei : {attendu.difference(fin_de_mois.index)[:5].tolist()} -> STOP."
        )

    dd_fin = (fin_de_mois / fin_de_mois.cummax() - 1.0) * 100.0
    dd_moy = (moyenne_mois / moyenne_mois.cummax() - 1.0) * 100.0

    quotidien, moyenne = _sous_les_seuils(mois_touches), _sous_les_seuils(dd_moy)
    # Le chiffre parlant, calcule ICI plutot que laisse a la soustraction du lecteur.
    # L'emboitement est garanti : cummax(jour) >= cummax(moyenne) et min(jour) <= moyenne,
    # donc tout mois vu par la moyenne est aussi vu par le quotidien. La difference est un
    # nombre de mois RATES, jamais un solde de deux ensembles disjoints.
    rates = {}
    for nom, q in quotidien.items():
        manques = q["mois_sous_le_seuil"] - moyenne[nom]["mois_sous_le_seuil"]
        if manques < 0:
            raise DonneeManquante(
                f"{nom} : la moyenne mensuelle voit PLUS de signaux que le quotidien "
                f"({moyenne[nom]['mois_sous_le_seuil']} > {q['mois_sous_le_seuil']}) -> impossible, "
                "l'emboitement est mathematique. Un des deux calculs est faux : STOP."
            )
        rates[nom] = manques
    return {
        "marche": "Nikkei 225 (FRED, Nikkei Inc.) — seul marche dont on a le quotidien sur longue periode",
        "url": "https://fred.stlouisfed.org/series/NIKKEI225",
        "periode": f"{fin_de_mois.index.min()} -> {fin_de_mois.index.max()}",
        "protocole": "Meme marche, meme periode, meme regle de repli. SEULE variable : la granularite.",
        "ATTENTION_DEUX_COMPTAGES": "En QUOTIDIEN, un mois compte des qu'UN SEUL JOUR passe sous le "
                                    "seuil. En MENSUEL, il compte si LA VALEUR DU MOIS est sous le "
                                    "seuil. C'est voulu (le robot verrait-il un signal ?), mais les "
                                    "colonnes 'part des mois' ne mesurent donc PAS la meme chose.",
        "quotidien_LA_VERITE": quotidien,
        "fin_de_mois": _sous_les_seuils(dd_fin),
        "moyenne_du_mois_METHODE_SHILLER": moyenne,
        "mois_rates_par_la_moyenne_du_mois": rates,
        "LIMITE": "Biais mesure sur le NIKKEI. Ce n'est pas mecaniquement sa valeur sur le S&P 500 : "
                  "c'est un ORDRE DE GRANDEUR, a presenter comme tel.",
    }


def mesure_prix_contre_rendement_total(debut: str = "1934-01") -> dict:
    """B. Le repli est-il rabote par les DIVIDENDES REINVESTIS plutot que par la granularite ?"""
    sh = charge_shiller()
    complet = sh["P"].notna() & sh["D"].notna() & sh["CPI"].notna()
    base = sh.loc[: complet[complet].index.max()]

    prix = base["P"]
    # Rendement total : EXACTEMENT la construction de build_data.py (pas une 2e formule).
    rendement = ((base["P"] + base["D"] / 12.0) / base["P"].shift(1) - 1.0).iloc[1:]
    if rendement.isna().any():
        raise DonneeManquante("Rendement US non calculable sur certains mois -> STOP.")
    tr = (1.0 + rendement).cumprod()

    commun = prix.index.intersection(tr.index)
    prix, tr = prix.loc[commun], tr.loc[commun]      # MEMES mois des deux cotes, sinon on compare deux periodes
    dd_prix = (prix / prix.cummax() - 1.0) * 100.0
    dd_tr = (tr / tr.cummax() - 1.0) * 100.0
    if debut:
        d0 = pd.Period(debut, freq="M")
        dd_prix, dd_tr = dd_prix.loc[dd_prix.index >= d0], dd_tr.loc[dd_tr.index >= d0]

    # Les annees ou le debat se joue : le pire repli de chaque annee, dans les deux mondes.
    par_an_prix = dd_prix.groupby(dd_prix.index.year).min()
    par_an_tr = dd_tr.groupby(dd_tr.index.year).min()
    annees = sorted(set(par_an_prix.index) & set(par_an_tr.index))
    recentes = [a for a in annees if a >= max(annees) - 9]

    return {
        "marche": "S&P 500 (Robert Shiller, ie_data.xls) — prix MOYENNE MENSUELLE",
        "url": "https://shillerdata.com/",
        "periode": f"{dd_prix.index.min()} -> {dd_prix.index.max()}",
        "protocole": "MEMES mois, MEME regle de plus-haut. SEULE variable : prix seul vs dividendes reinvestis.",
        "prix_seul": _sous_les_seuils(dd_prix),
        "rendement_total_CE_QUE_LE_MOTEUR_UTILISE": _sous_les_seuils(dd_tr),
        "pire_repli_par_annee_10_dernieres": [
            {"annee": int(a),
             "prix_seul_pct": round(float(par_an_prix[a]), 2),
             "rendement_total_pct": round(float(par_an_tr[a]), 2)}
            for a in recentes
        ],
    }


def mesure_sp500_quotidien(annees: int = 10) -> dict:
    """C. Le S&P 500 EN COURS QUOTIDIENS — ce que la moyenne mensuelle efface, chez NOUS.

    La section A mesure la granularite sur le Nikkei (seul marche dont on ait le quotidien sur
    77 ans). Mais l'encadre du §7.2 bis parle de 2020 et 2022 SUR LE S&P 500 : ces deux chiffres
    doivent venir du S&P 500 lui-meme, pas d'un ordre de grandeur japonais.

    ⚠️ LIMITES ASSUMEES, a dire a l'ecran :
      - FRED SP500 est un INDICE DE PRIX (sans dividendes) : comparable a la colonne « prix seul »
        de la section B, PAS a la colonne « rendement total ».
      - La serie FRED est GLISSANTE (10 ans) : le plus-haut de reference ne remonte donc pas
        au-dela du premier jour disponible. Suffisant pour 2020 et 2022 (dont les pics sont
        dedans), insuffisant pour toute question anterieure.
    """
    d = pd.read_csv(io.BytesIO(telecharge(URL_SP500_QUOTIDIEN, 1_000)))
    if d.shape[1] != 2:
        raise DonneeManquante(f"FRED SP500 : format inattendu ({list(d.columns)})")
    d.columns = ["date", "v"]
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["v"] = pd.to_numeric(d["v"], errors="coerce")     # FRED ecrit "." les jours feries
    d = d.dropna().sort_values("date").reset_index(drop=True)
    if len(d) < 1_500:
        raise DonneeManquante(f"FRED SP500 : {len(d)} seances, trop peu pour {annees} ans.")
    if (d["v"] <= 0).any():
        raise DonneeManquante("FRED SP500 : cours <= 0 -> STOP.")

    d["dd"] = (d["v"] / d["v"].cummax() - 1.0) * 100.0
    par_an = []
    for an, w in d.groupby(d["date"].dt.year):
        i = w["dd"].idxmin()
        par_an.append({"annee": int(an), "pire_repli_quotidien_pct": round(float(w.loc[i, "dd"]), 2),
                       "date": str(w.loc[i, "date"].date())})
    return {
        "marche": "S&P 500, cours de CLOTURE QUOTIDIENS (indice de PRIX, sans dividendes)",
        "source": "FRED SP500", "url": "https://fred.stlouisfed.org/series/SP500",
        "periode": f"{d['date'].min().date()} -> {d['date'].max().date()}",
        "seances": int(len(d)),
        "pire_repli_par_annee": par_an,
        "pire_repli_de_la_periode_pct": round(float(d["dd"].min()), 2),
        "date_du_pire_repli": str(d.loc[d["dd"].idxmin(), "date"].date()),
        "LIMITE_serie_glissante": "FRED SP500 ne couvre que les ~10 dernieres annees : le plus-haut "
                                  "de reference ne remonte pas avant le premier jour disponible. "
                                  "Valable pour 2020 et 2022, PAS pour une question anterieure.",
        "LIMITE_prix_seul": "Indice de PRIX (sans dividendes) : a comparer a la colonne 'prix seul' "
                            "de la section B, jamais a la colonne 'rendement total'.",
    }


def main() -> int:
    if not DONNEES_REELLES:
        raise SystemExit("DONNEES_REELLES=False : refus de produire quoi que ce soit.")
    OUT.mkdir(exist_ok=True)

    print("1/3 Granularite (Nikkei quotidien vs fin de mois vs moyenne du mois)...")
    gran = mesure_granularite()
    print("2/3 Prix seul vs rendement total (S&P 500 Shiller)...")
    pt = mesure_prix_contre_rendement_total()
    print("3/3 S&P 500 en cours QUOTIDIENS (FRED SP500, 10 ans glissants)...")
    quot = mesure_sp500_quotidien()

    print(f"\n=== A. GRANULARITE — Nikkei, {gran['periode']} ===")
    for cle in ("quotidien_LA_VERITE", "fin_de_mois", "moyenne_du_mois_METHODE_SHILLER"):
        b = gran[cle]["B20"]
        print(f"  {cle:34s} : {b['mois_sous_le_seuil']:4d} mois sous -20 % "
              f"({b['pct_du_temps']:4.1f} % du temps) | dernier : {b['dernier_mois_sous_le_seuil']}")

    print(f"\n=== B. PRIX vs RENDEMENT TOTAL — S&P 500, {pt['periode']} ===")
    for cle in ("prix_seul", "rendement_total_CE_QUE_LE_MOTEUR_UTILISE"):
        b = pt[cle]["B20"]
        print(f"  {cle:36s} : {b['mois_sous_le_seuil']:4d} mois sous -20 % "
              f"({b['pct_du_temps']:4.1f} % du temps) | dernier : {b['dernier_mois_sous_le_seuil']}")
    print(f"\n=== C. S&P 500 QUOTIDIEN — {quot['periode']} ({quot['seances']} seances) ===")
    quot_par_an = {a["annee"]: a for a in quot["pire_repli_par_annee"]}
    print("  pire repli de chaque annee — QUOTIDIEN / prix mensuel / rendement total mensuel :")
    for a in pt["pire_repli_par_annee_10_dernieres"]:
        q = quot_par_an.get(a["annee"])
        qs = f"{q['pire_repli_quotidien_pct']:7.2f} % ({q['date']})" if q else "        n/d      "
        print(f"    {a['annee']} : {qs}  /  {a['prix_seul_pct']:7.2f} %  /  {a['rendement_total_pct']:7.2f} %")

    out = {
        "genere_le": horodatage(),
        "donnees_reelles": True,
        "quoi": "Pourquoi le seuil des -20 % n'est plus franchi depuis 2010 dans notre moteur ? "
                "Deux suspects mesures separement : la granularite mensuelle et le rendement total.",
        "A_granularite": gran,
        "B_prix_contre_rendement_total": pt,
        "C_sp500_quotidien": quot,
        "A_LIRE": {
            "aucune_conclusion_pre_ecrite": "Ce fichier ne conclut pas a la place du fact-check : il "
                "donne les comptages. La phrase publiee au §7 doit citer CES chiffres, pas une intuition.",
            "les_deux_effets_se_cumulent": "Granularite et rendement total ne s'excluent pas : ils "
                "poussent tous les deux dans le meme sens (moins de franchissements). Attribuer 100 % "
                "de l'effet a l'un des deux serait faux.",
            "ce_que_le_protocole_a_fige": "Le protocole ep. 2 §3 dit 'S&P 500 dividendes reinvestis' et "
                "'granularite mensuelle assumee et dite'. Les deux choix sont donc DANS le protocole : "
                "ce module ne les conteste pas, il en CHIFFRE la consequence sur le declenchement.",
        },
    }
    ecris(OUT / "biais_seuil.json", json.dumps(out, indent=2, ensure_ascii=False))
    print("\nOK -> resultats/biais_seuil.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
