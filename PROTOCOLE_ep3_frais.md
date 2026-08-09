# 🔒 PROTOCOLE — « Le Test » ép. 3 : les frais, ce que dit le document officiel

**v2 — 06/08/2026.** v1 créée le 05/08/2026 (sauvegardée : `_backups/PF_LeTest_Ep3_ETF_PROTOCOLE_v1_2026-08-05.md`).
**Statut : GO ÉCRITURE. Les 6 arbitrages sont rendus, le fact-check est passé.**

## ✅ ARBITRAGES ALEKSANDAR — 06/08/2026 (détail au registre)

| # | Décision |
|---|---|
| 1 | **Angle v2 : GO.** « Les frais : ce que dit le document officiel que personne ne lit. » |
| 2 | **Les 4 critères : VALIDÉS tels quels** (frais courants · réplication · encours · dividendes). Le Gardien recommandait de n'en garder qu'un ; arbitrage contraire assumé. |
| 3 | **Ratio de durée : grille d'impact ≤ 1/3, lecture du document ≥ 2/3.** Le **panel chronomètre** — Spectateur + Gardien. |
| 4 | **I5 : on MONTRE MR-CP.14 avec son sous-titre**, attribué explicitement (guillemets + source à l'écran + voix « c'est le régulateur qui l'écrit, pas nous »), phrase LR4 cond.1 **dans le même plan**. |
| 5 | **I6 : GO** — gate B-roll/Short codée **avant** toute prod. ✅ faite, `gate_broll_ep3.py`. |
| 6 | **B7 : correction du chapitre 4 de l'ebook** (source + extrait), impératif retiré. Dépublication Gumroad = geste Aleksandar. **L'ép. 3 ne décale pas**, correction cette semaine. |

⚠️ **Le §2 est validé mais reste le point faible identifié par le Gardien** : le critère 1 est
sourcé et occupe tout le §8 ; les critères 2, 3 et 4 n'ont ni source, ni relevé, ni gate. Le
chiffre solide leur prête sa crédibilité. **Le ratio du point 3 est ce qui empêche l'épisode de
basculer** — d'où le chronomètre au panel.

**Règle d'or (Statisticien) :** la période, les règles et les métriques sont figées **avant** le
moindre calcul. On publie toutes les valeurs obtenues, jamais une sélection. Le verdict sort même
s'il nous contredit.

> ⚠️ **C'EST L'ÉPISODE LE PLUS PROCHE DE LA LIGNE ROUGE QU'ON AIT JAMAIS FAIT.** Les deux premiers
> testaient une **méthode** (étaler ou non, attendre ou non). Celui-ci parle d'un **type
> d'instrument financier**. Le protocole est donc écrit d'abord pour dire ce qu'on **ne fera pas**.

---

## 📋 CHANGELOG v1 → v2 (ce qui a bougé, et pourquoi)

| # | Condition posée par le Gardien (05/08) | État | Preuve |
|---|---|---|---|
| 1 | `gate_conformite_ep3.py` écrite et VERTE sur le fichier piégé | ✅ **LEVÉE** | `test_gate_conformite_ep3.py` — 11 tests verts |
| 2 | Arbitrage Aleksandar sur les 4 critères amendés | ⏳ **ATTEND TON GO** | §2 ci-dessous |
| 3 | Décision d'angle (retourner l'épisode vers le document officiel) | ⏳ **ATTEND TON GO** — proposé adopté au §1 | §1 ci-dessous |
| 4 | Définition exacte des frais figée AVANT le relevé | ✅ **LEVÉE** | `DEFINITION_FRAIS_ep3.md` + 2 tests de refus |
| 5 | Points IMPORTANT (mention IA, extraction déterministe, B-roll, Short, DM, `carte_source.py`) | ✅ **INTÉGRÉS** | §5 bis et §7 |

**Ajouts de la v2 :** la définition des frais (§3 bis), le moteur et sa gate (§7), le relevé
déterministe et ses résultats complets (§8), les limites mesurées (§9).

---

## 0. LES SIX LIGNES ROUGES (inchangées — elles priment sur tout le reste)

**Elles ne sont pas négociables en cours de production. Si un choix éditorial les heurte, c'est le
choix éditorial qui saute, jamais la ligne rouge.** *(LR1, LR1 bis, LR2, LR3, LR5, LR6 sont
reprises mot pour mot de la v1 ; seule LR4 gagne sa mise en œuvre en code.)*

### 🔴 LR1 — AUCUN ETF NOMMÉ. Jamais, nulle part.
Ni dans le script, ni à l'écran, ni dans le titre, ni dans la miniature, ni dans la description,
ni dans les chapitres, ni dans les réponses aux commentaires. **Ni « par exemple », ni « comme
le… », ni un ISIN, ni un ticker, ni un nom d'émetteur.** Un nom cité « juste pour illustrer »
reste un instrument nommé — et un instrument nommé + une opinion = recommandation
d'investissement au sens **MAR**, ce qu'une chaîne anonyme ne peut pas produire
(`compliance-finance.md`, ligne rouge 2).
**Étendue (point 5 du Gardien) aux DM, mails, newsletter, live et commentaire épinglé.**
*Conséquence pratique assumée : on ne montrera jamais une capture d'écran de courtier, de
comparateur ou de fiche produit. Un logo lisible dans un B-roll est un STOP.*

### 🔴 LR1 bis — AUCUN INSTRUMENT **IDENTIFIABLE** (le trou de LR1)
LR1 interdit de **nommer**. Elle n'interdisait pas de **désigner**. Or MAR et l'AMF regardent si
l'instrument est *identifiable*, pas s'il est écrit.
- **Jamais plus de DEUX critères restrictifs** dans une même phrase, une même carte, un même plan.
- **Aucun critère restrictif chiffré** (voir LR2).
- **Test avant montage** : si la phrase seule permet de retrouver moins de dix produits, c'est une
  désignation → STOP.

