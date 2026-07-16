# 📐 CONTRAT — module BACKTEST (avant toute ligne de code)
*Rédigé le 13/07/2026, avant l'implémentation. Règle `@.claude/rules/code.md` §1.*

## 0. Ce que ce module DOIT être
Le **moteur de preuve** de la nouvelle ligne éditoriale. Il est **publié avec la vidéo** (reproductible : quelqu'un doit pouvoir relancer et retrouver nos chiffres). Il ne « raconte » rien : il **mesure**, et il publie **toutes les fenêtres**, jamais celle qui nous arrange.

## 1. Signature — **RÉELLE** (amendée le 13/07/2026 après la gate code-reviewer)
```python
run(df,
    marche: str,            # "US" | "US_EUR" | "JP" | "JP_EUR"   (porte AUSSI la devise)
    horizon_months: int,    # 120 (10 ans, standard Vanguard)
    dca_months: int,        # 3 | 6 | 12 | 24
    cash_rate: str,         # "taux_court" (celui de LA DEVISE du marché) | "zero"
    real: bool,             # True = déflaté par l'IPC — **US SEULEMENT**
    annual_fee: float,      # FRACTION (0.003 = 0,3 %), bornée à 0,1 ; défaut 0 → « avant frais »
    accum_months: int,      # TEST B : durée d'accumulation avant investissement (défaut 12)
    debut: str | None,      # "1934-01" — force la MÊME période pour des scénarios comparables
) -> pd.DataFrame           # 1 ligne par fenêtre de départ, JAMAIS un chiffre unique
```
> 📌 **Amendement traçé.** La v1 du contrat annonçait `run_backtest(market=…, cash_rate="tbill")`. Le
> code réel expose la signature ci-dessus. Le contrat est publié avec la vidéo : **il doit dire la
> vérité du code**, pas une intention périmée.

## 2. Inputs valides / invalides — tous IMPLÉMENTÉS (vérifié par le relecteur)
- ✅ Valide : toute fenêtre `t0` telle que `t0 + horizon_months` existe.
- ❌ **`marche="US_EUR"` avant janvier 1999** → série vide. **L'euro n'existe pas avant.** Aucun ECU synthétique.
- ❌ `dca_months > horizon_months` → `ValueError`.
- ❌ **`real=True` sur autre chose que `"US"`** → `ValueError`. On n'a que l'IPC **américain** : il ne déflate ni le Japon ni la zone euro. *(Le premier garde-fou testait `marche.startswith("US")` — or `"US_EUR".startswith("US")` vaut **True** : on aurait déflaté des euros par le CPI-U. Corrigé en liste blanche explicite.)*
- ❌ **`cash_rate="taux_court"` sur une devise sans série suffisante** → `DonneeManquante`. **Un investisseur japonais n'est pas rémunéré au bon du Trésor américain.**
- ❌ `annual_fee=0.3` → `ValueError` (c'est 30 %/an, pas 0,3 % — coquille classique, bornée à 10 %).
- ❌ Mois **non contigus** dans une série → `DonneeManquante` (sinon un « horizon de 120 mois » couvrirait plus de 120 mois calendaires en silence).

## 3. Erreurs attendues (comportement, pas plantage muet)
Toute donnée absente → **exception explicite**, jamais un `NaN` qui se propage jusqu'au graphique. Jamais de `fillna` silencieux. **Un trou de données est un STOP, pas un zéro.**

---
## 4. LES DEUX TESTS (le protocole est figé AVANT de calculer)

**TEST A — le capital qu'on a DÉJÀ** (la question classique)
`Tout d'un coup` (j'investis les 10 000 € à t0) **vs** `DCA` (je les étale sur D mois ; ce qui attend dort au taux du cash).
Les deux sont mesurés **à la même date de fin** (t0 + horizon).

**TEST B — le salaire qui TOMBE CHAQUE MOIS** (🎯 notre thèse — personne ne la dit en France)
`Immédiat` (j'investis mes 500 € dès qu'ils arrivent) **vs** `J'accumule 12 mois puis j'investis le tas`.
→ Ce test existe pour **prouver que « 500 €/mois depuis son salaire » n'est PAS du DCA** : c'est une série de petits « tout d'un coup ». Les études ne condamnent qu'une chose : **étaler un capital qu'on a déjà.**

## 5. Sortie
- `resultats/resultats_<marche>_dca<D>_<cash>_<nominal|reel>[_frais]_<debut|tout>.csv` : **une ligne par fenêtre de départ** (départ, fin, valeur finale A, valeur finale B, écart %).
- `data/metadata.json` : source, URL, **date de génération**, période, devise, dividendes oui/non, granularité, **biais déclarés**.
- `resultats/synthese.json` : les 10 scénarios **+ une section `A_LIRE_AVANT_DE_CITER_UN_CHIFFRE`** qui dit noir sur blanc ce que chaque chiffre **ne** prouve **pas**.
- **Un chiffre sans son fichier daté = un chiffre non publiable.**

---
## 6. ⚠️ LES BIAIS — DÉCLARÉS D'AVANCE (le Statisticien les a listés, on ne les découvre pas après)
| Biais | Notre situation | Ce qu'on fait |
|---|---|---|
| **Granularité** | Shiller = **moyennes MENSUELLES** de cours quotidiens → **lisse les krachs**. On croyait que ça flattait notre thèse. **On l'a mesuré : c'est plus subtil que ça.** | **MESURÉ, pas supposé** (`mesure_biais_lissage.py`, sur le Nikkei) : **+1,2 pt** sur le taux de victoire du tout-d'un-coup, mais **−0,51 pt** sur l'écart médian. **Biais MIXTE** → à l'écran, on donne **les deux chiffres**. |
| **Biais de survie** | Ne tester que les USA = choisir le marché le plus performant du siècle | **Japon obligatoire** (1949→2026, il a perdu 80 % et mis 34 ans à revenir) |
| **Devise** | Le change peut faire **10× l'écart mesuré** | Version **EUR** systématique — mais **seulement à partir de 1999** |
| **Dividendes** | Shiller les a. **Le Nikkei 225 de FRED = PRIX SEUL** | On l'annonce : le Japon est **sous-estimé** (dividendes exclus) |
| **Nominal vs réel** | | On ne mélange **jamais** une série réelle et un taux nominal |
| **Le cash qui attend** | Cash à 0 % ≠ cash rémunéré → **ça change le résultat** | Les **deux** versions sont calculées |
| **Frais / fiscalité** | | Défaut = 0 → résultats **annoncés « avant frais »** |
| **Cherry-picking** | | **Période ET règle figées AVANT le calcul. Toutes les fenêtres publiées.** |
| **Extrapolation** | | **Interdiction de conclure sur le futur.** Un backtest ne prédit rien. |

## 7. Architecture — 2 options (règle §7 : décision structurante)
- **(a) Pré-calculer → CSV/JSON, le data-film ne fait que LIRE.** ✅ **RETENU.** Le chiffre est figé, versionné, publiable, rejouable. Le film ne peut pas inventer ce qu'il n'a pas lu.
- **(b) Le film calcule à la volée.** ❌ Rejeté : un bug de rendu deviendrait un bug de **donnée**, et on ne pourrait pas publier le chiffre sans relancer la vidéo. Mauvais choix ici parce que **l'anti-fiction exige que la donnée soit un artefact séparé, vérifiable.**

---
# 🚨 CE QUE LE CODE NE PROUVE PAS (à lire AVANT d'écrire une ligne de script)
*Ajouté le 13/07/2026 sur signalement du code-reviewer. Ce sont les deux endroits où le module pourrait faire dire à l'écran plus fort que ce qu'il mesure.*

### 1. La ligne « en réel » est une TAUTOLOGIE — elle ne vérifie rien
L'écart du TEST A est **mathématiquement invariant au déflateur** : l'inflation se simplifie exactement dans le rapport tout-d'un-coup / DCA. Les chiffres A de la ligne `real=true` sont donc **identiques au centième** à ceux de la ligne nominale — ce n'est pas une confirmation, c'est une **identité algébrique**.
> ⛔ **INTERDIT à l'écran** : « et même en tenant compte de l'inflation, on retrouve 68,9 % ». Ce serait présenter une trivialité comme une preuve de robustesse.
> ✅ Seul le **TEST B** bouge en réel — et il suppose alors un **salaire parfaitement indexé sur l'inflation**. À dire si on l'utilise.

### 2. Le DCA n'est PAS « 12 versements égaux de 833 € »
Le cash qui attend est **rémunéré**, et ses intérêts sont **réinvestis avec les versements suivants** : le 12ᵉ versement est plus gros que le 1ᵉʳ (en 1981, taux ~15 %/an → **+14 %**).
> C'est économiquement juste, mais **quiconque reproduit avec la règle naïve « 10 000 ÷ 12 » ne retrouvera pas nos chiffres.** Le module est publié avec la vidéo : si on décrit la méthode à l'écran, on décrit **celle-là**.

### 3. Le biais de lissage est MIXTE — pas dans le sens qu'on croyait
On a **mesuré** l'effet des moyennes mensuelles de Shiller (sur le Nikkei, seul marché dont on a le quotidien) : **+1,2 pt** sur le taux de victoire du tout-d'un-coup, mais **−0,51 pt** sur l'écart médian. *(Chiffres régénérés le 13/07/2026 après correction du mois de juillet incomplet — la 1re version disait +1,3 / −0,53.)*
> ⛔ On ne peut donc PAS dire « le lissage flatte notre thèse ». Il faut donner **les deux chiffres**.
> ✅ Et c'est un bien meilleur moment de télé : *« on a mesuré notre propre biais — il n'était pas où on le croyait. »*
