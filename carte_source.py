#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# carte_source.py — OPTION « URL officielle courte affichee a l'ecran ».
#
# Origine : audit TikTok du 05/08/2026 (@ia_irl, 111 k vues, Claude branche sur le BOFiP).
# Son procede reutilisable n'est pas l'outil, c'est la PREUVE PAR LA SOURCE CLIQUABLE : chaque
# reponse ressort le lien vers l'article officiel. C'est exactement notre Fact-Lock, mais
# MONTRE a l'ecran au lieu d'etre range dans un fichier que personne ne lit.
#
# A partir de l'EPISODE 3. Aucun re-render retroactif (decision Aleksandar, 05/08/2026).
#
# ---------------------------------------------------------------------------
# SA GATE (nommee AVANT le code, regle §6 de methode-agentique.md)
# ---------------------------------------------------------------------------
# `test_carte_source.py` : le module doit REFUSER d'afficher une URL non officielle, un
# raccourcisseur, ou une URL vide — et accepter les domaines sources reellement utilises par
# le studio. Un afficheur d'URL qui accepte n'importe quoi transformerait la promesse
# « tout est verifiable » en decor : le spectateur lit une adresse a l'ecran, la croit, et
# elle ne mene nulle part. Ce serait pire que de ne rien afficher.
#
# ---------------------------------------------------------------------------
# CONTRAT
# ---------------------------------------------------------------------------
# libelle_source(url) -> str
#   Rend la forme COURTE affichable (domaine + chemin tronque), ex :
#     "https://bofip.impots.gouv.fr/bofip/1234-PGP.html" -> "bofip.impots.gouv.fr"
#     "https://www.insee.fr/fr/statistiques/1234"        -> "insee.fr/statistiques"
#   Leve SourceRefusee si l'URL n'est pas affichable (voir plus bas).
#
# dessiner_bandeau(draw, url, largeur, hauteur, police, ...) -> int
#   Ecrit « source : <libelle> » en bas de carte. Rend le y utilise (chainage, cf. la lecon
#   du 30/06 sur les blocs qui se chevauchent). Leve SourceRefusee avant tout dessin.
#
# REFUS (SourceRefusee, jamais un rendu silencieux) :
#   - URL vide ou non https ;
#   - domaine hors liste blanche des sources officielles/primaires du studio ;
#   - raccourcisseur d'URL (bit.ly, t.co, lnkd.in…) : une adresse raccourcie affichee a
#     l'ecran est INVERIFIABLE par le spectateur — c'est l'inverse du but recherche ;
#   - URL de redirection/affiliation (try.*, *?tag=, utm_*) : ce n'est pas une source.
"""Affichage a l'ecran d'une URL de source officielle, avec garde-fou anti-fiction."""
import re
from urllib.parse import urlsplit

# Sources primaires reellement utilisees par le studio (Fact-Lock des episodes publies) +
# les institutions dont on cite couramment les chiffres. A completer AU CAS PAR CAS, jamais
# en ouvrant a un domaine generique : c'est la liste blanche qui fait la valeur de l'affichage.
DOMAINES_OFFICIELS = {
    # France — administration et regulateurs
    "impots.gouv.fr", "bofip.impots.gouv.fr", "service-public.fr", "legifrance.gouv.fr",
    "insee.fr", "amf-france.org", "banque-france.fr", "economie.gouv.fr", "urssaf.fr",
    "ameli.fr", "info-retraite.fr", "orias.fr",
    # Europe / international
    "ecb.europa.eu", "esma.europa.eu", "eur-lex.europa.eu", "oecd.org", "imf.org",
    # Donnees de marche utilisees par nos backtests
    "shillerdata.com", "fred.stlouisfed.org", "stlouisfed.org", "msci.com", "spglobal.com",
}
RACCOURCISSEURS = {"bit.ly", "t.co", "lnkd.in", "tinyurl.com", "ow.ly", "buff.ly",
                   "rebrand.ly", "cutt.ly", "s.id", "urlz.fr", "lc.cx"}
RE_PARAM_TRACKING = re.compile(r"[?&](tag|utm_[a-z]+|aff|ref)=", re.I)
# Sous-domaines de redirection d'affiliation (try.elevenlabs.io, go.*, link.*). Teste sur le
# DOMAINE, pas sur l'URL entiere : « https://try... » ne commence pas par « try. ».
RE_DOMAINE_REDIRECTION = re.compile(r"^(try|go|link|click|track|r)\.", re.I)
LONGUEUR_MAX = 42  # au-dela, illisible en vignette mobile (regle miniature.md : lisible a 150 px)


class SourceRefusee(ValueError):
    """L'URL ne peut pas etre affichee comme source. Le message dit pourquoi."""


RE_HOTE_SAIN = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")


