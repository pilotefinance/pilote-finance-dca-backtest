#!/usr/bin/env python3
"""LA GATE DU MOTEUR — `simulateur_frais.py` doit REFUSER avant de calculer.

Un simulateur de frais qui calcule tout ce qu'on lui donne est un piege : il produira sans
broncher la comparaison « frais courants d'un ETF » contre « incidence des couts annuels d'un
DIC », et le chiffre sortira juste — arithmetiquement juste, editorialement faux. C'est la
faute « prix vs rendement total » de l'ep. 2, celle qu'on a jure de ne pas rejouer.

Ces tests verifient donc TROIS choses, dans cet ordre :
  1. les REFUS (la conformite est du code, pas de la prose) ;
  2. l'arithmetique (verifiable a la main, sinon le test ne prouve rien) ;
  3. les PANNES revendiquees par le tribunal des cas — une panne annoncee sans test est une
     promesse, pas une protection (relecture code-reviewer du 06/08/2026).

Lancer : python -m pytest test_simulateur_frais.py -q
"""
import json
import pathlib
import subprocess
import sys

import pytest

import simulateur_frais as sf
from simulateur_frais import (
    DEFINITIONS_FRAIS,
    HORIZONS_PROTOCOLE,
    BornesIncomparables,
    DefinitionNonSimulable,
    GrilleIncomplete,
    NiveauDeFrais,
    SourceManquante,
    capital_final,
    simuler_grille,
)

SOURCE = "ESMA Market Report — Costs and Performance of EU Retail Investment Products 2025"
URL = "https://www.esma.europa.eu/sites/default/files/2026-03/rapport.pdf"
DATE = "2026-08-06"
DOSSIER = pathlib.Path(sf.__file__).parent
# Une phrase LR4 cond.1 recevable : elle nomme les deux categories et fait une vraie phrase.
CAT_A = "UCITS actions — ETF"
CAT_B = "UCITS actions — gestion active"
PHRASE_OK = (
    f"Ces deux chiffres sont des moyennes de deux catégories différentes de fonds actions — "
    f"« {CAT_A} » et « {CAT_B} » — publiées le même jour dans le même tableau de l'ESMA."
)


def niveau(valeur, **kw):
    """Un niveau de frais valide, dont on ne surcharge que ce que le test veut changer."""
    base = dict(
        definition="ongoing_costs_esma",
        categorie=CAT_A,
        source=SOURCE,
        page="p. 18, table MR-CP.14",
        url=URL,
        date_releve=DATE,
    )
    base.update(kw)
    return NiveauDeFrais(valeur_pct=valeur, **base)


def grille(basse=0.21, haute=1.28, **kw):
    """La grille du protocole, avec des bornes valides par defaut."""
    kw.setdefault("hypotheses_rendement_pct", (0.0, 5.0))
    return simuler_grille(niveau(basse), niveau(haute), **kw)


# ---------------------------------------------------------------------------
# 1. LES REFUS — source, definition, page, url, date
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("champ", ["categorie", "source", "page", "url", "date_releve"])
def test_refuse_un_chiffre_sans_sa_source(champ):
    """LR3 : un chiffre de frais sans source, sans page ou sans date ne se monte pas."""
    with pytest.raises(SourceManquante):
        niveau(0.21, **{champ: ""})


def test_refuse_une_definition_inventee():
    with pytest.raises(SourceManquante):
        niveau(0.21, definition="ter_maison")


@pytest.mark.parametrize("valeur", [-0.1, 10.1, 22.0])
def test_refuse_une_valeur_hors_bornes(valeur):
    """22 saisi pour 0,22 % est l'erreur de saisie la plus probable : elle doit STOPper."""
    with pytest.raises(SourceManquante):
        niveau(valeur)


def test_refuse_la_page_piegee_MR_CP_4():
    """La table p. 12 EXCLUT les ETF : un chiffre pris la et dit « ETF » serait faux."""
    with pytest.raises(SourceManquante) as exc:
        niveau(0.21, page="p. 12, table MR-CP.4")
    assert "MR-CP.4" in str(exc.value)


def test_refuse_une_page_illisible():
    with pytest.raises(SourceManquante):
        niveau(0.21, page="quelque part dans le rapport")


def test_la_table_piegee_ne_se_blanchit_pas_en_citant_une_table_autorisee_a_cote():
    """« p. 12 et p. 18 » passait : le controle etait une intersection, pas une inclusion."""
    with pytest.raises(SourceManquante):
        niveau(0.21, page="p. 12 et p. 18, tables MR-CP.4 et MR-CP.14")


