#!/usr/bin/env python3
# simulateur_frais.py — LE MOTEUR DE L'EPISODE 3 « ETF ». Ecrit APRES la gate, AVANT le releve.
#
# Ce qu'il calcule : ce que coute UN POINT DE FRAIS EN PLUS sur un horizon donne. Rien d'autre.
# Il ne compare pas deux produits, il ne designe rien, il ne conclut pas.
#
# ---------------------------------------------------------------------------
# POURQUOI IL REFUSE AUTANT DE CHOSES
# ---------------------------------------------------------------------------
# Le Gardien conformite a rendu STOP sur le protocole de l'ep. 3 (05/08/2026). Son point n°4 :
#
#   « TER, couts totaux ESMA et frais agreges du DIC/PRIIPs NE MESURENT PAS LA MEME CHOSE —
#     les confondre serait la faute "prix vs rendement total" de l'ep. 2, rejouee sur les frais. »
#
# A l'ep. 2, cette faute avait ete evitee de justesse EN PROSE, par une relecture. En prose, un
# soir a 23 h, elle passe. Ici elle est du CODE, en DEUX verrous (relecture du 06/08) :
#   - comparer deux definitions differentes           -> BornesIncomparables ;
#   - simuler une definition qui n'est pas un taux
#     annuel recurrent (frais d'entree, incidence DIC) -> DefinitionNonSimulable.
# Le premier verrou seul laissait passer le pire cas : DEUX bornes en frais d'entree/sortie,
# composees comme si c'etait une charge annuelle. Arithmetiquement juste, editorialement faux.
# Aucun de ces deux refus n'a de contournement, pas meme un drapeau.
#
# Les autres refus viennent de LR4 (protocole v2) :
#   - bornes sans source / page / url / date / categorie  -> SourceManquante
#   - page hors des tables autorisees par la definition   -> SourceManquante
#     (le piege identifie : MR-CP.4 p. 12 EXCLUT les ETF)
#   - url hors liste blanche `carte_source`               -> SourceManquante
#   - bornes de sources ou de dates differentes           -> BornesIncomparables
#   - categories differentes SANS vraie phrase d'avert.   -> BornesIncomparables
#   - grille amputee d'un horizon du protocole, ou sans
#     l'hypothese 0 %                                     -> GrilleIncomplete
#     (a 0 %, l'ecart de frais est pur et inattaquable : le chiffre le plus honnete du lot)
#
# ---------------------------------------------------------------------------
# CONTRAT
# ---------------------------------------------------------------------------
# NiveauDeFrais(valeur_pct, definition, categorie, source, page, url, date_releve)
#   valeur_pct : frais ANNUELS en POINTS DE POURCENTAGE, tels qu'ils se lisent dans le document
#                (0.5 point = 0,5 % par an). Jamais une fraction : 0.5 ne veut pas dire 50 %.
#   Leve SourceManquante si un champ est vide/invalide, ou la valeur hors [0 ; 10] points.
#
# capital_final(capital_initial, versement_annuel, annees, rendement_brut_pct, frais_pct) -> float
#   BRIQUE ARITHMETIQUE NUE — elle ne porte ni source ni definition, donc rien de ce qu'elle rend
#   n'est publiable tel quel. Ce qui est publiable sort de `simuler_grille`, et uniquement en
#   grille entiere. Interets composes, pas de temps MENSUEL, dans cet ordre chaque mois :
#   performance brute, puis prelevement des frais sur l'encours, puis versement (fin de mois).
#   Convention figee : (1 - fm)**12 == (1 - f) exactement -> a 0 % de rendement et sans versement,
#   capital_final == C * (1 - f)**N. Verifiable a la main, donc testable.
#
# simuler_grille(borne_basse, borne_haute, ...) -> dict JSON-serialisable
#   Rend TOUTE la grille : horizons x hypotheses de rendement, jamais une case isolee.
#
# ---------------------------------------------------------------------------
# LE « COUT D'UN POINT DE FRAIS » — deux chiffres, parce qu'un seul mentirait
# ---------------------------------------------------------------------------
# L'effet des frais n'est PAS lineaire : sur 30 ans a 5 %, le 1er point coute plus cher que le 2e.
# Diviser l'ecart total par l'ecart en points donne donc une MOYENNE, pas « le cout d'un point ».
# Le moteur publie les deux, nommes pour ce qu'ils sont :
#   - cout_moyen_par_point_sur_lecart_releve_euros : l'ecart total ramene par point relevé ;
#   - cout_du_point_de_frais_suivant_euros         : le VRAI point marginal, borne basse -> +1 pt.
# Le second est celui qui peut s'ecrire « ce que coute 1 point de frais en plus » a l'ecran.
#
# ---------------------------------------------------------------------------
# TRIBUNAL DES CAS (code.md §3) — pannes prevues, toutes couvertes par un test
# ---------------------------------------------------------------------------
#  1. frais saisis en fraction (0.0138) au lieu de points (1.38)  -> avertissement (les deux
#     bornes sous 0,05 point), jamais un silence.
#  2. frais > 10 points (22 saisi pour 0,22)                      -> SourceManquante.
#  3. bornes identiques ou ecart infime (< 0,01 point)            -> couts par point a None +
#     avertissement : pas de division par presque-zero.
#  4. borne basse > borne haute (inversion a la saisie)           -> reordonnancement + avert.
#  5. rendement negatif                                            -> hypothese legitime, acceptee.
#  6. horizon 0 an, non entier, ou grille amputee du 10/20/30      -> GrilleIncomplete.
#  7. fichier de faits absent (le releve n'a pas eu lieu)          -> message clair, rc 2.
#  8. JSON de faits valide mais structurellement faux              -> message clair, rc 2.
#  9. fichier de sortie verrouille (OneDrive, Excel, editeur)      -> message clair, rc 3.
# 10. console cp1252 (accents illisibles)                          -> stdout reconfigure UTF-8.
#
# Usage : python simulateur_frais.py --faits <faits.json> [--sortie <res.json>] [--dry-run]
# Retour 0 = OK · 1 = refus de conformite (le calcul n'a pas eu lieu) · 2 = mauvais usage ou
# donnees illisibles · 3 = ecriture impossible (le calcul, lui, etait bon).
"""Simulateur d'impact des frais — ep. 3 « ETF ». Arithmetique seule, chaque chiffre source."""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile

