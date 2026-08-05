# 📐 CONTRAT — module BACKTEST KRACH (« Le Test » ép. 2)

*Rédigé le 04/08/2026, **AVANT** toute ligne de code. Règle `@.claude/rules/code.md` §1.*
*Protocole figé de référence : `PF_LeTest_Ep2_Krach_PROTOCOLE.md` (verrouillé avant calcul).*

## 0. Ce que ce module DOIT être

L'extension du moteur de l'ép. 1. Il mesure **une seule question** : *« attendre un repli
de X % pour investir, ça donne quoi, sur toutes les fenêtres de l'Histoire ? »*
Il ne raconte rien. Il publie **toutes les fenêtres**, jamais celle qui arrange.
Il est **publié avec la vidéo** : quelqu'un doit pouvoir le relancer et retrouver nos chiffres.

**Il RÉUTILISE le moteur ép. 1** (`backtest.py` / `build_data.py`) : mêmes données, mêmes
garde-fous (`_serie`, contiguïté des mois, taux de cash par devise, refus explicite). Aucune
duplication de la logique de chargement — un seul endroit où une donnée peut manquer.

---

## 1. Signature

```python
run_krach(df: pd.DataFrame,
          marche: str = "US",            # "US" | "US_EUR" | "JP" | "JP_EUR"  (porte AUSSI la devise)
          horizon_months: int = 120,     # 10 ans (même standard que l'ép. 1)
          seuils: tuple[float, ...] = (0.10, 0.20, 0.30),   # FRACTIONS : 0.20 = -20 %
          cash_rate: str = "taux_court", # "taux_court" (celui de LA DEVISE) | "zero"
          real: bool = False,            # True = déflaté par l'IPC — US SEULEMENT
          annual_fee: float = 0.0,       # FRACTION (0.003 = 0,3 %), bornée à 10 %/an
          debut: str | None = "1934-01", # force la MÊME période pour des scénarios comparables
          reference: str = "ath",        # "ath" = plus-haut historique réel | "depuis_t0"
          delai_execution: int = 0,      # mois entre le signal et l'achat (0 = achat le mois du signal)
          ) -> pd.DataFrame              # 1 LIGNE PAR FENÊTRE DE DÉPART, jamais un chiffre unique
```

### Les 4 robots (protocole §2, non négociables)
| Robot | Règle |
|---|---|
| **A** (témoin) | investit 100 % du capital à `t0`. C'est le lump sum de l'ép. 1. |
| **B10 / B20 / B30** | reste en **cash rémunéré** ; investit **tout**, en une fois, au **premier** mois où l'indice est ≤ −10 / −20 / −30 % **sous le dernier plus-haut**. |
| Cash en attente | rémunéré au **taux court de la devise du marché** (`cash_rate="taux_court"`). **Jamais 0 %** dans le scénario principal. |
| Attente infinie | si le repli n'arrive jamais avant la fin de l'horizon, **B reste en cash jusqu'au bout**. C'est un **résultat publié**, pas une fenêtre exclue. |

### ⚠️ Le point d'interprétation du protocole : « le dernier plus-haut »
Le protocole dit « depuis le dernier plus-haut » sans dire **si ce plus-haut peut être
antérieur à `t0`**. Les deux lectures sont défendables et **elles ne donnent pas le même
chiffre**. On ne tranche donc PAS à la place d'Aleksandar : **on calcule et on publie les deux.**

- `reference="ath"` — le plus-haut **historique réel**, calculé sur **toute** la série
  (depuis 1871), même avant `t0`. Lecture littérale du protocole, et convention des études
  « buy the dip ». **Conséquence :** une fenêtre qui démarre alors que le marché est déjà
  sous le seuil → **B investit dès `t0` et devient identique à A** (égalité stricte, à publier
  à part : ce n'est ni une victoire ni une défaite).
- `reference="depuis_t0"` — le plus-haut **observé depuis que l'investisseur attend**.
  Lecture « je regarde le marché à partir d'aujourd'hui ». Aucune égalité au mois 0.

### Convention de calendrier (mensuel)
- Le signal du mois `T` est lu sur la valeur du mois `T` et l'achat se fait **à cette même
  valeur** (`delai_execution=0`). C'est une **hypothèse favorable à B** (achat au niveau
  exact observé). Elle est **mesurée**, pas supposée : la variante `delai_execution=1`
  (achat le mois suivant) est calculée et publiée.