def test_une_definition_sans_table_autorisee_ne_court_circuite_pas_le_controle():
    """`incidence_couts_annuels_dic` n'a pas de table chiffree : elle n'est pas non plus simulable.

    Le contrôle de page ne s'applique pas à elle (rien à contrôler), mais elle est bloquée en
    amont par `DEFINITIONS_SIMULABLES` — il ne doit pas exister de chemin où l'absence de table
    autorisée serve de passe-droit.
    """
    n = niveau(0.21, definition="incidence_couts_annuels_dic", page="n'importe quoi")
    assert n.definition not in sf.DEFINITIONS_SIMULABLES
    with pytest.raises(DefinitionNonSimulable):
        simuler_grille(n, niveau(1.28, definition="incidence_couts_annuels_dic", page="idem"))


def test_accepte_les_pages_autorisees():
    for page in ("p. 6", "p. 18, table MR-CP.14", "p.19"):
        assert niveau(0.21, page=page).valeur_pct == 0.21


def test_refuse_une_url_hors_liste_blanche_via_carte_source():
    """On reutilise la liste blanche de carte_source : refuse au relevé, pas au rendu."""
    with pytest.raises(SourceManquante) as exc:
        niveau(0.21, url="https://comparateur-etf-pas-cher.example.com/frais")
    assert "carte_source" in str(exc.value)


@pytest.mark.parametrize("date", ["06/08/2026", "été 2026", "2026-13-01"])
def test_refuse_une_date_qui_nen_est_pas_une(date):
    with pytest.raises(SourceManquante):
        niveau(0.21, date_releve=date)


# ---------------------------------------------------------------------------
# 2. LES DEUX VERROUS CENTRAUX (point n°4 du Gardien)
# ---------------------------------------------------------------------------
def test_verrou_1_deux_definitions_ne_se_comparent_pas():
    """Frais courants contre incidence des couts annuels du DIC : refus, sans contournement."""
    with pytest.raises(BornesIncomparables) as exc:
        simuler_grille(
            niveau(0.21),
            niveau(1.28, definition="incidence_couts_annuels_dic", page="p. 6"),
            phrase_categories=PHRASE_OK,
        )
    assert "ne mesurent pas la même chose" in str(exc.value)


def test_verrou_2_une_mesure_non_recurrente_ne_se_compose_pas():
    """Le trou du verrou 1 : DEUX bornes en frais d'entree, composees comme une charge annuelle.

    Arithmetiquement juste, editorialement faux — c'est exactement le cas que le protocole
    interdit, et il passait avant la relecture du 06/08.
    """
    basse = niveau(0.21, definition="couts_ponctuels_esma", page="p. 14")
    haute = niveau(1.28, definition="couts_ponctuels_esma", page="p. 14")
    with pytest.raises(DefinitionNonSimulable) as exc:
        simuler_grille(basse, haute)
    assert "taux annuel" in str(exc.value)


def test_seule_la_mesure_recurrente_est_simulable():
    assert frozenset({"ongoing_costs_esma"}) == sf.DEFINITIONS_SIMULABLES
    assert set(sf.DEFINITIONS_SIMULABLES) < set(DEFINITIONS_FRAIS)


def test_refuse_deux_sources_differentes():
    with pytest.raises(BornesIncomparables):
        simuler_grille(niveau(0.21), niveau(1.28, source="AMF, autre étude"))


def test_refuse_deux_dates_de_releve_differentes():
    with pytest.raises(BornesIncomparables):
        simuler_grille(niveau(0.21), niveau(1.28, date_releve="2025-01-01"))


def test_refuse_deux_categories_sans_phrase_davertissement():
    with pytest.raises(BornesIncomparables) as exc:
        simuler_grille(niveau(0.21), niveau(1.28, categorie=CAT_B))
    assert "MÊME PHRASE" in str(exc.value)


