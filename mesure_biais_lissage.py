#!/usr/bin/env python3
"""COMBIEN vaut le biais de lissage de Shiller ? On le MESURE, on ne le suppose pas.

Shiller donne des MOYENNES MENSUELLES de cours quotidiens. Une moyenne efface le creux
d'un krach. Tout le monde ecrit « attention, ca lisse » en note de bas de page et passe
a la suite. Nous, on le chiffre.

Methode : sur le Nikkei (le seul marche dont on a le QUOTIDIEN sur 77 ans), on construit
DEUX series du MEME marche, MEME periode, MEME regle :
  (1) cours de FIN DE MOIS      -> la verite
  (2) MOYENNE des cours du mois -> la methode Shiller
Cash a 0 % dans les deux cas : une seule variable change, la granularite. L'ecart = le biais.

⚠️ RESULTAT CONTRE-INTUITIF (13/07/2026) : le biais est MIXTE, pas unidirectionnel.
Le lissage gonfle le TAUX DE VICTOIRE du tout-d'un-coup, mais REDUIT son ecart median.
On ne peut donc PAS dire a l'ecran « le lissage flatte notre these ». Il faut donner les deux.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd
from build_data import DonneeManquante, horodatage, mois_en_cours, telecharge

from backtest import dca_auto_finance, ecris  # UNE SEULE regle DCA dans tout le module

DONNEES_REELLES = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
OUT = HERE / "resultats"
OUT.mkdir(exist_ok=True)          # ne depend plus de backtest.py

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NIKKEI225"


def charge_nikkei_quotidien() -> pd.DataFrame:
    """Meme telechargement que build_data (retry compris) — pas une 2e implementation."""
    d = pd.read_csv(io.BytesIO(telecharge(URL, 1_000)))
    if d.shape[1] != 2:
        raise DonneeManquante(f"FRED NIKKEI225 : format inattendu ({list(d.columns)})")
    d.columns = ["date", "v"]
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["v"] = pd.to_numeric(d["v"], errors="coerce")
    d = d.dropna()
    if len(d) < 10_000:
        raise DonneeManquante(f"NIKKEI225 : {len(d)} lignes, trop peu.")
    d["mois"] = d["date"].dt.to_period("M")
    # ⚠️ LE BUG ATTRAPE PAR LA 3e RELECTURE : sans cette ligne, le mois calendaire EN COURS
    # (incomplet, ~8 seances) entrait ici alors que build_data l'ecartait -> le module publiait
    # DEUX chiffres differents pour la MEME mesure (807 fenetres ici, 806 dans synthese.json).
    return d[d["mois"] < mois_en_cours()]


def test_A(idx: pd.Series, horizon: int = 120, dca: int = 12) -> dict:
    """EXACTEMENT la regle de backtest.py (fonction importee, pas recopiee), cash a 0 %."""
    n, ecarts = len(idx), []
    zero = [0.0] * (horizon + 1)          # cash a 0 % : on isole STRICTEMENT la granularite
    for i in range(n - horizon):
        c = (idx.iloc[i + horizon] / idx.iloc[i:i + horizon + 1]).to_numpy()
        lump = float(c[0])
        dca_v = dca_auto_finance(c, zero, dca, horizon)
        ecarts.append((lump / dca_v - 1.0) * 100.0)
    s = pd.Series(ecarts)
    return {"fenetres": len(s), "pct_lump_gagne": round(float((s > 0).mean() * 100), 1),
            "ecart_median_pct": round(float(s.median()), 2),
            "pire_fenetre_pct": round(float(s.min()), 2)}


def main() -> int:
    d = charge_nikkei_quotidien()
    fin_de_mois = d.groupby("mois")["v"].last()    # la verite
    moyenne_mois = d.groupby("mois")["v"].mean()   # la methode Shiller
    commun = fin_de_mois.index

    # Vrai controle (l'ancien `intersection` etait un placebo : meme groupby des deux cotes).
    attendu = pd.period_range(commun.min(), commun.max(), freq="M")
    if not commun.equals(attendu):
        raise DonneeManquante(f"Mois manquants dans le Nikkei : {attendu.difference(commun)[:5].tolist()} -> STOP.")

    a = test_A(fin_de_mois.loc[commun])
    b = test_A(moyenne_mois.loc[commun])
    d_taux = round(b["pct_lump_gagne"] - a["pct_lump_gagne"], 1)
    d_med = round(b["ecart_median_pct"] - a["ecart_median_pct"], 2)

    print(f"Nikkei 225 — meme marche, meme periode ({commun.min()} -> {commun.max()}), meme regle,")
    print("cash a 0 %. UNE SEULE chose change : la granularite.\n")
    print(f"  FIN DE MOIS (la verite)         : le tout-d'un-coup gagne {a['pct_lump_gagne']} % des fenetres"
          f" | median +{a['ecart_median_pct']} % | pire {a['pire_fenetre_pct']} %")
    print(f"  MOYENNE du mois (methode Shiller): le tout-d'un-coup gagne {b['pct_lump_gagne']} % des fenetres"
          f" | median +{b['ecart_median_pct']} % | pire {b['pire_fenetre_pct']} %")
    print(f"\n  >>> BIAIS MESURE : {d_taux:+} pt sur le taux de victoire, {d_med:+} pt sur l'ecart median.")
    print("      Le biais est MIXTE. Interdit de dire 'le lissage flatte notre these' : donner LES DEUX.")

    out = {
        "genere_le": horodatage(),
        "donnees_reelles": True,
        "quoi": "Effet MESURE du lissage mensuel (methode Shiller) sur le resultat DCA vs tout d'un coup",
        "marche": "Nikkei 225 — seul marche dont on a le quotidien sur longue periode",
        "source": "FRED (Nikkei Inc.)", "url": "https://fred.stlouisfed.org/series/NIKKEI225",
        "periode": f"{commun.min()} -> {commun.max()}",
        "protocole": "Meme marche, meme periode, meme regle, cash a 0 %. Seule variable : la granularite.",
        "fin_de_mois_LA_VERITE": a,
        "moyenne_du_mois_METHODE_SHILLER": b,
        "biais_pts_taux_de_victoire": d_taux,
        "biais_pts_ecart_median": d_med,
        "LECTURE": "Le biais est MIXTE, pas unidirectionnel : le lissage gonfle le taux de victoire du "
                   "tout-d'un-coup mais REDUIT son ecart median. On ne peut pas dire 'ca flatte notre "
                   "these'. A l'ecran : donner les deux chiffres.",
        "LIMITE": "Biais mesure sur le NIKKEI. Ce n'est pas mecaniquement sa valeur sur le S&P 500.",
        "COHERENCE": "La ligne 'fin_de_mois' DOIT reproduire exactement le scenario JP de "
                     "synthese.json (memes fenetres, meme mediane). Si ce n'est pas le cas, "
                     "les deux fichiers ne parlent pas des memes donnees -> STOP.",
    }
    ecris(OUT / "biais_lissage.json", json.dumps(out, indent=2, ensure_ascii=False))
    print("\nOK -> resultats/biais_lissage.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
