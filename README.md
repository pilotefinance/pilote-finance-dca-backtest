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
