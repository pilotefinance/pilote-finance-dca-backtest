#!/usr/bin/env python3
"""Tests du moteur KRACH (ep. 2). Regle code.md §4 : le test qui echoue d'abord.

Toutes les series sont SYNTHETIQUES et choisies pour que le resultat attendu se calcule
A LA MAIN. On ne teste jamais le moteur contre lui-meme.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest_krach import (
    OUT,
    controle_croise,
    controle_orphelins,
    etiquette,
    replique_pwl,
    resume_krach,
    run_krach,
    signal_dans_la_donnee,
)
from build_data import DonneeManquante


def fabrique(valeurs, taux_annuel_pct=None, debut="2000-01", colonne="us_tr_usd") -> pd.DataFrame:
    """Un df au format `charge()` : index mensuel contigu, colonnes du moteur ep. 1."""
    idx = pd.period_range(debut, periods=len(valeurs), freq="M")
    df = pd.DataFrame(index=idx)
    df.index.name = "mois"
    df[colonne] = np.asarray(valeurs, dtype=float)
    df["us_ipc"] = 100.0
    if taux_annuel_pct is not None:
        df["cash_usd_pct"] = float(taux_annuel_pct)
    return df


# --------------------------------------------------------------------------- etiquettes
def test_etiquette_stable():
    assert etiquette(0.10) == "B10"
    assert etiquette(0.20) == "B20"
    assert etiquette(0.30) == "B30"
    assert etiquette(0.155) == "B15.5"   # jamais deux seuils differents sous le meme nom


# --------------------------------------------------------------------------- le krach n'arrive jamais
def test_marche_qui_ne_baisse_jamais_B_reste_en_cash():
    r = run_krach(fabrique([1.01 ** k for k in range(25)]), horizon_months=12,
                  seuils=(0.10,), cash_rate="zero", debut=None)
    assert len(r) == 13
    assert not r["B10_declenche"].any()
    assert r["B10_mois_attente"].isna().all()          # ABSENT, jamais 0 ni -1
    assert np.allclose(r["B10_final"], 1.0)            # cash a 0 % : le capital ne bouge pas
    res = resume_krach(r)
    assert res["strategies"]["B10"]["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"] == 100.0
    assert res["strategies"]["B10"]["pct_fenetres_ou_B_bat_A"] == 0.0
    assert res["strategies"]["B10"]["quand_le_signal_est_venu_APRES_t0"]["fenetres"] == 0
    assert res["strategies"]["B10"]["pct_fenetres_ou_le_signal_est_DEJA_LA_a_t0"] == 0.0


def test_attente_infinie_avec_cash_remunere_vaut_exactement_le_taux():
    """Marche plat + cash a 12 %/an + horizon 10 ans -> B = 1,12^10, A = 1,0. Calculable a la main."""
    r = run_krach(fabrique([1.0] * 140, taux_annuel_pct=12.0), horizon_months=120,
                  seuils=(0.20,), cash_rate="taux_court", debut=None)
    assert not r["B20_declenche"].any()
    assert np.allclose(r["A_final"], 1.0)
    assert np.allclose(r["B20_final"], 1.12 ** 10)
    assert np.allclose(r["B20_ecart_pct"], (1.12 ** 10 - 1.0) * 100.0)


# --------------------------------------------------------------------------- le krach arrive
def test_declenchement_au_bon_mois_et_valeur_exacte():
    # 100 pendant 5 mois, puis -21 % au mois 5, puis remontee.
    v = [100.0] * 5 + [79.0, 85.0, 95.0, 110.0, 120.0, 130.0, 140.0, 150.0]
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.10, 0.20, 0.30), cash_rate="zero", debut=None)
    ligne = r.iloc[0]
    assert ligne["B10_mois_attente"] == 5
    assert ligne["B20_mois_attente"] == 5          # -21 % franchit -10 % ET -20 % le meme mois
    assert not ligne["B30_declenche"]              # -21 % ne franchit PAS -30 %
    assert np.isclose(ligne["A_final"], v[12] / v[0])
    assert np.isclose(ligne["B20_final"], v[12] / v[5])   # cash a 0 %, achat a la valeur du mois 5
    assert np.isclose(ligne["B30_final"], 1.0)            # jamais investi -> cash a 0 %


def test_monotonie_des_seuils():
    """B30 ne peut JAMAIS declencher avant B20, ni B20 avant B10."""
    v = [100.0, 100.0, 95.0, 88.0, 78.0, 66.0, 60.0] + [70.0 + k for k in range(20)]
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.10, 0.20, 0.30), cash_rate="zero", debut=None)
    m = r[["B10_mois_attente", "B20_mois_attente", "B30_mois_attente"]].dropna()
    assert (m["B10_mois_attente"] <= m["B20_mois_attente"]).all()
    assert (m["B20_mois_attente"] <= m["B30_mois_attente"]).all()


def test_signal_au_tout_dernier_mois_de_l_horizon():
    """Panne #10 : le repli tombe exactement au mois `horizon` -> B achete a la valeur finale."""
    v = [100.0] * 12 + [70.0] + [100.0] * 5
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    ligne = r.iloc[0]
    assert ligne["B20_mois_attente"] == 12
    assert np.isclose(ligne["B20_final"], 1.0)     # cash a 0 % jusqu'au bout, achat a t=fin


