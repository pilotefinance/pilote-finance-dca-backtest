#!/usr/bin/env python3
"""LA GATE DU RELEVE — `relever_frais_ep3.py` doit s'ARRETER plutot que de deviner.

Un extracteur de PDF qui « fait au mieux » quand la structure change est le pire outil possible
pour une chaine anti-fiction : il rend un chiffre plausible issu d'une table qui n'est plus la
bonne, et personne ne le voit. Ces tests verifient qu'il refuse.

Ils verifient aussi que le releve REEL correspond bien au document reellement lu (empreinte
SHA-256) : si l'ESMA remplace son PDF, le test rougit et le relevé doit etre refait, pas adapte.

Lancer : python -m pytest test_relever_frais_ep3.py -q
"""
import json
import pathlib

import pytest

import relever_frais_ep3 as rel
from relever_frais_ep3 import ReleveImpossible, relever

PDF = pathlib.Path(rel.PDF_DEFAUT)
pdf_present = pytest.mark.skipif(
    not PDF.exists(), reason=f"PDF source absent ({PDF}) — relevé impossible hors poste de prod"
)


# ---------------------------------------------------------------------------
# 1. LES REFUS
# ---------------------------------------------------------------------------
def test_refuse_un_pdf_absent(tmp_path):
    with pytest.raises(ReleveImpossible) as exc:
        relever(tmp_path / "pas_la.pdf")
    assert "introuvable" in str(exc.value)


def test_refuse_une_page_qui_ne_contient_pas_la_table(monkeypatch, tmp_path):
    """Si la pagination du rapport change, on s'arrete — on ne cherche pas la table ailleurs."""
    faux = tmp_path / "faux.pdf"
    faux.write_bytes(b"%PDF-1.4 faux")
    monkeypatch.setattr(rel, "_texte_page", lambda pdf, n: "Une page sans rien d'attendu.")
    with pytest.raises(ReleveImpossible) as exc:
        # Empreinte assumée : sinon c'est ELLE qui refuse, et le test ne prouve plus rien
        # sur la pagination — il passerait sur un module qui ne cherche même pas la table.
        relever(faux, date_releve="2026-08-06", accepter_nouvelle_empreinte=True)
    assert "introuvable" in str(exc.value)


ENTETE = "Active funds Passive funds ETFs\n1Y 10Y 1Y 10Y 1Y 10Y\n"


def page_factice(lignes, entete=ENTETE, fin="Bond UCITS\n"):
    """Une page 18 factice, conforme par defaut — chaque test n'en casse qu'UNE chose."""
    return (
        f"{rel.CODE_TABLE}\n{rel.TITRE_TABLE}\n{entete}Ongoing costs\nEquity UCITS\n{lignes}{fin}"
    )


def relever_page(monkeypatch, tmp_path, page):
    faux = tmp_path / "faux.pdf"
    faux.write_bytes(b"%PDF-1.4 faux")
    monkeypatch.setattr(rel, "_texte_page", lambda pdf, n: page)
    return relever(faux, date_releve="2026-08-06", accepter_nouvelle_empreinte=True)


def test_refuse_une_ligne_dannee_incomplete_MEME_si_une_autre_annee_est_lisible(
    monkeypatch, tmp_path
):
    """Le vrai piege : une colonne disparait sur 2024, et le script replie sur 2023 EN SILENCE.

    L'ancien test n'injectait qu'UNE annee — le refus venait d'un « aucune ligne exploitable »,
    pas du controle des six valeurs. Il passait sur un module cassé.
    """
    page = page_factice(
        "2023 1.29 1.43 0.22 0.30 0.22 0.27\n2024 1.28 1.39 0.22 0.28 0.21\n"
    )
    with pytest.raises(ReleveImpossible) as exc:
        relever_page(monkeypatch, tmp_path, page)
    assert "2024" in str(exc.value)


