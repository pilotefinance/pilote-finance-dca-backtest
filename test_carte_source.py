#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA GATE de `carte_source.py` — nommee AVANT le code (regle §6, 05/08/2026).

Un afficheur d'URL qui accepte n'importe quoi transforme « tout est verifiable » en decor :
le spectateur lit une adresse a l'ecran, la croit, et elle ne mene nulle part. Ces tests
verrouillent le refus. Le cas qui DOIT echouer compte autant que celui qui doit passer
(lecon du 03/08 : un comparateur ne se teste pas seulement sur ce qui marche).

Lancement : python -m pytest test_carte_source.py -q
"""
import pytest

from carte_source import SourceRefusee, dessiner_bandeau, libelle_source, verifier

SOURCE_OK = "https://www.insee.fr/fr/statistiques/8901234"


def _image_et_encre(marge_bas=38, taille=44, largeur=1920, hauteur=1080):
    """Dessine le bandeau et mesure l'ENCRE réellement posée. Rend (retour, haut, bas)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (largeur, hauteur), (0, 0, 0))
    d = ImageDraw.Draw(im)
    try:
        police = ImageFont.truetype("arialbd.ttf", taille)
    except OSError:
        # SKIP explicite : `load_default()` ignore la taille demandee, donc le test
        # « deux tailles s'alignent » comparerait deux fois la MEME police et serait vert par
        # construction. Un test tautologique est pire qu'un test absent — c'est la leçon du
        # 05/08 sur les gates qui mesurent la mauvaise chose. (3e passage code-reviewer)
        pytest.skip("police arialbd.ttf absente : mesure de rendu non concluante")
    retour = dessiner_bandeau(d, SOURCE_OK, largeur, hauteur, police, marge_bas=marge_bas)
    lignes = [y for y in range(hauteur) if any(im.getpixel((x, y)) != (0, 0, 0)
                                               for x in range(0, largeur, 3))]
    if not lignes:
        pytest.skip("aucune encre mesurable (police de repli sans rendu exploitable)")
    return retour, lignes[0], lignes[-1]


# --- ce qu'on doit ACCEPTER : les sources reelles de nos episodes ---------------
@pytest.mark.parametrize("url", [
    "https://bofip.impots.gouv.fr/bofip/1234-PGP.html",
    "https://www.insee.fr/fr/statistiques/8901234",
    "https://www.service-public.fr/particuliers/vosdroits/F2456",
    "https://shillerdata.com/",
    "https://fred.stlouisfed.org/series/DGS3MO",
    "https://www.amf-france.org/fr/actualites-publications",
    "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006307844",
])
def test_sources_officielles_acceptees(url):
    assert libelle_source(url)


def test_sous_domaine_officiel_accepte():
    assert verifier("https://bofip.impots.gouv.fr/x") == "bofip.impots.gouv.fr"


# --- ce qu'on doit REFUSER -----------------------------------------------------
def test_refuse_un_raccourcisseur():
    """Une URL raccourcie affichee a l'ecran est invérifiable : elle detruit le but."""
    with pytest.raises(SourceRefusee, match="raccourcisseur"):
        libelle_source("https://bit.ly/3xYzAbc")


def test_refuse_un_lien_daffiliation():
    with pytest.raises(SourceRefusee, match="affiliation"):
        libelle_source("https://try.elevenlabs.io/8zdlbv98rm1t")


def test_refuse_un_lien_avec_parametre_de_tracking():
    with pytest.raises(SourceRefusee, match="affiliation"):
        libelle_source("https://www.amazon.fr/dp/2361170566?tag=pilotefinance-21")


def test_refuse_un_domaine_hors_liste_blanche():
    """Un blog, un media, un forum : ce ne sont pas des sources primaires."""
    with pytest.raises(SourceRefusee, match="liste blanche"):
        libelle_source("https://unblogfinance.example/article-genial")


def test_refuse_http_non_securise():
    with pytest.raises(SourceRefusee, match="non https"):
        libelle_source("http://www.insee.fr/fr/statistiques/1")


