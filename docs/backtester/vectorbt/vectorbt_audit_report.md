# Rapport d'Audit : Intégrer VectorBT dans notre pipeline

**TL;DR** : Un audit complet de la bibliothèque VectorBT face à notre moteur local. Le verdict est sans appel : **VectorBT est fantastique pour explorer rapidement des grilles de paramètres (10 à 100x plus rapide), mais il est incapable de reproduire fidèlement les règles de sécurité et de courtage de nos stratégies complexes.** Nous validons son utilisation en tant qu'outil complémentaire (Pre-Scan, Benchmarking), mais pas comme remplaçant.

---

## 1. Pourquoi cet audit ? Le problème de la vitesse matricielle

Quand on conçoit un système d'optimisation de trading, on se heurte rapidement à la physique de son processeur. Notre moteur principal `backtest_engine` analyse les bougies de cours une par une, de manière séquentielle, pour appliquer fidèlement toutes les règles de ta stratégie (exactement comme le ferait TradingView). C'est la seule façon de garantir une simulation réaliste.

Mais cette fidélité a un coût en temps. Dès que tu veux tester des milliers de combinaisons, ton processeur doit exécuter des millions de boucles.

VectorBT promet de résoudre ce problème de lenteur en modifiant radicalement le paradigme : au lieu de boucler dans le temps, il transforme toutes les bougies et tous les paramètres en matrices géantes et calcule tout en parallèle via du code compile JIT (Numba) ou Rust.

Nous avons voulu mesurer l'écart de performance et surtout, vérifier si les résultats restaient fidèles à la réalité économique de nos portefeuilles.

---

## 2. Le choc des réalités : Le test du Strategy Bridge

Pour mesurer la fidélité de VectorBT face à notre moteur de référence, nous avons écrit un prototype de liaison (`strategy_bridge.py`) et lancé la même stratégie HMA Crossover sur l'action `AMS.MC` (sur un échantillon historique de 5 000 bougies de 5 minutes).

Voici les résultats observés sur la même période :

| Indicateur de performance | Moteur principal (`backtest_engine`) | Mode vectorisé (`from_signals` de VectorBT) | Écart constaté |
|---|---|---|---|
| Nombre de trades exécutés | **4** | **137** | +133 trades |
| Profit net final (PnL) | **-49.36** | **+64.08** | +229.8% (irréaliste) |
| Perte maximale (Max Drawdown) | **-8.59%** | **0.0%** | Écart total |
| Ratio de Sharpe obtenu | **-4.20** | **+3.64** | Écart total |

### Pourquoi une telle différence de résultats ?
L'écart est colossal. En creusant dans les logs de simulation, nous avons identifié la cause de cette anomalie :
- **Le moteur principal applique des filtres stricts** : il respecte les limites de prix d'entrée maximales, la taille du bucket de capital alloué, les commissions asymétriques à l'achat et à la vente, et surtout les stops de sécurité ( safety stops combinant la perte maximale nette et le nombre maximal de bougies dans un trade). Ces filtres éliminent naturellement la majorité des mauvais signaux.
- **Le mode rapide de VectorBT ignore tout cela** : la fonction simple `from_signals` de VectorBT se contente d'acheter et de vendre aveuglément à chaque croisement de courbe sans appliquer tes règles de risque. Elle produit un résultat flatteur mais totalement déconnecté de la réalité de ton portefeuille.

Pour que VectorBT obtienne la même précision, il faudrait réécrire l'intégralité de la logique de notre broker en langage de bas niveau compilé JIT pour Numba (via des fonctions de rappel `from_order_func`). Cette tâche serait extrêmement complexe, longue à maintenir et annulerait le gain de vitesse recherché.

---

## 3. Nos choix d'intégration : Le meilleur des deux mondes

Puisque VectorBT ne peut pas remplacer notre simulateur principal, nous avons choisi de l'intégrer là où il excelle : en tant qu'outil d'accélération complémentaire.

### A. Le pré-filtrage de grille (Pre-Scan)
Avant de lancer une optimisation bayésienne fine avec notre moteur principal (qui prend quelques minutes), nous utilisons VectorBT pour réaliser un balayage rapide de la grille de paramètres sur une version ultra-simplifiée de la stratégie. 

VectorBT élimine instantanément les 90% de paramètres aberrants en quelques secondes. Notre optimizer Optuna peut ensuite concentrer ses calculs fins sur le top 10% des zones les plus rentables. 

### B. Le Benchmark statistique aléatoire (Random Benchmarking)
Pour valider qu'une stratégie optimisée possède un réel avantage mathématique sur le marché, nous utilisons le générateur de signaux aléatoires de VectorBT pour simuler des centaines de portefeuilles fictifs au hasard. C'est l'outil parfait pour calculer le score de Sharpe dégonflé (DSR) à toute vitesse.

### C. La cartographie interactive (Heatmaps Plotly)
Nous exploitons le moteur graphique de VectorBT pour générer des cartes de chaleur en 2D interactives à la fin de nos optimisations locales, permettant d'identifier visuellement les sweet spots de paramètres.