@pytest.mark.parametrize(
    "phrase",
    [
        "x",
        "deux catégories différentes",
        "ok " * 25,
        # Le collage : les deux libelles bout a bout + du remplissage. Il passait la v1.
        f"{CAT_A} {CAT_B} zzzzzzzzzzzzzzzzzzzz.",
        # Assez longue, nomme les deux, mais ne dit pas qu'elles different, et ne finit pas.
        f"On compare « {CAT_A} » avec « {CAT_B} » sur le même tableau de l'ESMA publié en mars",
    ],
)
def test_la_derogation_exige_une_VRAIE_phrase_qui_nomme_les_deux_categories(phrase):
    """Une chaine non vide, ni un collage des deux libelles, ne deverrouillent LR4 cond.1."""
    with pytest.raises(BornesIncomparables):
        simuler_grille(niveau(0.21), niveau(1.28, categorie=CAT_B), phrase_categories=phrase)


def test_accepte_deux_categories_AVEC_la_phrase_et_la_republie():
    out = simuler_grille(niveau(0.21), niveau(1.28, categorie=CAT_B), phrase_categories=PHRASE_OK)
    assert PHRASE_OK in out["avertissements"]


# ---------------------------------------------------------------------------
# 3. LA GRILLE — entiere, avec le 0 %, jamais amputee
# ---------------------------------------------------------------------------
def test_refuse_une_grille_sans_lhypothese_zero_pourcent():
    with pytest.raises(GrilleIncomplete) as exc:
        grille(hypotheses_rendement_pct=(5.0, 7.0))
    assert "0 %" in str(exc.value)


def test_refuse_une_seule_hypothese_de_rendement():
    with pytest.raises(GrilleIncomplete):
        grille(hypotheses_rendement_pct=(0.0,))


def test_refuse_deux_hypotheses_identiques_deguisees_en_deux():
    """(0 %, 0 %) satisfaisait « au moins deux » : il faut deux valeurs DISTINCTES."""
    with pytest.raises(GrilleIncomplete):
        grille(hypotheses_rendement_pct=(0.0, 0.0))


@pytest.mark.parametrize("horizons", [(), (0,), (-10, 20), (10.9, 20, 30), (10, 20, True)])
def test_refuse_un_horizon_absurde(horizons):
    with pytest.raises(GrilleIncomplete):
        grille(horizons=horizons)


@pytest.mark.parametrize("horizons", [(30,), (20, 30), (10, 30), (5, 10, 20)])
def test_refuse_une_grille_amputee_dun_horizon_du_protocole(horizons):
    """LR4(b) : « 30 ans est un cherry-picking d'horizon ». On peut ajouter, jamais retirer."""
    with pytest.raises(GrilleIncomplete) as exc:
        grille(horizons=horizons)
    assert "cherry-picking" in str(exc.value)


def test_accepte_un_horizon_supplementaire():
    out = grille(horizons=(5, 10, 20, 30))
    assert sorted({c["horizon_ans"] for c in out["grille"]}) == [5, 10, 20, 30]


def test_refuse_une_hypothese_de_rendement_qui_devient_une_promesse():
    with pytest.raises(GrilleIncomplete):
        grille(hypotheses_rendement_pct=(0.0, 30.0))


def test_signale_une_hypothese_elevee_sans_la_refuser():
    out = grille(hypotheses_rendement_pct=(0.0, 12.0))
    assert any("élevée" in a for a in out["avertissements"])


def test_refuse_une_grille_sans_capital_ni_versement():
    """Capital nul : toutes les cases a zero, en FEU VERT — c'etait une sortie muette."""
    with pytest.raises(GrilleIncomplete):
        grille(capital_initial=0.0, versement_annuel=0.0)


def test_la_grille_du_protocole_est_bien_10_20_30_fois_les_hypotheses():
    out = grille(hypotheses_rendement_pct=(0.0, 5.0, 7.0))
    assert HORIZONS_PROTOCOLE == (10, 20, 30)
    assert len(out["grille"]) == 3 * 3
    assert {c["horizon_ans"] for c in out["grille"]} == {10, 20, 30}
    assert out["publication"] == "grille_entiere_obligatoire"


def test_aucune_fonction_publiable_ne_rend_une_seule_case():
    """`capital_final` est une brique NUE (ni source ni definition) : elle ne publie rien.

    Ce que ce test verrouille : la surface publique du module. Toute nouvelle fonction exportee
    doit etre ajoutee ici en conscience — c'est le moment ou quelqu'un tenterait d'exposer
    « la » case.
    """
    assert set(sf.__all__) == {
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
    }
    assert "grille" in simuler_grille(niveau(0.21), niveau(1.28))