def _domaine(url):
    hote = (urlsplit(url).hostname or "").lower().rstrip(".")  # « insee.fr. » == « insee.fr »
    return hote[4:] if hote.startswith("www.") else hote


def verifier(url):
    """Valide l'URL comme source affichable. Leve SourceRefusee, sinon rend le domaine."""
    if not url or not str(url).strip():
        raise SourceRefusee("aucune URL fournie : on n'affiche pas un bandeau « source » vide.")
    url = str(url).strip()
    if not url.lower().startswith("https://"):
        raise SourceRefusee("URL non https (%s) : une source officielle l'est toujours." % url)
    # ANTISLASH : les navigateurs (WHATWG) traitent « \ » comme « / », Python non. Sur
    # « https://evil.example\@insee.fr/x », urlsplit rend l'hote « insee.fr » alors que le
    # navigateur ira sur evil.example. On afficherait donc « insee.fr » sous un chiffre venu
    # d'ailleurs. Divergence dans le mauvais sens -> refus sec. (code-reviewer, 05/08/2026)
    if "\\" in url:
        raise SourceRefusee("antislash dans l'URL : lecture ambigue entre navigateur et "
                            "analyseur, on n'affiche pas une source qu'on ne sait pas lire.")
    # `urlsplit` peut lever tout seul (« https://[oops/x » -> ValueError: Invalid IPv6 URL) :
    # un appelant qui fait `except SourceRefusee` se prendrait un crash en plein rendu, alors
    # que le contrat promet SourceRefusee. (4e passage)
    try:
        decoupe = urlsplit(url)
        dom = _domaine(url)
    except ValueError:
        raise SourceRefusee("URL illisible : %s" % url) from None
    if not dom:
        raise SourceRefusee("URL illisible : %s" % url)
    if not RE_HOTE_SAIN.match(dom):
        raise SourceRefusee("nom d'hote inhabituel (%r) : refus par principe." % dom)
    try:
        port = decoupe.port
    except ValueError:
        raise SourceRefusee("port illisible dans l'URL : %s" % url) from None
    if port is not None:
        # Le libelle affiche le domaine seul : « insee.fr:8443 » deviendrait « insee.fr »,
        # ce qui masquerait une destination differente.
        raise SourceRefusee("port explicite (%s) : une source officielle n'en a pas." % port)
    if dom in RACCOURCISSEURS:
        raise SourceRefusee(
            "raccourcisseur (%s) : une adresse raccourcie affichee a l'ecran est INVERIFIABLE "
            "par le spectateur — elle detruit exactement ce qu'on veut prouver." % dom)
    if RE_DOMAINE_REDIRECTION.match(dom) or RE_PARAM_TRACKING.search(url):
        raise SourceRefusee("lien de redirection/affiliation (%s) : ce n'est pas une source, "
                            "c'est un lien commercial." % dom)
    if dom not in DOMAINES_OFFICIELS and not any(
            dom.endswith("." + d) for d in DOMAINES_OFFICIELS):
        raise SourceRefusee(
            "domaine hors liste blanche : %s. Si c'est une vraie source primaire, ajoute-la "
            "explicitement a DOMAINES_OFFICIELS — jamais d'ouverture generique." % dom)
    return dom


def libelle_source(url, longueur_max=LONGUEUR_MAX):
    """Forme courte affichable — TOUJOURS un vrai prefixe de l'URL reelle.

    ⚠️ Corrige le 05/08/2026 apres code-reviewer, defaut ANTI-FICTION avere. La premiere
    version sautait les segments « inutiles » puis recollait un segment profond derriere le
    domaine : `insee.fr/fr/statistiques/8901234` devenait `insee.fr/statistiques`, qui rend un
    **HTTP 500** ; `bofip.impots.gouv.fr/bofip/1234-PGP.html` devenait `bofip.impots.gouv.fr/bofip`,
    qui rend un **404**. Le spectateur lisait a l'ecran une adresse qui n'existe pas — soit
    exactement ce que l'en-tete de ce fichier qualifie de « pire que de ne rien afficher ».
    Pire : deux pages differentes du meme dossier rendaient le MEME libelle, donc le bandeau
    « prouvait » quelque chose qu'il n'identifiait pas.

    Regle desormais : on ne garde que des segments CONSECUTIFS depuis la racine, jamais de
    saut, et toute troncature est signalee par une ellipsis. Invariant verifie par la gate :
    `libelle.rstrip('/…')` est toujours un prefixe de `domaine + chemin`.
    """
    dom = verifier(url)
    decoupe = urlsplit(str(url).strip())  # strip : sinon les espaces finissent DESSINES
    # Segments vides (`//fr//x`) et « .. » : ecrases ou reinterpretes, le libelle cesserait
    # d'etre un prefixe litteral de l'URL — et « /fr/../evil/x » s'afficherait « /fr/../evil »
    # alors que le navigateur ira sur « /evil ». Meme divergence que l'antislash : on refuse.
    brut = [s for s in decoupe.path.split("/")]
    # `%2e%2e` EST un segment double-point pour un navigateur (spec WHATWG) : sans ce test,
    # « /fr/%2e%2e/evil/x » s'affichait tel quel alors que le navigateur va sur « /evil/x ».
    # Meme divergence que l'antislash, en pourcent-encode. (4e passage)
    if any(s == ".." for s in brut) or "//" in decoupe.path or "%2e" in decoupe.path.lower():
        raise SourceRefusee("chemin ambigu (« .. », double barre ou point encode) : la "
                            "destination reelle differe de ce qui serait affiche.")
    chemin = [s for s in brut if s]
    # QUERY / FRAGMENT (bloquant trouve au 3e passage, 05/08/2026) : les jeter en silence
    # rejoue le defaut du tour 2 sous une autre forme. `fred.stlouisfed.org/graph/?g=1abcd`
    # devenait « fred.stlouisfed.org/graph » — une page qui EXISTE, mais qui n'est pas le
    # graphique source. Or les URL FRED et INSEE a parametres sont justement les sources de
    # nos backtests. Une adresse tronquee doit TOUJOURS le dire.
    tronque = bool(decoupe.query or decoupe.fragment)
    if not chemin:
        return dom + "/…" if tronque else dom
    libelle = dom
    for seg in chemin:  # segments DANS L'ORDRE, sans jamais en sauter un
        candidat = "%s/%s" % (libelle, seg)
        if len(candidat) + 2 > longueur_max:  # +2 : la place de l'ellipsis
            return libelle + "/…"
        libelle = candidat
    return libelle + "…" if tronque else libelle


