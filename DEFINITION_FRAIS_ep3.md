# 🔒 DÉFINITION DES FRAIS — FIGÉE AVANT LE RELEVÉ · « Le Test » ép. 3

**Créé le 06/08/2026 · Lève le point n°4 du STOP du Gardien conformité (05/08/2026).**

> **Le point du Gardien, mot pour mot :** *« Définition exacte des frais figée AVANT le relevé :
> quel document, quelle table, quelle page (comme l'ép. 2 l'a fait avec "PWL, Table 7, p. 9").
> TER, coûts totaux ESMA et frais agrégés du DIC/PRIIPs **ne mesurent pas la même chose** — les
> confondre serait la faute "prix vs rendement total" de l'ép. 2, rejouée sur les frais. »*

**Ce document fige QUOI on mesure et OÙ on le lit. Il ne contient AUCUNE valeur** — les valeurs
sortent du relevé, qui vient après, et qui se fait par extraction déterministe du PDF public.

---

## 1. LES TROIS MESURES QUI SE RESSEMBLENT, ET QUI NE SE COMPARENT PAS

Trois chiffres de frais circulent, tous légitimes, tous différents. Les additionner ou les
comparer entre eux produit un résultat arithmétiquement juste et éditorialement faux.

| Mesure | Ce qu'elle contient | Ce qu'elle ne contient PAS |
|---|---|---|
| **A. Frais courants** *(ongoing costs)* | Les coûts **récurrents** supportés par le fonds sur un an, tels que publiés dans le DIC PRIIPs. | Frais d'entrée/sortie · frais de courtage · écart achat-vente payé en Bourse · fiscalité. |
| **B. Frais d'entrée et de sortie** *(one-off costs)* | Souscription et rachat, tels que publiés dans le DIC. | — mais c'est un **maximum autorisé**, pas ce qui est réellement prélevé. |
| **C. Incidence des coûts annuels** *(DIC PRIIPs)* | Coûts ponctuels **amortis sur la durée de détention recommandée** + coûts récurrents + coûts accessoires. | Dépend de l'horizon affiché dans le DIC → **ce n'est pas un taux annuel de frais courants**. |

**A + B ne fait pas C, et C n'est pas une version « complète » de A.** Ce sont trois façons
différentes de découper la même facture.

## 2. LA MESURE RETENUE POUR L'ÉPISODE : **A — les frais courants annuels**

**Clé technique dans le moteur : `ongoing_costs_esma`.**

### Pourquoi celle-là (et la justification est antérieure au relevé)

1. **C'est ESMA lui-même qui met l'accent dessus**, et il écrit pourquoi : *« Given this
   uncertainty about the actual level of entry and exit costs charged to investors […] we've
   decided for now on to put more emphasize on ongoing costs, whose PRIIPs KIDs disclosure
   corresponds to the actual level for the previous year »* — rapport ESMA 2025, **p. 14**,
   encadré **MR-CP.8**. Autrement dit : A est un montant **constaté**, B est un **plafond
   déclaré**. On ne bâtit pas un calcul sur un plafond.
2. **C'est la seule des trois qui est un taux annuel comparable d'un horizon à l'autre.** C, qui
   dépend de la durée de détention recommandée affichée dans le DIC, ne peut pas alimenter une
   grille 10/20/30 ans sans être recalculée — donc sans cesser d'être le chiffre publié.
3. **C'est la seule qui existe pour toutes les catégories** que l'épisode évoque, à la même date
   et dans le même tableau.

### ⚠️ CE QUE CES CHIFFRES NE SONT PAS — « ce que paie un particulier »

La note de MR-CP.14 le dit : *« geometric mean aggregation, **retail and institutional
investors** »*. Les valeurs relevées **mélangent la clientèle particulière et institutionnelle**.
👉 **Interdit en voix off comme à l'écran : « ce que TU paies ».** Formulation autorisée : « ce que
publie le régulateur, tous investisseurs confondus ».

### Ce que cette mesure EXCLUT — à dire à l'écran, pas en note de bas de page