# ---------------------------------------------------------------------------
# 4. L'ARITHMETIQUE — verifiable a la main, sinon le test ne prouve rien
# ---------------------------------------------------------------------------
def test_a_zero_pourcent_le_capital_vaut_exactement_C_fois_un_moins_f_puissance_N():
    """La convention figee : (1 - f_mensuel)^12 == 1 - f. Donc 10 000 * (1-0,01)^10 sur 10 ans."""
    attendu = 10_000.0 * (1.0 - 0.01) ** 10
    obtenu = capital_final(10_000.0, 0.0, 10, 0.0, 1.0)
    assert obtenu == pytest.approx(attendu, rel=1e-12)
    assert obtenu == pytest.approx(9_043.82, abs=0.01)


def test_sans_frais_ni_versement_cest_la_capitalisation_pure():
    assert capital_final(10_000.0, 0.0, 20, 5.0, 0.0) == pytest.approx(
        10_000.0 * 1.05**20, rel=1e-12
    )


def test_les_frais_reduisent_toujours_le_capital():
    for rendement in (-2.0, 0.0, 5.0, 7.0):
        for annees in (10, 20, 30):
            sans = capital_final(10_000.0, 0.0, annees, rendement, 0.0)
            avec = capital_final(10_000.0, 0.0, annees, rendement, 0.5)
            assert avec < sans


def test_un_rendement_negatif_reste_une_hypothese_legitime():
    assert capital_final(10_000.0, 0.0, 10, -2.0, 0.2) < 10_000.0


def test_les_versements_sont_pris_en_compte_douze_fois_par_an():
    assert capital_final(0.0, 1_200.0, 10, 0.0, 0.0) == pytest.approx(12_000.0, abs=1e-6)


def test_le_versement_de_fin_de_mois_ne_subit_pas_les_frais_du_mois():
    """La convention est explicite : perf, puis frais, PUIS versement. Elle doit se voir.

    Un seul mois, 1 200 €/an = 100 € verses : le capital final doit valoir exactement le
    capital initial ampute des frais du mois, PLUS 100 € intacts.
    """
    initial, frais = 10_000.0, 6.0
    fm = 1.0 - (1.0 - frais / 100.0) ** (1.0 / 12)
    obtenu = capital_final(initial, 1_200.0, 1, 0.0, frais)
    # Un an = 12 mois de (encours * (1 - fm) + 100).
    attendu = initial
    for _ in range(12):
        attendu = attendu * (1.0 - fm) + 100.0
    assert obtenu == pytest.approx(attendu, rel=1e-12)
    assert obtenu > initial * (1.0 - frais / 100.0)


@pytest.mark.parametrize("frais", [-0.1, 10.1])
def test_capital_final_refuse_un_taux_de_frais_hors_contrat(frais):
    """Meme contrat que NiveauDeFrais : deux bornes differentes seraient un piege."""
    with pytest.raises(ValueError):
        capital_final(10_000.0, 0.0, 10, 0.0, frais)


# ---------------------------------------------------------------------------
# 5. LE COUT D'UN POINT DE FRAIS — moyenne et point marginal, nommes pour ce qu'ils sont
# ---------------------------------------------------------------------------
def _case(out, annees, rendement):
    return next(
        c
        for c in out["grille"]
        if c["horizon_ans"] == annees and c["hypothese_rendement_brut_pct"] == rendement
    )


def test_avec_un_ecart_dexactement_un_point_la_moyenne_est_lecart():
    out = grille(basse=0.20, haute=1.20)
    case = _case(out, 10, 0.0)
    assert case["cout_moyen_par_point_sur_lecart_releve_euros"] == pytest.approx(
        case["ecart_euros"], abs=0.01
    )
    attendu = 10_000.0 * (0.998**10 - 0.988**10)  # calcul a la main
    assert case["ecart_euros"] == pytest.approx(attendu, abs=0.01)


def test_le_point_marginal_nest_PAS_la_moyenne_quand_lecart_depasse_un_point():
    """L'effet des frais n'est pas lineaire : les deux chiffres doivent differer, et le dire."""
    out = grille(basse=0.0, haute=2.0)
    case = _case(out, 30, 5.0)
    moyenne = case["cout_moyen_par_point_sur_lecart_releve_euros"]
    marginal = case["cout_du_point_de_frais_suivant_euros"]
    attendu = capital_final(10_000.0, 0.0, 30, 5.0, 0.0) - capital_final(
        10_000.0, 0.0, 30, 5.0, 1.0
    )
    assert marginal == pytest.approx(attendu, abs=0.01)
    assert marginal > moyenne  # le 1er point coute plus cher que le 2e
    assert any("pas linéaire" in m for m in out["ce_que_ce_calcul_ne_prouve_pas"])