- Le cash accumule le rendement du mois `j` pour chaque mois écoulé `j ∈ [t0+1, T]`
  (même convention que le DCA auto-financé de l'ép. 1).

---

## 2. Inputs valides / invalides — TOUS implémentés

- ✅ Valide : toute fenêtre `t0` telle que `t0 + horizon_months` existe dans la série.
- ❌ `seuils` vide, ou un seuil hors `]0, 1[` → `ValueError`. *(`20` au lieu de `0.20` = la
  coquille classique : elle doit exploser, pas produire « le krach n'arrive jamais ».)*
- ❌ `seuils` non triés / doublons → acceptés mais **normalisés** (tri croissant, dédoublonnés) :
  un ordre d'écriture ne doit pas changer un chiffre publié.
- ❌ `reference` inconnu → `ValueError` (jamais un `else` silencieux qui retombe sur un défaut).
- ❌ `delai_execution < 0` ou non entier → `ValueError`.
- ❌ `real=True` sur autre chose que `"US"` → `ValueError` (on n'a que l'IPC **américain**).
- ❌ `annual_fee=0.3` → `ValueError` (c'est 30 %/an, pas 0,3 %).
- ❌ `cash_rate="taux_court"` sur une devise sans série suffisante → `DonneeManquante`.
  **Conséquence assumée : le Japon long tourne à `cash_rate="zero"`** (le taux court JPY de
  FRED commence en 2002 et ne couvre pas le krach de 1990). **Ça DÉFAVORISE les robots B**
  japonais → notre chiffre japonais pour B est un **plancher**. Dit à l'écran.
- ❌ Mois **non contigus** → `DonneeManquante` (hérité de `_serie`, ép. 1).
- ❌ Série plus courte que l'horizon → `DonneeManquante`.

## 3. Erreurs attendues
Toute donnée absente → **exception explicite**. Jamais un `NaN` qui se propage jusqu'à
l'écran, jamais un `fillna` silencieux. **Un trou de données est un STOP, pas un zéro.**

---

## 4. MÉTRIQUES PUBLIÉES (protocole §4 — toutes, aucune sélection)

Pour **chaque** seuil, sur **toutes** les fenêtres :
1. **% de fenêtres où B bat A** — et, séparément, **% d'égalité stricte** et **% où A bat B**.
   *(Sans la colonne « égalité », le mode `ath` compterait une égalité comme une défaite de B.)*
2. **Écart médian** `B/A − 1` (et la moyenne, publiée à côté — jamais à la place).
3. **Temps d'attente** : moyenne et médiane des mois passés en cash **quand le signal arrive**,
   plus le **% de fenêtres où il n'arrive JAMAIS** sur les 10 ans.
4. **Pire et meilleur cas de chaque stratégie** : multiple final min/max (× le capital) pour A
   et pour chaque B, plus l'écart min/max — avec la **date de départ** de chacun.
5. **Décomposition honnête** : les mêmes chiffres restreints aux fenêtres **où le signal est
   arrivé** (ce que l'attente donne *quand elle est « récompensée »*).
6. **Réplique Japon** (mêmes 4 robots) — biais de survie.
7. **Réplique PWL** (protocole §5) : voir §5 ci-dessous.

## 5. Le contrôle externe PWL — ⚠️ ce n'est PAS la même mesure que B20

**Chiffre étalon** : Benjamin Felix, PWL Capital, *« Dollar Cost Averaging vs. Lump Sum
Investing »*, juin 2020, **Table 7 p. 9 : États-Unis = 50,00 %**.
*(Déjà cité et sourcé dans le Fact-Lock de l'ép. 1 — PDF lu le 13/07/2026.)*

> ⛔ **PWL ne mesure PAS notre B20.** PWL mesure : *après une chute de 20 % **déjà constatée**,
> le **lump sum** bat-il le **DCA sur 12 mois** ?* → 50 % aux USA.
> Notre B20 mesure : *attendre une chute de 20 % **qui n'est pas encore arrivée**, en cash,
> bat-il l'investissement immédiat ?* **Ce sont deux expériences différentes.**

Le module calcule donc **les deux** :
- `B20` (notre question), et
- **`replique_pwl`** — la vraie réplique du chiffre PWL avec nos données : on prend le
  **TEST A de l'ép. 1** (lump vs DCA 12 mois) et on le **restreint aux fenêtres qui démarrent
  alors que le marché est déjà ≥ 20 % sous son plus-haut historique**. Ce chiffre-là, et lui
  seul, est comparable aux 50,00 % de PWL.

Écarts déclarés d'avance avec PWL : indice (CRSP 1-10 vs S&P 500 Shiller), période
(01/1926–03/2020 vs 01/1934–06/2026), granularité (nos prix Shiller sont des **moyennes
mensuelles**), cash (bon du Trésor 1 mois chez PWL, 3 mois chez nous).

---

## 6. Sortie
- `resultats/krach_<marche>_<reference>_<cash>_<...>.csv` — **une ligne par fenêtre** :
  départ, fin, valeur finale A, et pour chaque seuil : mois de déclenchement (ou vide),
  valeur finale B, écart %.
- `resultats/synthese_krach.json` — tous les scénarios **+ une section
  `A_LIRE_AVANT_DE_CITER_UN_CHIFFRE`** qui dit ce que chaque chiffre **ne** prouve **pas**.
- `resultats/SECTION_7.md` — **le tableau du §7 du protocole, généré par le moteur.**
  **Aucun chiffre n'est jamais tapé à la main, nulle part.**
- **Un chiffre sans son fichier daté = un chiffre non publiable.**

---

## 7. ⚠️ LES BIAIS — déclarés AVANT le calcul

| Biais | Situation | Ce qu'on fait |
|---|---|---|
| **Granularité** | Shiller = moyennes mensuelles → **lisse les krachs**. Un −20 % intra-mois peut ne jamais apparaître. | Déclaré à l'écran. Le signal B est donc **conservateur** : certains replis réels sont ratés par la donnée. Mesuré côté ép. 1 (`biais_lissage.json`). |
| **Définition du plus-haut** | Change le résultat. | **Les DEUX définitions publiées** (§1). |
| **Exécution** | Acheter au mois du signal = hypothèse favorable à B. | Variante `delai_execution=1` calculée. |
| **Biais de survie** | Ne tester que les USA = choisir le marché le plus performant du siècle. | **Japon obligatoire** (Nikkei, FRED). |
| **Dividendes** | Nikkei FRED = **PRIX SEUL**. | Déclaré : le Japon est **sous-estimé**. |
| **Le cash qui attend** | À 0 %, on assassine B. | `taux_court` par défaut ; version `zero` publiée **à côté**, jamais à la place. Japon long = `zero` faute de série → **plancher pour B**. |
| **Nominal vs réel** | | Jamais une série réelle avec un taux nominal. Défaut = **nominal**, « avant frais, avant impôt ». |
| **Cherry-picking** | | **Période et règles figées avant le calcul. Toutes les fenêtres publiées.** |
| **Extrapolation** | | **Interdiction de conclure sur le futur.** Un backtest ne prédit rien. |
| **Fenêtres chevauchantes** | 990 fenêtres de 10 ans issues de 92 ans de données ne sont **pas** 990 observations indépendantes. | Déclaré : **aucun test de significativité**, aucun « p-value ». On décrit, on n'infère pas. |

---

## 8. 🧯 TRIBUNAL DES CAS (règle code.md §3 — 10 pannes réelles, listées AVANT de coder)

| # | Panne | Parade codée |
|---|---|---|
| 1 | `data/marches.csv` absent (build jamais lancé) | `DonneeManquante` explicite → « lancer `build_data.py` » |
| 2 | OneDrive tient le CSV/JSON ouvert → `PermissionError` | `ecris()` de l'ép. 1 : échec **bruyant**, jamais à moitié |
| 3 | Disque plein → fichier tronqué | relecture de la taille après écriture (`ecris`) |
| 4 | Trou de mois dans une série (FRED révise) | contiguïté vérifiée par `_serie` → `DonneeManquante` |
| 5 | Taux court absent sur la devise (JPY < 2002) | `DonneeManquante` explicite → on bascule sur `zero` **en le disant** |
| 6 | Seuil passé en `20` au lieu de `0.20` | `ValueError` (borne `]0, 1[`) |
| 7 | `annual_fee=0.3` (30 %/an) | `ValueError` (hérité ép. 1) |
| 8 | Console Windows en cp1252 → `UnicodeEncodeError` à l'affichage | `sys.stdout.reconfigure(encoding="utf-8")` |
| 9 | Chemins avec espaces / `%` (dossier « Production 100 % IA ») | `pathlib` partout, jamais de concaténation de chaînes |
| 10 | Le signal tombe au **tout dernier mois** de l'horizon (`k = horizon`) | cas traité explicitement : B achète à la valeur finale → B = cash accumulé. Testé. |
| 11 | `real=True` sur `US_EUR` (le piège `startswith`) | liste blanche explicite (hérité ép. 1) |
| 12 | Fenêtre qui démarre déjà sous le seuil (mode `ath`) | B ≡ A → **égalité stricte comptée à part**, jamais comme une défaite |

## 9. Tests (le test qui échoue d'abord — code.md §4)
`test_backtest_krach.py`, sur séries **synthétiques** aux valeurs calculables à la main :
marché qui ne baisse jamais (100 % de « jamais déclenché »), krach de −20 % au mois connu,
cash à 0 % (B = 1,0 exactement), monotonie des seuils (B30 ne déclenche jamais avant B20),
égalité stricte en mode `ath`, signal au dernier mois, et **tous** les refus du §2.

## 10. Gates avant livraison
`pytest` → `ruff check .` → agent **`code-reviewer`** → agent **`fact-check`** sur les
chiffres sortis. **Aucun chiffre ne part dans le protocole §7 avant que le moteur ait tourné.**