def test_refuse_un_entete_de_colonnes_absent(monkeypatch, tmp_path):
    with pytest.raises(ReleveImpossible) as exc:
        relever_page(monkeypatch, tmp_path, page_factice("2024 1.28 1.39 0.22 0.28 0.21 0.26\n", entete=""))
    assert "en-tête" in str(exc.value)


def test_refuse_un_ordre_de_colonnes_inverse(monkeypatch, tmp_path):
    """LE bloquant de la relecture : sans ce contrôle, 0,21 sortait étiqueté « gestion active ».

    Chiffre plausible, étiquette fausse, FEU VERT — le pire cas possible pour l'anti-fiction.
    """
    inverse = "ETFs Passive funds Active funds\n1Y 10Y 1Y 10Y 1Y 10Y\n"
    with pytest.raises(ReleveImpossible) as exc:
        relever_page(
            monkeypatch, tmp_path, page_factice("2024 0.21 0.26 0.22 0.28 1.28 1.39\n", entete=inverse)
        )
    assert "ordre" in str(exc.value)


def test_refuse_une_valeur_qui_nest_pas_un_taux_de_frais(monkeypatch, tmp_path):
    """La section « Net performance » de la même page a EXACTEMENT le même format de ligne."""
    with pytest.raises(ReleveImpossible) as exc:
        relever_page(monkeypatch, tmp_path, page_factice("2024 17.0 7.6 21.3 9.3 21.4 9.3\n"))
    assert "frais courants" in str(exc.value)


def test_la_section_performance_narrete_pas_le_bloc_actions(monkeypatch, tmp_path):
    """Si « Bond UCITS » change de libellé, « Net performance » doit borner la tranche."""
    page = page_factice(
        "2024 1.28 1.39 0.22 0.28 0.21 0.26\n",
        fin="Net performance\nEquity UCITS\n2024 17.0 7.6 21.3 9.3 21.4 9.3\n",
    )
    faits = relever_page(monkeypatch, tmp_path, page)
    assert faits["releve_complet_toutes_categories"]["etf"]["frais_courants_1an_pct"] == 0.21


def test_prend_lannee_la_plus_recente_et_pas_la_premiere_lue(monkeypatch, tmp_path):
    """Les annees se suivent dans le tableau : on retient la plus recente, jamais celle du haut."""
    page = page_factice(
        "2023 1.29 1.43 0.22 0.30 0.22 0.27\n2024 1.28 1.39 0.22 0.28 0.21 0.26\n",
        fin="Bond UCITS\n2024 0.70 0.81 0.12 0.17 0.19 0.24\n",
    )
    faits = relever_page(monkeypatch, tmp_path, page)
    assert faits["table"]["annee_retenue"] == 2024
    assert faits["releve_complet_toutes_categories"]["actif"]["frais_courants_1an_pct"] == 1.28
    # La section « Bond UCITS » ne doit pas contaminer le relevé actions.
    assert faits["releve_complet_toutes_categories"]["etf"]["frais_courants_1an_pct"] == 0.21


def test_les_bornes_sont_le_min_et_le_max_sans_choix_humain(monkeypatch, tmp_path):
    """Regle mecanique : aucune place pour un cherry-picking de borne."""
    faits = relever_page(monkeypatch, tmp_path, page_factice("2024 1.28 1.39 0.22 0.28 0.21 0.26\n"))
    assert faits["bornes"]["basse"]["valeur_pct"] == 0.21
    assert faits["bornes"]["haute"]["valeur_pct"] == 1.28


def test_refuse_de_departager_deux_categories_a_egalite(monkeypatch, tmp_path):
    """Le tie-break alphabetique choisissait TOUJOURS « etf » — un choix humain deguise en tri.

    Cas réel : sur la ligne 2023 du même tableau, passif et ETF sont tous deux à 0,22 %.
    """
    page = page_factice("2023 1.29 1.43 0.22 0.30 0.22 0.27\n")
    with pytest.raises(ReleveImpossible) as exc:
        relever_page(monkeypatch, tmp_path, page)
    assert "égalité" in str(exc.value)


