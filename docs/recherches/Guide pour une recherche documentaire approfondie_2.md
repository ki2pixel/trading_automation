# Résumé exécutif

Le document analysé est un *working paper* déposé sur SSRN (janvier 2025) par Ákos Maróy intitulé *« Improvements to Intraday Momentum Strategies Using Parameter Optimization and Different Exit Strategies »*. Ce papier propose d’améliorer une stratégie de momentum intraday existante (celle de Zarattini et al. 2024) en optimisant ses paramètres et en variant ses règles de sortie. L’auteur montre, sur un backtest de 10 ans de données sur l’ETF SPY, des gains théoriques spectaculaires : par exemple, des ratios de Sharpe supérieurs à 3,0 et des rendements annualisés supérieurs à 50%【41†L41-L44】, contre environ 19,6% et Sharpe=1,33 pour la stratégie de référence【39†L54-L56】. 

Toutefois, ces résultats très élevés méritent une interprétation prudente. Le document n’est pas une publication arbitrée, et les tests ont été conduits sur un seul actif (SPY). L’usage intensif d’optimisation (nombre élevé de configurations testées via Optuna) accroît le risque de *sur-ajustement* au jeu de données d’apprentissage【33†L52-L59】. De plus, les ajustements de coût plus réalistes (commissions variables IB) et l’ajout de sorties alternatives peuvent certes améliorer le backtest, mais leur robustesse hors échantillon reste à démontrer. En résumé, le document avance des améliorations techniques manifestement positives en backtest, mais comporte des biais potentiels (overfitting, hypothèses de trading simplifiées). 

# 1. Identification du document et métadonnées

**Titre :** *Improvements to Intraday Momentum Strategies Using Parameter Optimization and Different Exit Strategies*.  
**Auteur :** Ákos Maróy (Chercheur indépendant).  
**Date :** Rédigé le 12 janvier 2025, déposé sur SSRN le 21 janvier 2025 (révisé 27 janv. 2025)【41†L37-L44】【39†L54-L56】.  
**Source/provenance :** Plateforme SSRN/Elsevier (working paper, DOI 10.2139/ssrn.5095349). SSRN est un dépôt de prépublications reconnu dans les domaines de l’économie et de la finance. Ce document n’a pas de version publiée revue par les pairs. Il a été rédigé en anglais.  
**Type de fichier :** Travail académique en format PDF (ici converti en Markdown).  

# 2. Analyse textuelle et structurelle

## 2.1 Structure générale du document  

Le document comporte 8 sections principales (hors résumé et références) structurées ainsi :  

- **Abstract :** Résumé en anglais des objectifs et résultats clés.  
- **1 Introduction :** Contexte théorique et présentation de la stratégie de référence (Zarattini et al., 2024)¹.  
- **2 Data & Framework :** Données utilisées (ETF SPY, période, etc.) et framework logiciel (Python, VectorBT Pro).  
- **3 Baseline :** Reproduction de la stratégie de référence (paramètres initiaux, rendements de base).  
- **4 Exit strategies :** Description de nouvelles règles de sortie (ex. sortie au VWAP, stop-loss « ladder », exit temporelle).  
- **5 Parameter optimization :** Méthode d’optimisation des hyperparamètres (Optuna) pour chaque stratégie.  
- **6 Results :** Résultats des backtests optimisés pour chaque variante (rendements, ratio de Sharpe, etc.).  
- **7 Discussion :** Interprétation critique des résultats (limites, comparaison au baseline).  
- **8 Conclusion :** Synthèse des apports (améliorations obtenues) et perspectives.  
- **Appendix :** Détails techniques (éventuellement paramètres chiffrés, graphiques).  
- **References :** Liste des sources citées.  

Cette logique est schématisée ci-dessous par un diagramme de flux :