> 🧾 **RETRAIT TRACÉ — 07/08/2026, décision du panel.** Le 06/08, un point **1** avait été ajouté
> ici : *« les coûts de DISTRIBUTION — la plus grosse exclusion »*, chiffrée à **48 % du coût
> total d'un UCITS**, et déclarée prioritaire à l'écran. **Le panel a démontré qu'elle est
> INVERSÉE, et elle est retirée.** Deux erreurs cumulées :
> **(a) le sens.** Les **rétrocessions** (inducements) sont comptées **DANS** les frais courants,
> elles n'en sont pas exclues — le rapport le dit lui-même p. 22 et p. 27 : *« 45% of ongoing
> costs **is paid as** inducements to distributors »*. Ce qui est hors périmètre, ce sont les
> seuls frais que l'investisseur paie **en direct** au distributeur, un poste bien plus étroit.
> Présenter ça comme « la plus grosse exclusion » revenait à retrancher deux fois une charge déjà
> comptée, et donc à **sur-estimer** ce que notre chiffre sous-estime.
> **(b) la source.** Le **48 %** ne vient PAS du rapport que nous relevons : il vient du *ESMA
> Market Report on total costs of investing in UCITS and AIFs*, **novembre 2025** — un autre
> document, un autre périmètre, que nous n'avons pas ouvert. Le citer depuis une note de bas de
> page qui le mentionne, c'est publier un chiffre de seconde main.
>
> **Troisième fois en deux jours que la faute est un rapport de périmètre**, après « bornes de
> catégories différentes » (LR4) et « fausses fourchettes » (ebook). C'est le motif d'erreur
> dominant de cet épisode, et la raison d'être du §4.
> **Les exclusions sont les quatre ci-dessous. Point.**

**1. L'écart achat-vente (bid-ask spread)** — note 28, **p. 19** : *« Trading in ETF also involves
bid–ask spreads, a key component of the total costs paid by an investor to own an ETF. Bid-ask
spreads can make the initial investment more expensive, especially considering that retail
investment is carried out on the secondary market. Due to lack of data availability, this analysis
does not include information on bid-ask spreads. »*
*(La phrase du milieu — celle qui dit que ça renchérit l'investissement du particulier — ne doit
PAS être coupée : elle va dans notre sens.)*

**2. Les frais de courtage payés par l'investisseur sur son propre compte.**
⚠️ **Formulation précise obligatoire** : les **coûts de transaction DU FONDS**, eux, **sont
inclus** dans les frais courants publiés (note 1, p. 4 : *« ongoing management fees, transaction
costs and potential performance fees »*). Dire « ça n'inclut pas les frais de courtage » sans
préciser **lesquels** est faux dans un sens et vrai dans l'autre.

**3. Les frais d'enveloppe** (compte-titres, PEA, assurance-vie).

**4. Toute fiscalité.**

