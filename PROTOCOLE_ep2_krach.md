# 🔒 PROTOCOLE FIGÉ — « Le Test » ép. 2 : Attendre le krach pour investir ?
**Créé le 04/08/2026 par Cowork (Opus) · GO Aleksandar 04/08 · Statut : PROTOCOLE VERROUILLÉ AVANT CALCUL.**
**Règle d'or (Statisticien) : la période, les règles et les métriques ci-dessous sont figées AVANT d'exécuter le moindre calcul. On publie TOUTES les fenêtres, jamais une sélection. Le verdict sort même s'il nous contredit.**

---
## 1. LA QUESTION (l'intention de recherche captée)
« J'ai de l'argent à investir, mais les marchés sont hauts. **Est-ce que j'attends le krach ?** »
Le Short « Attendre le krach pour investir ? Pile ou face » = 135 vues · 52,4 % de rétention sur 32 abonnés — meilleure distribution organique du mois. La longue répond à la question que le Short a ouverte.

## 2. LES STRATÉGIES COMPARÉES (règles mécaniques, zéro jugement)
Un capital de départ (ex. 10 000 $ — même convention que l'ép. 1), un horizon donné, et 4 robots :
- **A (témoin)** : investit TOUT immédiatement (lump sum). C'est le témoin de l'ép. 1.
- **B10** : reste en cash rémunéré, investit tout au premier repli de **−10 %** depuis le dernier plus-haut.
- **B20** : idem au premier repli de **−20 %** (le « vrai krach » officiel, bear market).
- **B30** : idem à **−30 %**.
- **Règle du cash (piège n°1 du Statisticien)** : le cash en attente est rémunéré au **taux court US (série FRED déjà dans le moteur)** — jamais à 0 %.
- **Règle de l'attente infinie** : si le repli n'arrive jamais avant la fin de l'horizon, B reste en cash rémunéré jusqu'au bout — c'est un résultat, pas un cas à exclure.

> 📌 **AMENDEMENT TRACÉ — le « dernier plus-haut » (Aleksandar, 04/08/2026).** La v1 disait « depuis le dernier plus-haut » sans préciser si ce plus-haut pouvait être **antérieur à t0**. Le moteur a signalé l'ambiguïté **avant** de trancher, et a calculé les deux lectures. **Arbitrage : la lecture PRINCIPALE est « plus-haut OBSERVÉ DEPUIS t0 »** — l'investisseur regarde le marché à partir du jour où il a l'argent. La lecture « **plus-haut historique réel** » (le pic peut dater d'avant t0 : en 1934, le marché est encore loin sous son sommet de 1929) **reste publiée en comparaison** au §7. Les deux chiffres restent au protocole ; aucun ne peut être cité sans dire lequel c'est.

## 3. DONNÉES & FENÊTRES (identiques à l'ép. 1 — moteur réutilisé)
- **Marché principal** : S&P 500 **dividendes réinvestis** (Robert Shiller, shillerdata.com), mensuel.
- **Période** : la totalité disponible du moteur ép. 1 (1934-2026), **tous les départs mensuels possibles** (~990 fenêtres), horizon **10 ans** par défaut.
- **Contrôle biais de survie (piège n°2)** : répliquer le test sur le **Nikkei 225** (FRED, déjà dans le moteur) — le marché qui a mal tourné.
- **Convention affichée à l'écran (héritée ép. 1)** : « en dollars, avant frais et avant impôt » — dit tel quel, carte + description. Nominal, jamais mélangé avec du réel.
- **Granularité mensuelle** assumée et dite (piège n°9 : une moyenne mensuelle lisse les krachs).

> 📌 **DÉCISION CONFIRMÉE — 2020 et 2022 (Aleksandar, 04/08/2026) : PROTOCOLE INCHANGÉ.** Le moteur a découvert que **ni le Covid ni 2022 ne déclenchent le robot B20** dans notre donnée. Ce n'est pas un bug : c'est la conséquence, mesurée, des deux choix déjà inscrits dans ce §3 (dividendes réinvestis + moyennes mensuelles). **Aucune règle ne change.** En contrepartie, ces chiffres sont **DITS À L'ÉCRAN** — encadré « granularité » du §7.2 bis, c'est un moment fort de l'épisode, pas une note de bas de page.