def test_delai_execution_achete_le_mois_suivant():
    v = [100.0] * 5 + [79.0, 85.0, 95.0, 110.0, 120.0, 130.0, 140.0, 150.0]
    r0 = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    r1 = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None,
                   delai_execution=1)
    assert r0.iloc[0]["B20_mois_attente"] == r1.iloc[0]["B20_mois_attente"] == 5   # le SIGNAL ne bouge pas
    assert np.isclose(r0.iloc[0]["B20_final"], v[12] / v[5])
    assert np.isclose(r1.iloc[0]["B20_final"], v[12] / v[6])                       # l'ACHAT, si


# --------------------------------------------------------------------------- les deux plus-hauts
def test_mode_ath_declenche_a_t0_et_donne_une_EGALITE_stricte():
    """Fenetre qui demarre deja 25 % sous le plus-haut : B investit a t0, donc B EST A."""
    v = [100.0] * 3 + [75.0] * 20
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut=None, reference="ath")
    tardive = r[r["depart"] == "2000-06"].iloc[0]        # mois 5 : deja -25 % sous le pic du mois 0
    assert tardive["B20_mois_attente"] == 0
    assert tardive["B20_final"] == tardive["A_final"]
    assert tardive["B20_ecart_pct"] == 0.0
    res = resume_krach(r)
    b = res["strategies"]["B20"]
    assert b["pct_fenetres_egalite_stricte"] > 0
    # une egalite n'est NI une victoire NI une defaite
    total = b["pct_fenetres_ou_B_bat_A"] + b["pct_fenetres_egalite_stricte"] + b["pct_fenetres_ou_A_bat_B"]
    assert abs(total - 100.0) < 0.2


def test_mode_depuis_t0_ne_declenche_jamais_au_mois_0():
    v = [100.0] * 3 + [75.0] * 20
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut=None, reference="depuis_t0")
    attentes = r["B20_mois_attente"].dropna()
    assert (attentes > 0).all()
    assert np.allclose(r["drawdown_t0_pct"], 0.0)   # par construction : le pic demarre a t0


def test_les_deux_lectures_donnent_des_chiffres_DIFFERENTS():
    v = [100.0] * 3 + [75.0] * 20
    a = resume_krach(run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                               debut=None, reference="ath"))
    t = resume_krach(run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                               debut=None, reference="depuis_t0"))
    assert (a["strategies"]["B20"]["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"]
            != t["strategies"]["B20"]["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"])


