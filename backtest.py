#!/usr/bin/env python3
"""Moteur de backtest — DCA vs tout d'un coup. Pilote Finance, « Le Test ».

DEUX questions, pas une :
  TEST A — un capital qu'on a DEJA : tout d'un coup  vs  etale sur D mois.
  TEST B — un salaire qui TOMBE chaque mois : investi tout de suite  vs  accumule 12 mois puis investi.
           ^ NOTRE THESE : « 500 EUR/mois depuis son salaire », ce n'est PAS du DCA.

PROTOCOLE FIGE AVANT LE CALCUL (CONTRAT_backtest.md) :
  - TOUTES les fenetres de depart sont publiees. Jamais une seule. Jamais celle qui nous arrange.
  - Lump et DCA sont compares a la MEME date de fin.
  - Comparer deux scenarios exige la MEME PERIODE (sinon on compare 63 ans de donnees, pas une hypothese).
  - Le cash qui attend est remunere au taux court de SA DEVISE (jamais le T-bill US pour un yen).
  - Aucun resultat n'autorise a conclure sur le FUTUR.

v2 — 13/07/2026, apres gate code-reviewer (verdict STOP sur la v1). Corriges :
  BLOQUANT 1+2 : le DCA est desormais AUTO-FINANCE (il verse pot/(D-k)) -> il ne peut plus etre
                 a sec, il n'y a plus de residu a effacer avec max(), et le cash restant n'est plus
                 gele a 0 % pendant 9 ans (ce qui defavorisait le DCA, donc FLATTAIT notre these).
  BLOQUANT 3   : taux de cash par DEVISE + refus explicite si la devise n'a pas de serie.
  BLOQUANT 4   : `debut` obligatoire pour comparer des scenarios sur la MEME periode.
  IMPORTANT 6  : verification de CONTIGUITE des mois (un trou ne peut plus etre epissé en silence).
  IMPORTANT 8  : refus explicite si la serie est plus courte que l'horizon.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# UNE SEULE definition de chaque outil partage (le relecteur a attrape 2 classes
# DonneeManquante distinctes : un except sur l'une n'attrapait pas l'autre).
from build_data import DonneeManquante, horodatage

DONNEES_REELLES = True

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "resultats"
OUT.mkdir(exist_ok=True)

MARCHES = {
    "US":     ("us_tr_usd",   "usd", "S&P 500, dividendes reinvestis, en USD"),
    "US_EUR": ("us_tr_eur",   "eur", "S&P 500, dividendes reinvestis, converti en EUR"),
    "JP":     ("jp_prix_jpy", "jpy", "Nikkei 225, PRIX SEUL (sans dividendes), en yens"),
    "JP_EUR": ("jp_prix_eur", "eur", "Nikkei 225, PRIX SEUL, converti en EUR"),
}


def ecris(chemin: Path, contenu: str) -> None:
    """OneDrive tient les fichiers ouverts -> echouer BRUYAMMENT, jamais a moitie."""
    try:
        chemin.write_text(contenu, encoding="utf-8")
    except PermissionError as e:
        raise DonneeManquante(f"Ecriture refusee sur {chemin} (OneDrive ?). Fermer Excel/l'explorateur.") from e
    if not chemin.exists() or chemin.stat().st_size < len(contenu) // 2:
        raise DonneeManquante(f"Ecriture incomplete sur {chemin} (disque plein ?)")


def dca_auto_finance(c, r, dca_months: int, horizon_months: int, f: float = 1.0) -> float:
    """LA regle DCA du studio — UNE SEULE definition, partagee par tous les scripts.

    Au mois k on verse `pot / (dca_months - k)`. Le pot est donc exactement epuise a k = D-1 :
    impossible d'etre a sec, aucun residu a effacer, et le cash qui attend est VRAIMENT remunere.
    ⚠️ Consequence a dire a l'ecran : les versements ne sont PAS egaux (les interets du cash en
    attente sont reinvestis avec les versements suivants).

    c : facteurs de croissance de i+k jusqu'a la fin.  r : taux mensuel du cash.
    """
    if dca_months < 1:
        raise ValueError(f"dca_months={dca_months} : il faut au moins 1 versement.")
    if len(c) <= horizon_months or len(r) <= dca_months:
        raise ValueError(f"Series trop courtes : len(c)={len(c)}, len(r)={len(r)} "
                         f"pour dca={dca_months}, horizon={horizon_months}.")
    pot, valeur, actualise, facteur = 1.0, 0.0, 0.0, 1.0
    for k in range(dca_months):
        verse = pot / (dca_months - k)
        valeur += verse * float(c[k]) * f ** (horizon_months - k)
        actualise += verse / facteur          # versement ramene a sa valeur de t0
        pot -= verse
        facteur *= (1.0 + float(r[k + 1]))
        pot *= (1.0 + float(r[k + 1]))        # ce qui reste attend un mois de plus, au taux du cash
    # VRAI invariant : la somme des versements ACTUALISES a t0 vaut exactement le capital de depart.
    # (Verifier "pot == 0" serait un placebo : pot -= pot/1 vaut 0 par construction.)
    if abs(actualise - 1.0) > 1e-9:
        raise RuntimeError(f"Versements DCA actualises = {actualise} != 1.0 -> bug d'arithmetique, STOP.")
    return valeur


def charge() -> pd.DataFrame:
    csv = DATA / "marches.csv"
    if not csv.exists():
        raise DonneeManquante("data/marches.csv absent -> lancer build_data.py d'abord.")
    df = pd.read_csv(csv)
    df["mois"] = pd.PeriodIndex(df["mois"], freq="M")
    return df.set_index("mois").sort_index()


def _serie(df, marche: str, cash_rate: str, real: bool, debut: str | None):
    if marche not in MARCHES:
        raise ValueError(f"marche inconnu : {marche} (attendus : {list(MARCHES)})")
    col, devise, _ = MARCHES[marche]
    idx = df[col].dropna()

    if real and marche != "US":
        # Liste blanche EXPLICITE, jamais un prefixe : "US_EUR".startswith("US") vaut True,
        # et on deflaterait des euros par l'IPC americain sans que rien ne le signale.
        raise ValueError(f"real=True refuse pour {marche} : on n'a que l'IPC AMERICAIN. "
                         "Il ne deflate ni le Japon ni la zone euro.")

    if cash_rate == "zero":
        cash = pd.Series(0.0, index=idx.index)
    elif cash_rate == "taux_court":
        col_cash = f"cash_{devise}_pct"
        if col_cash not in df.columns:
            raise ValueError(f"Pas de taux court pour la devise {devise}. Refuse (jamais le T-bill US "
                             f"pour un investisseur en {devise}).")
        taux = df[col_cash].dropna()
        commun = idx.index.intersection(taux.index)
        if len(commun) < 121:
            raise DonneeManquante(
                f"Taux court {devise} : {len(commun)} mois communs avec le marche {marche}. "
                "Trop court pour un horizon de 10 ans. Utiliser cash_rate='zero' ET LE DIRE."
            )
        idx, taux = idx.loc[commun], taux.loc[commun]
        cash = (1.0 + taux / 100.0) ** (1.0 / 12.0) - 1.0
    else:
        raise ValueError(f"cash_rate inconnu : {cash_rate} (attendus : taux_court | zero)")

    if debut:
        d = pd.Period(debut, freq="M")
        if d < idx.index.min():
            raise ValueError(f"debut={debut} demande, mais {marche} commence en {idx.index.min()}.")
        idx, cash = idx.loc[idx.index >= d], cash.loc[cash.index >= d]

    if real:
        ipc = df["us_ipc"].reindex(idx.index)
        if ipc.isna().any():
            raise DonneeManquante("IPC manquant sur la periode demandee -> STOP.")
        idx = idx / ipc
        infl = ipc.pct_change()
        cash = ((1.0 + cash) / (1.0 + infl) - 1.0)
        # INVARIANT TACITE (a ne pas casser) : r[0] n'est JAMAIS consomme — le TEST A lit
        # r[1..D], et le TEST B le multiplie par une poche vide. Si un jour on reecrit le
        # TEST B en "poche = (poche + 1) * (1 + r[k])", la 1re fenetre utiliserait
        # silencieusement un mois de cash a 0 %.
        cash.iloc[0] = 0.0

    # IMPORTANT 6 : les mois doivent etre CONTIGUS. Sinon un "horizon de 120 mois"
    # couvrirait plus de 120 mois calendaires, sans que rien ne le signale.
    attendu = pd.period_range(idx.index.min(), idx.index.max(), freq="M")
    if len(idx) != len(attendu) or not idx.index.equals(attendu):
        manquants = attendu.difference(idx.index)[:5].tolist()
        raise DonneeManquante(f"Mois manquants dans {marche} : {manquants} -> STOP (jamais d'epissure silencieuse).")
    if idx.isna().any() or cash.isna().any():
        raise DonneeManquante("Trou interne dans la serie -> STOP.")
    return idx, cash


def run(df, marche="US", horizon_months=120, dca_months=12, cash_rate="taux_court",
        real=False, annual_fee=0.0, accum_months=12, debut=None) -> pd.DataFrame:
    if dca_months > horizon_months:
        raise ValueError("dca_months > horizon_months : on comparerait deux choses differentes.")
    if not 0.0 <= annual_fee < 0.1:
        raise ValueError(f"annual_fee={annual_fee} : une FRACTION (0.003 = 0,3 %), jamais un pourcentage. "
                         "Borne a 10 %/an pour attraper la coquille classique (0.3 = 30 %/an).")

    idx, cash = _serie(df, marche, cash_rate, real, debut)
    n = len(idx)
    if n <= horizon_months:
        raise DonneeManquante(f"{n} mois disponibles, {horizon_months + 1} requis pour {marche}.")

    f = (1.0 - annual_fee) ** (1.0 / 12.0) if annual_fee else 1.0
    m, lignes = idx.index, []

    for i in range(n - horizon_months):
        fin = i + horizon_months
        c = (idx.iloc[fin] / idx.iloc[i:fin + 1]).to_numpy()   # facteur de i+k -> fin
        r = cash.iloc[i:fin + 1].to_numpy()

        # ---- TEST A : capital DEJA en main = 1.0 ----
        a_lump = float(c[0]) * f ** horizon_months

        # DCA AUTO-FINANCE : au mois k on verse pot/(D-k). Le pot est exactement epuise a k=D-1.
        # -> impossible d'etre a sec, aucun residu a effacer, le cash en attente est vraiment remunere.
        a_dca = dca_auto_finance(c, r, dca_months, horizon_months, f)

        # ---- TEST B : un SALAIRE de 1.0 tombe chaque mois pendant tout l'horizon ----
        b_immediat = sum(float(c[k]) * f ** (horizon_months - k) for k in range(horizon_months))
        b_accum, poche = 0.0, 0.0
        for k in range(horizon_months):
            poche = poche * (1.0 + float(r[k])) + 1.0        # le salaire tombe, la poche dort
            if (k + 1) % accum_months == 0:                   # tous les N mois : on investit le tas
                b_accum += poche * float(c[k]) * f ** (horizon_months - k)
                poche = 0.0
        b_accum += poche                                      # reliquat jamais investi : reste du cash

        lignes.append({
            "depart": str(m[i]), "fin": str(m[fin]),
            "A_tout_d_un_coup": a_lump, "A_dca": a_dca,
            "A_ecart_pct": (a_lump / a_dca - 1.0) * 100.0,
            "B_salaire_immediat": b_immediat, "B_salaire_accumule": b_accum,
            "B_ecart_pct": (b_immediat / b_accum - 1.0) * 100.0,
        })

    res = pd.DataFrame(lignes)
    res.attrs["params"] = dict(marche=marche, horizon_months=horizon_months, dca_months=dca_months,
                               cash_rate=cash_rate, real=real, annual_fee=annual_fee,
                               accum_months=accum_months, debut=debut)
    return res


def resume(r: pd.DataFrame) -> dict:
    if r.empty:
        raise DonneeManquante("Aucune fenetre -> rien a resumer.")
    return {
        **r.attrs["params"], "fenetres": len(r),
        "periode": f"{r['depart'].iloc[0]} -> {r['fin'].iloc[-1]}",
        "A_pct_fenetres_ou_lump_gagne": round(float((r["A_ecart_pct"] > 0).mean() * 100), 1),
        "A_ecart_median_pct": round(float(r["A_ecart_pct"].median()), 2),
        "A_pire_fenetre_pour_lump_pct": round(float(r["A_ecart_pct"].min()), 2),
        "A_pire_depart": r.loc[r["A_ecart_pct"].idxmin(), "depart"],
        "A_meilleure_fenetre_pct": round(float(r["A_ecart_pct"].max()), 2),
        "B_pct_fenetres_ou_immediat_gagne": round(float((r["B_ecart_pct"] > 0).mean() * 100), 1),
        "B_ecart_median_pct": round(float(r["B_ecart_pct"].median()), 2),
        "B_pire_fenetre_pct": round(float(r["B_ecart_pct"].min()), 2),
        "B_pire_depart": r.loc[r["B_ecart_pct"].idxmin(), "depart"],
    }


# BLOQUANT 4 : chaque groupe de scenarios comparables partage EXACTEMENT la meme periode de depart.
SCENARIOS = [
    # -- Groupe US, tous bornes a 1934-01 : "cash remunere vs cash a 0 %" compare enfin une HYPOTHESE,
    #    et non 63 ans de donnees en plus.
    dict(marche="US", dca_months=12, cash_rate="taux_court", real=False, debut="1934-01"),
    dict(marche="US", dca_months=12, cash_rate="zero",       real=False, debut="1934-01"),
    dict(marche="US", dca_months=12, cash_rate="taux_court", real=True,  debut="1934-01"),
    dict(marche="US", dca_months=6,  cash_rate="taux_court", real=False, debut="1934-01"),
    dict(marche="US", dca_months=24, cash_rate="taux_court", real=False, debut="1934-01"),
    dict(marche="US", dca_months=12, cash_rate="taux_court", real=False, debut="1934-01", annual_fee=0.003),
    # -- Vue LONGUE (1871+) : cash a 0 % obligatoire (aucun taux court avant 1934). Periode DIFFERENTE :
    #    a ne JAMAIS comparer aux lignes ci-dessus.
    dict(marche="US", dca_months=12, cash_rate="zero",       real=False, debut=None),
    # -- L'investisseur en EUROS (1999+ : l'euro n'existe pas avant)
    dict(marche="US_EUR", dca_months=12, cash_rate="taux_court", real=False, debut=None),
    # -- Le TEMOIN japonais (biais de survie). Cash a 0 % : pas de taux court avant 2002.
    dict(marche="JP",     dca_months=12, cash_rate="zero",       real=False, debut=None),
    dict(marche="JP_EUR", dca_months=12, cash_rate="taux_court", real=False, debut=None),
]


def main():
    df = charge()
    tous = []
    for s in SCENARIOS:
        r = run(df, horizon_months=120, **s)
        nom = (f"{s['marche']}_dca{s['dca_months']}_{s['cash_rate']}"
               f"_{'reel' if s['real'] else 'nominal'}"
               f"{'_frais' if s.get('annual_fee') else ''}"
               f"_{s['debut'] or 'tout'}")
        r.to_csv(OUT / f"resultats_{nom}.csv", index=False)
        res = resume(r)
        res["fichier"] = f"resultats_{nom}.csv"
        tous.append(res)
        print(f"\n=== {nom}  ({res['fenetres']} fenetres, {res['periode']}) ===")
        print(f"  A  tout-d'un-coup > DCA dans {res['A_pct_fenetres_ou_lump_gagne']} % des fenetres"
              f" | median +{res['A_ecart_median_pct']} %"
              f" | PIRE {res['A_pire_fenetre_pour_lump_pct']} % (depart {res['A_pire_depart']})")
        print(f"  B  salaire investi TOUT DE SUITE > accumule {s.get('accum_months', 12)} mois dans "
              f"{res['B_pct_fenetres_ou_immediat_gagne']} % des fenetres"
              f" | median +{res['B_ecart_median_pct']} %"
              f" | PIRE {res['B_pire_fenetre_pct']} % (depart {res['B_pire_depart']})")

    synthese = {
        "genere_le": horodatage(),
        "donnees_reelles": True,
        "avertissement": "Un backtest MESURE LE PASSE. Il ne predit RIEN sur le futur.",
        "A_LIRE_AVANT_DE_CITER_UN_CHIFFRE": {
            "la_ligne_reel_ne_prouve_RIEN": "L'ecart du TEST A est MATHEMATIQUEMENT INVARIANT au "
                "deflateur : l'inflation se simplifie dans le ratio lump/DCA. Les chiffres A de la "
                "ligne real=true sont donc IDENTIQUES a la ligne nominale — c'est une identite "
                "algebrique, PAS une verification independante. INTERDIT de dire a l'ecran "
                "'et meme en reel, on retrouve le meme resultat'. Seul le TEST B bouge en reel "
                "(et il suppose alors un salaire parfaitement indexe sur l'inflation).",
            "le_DCA_n_est_PAS_12_versements_egaux": "Le cash en attente est REMUNERE et ses interets "
                "sont reinvestis avec les versements suivants : le 12e versement est donc plus gros "
                "que le 1er (en 1981, ~14 % de plus). Qui reproduirait avec la regle naive "
                "'12 x 833 EUR' ne retrouverait PAS nos chiffres. A dire si on decrit la methode.",
            "le_TEST_B_ne_depend_PAS_de_dca_months": "Les lignes dca6 / dca12 / dca24 affichent le "
                "MEME B (86,7 % / +3,52 % / -4,92 %) parce que le TEST B ne fait pas intervenir "
                "dca_months : c'est UN SEUL calcul repete, pas trois mesures. INTERDIT de "
                "presenter ces 3 lignes comme une confirmation. Seul le TEST A y varie.",
            "periodes_non_comparables": "Ne JAMAIS comparer deux lignes dont le champ 'periode' "
                "differe : on comparerait des donnees, pas une hypothese.",
            "pourquoi_les_lignes_EUR_s_arretent_en_2026-01": "La serie du taux court zone euro "
                "(OCDE via FRED) s'arrete en 2026-01. US_EUR et JP_EUR s'arretent donc 5 mois "
                "plus tot que les lignes USD. Ce n'est pas un choix editorial, c'est la donnee.",
            "A_ecart_pct_n_est_PAS_une_perte": "A_ecart_pct est l'ecart RELATIF entre DEUX "
                "STRATEGIES. '-29,35 %' ne veut PAS dire 'on perd 29 %' : ca veut dire que le "
                "tout-d'un-coup finit 29 % en dessous du DCA. A dire autrement a l'ecran.",
            "JP_EUR_est_une_mesure_GROSSIERE": "jp_prix_eur melange un cours de FIN de mois "
                "(Nikkei) et des taux de change en MOYENNE mensuelle (FRED). Le bruit ainsi cree "
                "est du meme ordre que l'ecart median mesure (0,5 %). Dire 'quasiment 50/50', "
                "JAMAIS '51,2 %'.",
        },
        "scenarios": tous,
    }
    ecris(OUT / "synthese.json", json.dumps(synthese, indent=2, ensure_ascii=False))
    print(f"\nOK -> {OUT}/synthese.json  ({len(tous)} scenarios)")


if __name__ == "__main__":
    main()