def dessiner_bandeau(draw, url, largeur, hauteur, police, couleur=(150, 200, 220),
                     marge_bas=38, prefixe="source : ", longueur_max=LONGUEUR_MAX):
    """Ecrit « source : <libelle> » en bas de carte. Rend (y_encre, hauteur_encre).

    ⚠️ Placement corrige le 05/08/2026 (code-reviewer). `draw.text` ancre en HAUT DE LA BOITE
    DE LIGNE, pas en haut de l'encre : calculer `h = bas - haut` puis poser l'ancre a
    `hauteur - marge - h` retire l'ascendante que `draw.text` va reintroduire. Mesure : marge
    basse reelle 30 px pour 38 demandes, ecart egal a `haut` (8 px a 44 px de police) — il
    CROIT avec la taille et VARIE selon les glyphes, donc deux bandeaux de tailles differentes
    ne s'alignent pas. Meme famille que le bug du 30/06. On ancre desormais sur le BAS de la
    bbox, et on annule l'approche gauche.

    Rend `(y_encre, hauteur_encre)` — l'encre, pas l'ancre de dessin : un appelant qui empile
    un bloc au-dessus doit pouvoir s'y fier sans reprendre le decalage.

    `longueur_max` (ajout 08/08/2026, ep. 3) : un PDF d'institution a une URL profonde
    (`esma.europa.eu/sites/default/files/2026-03/ESMA50-...pdf`). Affichee tronquee, elle est
    litteralement exacte mais personne ne la retapera — le but du bandeau est qu'un spectateur
    PUISSE aller voir. Une carte peut donc demander une forme plus courte (le domaine seul) ;
    l'ellipsis dit toujours que l'adresse est tronquee, et l'URL complete reste en description.
    """
    libelle = prefixe + libelle_source(url, longueur_max)  # leve AVANT de dessiner quoi que ce soit
    gauche, haut, droite, bas = draw.textbbox((0, 0), libelle, font=police)
    w = droite - gauche
    if w > largeur:
        raise SourceRefusee(
            "le bandeau (%d px) deborde de la carte (%d px) : reduis la police ou raccourcis "
            "le libelle — un texte coupe au bord ne prouve rien." % (w, largeur))
    y_ancre = hauteur - marge_bas - bas
    # « Un texte coupe au bord ne prouve rien » vaut AUSSI en haut. Mesure du 3e passage :
    # sur une carte 1920x60 a 44 px de police, y_ancre valait -19 (moitie haute du texte
    # coupee) sans le moindre refus ; avec marge_bas > hauteur, plus rien n'etait dessine,
    # en silence. Un bandeau invisible ou ampute est pire qu'une absence de bandeau : on
    # croit avoir affiche la source.
    if marge_bas >= hauteur or y_ancre + haut < 0:
        raise SourceRefusee(
            "le bandeau ne tient pas en hauteur (carte %d px, marge %d px, texte %d px) : "
            "il serait coupe ou invisible." % (hauteur, marge_bas, bas - haut))
    draw.text(((largeur - w) // 2 - gauche, y_ancre), libelle, font=police, fill=couleur)
    return y_ancre + haut, bas - haut