**Conséquence assumée et affichée : le chiffre de l'épisode sous-estime le coût réel supporté par
un particulier.** C'est l'inverse d'un chiffre qui arrange : on le dit, et on dit pourquoi on ne
peut pas faire mieux (la donnée n'existe pas publiquement).

## 3. LE DOCUMENT, LA TABLE, LA PAGE (l'équivalent du « PWL, Table 7, p. 9 » de l'ép. 2)

**Document primaire :**
> **ESMA Market Report — *Costs and Performance of EU Retail Investment Products 2025***
> Référence **ESMA50-1949966494-4065** · publié le **3 mars 2026**
> Période de reporting : **1ᵉʳ janvier 2015 → 31 décembre 2024**
> 🔗 `https://www.esma.europa.eu/sites/default/files/2026-03/ESMA50-1949966494-4065_Market_Report_-_Costs_and_Performance_of_EU_Retail_Investment_Products.pdf`

> 📌 **AMENDEMENT TRACÉ — 06/08/2026, après le STOP du Gardien (bloquant B4).** La v1 de ce §3
> désignait la table **p. 6** comme table principale, et **MR-CP.14 p. 18** comme table de
> comparaison dérogatoire. Or `relever_frais_ep3.py` n'a jamais relevé la p. 6 : il ne lit que la
> p. 18. **La définition ne contraignait donc plus le relevé, elle le suivait** — exactement le
> vice que ce document existe pour empêcher. Le tableau ci-dessous est corrigé : **MR-CP.14 p. 18
> est la table PRINCIPALE**, pour une raison qui ne doit rien aux valeurs qu'elle contient — c'est
> **la seule des quatre qui distingue les trois modes de gestion** (actif / passif hors ETF / ETF),
> donc la seule qui permette de relever plusieurs catégories **dans un même tableau, à une même
> date, avec une même méthode d'agrégation**, ce qu'exige LR4 cond.1. La p. 6, elle, mélange des
> horizons (5 ans) et ne sépare pas passif hors ETF et ETF : elle ne pouvait pas tenir ce rôle.

**Tables autorisées pour le relevé — aucune autre :**

| Table | Page | Ce qu'elle donne | Usage autorisé |
|---|---|---|---|
| **MR-CP.14** — *UCITS costs and net performance by management type* | **p. 18** | Frais courants et performance nette par **type de gestion** : actif / passif hors ETF / ETF, aux horizons 1 an et 10 ans, année par année. | **Table PRINCIPALE du relevé** (amendement du 06/08). Comparaison entre catégories **uniquement** avec la phrase LR4 cond.1. |
| **Essential statistics – UCITS** | **p. 6** | Ongoing charges par classe d'actifs, **fonds non-ETF** et **ETF actions**, horizon 5 ans (2020-2024). | Contrôle de cohérence uniquement. Ne sépare pas passif hors ETF et ETF → ne peut pas fournir une borne. |
| **MR-CP.16** — *Dispersion of passive ongoing costs by asset class* | **p. 19** | **Dispersion** (écart-type) des frais courants des fonds passifs. | Montrer qu'une catégorie n'est pas un point mais un nuage. |
| **MR-CP.4** — *UCITS ongoing costs across periods* | **p. 12** | Frais courants par horizon 1/5/10 ans — ⚠️ **actifs et passifs NON-ETF uniquement**, les ETF en sont exclus. | À ne **jamais** utiliser pour un chiffre présenté comme « ETF ». Piège identifié. |

**Source secondaire admise** (contrôle externe, marché français) : AMF, *Analyse des frais des
fonds de droit français*, Pierre-Emmanuel Darpeix, mai 2024 —
`https://www.amf-france.org/sites/institutionnel/files/private/2024-05/etude-analyse-des-frais_fr_0.pdf`.
Elle **ne peut pas** fournir une borne du calcul (autre source, autre date, autre périmètre → le
moteur refuserait, et il a raison). Elle sert uniquement à **confronter** l'ordre de grandeur
européen au marché français, et l'écart est **signalé, pas expliqué** (protocole de l'ép. 2, §5).

**Référence réglementaire de la mesure C** (citée à l'écran quand on explique le DIC, jamais
utilisée dans le calcul) : règlement délégué **(UE) 2017/653**, modifié par **(UE) 2021/2268** —
présentation des coûts en deux tableaux (coûts au fil du temps · composition des coûts) en
vigueur depuis le **01/01/2023**.

## 4. LA RÈGLE DE COMPARAISON (ce que le code applique déjà)

`simulateur_frais.py` refuse, **sans contournement possible**, de comparer deux niveaux de frais
de définitions différentes → `BornesIncomparables`. Il refuse également deux sources différentes,
deux dates de relevé différentes, et deux **catégories** différentes tant qu'aucune phrase
d'avertissement n'est fournie — cette phrase étant alors **republiée dans la sortie JSON**, donc
obligatoirement à l'écran (LR4 cond.1 : « la carte le dit dans la même phrase »).

Gate : `test_simulateur_frais.py::test_LE_refus_central_deux_definitions_ne_se_comparent_pas` et
`::test_le_refus_central_na_aucun_contournement`. **La prose de ce document ne protège rien ; ces
deux tests, si.**

## 5. TRAÇABILITÉ HONNÊTE DE LA RÉDACTION DE CE DOCUMENT