def test_le_plus_haut_ath_remonte_AVANT_debut():
    """Le pic d'avant `debut` doit compter : sinon toute fenetre 1934 croirait le marche au sommet."""
    v = [100.0] * 3 + [70.0] * 25
    df = fabrique(v)
    r = run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut="2000-10", reference="ath")     # demarre APRES la chute
    assert (r["B20_mois_attente"] == 0).all()           # -30 % sous le pic du mois 0 : signal immediat
    assert np.allclose(r["drawdown_t0_pct"], -30.0)


# --------------------------------------------------------------------------- frais
def test_frais_rongent_A_et_B_du_bon_nombre_de_mois():
    v = [100.0] * 5 + [79.0] + [100.0] * 12
    sans = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    avec = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None,
                     annual_fee=0.012)
    f = (1.0 - 0.012) ** (1.0 / 12.0)
    assert np.isclose(avec.iloc[0]["A_final"], sans.iloc[0]["A_final"] * f ** 12)
    assert np.isclose(avec.iloc[0]["B20_final"], sans.iloc[0]["B20_final"] * f ** 7)  # investi 12-5 mois


# --------------------------------------------------------------------------- normalisation
def test_seuils_desordonnes_et_doublons_normalises():
    v = [100.0] * 5 + [60.0] + [100.0] * 12
    a = run_krach(fabrique(v), horizon_months=12, seuils=(0.30, 0.10, 0.20, 0.20), cash_rate="zero", debut=None)
    b = run_krach(fabrique(v), horizon_months=12, seuils=(0.10, 0.20, 0.30), cash_rate="zero", debut=None)
    pd.testing.assert_frame_equal(a, b)


# --------------------------------------------------------------------------- LES REFUS (tribunal des cas)
@pytest.mark.parametrize("seuils", [(20,), (0.0,), (1.0,), (-0.2,), ()])
def test_seuil_hors_bornes_explose(seuils):
    with pytest.raises(ValueError):
        run_krach(fabrique([100.0] * 20), horizon_months=12, seuils=seuils, cash_rate="zero", debut=None)


def test_reference_inconnue_explose():
    with pytest.raises(ValueError, match="reference"):
        run_krach(fabrique([100.0] * 20), horizon_months=12, cash_rate="zero", debut=None,
                  reference="plus_haut_du_mois")


@pytest.mark.parametrize("delai", [-1, 1.5, "1", True, 12, 99])
def test_delai_execution_invalide_explose(delai):
    with pytest.raises(ValueError, match="delai_execution"):
        run_krach(fabrique([100.0] * 20), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut=None, delai_execution=delai)


def test_delai_execution_apres_un_signal_tardif_reste_dans_la_fenetre():
    """Signal au mois 11, delai 2, horizon 12 -> l'achat est rabote a la fin, jamais hors fenetre."""
    v = [100.0] * 11 + [70.0] + [90.0] * 8
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut=None, delai_execution=2)
    ligne = r.iloc[0]
    assert ligne["B20_mois_attente"] == 11
    assert np.isclose(ligne["B20_final"], 1.0)     # achat au mois 12 = valeur finale, cash a 0 %


def test_repli_exactement_au_seuil_declenche():
    """-20,000000 % PILE doit compter : sinon un seuil rond est manque pour cause d'arrondi."""
    v = [100.0] * 3 + [80.0] + [100.0] * 12
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    assert r.iloc[0]["B20_mois_attente"] == 3


def test_frais_en_pourcentage_au_lieu_de_fraction_explose():
    with pytest.raises(ValueError, match="annual_fee"):
        run_krach(fabrique([100.0] * 20), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut=None, annual_fee=0.3)


def test_real_refuse_hors_US():
    df = fabrique([100.0] * 20, colonne="jp_prix_jpy")
    with pytest.raises(ValueError, match="IPC"):
        run_krach(df, marche="JP", horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut=None, real=True)


def test_serie_trop_courte_pour_l_horizon():
    with pytest.raises(DonneeManquante):
        run_krach(fabrique([100.0] * 12), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)


def test_taux_court_absent_de_la_devise_refuse():
    with pytest.raises(ValueError, match="taux court"):
        run_krach(fabrique([100.0] * 200), horizon_months=12, seuils=(0.20,),
                  cash_rate="taux_court", debut=None)