from carte_source import SourceRefusee
from carte_source import verifier as verifier_url

with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

__all__ = [
    "DEFINITIONS_FRAIS",
    "DEFINITIONS_SIMULABLES",
    "HORIZONS_PROTOCOLE",
    "BornesIncomparables",
    "DefinitionNonSimulable",
    "GrilleIncomplete",
    "NiveauDeFrais",
    "RefusDeConformite",
    "SourceManquante",
    "capital_final",
    "simuler_grille",
]

# ---------------------------------------------------------------------------
# LES DEFINITIONS FIGEES (protocole §3 bis — figees AVANT le releve)
# ---------------------------------------------------------------------------
# Trois mesures de frais coexistent sur le marche et ne mesurent PAS la meme chose. Le moteur
# les connait toutes les trois pour pouvoir REFUSER de les melanger, et refuser d'en simuler
# deux. Le detail et la justification vivent dans `DEFINITION_FRAIS_ep3.md`.
DEFINITIONS_FRAIS: dict[str, dict[str, object]] = {
    "ongoing_costs_esma": {
        "libelle": "frais courants annuels (ongoing costs)",
        "perimetre": (
            "Couts RECURRENTS supportes par le fonds sur une annee (frais de gestion, couts de "
            "transaction DU FONDS, commissions de performance), tels que publies dans le DIC "
            "PRIIPs. Les retrocessions aux distributeurs sont DEDANS, pas dehors. N'inclut NI "
            "les frais d'entree/sortie, NI l'ecart achat-vente paye en Bourse, NI le courtage "
            "paye par l'investisseur, NI les frais d'enveloppe, NI la fiscalite."
        ),
        "document": (
            "ESMA Market Report — Costs and Performance of EU Retail Investment Products 2025"
        ),
        "reference": "ESMA50-1949966494-4065, 3 mars 2026 (donnees arretees au 31/12/2024)",
        # Tables autorisees par DEFINITION_FRAIS_ep3.md §3. La p. 12 (MR-CP.4) en est ABSENTE
        # exprès : elle exclut les ETF, c'est le piege n°1 du releve.
        "pages_autorisees": (6, 18, 19),
    },
    "couts_ponctuels_esma": {
        "libelle": "frais d'entree et de sortie (one-off costs)",
        "perimetre": (
            "Frais de souscription et de rachat. ATTENTION : le DIC publie le MAXIMUM "
            "autorise, pas le montant reellement preleve — ESMA le dit lui-meme (encadre "
            "MR-CP.8, p. 14). Non additionnable a un frais courant, et NON SIMULABLE comme une "
            "charge annuelle."
        ),
        "document": (
            "ESMA Market Report — Costs and Performance of EU Retail Investment Products 2025"
        ),
        "reference": "ESMA50-1949966494-4065, 3 mars 2026, encadre MR-CP.8, p. 14",
        "pages_autorisees": (6, 12, 14),
    },
    "incidence_couts_annuels_dic": {
        "libelle": "incidence des couts annuels (DIC PRIIPs)",
        "perimetre": (
            "Chiffre agrege du DIC PRIIPs : couts ponctuels AMORTIS sur la duree de detention "
            "recommandee + couts recurrents + couts accessoires. Depend donc de l'horizon "
            "affiche dans le DIC. Ce n'est PAS un taux de frais courants : le composer sur "
            "10/20/30 ans compterait deux fois les frais d'entree."
        ),
        "document": "Reglement delegue (UE) 2017/653, modifie par 2021/2268 (DIC PRIIPs)",
        "reference": "presentation des couts en vigueur depuis le 01/01/2023",
        "pages_autorisees": (),  # cite a l'ecran, jamais releve dans un tableau chiffre
    },
}

# Une seule des trois est un TAUX ANNUEL RECURRENT, donc la seule qui puisse etre composee sur
# 10/20/30 ans. `DEFINITION_FRAIS_ep3.md` §3 : les autres sont « citees a l'ecran quand on
# explique le DIC, JAMAIS utilisees dans le calcul ».
DEFINITIONS_SIMULABLES: frozenset[str] = frozenset({"ongoing_costs_esma"})

