#!/usr/bin/env python3
"""Constructeur du jeu de donnees du backtest Pilote Finance.

ANTI-FICTION : ce script ne FABRIQUE aucune donnee. Il telecharge des series
reelles, les trace (source + URL + date de telechargement) et ECHOUE BRUYAMMENT
si une donnee manque. Un trou = un STOP, jamais un zero.

Contrat : CONTRAT_backtest.md (redige AVANT ce code).
Sorties  : data/marches.csv + data/metadata.json (le CSV sans le JSON est inutilisable).

v2 — 13/07/2026, apres gate code-reviewer (verdict STOP). Corriges :
  - ffill(limit=3) sur les dividendes : SUPPRIME (il inventait jusqu'a 3 mois de dividendes 2026).
  - fillna(0.0) sur les rendements : SUPPRIME (un dividende manquant devenait un mois de marche a +0,00 %).
  - Taux de cash par DEVISE (un investisseur japonais n'est pas remunere au bon du Tresor americain).
  - Retry reseau + PermissionError explicite + relecture des DEUX sorties.
"""
from __future__ import annotations

import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

DONNEES_REELLES = True  # regle code.md §6 : jamais de valeur inventee

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # panne #8 : cp1252 sous Windows

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DATA.mkdir(exist_ok=True)

TIMEOUT = 90
UA = {"User-Agent": "PiloteFinance-backtest/1.0 (recherche editoriale, donnees publiques)"}

SHILLER_URL = (
    "https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/"
    "downloads/165d8a6e-26bf-44ec-a26c-a35f7f993480/ie_data.xls"
)
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


class DonneeManquante(RuntimeError):
    """Une donnee attendue est absente. On s'arrete. On n'invente pas."""