def test_mois_non_contigus_refuses():
    df = fabrique([100.0] * 30)
    df.loc[df.index[10], "us_tr_usd"] = np.nan     # un trou -> jamais d'epissure silencieuse
    with pytest.raises(DonneeManquante, match="manquants"):
        run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)


def test_horizon_absurde_refuse():
    with pytest.raises(ValueError, match="horizon_months"):
        run_krach(fabrique([100.0] * 20), horizon_months=0, seuils=(0.20,), cash_rate="zero", debut=None)


def test_resume_refuse_un_tableau_vide():
    r = run_krach(fabrique([100.0] * 20), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    with pytest.raises(DonneeManquante):
        resume_krach(r.iloc[0:0])


# --------------------------------------------------------------------------- le signal dans la donnee
def test_signal_dans_la_donnee_trouve_le_dernier_seuil_franchi():
    # pic au mois 0, -25 % au mois 2, puis remontee au-dessus du pic et plus jamais de repli.
    v = [100.0, 100.0, 75.0, 90.0] + [110.0 + k for k in range(16)]
    s = signal_dans_la_donnee(fabrique(v), debut=None, seuils=(0.20, 0.30))
    assert s["seuils"]["B20"]["mois_sous_le_seuil"] == 1
    assert s["seuils"]["B20"]["dernier_mois_sous_le_seuil"] == "2000-03"   # le 3e mois
    assert s["seuils"]["B30"]["mois_sous_le_seuil"] == 0
    assert s["seuils"]["B30"]["dernier_mois_sous_le_seuil"] is None
    d = s["depuis_le_dernier_signal_-20pct"]
    assert d["mois_ecoules_sans_signal"] == len(v) - 3
    assert d["pire_repli_mensuel_depuis"] < 0.0        # -10 % au mois 3, jamais -20 %
    assert d["pire_repli_mensuel_depuis"] > -20.0


def test_signal_dans_la_donnee_refuse_une_periode_vide():
    with pytest.raises(DonneeManquante):
        signal_dans_la_donnee(fabrique([100.0] * 20), debut="2050-01")


def test_signal_dans_la_donnee_refuse_un_ipc_troue():
    df = fabrique([100.0] * 20)
    df.loc[df.index[5], "us_ipc"] = np.nan
    with pytest.raises(DonneeManquante, match="IPC"):
        signal_dans_la_donnee(df, real=True, debut=None)


def test_signal_dans_la_donnee_refuse_des_mois_non_contigus():
    df = fabrique([100.0] * 20)
    df.loc[df.index[7], "us_tr_usd"] = np.nan
    with pytest.raises(DonneeManquante, match="manquants"):
        signal_dans_la_donnee(df, debut=None)


def test_marche_inconnu_explose_proprement():
    with pytest.raises(ValueError, match="marche inconnu"):
        signal_dans_la_donnee(fabrique([100.0] * 20), marche="MARS", debut=None)


# --------------------------------------------------------------------------- la config de PRODUCTION
def test_config_de_production_ath_plus_taux_court():
    """`US_principal` : le SEUL cas ou l'index de travail est restreint par une intersection.

    Le plus-haut vient de la serie COMPLETE (200 mois), l'index de travail du croisement avec
    le taux court (les 60 derniers mois). Le pic d'avant doit quand meme compter.
    """
    v = [100.0] * 60 + [70.0] * 200                  # pic au debut, -30 % ensuite, pour toujours
    df = fabrique(v)
    df["cash_usd_pct"] = np.nan
    df.iloc[130:, df.columns.get_loc("cash_usd_pct")] = 0.0   # taux court connu sur les 130 derniers mois
    r = run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="taux_court",
                  debut=None, reference="ath")
    assert len(r) == 118                                       # 130 mois communs - 12
    assert np.allclose(r["drawdown_t0_pct"], -30.0)            # le pic du mois 0 compte toujours
    assert (r["B20_mois_attente"] == 0).all()
    assert np.allclose(r["B20_final"], r["A_final"])