def test_refuse_un_pdf_dont_lempreinte_a_change(tmp_path):
    """Un document remplacé par l'ESMA ne repart pas en silence."""
    faux = tmp_path / "faux.pdf"
    faux.write_bytes(b"%PDF-1.4 autre document")
    with pytest.raises(ReleveImpossible) as exc:
        relever(faux)
    assert "empreinte" in str(exc.value)


def test_une_date_de_releve_explicite_est_respectee(monkeypatch, tmp_path):
    faits = relever_page(monkeypatch, tmp_path, page_factice("2024 1.28 1.39 0.22 0.28 0.21 0.26\n"))
    assert faits["bornes"]["basse"]["date_releve"] == "2026-08-06"


@pdf_present
def test_sans_date_explicite_le_releve_porte_la_date_du_jour():
    """Rejoué dans trois semaines, le relevé se datait du 06/08 : une donnée fabriquée.

    Le défaut n'est atteignable que sur le document CONFORME : dès que l'empreinte change, la
    date devient obligatoire (on ne date pas un nouveau document de la veille).
    """
    import datetime as dt

    faits = relever(PDF)
    assert faits["bornes"]["basse"]["date_releve"] == dt.date.today().isoformat()


def test_un_document_remplace_exige_une_date_de_releve(monkeypatch, tmp_path):
    """« --accepter-nouvelle-empreinte ET --date-releve » était une promesse du message, pas du code."""
    faux = tmp_path / "faux.pdf"
    faux.write_bytes(b"%PDF-1.4 faux")
    monkeypatch.setattr(rel, "_texte_page", lambda pdf, n: page_factice("2024 1.28 1.39 0.22 0.28 0.21 0.26\n"))
    with pytest.raises(ReleveImpossible) as exc:
        relever(faux, accepter_nouvelle_empreinte=True)
    assert "date-releve" in str(exc.value)


def test_un_document_remplace_ne_publie_pas_les_metadonnees_de_lancien(monkeypatch, tmp_path):
    """Sinon le JSON affirme une date de publication pour un document que personne n'a relu."""
    faits = relever_page(monkeypatch, tmp_path, page_factice("2024 1.28 1.39 0.22 0.28 0.21 0.26\n"))
    doc = faits["document"]
    assert doc["document_conforme_a_lempreinte"] is False
    assert doc["publie_le"] is None and doc["donnees_arretees_au"] is None
    assert doc["metadonnees_non_reverifiees"] is True


@pdf_present
def test_le_document_conforme_publie_bien_ses_metadonnees():
    doc = relever(PDF, date_releve="2026-08-06")["document"]
    assert doc["publie_le"] == "2026-03-03"
    assert doc["metadonnees_non_reverifiees"] is False


# ---------------------------------------------------------------------------
# 2. LE RELEVE REEL — il doit rester rejouable a l'identique
# ---------------------------------------------------------------------------
@pdf_present
def test_le_document_lu_est_bien_celui_du_06_08_2026():
    """Si l'ESMA remplace son PDF, ce test rougit : le relevé se refait, il ne s'adapte pas."""
    faits = relever(PDF)
    assert faits["document"]["document_conforme_a_lempreinte"], (
        "le PDF de sources_ep3/ n'a plus l'empreinte du document relevé le 06/08/2026"
    )


@pdf_present
def test_le_releve_reel_est_complet_et_source():
    faits = relever(PDF)
    assert set(faits["releve_complet_toutes_categories"]) == {"actif", "passif_non_etf", "etf"}
    for borne in faits["bornes"].values():
        assert borne["definition"] == "ongoing_costs_esma"
        for champ in ("source", "page", "url", "date_releve", "categorie"):
            assert str(borne[champ]).strip()
        assert "MR-CP.14" in borne["page"] and "p. 18" in borne["page"]