# LR4 cond.2 : la grille entiere. Ces horizons sont un PLANCHER : on peut en ajouter, jamais en
# retirer — retirer le 10 ans pour ne garder que le 30 ans est exactement le cherry-picking que
# LR4(b) nomme.
HORIZONS_PROTOCOLE: tuple[int, ...] = (10, 20, 30)
# L'hypothese 0 % est OBLIGATOIRE : a 0 %, l'ecart de frais ne doit rien a une hypothese de
# marche. C'est le seul chiffre de l'episode que personne ne peut discuter.
HYPOTHESE_OBLIGATOIRE_PCT = 0.0
FRAIS_MAX_POINTS = 10.0  # au-dela, c'est une erreur de saisie, pas un fonds.
RENDEMENT_MAX_PCT = 25.0  # au-dela, l'hypothese devient une promesse : refus.
RENDEMENT_A_SIGNALER_PCT = 10.0  # au-dela, on l'assume mais on l'ecrit.
ECART_MINIMAL_POINTS = 0.01  # sous ce seuil, « le cout d'un point » serait une extrapolation.
SEUIL_SOUPCON_FRACTION = 0.05  # deux bornes sous 0,05 point : frais probablement en fraction.
LONGUEUR_MINIMALE_PHRASE = 60  # une vraie phrase, pas un « x » qui deverrouille la derogation.
MOIS_PAR_AN = 12

MENTIONS_OBLIGATOIRES: tuple[str, ...] = (
    "à performance brute identique — hypothèse d'école",
    "toutes choses égales par ailleurs : ça n'arrive jamais",
    "ce calcul ne dit pas lequel choisir",
)

RE_PAGE = re.compile(r"\bp\.?\s*(\d{1,3})\b", re.I)


class RefusDeConformite(Exception):
    """Le calcul n'a pas eu lieu : une condition du protocole n'est pas remplie."""


class SourceManquante(RefusDeConformite):
    """Un chiffre sans source vérifiable, ou lu dans une table non autorisée (LR3)."""


class BornesIncomparables(RefusDeConformite):
    """Les deux bornes ne mesurent pas la même chose, ou ne sortent pas du même relevé (LR4)."""


class DefinitionNonSimulable(RefusDeConformite):
    """Cette mesure de frais n'est pas un taux annuel récurrent : la composer serait faux."""


class GrilleIncomplete(RefusDeConformite):
    """On publie la grille entière, dont l'hypothèse 0 % — jamais une sélection (LR4)."""


@dataclasses.dataclass(frozen=True)
class NiveauDeFrais:
    """Un niveau de frais RELEVE : une valeur, et tout ce qui permet de la retrouver.

    `valeur_pct` est en POINTS DE POURCENTAGE annuels (0.5 = 0,5 % par an).
    """

    valeur_pct: float
    definition: str
    categorie: str
    source: str
    page: str
    url: str
    date_releve: str

    def __post_init__(self) -> None:
        if self.definition not in DEFINITIONS_FRAIS:
            raise SourceManquante(
                f"definition inconnue : {self.definition!r}. "
                f"Definitions figees : {', '.join(sorted(DEFINITIONS_FRAIS))}. "
                "Une definition ne s'invente pas au moment du calcul."
            )
        for champ in ("categorie", "source", "page", "url", "date_releve"):
            if not str(getattr(self, champ) or "").strip():
                raise SourceManquante(
                    f"champ « {champ} » vide : un chiffre de frais sans {champ} ne se monte pas "
                    "(protocole LR3)."
                )
        if not isinstance(self.valeur_pct, (int, float)) or self.valeur_pct != self.valeur_pct:
            raise SourceManquante("valeur_pct doit être un nombre réel.")
        if not 0.0 <= float(self.valeur_pct) <= FRAIS_MAX_POINTS:
            raise SourceManquante(
                f"valeur_pct = {self.valeur_pct} hors bornes [0 ; {FRAIS_MAX_POINTS}] points. "
                "Rappel : la valeur se lit en points de pourcentage annuels (0,22 = 0,22 %)."
            )
        self._controler_la_page()
        self._controler_lurl()
        self._controler_la_date()

    def _controler_la_page(self) -> None:
        """La page relevée doit appartenir aux tables autorisées par la définition."""
        autorisees = DEFINITIONS_FRAIS[self.definition]["pages_autorisees"]
        if not autorisees:
            return  # définition non relevable dans un tableau : le contrôle se fait ailleurs
        pages = {int(p) for p in RE_PAGE.findall(str(self.page))}
        if not pages:
            raise SourceManquante(
                f"champ « page » = {self.page!r} : aucun numéro de page lisible. LR3 exige de "
                "pouvoir retrouver le chiffre dans le document (format attendu : « p. 18 »)."
            )
        # Inclusion STRICTE, pas intersection : « p. 12 et p. 18 » blanchissait la table piegee
        # en citant a cote une table autorisee (relecture du 06/08).
        if not pages <= set(autorisees):
            raise SourceManquante(
                f"page {sorted(pages)} hors des tables autorisées pour "
                f"« {DEFINITIONS_FRAIS[self.definition]['libelle']} » : "
                f"{list(autorisees)} (DEFINITION_FRAIS_ep3.md §3). Rappel du piège identifié : "
                "la table MR-CP.4, p. 12, EXCLUT les ETF — un chiffre pris là et présenté comme "
                "« ETF » serait faux."
            )

    def _controler_lurl(self) -> None:
        """Réutilise la liste blanche de `carte_source` : la source affichable est la même."""
        try:
            verifier_url(self.url)
        except SourceRefusee as exc:
            raise SourceManquante(
                f"URL refusée par carte_source ({self.url!r}) : {exc}. Un chiffre dont la source "
                "ne peut pas s'afficher à l'écran ne se monte pas."
            ) from exc

    def _controler_la_date(self) -> None:
        try:
            datetime.date.fromisoformat(str(self.date_releve))
        except ValueError as exc:
            raise SourceManquante(
                f"date_releve = {self.date_releve!r} : format attendu AAAA-MM-JJ. LR3 exige une "
                "donnée DATÉE, pas une date approximative."
            ) from exc

    @property
    def fraction(self) -> float:
        """Le taux annuel en fraction (0,22 % -> 0.0022)."""
        return float(self.valeur_pct) / 100.0

    def en_dict(self) -> dict:
        d = dataclasses.asdict(self)
        definition = DEFINITIONS_FRAIS[self.definition]
        d["definition_libelle"] = definition["libelle"]
        d["definition_perimetre"] = definition["perimetre"]
        return d


