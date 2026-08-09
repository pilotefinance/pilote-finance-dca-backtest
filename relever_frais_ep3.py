#!/usr/bin/env python3
# relever_frais_ep3.py — LE RELEVE de l'episode 3 « ETF ». Extraction DETERMINISTE, zero modele.
#
# Pourquoi ce script existe plutot qu'un copier-coller : point IMPORTANT du Gardien conformite
# (05/08/2026) — « aucun chiffre de frais produit ou "verifie" par un modele : extraction
# deterministe depuis le PDF public, avec la page ». Un chiffre lu par un modele est un chiffre
# qu'on ne peut pas rejouer. Ici, `python relever_frais_ep3.py` redonne exactement le meme JSON,
# et l'empreinte SHA-256 du PDF prouve qu'on a lu le meme document.
#
# CE QU'IL RELEVE — et RIEN d'autre (tables autorisees figees dans `DEFINITION_FRAIS_ep3.md`,
# ecrit AVANT ce script) :
#   Table MR-CP.14, page 18 — « UCITS costs and net performance by management type »
#   Section « Equity UCITS », ligne « Ongoing costs », annee la plus recente, horizon 1 an.
#   Trois categories que le rapport distingue lui-meme : Active funds · Passive funds · ETFs.
#
# ---------------------------------------------------------------------------
# CE QUI A FAILLI PASSER (relecture code-reviewer, 06/08/2026 — 2e passe)
# ---------------------------------------------------------------------------
# La v1 de ce script lisait les six nombres d'une ligne et leur collait les etiquettes
# « actif / passif / ETF » DANS L'ORDRE, sans jamais lire l'en-tete des colonnes. Sur une page ou
# l'ordre des colonnes serait inverse, il rendait un FEU VERT en etiquetant 0,21 % « gestion
# active » et 1,28 % « ETF ». Chiffre plausible, etiquette fausse, aucun refus — le pire cas
# imaginable pour une chaine anti-fiction, sur le chiffre meme qui part a l'ecran.
# D'ou `RE_ENTETE` : l'ordre des colonnes est VERIFIE dans le document avant toute lecture.
# De meme, une ligne d'annee incomplete etait silencieusement IGNOREE, et le script repliait sur
# l'annee precedente sans le dire. Desormais : toute annee vue mais non lisible = STOP.
#
# ---------------------------------------------------------------------------
# LA REGLE DE SELECTION DES BORNES — mecanique, figee AVANT de regarder les valeurs
# ---------------------------------------------------------------------------
#   borne basse = la PLUS BASSE des trois · borne haute = la PLUS HAUTE des trois.
# Aucun choix humain, donc aucun cherry-picking possible. Les trois valeurs sont publiees, pas
# seulement les deux retenues (protocole LR4 cond.2 : on publie la grille entiere).
#
# Horizon 1 an et non 10 ans : le 1 an est le taux de frais CONSTATE sur l'annee, le 10 ans est
# une moyenne geometrique qui melange des annees anciennes. Choix justifie avant lecture, et les
# valeurs 10 ans sont relevees quand meme, pour que personne n'ait a nous croire.
#
# CONTRAT
#   relever(pdf, date_releve, accepter_nouvelle_empreinte=False) -> dict
#     Leve ReleveImpossible si : la page 18 ne porte pas la table attendue · l'en-tete des
#     colonnes n'est pas celui attendu, dans l'ordre attendu · une annee est presente mais
#     illisible · une valeur sort de [0 ; 10] points · l'empreinte du PDF a change.
#     Leve PdfIllisible si le fichier n'est pas un PDF exploitable.
#     Le script s'ARRETE : il ne devine jamais un chiffre absent.
#
# Usage : python relever_frais_ep3.py [--pdf X] [--sortie Y] [--date-releve AAAA-MM-JJ]
#                                     [--accepter-nouvelle-empreinte]
# Retour 0 = releve ecrit · 1 = releve impossible (structure ou document non conforme) ·
#        2 = mauvais usage ou PDF illisible · 3 = ecriture impossible.
"""Releve deterministe des frais courants publies par l'ESMA — ep. 3."""
from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import json
import pathlib
import re
import sys