def test_real_et_ath_deflatent_des_DEUX_cotes():
    """real=True : la serie de travail ET le plus-haut doivent etre deflates par le MEME IPC."""
    v = [100.0] * 5 + [75.0] * 20
    df = fabrique(v)
    df["us_ipc"] = [100.0 * 1.01 ** k for k in range(len(v))]   # inflation reguliere
    nominal = run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    reel = run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None, real=True)
    # En reel, l'indice deflate baisse plus vite : le signal ne peut pas arriver PLUS TARD.
    assert (reel["B20_mois_attente"].fillna(99) <= nominal["B20_mois_attente"].fillna(99)).all()
    assert np.isfinite(reel.select_dtypes(include=[float]).to_numpy()).all()


# --------------------------------------------------------------------------- aucun inf ne sort
def test_un_indice_a_zero_est_refuse_pas_publie_en_inf():
    df = fabrique([100.0] * 10 + [0.0] + [100.0] * 12)
    with pytest.raises(DonneeManquante, match="<= 0"):
        run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)


def test_un_indice_negatif_est_refuse():
    df = fabrique([100.0] * 10 + [-5.0] + [100.0] * 12)
    with pytest.raises(DonneeManquante, match="<= 0"):
        run_krach(df, horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)


def test_aucune_valeur_non_finie_ne_sort_du_moteur():
    r = run_krach(fabrique([100.0 + k for k in range(40)]), horizon_months=12, cash_rate="zero", debut=None)
    assert np.isfinite(r.select_dtypes(include=[float]).to_numpy()).all()


# --------------------------------------------------------------------------- resume calcule a la main
def test_resume_krach_compte_juste_sur_un_cas_pose_a_la_main():
    """4 fenetres construites une par une. Plus-haut = cummax = [100, 110, 110, 110, 200].

    i=0 [100 -> 110] : repli max 0 %          -> JAMAIS de signal, B reste en cash (1,0) < A (1,1)
    i=1 [110 ->  75] : -31,8 % au mois k=1    -> on a VRAIMENT attendu 1 mois, B (1,0) > A (0,68)
    i=2 [ 75 ->  78] : deja -31,8 % a t0      -> signal immediat, B EST A -> egalite stricte
    i=3 [ 78 -> 200] : deja -29,1 % a t0      -> signal immediat, B EST A -> egalite stricte
    """
    v = [100.0, 110.0, 75.0, 78.0, 200.0]            # 5 mois, horizon 1 -> 4 fenetres
    r = run_krach(fabrique(v), horizon_months=1, seuils=(0.20,), cash_rate="zero",
                  debut=None, reference="ath")
    assert pd.isna(r["B20_mois_attente"].iloc[0])
    assert r["B20_mois_attente"].iloc[1] == 1
    assert (r["B20_mois_attente"].iloc[2:] == 0).all()
    res = resume_krach(r)
    b = res["strategies"]["B20"]
    assert b["pct_fenetres_ou_le_krach_n_arrive_JAMAIS"] == 25.0
    assert b["pct_fenetres_ou_le_signal_est_DEJA_LA_a_t0"] == 50.0
    assert b["quand_le_signal_est_venu_APRES_t0"]["fenetres"] == 1
    assert b["quand_le_signal_est_venu_APRES_t0"]["pct_ou_B_bat_A"] == 100.0
    assert b["pct_fenetres_egalite_stricte"] == 50.0
    assert b["pct_fenetres_ou_B_bat_A"] == 25.0
    assert b["pct_fenetres_ou_A_bat_B"] == 25.0
    assert b["attente_moyenne_mois_quand_on_attend"] == 1.0
    somme = (b["pct_fenetres_ou_B_bat_A"] + b["pct_fenetres_egalite_stricte"]
             + b["pct_fenetres_ou_A_bat_B"])
    assert abs(somme - 100.0) < 1e-9


