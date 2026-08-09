#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# relever_citations_ep3.py — les CITATIONS qui vont etre GRAVEES A L'ECRAN, ep. 3 « ETF ».
#
# Pourquoi ce fichier existe. `relever_frais_ep3.py` verrouille les CHIFFRES mesures. Restaient
# trois enonces que l'episode affiche entre guillemets et attribue a une institution, et qui
# n'etaient verrouilles NULLE PART : le sous-titre anglais de la table MR-CP.14, la note 28 sur
# l'ecart achat-vente, et les « trois pages » du DIC. Le panel v2 les avait deja signales
# (« une citation attribuee a un regulateur et affichee entre guillemets se recopie, elle ne se
# retape pas ») — sans code, la consigne reposait sur la vigilance de celui qui tape la carte.
#
# Le sous-titre est le cas d'ecole : il porte un tiret DEMI-CADRATIN (U+2013) et PAS d'espace
# avant le %, deux details qu'une resaisie francise sans que personne ne le voie.
#
# ---------------------------------------------------------------------------
# CONTRAT
# ---------------------------------------------------------------------------
# relever(pdf: Path) -> dict
#   Ouvre le PDF ESMA, VERIFIE son empreinte SHA-256 contre celle du releve des frais, puis
#   EXTRAIT les citations du texte du PDF. Aucune citation n'est ecrite dans ce fichier :
#   elles sont cherchees, et leur absence est une erreur, jamais un repli.
#   Leve CitationIntrouvable si une citation attendue n'est pas dans le PDF.
#
# LE CAS PARTICULIER, ASSUME ET TRACE : le fait juridique des « trois pages » ne vient pas de ce
# PDF mais d'EUR-Lex (reglement (UE) n° 1286/2014, art. 6 §4). Il ne peut donc pas etre extrait
# ici. Il est porte avec sa citation, son URL, sa date de VERIFICATION EN DIRECT et sa date de
# peremption — et le champ `_extrait_du_pdf: false` le dit, pour qu'on ne le confonde jamais
# avec une citation recopiee par la machine.
#
# SA GATE : ce script EST la gate. Si l'empreinte du PDF a bouge, ou si une citation attendue
# n'est plus dans le document, il sort en erreur et n'ecrit rien — donc `gen_ep3_overlays.py`
# n'a pas de quoi dessiner et le montage n'a pas de cartes. La chaine casse au bon endroit.
#
# Usage : python relever_citations_ep3.py [--check]   (--check : verifie, n'ecrit rien)
"""Releve deterministe des citations affichees a l'ecran (ep. 3)."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
for _flux in (sys.stdout, sys.stderr):
    with contextlib.suppress(AttributeError, OSError):
        _flux.reconfigure(encoding="utf-8", errors="replace")

PDF = HERE / "sources_ep3" / "ESMA50-1949966494-4065.pdf"
FAITS_FRAIS = HERE / "faits_frais_ep3.json"
OUT = HERE / "faits_citations_ep3.json"

# Page du document (1-based, telle qu'imprimee) -> index pypdf. Le PDF ESMA n'a pas de decalage
# de pagination : p. 18 = index 17. Verifie a l'extraction (la citation doit etre SUR cette page).
PAGE_TABLE = 18
PAGE_NOTE_SPREAD = 19


class CitationIntrouvable(RuntimeError):
    """Une citation attendue n'est pas dans le PDF. Jamais de repli : on n'affiche rien."""


# La citation du DIC, telle qu'elle figure a l'article 6 §4 (verifiee en direct sur EUR-Lex le
# 08/08/2026). Constante nommee, parce que le NOMBRE affiche a l'ecran en est derive.
CITATION_DIC = ("The key information document shall be drawn up as a short document written in "
                "a concise manner and of a maximum of three sides of A4-sized paper when printed")
# Le texte de loi ecrit le nombre EN LETTRES. Table minimale et explicite : on ne convertit que
# ce qu'on a reellement lu. Un mot absent de la table = STOP, jamais un chiffre devine.
NOMBRES_EN_LETTRES_EN = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}


def _pages_de(citation):
    """Rend le nombre de pages EN CHIFFRES, lu dans la citation. Aucun chiffre tape a la main.

    « … a maximum of three sides of A4-sized paper … » -> « 3 ». Si la citation change de
    nombre (reforme RIS : passage a quatre pages), la carte suit le texte au lieu de repeter
    ce que quelqu'un avait tape un soir.
    """
    m = re.search(r"maximum of (\w+) sides of A4", citation)
    if not m:
        raise CitationIntrouvable(
            "la citation du DIC ne dit plus « maximum of <nombre> sides of A4 » : le nombre de "
            f"pages affiche a l'ecran ne peut plus etre derive du texte. Recu : {citation!r}")
    mot = m.group(1).lower()
    if mot not in NOMBRES_EN_LETTRES_EN:
        raise CitationIntrouvable(
            f"nombre de pages ecrit « {mot} » dans la citation : hors table de conversion. "
            "Ajoute-le explicitement plutot que de laisser deviner un chiffre a l'ecran.")
    return NOMBRES_EN_LETTRES_EN[mot]


def _texte_page(pdf: pathlib.Path, page_1based: int) -> str:
    try:
        import pypdf
    except ImportError:
        sys.exit("pypdf absent : pip install pypdf. Sans lui, aucune citation n'est verifiable.")
    try:
        lecteur = pypdf.PdfReader(str(pdf))
    except Exception as exc:                                    # noqa: BLE001 (PDF illisible)
        sys.exit(f"PDF illisible ({pdf.name}) : {exc}")
    if page_1based > len(lecteur.pages):
        sys.exit(f"Le PDF n'a que {len(lecteur.pages)} pages : p. {page_1based} demandee.")
    return lecteur.pages[page_1based - 1].extract_text() or ""


def _empreinte(pdf: pathlib.Path) -> str:
    return hashlib.sha256(pdf.read_bytes()).hexdigest()


def _une_ligne(texte: str) -> str:
    """Recolle les coupures de ligne du PDF, sans toucher aux caracteres eux-memes.

    On normalise les espaces MULTIPLES et les retours a la ligne — jamais les tirets ni la
    ponctuation : c'est precisement ce qui doit rester au caractere pres.
    """
    return re.sub(r"\s+", " ", texte).strip()


def relever(pdf: pathlib.Path = PDF) -> dict:
    """Voir le CONTRAT."""
    if not pdf.exists():
        sys.exit(f"PDF source introuvable : {pdf}\n-> il doit rester sur disque : c'est LUI qui "
                 "fait foi, pas notre memoire de ce qu'il dit.")
    if not FAITS_FRAIS.exists():
        sys.exit(f"{FAITS_FRAIS.name} introuvable -> lance d'abord relever_frais_ep3.py.")
    faits = json.loads(FAITS_FRAIS.read_text(encoding="utf-8"))
    attendu = faits["document"]["sha256_attendu"]
    reel = _empreinte(pdf)
    if reel != attendu:
        sys.exit("STOP : l'empreinte du PDF a change.\n"
                 f"   attendu : {attendu}\n   trouve  : {reel}\n"
                 "-> ce n'est plus le document sur lequel le releve des frais a ete fait. "
                 "Refais le releve ET le fact-check avant d'afficher la moindre citation.")

    # --- 1. Sous-titre de la table MR-CP.14 (p. 18) — EXTRAIT, jamais retape ----------------
    page_table = _texte_page(pdf, PAGE_TABLE)
    m = re.search(r"(Passive funds[^\n]*?active funds)", page_table)
    if not m:
        raise CitationIntrouvable(
            f"le sous-titre de MR-CP.14 n'est plus a la p. {PAGE_TABLE} du PDF. On n'affiche "
            "pas une phrase attribuee a l'ESMA qu'on ne retrouve pas dans son document.")
    sous_titre = _une_ligne(m.group(1))
    # ⚠️ Corrige le 08/08/2026 (code-reviewer) : la v1 ecrivait
    #     `"% " in sous_titre.replace("% cheaper", "")`
    # ce qui EFFACAIT justement le cas cherche — « 60–80 % cheaper » (espace francais avant le
    # %) passait au VERT. Seul le tiret etait reellement controle, et le test du piege passait
    # pour la mauvaise raison : il modifiait le tiret ET l'espace, c'est le tiret qui refusait.
    # Un garde-fou qui ne garde rien est pire qu'aucun : il donne confiance.
    if "–" not in sous_titre or re.search(r"\s%", sous_titre):
        # Le tiret demi-cadratin et l'absence d'espace avant le % SONT la citation. Si
        # l'extraction les perd, c'est l'extraction qui est fausse, et il ne faut surtout pas
        # l'afficher : ce serait une citation francisee presentee comme le texte du regulateur.
        raise CitationIntrouvable(
            f"typographie du sous-titre alteree a l'extraction : {sous_titre!r}. "
            "Le tiret demi-cadratin et « 80% » sans espace font partie de la citation.")

    # --- 2. Note 28 : l'ecart achat-vente n'est PAS dans la mesure (p. 19) ------------------
    # On extrait DEUX phrases, pas une. La v1 ne gardait que la derniere (« pas de donnee
    # disponible ») : la carte affirmait alors « le rapport le dit lui-meme » en montrant la
    # phrase la plus FAIBLE de la note — celle qui ne dit que l'absence de donnee, pas que le
    # cout existe. C'est ce que le fact-check du 08/08 a bloque, et c'est aussi ce que
    # `DEFINITION_FRAIS_ep3.md` §2 interdit noir sur blanc (« la phrase du milieu ne doit PAS
    # etre coupee »). La phrase du milieu est celle qui porte la preuve : le spread rend
    # l'investissement initial plus cher.
    # La 1re phrase de la note est volontairement laissee de cote : l'extracteur y rend
    # « bid –ask » (espace parasite absent du document imprime). Une citation gravee a l'ecran
    # ne se retouche pas — on cite donc les deux phrases que l'extraction rend proprement.
    page_note = _texte_page(pdf, PAGE_NOTE_SPREAD)
    m = re.search(r"(Bid-ask spreads can make the initial investment\s*more expensive,.*?"
                  r"information on bid-ask spreads)", page_note, re.S)
    if not m:
        raise CitationIntrouvable(
            f"la note sur l'ecart achat-vente n'est plus a la p. {PAGE_NOTE_SPREAD}, ou elle "
            "n'a plus ses deux phrases. La carte « ce que la mesure exclut » affirme que le "
            "regulateur le dit lui-meme : sans la phrase qui dit que ce cout EXISTE, on ne "
            "l'affirme pas.")
    note_spread = _une_ligne(m.group(1)) + "."
    # On exige les DEUX fragments par leur texte propre. Tester « does not include » ne suffit
    # pas : en retirant « Due to lack of data availability » du document, la phrase restante
    # contient encore « does not include » et le controle passait au vert (piege du test qui
    # ne mordait plus, 08/08/2026).
    for fragment, quoi in (("more expensive", "que l'ecart achat-vente rencherit "
                                              "l'investissement initial"),
                           ("Due to lack of data availability", "que l'ESMA declare ne pas "
                                                               "avoir la donnee")):
        if fragment not in note_spread:
            raise CitationIntrouvable(
                f"la note 28 sur l'ecart achat-vente ne dit plus {quoi} (fragment "
                f"« {fragment} » absent). La carte « ce que la mesure exclut » ne peut pas "
                f"l'affirmer. Recu : {note_spread!r}")
    if not re.search(r"^\s*28\s", page_note[max(0, m.start() - 400):m.start()], re.M):
        # Le numero de note est AFFICHE sur la carte (« ESMA p. 19, note 28 ») : s'il a bouge,
        # la carte enverrait le spectateur a la mauvaise note.
        raise CitationIntrouvable(
            "la phrase sur l'ecart achat-vente n'est plus rattachee a la note 28 : le renvoi "
            "affiche sur la carte serait faux.")

    return {
        "_lisez_moi": "Citations AFFICHEES A L'ECRAN, extraites du PDF source par "
                      "relever_citations_ep3.py. Aucune n'est saisie a la main. L'empreinte "
                      "SHA-256 du PDF est verifiee avant toute extraction.",
        "document": {
            "titre": faits["document"]["titre"],
            "reference": faits["document"]["reference"],
            "url": faits["document"]["url"],
            "sha256": reel,
            "sha256_conforme": True,
        },
        "sous_titre_table": {
            "citation_exacte": sous_titre,
            "table": faits["table"]["code"],
            "page": PAGE_TABLE,
            "langue": "en",
            "_extrait_du_pdf": True,
            "a_afficher_avec": "attribution explicite a l'ESMA : c'est le regulateur qui "
                               "l'ecrit, pas nous.",
        },
        "exclusion_ecart_achat_vente": {
            "citation_exacte": note_spread,
            "page": PAGE_NOTE_SPREAD,
            "note": 28,
            "langue": "en",
            "_extrait_du_pdf": True,
        },
        # --- Le cas particulier, assume et trace : hors de ce PDF -------------------------
        "dic_trois_pages": {
            "citation_exacte": CITATION_DIC,
            "texte": "règlement (UE) n° 1286/2014, article 6, paragraphe 4",
            # Ce que l'article dit EXACTEMENT : un PLAFOND, pas un format. Le champ existe pour
            # que la carte ne puisse pas ecrire « trois pages imposees » — l'article impose
            # « trois pages AU MAXIMUM ». Bloquant leve par le fact-check du 08/08/2026.
            "nature_de_la_regle": "plafond (maximum), pas un format impose",
            # Le NOMBRE est DERIVE de la citation, jamais tape : « 3 PAGES MAXIMUM » ecrit a la
            # main passait les garde-fous meme en y mettant « 4 » (code-reviewer, 2e passe du
            # 08/08). C'est le seul chiffre de l'ecran qui ne vient pas du moteur : il doit
            # venir du texte de loi, mot pour mot.
            "formulation_autorisee_a_lecran": "%s PAGES MAXIMUM" % _pages_de(CITATION_DIC),
            "_nombre_de_pages_derive_de": "la citation (« three sides of A4-sized paper »)",
            # A qui, et quand : art. 13 — en temps utile avant que l'investisseur de detail ne
            # soit lie. « avant TOUT achat de fonds » etait un absolu que le texte ne porte pas.
            "a_qui": "investisseurs de détail (les fonds UCITS y sont entrés le 01/01/2023, "
                     "fin de l'exemption transitoire)",
            # Version d'ECRAN : la mention complete ne tient pas sur une carte, et une source
            # illisible ne prouve rien. Le detail (UCITS, 01/01/2023) reste ici, dans le fichier
            # de faits, et en description.
            "a_qui_court": "investisseurs de détail",
            "quand": "en temps utile avant que l'investisseur ne soit lié (article 13)",
            # L'article 6 §4 ne traite QUE de la longueur et de la presentation. Le CONTENU du
            # document (dont la section « Quels sont les coûts ? ») est impose par l'article 8,
            # paragraphe 3 — verifie en direct sur EUR-Lex le 08/08/2026. Une carte qui liste
            # ce qu'on lit DANS le document doit citer le 8 §3, jamais le 6 §4.
            "article_du_contenu": "règlement (UE) n° 1286/2014, article 8, paragraphe 3 — "
                                  "(c) « En quoi consiste ce produit ? » et (f) « Quels sont "
                                  "les coûts ? »",
            "consolidation": "2024-01-09",
            "statut": "en vigueur",
            "url": "https://eur-lex.europa.eu/eli/reg/2014/1286/2024-01-09/eng",
            "langue": "en",
            "_extrait_du_pdf": False,
            "_pourquoi": "fait JURIDIQUE : il ne vit pas dans le rapport ESMA mais dans "
                         "EUR-Lex. Il ne peut donc pas etre extrait ici — il est verifie en "
                         "direct, et la date ci-dessous le dit.",
            "verifie_en_direct_le": "2026-08-08",
            "peremption": "La modernisation du DIC (4 pages A4 + section « Product at a "
                          "glance ») est la procedure 2023/0166 (COD), toujours en cours : "
                          "application prevue 18 mois apres publication des actes delegues / "
                          "RTS. A REVERIFIER si le tournage glisse de plus de 3 mois.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Releve les citations affichees a l'ecran (ep. 3).")
    ap.add_argument("--check", action="store_true", help="verifie et affiche, n'ecrit rien")
    a = ap.parse_args(argv)

    try:
        faits = relever()
    except CitationIntrouvable as exc:
        print(f"🔴 STOP — {exc}")
        return 1

    print("== relever_citations_ep3 ==")
    print(f"   PDF        : {PDF.name} (empreinte conforme au releve des frais)")
    print(f"   sous-titre : « {faits['sous_titre_table']['citation_exacte']} »")
    print(f"                 {faits['sous_titre_table']['table']}, "
          f"p. {faits['sous_titre_table']['page']} — extrait du PDF")
    print(f"   note {faits['exclusion_ecart_achat_vente']['note']}    : "
          f"« {faits['exclusion_ecart_achat_vente']['citation_exacte'][:78]}… »")
    print(f"   DIC        : {faits['dic_trois_pages']['texte']} — "
          f"verifie en direct le {faits['dic_trois_pages']['verifie_en_direct_le']} "
          f"({faits['dic_trois_pages']['statut']})")
    if a.check:
        print("\n--check : rien n'a ete ecrit.")
        return 0
    OUT.write_text(json.dumps(faits, ensure_ascii=False, indent=2), encoding="utf-8")
    # Relecture apres aller-retour disque : sous OneDrive, une ecriture peut partir en erreur
    # differee, et une citation tronquee serait pire qu'absente.
    relu = json.loads(OUT.read_text(encoding="utf-8"))
    if relu != faits:
        sys.exit("STOP : relecture de %s != ce qui a ete ecrit." % OUT.name)
    print(f"\nFEU VERT — citations verrouillees : {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
