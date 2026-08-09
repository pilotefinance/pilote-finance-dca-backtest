# Backtest — « DCA vs tout d'un coup » (Pilote Finance)

[![CI](https://github.com/pilotefinance/pilote-finance-dca-backtest/actions/workflows/ci.yml/badge.svg)](https://github.com/pilotefinance/pilote-finance-dca-backtest/actions/workflows/ci.yml)
*Ce badge est vert quand tous les tests et le lint passent — vérifié par GitHub à chaque
modification et re-validé chaque mois, pas par nous sur parole.*

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

## Épisode 3 — « Les frais : ce que dit le document officiel que personne ne lit »

Le troisième épisode ne rejoue pas un backtest : il **lit un document réglementaire** et **reprend
une mesure publiée par le régulateur**, puis chiffre ce qu'un écart de frais change sur un capital
placé une fois.

**La définition avant le chiffre.** Le périmètre des « frais courants » a été figé **avant** le
relevé, dans [`DEFINITION_FRAIS_ep3.md`](DEFINITION_FRAIS_ep3.md) : deux chiffres de définitions
différentes produisent un résultat arithmétiquement juste et éditorialement faux. Le module refuse
de comparer deux bornes qui ne partagent pas la même définition (`BornesIncomparables`).

**Le protocole a été figé AVANT le moindre calcul** :
[`PROTOCOLE_ep3_frais.md`](PROTOCOLE_ep3_frais.md).

**Aucun chiffre n'est saisi à la main.** Ils sont extraits du PDF de l'ESMA par
`relever_frais_ep3.py`, et l'empreinte SHA-256 du document est vérifiée à chaque exécution : si
l'ESMA remplace son PDF, le relevé **s'arrête** au lieu de s'adapter.

```bash
pip install -r requirements.txt
python relever_frais_ep3.py       # PDF ESMA -> faits_frais_ep3.json      (voir note ci-dessous)
python relever_citations_ep3.py   # PDF ESMA -> faits_citations_ep3.json
python simulateur_frais.py        # -> resultats_ep3/frais_ep3.json
python -m pytest test_simulateur_frais.py test_relever_frais_ep3.py test_carte_source.py
```

> **Le PDF de l'ESMA n'est pas redistribué ici** — c'est le document du régulateur. On publie son
> URL et son empreinte SHA-256 (dans `faits_frais_ep3.json`), ce qui permet de vérifier qu'on a lu
> **exactement** le même fichier. Place-le dans `sources_ep3/` pour rejouer les relevés ; sans lui,
> les tests qui en dépendent sont **ignorés proprement** (`skip`), jamais contournés.
> Source : ESMA, *Costs and Performance of EU Retail Investment Products 2025*
> (ESMA50-1949966494-4065), publié le 03/03/2026, données arrêtées au 31/12/2024 — table MR-CP.14, p. 18.

### Les fichiers de l'épisode 3

| Fichier | Quoi |
|---|---|
| `DEFINITION_FRAIS_ep3.md` | Le périmètre des frais, figé **avant** le relevé. |
| `PROTOCOLE_ep3_frais.md` | Le protocole figé avant calcul (règle du Statisticien). |
| `relever_frais_ep3.py` | Extraction déterministe des chiffres du PDF ESMA + vérification de l'empreinte. |
| `relever_citations_ep3.py` | Extraction des citations affichées à l'écran, au caractère près. |
| `simulateur_frais.py` | Le calcul : capital placé une fois, 10/20/30 ans, 0/5/7 % brut. |
| `carte_source.py` | La liste blanche des domaines officiels : une source invérifiable à l'écran est refusée. |
| `faits_frais_ep3.json` | Les chiffres relevés, avec leur catégorie, leur page et leur date. |
| `faits_citations_ep3.json` | Les citations exactes, avec leur page et leur note. |
| `resultats_ep3/frais_ep3.json` | La grille complète + ce que le calcul **ne prouve pas**. |

### Ce que ce calcul ne prouve pas

C'est écrit dans le JSON de résultats, et dit dans la vidéo : il **ne dit pas lequel choisir** — il
chiffre un écart de frais, rien d'autre. Il suppose la performance brute identique, ce qui n'arrive
jamais. Les frais courants **sous-estiment** le coût réel (ni courtage, ni écart achat-vente, ni
enveloppe, ni fiscalité). Et une moyenne de catégorie ne décrit **aucun produit** en particulier.