## 4. MÉTRIQUES PUBLIÉES (toutes, pas de sélection)
1. **% des fenêtres où chaque B bat A** (le chiffre du verdict).
2. Écart **médian** d'arrivée (pas seulement la moyenne).
3. **Temps moyen passé à attendre** le déclencheur (et % de fenêtres où il n'arrive JAMAIS).
4. Le pire cas et le meilleur cas de chaque stratégie (fourchette honnête).
5. Répliqué sur le Japon (mêmes 4 robots).

## 5. CONTRÔLE EXTERNE (anti-fiction) — ✅ **AMENDÉ le 04/08/2026 après lecture intégrale du PDF**

> 📌 **Amendement tracé (Aleksandar, 04/08/2026).** La v1 de ce §5 disait : « après une chute de 20 %, le lump sum gagne encore ~50 % du temps ; notre B20 doit être confronté à ce chiffre : écart expliqué ou signalé. » **Cette formulation était fautive** : elle demandait de confronter deux tests qui ne posent pas la même question. Le PDF a été lu intégralement ; voici les définitions exactes, et le cadre de lecture corrigé.

**La source** : Benjamin Felix, PWL Capital, *« Dollar Cost Averaging vs. Lump Sum Investing »*, **juin 2020**.
🔗 `https://pwlcapital.com/wp-content/uploads/2024/08/Dollar-Cost-Averaging-vs-Lump-Sum-Investing.pdf`

**La méthode exacte, côté États-Unis** :
- Indice : **CRSP 1-10, en RENDEMENT TOTAL** (ce n'est **pas** un indice de prix).
- Période : **01/1926 → 03/2020**. Cash en attente : **bons du Trésor 1 mois**. Devise : **USD**.
- **Table 7, p. 9** : LSI (tout d'un coup) *vs* **DCA sur 12 mois**, sur des fenêtres démarrant **LE MOIS SUIVANT** une chute **≥ 20 % « from the previous peak »** (chute mesurée en données **mensuelles**).
- Résultats : **États-Unis 50,00 %** · moyenne des 6 marchés **53,66 %** · avantage annualisé du tout d'un coup **+0,25 pt/an**.
- **PWL attribue lui-même** la faiblesse du chiffre américain aux **années 1930**.

**⚠️ CADRE DE LECTURE — PWL et notre B20 sont COMPLÉMENTAIRES, pas concurrents :**
| | La question posée |
|---|---|
| **PWL** | Le krach **a déjà eu lieu**. J'ai le capital en main : je place tout d'un coup, ou j'étale ? |
| **Notre B20** | Le krach **n'a pas encore eu lieu**. J'attends en cash qu'il arrive, ou je place tout de suite ? |

> ⛔ **Il est donc INTERDIT de présenter l'un comme un « écart » à expliquer par rapport à l'autre.** Ce sont deux expériences différentes, et elles se complètent : PWL répond à « après », nous répondons à « avant ».

**Ce qui est quand même comparable** : le moteur réplique la règle PWL **à l'identique** sur nos données (mêmes fenêtres « le mois suivant une chute ≥ 20 % »).

❌ **L'hypothèse « prix vs rendement total » est ÉCARTÉE** : les deux études travaillent en rendement total.

🚩 **L'écart résiduel est SIGNALÉ, pas expliqué.** La seule piste disponible est celle que **PWL avance lui-même** — ses années 1926-1933, absentes de notre période. **Et nous ne pouvons pas la tester** : le taux court US (FRED TB3MS) commence en 1934-01 ; sans lui, le cash du DCA serait à 0 %, ce qui favorise mécaniquement le tout d'un coup — on ne reconstituerait pas leur chiffre, on en fabriquerait un autre.

> 🧾 **Correction tracée, 05/08/2026.** Une version antérieure de ce §5 et du §7.5 écrivait que l'écart était « expliqué » parce que « nos fenêtres post-krach sont presque toutes des sorties de crise gagnantes ». **Vérification faite : c'est faux sur nos données.** Nos fenêtres les plus anciennes sont les *moins* favorables au tout d'un coup, pas les plus. La phrase a été retirée des deux endroits. Le découpage de période qui l'accompagnait vit désormais dans `synthese_krach.json` comme **diagnostic pour le fact-check uniquement** : découper une période après avoir vu le résultat, c'est ce que la règle d'or interdit de publier comme résultat.

⚠️ **Enfin** : nos fenêtres éligibles ne forment qu'un **petit nombre de blocs contigus** (chiffre généré au §7.5). Des fenêtres consécutives décrivent le même krach vu à un mois d'intervalle — ce ne sont pas des observations indépendantes. Et un bloc **n'est pas** un bear market distinct : un même krach se recoupe en plusieurs blocs dès que l'indice repasse un mois au-dessus du seuil (1937, 1987-88, 2004). **Le nombre de krachs réellement distincts est donc encore plus petit que le chiffre affiché** — l'approximation va dans le sens qui rassure, on la déclare.

- Rendu : FEU VERT fact-check obligatoire sur chaque chiffre affiché (source + date sur chaque carte).

## 6. ⚖️ PRÉ-CHECK CONFORMITÉ (compliance-finance.md v2)
- Terrain : **méthode mesurée sur un INDICE** → hors MAR, hors conseil (liste ✅ n°3). Aucun ETF/instrument nommé. Aucun « achetez / attendez / il faut ». Aucune extrapolation vers le futur — **interdiction de conclure « donc fais X »** : le verdict est un constat historique, la leçon est pédagogique.
- Mentions prod : IA=Oui · Not for kids · sources+dates à l'écran · « expérience pédagogique, pas un conseil ».

## 7. RÉSULTATS (remplis PAR LE MOTEUR — `backtest_krach.py`, DONNEES_REELLES=True)

> Généré le **2026-08-04 22:14 UTC** par `backtest_krach.py` (dépôt `pilote-finance-dca-backtest`).
> Données : S&P 500 dividendes réinvestis (Robert Shiller, shillerdata.com) + taux courts FRED, `data/marches.csv`. **En dollars, avant frais et avant impôt. Nominal.**
> Chaque chiffre ci-dessous sort d'un fichier de résultats daté : §7.1 à §7.4 des `resultats/krach_*.csv`, §7.2 bis de `resultats/biais_seuil.json`, §7.5 de `resultats/synthese_krach.json`. **Aucun chiffre saisi à la main.**

**Scénario principal : 1934-01 -> 2026-06, 990 fenêtres de départ mensuelles, horizon 10 ans, cash en attente rémunéré au bon du Trésor 3 mois (FRED TB3MS), plus-haut = **celui observé depuis t0** — l'investisseur regarde le marché à partir du jour où il a l'argent.**

> 🔁 **Arbitrage Aleksandar, 04/08/2026 — le « dernier plus-haut ».** Le protocole ne tranchait pas entre deux lectures. La lecture retenue est **« observé depuis t0 »**. La lecture **« plus-haut historique réel »** (le pic peut être antérieur à t0, comme en 1934 où le marché est encore loin sous 1929) reste **publiée en comparaison** — scénario `US_plushaut_historique` au §7.1. Sur le seuil des −20 %, l'écart entre les deux lectures est de **36.1 %** (retenue) contre **29.8 %** (comparative).

### 7.1 — Le tableau brut (tous les scénarios, toutes les fenêtres)

| Scénario | Robot | B bat A | égalité stricte | écart médian | krach JAMAIS venu | attente moy. si on attend (mois) | pire écart | meilleur écart |
|---|---|---|---|---|---|---|---|---|
| US_principal | B10 | 39.1 % | 0.0 % | -7.15 % | 0.0 % | 31.4 | -74.86 % | +37.90 % |
| US_principal | B20 | 36.1 % | 0.0 % | -27.62 % | 32.0 % | 48.9 | -82.39 % | +58.41 % |
| US_principal | B30 | 26.5 % | 0.0 % | -48.39 % | 64.4 % | 54.9 | -82.39 % | +78.08 % |
| US_plushaut_historique | B10 | 29.0 % | 33.3 % | +0.00 % | 0.0 % | 30.6 | -73.30 % | +23.63 % |
| US_plushaut_historique | B20 | 29.8 % | 18.2 % | -6.69 % | 24.5 % | 50.3 | -82.39 % | +58.41 % |
| US_plushaut_historique | B30 | 26.6 % | 12.4 % | -39.93 % | 55.4 % | 51.8 | -82.39 % | +65.45 % |
| US_achat_M1 | B10 | 41.4 % | 0.0 % | -4.68 % | 0.0 % | 31.4 | -74.33 % | +50.91 % |
| US_achat_M1 | B20 | 35.9 % | 0.0 % | -26.71 % | 32.0 % | 48.9 | -82.39 % | +73.35 % |
| US_achat_M1 | B30 | 27.9 % | 0.0 % | -48.31 % | 64.4 % | 54.9 | -82.39 % | +85.04 % |
| US_cash_zero | B10 | 30.3 % | 0.0 % | -16.90 % | 0.0 % | 31.4 | -78.29 % | +37.31 % |
| US_cash_zero | B20 | 26.5 % | 0.0 % | -41.32 % | 32.0 % | 48.9 | -85.35 % | +55.51 % |
| US_cash_zero | B30 | 18.9 % | 0.0 % | -66.84 % | 64.4 % | 54.9 | -85.35 % | +58.48 % |
| US_long_1871 🕒 | B10 | 35.9 % | 0.0 % | -9.83 % | 0.0 % | 28.3 | -78.81 % | +37.31 % |
| US_long_1871 🕒 | B20 | 32.3 % | 0.0 % | -20.85 % | 19.0 % | 50.2 | -85.35 % | +58.87 % |
| US_long_1871 🕒 | B30 | 18.9 % | 0.0 % | -54.62 % | 60.1 % | 54.6 | -85.35 % | +78.45 % |
| US_EUR 🕒 | B10 | 50.2 % | 0.0 % | +1.16 % | 0.0 % | 20.5 | -55.41 % | +29.77 % |
| US_EUR 🕒 | B20 | 54.1 % | 0.0 % | +5.19 % | 42.9 % | 24.7 | -82.12 % | +46.54 % |
| US_EUR 🕒 | B30 | 57.1 % | 0.0 % | +23.93 % | 42.9 % | 31.4 | -82.12 % | +69.42 % |
| JP 🕒 | B10 | 46.2 % | 0.0 % | -2.79 % | 0.0 % | 16.7 | -74.53 % | +31.28 % |
| JP 🕒 | B20 | 40.4 % | 0.0 % | -13.53 % | 8.4 % | 29.7 | -83.12 % | +57.18 % |
| JP 🕒 | B30 | 32.5 % | 0.0 % | -47.21 % | 26.7 % | 47.7 | -83.12 % | +82.82 % |
| JP_plushaut_historique 🕒 | B10 | 10.4 % | 64.6 % | +0.00 % | 0.0 % | 19.4 | -68.11 % | +23.77 % |
| JP_plushaut_historique 🕒 | B20 | 17.9 % | 50.9 % | +0.00 % | 6.6 % | 30.9 | -83.12 % | +47.22 % |
| JP_plushaut_historique 🕒 | B30 | 14.9 % | 42.3 % | +0.00 % | 10.7 % | 55.1 | -83.12 % | +49.80 % |
| JP_cash_remunere_2002 🕒 | B10 | 54.4 % | 0.0 % | +2.99 % | 0.0 % | 16.0 | -49.44 % | +31.38 % |
| JP_cash_remunere_2002 🕒 | B20 | 48.5 % | 0.0 % | -2.27 % | 0.0 % | 27.4 | -46.85 % | +57.63 % |
| JP_cash_remunere_2002 🕒 | B30 | 23.7 % | 0.0 % | -49.12 % | 53.8 % | 32.3 | -72.42 % | +84.25 % |

*« B bat A » = % des fenêtres où attendre finit au-dessus d'investir tout de suite. « Égalité stricte » = fenêtres où le marché était **déjà** sous le seuil au départ : B investit à t0, il EST A. Ce ne sont ni des victoires ni des défaites.*

🕒 **Périodes différentes du scénario principal (1934-01 -> 2026-06) : `US_long_1871` (1871-02 -> 2026-06), `US_EUR` (1999-01 -> 2026-01), `JP` (1949-05 -> 2026-06), `JP_plushaut_historique` (1949-05 -> 2026-06), `JP_cash_remunere_2002` (2002-04 -> 2026-04).** Ces lignes ne se comparent PAS au principal ni entre elles : on comparerait des données, pas une hypothèse. En particulier `US_EUR` intègre l'effet de change et ne couvre que l'après-1999 — c'est le seul scénario où attendre ressort gagnant, et cette victoire n'est **pas** transposable au tableau principal.

### 7.2 — Le chiffre que le protocole exige : le krach qui n'arrive JAMAIS

| Robot | % des fenêtres de 10 ans où le repli n'est JAMAIS venu | signal déjà là à t0 | attente médiane si le signal vient après t0 |
|---|---|---|---|
| B10 | **0.0 %** | 0.0 % | 26.0 mois |
| B20 | **32.0 %** | 0.0 % | 43.0 mois |
| B30 | **64.4 %** | 0.0 % | 51.0 mois |

*Scénario principal (1934-01 -> 2026-06, 990 fenêtres). Dans les fenêtres « JAMAIS », le robot B a passé **10 ans entiers en cash** sans jamais investir.*

### 7.2 bis — 🚨 OÙ SONT PASSÉS 2020 ET 2022 ? (tranché : protocole inchangé, chiffres dits)

Sur 1934-01 -> 2026-06 (1110 mois), le S&P 500 dividendes réinvestis a passé, sous son plus-haut historique (calculé depuis 1871-02) :

> ℹ️ **Ce tableau-ci est en lecture « plus-haut historique »**, pas en lecture « depuis t0 » (celle du §7.2). C'est volontaire : la question posée ici est « le marché a-t-il été 20 % sous son sommet ? », indépendamment de la date d'arrivée de l'investisseur. Le sens de l'écart est **conservateur** : un plus-haut observé depuis t0 est toujours ≤ le plus-haut historique, donc **en lecture principale les signaux sont encore plus rares** que ce que montre ce tableau.

| Seuil | mois passés sous le seuil | % du temps | dernier mois sous le seuil |
|---|---|---|---|
| B10 | 346 | 31.2 % | **2025-04** |
| B20 | 180 | 16.2 % | **2010-09** |
| B30 | 123 | 11.1 % | **2009-08** |

> ⚠️ **Le seuil des −20 % n'a plus été atteint depuis 2010-09** — soit **189 mois** de suite. Sur toute cette période, le pire repli mensuel mesuré est **-19.26 %** (2022-10). Les trois pires années depuis : **2022 : -19.26 %** · **2020 : -18.92 %** · **2010 : -18.32 %**.

**Pourquoi ? Deux suspects, MESURÉS séparément** (`mesure_biais_seuil.py` → `resultats/biais_seuil.json`, généré le **2026-08-04 21:45 UTC**) — aucune cause n'est affirmée sans son chiffre :

**Suspect 1 — les dividendes réinvestis.** Mêmes mois, même règle, 1934-01 -> 2026-06 : seule change la définition de l'indice.

| Indice | mois passés sous −20 % | % du temps | dernier mois sous −20 % |
|---|---|---|---|
| **Prix seul** (celui dont parlent les médias) | 356 | 32.1 % | **2022-10** |
| **Rendement total** (ce que le protocole §3 impose) | 180 | 16.2 % | **2010-09** |

Pire repli de chaque année, dans les deux mondes :

| Année | prix seul | rendement total |
|---|---|---|
| 2017 | -0.32 % | -0.15 % |
| 2018 | -11.52 % | -11.08 % |
| 2019 | -10.14 % | -9.53 % |
| 2020 | -19.09 % | -18.92 % |
| 2021 | -0.19 % | -0.08 % |
| 2022 | -20.29 % | -19.26 % |
| 2023 | -15.28 % | -13.81 % |
| 2024 | -1.12 % | -1.01 % |
| 2025 | -11.08 % | -10.88 % |
| 2026 | -3.96 % | -3.77 % |

**Suspect 2 — la granularité mensuelle.** Mesurée sur le Nikkei (1949-05 -> 2026-07), seul marché dont on a le quotidien sur longue période. Même marché, même règle, seule change la finesse.

⚠️ *Les deux colonnes ne comptent pas la même chose : en **quotidien**, un mois compte dès qu'**un seul jour** passe sous le seuil ; en **mensuel**, il compte si **la valeur du mois** est sous le seuil. C'est justement la comparaison qui nous intéresse — un robot qui surveillerait en quotidien verrait-il des signaux que le nôtre ne voit pas ?*

| Granularité | mois où le signal −20 % existe | part des mois | dernier mois avec signal |
|---|---|---|---|
| **Quotidien** (la vérité) | 546 | 58.9 % | 2025-04 |
| Fin de mois | 494 | 53.3 % | 2023-10 |
| **Moyenne du mois** (méthode Shiller, la nôtre) | 487 | 52.5 % | 2023-05 |

➡️ **La moyenne mensuelle rate 59 mois de signal sur les 546 que voit le quotidien.** L'effet existe, il est réel — mais il est plus petit que celui du suspect 1.

*Biais mesure sur le NIKKEI. Ce n'est pas mecaniquement sa valeur sur le S&P 500 : c'est un ORDRE DE GRANDEUR, a presenter comme tel.*


---

#### 📺 ENCADRÉ « GRANULARITÉ » — À DIRE À L'ÉCRAN

*Arbitrage Aleksandar du 04/08/2026 : protocole INCHANGÉ, et ces chiffres sont dits, pas enterrés en note de bas de page.*

| Krach | en cours **quotidiens** | en **moyenne mensuelle** (prix) | en **moyenne mensuelle** (dividendes réinvestis) | notre robot le voit ? |
|---|---|---|---|---|
| **2020** | **-33.92 %** (2020-03-23) | -19.09 % → NON | -18.92 % → NON | **NON** |
| **2022** | **-25.43 %** (2022-10-12) | -20.29 % → OUI | -19.26 % → NON | **NON** |

> **Le Covid a fait −33.92 % en cours de séance. Dans notre donnée mensuelle, il vaut −18.92 % : il n'a jamais atteint les −20 %. Notre robot « j'attends le krach » ne l'a même pas vu passer.**

Source du quotidien : FRED SP500 (https://fred.stlouisfed.org/series/SP500), 2016-08-04 -> 2026-08-03, 2512 séances. Indice de PRIX (sans dividendes) : a comparer a la colonne 'prix seul' de la section B, jamais a la colonne 'rendement total'. FRED SP500 ne couvre que les ~10 dernieres annees : le plus-haut de reference ne remonte pas avant le premier jour disponible. Valable pour 2020 et 2022, PAS pour une question anterieure.

---

✅ **DÉCISION PRISE (Aleksandar, 04/08/2026) : PROTOCOLE INCHANGÉ.** S&P 500 dividendes réinvestis et granularité mensuelle restent tels quels — les deux étaient déjà déclarés au §3. En contrepartie, **ces chiffres sont dits à l'écran** : voir l'encadré ci-dessous. Aucune règle, aucune période, aucune métrique n'a été modifiée après le calcul.

### 7.3 — Le pire et le meilleur cas de chaque robot (fourchette honnête)

| Robot | multiple final le PIRE (départ) | multiple final le MEILLEUR (départ) |
|---|---|---|
| A (témoin) | ×0.7 (1999-03) | ×6.82 (1949-06) |
| B10 | ×0.72 (1999-03) | ×5.96 (1990-04) |
| B20 | ×0.94 (1999-03) | ×5.12 (1987-09) |
| B30 | ×0.97 (1999-03) | ×4.39 (2008-09) |

*Multiple final du capital de départ, mêmes fenêtres, avant frais et avant impôt.*

### 7.4 — ⚠️ SOUS-ENSEMBLE : les fenêtres où le signal est venu APRÈS t0

> 🚨 **Le chiffre le plus flatteur du document, et le plus facile à sortir de son contexte.** Cette section **exclut** les fenêtres où le krach n'est jamais venu — c'est-à-dire précisément celles où le robot a attendu **10 ans entiers en cash sans jamais investir**. Elle ne dit donc pas « ce que donne l'attente », elle dit « ce que donne l'attente **quand elle est récompensée** ». Interdiction de citer une de ces valeurs sans son dénominateur.

| Robot | fenêtres retenues | exclues : signal jamais venu | exclues : signal déjà là à t0 | B bat A | écart médian |
|---|---|---|---|---|---|
| B10 | **990 / 990** *(toutes les fenêtres — pas un sous-ensemble)* | 0 | 0 | 39.1 % | -7.15 % |
| B20 | **673 / 990** | 317 | 0 | 53.0 % | 2.14 % |
| B30 | **352 / 990** | 638 | 0 | 73.3 % | 31.52 % |

*C'est la SEULE comparaison licite avec le scénario `US_achat_M1` : le taux brut du §7.1 bouge pour une raison comptable (les égalités disparaissent), pas économique.*

### 7.5 — Le contrôle externe PWL 2020 : DEUX QUESTIONS COMPLÉMENTAIRES (protocole §5)

> ✅ **Fact-check fait le 04/08/2026 : PDF PWL lu intégralement.** L'hypothèse « écart prix vs rendement total » est **écartée** — les deux études travaillent sur des indices de **rendement total**. Et surtout : **les deux tests ne posent pas la même question.** Ils ne se contredisent pas, ils se complètent.

| | La question posée | Le chiffre |
|---|---|---|
| **PWL / Felix 2020 (USA)** | Le krach **a déjà eu lieu**. J'ai le capital en main : je place tout d'un coup, ou j'étale sur 12 mois ? | le tout d'un coup gagne **50.00 %** du temps |
| **Notre réplique de leur test** | La même question, la même règle, sur nos données : 181 fenêtres démarrant **le mois suivant** une chute ≥ 20 % (= 14 blocs contigus, soit encore moins de krachs réels) | **71.3 %** |
| **Notre B20** | Le krach **n'a pas encore eu lieu**. J'attends en cash qu'il arrive, ou je place tout de suite ? | attendre gagne **36.1 %** du temps (**53.0 %** quand le signal finit par venir) |

**La méthode PWL, telle qu'écrite dans le PDF** : CRSP 1-10, RENDEMENT TOTAL (pas un indice de prix) · 01/1926 -> 03/2020 · cash = bons du Tresor US 1 MOIS · USD · LSI (tout d'un coup) vs DCA sur 12 MOIS, sur des fenetres demarrant LE MOIS SUIVANT une chute >= 20 % « from the previous peak » (mesuree en donnees MENSUELLES). Table 7, p. 9 : États-Unis **50.00 %**, moyenne des 6 marchés **53.66 %**, avantage annualisé du tout d'un coup **+0.25 pt/an**.
Source : Benjamin Felix, PWL Capital, « Dollar Cost Averaging vs. Lump Sum Investing », juin 2020 — https://pwlcapital.com/wp-content/uploads/2024/08/Dollar-Cost-Averaging-vs-Lump-Sum-Investing.pdf

**Notre réplique donne 71.3 % contre 50.00 % (+21.3 pt). Cet écart est SIGNALÉ, pas expliqué.** La seule piste disponible est celle que **PWL avance lui-même** : PWL attribue lui-meme la faiblesse du chiffre americain aux annees 1930, incluses dans sa periode (depuis 1926) et ABSENTES de la notre (depuis 1934, faute de taux court US avant cette date). Notre série commence en **1934-01**.

⛔ **Et cette piste, nous ne pouvons pas la tester :** Rejouer PWL sur 1926-1933 chez nous : le taux court US (FRED TB3MS) commence en 1934-01. Sans lui, le cash du DCA serait a 0 %, ce qui FAVORISE mecaniquement le tout d'un coup — on ne reconstituerait donc pas le chiffre de PWL, on en fabriquerait un autre. On s'arrete et on le dit.

> 🧾 **Note de méthode, ajoutée le 05/08/2026.** Une version antérieure de cette section écrivait que « nos fenêtres post-krach sont presque toutes des sorties de crise gagnantes ». **Vérification faite : c'est faux sur nos données** — nos fenêtres les plus anciennes sont les *moins* favorables au tout d'un coup, pas les plus. La phrase a été retirée. Le découpage de période qui l'accompagnait reste dans `synthese_krach.json` comme **diagnostic pour le fact-check**, et n'est pas publié ici : découper une période après avoir vu le résultat, c'est précisément ce que le protocole interdit de présenter comme un résultat.

⚠️ **181 fenêtres ne sont pas 181 observations indépendantes : elles ne forment que **14 blocs contigus** depuis 1934-01.** Des fenêtres consécutives décrivent le même krach vu à un mois d'intervalle. Et le nombre de krachs **réellement distincts est encore plus petit** : un même bear market se recoupe en plusieurs blocs dès que l'indice repasse un mois au-dessus du seuil (1937, 1987-88, 2004). Un bloc = une suite de fenetres eligibles qui se touchent. Ce n'est PAS un bear market distinct : un meme krach se recoupe en plusieurs blocs des que l'indice repasse un mois au-dessus du seuil (1937, 1987-88 et 2004 sont dans ce cas). Le nombre de krachs REELLEMENT distincts est donc encore PLUS PETIT que ce chiffre. L'erreur va dans le sens qui rassure — on la declare. C'est la note « fenêtres chevauchantes » du §7.6, poussée à l'extrême.

*Repère : le même test **sans aucune condition de repli** donne **68.9 %** sur les 990 fenêtres — c'est le chiffre publié à l'ép. 1.*

Différences de méthode déclarées :
- Indice : S&P 500 dividendes reinvestis (Shiller) vs CRSP 1-10 (PWL). ⚠️ LES DEUX sont des indices de RENDEMENT TOTAL : l'ecart ne vient PAS d'un choix prix vs dividendes reinvestis.
- Periode : 1934-01 -> 2026-06 vs 01/1926 -> 03/2020 (PWL). C'est la difference principale : les annees 1930 sont chez eux, pas chez nous.
- Granularite : nos prix Shiller sont des MOYENNES MENSUELLES ; la chute de 20 % de PWL est elle aussi mesuree en donnees mensuelles.
- Cash : bon du Tresor 3 mois (TB3MS) chez nous, bons du Tresor US 1 MOIS chez PWL.

### 7.6 — Ce que ces chiffres NE prouvent PAS

- **le_protocole_etait_FIGE_avant_le_calcul** — Periode, regles et metriques sont verrouillees dans PF_LeTest_Ep2_Krach_PROTOCOLE.md AVANT que ce script tourne. Toutes les fenetres sont publiees, jamais une selection.
- **PWL_et_B20_sont_COMPLEMENTAIRES_pas_concurrents** — PWL (Table 7 p. 9, 50,00 % aux USA) mesure : le krach A DEJA EU LIEU, je place tout d'un coup ou j'etale sur 12 mois ? Notre B20 mesure : le krach N'A PAS ENCORE EU LIEU, faut-il l'attendre en cash ? Ce sont DEUX QUESTIONS DIFFERENTES. Presenter l'une comme un 'ecart' a l'autre serait une faute de lecture. Fact-check du 04/08/2026 : les deux etudes utilisent des indices de RENDEMENT TOTAL — l'hypothese d'un ecart prix/dividendes est ECARTEE ; l'ecart vient de la PERIODE (PWL inclut les annees 1930, pas nous) et de l'INDICE (CRSP 1-10 vs S&P 500).
- **le_plus_haut_ARBITRE_le_04_08_2026** — Le protocole ne disait pas si le plus-haut pouvait etre anterieur a t0. ARBITRAGE ALEKSANDAR : la lecture PRINCIPALE est 'depuis_t0' (le plus-haut observe depuis que l'investisseur a l'argent). La lecture 'ath' (plus-haut historique reel) reste PUBLIEE en comparaison — scenario US_plushaut_historique. Elles ne donnent PAS le meme chiffre : citer l'un sans dire lequel, c'est cacher la moitie du resultat.
- **le_plus_haut_ne_remonte_pas_avant_le_debut_de_la_SERIE** — En mode 'ath', le plus-haut est le maximum depuis le PREMIER MOIS DISPONIBLE de la serie : 1871 pour le S&P 500, mais 1949 pour le Nikkei et 1999 pour les series en euros (champ 'plus_haut_remonte_a' de chaque scenario). Les toutes premieres fenetres de ces series voient donc un plus-haut tronque.
- **les_egalites_ne_sont_PAS_des_defaites_EN_LECTURE_ath** — ⚠️ NE CONCERNE PAS LE SCENARIO PRINCIPAL (lecture depuis_t0, ou il n'y a aucune egalite). En lecture 'ath', une fenetre qui demarre DEJA sous le seuil fait investir B des t0 : B est alors STRICTEMENT identique a A. Ces fenetres sont comptees a part (pct_fenetres_egalite_stricte). Les noyer dans 'A bat B' gonflerait artificiellement le score du temoin.
- **comparer_achat_M1_au_principal_EST_LICITE_en_lecture_depuis_t0** — En lecture 'depuis_t0' (le scenario principal) aucune fenetre ne declenche a t0 : la comparaison brute entre US_principal et US_achat_M1 EST valide, le delai d'execution est la seule chose qui change. ⚠️ En lecture 'ath' en revanche elle ne l'est PAS : les fenetres qui declenchaient a t0 cessent d'etre des egalites strictes et deviennent des victoires ou des defaites, donc le taux brut bouge pour une raison COMPTABLE. Pour ces scenarios-la, passer par le bloc 'quand_le_signal_est_venu_APRES_t0'.
- **le_repli_est_mesure_en_RENDEMENT_TOTAL_pas_en_prix** — Le protocole §3 fixe le S&P 500 dividendes REINVESTIS : le repli des robots B est donc calcule sur le rendement total, pas sur l'indice de prix dont parlent les medias quand ils annoncent un 'bear market'. Les dividendes reinvestis rabotent mecaniquement le repli. Effet MESURE (pas suppose) : biais_seuil.json.
- **granularite_mensuelle** — Les prix Shiller sont des MOYENNES MENSUELLES de cours quotidiens : elles LISSENT les krachs. Effet MESURE sur le DECLENCHEMENT D'UN SEUIL : resultats/biais_seuil.json (section A, sur le Nikkei quotidien). ⚠️ Ne PAS confondre avec resultats/biais_lissage.json (ep. 1), qui mesure l'effet du lissage sur l'ecart lump/DCA — une autre question.
- **acheter_le_mois_du_signal_FLATTE_B** — Le scenario principal fait acheter B a la valeur du mois ou le repli est constate. Le scenario 'US_achat_M1' mesure un mois de reaction en plus — a lire via le bloc 'quand_le_signal_est_venu_APRES_t0', pas via le taux brut.
- **le_Japon_avec_cash_a_0_est_un_PLANCHER_pour_B** — Le taux court japonais (FRED) commence en 2002 et ne couvre pas le krach de 1990 : le scenario japonais long fait donc attendre B a 0 %. Ca DEFAVORISE B. Son chiffre japonais est un plancher, pas une mesure exacte.
- **le_Nikkei_est_SANS_DIVIDENDES** — FRED NIKKEI225 = PRIX SEUL. Le Japon est donc sous-estime pour TOUTES les strategies (A comme B). A dire a l'ecran.
- **certains_scenarios_ne_mesurent_RIEN_EN_LECTURE_ath** — ⚠️ NE CONCERNE QUE LES SCENARIOS EN LECTURE 'ath'. Quand 100 % des fenetres declenchent a t0 (le Nikkei post-2002 est sous son pic de 1989 pendant des decennies), B n'attend jamais : il EST A. Ces scenarios portent un champ 'AVERTISSEMENT_SCENARIO_DEGENERE'. Les aligner dans un tableau a cote de scenarios qui mesurent quelque chose serait trompeur.
- **periodes_non_comparables** — Ne JAMAIS comparer deux scenarios dont le champ 'periode' differe (US_long_1871, US_EUR, JP, JP_cash_remunere_2002) : on comparerait des donnees, pas une hypothese.
- **fenetres_chevauchantes** — Des fenetres de 10 ans a pas mensuel se recouvrent : elles ne sont PAS des observations independantes. Aucun test de significativite, aucune p-value n'est publiee. On DECRIT le passe, on n'infere rien.
- **ecart_pct_n_est_PAS_une_perte** — L'ecart est RELATIF entre DEUX STRATEGIES. '-30 %' ne veut pas dire 'on perd 30 %' : ca veut dire que B finit 30 % sous A. A dire autrement a l'ecran.
- **aucune_conclusion_sur_le_FUTUR** — Un backtest MESURE LE PASSE. Il ne predit RIEN. Interdiction de conclure « donc fais X » (protocole §6, compliance-finance v2).

*(Fichiers sources : `resultats/synthese_krach.json`, `resultats/biais_seuil.json`, `resultats/krach_*.csv`.)*

## 8. HANDOFF
1. **CC** : étendre le moteur ép. 1 (`pilote-finance-dca-backtest`) → `backtest_krach.py` selon §2-4. Contrat d'abord (règle code.md §1), tests, ruff, code-reviewer. Sortie : tableau §7 + JSON.
2. **Cowork** : fact-check des sorties vs PWL → écriture du script (structure Opus, corps Fable) → panel 7 + **Statisticien (obligatoire, données chiffrées)** → v2 → prod CC → gates → publi (après réouverture du compte).