def capital_final(
    capital_initial: float,
    versement_annuel: float,
    annees: int,
    rendement_brut_pct: float,
    frais_pct: float,
) -> float:
    """Capital au bout de `annees`, frais preleves sur l'encours, pas de temps mensuel.

    BRIQUE NUE : ce nombre ne porte ni source ni definition, il n'est pas publiable seul.
    Convention figee (et testee) : (1 - fm)**12 == (1 - f), donc a 0 % de rendement et sans
    versement, le resultat vaut exactement `capital_initial * (1 - f)**annees`.
    """
    # ValueError et non GrilleIncomplete : une brique NUE ne leve jamais une exception de
    # conformite — sinon un plantage arithmetique ressortirait en « refus de conformite » (rc 1).
    # Les horizons sont valides en amont par `_controler_grille`, c'est lui qui porte la regle.
    if not isinstance(annees, int) or isinstance(annees, bool) or annees <= 0:
        raise ValueError(f"horizon invalide : {annees!r} (entier ≥ 1 attendu).")
    if capital_initial < 0 or versement_annuel < 0:
        raise ValueError("capital initial et versement ne peuvent pas être négatifs.")
    if not 0.0 <= float(frais_pct) <= FRAIS_MAX_POINTS:
        raise ValueError(f"taux de frais hors [0 ; {FRAIS_MAX_POINTS}] points : {frais_pct}")
    r = float(rendement_brut_pct) / 100.0
    if r <= -1.0:
        raise ValueError(f"rendement brut ≤ -100 % : {rendement_brut_pct}")

    f = float(frais_pct) / 100.0
    rm = (1.0 + r) ** (1.0 / MOIS_PAR_AN) - 1.0
    fm = 1.0 - (1.0 - f) ** (1.0 / MOIS_PAR_AN)
    versement_mensuel = float(versement_annuel) / MOIS_PAR_AN

    encours = float(capital_initial)
    for _ in range(annees * MOIS_PAR_AN):
        encours = encours * (1.0 + rm) * (1.0 - fm) + versement_mensuel
    return encours


def _controler_definitions(basse: NiveauDeFrais, haute: NiveauDeFrais) -> None:
    """Les DEUX verrous du point n°4 du Gardien. Aucun contournement, pas meme un drapeau."""
    if basse.definition != haute.definition:
        raise BornesIncomparables(
            f"définitions différentes : « {DEFINITIONS_FRAIS[basse.definition]['libelle']} » "
            f"contre « {DEFINITIONS_FRAIS[haute.definition]['libelle']} ». "
            "Ces deux mesures ne mesurent pas la même chose ; les comparer serait la faute "
            "« prix vs rendement total » de l'ép. 2, rejouée sur les frais. Aucun paramètre "
            "ne permet de passer outre."
        )
    if basse.definition not in DEFINITIONS_SIMULABLES:
        raise DefinitionNonSimulable(
            f"« {DEFINITIONS_FRAIS[basse.definition]['libelle']} » n'est pas un taux annuel "
            "récurrent : la composer sur 10, 20 ou 30 ans produirait un chiffre "
            "arithmétiquement juste et faux. Seule mesure simulable : "
            f"{', '.join(sorted(DEFINITIONS_SIMULABLES))}."
        )