### 🔴 LR2 — On enseigne sur des CATÉGORIES, jamais sur des produits. **AUCUN SEUIL.**
Aucun critère ne sort accompagné d'un plancher, d'un plafond ou d'un ordre de préférence.
« En dessous de 0,3 % c'est bon marché » **est une recommandation implicite**. On montre la
fourchette publique et **où on lit le chiffre dans le document**, jamais où passe la limite du bon
et du mauvais.
**La grille doit garder au moins un critère dont la réponse dépend du spectateur.** Une grille
dont toutes les cases pointent au même endroit **est** une recommandation.

> ~~🆕 v2 — le relevé montre que passif hors ETF (0,22 %) et ETF (0,21 %) sont à un centième l'un
> de l'autre : l'épisode ne peut mécaniquement pas pointer vers un type de produit.~~
>
> 🚫 **ARGUMENT RETIRÉ le 06/08 — le Gardien l'a démonté, et il avait raison.** Trois raisons :
> **(a)** il n'est pas dans l'épisode : le moteur compare l'**ETF** au fonds **actif**, le 0,22 %
> ne vit que dans un tableau de nuances — on ne se défend pas d'un pointage avec une donnée absente
> du plan qui claque ; **(b)** il était annulé par notre propre code : à égalité, le relevé
> départageait par ordre **alphabétique**, et « etf » passe avant « passif_non_etf » — le biais
> était dans le tri *(corrigé : le relevé refuse désormais de départager deux ex aequo)* ;
> **(c)** il se retourne juridiquement — dire « on ne peut pas pointer parce que deux catégories
> sont à égalité », c'est admettre que **si elles ne l'étaient pas, on pointerait**. L'édition 2027
> peut donner 0,25 contre 0,19. **Une ligne rouge conditionnée par un chiffre n'est pas une ligne
> rouge.** Le vrai bouclier ne doit rien aux données : aucun seuil, aucun instrument identifiable,
> un critère dont la réponse dépend du spectateur.

### 🔴 LR3 — Toute donnée de frais = fourchette PUBLIQUE, SOURCÉE et DATÉE.
Sources admises : **ESMA** (*Costs and Performance of EU Retail Investment Products*), **AMF**
(Observatoire de l'épargne), **règlement PRIIPs / DIC** pour la définition normalisée.
Chaque chiffre affiché porte sa source **et** sa date à l'écran. Une fourchette qu'on ne retrouve
pas dans un document public **ne se monte pas**.
✅ **v2 : appliquée par le code.** `NiveauDeFrais` refuse (`SourceManquante`) tout chiffre sans
source, page, URL, catégorie et date de relevé. Un chiffre non sourcé ne peut pas physiquement
entrer dans le moteur.

### 🔴 LR4 — Les calculs d'impact sont de l'ARITHMÉTIQUE, et les BORNES aussi doivent l'être.
Quatre conditions, toutes désormais **exécutées par du code** :

| Condition | Comment elle est tenue en v2 |
|---|---|
| 1. Bornes de même source, même catégorie, même date | `BornesIncomparables` sinon. Catégories différentes admises **uniquement** avec une phrase d'avertissement, **republiée dans la sortie JSON** donc obligatoirement à l'écran. |
| 2. Grille entière — 10/20/30 ans × ≥ 2 hypothèses **dont 0 %** | `GrilleIncomplete` sinon. Le moteur **n'expose aucune fonction** qui rende une seule case (test dédié). |
| 3. Sortie **par point de frais** | `cout_par_point_de_frais_euros` dans chaque case. |
| 4. Aucune extrapolation, code public, phrase « donc le moins cher gagne » **interdite** | Mentions obligatoires et §« ce que ce calcul ne prouve pas » écrits **dans la sortie JSON**, pas dans un coin du script. |

### 🔴 LR5 — RIEN À VENDRE, ET RIEN QUI Y MÈNE.
Sur CET épisode : **aucun lien affilié**, **aucun lien newsletter**, **aucun lien vers un produit
payant** — **l'ebook 7 € n'a rien à faire sous cet épisode-là.** Écran de fin pointant uniquement
vers une autre vidéo PF. La description ne contient QUE : les sources datées, le dépôt de code,
les mentions IA et pédagogique, les chapitres.
*Pourquoi si strict ici :* l'AMF (Q7) rappelle que **la gratuité ne protège pas**, et (Q5) qu'**un
envoi en nombre peut être « personnalisé »**. L'ESMA (janv. 2026) ajoute que *proposer des
formations ou des contenus pédagogiques pourrait également être considéré comme un conseil*.

### 🔴 LR6 — Le PACKAGING est soumis aux mêmes règles que le script.
Famille interdite dans le titre, la miniature, les chapitres et le commentaire épinglé :
**« le bon » · « le meilleur » · « bien choisir » · « celui qu'il te faut » · « ce qu'il faut
prendre » · « avant d'acheter »**. **Les DEUX variantes A/B** passent la gate, pas seulement celle
qui part. *Le CTR est à 1,0 % et c'est le goulot déclaré : c'est précisément sous cette pression
que la formulation interdite arrive.*

---

## 1. LA QUESTION ET L'ANGLE

**Angle v1 (abandonné)** : « les 4 critères pour choisir un ETF ». L'autorité venait de nous.

**Angle v2 — RECOMMANDÉ, adopté sous réserve de ton arbitrage (condition n°3 du Gardien) :**

> ### « Les frais : ce que dit le document officiel que personne ne lit »

L'autorité passe **de nous au document**. On n'explique plus « comment choisir » : on explique
**comment se lit un document réglementaire** (le DIC), et **ce que le régulateur lui-même publie**
sur les frais. C'est le terrain le plus sûr qui existe — expliquer la réglementation — et il
désamorce le piège « expert par perception du public » (règlement 2016/958, art. 1a) : voix IA
assurée + DA soignée = statut d'expert perçu, qui est le risque structurel n°1 de cet épisode.

**Intention de recherche visée** : *« comment choisir un ETF »* — explicite et récurrente,
cohérente avec le 2ᵉ poste de trafic de la chaîne (recherche : 78 vues / 102 min sur 28 j au
relevé du 05/08). L'ép. 2 venait des suggestions ; celui-ci vise la recherche.

**Ce que la vidéo ne fera pas :** dire lequel choisir. La promesse de la chaîne reste
« on ne te dit pas quoi acheter ».

> ⏳ **CE QUI ATTEND TON GO** : le basculement d'angle. Si tu gardes l'angle v1 (« les 4 critères »),
> tout le reste du protocole tient encore, mais le §1 doit être réécrit et le Gardien re-saisi sur
> ce point précis — c'était son bloquant le plus structurel.

## 2. LES 4 CRITÈRES — ⏳ ATTEND TON ARBITRAGE (condition n°2)

Inchangés depuis la v1, tels qu'amendés par le Gardien. Tu dois les valider ou les couper :

1. **Les frais courants** — le seul paramètre connu à l'avance et certain. *(Celui que le moteur
   chiffre. Le seul dont on ait des données publiques exploitables.)*