def telecharge(url: str, minimum_octets: int, essais: int = 3) -> bytes:
    """Panne #1/#7 : reseau coupe, 503 FRED, blip CDN -> 3 tentatives, puis STOP parlant."""
    derniere = None
    for n in range(1, essais + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
            r.raise_for_status()
            if len(r.content) < minimum_octets:   # panne #4 : fichier tronque / 0 octet
                raise DonneeManquante(f"Fichier trop petit ({len(r.content)} o < {minimum_octets} o)")
            return r.content
        except Exception as e:  # noqa: BLE001 - on veut vraiment tout retenter puis relancer
            derniere = e
            if n < essais:
                print(f"    tentative {n}/{essais} echouee ({e}) - nouvel essai dans {2 * n} s")
                time.sleep(2 * n)
    raise DonneeManquante(f"Echec apres {essais} tentatives sur {url} : {derniere}")


def charge_shiller() -> pd.DataFrame:
    """S&P 500 mensuel : prix, dividendes, IPC. 1871 -> aujourd'hui.

    BIAIS DECLARE : les prix Shiller sont des MOYENNES MENSUELLES de cours
    quotidiens -> ils LISSENT les krachs. Effet mesure : mesure_biais_lissage.py.
    """
    df = pd.read_excel(io.BytesIO(telecharge(SHILLER_URL, 500_000)), sheet_name="Data", header=7)

    if not {"Date", "P", "D", "CPI"}.issubset(df.columns):   # panne #5 : en-tete qui bouge
        raise DonneeManquante(
            f"En-tete Shiller inattendu (header=7 ne colle plus). Colonnes : {list(df.columns)[:15]}"
        )

    df = df[["Date", "P", "D", "CPI"]].dropna(subset=["Date"]).copy()

    def _en_mois(v):
        # Panne #6 : "2026.1" = OCTOBRE, pas janvier. On passe par la chaine, jamais par le float.
        an, mois = f"{float(v):.2f}".split(".")
        m = int(mois)
        return pd.Period(f"{an}-{m:02d}", freq="M") if 1 <= m <= 12 else None

    df["mois"] = df["Date"].map(_en_mois)
    df = df.dropna(subset=["mois"])
    for c in ("P", "D", "CPI"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.set_index("mois").sort_index()[["P", "D", "CPI"]]

    # Panne #2 : l'URL Yale que tout le monde cite s'arrete en sept. 2023.
    if df.index.max() < pd.Period("2025-01", freq="M"):
        raise DonneeManquante(
            f"Shiller s'arrete en {df.index.max()} : c'est le fichier PERIME (piege de l'URL Yale). "
            "Reprendre le lien depuis shillerdata.com."
        )
    return df


def charge_fred(sid: str, mini_lignes: int) -> pd.Series:
    df = pd.read_csv(io.BytesIO(telecharge(FRED.format(sid=sid), 1_000)))
    if df.shape[1] != 2:
        raise DonneeManquante(f"FRED {sid} : format inattendu ({list(df.columns)})")
    df.columns = ["date", "valeur"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce")  # panne #3 : FRED ecrit "."
    df = df.dropna()
    if len(df) < mini_lignes:
        raise DonneeManquante(f"FRED {sid} : {len(df)} lignes < {mini_lignes} attendues")
    s = df.set_index(df["date"].dt.to_period("M"))["valeur"]
    s = s.groupby(level=0).last()   # quotidien -> DERNIER cours du mois (pas une moyenne)
    # Le mois calendaire EN COURS est incomplet : ce n'est pas une cloture mensuelle.
    # On l'ECARTE plutot que de le faire passer pour un mois plein.
    return s[s.index < mois_en_cours()]


def mois_en_cours() -> pd.Period:
    """Le mois calendaire courant n'est PAS clos : ce n'est pas une cloture mensuelle."""
    return pd.Timestamp.today().to_period("M")


def _ecris(chemin: Path, contenu: str) -> None:
    """Panne #10 : OneDrive verrouille / disque plein -> echouer BRUYAMMENT, jamais a moitie."""
    try:
        chemin.write_text(contenu, encoding="utf-8")
    except PermissionError as e:
        raise DonneeManquante(
            f"Ecriture refusee sur {chemin} (OneDrive tient le fichier ouvert ?). Fermer Excel/l'explorateur."
        ) from e
    if not chemin.exists() or chemin.stat().st_size < len(contenu) // 2:
        raise DonneeManquante(f"Ecriture incomplete sur {chemin} (disque plein ?)")


def horodatage() -> str:
    """datetime.UTC n'existe qu'a partir de Python 3.11 -> on garde timezone.utc (portable)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")  # noqa: UP017
def main() -> int:
    if not DONNEES_REELLES:
        raise SystemExit("DONNEES_REELLES=False : refus de produire quoi que ce soit.")

    print("1/7 Shiller (S&P 500 + dividendes + IPC)...")
    sh = charge_shiller()
    print(f"    {sh.index.min()} -> {sh.index.max()}  ({len(sh)} mois)")

    print("2/7 FRED TB3MS  — bon du Tresor US 3 mois (le cash en DOLLARS)...")
    cash_usd = charge_fred("TB3MS", 900)
    print("3/7 FRED IR3TIB01EZM156N — taux 3 mois zone EURO (le cash en EUROS)...")
    cash_eur = charge_fred("IR3TIB01EZM156N", 300)
    print("4/7 FRED IR3TIB01JPM156N — taux 3 mois JAPON (le cash en YENS ; 2002+ SEULEMENT)...")
    cash_jpy = charge_fred("IR3TIB01JPM156N", 200)

    print("5/7 FRED EXUSEU (USD par EUR — l'euro n'existe qu'a partir de 1999)...")
    usd_par_eur = charge_fred("EXUSEU", 300)
    print("6/7 FRED NIKKEI225 (marche temoin — PRIX SEUL, sans dividendes)...")
    nikkei = charge_fred("NIKKEI225", 10_000)
    print("7/7 FRED EXJPUS (yens par USD)...")
    jpy_par_usd = charge_fred("EXJPUS", 500)

    # ---- Indice de rendement TOTAL US (dividendes reinvestis), en USD ----
    # AUCUN ffill, AUCUN fillna : un dividende manquant est un STOP, pas un zero.
    p, d = sh["P"], sh["D"]
    complet = p.notna() & d.notna() & sh["CPI"].notna()
    dernier_complet = complet[complet].index.max()
    base = sh.loc[:dernier_complet]
    if base[["P", "D", "CPI"]].isna().any().any():
        trous = base[base[["P", "D", "CPI"]].isna().any(axis=1)].index.tolist()
        raise DonneeManquante(f"Trou interne dans Shiller (P/D/CPI) : {trous[:5]} -> STOP, on n'invente pas.")

    rendement = (base["P"] + base["D"] / 12.0) / base["P"].shift(1) - 1.0
    rendement = rendement.iloc[1:]                      # 1re ligne : pas de mois precedent, on la RETIRE
    if rendement.isna().any():
        raise DonneeManquante("Rendement US non calculable sur certains mois -> STOP.")
    tr_us = (1.0 + rendement).cumprod()
    print(f"    S&P 500 rendement total : {tr_us.index.min()} -> {tr_us.index.max()} "
          f"(les mois 2026 sans dividende publie sont ECARTES, pas inventes)")

    tr_jp = nikkei / nikkei.iloc[0]   # PRIX SEUL. On ne fabrique pas de dividendes japonais.

    idx = pd.PeriodIndex(sorted(set(tr_us.index) | set(nikkei.index)), freq="M")
    out = pd.DataFrame(index=idx)
    out["us_tr_usd"] = tr_us
    out["us_ipc"] = sh["CPI"]
    out["jp_prix_jpy"] = tr_jp
    out["usd_par_eur"] = usd_par_eur          # VIDE avant 1999 : assume, pas rempli
    out["jpy_par_usd"] = jpy_par_usd
    out["cash_usd_pct"] = cash_usd
    out["cash_eur_pct"] = cash_eur
    out["cash_jpy_pct"] = cash_jpy
    out["us_tr_eur"] = out["us_tr_usd"] / out["usd_par_eur"]
    out["jp_prix_eur"] = out["jp_prix_jpy"] / out["jpy_par_usd"] / out["usd_par_eur"]
    out = out.sort_index()
    out.index.name = "mois"

    csv = DATA / "marches.csv"
    _ecris(csv, out.to_csv())
    if len(pd.read_csv(csv)) != len(out):
        raise DonneeManquante("Relecture du CSV incoherente -> STOP.")

    meta = {
        "genere_le": horodatage(),
        "donnees_reelles": True,
        "avertissement": "Un backtest MESURE LE PASSE. Il ne predit RIEN sur le futur.",
        "aucune_donnee_inventee": "Aucun ffill, aucun fillna. Un trou = une exception, jamais un zero.",
        "series": {
            "us_tr_usd": {
                "quoi": "S&P 500, rendement TOTAL (dividendes reinvestis), USD, nominal",
                "source": "Robert Shiller, ie_data.xls", "url": "https://shillerdata.com/",
                "periode": f"{tr_us.index.min()} -> {tr_us.index.max()}",
                "granularite": "mensuelle",
                "BIAIS_DECLARE": "Prix = MOYENNES MENSUELLES de cours quotidiens : ca LISSE les "
                                 "krachs. Effet MESURE (pas suppose) : resultats/biais_lissage.json.",
            },
            "us_ipc": {"quoi": "Indice des prix US (rendement REEL)", "source": "Shiller / BLS CPI-U",
                       "url": "https://shillerdata.com/"},
            "jp_prix_jpy": {
                "quoi": "Nikkei 225, PRIX SEUL, en yens", "source": "FRED (Nikkei Inc.)",
                "url": "https://fred.stlouisfed.org/series/NIKKEI225",
                "periode": f"{nikkei.index.min()} -> {nikkei.index.max()}",
                "granularite": "dernier cours du mois (pas une moyenne)",
                "BIAIS_DECLARE": "SANS DIVIDENDES -> le Japon est SOUS-ESTIME. A dire a l'ecran.",
                "pourquoi": "Marche temoin contre le biais de survie : ne tester que les USA, "
                            "c'est choisir le marche le plus performant du siecle.",
            },
            "cash_usd_pct": {"quoi": "Le cash qui ATTEND, en dollars — bon du Tresor 3 mois",
                             "source": "FRED TB3MS", "url": "https://fred.stlouisfed.org/series/TB3MS",
                             "periode": f"{cash_usd.index.min()} -> {cash_usd.index.max()}"},
            "cash_eur_pct": {"quoi": "Le cash qui ATTEND, en euros — taux interbancaire 3 mois zone euro",
                             "source": "FRED IR3TIB01EZM156N",
                             "url": "https://fred.stlouisfed.org/series/IR3TIB01EZM156N",
                             "periode": f"{cash_eur.index.min()} -> {cash_eur.index.max()}"},
            "cash_jpy_pct": {"quoi": "Le cash qui ATTEND, en yens — taux interbancaire 3 mois",
                             "source": "FRED IR3TIB01JPM156N",
                             "url": "https://fred.stlouisfed.org/series/IR3TIB01JPM156N",
                             "periode": f"{cash_jpy.index.min()} -> {cash_jpy.index.max()}",
                             "LIMITE_ASSUMEE": "Commence en 2002 : ne couvre PAS le krach japonais de "
                                               "1990. Le scenario Japon long tourne donc avec le cash a "
                                               "0 %, ce qui DEFAVORISE le DCA japonais -> notre chiffre "
                                               "japonais pour le 'tout d'un coup' est un PLAFOND. Dit a l'ecran."},
            "usd_par_eur": {"quoi": "USD par EUR", "source": "FRED EXUSEU",
                            "url": "https://fred.stlouisfed.org/series/EXUSEU",
                            "periode": f"{usd_par_eur.index.min()} -> {usd_par_eur.index.max()}",
                            "LIMITE_ASSUMEE": "L'EURO N'EXISTE PAS AVANT 1999. Aucun euro synthetique "
                                              "fabrique : les colonnes EUR sont VIDES avant 1999."},
            "jpy_par_usd": {"quoi": "Yens par USD", "source": "FRED EXJPUS",
                            "url": "https://fred.stlouisfed.org/series/EXJPUS"},
            "us_tr_eur": {
                "quoi": "SERIE DERIVEE — S&P 500 rendement total, vu par un investisseur en EUROS",
                "calcul": "us_tr_usd / usd_par_eur",
                "sources": ["Shiller ie_data.xls", "FRED EXUSEU"],
                "LIMITE_ASSUMEE": "Commence en 1999-01 : avant, l'euro n'existe pas. Aucun ECU "
                                  "synthetique n'est fabrique.",
                "pourquoi": "L'effet de change peut peser autant que le marche lui-meme. Un Francais "
                            "qui achete du S&P 500 n'obtient PAS le rendement du S&P 500.",
            },
            "jp_prix_eur": {
                "quoi": "SERIE DERIVEE — Nikkei 225 (PRIX SEUL), vu par un investisseur en EUROS",
                "calcul": "jp_prix_jpy / jpy_par_usd / usd_par_eur  (yen -> dollar -> euro)",
                "sources": ["FRED NIKKEI225", "FRED EXJPUS", "FRED EXUSEU"],
                "LIMITE_ASSUMEE": "1999+ (euro) ET sans dividendes (Nikkei prix seul) : DOUBLE "
                                  "sous-estimation du Japon. A dire a l'ecran.",
            },
        },
    }
    _ecris(DATA / "metadata.json", json.dumps(meta, indent=2, ensure_ascii=False))
    json.loads((DATA / "metadata.json").read_text("utf-8"))   # on relit AUSSI le JSON

    print(f"\nOK -> {csv} ({len(out)} mois)")
    print(f"OK -> {DATA / 'metadata.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