with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL_PDF = (
    "https://www.esma.europa.eu/sites/default/files/2026-03/"
    "ESMA50-1949966494-4065_Market_Report_-_Costs_and_Performance_of_EU_Retail_"
    "Investment_Products.pdf"
)
PDF_DEFAUT = pathlib.Path("sources_ep3/ESMA50-1949966494-4065.pdf")
# Empreinte du document reellement lu le 06/08/2026. Si elle change, le rapport a ete remplace :
# le releve S'ARRETE. Il ne reprend qu'avec --accepter-nouvelle-empreinte ET une nouvelle date.
SHA256_ATTENDU = "0f87b0efc3b57765b42c44611cdd667853c44c981d915a5a4c12630f3041e68e"

PAGE_TABLE = 18  # page imprimee ET index PDF : ils coincident dans ce document (verifie).
TITRE_TABLE = "UCITS costs and net performance by management type"
CODE_TABLE = "MR-CP.14"
# L'ordre des colonnes, LU DANS LE DOCUMENT et non suppose. C'est le garde-fou n°1.
RE_ENTETE = re.compile(
    r"Active funds\s+Passive funds\s+ETFs\s+1Y\s+10Y\s+1Y\s+10Y\s+1Y\s+10Y"
)
CATEGORIES = (
    ("actif", "UCITS actions — gestion active"),
    ("passif_non_etf", "UCITS actions — gestion passive hors ETF"),
    ("etf", "UCITS actions — ETF"),
)
DEFINITION = "ongoing_costs_esma"
SOURCE = "ESMA Market Report — Costs and Performance of EU Retail Investment Products 2025"
FRAIS_MAX_POINTS = 10.0  # meme contrat que le moteur : au-dela, ce n'est pas un frais courant.

# Une ligne d'annee de la table : « 2024 1.28 1.39 0.22 0.28 0.21 0.26 »
#   -> Active 1Y, Active 10Y, Passive 1Y, Passive 10Y, ETF 1Y, ETF 10Y
RE_LIGNE_ANNEE = re.compile(r"^(20\d{2})((?:\s+\d+\.\d+){6})\s*$")
RE_DEBUT_ANNEE = re.compile(r"^(20\d{2})\b")


class ReleveImpossible(Exception):
    """La page ne contient pas ce que le protocole a decrit : on s'arrete, on ne devine pas."""


class PdfIllisible(Exception):
    """Le fichier n'est pas un PDF exploitable : panne technique, pas un probleme de structure."""


def _texte_page(pdf: pathlib.Path, numero: int) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depend de l'environnement
        raise PdfIllisible(
            "pypdf est absent : `pip install pypdf`. Le relevé ne se fait pas à la main."
        ) from exc
    try:
        lecteur = PdfReader(str(pdf))
        nb_pages = len(lecteur.pages)
    except Exception as exc:  # pypdf leve des exceptions maison (fichier tronque, chiffre…)
        raise PdfIllisible(f"PDF illisible ({pdf}) : {exc}") from exc
    if numero > nb_pages:
        raise ReleveImpossible(
            f"le PDF ne compte que {nb_pages} pages : la page {numero} n'existe pas. "
            "Le rapport a changé : refais le relevé, ne l'adapte pas au hasard."
        )
    try:
        return lecteur.pages[numero - 1].extract_text() or ""
    except Exception as exc:
        raise PdfIllisible(f"extraction de la page {numero} impossible : {exc}") from exc