def _controler_bornes(
    basse: NiveauDeFrais, haute: NiveauDeFrais, phrase_categories: str
) -> tuple[NiveauDeFrais, NiveauDeFrais, list[str]]:
    """Applique LR4 cond.1. Rend (basse, haute) reordonnees + les avertissements a afficher."""
    _controler_definitions(basse, haute)
    avertissements: list[str] = []

    if basse.source != haute.source:
        raise BornesIncomparables(
            "les deux bornes ne sortent pas de la même source (LR4 cond.1) : "
            f"{basse.source!r} contre {haute.source!r}."
        )
    if basse.date_releve != haute.date_releve:
        raise BornesIncomparables(
            "les deux bornes ne sortent pas du même relevé (LR4 cond.1) : "
            f"{basse.date_releve} contre {haute.date_releve}."
        )
    if basse.categorie != haute.categorie:
        phrase = phrase_categories.strip()
        manquantes = [c for c in (basse.categorie, haute.categorie) if c not in phrase]
        # Une phrase, pas un collage : la v1 acceptait les deux libelles colles bout a bout
        # suivis de remplissage. On exige donc AUSSI un mot de la regle et une ponctuation
        # finale, et que les noms de categorie ne devorent pas la phrase (relecture du 06/08).
        longueur_utile = len(phrase) - sum(len(c) for c in (basse.categorie, haute.categorie))
        recevable = (
            len(phrase) >= LONGUEUR_MINIMALE_PHRASE
            and not manquantes
            and longueur_utile >= LONGUEUR_MINIMALE_PHRASE // 2
            and re.search(r"catégorie|différent", phrase, re.I)
            and phrase.rstrip().endswith((".", "!", "?"))
        )
        if not recevable:
            raise BornesIncomparables(
                f"catégories différentes (« {basse.categorie} » contre « {haute.categorie} ») "
                "sans phrase d'avertissement recevable. LR4 cond.1 : la carte doit le dire DANS "
                f"LA MÊME PHRASE — une vraie phrase (≥ {LONGUEUR_MINIMALE_PHRASE} caractères, "
                "terminée par un point) qui NOMME les deux catégories et dit qu'elles sont "
                "différentes. "
                + (f"Manquant dans la phrase : {manquantes}." if manquantes else "")
            )
        avertissements.append(phrase)

    if basse.valeur_pct > haute.valeur_pct:
        basse, haute = haute, basse
        avertissements.append(
            "bornes réordonnées : la borne « basse » fournie était supérieure à la borne « haute »."
        )
    # Arrondi AVANT comparaison : sans lui, 0,28 - 0,27 (= 0,010000000000000009) etait publiable
    # et 0,29 - 0,28 (= 0,009999999999999953) ne l'etait pas. Deux ecarts identiques a l'ecran,
    # deux comportements. Sur cette table, l'ecart passif/ETF vaut justement 0,01 point.
    ecart = round(haute.valeur_pct - basse.valeur_pct, 6)
    if ecart < ECART_MINIMAL_POINTS:
        avertissements.append(
            f"écart entre bornes inférieur à {ECART_MINIMAL_POINTS} point : le coût par point "
            "n'est pas publié — le calculer reviendrait à extrapoler depuis presque rien."
        )
    if max(basse.valeur_pct, haute.valeur_pct) < SEUIL_SOUPCON_FRACTION:
        avertissements.append(
            f"les deux bornes sont sous {SEUIL_SOUPCON_FRACTION} point : vérifie qu'elles ont "
            "bien été relevées en points de pourcentage (1,38 = 1,38 %) et non en fraction "
            "(0,0138)."
        )
    # Les phrases DESTINEES A L'ECRAN, distinctes des avertissements techniques (qui, eux,
    # s'adressent a celui qui lance le moteur). Seule la phrase LR4 cond.1 en fait partie.
    a_lecran = [phrase_categories.strip()] if basse.categorie != haute.categorie else []
    return basse, haute, avertissements, a_lecran


def _controler_grille(
    horizons: tuple[int, ...], hypotheses: tuple[float, ...]
) -> list[str]:
    """LR4 cond.2 : la grille entiere. Rend les avertissements, leve si elle est amputee."""
    avertissements: list[str] = []
    if any(not isinstance(a, int) or isinstance(a, bool) or a <= 0 for a in horizons):
        raise GrilleIncomplete(
            f"horizons invalides : {list(horizons)} — des entiers ≥ 1 sont attendus."
        )
    manquants = sorted(set(HORIZONS_PROTOCOLE) - set(horizons))
    if manquants:
        raise GrilleIncomplete(
            f"horizons {manquants} absents de la grille. Le protocole impose 10/20/30 ans comme "
            "PLANCHER : on peut en ajouter, jamais en retirer — ne garder que l'horizon le plus "
            "long est le cherry-picking d'horizon que LR4(b) nomme explicitement."
        )
    if len(set(hypotheses)) < 2:
        raise GrilleIncomplete(
            "au moins DEUX hypothèses de rendement DISTINCTES sont exigées (LR4 cond.2) — une "
            "seule hypothèse, c'est un scénario choisi."
        )
    if not any(abs(h - HYPOTHESE_OBLIGATOIRE_PCT) < 1e-12 for h in hypotheses):
        raise GrilleIncomplete(
            "l'hypothèse 0 % est OBLIGATOIRE (LR4 cond.2) : à 0 %, l'écart de frais ne doit "
            "rien à une hypothèse de marché. C'est le chiffre le plus honnête du lot."
        )
    if any(abs(h) > RENDEMENT_MAX_PCT for h in hypotheses):
        raise GrilleIncomplete(
            f"hypothèse de rendement au-delà de ±{RENDEMENT_MAX_PCT} % : ce n'est plus une "
            "hypothèse d'école, c'est une promesse."
        )
    fortes = [h for h in hypotheses if abs(h) > RENDEMENT_A_SIGNALER_PCT]
    if fortes:
        avertissements.append(
            f"hypothèse(s) de rendement élevée(s) affichée(s) : {fortes} % — à dire à l'écran "
            "comme une hypothèse, jamais comme une attente."
        )
    return avertissements


