# Backtest — « DCA vs tout d'un coup » (Pilote Finance)

Le code de l'épisode **Pilote Finance — « DCA vs tout d'un coup »**. Il est publié pour que
n'importe qui puisse **refaire le calcul** et nous contredire.

**Données : Robert Shiller ([shillerdata.com](https://shillerdata.com/)) + [FRED](https://fred.stlouisfed.org/)** —
séries publiques, téléchargées à l'exécution. Aucune clé d'API n'est nécessaire.

**Le bug qu'on avoue dans la vidéo est documenté dans [`BUG_v1_2026-07-13.md`](BUG_v1_2026-07-13.md)**
— ligne par ligne, et reproductible. Notre premier chiffre était faux ; les deux erreurs allaient
dans *notre* sens. C'est pour ça qu'on publie le code.

## Relancer

```bash
pip install -r requirements.txt
python build_data.py     # télécharge Shiller + FRED -> data/marches.csv + data/metadata.json
python backtest.py       # -> resultats/*.csv + resultats/synthese.json
```

Optionnel — mesure du biais de lissage de la série Shiller (prix = moyennes mensuelles) :

```bash
python mesure_biais_lissage.py    # -> resultats/biais_lissage.json
```

## Les fichiers

| Fichier | Quoi |
|---|---|
| `build_data.py` | Télécharge et assemble les séries. **Un trou = une exception, jamais un zéro.** |
| `backtest.py` | Le moteur : fenêtres glissantes, DCA vs tout d'un coup. |
| `mesure_biais_lissage.py` | Mesure l'effet du lissage de Shiller (il **flatte** le tout-d'un-coup). |
| `CONTRAT_backtest.md` | Ce que le module garantit — et ce qu'il refuse de faire. |
| `data/metadata.json` | Chaque série : source, période, granularité et **son biais déclaré**. |
| `resultats/synthese.json` | Tous les scénarios + **les avertissements à lire avant de citer un chiffre**. |
| `resultats/*.csv` | Le détail fenêtre par fenêtre (chaque chiffre a son fichier). |
| `BUG_v1_2026-07-13.md` | Le bug de la v1, documenté. |

## Épisode 2 — « Attendre le krach pour investir ? »

Le même dépôt porte le moteur du **deuxième épisode** : *faut-il attendre un krach avant
d'investir ?* Quatre robots, 10 000 $, un horizon de 10 ans, **990 départs mensuels** de
janvier 1934 à juin 2026 — celui qui investit tout de suite, et ceux qui attendent un repli de
10 %, 20 % ou 30 % avant d'entrer, leur argent placé en bons du Trésor pendant l'attente.

**Le protocole a été figé AVANT le moindre calcul** : [`PROTOCOLE_ep2_krach.md`](PROTOCOLE_ep2_krach.md).
Période, règles et métriques y sont verrouillées, et **toutes les fenêtres sont publiées, jamais
une sélection**.

```bash
python backtest_krach.py        # -> resultats/krach_*.csv + resultats/synthese_krach.json
python mesure_biais_seuil.py    # -> resultats/biais_seuil.json (granularité + prix vs rdt total)
python -m pytest test_backtest_krach.py
```

| Fichier | À quoi il sert |
|---|---|
| `backtest_krach.py` | Le moteur de l'ép. 2 : seuils de repli, attente en cash, 990 fenêtres. |
| `PROTOCOLE_ep2_krach.md` | Le protocole **figé avant calcul** (règle du Statisticien). |
| `CONTRAT_backtest_krach.md` | Ce que le module garantit — et ce qu'il refuse de faire. |
| `mesure_biais_seuil.py` | Mesure deux biais : la granularité mensuelle **lisse les krachs**, et l'indice de prix n'est pas le rendement total. |
| `resultats/synthese_krach.json` | Tous les scénarios + les avertissements à lire avant de citer un chiffre. |
| `resultats/cartes_ep2.json` | Les chiffres réellement affichés à l'écran, chacun avec sa source. |
| `resultats/SECTION_7.md` | Le tableau complet des résultats. |

Deux points que la vidéo dit et que le code prouve : le krach de −20 % **n'est jamais venu dans
32 % des fenêtres de 10 ans**, et le krach de 2020 vaut −33,9 % en cours quotidiens mais
−18,9 % dans notre donnée mensuelle en rendement total — **le même krach, trois mesures**, et le
robot ne se déclenche pas.

## À lire avant de citer un chiffre

`resultats/synthese.json` contient une section `A_LIRE_AVANT_DE_CITER_UN_CHIFFRE`. Elle n'est pas
décorative — elle liste ce que ces résultats **ne** disent **pas** (périodes non comparables,
l'écart n'est pas une perte, la ligne « réel » n'est pas une vérification indépendante…).

Les limites connues sont déclarées dans les données elles-mêmes (`data/metadata.json`), pas
enterrées : Shiller lisse les krachs, le Japon est sans dividendes, l'euro n'existe pas avant 1999.

## Licence

[MIT](LICENSE) — reprends-le, modifie-le, republie-le. C'est fait pour.

---

**Un backtest MESURE LE PASSÉ. Il ne prédit RIEN sur le futur.**
Expérience pédagogique sur données passées — **pas un conseil en investissement.**