def _bloc_actions(compact: str) -> str:
    """Isole la section « Equity UCITS » de la ligne « Ongoing costs ». Rien d'autre."""
    if CODE_TABLE not in compact or TITRE_TABLE not in re.sub(r"\s+", " ", compact):
        raise ReleveImpossible(
            f"page {PAGE_TABLE} : table « {CODE_TABLE} — {TITRE_TABLE} » introuvable. "
            "Le rapport a changé de pagination : refais le relevé, ne l'adapte pas au hasard."
        )
    debut_table = compact.find(CODE_TABLE)
    debut_couts = compact.find("Ongoing costs", debut_table)
    if debut_couts < 0:
        raise ReleveImpossible(f"page {PAGE_TABLE} : ligne « Ongoing costs » introuvable.")
    # GARDE-FOU N°1 : l'ordre des colonnes est lu, jamais suppose.
    if not RE_ENTETE.search(compact[debut_table:debut_couts]):
        raise ReleveImpossible(
            f"page {PAGE_TABLE} : l'en-tête des colonnes attendu (« Active funds · Passive "
            "funds · ETFs », puis « 1Y 10Y » trois fois) est absent ou dans un autre ordre. "
            "Sans lui, associer un chiffre à une catégorie serait une supposition."
        )
    debut_actions = compact.find("Equity UCITS", debut_couts)
    if debut_actions < 0:
        raise ReleveImpossible(
            f"page {PAGE_TABLE} : section « Equity UCITS » des coûts courants introuvable."
        )
    # La section s'arrete au premier changement de bloc : « Bond UCITS » (autre classe d'actifs)
    # ou « Net performance » (autre grandeur — ses lignes d'annees ont EXACTEMENT le meme format
    # et vaudraient des « frais courants » a 21,4 %).
    fins = [
        i
        for i in (compact.find("Bond UCITS", debut_actions), compact.find("Net performance", debut_actions))
        if i > 0
    ]
    if not fins:
        raise ReleveImpossible(
            f"page {PAGE_TABLE} : fin de la section « Equity UCITS » introuvable — impossible "
            "de garantir que les lignes lues sont bien des frais courants d'actions."
        )
    return compact[debut_actions : min(fins)]


def _lignes_par_annee(bloc: str) -> dict[int, list[float]]:
    """Lit les lignes d'annee. Toute annee VUE mais illisible fait STOPper (jamais de repli)."""
    lignes: dict[int, list[float]] = {}
    vues: set[int] = set()
    for brute in bloc.splitlines():
        ligne = brute.strip()
        debut = RE_DEBUT_ANNEE.match(ligne)
        if not debut:
            continue
        vues.add(int(debut.group(1)))
        complete = RE_LIGNE_ANNEE.match(ligne)
        if complete:
            lignes[int(complete.group(1))] = [float(v) for v in complete.group(2).split()]
    if not lignes:
        raise ReleveImpossible(
            f"page {PAGE_TABLE} : aucune ligne d'année exploitable dans « Equity UCITS ». "
            "La structure du tableau a changé."
        )
    # GARDE-FOU N°2 : sans ça, une colonne disparue faisait replier sur l'annee precedente, en
    # silence, avec un FEU VERT.
    incompletes = sorted(vues - set(lignes))
    if incompletes:
        raise ReleveImpossible(
            f"page {PAGE_TABLE} : année(s) {incompletes} présente(s) mais illisible(s) (six "
            "valeurs attendues). Une colonne a disparu ou le tableau a changé — on ne se replie "
            "pas sur l'année précédente."
        )
    return lignes