La règle du studio veut que la définition soit figée **avant** de voir les valeurs. Voici
exactement ce qui s'est passé, pour que personne n'ait à me croire sur parole :

- L'identification du document (titre, référence, date, pagination, titres des tables) a été
  faite par **extraction déterministe** du PDF public avec `pypdf` — pas par un modèle.
- Pendant cette reconnaissance, **la page 6 a été affichée en entier, valeurs comprises.** Elles
  ont donc été vues avant que ce document ne soit écrit. Le nier serait exactement le genre de
  petit arrangement que le protocole interdit.
- **Ce que cela ne change pas** : le choix de la mesure A repose sur deux arguments écrits **dans
  le rapport lui-même** (p. 14 pour « constaté vs plafond », p. 19 pour l'exclusion des spreads),
  vérifiables par n'importe qui, et qui auraient conduit à la même mesure quelles qu'aient été
  les valeurs.
- **Ce que cela impose** : le relevé qui suit est fait **par script**, il enregistre la page et la
  ligne de chaque valeur, et **aucune valeur n'est saisie à la main** — ni ici, ni dans le
  moteur, ni dans les cartes. Le test
  `test_aucune_valeur_de_frais_nest_ecrite_en_dur_dans_le_moteur` le vérifie par l'AST.

## 6. CE QUI FERAIT ÉCHOUER LE RELEVÉ (à surveiller au moment de l'exécuter)

- Prendre un chiffre de **MR-CP.4** (p. 12) en croyant qu'il couvre les ETF : il les exclut.
- Mélanger l'horizon 1 an et l'horizon 5 ans dans la même comparaison.
- Prendre un chiffre **ESG** pour un chiffre « tous fonds » (p. 24, MR-CP.25 : les deux colonnes
  se ressemblent beaucoup).
- Additionner ongoing costs et one-off costs pour faire « le coût total » : interdit, la mesure B
  est un maximum déclaré (p. 14).
- Utiliser un chiffre du chapitre **SRP** (produits structurés, p. 33 et suivantes) : ce n'est pas
  la même famille de produits.
- Relever une ligne de la section **« Net performance »** de la p. 18 : ses lignes d'années ont
  **exactement le même format** que celles des coûts (« 2024 17.0 7.6 21.3 9.3 21.4 9.3 »), et
  elles passeraient pour des frais à 21,4 %. *(Deux garde-fous en code : la section est bornée par
  « Net performance » autant que par « Bond UCITS », et toute valeur hors [0 ; 10] points fait
  STOPper le relevé.)*

## 7. 🚫 CE QUE LA MÊME PAGE PUBLIE ET QUE NOUS NE RELEVONS PAS — déclaré, pas caché

La page 18 publie, **sous** les coûts, les **performances nettes** par mode de gestion (actif /
passif hors ETF / ETF, 1 an et 10 ans). Nous ne les relevons pas, et il faut le dire, parce que le
protocole promet « on publie toutes les valeurs obtenues, jamais une sélection ».

**La raison n'est pas éditoriale, elle est de périmètre** : la mesure figée au §2 est un **coût**.
Une performance n'est pas la même grandeur, ne se relève pas sous la même définition, et surtout —
comparer les performances de deux catégories de fonds nous ferait franchir exactement la ligne que
l'épisode entier est construit pour ne pas franchir. **Un coût est un fait connu à l'avance ; une
performance passée est une promesse implicite.**

⚠️ **Conséquence pour le montage** : si un plan montre la table MR-CP.14 à l'écran, ces lignes de
performance seront visibles, **et le sous-titre que l'ESMA a mis lui-même sur cette table aussi** :
*« Passive funds are on average about 60-80 % cheaper than active funds »*. C'est une conclusion
comparative, sourçable mais que **nous** nous interdisons de formuler. **Décision à prendre avant
le montage, pas pendant** : soit la table est montrée avec cette phrase **attribuée explicitement à
l'ESMA à l'écran** (l'autorité est alors bien le document, ce qui est l'angle même de l'épisode),
soit on ne montre pas la table. *(Point I5 du Gardien, 06/08.)*