@pytest.mark.parametrize("vide", ["", "   ", None])
def test_refuse_une_url_vide(vide):
    with pytest.raises(SourceRefusee, match="aucune URL"):
        libelle_source(vide)


def test_un_domaine_qui_CONTIENT_un_domaine_officiel_est_refuse():
    """« impots.gouv.fr.pirate.example » ne doit pas passer pour impots.gouv.fr."""
    with pytest.raises(SourceRefusee, match="liste blanche"):
        libelle_source("https://impots.gouv.fr.pirate.example/faux")


# --- lisibilite : le libelle doit rester court ---------------------------------
def test_le_libelle_reste_lisible():
    lib = libelle_source("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006307844")
    assert len(lib) <= 42, "trop long pour etre lu a l'ecran : %r" % lib


# --- L'INVARIANT CENTRAL : le libellé doit être une adresse VRAIE ---------------
# Ces deux tests remplacent ceux du 05/08 après-midi, qui verrouillaient le défaut :
# ils exigeaient `insee.fr/statistiques` — une adresse qui rend HTTP 500. Une gate verte
# sur un module faux est pire qu'une absence de gate.
@pytest.mark.parametrize("url", [
    "https://www.insee.fr/fr/statistiques/8901234",
    "https://bofip.impots.gouv.fr/bofip/1234-PGP.html",
    "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006307844",
    "https://www.impots.gouv.fr/particulier/questions/comment-declarer",
    "https://fred.stlouisfed.org/series/DGS3MO",
    # URL À PARAMÈTRES — la forme des sources FRED/INSEE de nos backtests. Absentes du jeu
    # au 3e passage, c'est ce qui a laissé passer le bloquant « query jetée en silence ».
    "https://fred.stlouisfed.org/graph/?g=1abcd",
    "https://www.insee.fr/fr/statistiques/8901234?page=2",
    "https://www.insee.fr/fr/statistiques/1#tableau-2",
])
def test_le_libelle_est_un_prefixe_ET_signale_toute_troncature(url):
    """Deux exigences, pas une : le libellé doit être un vrai préfixe de l'URL COMPLÈTE
    (query et fragment compris), et toute troncature doit porter une ellipsis.

    Le test du 2e passage ne comparait qu'au chemin : une query jetée restait « un préfixe »
    et passait. « Être un préfixe » ≠ « désigner la même page » — c'est la leçon du tour 2
    déplacée, pas soldée."""
    from urllib.parse import urlsplit
    lib = libelle_source(url)
    d = urlsplit(url)
    hote = (d.hostname or "").replace("www.", "", 1)
    reel = hote + d.path.rstrip("/")
    if d.query:
        reel += "?" + d.query
    if d.fragment:
        reel += "#" + d.fragment
    nu = lib.rstrip("…").rstrip("/")
    assert reel.startswith(nu), "libellé %r absent du début de %r" % (nu, reel)
    if nu != reel:
        assert lib.endswith("…"), (
            "libellé %r tronqué SANS ellipsis : il se lit comme une adresse complète alors "
            "qu'il en désigne une autre (URL réelle %r)" % (lib, reel))


def test_deux_pages_differentes_ne_rendent_pas_le_meme_libelle():
    """Un libellé qui ne distingue pas deux pages ne prouve rien.

    ⚠️ Limite ASSUMÉE, mesurée au 3e passage : avec LONGUEUR_MAX = 42, deux URL longues du
    même dossier (`…/vosdroits/F2456` et `…/F9999`) rendent le même libellé tronqué. On ne
    peut pas identifier une page en 42 caractères. L'ellipsis rend la chose honnête — le
    bandeau annonce alors un DOSSIER, pas une page — mais il ne faut pas croire l'inverse :
    ce test ne vaut que pour les URL qui tiennent entières.
    """
    a = libelle_source("https://www.insee.fr/fr/statistiques/8901234")
    b = libelle_source("https://www.insee.fr/fr/information/5555555")
    assert a != b, "les deux pages rendent %r : le bandeau n'identifie pas la source" % a
    assert not a.endswith("…") and not b.endswith("…"), "cas hors périmètre de ce test"