2. **Le mode de réplication** (physique / synthétique) — **descriptif pur**, risque de
   contrepartie énoncé comme **fait réglementaire** (règles UCITS de collatéralisation, sourcées),
   jamais comme « plus sûr / moins sûr ». ⚠️ **L'angle « éligibilité PEA » reste RETIRÉ** (LR1 bis).
3. **La taille de l'encours** — risque de fermeture/fusion, événement documenté et factuel.
   ⚠️ **La « liquidité » reste RETIRÉE** (prix d'exécution = terrain MAR).
4. **Le traitement des dividendes** (capitalisant / distribuant) — **NON NÉGOCIABLE (LR2)** : c'est
   le seul critère dont la réponse dépend du spectateur, donc le seul qui empêche la grille de se
   résoudre en une réponse unique.

*Candidats écartés volontairement : la **performance passée du fonds** (la mettre dans une grille
de choix suggérerait qu'elle prédit quelque chose) ; l'**écart de suivi / tracking difference**
(se calcule produit par produit → fait sauter LR1 bis et LR3 d'un coup).*

## 3. LES DONNÉES

- Fourchettes de frais par **catégorie** de fonds, issues des publications ESMA/AMF (LR3).
- **Aucune base produit, aucun scraping de courtier, aucun comparateur commercial.**
- Le calcul d'impact est un simulateur d'intérêts composés écrit pour l'occasion (`§7`).

## 3 bis. 🆕 LA DÉFINITION DES FRAIS — FIGÉE AVANT LE RELEVÉ (condition n°4 ✅)

**Document dédié : `DEFINITION_FRAIS_ep3.md`.** L'équivalent, pour cet épisode, du « PWL, Table 7,
p. 9 » de l'ép. 2.

Trois mesures coexistent et **ne mesurent pas la même chose** : les **frais courants** (récurrents,
constatés), les **frais d'entrée/sortie** (un **maximum déclaré**, pas ce qui est prélevé), et
l'**incidence des coûts annuels du DIC** (qui amortit les frais d'entrée sur la durée de détention
recommandée, donc dépend de l'horizon). **Les comparer entre elles, c'est la faute « prix vs
rendement total » de l'ép. 2, rejouée sur les frais.**

**Mesure retenue : les frais courants annuels** (`ongoing_costs_esma`), pour trois raisons écrites
**dans le rapport lui-même**, donc antérieures à toute valeur :
1. ESMA met lui-même l'accent dessus, et dit pourquoi (**p. 14**, encadré MR-CP.8) : les frais
   d'entrée publiés sont des **plafonds**, les frais courants sont un **niveau constaté**.
2. C'est la seule des trois qui est un **taux annuel** comparable d'un horizon à l'autre.
3. C'est la seule disponible pour **toutes les catégories**, à la même date, dans le même tableau.

**Ce que cette mesure EXCLUT, et qui sera DIT À L'ÉCRAN** — ESMA l'écrit noir sur blanc (**p. 19,
note 28**) : les **écarts achat-vente** payés en Bourse ne sont pas inclus, faute de données.
S'ajoutent les frais de courtage, les frais d'enveloppe et la fiscalité.
👉 **Conséquence assumée : notre chiffre SOUS-ESTIME le coût réel.** On le dit, et on dit pourquoi
on ne peut pas faire mieux. C'est l'inverse d'un chiffre qui arrange.

⚖️ **Traçabilité honnête** : la page 6 du rapport, valeurs comprises, a été affichée pendant
l'identification du document, **avant** la rédaction de la définition. C'est écrit noir sur blanc
au §5 de `DEFINITION_FRAIS_ep3.md` plutôt que passé sous silence. Ce que ça ne change pas : les
trois raisons ci-dessus sont dans le rapport, vérifiables par n'importe qui, et auraient donné la
même mesure quelles qu'aient été les valeurs.

## 4. LA MÉTHODE

1. ✅ Figer les 4 critères et les hypothèses (ce document) — *critères en attente de ton GO*.
2. ✅ Gardien conformité sur le protocole — rendu le 05/08, 5 conditions, 3 levées.
3. ✅ **Définition figée** (§3 bis) — **avant** le relevé.
4. ✅ **Relevé** des fourchettes publiques, source + page + date, par **extraction déterministe**
   (`relever_frais_ep3.py` → `faits_frais_ep3.json`).
5. ✅ **Moteur** (`simulateur_frais.py`) + gate (`test_simulateur_frais.py`) — sortie JSON avec
   source par chiffre.
6. ⏳ `fact-check` sur les chiffres affichés, puis panel de relecture (7 + **Statisticien**) sur le
   script.
7. ⏳ Prod : voix → cartes (`carte_source.py`) → montage FILM → gates (`gate_conformite_ep3`,
   `qa_video`, `gate_duree_voix`, pré-vol IA, provenance, `gate_packaging`).

## 5. CE QUI FERAIT ÉCHOUER CET ÉPISODE

- Un nom de produit qui se glisse « pour rendre concret » → **LR1**, STOP.
- Une fourchette de frais « de mémoire » ou reprise d'un site commercial → **LR3**, STOP.
- Une phrase du type « le moins cher est toujours le meilleur » : **recommandation déguisée**, et
  c'est faux (la réplication et l'encours comptent aussi).
- Une réponse en commentaire qui nomme un produit « à titre d'exemple » → réponse-type obligatoire.
- Un B-roll où un logo d'émetteur ou une interface de courtier est lisible → contrôle sur le
  **rendu final**, toute la durée du plan (leçon du 18/07).
- 🆕 **Additionner frais courants et frais d'entrée pour faire « le coût total »** → interdit : le
  second est un maximum déclaré (`DEFINITION_FRAIS_ep3.md`, §6).

## 5 bis. 🆕 LES POINTS IMPORTANT DU GARDIEN — INTÉGRÉS (condition n°5 ✅)

- **Mention IA dans les 30 premières secondes** (pas seulement en description) → contrôle
  `preflight_mention_ia.py`.
- **Aucun chiffre de frais produit ou « vérifié » par un modèle** → ✅ tenu : `relever_frais_ep3.py`
  extrait du PDF public avec `pypdf`, enregistre la **page**, la **table** et le **SHA-256** du
  document, et le relevé est **rejouable à l'identique** (test dédié).
- **Aucun plan de B-roll montrant un écran de cotation, une interface, un tableau de tickers ou un
  graphique chiffré** — interdit **à la génération**, pas « vérifié » après coup.
- **Le Short dérivé passe la même gate.** Le calcul d'impact et le critère de réplication sont
  déclarés **non découpables** : on ne sort pas la case à 30 ans toute seule en Short.
- **LR1 étendue aux DM, mails, newsletter, live et commentaire épinglé** ; modération quotidienne
  les **72 premières heures**.
- **Bandeau source via `carte_source.py`** (`SourceRefusee` = STOP). ⚠️ **`esma.europa.eu` est déjà
  dans `DOMAINES_OFFICIELS`** — vérifié, aucun ajout de domaine nécessaire.

## 6. INTERDICTION DE CONCLURE SUR LE FUTUR

Aucune phrase de la forme « donc prends… », « il vaut mieux… », « ça rapportera… ». Le livrable est
une **grille de lecture** et un **ordre de grandeur d'impact**, rien d'autre.

## 7. 🆕 LES GATES DE CET ÉPISODE — ÉCRITES ET VERTES (condition n°1 ✅)

| Gate | Ce qu'elle empêche | État |
|---|---|---|
| `gate_conformite_ep3.py` | ISIN, émetteur (**accents compris**), ticker (**y compris alphanumérique**), seuil chiffré, liste noire, URL hors liste blanche — **et désormais l'ABSENCE d'une mention obligatoire** | ✅ **31 tests verts**, dont le fichier piégé (8 pièges) |
| `test_simulateur_frais.py` | Comparer deux **définitions** de frais · **composer** une mesure qui n'est pas un taux annuel · publier une grille **amputée** d'un horizon ou du 0 % · un chiffre sans source, hors table autorisée, ou dont l'URL n'est pas affichable · une valeur de frais **en dur dans le code** (contrôle par AST) | ✅ **85 tests verts** |
| `test_relever_frais_ep3.py` | Un relevé qui **devine** l'ordre des colonnes · une année illisible qui replie en silence sur la précédente · un ex aequo départagé sans arbitrage · un document remplacé (SHA-256) · un relevé non rejouable | ✅ **23 tests verts** |

**⚙️ L'ENCHAÎNEMENT OBLIGATOIRE AVANT TOUT UPLOAD** — la chaîne complète, du PDF à l'écran.
**Les lignes ci-dessous sont FIGÉES et se copient telles quelles.** Elles ne se reconstituent pas
de mémoire : le 08/08/2026, la gate de conformité relancée sans ses `--script` a rendu **2 faux
STOP** sur le hook (« avant d'acheter », légitime dans un corps narratif, interdit en packaging).
Une gate qu'on relance mal, c'est un STOP auquel on finit par ne plus croire.

```bash
# --- 1. LES CHIFFRES : du PDF public aux faits sources -------------------------------------
python relever_frais_ep3.py                                 # PDF (SHA-256 verifie) -> faits_frais_ep3.json
python relever_citations_ep3.py                             # PDF -> faits_citations_ep3.json (citations ecran)
python simulateur_frais.py --faits faits_frais_ep3.json     # faits -> resultats_ep3/frais_ep3.json

# --- 2. LA PROD : voix -> cartes -> montage (la gate duree voix est DANS le build) ----------
python gen_voice.py PF_LeTest_Ep3_ETF_production_spec.json  # purger le MP3 a refaire : gen_voice saute l'existant
python gen_ep3_overlays.py                                  # 9 cartes + manifeste cartes_ep3.json
python build_film_generic.py PF_LeTest_Ep3_ETF_production_spec.json

# --- 3. LES GATES : dans cet ordre, toutes, avant de dire « c'est bon » ---------------------
ruff check .
python -m pytest -q                                         # suite complete du studio

python gate_conformite_ep3.py \
       PF_LeTest_Ep3_ETF_SCRIPT_v3.md PF_LeTest_Ep3_ETF_production_spec.json \
       cartes_ep3.json faits_citations_ep3.json REPONSES_TYPE_COMMENTAIRES_ep3.md \
       --script PF_LeTest_Ep3_ETF_SCRIPT_v3.md \
       --script PF_LeTest_Ep3_ETF_production_spec.json \
       --exige-json resultats_ep3/frais_ep3.json

python qa_video.py PF_LeTest_Ep3_ETF_build/PF_LeTest_Ep3_ETF_FILM_complet.mp4 400 480
python preflight_mention_ia.py PF_LeTest_Ep3_ETF_production_spec.json
python provenance.py PF_LeTest_Ep3_ETF_build/PF_LeTest_Ep3_ETF_FILM_complet.mp4   # doit dire SCRIPT-LOCK
```

**Les deux drapeaux qu'on oublie, et ce qu'ils coûtent :**
- `--exige-json` est **obligatoire** : sans lui la gate refuse de tourner (rc 2). C'est ce qui
  garantit que la phrase LR4 cond.1 arrive à l'écran, et non qu'elle dort dans un JSON.
- `--script` **déclare un corps narratif**. La famille packaging de LR6 (« avant d'acheter »,
  « bien choisir »…) est **STOP par défaut sur tout fichier** : il faut demander l'exception, on
  ne peut pas oublier d'être sévère. Le script et le spec (qui porte le texte dit) sont les
  **seuls** fichiers à déclarer — jamais les cartes, jamais la description, jamais le kit.
- **Le contrôle image des cartes reste MANUEL** (9 frames au centre de la fenêtre de chaque carte,
  relues à l'œil). Automatisation candidate en **P4** (`OPPORTUNITES_AUTOMATION.md`) : tant
  qu'elle n'existe pas, ce contrôle se fait à la main **à chaque rendu**, sans exception.

**Les DEUX refus centraux, ceux qui justifient tout le reste :**
1. deux niveaux de frais de **définitions différentes** → `BornesIncomparables` ;
2. une mesure qui **n'est pas un taux annuel récurrent** (frais d'entrée, incidence DIC) qu'on
   composerait sur 10/20/30 ans → `DefinitionNonSimulable`.

**Aucun des deux n'a de contournement, pas même un drapeau.** *(Le second a été ajouté à la
relecture du 06/08 : le premier seul laissait passer le pire cas — **deux** bornes en frais
d'entrée, composées comme une charge annuelle. Arithmétiquement juste, éditorialement faux : très
exactement la faute que ce protocole existe pour empêcher.)*

**Autres trous bouchés à la relecture du 06/08** (chacun avait son chemin de code) : grille réduite
au seul horizon 30 ans ; « coût par point » publié depuis un écart quasi nul ; moyenne présentée
comme point marginal ; dérogation « catégories différentes » déverrouillée par une chaîne d'un
caractère ; chiffre pris dans la table piégée p. 12 ; capital nul rendant une grille de zéros en
FEU VERT ; plantage disque sorti en code « refus de conformité ».

## 8. 🆕 RÉSULTATS (remplis PAR LE MOTEUR — aucun chiffre saisi à la main)

> Relevé : `relever_frais_ep3.py` → `faits_frais_ep3.json`.
> Calcul : `simulateur_frais.py` → `resultats_ep3/frais_ep3.json`.
> **Source unique** : ESMA Market Report — *Costs and Performance of EU Retail Investment
> Products 2025*, **ESMA50-1949966494-4065**, publié le **3 mars 2026**, données arrêtées au
> **31/12/2024**. Table **MR-CP.14, p. 18**, section « Equity UCITS — Ongoing costs », année
> **2024**, horizon **1 an**. SHA-256 du PDF : `0f87b0ef…41e68e`.

### 8.1 — Le relevé complet (les TROIS catégories, pas seulement les deux retenues)

| Catégorie (fonds actions UCITS, EU27) | Frais courants — horizon 1 an | horizon 10 ans |
|---|---|---|
| Gestion **active** | **1,28 %** | 1,39 % |
| Gestion **passive hors ETF** | **0,22 %** | 0,28 % |
| **ETF** | **0,21 %** | 0,26 % |

**Règle de sélection des bornes, figée avant lecture et purement mécanique** : borne basse = la
plus basse des trois, borne haute = la plus haute. Aucun choix humain, donc aucun cherry-picking
possible. → **écart retenu : 1,07 point de frais** (0,21 % ↔ 1,28 %).

> 📌 **Phrase obligatoire à l'écran (LR4 cond.1), générée par le relevé et republiée dans la
> sortie JSON :** « Ces deux chiffres sont des moyennes de deux catégories différentes de fonds
> actions — *UCITS actions — ETF* et *UCITS actions — gestion active* — publiées le même jour dans
> le même tableau de l'ESMA ; ce ne sont pas deux produits, et l'écart entre eux n'est pas un
> conseil. »

### 8.2 — La grille ENTIÈRE (10/20/30 ans × 0 % / 5 % / 7 %), 10 000 € placés, sans versement

| Horizon | Hypothèse | Capital à 0,21 % | Capital à 1,28 % | Écart (€) | Écart (% du capital sans frais) | Coût **moyen** par point relevé | Coût du **point suivant** |
|---|---|---|---|---|---|---|---|
| 10 ans | 0 % | 9 792 € | 8 791 € | **1 001 €** | **10,01 %** | 935 € | 938 € |
| 10 ans | 5 % | 15 950 € | 14 320 € | 1 630 € | **10,01 %** | 1 523 € | 1 528 € |
| 10 ans | 7 % | 19 262 € | 17 294 € | 1 969 € | **10,01 %** | 1 840 € | 1 846 € |
| 20 ans | 0 % | 9 588 € | 7 729 € | **1 860 €** | **18,60 %** | 1 738 € | 1 749 € |
| 20 ans | 5 % | 25 441 € | 20 506 € | 4 934 € | **18,60 %** | 4 611 € | 4 641 € |
| 20 ans | 7 % | 37 104 € | 29 907 € | 7 196 € | **18,60 %** | 6 725 € | 6 769 € |
| 30 ans | 0 % | 9 389 € | 6 794 € | **2 594 €** | **25,94 %** | 2 425 € | 2 448 € |
| 30 ans | 5 % | 40 578 € | 29 365 € | 11 213 € | **25,94 %** | 10 479 € | 10 582 € |
| 30 ans | 7 % | 71 470 € | 51 721 € | 19 749 € | **25,94 %** | 18 457 € | 18 637 € |

> ⚠️ **Pourquoi DEUX colonnes « par point » et pas une.** L'effet des frais **n'est pas
> linéaire** : le premier point de frais coûte plus cher que le deuxième. Diviser l'écart total
> par 1,07 point donne une **moyenne**, pas « le coût d'un point ». Le moteur publie donc aussi le
> **vrai point marginal** (0,21 % → 1,21 %). Ici les deux colonnes sont proches parce que l'écart
> relevé fait presque pile 1 point — **c'est une coïncidence de ce relevé, pas une propriété**.
> **Seule la colonne « point suivant » peut s'écrire à l'écran « ce que coûte 1 point de frais en
> plus ».** *(Trou détecté et bouché à la relecture du 06/08 : la première version ne publiait que
> la moyenne, sous le nom du marginal.)*

### 8.3 — 📺 LE CHIFFRE LE PLUS SOLIDE DE L'ÉPISODE (et ce n'est pas celui qui claque)

Regarde la colonne « **écart en % du capital** » : **10,01 % à 10 ans, 18,60 % à 20 ans, 25,94 % à
30 ans — identique à 0 %, à 5 % et à 7 % de rendement.**

Ce n'est pas une coïncidence, c'est de l'arithmétique : les frais sont un pourcentage de l'encours,
donc leur effet **ne dépend pas de la performance du marché**. La ligne à 0 % n'est pas la ligne
prudente : **c'est la même conclusion que toutes les autres**, débarrassée de toute hypothèse.

👉 **Ça règle le procès de l'hypothèse de rendement** : on ne peut pas nous reprocher d'avoir
choisi un rendement flatteur, puisque le pourcentage n'en dépend pas.

> ⚠️ **TROIS LIMITES, ajoutées après le fact-check du 06/08 — à respecter dans le script.**
> **(a) Le dénominateur, c'est le capital SANS AUCUN FRAIS, pas ce que le spectateur a versé.**
> À 0 % il vaut 10 000 € et personne ne se trompe ; à 7 % il vaut **76 123 €**, alors que le
> spectateur a en tête ses 10 000 €. Dire « 25,94 % du capital » sans préciser lequel est une
> ambiguïté, pas un raccourci. Le §8.5 impose la formulation.
> **(b) « Peu importe ce que fait la Bourse » est vrai pour le POURCENTAGE, faux pour les euros** :
> **à 30 ans**, le même écart vaut **2 594 €** à 0 % et **19 749 €** à 7 %. Et ce sont les euros
> qui finissent en miniature. La punchline ne peut donc pas être dite sans son support.
> *(Correction du 07/08 — la v1 de ce point opposait 1 001 € à 19 749 €, soit **10 ans à 0 %**
> contre **30 ans à 7 %** : la paire mélangeait deux horizons et gonflait l'écart qu'elle
> prétendait démontrer. À horizon constant, le rapport est de 1 à 7,6 — pas de 1 à 20.)*
> **(c) L'invariance vient du MODÈLE**, pas d'une observation : performance brute identique, frais
> en pourcentage constant de l'encours, versement unique. Elle règle le procès du rendement, pas
> celui du modèle — et elle **ne tient plus avec des versements réguliers** (relancer le moteur
> avec `versement_annuel` si le script en parle ; c'est la question la plus probable en
> commentaire, réponse-type R7).
> **(d) Arrondis** : sur 4 des 9 lignes, la soustraction des deux capitaux *arrondis* ne redonne
> pas l'écart affiché (25 441 − 20 506 = 4 935, la colonne dit 4 934). Aucune valeur n'est fausse
> — ce sont des arrondis de valeurs exactes — mais **ne pas mettre les trois nombres dans le même
> plan**, ou afficher l'écart seul.

### 8.4 — Ce que ces chiffres ne prouvent PAS (à écrire à l'écran, comme au §7.6 de l'ép. 2)

- **Ce sont des moyennes de catégories, pas des produits.** Personne n'achète « la moyenne ».
- **Le calcul suppose la performance brute identique** — ce qui n'arrive jamais. C'est une
  hypothèse d'école, affichée comme telle.
- **Le chiffre sous-estime le coût réel** : ni écart achat-vente, ni courtage, ni enveloppe, ni
  fiscalité (ESMA, p. 19, note 28).
- **Aucun des quatre critères ne dit lequel prendre**, et la grille ne pointe pas vers un type de
  produit : passif hors ETF (0,22 %) et ETF (0,21 %) sont à un centième l'un de l'autre.
- **« Donc le moins cher gagne » est FAUX** et interdit : la réplication et l'encours comptent.
- **On n'a pas de statut CIF**, et sur cet épisode **rien à vendre**.

### 8.5 — 🗣️ COMMENT CES CHIFFRES SE DISENT (règles d'énonciation, Gardien 06/08)

| Chiffre | ❌ Interdit | ✅ Autorisé |
|---|---|---|
| **25,94 %** (30 ans) | « les frais te coûtent 25,94 % de ton capital » — et même « …de ton capital » tout court : le dénominateur n'est pas ce que tu as versé | « entre ces deux moyennes de catégories, l'écart de frais représente 25,94 % **du capital qu'on aurait sans aucun frais** à 30 ans, à performance brute identique » |
| **32,06 %** (part mangée) | « 32 % du capital partis en frais » | À manier avec la plus grande prudence : il se mesure contre **un fonds à frais nuls, qui n'existe pas**. *(Le champ JSON porte désormais cet avertissement dans son propre nom.)* |
| **1,28 % / 0,21 %** | « ce que TU paies » | « ce que publie le régulateur, **tous investisseurs confondus** » — la table agrège particuliers ET institutionnels |
| **19 749 €** (30 ans, 7 %) | En miniature ou en titre seul | Uniquement dans le même plan que l'hypothèse de rendement affichée |

**Trois conditions cumulatives pour tout chiffre à l'écran** : (1) jamais présenté comme le coût
des frais, toujours comme un **écart entre deux moyennes de catégories** ; (2) la phrase LR4
cond.1 **dans le même plan**, pas vingt secondes plus tard ; (3) **ni dans le titre, ni sur la
miniature sans son dénominateur**. *Le CTR à 1,0 % est exactement la pression qui produira cette
miniature-là.*

---

## 9. ⚖️ VERDICT DU GARDIEN CONFORMITÉ SUR LA v2 (06/08/2026)

> ### **GO SOUS CONDITIONS — à deux étages**
> **Écriture autorisée** (angle, critères, script, panel). **Production gelée** : aucune carte,
> aucune voix, aucun montage, aucun upload tant que les bloquants ne sont pas tombés.
> *« Si la réponse à l'un des bloquants est "on verra au montage", le verdict redevient STOP. »*

**Sur la question centrale — MAR ? CIF ?** → **Non aux deux.** CIF suppose une recommandation
*personnalisée* + un instrument *déterminé* : une vidéo diffusée à tous n'en coche aucune tant que
LR1 et LR1 bis tiennent. MAR suppose une information sur *un instrument ou un émetteur* : « gestion
active » et « ETF » sont un mode de gestion et une enveloppe, ni l'un ni l'autre. **Mais le
bouclier, c'est LR1 bis — pas l'argument du §0, qui a été retiré.**

### Traitement des 6 bloquants

| # | Bloquant | État |
|---|---|---|
| **B1** | La phrase LR4 cond.1 n'avait **aucune gate** entre le JSON et l'écran ; le protocole disait « republiée dans le JSON **donc** à l'écran » — une inférence, pas un contrôle | ✅ **LEVÉ.** `gate_conformite_ep3.py --exige-json` : les avertissements et mentions du moteur deviennent des **présences obligatoires**, absence = STOP. La gate sait enfin détecter un obligatoire ABSENT, pas seulement un interdit présent. |
| **B2** | `compliance-finance.md` introuvable | ✅ **FAUX POSITIF — mais l'alerte était juste.** Le fichier existe (98 lignes, lignes rouges CIF et MAR, liste noire, MAJ AI Act du 05/08) à `<dossier local des regles du studio>`. Le Gardien l'a cherché **en relatif** depuis le dossier de prod, où ce chemin n'existe pas. `CLAUDE.md` corrigé en **chemin absolu** : une règle qu'un relecteur ne trouve pas ne protège personne. |
| **B3** | Réponse-type commentaires inexistante | ✅ **LEVÉ.** `REPONSES_TYPE_COMMENTAIRES_ep3.md` — 9 réponses figées, 3 cas de suppression, règle des 72 h. |
| **B4** | La définition désignait la p. 6 comme table principale, le relevé n'a lu que la p. 18 : **la définition suivait le relevé au lieu de le contraindre** | ✅ **LEVÉ.** `DEFINITION_FRAIS_ep3.md` §3 amendé et daté : MR-CP.14 p. 18 devient la table **principale**, pour une raison indépendante des valeurs (seule table distinguant les trois modes de gestion). |
| **B5** | Tie-break alphabétique : à égalité, la borne basse tombait **toujours** sur l'ETF | ✅ **LEVÉ.** Le relevé lève `ReleveImpossible` sur une égalité et exige un arbitrage écrit. Test dédié sur le cas réel (ligne 2023 : passif et ETF à 0,22 %). |
| **B6** | Le relevé devinait la **sémantique des colonnes** (mapping par position) | ✅ **LEVÉ.** L'en-tête « Active funds · Passive funds · ETFs » + « 1Y 10Y » ×3 est **lu et vérifié** avant toute extraction. *(Trouvé en parallèle par la relecture de code : sur un ordre inversé, le script sortait 0,21 % étiqueté « gestion active », en FEU VERT.)* |

### Points IMPORTANT traités

**I1** ✅ La gate ratait « BNP Paribas Easy », « Global X », « First Trust », « Carmignac », et
**tous les tickers alphanumériques** (CW8, PE500). Corrigé, et **le fichier piégé a été enrichi des
cas qu'elle ratait — écrits rouges d'abord, gate corrigée ensuite**, jamais l'inverse.
**I2** ✅ Un livrable nommé `..._REGLES_....json` était ignoré et la gate rendait FEU VERT sans
rien lire : elle rend désormais **2**. *« Rien contrôlé » n'est pas « tout va bien ».*
**I3** ✅ Les chiffres agrègent **retail et institutionnel** : porté au §8.5 et dans la définition,
« ce que tu paies » est interdit.
**I4** ✅ Les performances nettes de la même page sont **déclarées hors périmètre**, avec la raison
(la mesure figée est un coût ; comparer des performances de catégories serait bien plus près de la
ligne rouge). Nouveau §7 de `DEFINITION_FRAIS_ep3.md`.
**I5** ✅ **TRANCHÉ (Aleksandar, 06/08) : ON MONTRE LA TABLE MR-CP.14 avec son sous-titre**,
attribué explicitement — guillemets + source à l'écran + à la voix « c'est le régulateur qui
l'écrit, pas nous » — et la **phrase LR4 cond.1 dans le même plan**.

> 🔤 **LE TEXTE EXACT, à recopier — pas à retaper** (fact-check du 06/08) :
> **`Passive funds are on average about 60–80% cheaper than active funds`**
> Tiret **demi-cadratin** (–), et **pas d'espace avant le %**. Une citation attribuée à un
> régulateur et affichée entre guillemets se recopie au caractère près. Même exigence pour les
> citations p. 14 et p. 19 si elles passent en carte.
>
> ⚠️ **Ce que le fact-check a vu et qui n'était pas dans la décision** : ce sous-titre **ne décrit
> pas nos deux chiffres**. Sur 0,21 contre 1,28, l'écart est de **83,6 %** — **hors de la
> fourchette « 60–80 % »** annoncée, qui couvre l'ensemble actions + obligations à 1 an et 10 ans.
> Si le plan montre la table **et** nos deux chiffres, un spectateur qui divise trouve 84 % et
> croit tenir une contradiction. **À traiter dans le script, pas au montage** : soit la voix dit
> que la fourchette de l'ESMA couvre un périmètre plus large que nos deux lignes, soit les deux
> chiffres n'apparaissent pas dans le même plan que le sous-titre. **C'est un point pour le panel.**
**I6** ✅ **LEVÉ (GO Aleksandar, 06/08) — `gate_broll_ep3.py`, 42 tests verts.** Elle contrôle le
**TEXTE qui fabrique les images** (requête stock, prompt de génération), pas les images : un plan
interdit qu'on ne télécharge jamais ne peut pas se retrouver au montage. Elle est **branchée dans
`fetch_broll.py`** : une requête interdite ne part pas au réseau.
Elle STOPpe sur : écran de cotation, tableau de tickers, interface de trading ou de courtier,
graphique de prix ou chiffré, place boursière identifiable, marque financière nommée, et sur les
mots `ETF` / `tracker` / `fonds indiciel` dans une requête d'image.
Elle applique aussi le **NON DÉCOUPABLE** au Short : la **réplication** y est interdite (40 s en
font une opinion sur la sûreté d'un montage), et un **chiffre d'impact ne part pas seul** — il
exige, dans le même Short, la phrase des catégories ET « hypothèse d'école ».
*Cas fondateur : `fetch_broll.py` documentait en exemple d'usage `--query "stock market ticker"`,
littéralement le plan que l'épisode interdit.*
**I7** 🔴 **VÉRIFIÉ — ET ÇA REMONTE EN BLOQUANT (B7).** Le Gardien avait écrit : *« si l'ebook
contient un chapitre sur les ETF ou les frais, l'isolation d'un seul épisode ne vaut rien »*.

**C'est le cas.** `ebook_finance_ia_sans_jargon_DRAFT.md`, **chapitre 4 — « Les deux ennemis
silencieux : les frais et l'inflation »**, et le HTML en vente porte le même texte.

Trois problèmes, du plus grave au moins grave :

1. 🚨 **ANTI-FICTION — deux fourchettes de frais NON SOURCÉES.** L'ebook écrit : *« Un fonds
   activement géré facture typiquement autour de **1,5 à 2 %** par an. Un fonds indiciel (ETF)
   […] souvent autour de **0,2 à 0,3 %** »*, en ajoutant « ces fourchettes sont publiques » —
   **sans dire d'où elles viennent, ni de quelle catégorie, ni à quelle date**. C'est exactement
   le « de mémoire » que LR3 interdit, dans un produit payant en ligne depuis le 04/07. Le motif
   se suffit à lui-même : un chiffre qu'on ne peut pas retrouver ne se publie pas.

   > 🧾 **CORRECTION TRACÉE — 06/08/2026, fact-check.** Une version antérieure de ce point
   > ajoutait que ces fourchettes étaient **« fausses au regard de notre propre relevé »** et que
   > la borne haute était **« surestimée d'environ 50 % »**. **C'était une affirmation que la
   > source ne porte pas**, et elle comparait des périmètres différents : notre 1,28 % vient de
   > MR-CP.14, qui agrège **retail ET institutionnel** ; la table *retail* (MR-CP.4, p. 12) donne
   > **1,32 % à 1 an et 1,46 % à 10 ans** ; et le rapport écrit lui-même, **p. 15** : *« In the
   > equity segment, the average ongoing costs range between 0.5% and 2% across strategies »* —
   > sans compter les domiciles où le TER moyen approche 2 % (MR-CP.23, p. 22). Une fourchette
   > « 1,5 à 2 % » pour de l'actif actions vendu au détail **n'est donc pas démontrée fausse par
   > ce document**.
   >
   > **C'est la leçon du 05/08 rejouée, et par moi** : *« un chiffre exact peut mentir par son
   > qualificatif »*. Les chiffres cités étaient bons, le mot « fausses » ne l'était pas — je l'ai
   > écrit sans l'avoir mesuré. Le grief tenable, et le seul, est **l'absence de source**.
2. ⚖️ **LR5 vidée de son sens.** Isoler l'ép. 3 de l'ebook ne sert à rien si l'ebook vend le même
   sujet : le spectateur atterrit sur une chaîne dont 4 vidéos renvoient vers un produit payant
   qui traite des frais. C'est précisément ce que vise l'ESMA de janv. 2026 sur le contenu
   pédagogique menant à une offre.
3. 📌 **Une injonction** : *« les frais sont la seule variable que tu contrôles à 100 %.
   **Traque-les.** »* — un impératif, dans un produit payant, sur un sujet réglementé.

**Ce que ça n'est pas** : un problème créé par l'ép. 3. L'ebook est en vente depuis le 04/07 avec
ces chiffres. L'épisode ne fait que le mettre en pleine lumière — et il le mettrait devant une
audience nouvelle, sur le sujet exact, au moment le plus exposé de la chaîne.

**⏳ ARBITRAGE ALEKSANDAR REQUIS** (trois options, dans l'ordre de ma recommandation) :
**(a)** corriger le chapitre 4 avec les chiffres sourcés du relevé + retirer l'impératif, et
republier l'ebook **avant** l'ép. 3 — c'est aussi une amélioration du produit ;
**(b)** retirer les fourchettes chiffrées du chapitre 4 sans les remplacer (le raisonnement tient
sans elles) ;
**(c)** décaler l'ép. 3 après la correction. **Ne rien faire n'est pas une option** : le problème
n°1 est anti-fiction, pas conformité, et il existe déjà indépendamment de l'épisode.

## 10. ⏭️ CE QU'IL RESTE À FAIRE

1. ⏳ **Tes trois arbitrages** : l'angle (§1), les 4 critères (§2), et le **ratio de durée** que
   le Gardien exige — *« combien de minutes sur la lecture du document, contre combien sur la
   grille d'impact ; si la grille dépasse le tiers de la durée, l'angle est un habillage et je
   re-STOPpe au panel »*.
2. ⏳ I5 (montrer ou non la table), I6 (gate B-roll/Short), I7 (contenu de l'ebook).
3. ⏳ `fact-check` sur les chiffres du §8 avant toute carte.
4. ⏳ Script → panel de 7 + Statisticien.