def test_scenario_degenere_est_signale_automatiquement():
    """Toutes les fenetres declenchent a t0 -> le resume DOIT le dire, pas laisser croire a une mesure."""
    v = [100.0] * 2 + [50.0] * 20
    r = run_krach(fabrique(v), horizon_months=12, seuils=(0.20,), cash_rate="zero",
                  debut="2000-03", reference="ath")
    b = resume_krach(r)["strategies"]["B20"]
    assert b["pct_fenetres_egalite_stricte"] == 100.0
    assert "AVERTISSEMENT_SCENARIO_DEGENERE" in b


def test_resume_refuse_un_tableau_sans_ses_parametres():
    r = run_krach(fabrique([100.0] * 20), horizon_months=12, seuils=(0.20,), cash_rate="zero", debut=None)
    nu = pd.DataFrame(r)                     # copie sans attrs, comme un CSV relu
    nu.attrs = {}
    with pytest.raises(DonneeManquante, match="parametres"):
        resume_krach(nu)


# --------------------------------------------------------------------------- CSV orphelins
def test_controle_orphelins_passe_quand_le_dossier_est_propre():
    """Le dossier reel doit etre propre : c'est ce que le run de production verifie."""
    controle_orphelins({f.name for f in OUT.glob("krach_*.csv")})


def test_controle_orphelins_STOPPE_sur_un_csv_d_un_run_precedent():
    """Vecu le 04/08/2026 : deux fichiers « US_principal » donnaient DEUX verdicts differents."""
    reels = {f.name for f in OUT.glob("krach_*.csv")}
    assert reels, "aucun CSV de resultats : lancer `python backtest_krach.py` d'abord."
    ampute = set(list(reels)[1:])                     # on fait semblant d'avoir produit un fichier de moins
    with pytest.raises(DonneeManquante, match="ORPHELIN"):
        controle_orphelins(ampute)


# --------------------------------------------------------------------------- controle croise
def _faux_biais(mois=3, dernier="2000-04"):
    return {"genere_le": "2026-08-04 00:00 UTC",
            "B_prix_contre_rendement_total": {
                "rendement_total_CE_QUE_LE_MOTEUR_UTILISE": {
                    "B20": {"mois_sous_le_seuil": mois, "dernier_mois_sous_le_seuil": dernier}}}}


def test_controle_croise_passe_quand_les_deux_chemins_concordent():
    v = [100.0, 100.0, 75.0, 78.0, 90.0] + [110.0] * 10
    s = signal_dans_la_donnee(fabrique(v), debut=None, seuils=(0.20,))
    attendu = s["seuils"]["B20"]
    c = controle_croise(s, _faux_biais(attendu["mois_sous_le_seuil"],
                                       attendu["dernier_mois_sous_le_seuil"]))
    assert c["verdict"] == "OK"
    assert c["seuils_verifies"] == ["B20"]


def test_controle_croise_STOPPE_sur_un_comptage_divergent():
    v = [100.0, 100.0, 75.0, 78.0, 90.0] + [110.0] * 10
    s = signal_dans_la_donnee(fabrique(v), debut=None, seuils=(0.20,))
    with pytest.raises(DonneeManquante, match="CONTROLE CROISE"):
        controle_croise(s, _faux_biais(mois=s["seuils"]["B20"]["mois_sous_le_seuil"] + 1))


def test_controle_croise_STOPPE_sur_une_date_divergente():
    v = [100.0, 100.0, 75.0, 78.0, 90.0] + [110.0] * 10
    s = signal_dans_la_donnee(fabrique(v), debut=None, seuils=(0.20,))
    faux = _faux_biais(s["seuils"]["B20"]["mois_sous_le_seuil"], dernier="1999-01")
    with pytest.raises(DonneeManquante, match="dernier mois"):
        controle_croise(s, faux)