def test_un_ecart_infime_ne_publie_aucun_cout_par_point():
    """0.22 contre 0.2200001 donnait « écart 0,00 € » ET « 2 814 € par point ». Plus jamais."""
    out = grille(basse=0.22, haute=0.2200001)
    for case in out["grille"]:
        assert case["cout_moyen_par_point_sur_lecart_releve_euros"] is None
    assert any("inférieur à" in a for a in out["avertissements"])


def test_bornes_egales_ecart_nul_et_pas_de_division_par_zero():
    out = grille(basse=0.21, haute=0.21)
    assert all(c["ecart_euros"] == 0 for c in out["grille"])
    assert all(c["cout_moyen_par_point_sur_lecart_releve_euros"] is None for c in out["grille"])
    # Le point marginal reste calculable et publie : il faut alors dire qu'il ne decrit PAS
    # l'ecart entre les deux categories relevees, sinon la carte ment par juxtaposition.
    assert all(c["cout_du_point_de_frais_suivant_euros"] is not None for c in out["grille"])
    assert any("ne décrit donc PAS l'écart" in a for a in out["avertissements"])


def test_le_seuil_decart_ne_depend_pas_du_bruit_flottant():
    """0,28-0,27 et 0,29-0,28 valent tous deux 0,01 point : ils doivent se comporter pareil."""
    a = grille(basse=0.27, haute=0.28)
    b = grille(basse=0.28, haute=0.29)
    publie = lambda out: out["grille"][0]["cout_moyen_par_point_sur_lecart_releve_euros"]  # noqa: E731
    assert (publie(a) is None) == (publie(b) is None)
    assert a["bornes"]["ecart_points_de_frais"] == b["bornes"]["ecart_points_de_frais"] == 0.01


def test_bornes_inversees_reordonnees_et_signalees():
    out = grille(basse=1.28, haute=0.21)
    assert out["bornes"]["basse"]["valeur_pct"] == 0.21
    assert any("réordonnées" in a for a in out["avertissements"])


def test_alerte_si_les_frais_ont_lair_saisis_en_fraction():
    """1,2 % et 1,38 % saisis 0.012 / 0.0138 passaient sans un mot. Le seuil couvre le cas."""
    out = grille(basse=0.012, haute=0.0138)
    assert any("points de pourcentage" in a for a in out["avertissements"])


def test_lecart_en_pct_du_capital_ne_depend_pas_de_lhypothese_de_rendement():
    """Le chiffre le plus solide de l'episode : sans versement, l'ecart relatif est invariant."""
    out = grille(hypotheses_rendement_pct=(0.0, 5.0, 7.0))
    for annees in (10, 20, 30):
        parts = {_case(out, annees, r)["ecart_en_pct_du_capital_sans_frais"] for r in (0.0, 5.0, 7.0)}
        assert len(parts) == 1, f"à {annees} ans, l'écart relatif dépend du rendement : {parts}"


# ---------------------------------------------------------------------------
# 6. LA SORTIE — chaque chiffre porte sa source, et ce qu'il ne prouve pas
# ---------------------------------------------------------------------------
def test_chaque_borne_publiee_porte_source_page_url_date_et_definition():
    out = grille()
    for borne in ("basse", "haute"):
        d = out["bornes"][borne]
        for champ in ("source", "page", "url", "date_releve", "categorie", "definition"):
            assert str(d[champ]).strip()
        assert d["definition_libelle"] == DEFINITIONS_FRAIS[d["definition"]]["libelle"]


def test_la_sortie_porte_les_mentions_obligatoires_et_les_limites():
    out = grille()
    assert any("hypothèse d'école" in m for m in out["mentions_obligatoires"])
    assert any("lequel choisir" in m for m in out["ce_que_ce_calcul_ne_prouve_pas"])
    assert any("SOUS-ESTIME" in m for m in out["ce_que_ce_calcul_ne_prouve_pas"])


def test_la_sortie_est_serialisable_et_horodatee():
    out = grille()
    assert json.loads(json.dumps(out, ensure_ascii=False))["moteur"] == "simulateur_frais.py"
    assert out["calcule_le"].startswith("20")