def test_deux_urls_du_meme_dossier_trop_longues_sont_signalees_tronquees():
    """Le cas inverse : on n'identifie pas la page, mais on ne prétend pas le contraire."""
    a = libelle_source("https://www.service-public.fr/particuliers/vosdroits/F2456")
    b = libelle_source("https://www.service-public.fr/particuliers/vosdroits/F9999")
    if a == b:
        assert a.endswith("…"), (
            "deux pages rendent %r sans ellipsis : le bandeau prétend désigner une page "
            "précise alors qu'il désigne un dossier" % a)


def test_la_troncature_est_signalee():
    lib = libelle_source("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006307844")
    assert lib.endswith("…"), "une adresse tronquée sans ellipsis se lit comme une adresse complète"


# --- Contournements de la liste blanche (mesurés le 05/08) ---------------------
def test_refuse_lantislash_qui_change_la_destination():
    """Les navigateurs lisent « \\ » comme « / » : la vraie destination est evil.example."""
    with pytest.raises(SourceRefusee, match="ntislash"):
        libelle_source("https://evil.example\\@insee.fr/dossier")


def test_refuse_un_port_explicite():
    with pytest.raises(SourceRefusee, match="ort explicite"):
        libelle_source("https://insee.fr:8443/fr/statistiques/1")


def test_le_point_final_ne_fait_pas_un_faux_refus():
    """« insee.fr. » et « insee.fr » désignent le même hôte."""
    assert libelle_source("https://insee.fr./fr/statistiques/1").startswith("insee.fr")


def test_userinfo_arobase_refuse():
    with pytest.raises(SourceRefusee, match="liste blanche"):
        libelle_source("https://insee.fr@evil.example/x")


# --- dessiner_bandeau : la fonction qui porte la leçon du 30/06 -----------------
def test_la_marge_basse_demandee_est_la_marge_reelle():
    """Mesuré le 05/08 avant correction : 30 px d'encre pour 38 demandés (décalage
    d'ascendante réintroduit par draw.text). L'écart croît avec la taille de police."""
    (_y, _h), _haut, bas = _image_et_encre(marge_bas=38)
    reelle = 1080 - 1 - bas
    assert abs(reelle - 38) <= 2, "marge basse réelle %d px pour 38 demandés" % reelle


def test_le_y_rendu_designe_bien_lencre():
    """Un appelant qui empile un bloc au-dessus doit pouvoir s'y fier."""
    (y, h), haut, bas = _image_et_encre()
    assert abs(y - haut) <= 2, "y rendu %d, encre à %d" % (y, haut)
    assert abs(h - (bas - haut + 1)) <= 2, "hauteur rendue %d, encre %d" % (h, bas - haut + 1)


def test_deux_tailles_de_police_salignent_sur_la_meme_marge():
    """C'est ce que le décalage d'ascendante cassait : il variait avec la taille."""
    (_a, _b), _h1, bas1 = _image_et_encre(taille=28)
    (_c, _d), _h2, bas2 = _image_et_encre(taille=56)
    assert abs(bas1 - bas2) <= 3, "bas d'encre %d vs %d : les bandeaux ne s'alignent pas" % (
        bas1, bas2)


def test_refuse_de_dessiner_hors_du_cadre():
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (120, 80), (0, 0, 0))
    d = ImageDraw.Draw(im)
    try:
        police = ImageFont.truetype("arialbd.ttf", 44)
    except OSError:
        pytest.skip("police système absente")
    with pytest.raises(SourceRefusee, match="deborde"):
        dessiner_bandeau(d, SOURCE_OK, 120, 80, police)


def test_le_refus_leve_avant_tout_dessin():
    """Une URL refusée ne doit pas laisser la moitié d'un bandeau sur la carte."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (600, 200), (0, 0, 0))
    d = ImageDraw.Draw(im)
    police = ImageFont.load_default()
    with pytest.raises(SourceRefusee):
        dessiner_bandeau(d, "https://bit.ly/xyz", 600, 200, police)
    assert not im.getbbox(), "de l'encre a été posée malgré le refus"