def relever(
    pdf: pathlib.Path,
    date_releve: str | None = None,
    accepter_nouvelle_empreinte: bool = False,
) -> dict:
    """Extrait les frais courants « Equity UCITS » de la table MR-CP.14, page 18."""
    if not pdf.exists():
        raise ReleveImpossible(
            f"PDF introuvable : {pdf}\nTélécharge-le depuis {URL_PDF} et relance."
        )
    try:
        empreinte = hashlib.sha256(pdf.read_bytes()).hexdigest()
    except OSError as exc:
        raise PdfIllisible(f"lecture impossible de {pdf} : {exc}") from exc

    document_conforme = empreinte == SHA256_ATTENDU
    if not document_conforme and accepter_nouvelle_empreinte and not date_releve:
        # Le message ci-dessous promet « --accepter-nouvelle-empreinte ET --date-releve » : le
        # code doit l'EXIGER, sinon la promesse est de la prose (relecture du 06/08).
        raise ReleveImpossible(
            "document remplacé : --date-releve AAAA-MM-JJ est obligatoire avec "
            "--accepter-nouvelle-empreinte. Un relevé sur un nouveau document porte la date à "
            "laquelle il a été fait, jamais celle du précédent."
        )
    if not document_conforme and not accepter_nouvelle_empreinte:
        raise ReleveImpossible(
            f"le PDF n'a plus l'empreinte du document relevé le 06/08/2026.\n"
            f"  attendue : {SHA256_ATTENDU}\n  trouvée  : {empreinte}\n"
            "L'ESMA a remplacé son rapport. Le relevé ne repart PAS en silence : relance avec "
            "--accepter-nouvelle-empreinte ET --date-releve AAAA-MM-JJ, puis fais revalider les "
            "chiffres (fact-check) avant tout montage."
        )
    date = date_releve or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(date)
    except ValueError as exc:
        raise ReleveImpossible(f"date de relevé invalide : {date!r} (AAAA-MM-JJ attendu).") from exc

    compact = re.sub(r"[ \t]+", " ", _texte_page(pdf, PAGE_TABLE))
    lignes = _lignes_par_annee(_bloc_actions(compact))
    annee = max(lignes)
    valeurs = lignes[annee]

    # GARDE-FOU N°3 : un taux de frais courants hors [0 ; 10] points n'est pas un taux de frais.
    # Sans lui, une ligne de PERFORMANCE lue par erreur passerait pour des frais a 21,4 %.
    hors_bornes = [v for v in valeurs if not 0.0 <= v <= FRAIS_MAX_POINTS]
    if hors_bornes:
        raise ReleveImpossible(
            f"page {PAGE_TABLE}, année {annee} : valeur(s) {hors_bornes} hors [0 ; "
            f"{FRAIS_MAX_POINTS}] points. Ce ne sont pas des frais courants — probable lecture "
            "d'un autre bloc du tableau."
        )

    releve = {
        cle: {
            "categorie": libelle,
            "frais_courants_1an_pct": valeurs[2 * i],
            "frais_courants_10ans_pct": valeurs[2 * i + 1],
        }
        for i, (cle, libelle) in enumerate(CATEGORIES)
    }

    # Regle mecanique, figee avant lecture : min et max de l'horizon 1 an.
    par_1an = {cle: d["frais_courants_1an_pct"] for cle, d in releve.items()}
    # GARDE-FOU N°4 (Gardien conformite, 06/08) : la v1 departageait les ex aequo par ordre
    # ALPHABETIQUE — « etf » passant avant « passif_non_etf », la borne basse tombait
    # systematiquement sur l'ETF. Un tri qui va toujours dans le meme sens est un choix humain
    # deguise en regle mecanique, et sur cette table l'ecart passif/ETF vaut 0,01 point : le cas
    # est arrive des l'annee 2023. A egalite, on ne tranche pas en silence : on s'arrete.
    for extremum, nom in ((min(par_1an.values()), "basse"), (max(par_1an.values()), "haute")):
        ex_aequo = sorted(c for c, v in par_1an.items() if v == extremum)
        if len(ex_aequo) > 1:
            raise ReleveImpossible(
                f"borne {nom} à égalité entre {ex_aequo} ({extremum} %). La règle de sélection "
                "ne départage pas les ex aequo : trancher ici reviendrait à choisir la catégorie "
                "mise en avant. Arbitrage écrit obligatoire au protocole avant de relever."
            )
    cle_basse = min(par_1an, key=par_1an.get)
    cle_haute = max(par_1an, key=par_1an.get)

    def borne(cle: str) -> dict:
        return {
            "valeur_pct": releve[cle]["frais_courants_1an_pct"],
            "definition": DEFINITION,
            "categorie": releve[cle]["categorie"],
            "source": SOURCE,
            "page": f"p. {PAGE_TABLE}, table {CODE_TABLE}, « Equity UCITS », {annee}, horizon 1 an",
            "url": URL_PDF,
            "date_releve": date,
        }

    return {
        "_lisez_moi": (
            "Relevé produit par relever_frais_ep3.py — extraction déterministe, aucun chiffre "
            "saisi à la main, aucun chiffre lu par un modèle. Définition figée AVANT le relevé "
            "dans DEFINITION_FRAIS_ep3.md."
        ),
        "document": {
            "titre": SOURCE,
            "reference": "ESMA50-1949966494-4065",
            # Ces deux metadonnees decrivent le document du 06/08. Si l'empreinte a change, elles
            # ne decrivent plus rien de verifie : on les met a `null` plutot que de publier un
            # fait fabrique a cote d'un simple drapeau (relecture du 06/08).
            "publie_le": "2026-03-03" if document_conforme else None,
            "donnees_arretees_au": "2024-12-31" if document_conforme else None,
            "metadonnees_non_reverifiees": not document_conforme,
            "url": URL_PDF,
            "sha256": empreinte,
            "sha256_attendu": SHA256_ATTENDU,
            "document_conforme_a_lempreinte": document_conforme,
        },
        "table": {
            "code": CODE_TABLE,
            "titre": TITRE_TABLE,
            "page": PAGE_TABLE,
            "section": "Equity UCITS — Ongoing costs",
            "entete_colonnes_verifie": True,
            "annee_retenue": annee,
            "annees_disponibles": sorted(lignes),
        },
        "definition_frais": DEFINITION,
        "releve_complet_toutes_categories": releve,
        "regle_de_selection_des_bornes": (
            "borne basse = la plus basse des trois catégories à l'horizon 1 an ; borne haute = "
            "la plus haute. Règle mécanique figée avant lecture : aucun choix humain."
        ),
        # ⚠️ Ce qui suit n'est PAS relevé : ce sont les hypothèses de simulation, choisies par le
        # protocole (LR4 cond.2). Elles vivent ici parce que le moteur les lit ici, mais elles ne
        # sortent d'aucun document — et rien à l'écran ne doit les présenter comme une donnée.
        "_ces_hypotheses_ne_sont_pas_relevees": [
            "capital_initial",
            "versement_annuel",
            "horizons_ans",
            "hypotheses_rendement_brut_pct",
        ],
        "capital_initial": 10_000.0,
        "versement_annuel": 0.0,
        "horizons_ans": [10, 20, 30],
        "hypotheses_rendement_brut_pct": [0.0, 5.0, 7.0],
        "phrase_categories": (
            f"Ces deux chiffres sont des moyennes de deux catégories différentes de fonds "
            f"actions — « {releve[cle_basse]['categorie']} » et "
            f"« {releve[cle_haute]['categorie']} » — publiées le même jour dans le même tableau "
            f"de l'ESMA ; ce ne sont pas deux produits, et l'écart entre eux n'est pas un "
            f"conseil."
        ),
        "bornes": {"basse": borne(cle_basse), "haute": borne(cle_haute)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Relevé déterministe des frais courants (ép. 3).")
    ap.add_argument("--pdf", default=str(PDF_DEFAUT))
    ap.add_argument("--sortie", default="faits_frais_ep3.json")
    ap.add_argument(
        "--date-releve", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)."
    )
    ap.add_argument(
        "--accepter-nouvelle-empreinte",
        action="store_true",
        help="le PDF ESMA a changé : accepte de relever quand même, et redate le relevé.",
    )
    args = ap.parse_args(argv)
    try:
        faits = relever(
            pathlib.Path(args.pdf), args.date_releve, args.accepter_nouvelle_empreinte
        )
    except ReleveImpossible as exc:
        print(f"STOP — {exc}")
        return 1
    except PdfIllisible as exc:
        print(f"STOP — {exc}")
        return 2
    chemin = pathlib.Path(args.sortie)
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(faits, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        print(
            f"STOP — écriture impossible dans {chemin} : {exc}\n"
            "Le relevé, lui, était bon : ferme le fichier s'il est ouvert et relance."
        )
        return 3
    doc = faits["document"]
    print(f"FEU VERT — relevé écrit dans {chemin} (relevé daté du {faits['bornes']['basse']['date_releve']})")
    print(f"  document : {doc['reference']} · {doc['publie_le']} · sha256 {doc['sha256'][:16]}…")
    if not doc["document_conforme_a_lempreinte"]:
        print("  ⚠ EMPREINTE DIFFÉRENTE de celle du 06/08/2026 : le rapport a été remplacé.")
        print("    Les chiffres doivent repasser au fact-check avant tout montage.")
    for cle, d in faits["releve_complet_toutes_categories"].items():
        print(f"  {cle:15s} {d['frais_courants_1an_pct']:.2f} % (1 an) — {d['categorie']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