def test_aucune_valeur_de_frais_nest_ecrite_en_dur_dans_le_moteur():
    """Anti-fiction : le moteur ne connait aucun chiffre de frais. Il les recoit du releve.

    On lit l'AST, pas le texte : un commentaire pedagogique n'est pas une valeur en dur, alors
    qu'un litteral glisse dans le code, lui, en est une. Tout litteral numerique qui RESSEMBLE
    a un taux de frais (0 < v < FRAIS_MAX_POINTS, entier ou flottant) doit etre declare ici avec
    sa raison d'etre — sinon le test rougit, et c'est le but.

    Limite connue : un taux ecrit en CHAINE (« 0,22 ») passerait. Le format d'entree du moteur
    etant numerique, une telle chaine planterait au premier calcul.
    """
    import ast

    # Attention : en Python, 1 et 1.0 sont la MEME cle de dictionnaire. Le controle porte donc
    # sur la valeur numerique, quel que soit son type — ce qui est exactement ce qu'on veut ici.
    litteraux_structurels = {
        1: "neutre arithmétique — (1 + r), (1 - f) — et le pas d'un point (point marginal)",
        2: "arrondi d'affichage (round(..., 2)) et code retour « mauvais usage »",
        3: "code retour « écriture impossible »",
        4: "arrondi d'affichage (round(..., 4))",
        5: "hypothèse de rendement par défaut du CLI — ce n'est pas un frais",
        6: "arrondi d'affichage (round(..., 6))",
        0.01: "écart minimal publiable entre deux bornes",
        0.05: "seuil de soupçon « frais saisis en fraction »",
        1e-12: "tolérance de comparaison flottante pour l'hypothèse 0 %",
    }
    arbre = ast.parse(pathlib.Path(sf.__file__).read_text(encoding="utf-8"))
    suspects = {
        n.value
        for n in ast.walk(arbre)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, (int, float))
        and not isinstance(n.value, bool)
        and 0 < n.value < sf.FRAIS_MAX_POINTS
        and n.value not in litteraux_structurels
    }
    assert not suspects, (
        f"littéral(aux) non déclaré(s) dans le moteur : {sorted(suspects)}. "
        "Si c'est un taux de frais, il doit venir du relevé, pas du code."
    )