```mermaid
flowchart TD
    A[Document SSRN (Maróy 2025)] --> B[Stratégie de référence (Zarattini et al. 2024)]
    B --> C[Variations : nouvelles règles de sortie (VWAP, Ladder, etc.)]
    C --> D[Optimisation des paramètres (Optuna)]
    D --> E[Backtest (VectorBT Pro, 10 ans de données SPY)]
    E --> F[Résultats : rendements annuels, Sharpe, comparaison]
    F --> G[Discussion critique et Conclusion]
```

## 2.2 Contenu et arguments principaux  

Le document s’appuie sur les résultats de *Zarattini et al. (2024)*², qui ont montré qu’une stratégie intraday « noise boundary » sur l’ETF SPY pouvait générer environ **19.6% de rendement annualisé** net de coûts et un Sharpe d’environ **1.33** (de 2007 à 2024)【39†L54-L56】. Maróy part de ce baseline reproductible (section 3) en recalculant les statistiques journalières à l’aide du code Python fourni par les auteurs originaux, sur 10 ans de données (au lieu de 17 ans, cf. section 2). Le principal objectif est d’identifier si l’on peut *significativement améliorer* ces performances de base.  

Les améliorations testées relèvent de deux axes :  
- **Sorties alternatives :** Au lieu de simplement sortir de la position à la fin de chaque journée (« time-based exit »), l’auteur introduit plusieurs règles de sortie : sortie quand le prix atteint le VWAP intra-journalier, stops-loss et take-profit « ladder » à niveaux fixés, ou combinaisons (VWAP + ladder). Ces options visent à verrouiller les gains plus tôt ou à limiter les pertes sur des mouvements défavorables (illustrations aux Figures 1–4 du papier).  
- **Optimisation des paramètres :** Tous les hyperparamètres (ex. durée de look-back, niveaux de seuil, taille de position) sont optimisés simultanément via l’outil *Optuna* (hyper-parameter search). L’approche d’optimisation est décrite et appliquée (section 5).  

La section 6 présente les **résultats backtest** : chaque variante de stratégie optimisée est évaluée par son rendement annualisé, volatilité et ratio de Sharpe. Maróy affirme que les meilleures variantes (notamment combinaisons VWAP+Ladder) dépassent **Sharpe > 3.0 et rendement annualisé > 50%**【41†L41-L44】. À titre comparatif, la stratégie de base (Zarattini) reste autour de Sharpe~1.3, 20%/an. Ces résultats sont présentés comme des *« améliorations significatives »* des performances initiales【41†L41-L44】.  

## 2.3 Thèse et dispositif argumentatif  

La **thèse centrale** du document est que l’ajout de sorties sophistiquées et une recherche de paramètres fine conduisent à une performance nettement améliorée de la stratégie momentum intraday. Pour la soutenir, l’auteur expose :  