def simuler_grille(
    borne_basse: NiveauDeFrais,
    borne_haute: NiveauDeFrais,
    capital_initial: float = 10_000.0,
    versement_annuel: float = 0.0,
    horizons: tuple[int, ...] = HORIZONS_PROTOCOLE,
    hypotheses_rendement_pct: tuple[float, ...] = (0.0, 5.0),
    phrase_categories: str = "",
) -> dict:
    """Rend la grille ENTIERE horizons x hypotheses, chaque chiffre porte sa source."""
    horizons = tuple(horizons)
    hypotheses = tuple(float(h) for h in hypotheses_rendement_pct)
    if capital_initial <= 0 and versement_annuel <= 0:
        raise GrilleIncomplete(
            "capital initial et versement tous les deux nuls : la grille ne dirait rien."
        )

    avertissements = _controler_grille(horizons, hypotheses)
    basse, haute, avert_bornes, phrases_a_lecran = _controler_bornes(
        borne_basse, borne_haute, phrase_categories
    )
    avertissements = avert_bornes + avertissements
    ecart_points = round(haute.valeur_pct - basse.valeur_pct, 6)
    ecart_publiable = ecart_points >= ECART_MINIMAL_POINTS
    # Le VRAI point marginal : borne basse -> borne basse + 1 point. Indisponible si ce +1 point
    # sortirait des bornes de saisie admises.
    point_suivant = basse.valeur_pct + 1.0
    marginal_publiable = point_suivant <= FRAIS_MAX_POINTS
    if marginal_publiable and not ecart_publiable:
        avertissements.append(
            "seul le coût du point suivant est publié : l'écart relevé entre les deux bornes "
            "est trop faible pour en tirer une moyenne. Ce chiffre ne décrit donc PAS l'écart "
            "entre les deux catégories relevées."
        )

    cases = []
    for annees in sorted(horizons):
        for rendement in hypotheses:
            cf_basse = capital_final(
                capital_initial, versement_annuel, annees, rendement, basse.valeur_pct
            )
            cf_haute = capital_final(
                capital_initial, versement_annuel, annees, rendement, haute.valeur_pct
            )
            cf_sans_frais = capital_final(
                capital_initial, versement_annuel, annees, rendement, 0.0
            )
            ecart_euros = cf_basse - cf_haute
            cf_point_suivant = (
                capital_final(capital_initial, versement_annuel, annees, rendement, point_suivant)
                if marginal_publiable
                else None
            )
            cases.append(
                {
                    "horizon_ans": annees,
                    "hypothese_rendement_brut_pct": rendement,
                    "capital_final_borne_basse": round(cf_basse, 2),
                    "capital_final_borne_haute": round(cf_haute, 2),
                    "capital_final_sans_frais": round(cf_sans_frais, 2),
                    "ecart_euros": round(ecart_euros, 2),
                    "ecart_en_pct_du_capital_sans_frais": (
                        round(100.0 * ecart_euros / cf_sans_frais, 4) if cf_sans_frais else None
                    ),
                    # Moyenne sur l'ecart releve — l'effet n'est pas lineaire, le nom le dit.
                    "cout_moyen_par_point_sur_lecart_releve_euros": (
                        round(ecart_euros / ecart_points, 2) if ecart_publiable else None
                    ),
                    # LR4 cond.3 : « ce que coute 1 point de frais en plus », le vrai.
                    "cout_du_point_de_frais_suivant_euros": (
                        round(cf_basse - cf_point_suivant, 2)
                        if cf_point_suivant is not None
                        else None
                    ),
                    # ⚠️ Le chiffre le PLUS GROS de la sortie, donc le plus tentant, et celui qui
                    # se dit le plus mal. Il compare la borne HAUTE a un fonds A FRAIS NULS, qui
                    # n'existe pas. Le Gardien (06/08) l'a repere sans regle : il en a une, et
                    # elle est portee par le nom du champ lui-meme.
                    "part_mangee_par_la_borne_haute_pct_VS_UN_FONDS_SANS_FRAIS_QUI_NEXISTE_PAS": (
                        round(100.0 * (cf_sans_frais - cf_haute) / cf_sans_frais, 4)
                        if cf_sans_frais
                        else None
                    ),
                }
            )

    definition = dict(DEFINITIONS_FRAIS[basse.definition])
    definition.pop("pages_autorisees", None)
    return {
        "moteur": "simulateur_frais.py",
        "episode": "PF « Le Test » ép. 3 — ETF",
        "calcule_le": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "definition_frais": {"cle": basse.definition, **definition},
        "convention_calcul": (
            "Intérêts composés, pas de temps mensuel. Chaque mois : performance brute, puis "
            "prélèvement des frais sur l'encours, puis versement (fin de mois). Les frais "
            "annuels f vérifient exactement (1 - f_mensuel)^12 = 1 - f."
        ),
        "hypotheses": {
            "capital_initial": capital_initial,
            "versement_annuel": versement_annuel,
            "horizons_ans": sorted(horizons),
            "hypotheses_rendement_brut_pct": list(hypotheses),
        },
        "bornes": {
            "basse": basse.en_dict(),
            "haute": haute.en_dict(),
            "ecart_points_de_frais": round(ecart_points, 6),
        },
        "publication": "grille_entiere_obligatoire",
        # CE QUI DOIT ARRIVER A L'ECRAN — et rien d'autre. Champ dedie (relecture du 06/08) :
        # `gate_conformite_ep3.py --exige-json` ne lit QUE celui-ci. Sans lui, la gate exigeait
        # que le script contienne mot pour mot les avertissements TECHNIQUES (« valeurs par
        # defaut du moteur… »), donc STOPpait sur un script conforme — et une gate qui crie au
        # loup se fait desactiver.
        "a_dire_a_lecran": [a for a in avertissements if a in phrases_a_lecran]
        + list(MENTIONS_OBLIGATOIRES),
        "mentions_obligatoires": list(MENTIONS_OBLIGATOIRES),
        "ce_que_ce_calcul_ne_prouve_pas": [
            "Il ne dit pas lequel choisir : il chiffre un écart de frais, rien d'autre.",
            "Il suppose la performance brute identique — ce qui n'arrive jamais.",
            "Les frais courants n'incluent ni l'écart achat-vente payé en Bourse, ni le "
            "courtage de l'investisseur, ni les frais d'enveloppe, ni la fiscalité : le chiffre "
            "SOUS-ESTIME le coût réel. En revanche les rétrocessions aux distributeurs sont "
            "DEDANS — ne pas les retrancher une seconde fois.",
            "Une fourchette de catégorie n'est pas le frais d'un produit.",
            "L'effet des frais n'est pas linéaire : « le coût moyen par point » est une moyenne "
            "sur l'écart relevé, pas le coût d'un point pris isolément — c'est pourquoi le coût "
            "du point suivant est publié à côté.",
            "La « part mangée par la borne haute » se mesure contre un fonds à frais nuls, qui "
            "n'existe pas. C'est le plus gros chiffre de cette sortie et le plus facile à mal "
            "dire : il ne peut pas s'écrire « les frais te prennent X % » — il ne compare à rien "
            "de réel.",
            "Les valeurs relevées agrègent investisseurs particuliers ET institutionnels (note "
            "de la table ESMA) : aucune ne peut s'annoncer comme « ce que TU paies ».",
            "Aucune de ces valeurs n'est une prévision : c'est de l'arithmétique sur des "
            "hypothèses affichées.",
        ],
        "avertissements": avertissements,
        "grille": cases,
    }