# ---------------------------------------------------------------------------
# 7. LE CLI — les codes retour doivent DIRE ce qui s'est passé
# ---------------------------------------------------------------------------
def _lancer(*args):
    return subprocess.run(
        [sys.executable, "simulateur_frais.py", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=DOSSIER,
    )


def _faits(**surcharges):
    borne = {
        "definition": "ongoing_costs_esma",
        "categorie": CAT_A,
        "source": SOURCE,
        "page": "p. 18, table MR-CP.14",
        "url": URL,
        "date_releve": DATE,
    }
    faits = {
        "capital_initial": 10_000.0,
        "versement_annuel": 0.0,
        "horizons_ans": [10, 20, 30],
        "hypotheses_rendement_brut_pct": [0.0, 5.0],
        "bornes": {
            "basse": {**borne, "valeur_pct": 0.21},
            "haute": {**borne, "valeur_pct": 1.28},
        },
    }
    faits.update(surcharges)
    return faits


def _ecrire(tmp_path, faits):
    f = tmp_path / "faits.json"
    f.write_text(json.dumps(faits, ensure_ascii=False), encoding="utf-8")
    return f


def test_le_cli_sarrete_si_le_fichier_de_faits_nexiste_pas(tmp_path):
    r = _lancer("--faits", str(tmp_path / "absent.json"))
    assert r.returncode == 2
    # « relevé » accentué : prouve au passage que la console est bien reconfigurée en UTF-8.
    assert "relevé" in r.stdout


def test_le_cli_calcule_et_ecrit_depuis_un_fichier_de_faits(tmp_path):
    f = _ecrire(tmp_path, _faits())
    sortie = tmp_path / "res" / "frais.json"
    r = _lancer("--faits", str(f), "--sortie", str(sortie))
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert len(data["grille"]) == 6
    # Fact-Lock : la sortie doit pouvoir etre rattachee au releve exact.
    assert data["faits"]["sha256"]
    assert str(f) in data["faits"]["fichier"]


def test_le_cli_rend_1_sur_un_refus_de_conformite(tmp_path):
    """Un refus de conformite n'est pas un plantage : code 1, message lisible, aucun fichier."""
    faits = _faits()
    faits["bornes"]["haute"]["definition"] = "incidence_couts_annuels_dic"
    faits["bornes"]["haute"]["page"] = "p. 6"
    f = _ecrire(tmp_path, faits)
    sortie = tmp_path / "res.json"
    r = _lancer("--faits", str(f), "--sortie", str(sortie))
    assert r.returncode == 1
    assert "BornesIncomparables" in r.stdout
    assert not sortie.exists()


@pytest.mark.parametrize(
    "contenu", ["[]", '"texte"', '{"bornes": []}', '{"bornes": {"basse": 3, "haute": 4}}']
)
def test_le_cli_rend_2_sur_un_json_structurellement_faux(tmp_path, contenu):
    """Panne n°8 : un JSON valide mais faux ne doit pas sortir en « refus de conformite »."""
    f = tmp_path / "faits.json"
    f.write_text(contenu, encoding="utf-8")
    r = _lancer("--faits", str(f), "--sortie", str(tmp_path / "res.json"))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr


def test_le_cli_rend_2_si_horizons_ans_nest_pas_une_liste(tmp_path):
    f = _ecrire(tmp_path, _faits(horizons_ans=30))
    r = _lancer("--faits", str(f), "--sortie", str(tmp_path / "res.json"))
    assert r.returncode == 2
    assert "liste attendue" in r.stdout


def test_le_cli_rend_2_sur_une_valeur_a_virgule_francaise(tmp_path):
    faits = _faits()
    faits["bornes"]["basse"]["valeur_pct"] = "0,21"
    f = _ecrire(tmp_path, faits)
    r = _lancer("--faits", str(f), "--sortie", str(tmp_path / "res.json"))
    assert r.returncode == 2
    assert "POINT décimal" in r.stdout


def test_le_cli_rend_3_si_la_sortie_est_impossible_a_ecrire(tmp_path):
    """Panne n°9 : OneDrive/Excel qui verrouille. Ce n'est PAS un refus de conformite."""
    f = _ecrire(tmp_path, _faits())
    # Un dossier la ou le fichier devrait aller : os.replace echoue avec une OSError.
    sortie = tmp_path / "res.json"
    sortie.mkdir()
    r = _lancer("--faits", str(f), "--sortie", str(sortie))
    assert r.returncode == 3, r.stdout + r.stderr
    assert "écriture impossible" in r.stdout


@pytest.mark.parametrize(
    "absent",
    ["capital_initial", "versement_annuel", "horizons_ans", "hypotheses_rendement_brut_pct"],
)
def test_le_cli_signale_les_valeurs_par_defaut_absentes_du_releve(tmp_path, absent):
    """Anti-fiction : une hypothese que le releve ne porte pas doit etre dite comme telle.

    Le cas le plus dangereux est `hypotheses_rendement_brut_pct` : sans lui, le moteur fabrique
    une hypothese de rendement de 5 % qui ne sort d'aucun document.
    """
    faits = _faits()
    del faits[absent]
    f = _ecrire(tmp_path, faits)
    sortie = tmp_path / "res.json"
    r = _lancer("--faits", str(f), "--sortie", str(sortie))
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert any("valeurs par défaut" in a and absent in a for a in data["avertissements"])


def test_le_cli_rend_2_si_le_chemin_des_faits_est_un_dossier(tmp_path):
    """`--faits <dossier>` sortait en traceback + rc 1, donc lisible comme un refus LR."""
    dossier = tmp_path / "pas_un_fichier"
    dossier.mkdir()
    r = _lancer("--faits", str(dossier), "--sortie", str(tmp_path / "res.json"))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr


def test_le_dry_run_naffiche_le_json_et_necrit_rien(tmp_path):
    f = _ecrire(tmp_path, _faits())
    sortie = tmp_path / "res.json"
    r = _lancer("--faits", str(f), "--sortie", str(sortie), "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not sortie.exists()
    assert json.loads(r.stdout)["moteur"] == "simulateur_frais.py"


def test_les_accents_survivent_a_une_console_cp1252(tmp_path):
    """Panne n°10 : la console Windows en cp1252 ne doit pas faire planter la sortie."""
    import os

    r = subprocess.run(
        [sys.executable, "simulateur_frais.py", "--faits", str(tmp_path / "absent.json")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=DOSSIER,
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
    )
    assert r.returncode == 2
    assert "Traceback" not in r.stderr  # pas de UnicodeEncodeError sur les accents