@pdf_present
def test_le_releve_est_rejouable_a_lidentique():
    """Deux executions doivent rendre exactement le meme JSON, a date de releve fixee.

    Ce test ne vaut que s'il peut echouer : il echouerait si quelqu'un introduisait un
    horodatage d'execution, un `set` non ordonne, ou une valeur tiree du systeme dans la
    sortie. La date de relevé, elle, est passée explicitement — c'est le seul élément qui a le
    droit de bouger d'une exécution à l'autre.
    """
    a = json.dumps(relever(PDF, date_releve="2026-08-06"), ensure_ascii=False, sort_keys=True)
    b = json.dumps(relever(PDF, date_releve="2026-08-06"), ensure_ascii=False, sort_keys=True)
    assert a == b
    assert "2026-08-06" in a


@pdf_present
def test_un_pdf_corrompu_est_une_panne_technique_pas_un_probleme_de_structure(tmp_path):
    """Le vrai chemin pypdf, sur un cas d'echec : aucun test ne l'exercait."""
    tronque = tmp_path / "tronque.pdf"
    tronque.write_bytes(PDF.read_bytes()[:5000])
    with pytest.raises(rel.PdfIllisible):
        relever(tronque, date_releve="2026-08-06", accepter_nouvelle_empreinte=True)


def test_un_fichier_qui_nest_pas_un_pdf(tmp_path):
    faux = tmp_path / "pas_un.pdf"
    faux.write_text("bonjour", encoding="utf-8")
    with pytest.raises(rel.PdfIllisible):
        relever(faux, date_releve="2026-08-06", accepter_nouvelle_empreinte=True)


def test_les_codes_retour_du_cli_distinguent_structure_et_panne_technique(tmp_path):
    """rc 1 = relevé impossible · rc 2 = PDF illisible · rc 3 = écriture impossible."""
    import subprocess
    import sys

    def lancer(*args):
        return subprocess.run(
            [sys.executable, "relever_frais_ep3.py", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=pathlib.Path(rel.__file__).parent,
        )

    absent = lancer("--pdf", str(tmp_path / "absent.pdf"), "--sortie", str(tmp_path / "o.json"))
    assert absent.returncode == 1

    pas_un_pdf = tmp_path / "pas_un.pdf"
    pas_un_pdf.write_text("bonjour", encoding="utf-8")
    illisible = lancer(
        "--pdf", str(pas_un_pdf), "--sortie", str(tmp_path / "o.json"),
        "--accepter-nouvelle-empreinte", "--date-releve", "2026-08-06",
    )
    assert illisible.returncode == 2, illisible.stdout + illisible.stderr
    assert "Traceback" not in illisible.stderr

    if PDF.exists():
        dossier = tmp_path / "sortie_bloquee"
        dossier.mkdir()
        verrou = lancer("--pdf", str(PDF), "--sortie", str(dossier))
        assert verrou.returncode == 3, verrou.stdout + verrou.stderr


@pdf_present
def test_le_releve_alimente_le_moteur_sans_refus():
    """Bout en bout : le relevé doit passer les contrôles de conformite du simulateur."""
    from simulateur_frais import NiveauDeFrais, simuler_grille

    faits = relever(PDF)
    bornes = {
        k: NiveauDeFrais(
            valeur_pct=v["valeur_pct"],
            definition=v["definition"],
            categorie=v["categorie"],
            source=v["source"],
            page=v["page"],
            url=v["url"],
            date_releve=v["date_releve"],
        )
        for k, v in faits["bornes"].items()
    }
    out = simuler_grille(
        bornes["basse"],
        bornes["haute"],
        horizons=tuple(faits["horizons_ans"]),
        hypotheses_rendement_pct=tuple(faits["hypotheses_rendement_brut_pct"]),
        phrase_categories=faits["phrase_categories"],
    )
    assert len(out["grille"]) == 9
    # La phrase LR4 cond.1 doit se retrouver dans la sortie publiee.
    assert any("catégories différentes" in a for a in out["avertissements"])