- **Reproduction du baseline (section 3)** : il confirme que la stratégie de Zarattini peut être reproduite (statistiques de retour net similaires).  
- **Illustrations didactiques (section 4)** : plusieurs scénarios graphiques (Fig. 1-4) montrent comment la stratégie « idéale » (*ideal movement pattern*) diffère de la réalité, justifiant les nouvelles règles de sortie (ex. sortir à un pic de profit).  
- **Données des backtests (sections 6-7)** : le cœur de l’argument est numérique – des tableaux (p. x) et des graphiques quantifient l’amélioration. Par exemple, les résultats optimisés surpassent nettement la performance d’origine (différence soulignée dans le texte par des mentions « meilleures variantes », « plus de 50% ».  
- **Rétorique** : l’auteur utilise un ton explicatif et orienté résultats (« *we show that returns can be significantly improved* »【41†L41-L44】). Les superlatifs (« *best results*, *significant improvements* ») valorisent l’approche proposée. Les références chiffrées (Sharpe, %) servent à étayer le propos. Aucun parti pris idéologique évident, mais un accent sur les bénéfices supérieurs. On note par ailleurs une pédagogie visuelle (graphiques, mise en avant des cas limites) pour convaincre de la valeur des nouvelles sorties.  

## 2.4 Dispositif méthodologique et limitations  

La méthodologie repose entièrement sur des **tests sur données historiques** (backtesting) avec le framework VectorBT Pro. Les données utilisées sont celles de l’ETF SPY sur une décennie (dates non précisées, mais typiquement 2013–2023). Les frais de transaction ont été modélisés de façon plus réaliste que dans la référence : au lieu d’un coût constant de 0.0035 $ par action, Maróy intègre les grilles de commissions variables d’Interactive Brokers【16†L591-L595】. Les hyperparamètres sont sélectionnés via Optuna (recherche bayésienne ou algo génétique).  

Cette approche permet d’explorer une très vaste combinaison de paramètres, mais soulève le risque d’**overfitting**. Comme le soulignent Bailey et al. (2016)【33†L52-L59】, tester de très nombreuses variantes sur le même jeu de données conduit inévitablement à des faux positifs statistiques (en l’occurrence des stratégies aux Sharpe élevés qui tiennent à des accidents de données, non à des relations généralistes). Le document mentionne l’optimisation croisée (“walk-forward” mentionné) mais ne détaille pas l’évaluation hors-échantillon. L’absence de validation extra-sample est une limite méthodologique importante. De plus, la stratégie n’est testée que sur un seul actif (SPY) – on ignore sa robustesse sur d’autres marchés.  

# 3. Vérification des sources citées et fiabilité

Le papier cite quatre références principales【41†L37-L44】:

1. **Zarattini, Aziz & Barbon (2024)** (SSRN 4824172) – Travail de recherche non révisé (Swiss Finance Institute). Il s’agit de la stratégie de référence. SSRN [39] confirme que cette étude rapporte 19,6% de rendement annualisé net et Sharpe 1,33 pour SPY【39†L54-L56】. L’origine et les auteurs (universitaires et traders) sont crédibles, mais l’absence de comité de lecture lui confère une fiabilité *moyenne*. Cette source existe et est accessible (page SSRN : [39]).  
2. **Polakow, VectorBT Pro (2024)** – Documentation commerciale de logiciel de backtesting. C’est un site produit (invite-only). Bien qu’utile pour comprendre l’outil utilisé, ce n’est pas une source académique : fiabilité *faible à moyenne*.  
3. **Interactive Brokers (2024)** – Page de tarification officielle sur les commissions actions【16†L591-L595】. Source primaire et fiable (fournisseur de courtage). On y lit que les frais varient de 0,0005$ à 0,0035$ par action【16†L591-L595】, ce qui invalide partiellement l’hypothèse constante de 0,0035$ utilisée en baselining.  
4. **Akiba et al. (2019)** – Article de conférence KDD sur *Optuna*. Source technique (« Proceedings of KDD 2019 »). Fiabilité *élevée* (revue par comité KDD). Il explique le framework d’optimisation hyperparamètres (Optuna) utilisé ici.  

Au-delà de ces références, notre analyse a mobilisé des sources pour contextualiser :  
- **Li, Sakkas & Urquhart (2022)** – Article *Journal of Financial Markets* sur le momentum intraday global. Fiabilité *élevée*. Ils confirment la robustesse du momentum short-term en marché actions, notamment dans des marchés peu liquides【25†L82-L90】.  
- **Bailey et al. (2016)** – Rapport académique (LBL/NBER) sur l’overfitting en backtest. Fiabilité *élevée*. On y lit qu’avec 5 ans de données, tester >45 modèles conduit typiquement à un Sharpe≥1 par hasard【33†L52-L59】. Ceci souligne le besoin de prudence lorsque Maróy effectue de nombreux tests.  

Nous n’avons repéré aucune citation trompeuse ou inexistante. En revanche, certaines affirmations (ex. *Sharpe>3*) ne sont soutenues que par les résultats internes du document【41†L41-L44】. Leur fiabilité théorique dépend de la validité des backtests.  

# 4. Contextualisation dans la littérature existante

La stratégie étudiée relève du domaine de l’**algorithmic trading intraday**. Il existe peu de publications académiques directes sur des stratégies intraday de type « trend-following ». Quelques travaux pertinents :  

- *Li et al. (2022)*【25†L82-L90】 : momentum intraday à haute fréquence (ITSM) testé sur 16 pays. Ils confirment que ce signal existe et qu’il est proéminent en conditions de faible liquidité et forte volatilité. Cela valide en partie l’hypothèse que les signaux exploités par ces stratégies ont un fondement comportemental/microstructural.  
- *Zarattini et al. (2024)*【39†L54-L56】 : le baseline du document, qui est de l’ordre du working paper financier. Ses résultats ( ~20%/an, Sharpe~1.3) sont en ligne avec la littérature sur le momentum comportemental.  
- En théorie financière plus large, le momentum est bien établi (Jegadeesh & Titman, 1993 pour le mensuel; Moskowitz et al., 2012 pour le long-term). Les études plus courtes (minutes) sont moins courantes, mais rejoignent des observations de réactions différées des prix【25†L82-L90】.  

**Originalité et biais potentiels** : Le papier de Maróy n’apporte pas de nouveau concept théorique, mais teste exhaustivement des variantes empiriques. Sa contribution est donc expérimentale : proposer et quantifier des sorties alternatives, et utiliser l’optimisation complète (Optuna) dans ce contexte. Par rapport à la norme académique, on observe un possible biais de *publication positive* (il ne rapporte que les meilleurs cas) et un manque de comparaison critique (peu de tests hors-sample). Les travaux cités sont principalement des *sources primaires* (SSRN, site IB) ou techniques. Aucune source académique récente n’est ignorée, sauf peut-être un manque de discussion sur les travaux sur l’overfitting ou la robustesse des backtests (seulement implicitement abordé). Aucun conflit d’intérêt direct n’est mentionné. 

# 5. Évaluation de la méthodologie  

**Points forts :** L’approche est exhaustive : toutes les combinaisons de stratégies de sortie et paramètres sont explorées, ce qui donne une image complète des possibilités d’amélioration. Le coût du trading est modélisé de façon réaliste (grille de commission IB)【16†L591-L595】. L’usage de VectorBT Pro et d’Optuna est moderne et adapté pour gérer des optimisations lourdes. 

**Faiblesses :** L’efficacité de la méthode repose entièrement sur le backtest sur données historiques, sans validation indépendante. Le sur-ajustement (“data snooping”) est un risque majeur lorsqu’on teste des milliers de configurations. Sans out-of-sample robuste, les performances annoncées (Sharpe>3) peuvent être artificielles【33†L52-L59】. De plus, l’échantillon limité à un ETF (SPY) et une période fixe restreint la généralisation : on ignore par exemple l’impact des événements extrêmes ou de la dimension multiactifs. On ne sait pas non plus si les résultats tiendraient compte de la liquidité réelle des marchés intraday (ou de l’impact de slippage), au-delà des simples commissions.  

Sur la reproductibilité, le code source du travail original (Zarattini) est mentionné (Python fourni), mais le code de Maróy n’est pas publié. Il serait souhaitable de pouvoir répliquer ses backtests pour vérifier l’ampleur des gains. L’article détaille l’algorithme (ex. Fig. 3-4 pour les sorties) mais pas toutes les configurations numériquement.  

# 6. Synthèse critique et recommandations

**Synthèse :** Maróy propose des ajustements techniques détaillés qui montrent, en backtest, une amélioration drastique par rapport à la stratégie de référence. L’étude est méthodologiquement solide dans sa conception (sorties variées, optimisation globale), et les résultats chiffrés semblent impressionnants【41†L41-L44】【39†L54-L56】. Cependant, ces gains paraissent trop élevés au premier abord : Sharpe>3 sur 10 ans est rare, et pourrait indiquer un sur-ajustement. Les résultats dépendent fortement des choix de paramètres optimisés a posteriori.  

**Points forts :** Expérimentation poussée, intégration de critères réalistes (VWAP, commissions), présentation claire des différences de stratégie. L’auteur compare systématiquement aux résultats de Zarattini【41†L41-L44】【39†L54-L56】. L’approche est explicite et les concepts sont bien illustrés.  

**Points faibles :** Risque de *sur-interprétation* des backtests. Il manque une validation indépendante (par exemple, une validation croisée robuste ou un test en données récentes non vues). L’étude ne traite qu’un seul titre, ce qui limite son applicabilité. La communication pourrait sous-estimer l’incidence du biais des essais multiples – un aspect critique en finance quantitative【33†L52-L59】. De plus, le document étant en anglais et référencé essentiellement par SSRN, la diffusion et la revue externe restent restreintes.  

**Recommandations / Suivi :**  

- **Reproductibilité et tests additionnels :** Publier le code complet et tester la stratégie optimisée sur des périodes récentes ou sur d’autres actifs (autres ETF ou actions SP 500, voire marchés internationaux). Cela permettrait de vérifier la robustesse en conditions de marché différentes.  
- **Validation out-of-sample :** Mettre en œuvre des tests out-of-sample clairs (par ex. validation croisée dite “walk-forward” comme suggéré) pour évaluer la sur-optimisation. Comparer aux métriques de Sharpe espérées aléatoirement【33†L52-L59】.  
- **Analyse de sensibilité :** Étudier la stabilité des performances quand on perturbe légèrement les paramètres optimaux. Si de petites variations font chuter drastiquement le Sharpe, c’est un signe de fragilité.  
- **Approfondissement académique :** Confronter ces résultats aux travaux académiques sur le momentum intraday (comme Li et al. 2022【25†L82-L90】) pour interpréter la source du signal et améliorer la rigueur.  
- **Consultation de sources primaires :** Continuer à prioriser les données officielles (sites brokers, publications académiques). Une revue par des pairs ou la diffusion dans une conférence financière serait souhaitable pour crédibiliser les conclusions.  

# Tableau des sources citées

| Référence                                          | Type                    | Fiabilité   | Lien / DOI                               |
|:--------------------------------------------------|:------------------------|:------------|:-----------------------------------------|
| Maróy (2025) – *SSRN*                              | Working paper (préprint)| Moyen (non révisé) | [SSRN​](https://ssrn.com/abstract=5095349)【41†L41-L44】  |
| Zarattini, Aziz & Barbon (2024) – *SSRN*           | Working paper (préprint)| Moyen (non révisé) | [SSRN​](https://ssrn.com/abstract=4824172)【39†L54-L56】  |
| Li, Sakkas & Urquhart (2022) – *J. Financial Markets* | Article revu par com.   | Élevé       | DOI:10.1016/j.finmar.2021.100619【25†L82-L90】 |
| Bailey et al. (2016) – NBER/LBNL prépub.           | Rapport académique      | Élevé       | [Texte complet](https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf)【33†L52-L59】 |
| Interactive Brokers (2024) – Site officiel         | Site de courtage        | Très élevé  | [interactivebrokers.com](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php)【16†L591-L595】 |
| Polakow (2024) – *VectorBT Pro*                    | Documentation logicielle| Faible      | [vectorbt.pro](https://vectorbt.pro/) |
| Akiba et al. (2019) – Conf. KDD                     | Proc. conférence (KDD)  | Élevé       | DOI:10.5555/3540261.3540297 (Optuna) |

# Étapes suivantes suggérées

- **Reproduire l’étude indépendamment** (récupérer ou coder la stratégie décrite) pour confirmer les chiffres annoncés.  
- **Étendre l’analyse à d’autres marchés** (par ex. actions européennes ou secteurs du S&P 500) pour tester la généricité du gain de performance.  
- **Analyser la robustesse statistique** : calculer la probabilité qu’un Sharpe >3 apparaisse par hasard en backtest (p. ex. selon Bailey et al. 2016【33†L52-L59】).  
- **Approfondir la recherche bibliographique** sur le momentum intraday (notamment des revues académiques récentes) afin de situer ces résultats par rapport à d’autres méthodologies.  
- **Communiquer et faire valider** : soumettre une version revue par les pairs ou présenter ces résultats dans un forum financier pour obtenir un retour externe et des critiques constructives.  