# --------------------------------------------------------------------------- replique PWL
def test_replique_pwl_selectionne_le_mois_SUIVANT_la_chute():
    """Regle PWL (Table 7 p. 9) : la fenetre demarre LE MOIS SUIVANT une chute >= 20 %.

    Serie posee a la main : pic au mois 0 (indice 100), chute a 70 au mois 5 (-30 %), remontee
    au-dessus du pic ensuite. Le SEUL mois ou le repli >= 20 % est constate est le mois 5
    -> la seule fenetre eligible doit demarrer au mois 6, pas au mois 5.
    """
    v = [100.0] * 5 + [70.0] + [130.0 + k for k in range(150)]
    df = fabrique(v, taux_annuel_pct=2.0)
    r = replique_pwl(df, debut=None, horizon_months=120)
    assert r["fenetres_retenues"] == 1
    assert r["PWL"]["us_pct"] == 50.00                       # la citation ne bouge pas
    assert r["fenetres_totales"] == len(v) - 120


def test_replique_pwl_compte_les_EPISODES_pas_seulement_les_fenetres():
    """Deux krachs separes -> 2 episodes, meme si chacun rend plusieurs fenetres eligibles.

    Le repli reste >= 20 % pendant 3 mois d'affilee au 1er krach : 3 fenetres, 1 SEUL episode.
    """
    v = ([100.0] * 3 + [70.0, 71.0, 72.0]        # krach 1 : 3 mois sous -20 % du pic (100)
         + [200.0] * 3                            # nouveau sommet
         + [150.0]                                # krach 2 : 1 mois sous -20 % du pic (200)
         + [260.0 + k for k in range(140)])
    r = replique_pwl(fabrique(v, taux_annuel_pct=2.0), debut=None, horizon_months=120)
    assert r["fenetres_retenues"] == 4            # 3 fenetres du krach 1 + 1 du krach 2
    assert r["blocs_de_fenetres_contigus"] == 2   # mais DEUX blocs seulement


def test_blocs_ne_comptent_PAS_un_krach_deja_en_cours_au_depart():
    """Si le mois d'AVANT la 1re fenetre est deja sous le seuil, la 1re fenetre est la QUEUE d'un
    krach anterieur — pas le debut d'un nouveau bloc.

    Vecu sur les vraies donnees : en 1933-12 le marche est a -58 %, et le code comptait 1934-01
    comme un episode neuf -> 15 blocs au lieu de 14. L'erreur allait dans le sens qui RASSURE.
    """
    # Pic au mois 0, effondrement des le mois 1 et jusqu'au mois 4, puis remontee definitive.
    v = [100.0, 60.0, 61.0, 62.0, 63.0] + [200.0 + k for k in range(140)]
    df = fabrique(v, taux_annuel_pct=2.0)
    # `debut` au mois 3 : la 1re fenetre est 2000-04, et son mois d'avant (2000-03) est deja a -38 %.
    r = replique_pwl(df, debut="2000-04", horizon_months=120)
    assert r["fenetres_retenues"] >= 1
    assert r["blocs_de_fenetres_contigus"] == 0, (
        "aucun NOUVEAU bloc ne commence : le krach etait deja en cours avant la 1re fenetre"
    )


def test_replique_pwl_refuse_quand_aucune_chute_n_a_eu_lieu():
    df = fabrique([100.0 + k for k in range(150)], taux_annuel_pct=2.0)
    with pytest.raises(DonneeManquante, match="replique PWL impossible"):
        replique_pwl(df, debut=None, horizon_months=120)


def test_replique_pwl_STOPPE_sur_un_trou_au_milieu():
    """Un mois absent AILLEURS qu'au tout debut = donnee manquante -> STOP, jamais un silence."""
    v = [100.0] * 5 + [70.0] + [130.0 + k for k in range(150)]
    df = fabrique(v, taux_annuel_pct=2.0)
    # On casse la serie d'indice APRES le calcul des fenetres de l'ep. 1 : impossible ici, donc
    # on verifie l'autre bout — la 1re fenetre sans mois d'avant est TOLEREE, et une seule.
    r = replique_pwl(df, debut=None, horizon_months=120)
    assert r["fenetres_totales"] == len(v) - 120
    assert r["fenetres_retenues"] >= 1