# ---------------------------------------------------------------------------
# CLI — lit le fichier de FAITS (le releve), ecrit le JSON de resultats
# ---------------------------------------------------------------------------
CHAMPS_BORNE = ("valeur_pct", "definition", "categorie", "source", "page", "url", "date_releve")


def _niveau_depuis_dict(d: object, quel: str) -> NiveauDeFrais:
    if not isinstance(d, dict):
        raise ValueError(f"borne « {quel} » : objet attendu, {type(d).__name__} reçu.")
    manquants = [c for c in CHAMPS_BORNE if c not in d]
    if manquants:
        # Champ ABSENT = fichier de faits incomplet (structure) -> rc 2. Champ PRESENT mais vide
        # ou invalide = refus LR3 -> rc 1, leve par NiveauDeFrais. La frontiere est la.
        raise ValueError(
            f"borne « {quel} » : champs absents du fichier de faits : {', '.join(manquants)}."
        )
    try:
        valeur = float(d["valeur_pct"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"borne « {quel} » : valeur_pct = {d['valeur_pct']!r} illisible. Attendu un nombre "
            "avec un POINT décimal (0.22), pas une virgule ni un texte."
        ) from exc
    return NiveauDeFrais(
        valeur_pct=valeur,
        definition=str(d["definition"]),
        categorie=str(d["categorie"]),
        source=str(d["source"]),
        page=str(d["page"]),
        url=str(d["url"]),
        date_releve=str(d["date_releve"]),
    )


def charger_faits(chemin: pathlib.Path) -> dict:
    """Lit le fichier de faits (le releve). Aucune valeur en dur dans ce module."""
    if not chemin.exists():
        raise FileNotFoundError(
            f"fichier de faits introuvable : {chemin}\n"
            "Le relevé des fourchettes publiques (ESMA/AMF) n'a pas encore été fait, ou le "
            "chemin est faux. Le moteur ne fabrique aucune valeur : il s'arrête."
        )
    # Les octets sont lus UNE SEULE FOIS, et l'empreinte est calculee sur EUX. Lire le fichier
    # deux fois (une pour le calcul, une pour le Fact-Lock) permettrait de sceller la sortie
    # avec l'empreinte d'un fichier qui n'est pas celui qui a produit les chiffres.
    octets = chemin.read_bytes()
    try:
        faits = json.loads(octets.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"fichier de faits illisible ({chemin}) : {exc}") from exc
    if isinstance(faits, dict):
        faits["_sha256_du_fichier_lu"] = hashlib.sha256(octets).hexdigest()
    if not isinstance(faits, dict):
        raise ValueError(
            f"fichier de faits mal formé ({chemin}) : un objet JSON est attendu, "
            f"{type(faits).__name__} trouvé."
        )
    return faits


def _liste_de(faits: dict, cle: str, defaut: tuple) -> tuple:
    valeur = faits.get(cle, defaut)
    if not isinstance(valeur, (list, tuple)):
        raise ValueError(
            f"champ « {cle} » du fichier de faits : liste attendue, "
            f"{type(valeur).__name__} reçu ({valeur!r})."
        )
    return tuple(valeur)


def _ecrire_atomique(chemin: pathlib.Path, contenu: str) -> None:
    """Ecriture atomique, avec repli : le `os.replace` peut echouer sous OneDrive.

    Le fichier temporaire cree a cote est pris en charge par la synchronisation, ce qui fait
    echouer le remplacement de facon intermittente — alors qu'une ecriture directe passerait.
    On garde donc l'atomicite quand elle marche, et on retombe sur l'ecriture directe sinon,
    plutot que de perdre un resultat correct pour une raison de synchro.
    """
    chemin.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(chemin.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(contenu)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    try:
        os.replace(tmp, chemin)
        return
    except OSError:
        pass
    # Repli : le remplacement a echoue (synchronisation OneDrive). On ecrit d'abord un fichier
    # `.part` COMPLET, on verifie sa taille, et seulement ensuite on ecrase la destination —
    # sinon un disque plein transformerait un resultat correct en fichier tronque.
    attendu = contenu.encode("utf-8")
    part = chemin.with_suffix(chemin.suffix + ".part")
    try:
        part.write_bytes(attendu)
        if part.stat().st_size != len(attendu):
            raise OSError(f"écriture incomplète dans {part}")
        chemin.write_bytes(attendu)
        print("  ⚠ écriture NON atomique (repli OneDrive) : le remplacement a échoué.")
    finally:
        for reste in (pathlib.Path(tmp), part):
            with contextlib.suppress(OSError):
                reste.unlink()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Simulateur d'impact des frais (ép. 3). Chaque chiffre porte sa source."
    )
    ap.add_argument("--faits", required=True, help="JSON du relevé (bornes + sources).")
    ap.add_argument("--sortie", default="resultats_ep3/frais_ep3.json", help="JSON de résultats.")
    ap.add_argument("--dry-run", action="store_true", help="calcule et affiche, n'écrit rien.")
    args = ap.parse_args(argv)

    chemin_faits = pathlib.Path(args.faits)
    try:
        faits = charger_faits(chemin_faits)
        bornes = faits.get("bornes")
        if not isinstance(bornes, dict) or "basse" not in bornes or "haute" not in bornes:
            raise ValueError(
                "le fichier de faits doit contenir un objet bornes avec basse et haute."
            )
        # TOUTES les hypothèses non portées par le relevé doivent se déclarer : une hypothèse de
        # rendement fabriquée par le moteur ne doit jamais passer pour une donnée relevée.
        defauts = [
            c
            for c in (
                "capital_initial",
                "versement_annuel",
                "horizons_ans",
                "hypotheses_rendement_brut_pct",
            )
            if c not in faits
        ]
        sortie = simuler_grille(
            borne_basse=_niveau_depuis_dict(bornes["basse"], "basse"),
            borne_haute=_niveau_depuis_dict(bornes["haute"], "haute"),
            capital_initial=float(faits.get("capital_initial", 10_000.0)),
            versement_annuel=float(faits.get("versement_annuel", 0.0)),
            horizons=_liste_de(faits, "horizons_ans", HORIZONS_PROTOCOLE),
            hypotheses_rendement_pct=tuple(
                float(h) for h in _liste_de(faits, "hypotheses_rendement_brut_pct", (0.0, 5.0))
            ),
            phrase_categories=str(faits.get("phrase_categories", "")),
        )
    except RefusDeConformite as exc:
        print(f"STOP — {type(exc).__name__} : {exc}")
        return 1
    # OSError et pas seulement FileNotFoundError : `--faits <un dossier>` ou un verrou OneDrive
    # sortaient en traceback + rc 1, donc indiscernables d'un refus de conformite.
    except (OSError, ValueError, TypeError) as exc:
        print(f"STOP — {exc}")
        return 2

    # Fact-Lock : l'empreinte vient des octets REELLEMENT utilises pour le calcul (calculee dans
    # `charger_faits`), pas d'une seconde lecture du fichier.
    sortie["faits"] = {
        "fichier": str(chemin_faits),
        "sha256": faits.get("_sha256_du_fichier_lu"),
    }
    if defauts:
        sortie["avertissements"].append(
            "valeurs par défaut du moteur, absentes du relevé : " + ", ".join(defauts)
        )

    texte = json.dumps(sortie, ensure_ascii=False, indent=2)
    if args.dry_run:
        print(texte)
        return 0
    try:
        _ecrire_atomique(pathlib.Path(args.sortie), texte)
    except OSError as exc:
        print(
            f"STOP — écriture impossible dans {args.sortie} : {exc}\n"
            "Le calcul, lui, était bon : ferme le fichier s'il est ouvert (Excel, éditeur, "
            "synchronisation OneDrive) et relance."
        )
        return 3
    print(f"FEU VERT — {len(sortie['grille'])} cases écrites dans {args.sortie}")
    for a in sortie["avertissements"]:
        print(f"  ⚠ {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
