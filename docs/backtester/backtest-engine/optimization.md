# Optimiser tes stratégies : Grid Search vs Bayésien

**TL;DR** : L'optimizer local te permet d'explorer automatiquement des milliers de combinaisons de paramètres. Choisis la Grid Search pour tester une grille exhaustive de manière mathématique, ou la recherche Bayésienne (Optuna) pour trouver intelligemment les réglages optimaux en 10 fois moins d'essais.

Tu as développé ta stratégie et validé son code. Mais maintenant, tu te retrouves face à un problème vertigineux : comment trouver les réglages parfaits ? Ta longueur de moyenne mobile doit-elle être de 12, de 15, ou de 27 ? Est-ce que ton Stop Loss net doit être placé à 1.5% ou à 2% ? 

Essayer chaque combinaison manuellement est une perte de temps absurde. Tu as besoin d'un outil qui explore ces possibilités à ta place. Mais une question se pose rapidement : quelle méthode de recherche dois-tu choisir pour ton cas d'usage ?

Voici comment notre outil d'optimisation locale fonctionne et comment faire ton choix.

---

## 1. Grid Search (Recherche par Grille) : L'exhaustivité absolue

La **Grid Search** est la méthode la plus simple et la plus brute. Tu lui définis des plages précises (par exemple, tester toutes les longueurs de HMA rapide de 5 à 30 par pas de 5, et de HMA lente de 20 à 100 par pas de 10). Le moteur va alors calculer absolument toutes les combinaisons possibles sans exception.

### Quand l'utiliser ?
- Quand ton espace de recherche est petit (moins de 1 000 combinaisons au total).
- Quand tu veux cartographier scientifiquement l'ensemble des résultats pour comprendre comment ta stratégie réagit à chaque variation (utile pour générer des heatmaps).

### Lancer un test à blanc (Dry Run)
Avant de lancer des heures de calcul sur ton processeur, valide le nombre de combinaisons canoniques que ta commande va générer :

```bash
python3 -m backtest_engine optimize \
  --strategy hma_crossover \
  --symbol GMAB \
  --timeframe 15 \
  --param fast_len=5:30:5 \
  --param slow_len=20:100:10 \
  --param 'trade_direction_mode=Long only|Long & Short' \
  --score total_net_pnl \
  --dry-run
```

### Lancer l'exécution réelle
Pour lancer le calcul sur plusieurs cœurs de ton processeur (ici, en utilisant 8 processus parallèles) :

```bash
python3 -m backtest_engine optimize \
  --strategy hma_crossover \
  --symbol GMAB \
  --timeframe 15 \
  --param fast_len=5:30:5 \
  --param slow_len=20:100:10 \
  --workers 8 \
  --score total_net_pnl
```

---

## 2. Recherche Bayésienne (Optuna TPE) : L'exploration intelligente

Dès que tu t'attaques à des stratégies complexes (comme notre stratégie *Noise Boundary Intraday* ou *3Commas Bot*) avec 4 ou 5 paramètres différents, le nombre de combinaisons de ta grille explose pour dépasser les 50 000 possibilités. Même avec un processeur puissant, exécuter une Grid Search prendrait des heures.

La **Recherche Bayésienne** (s'appuyant sur l'algorithme TPE d'Optuna) résout ce problème de temps. Au lieu de tester chaque point de manière bête et méchante, l'algorithme observe les résultats des premiers essais aléatoires. Il construit alors un modèle probabiliste pour deviner quelles zones de paramètres ont le plus de chances d'améliorer ton score, et concentre ses calculs sur ces zones prometteuses.

En pratique, **300 à 500 essais bayésiens obtiennent souvent de meilleurs résultats qu'une grille exhaustive de 10 000 combinaisons**, en une fraction du temps.

### Lancer une recherche intelligente
Pour lancer une optimisation bayésienne limitée à 300 essais :

```bash
python3 -m backtest_engine optimize \
  --strategy noise_boundary_intraday \
  --symbol BTCUSD \
  --optimization-mode bayesian \
  --max-iterations 300 \
  --param lookback_days=10:40:1 \
  --param volatility_multiplier_enter=1.0:4.0:0.1 \
  --param volatility_multiplier_exit=0.5:2.0:0.1 \
  --score sharpe_ratio
```

### Recherche Multi-Objectif et Front de Pareto

Imagine que tu optimises ta stratégie sur le ratio de Sharpe. L'algorithme trouve un réglage avec un Sharpe incroyable de 3.5. En regardant de plus près, tu découvres que ce score provient d'un trade unique extraordinairement chanceux ; le profit net global est dérisoire et les autres trades sont tous perdants.

C'est le danger d'optimiser selon un unique critère : tu risques de générer des anomalies statistiques inadaptées à la réalité du trading.

Pour résoudre ce problème, le moteur supporte la **recherche multi-objectif**. Tu peux optimiser simultanément deux métriques indépendantes et parfois contradictoires : maximiser le Sharpe tout en maximisant le profit net total, ou encore minimiser le drawdown maximal.

L'algorithme d'Optuna ne te sortira pas une seule combinaison magique, mais un **Front de Pareto** : l'ensemble des compromis optimaux où aucune métrique ne peut être améliorée sans détériorer l'autre.

Pour lancer une recherche multi-objectif avec deux métriques :

```bash
python3 -m backtest_engine optimize \
  --strategy noise_boundary_intraday \
  --symbol BTCUSD \
  --optimization-mode bayesian \
  --max-iterations 300 \
  --score sharpe_ratio \
  --score-direction max \
  --secondary-score total_net_pnl \
  --secondary-score-direction max
```

À la fin de l'optimisation, l'outil génère un rapport spécifique en plus de ton résumé habituel :
- **pareto_front.json** : la liste de tous les points d'équilibre optimaux trouvés. Tu peux ainsi choisir visuellement le réglage qui correspond le mieux à ton profil de risque.

### Importance Relative des Paramètres

Tu lances une optimisation sur 6 paramètres différents. Après 300 essais, tu obtiens de super résultats. Mais une question te taraude : quels sont les leviers qui ont réellement fait bouger les performances ? Est-ce la longueur de ta moyenne mobile rapide, ou le multiplicateur de ton Stop Loss ?

Essayer de deviner ces relations à l'œil nu est souvent impossible.

Le moteur intègre un outil d'évaluation automatique de l'**importance des paramètres** s'appuyant sur l'algorithme fANOVA d'Optuna. À la fin de chaque run bayésien multi-paramètres, l'algorithme calcule la contribution de chaque variable dans l'amélioration de ton score.

Le résultat est directement écrit dans le dossier de rapport :
- **parameter_importance.json** : un dictionnaire associant à chaque paramètre un score d'importance normalisé de 0 à 1 (ou 0% à 100%).

Si ton indicateur de lookback de volatilité obtient une importance de 0.65 (65%) et ton ratio de stop suiveur obtient 0.05 (5%), tu sais immédiatement où concentrer tes efforts de recherche et d'ajustement.

---

## 3. Les outils avancés de notre Optimizer

### Le pré-calcul intelligent (Canonicalisation)
Pour éviter de perdre du temps à recalculer des simulations identiques, l'optimizer filtre et canonicalise la grille avant l'exécution :
- Si ta stratégie est configurée en mode `Long only`, l'optimizer fusionne et ignore toutes les variations de paramètres de coûts ou de commissions pour le côté `Short`.
- Si ton option `use_safety_stop` est désactivée (`false`), toutes les variations de seuils de stop loss de sécurité sont éliminées de la grille de calcul.

### Le critère d'arrêt dynamique (Early Convergence)
Pourquoi continuer à chercher si l'algorithme a déjà trouvé le réglage optimal ? En mode bayésien, tu peux activer `--enable-convergence-stop`. 

Le moteur surveille alors deux indicateurs pour couper les calculs prématurément s'ils ne mènent à rien :
- **La patience** : Arrêt si le meilleur score absolu n'a pas été amélioré depuis 100 itérations.
- **La stagnation** : Arrêt si la progression du score sur les 3 dernières fenêtres de 50 calculs est inférieure à 1%.

---

## 4. Interpréter les résultats : Éviter le piège du pic de performance

Une erreur fréquente après une optimisation est de choisir la combinaison de paramètres qui a obtenu le score maximal absolu. Souvent, ce point culminant est une anomalie statistique isolée : une configuration extrêmement instable où le moindre décalage d'un chiffre transforme ton robot rentable en gouffre financier.

Nous avons intégré un outil d'analyse à posteriori appelé le **Report Interpreter** (`report_interpreter.py`).

Au lieu de te donner un point unique, il filtre le meilleur quantile (le top 5% des runs) et identifie des zones stables : les **Sweet Spots**. 

Il te recommande ensuite la combinaison réellement testée qui se trouve géométriquement au centre de cette zone de stabilité. C'est l'assurance d'obtenir un paramétrage résilient.

### Lancer l'analyseur sur un run d'optimisation existant
```bash
python3 -m backtest_engine interpret-optimization \
  --job-dir reports/local_optimizer/hma_crossover/GMAB/T_2026-05-23_10-00-00 \
  --top-quantile 0.95 \
  --score-tolerance-pct 0.10
```

> [!NOTE]
> Tu peux également inscrire directement les clés `"top_quantile"` et `"score_tolerance_pct"` dans le fichier `optimization_config.json` de ton job. Toutes les commandes de génération et de rapport (FastAPI, script de régénération, ou worker) liront ces paramètres à la volée pour adapter la sélection sans intervention CLI.

---

## 5. Synthèse globale de portefeuille (Global Analysis)

Si tu optimises tes stratégies sur des dizaines d'actions différentes, tu n'as pas envie de parcourir les fichiers JSON de chaque symbole un par un.

Le module `global_analysis.py` regroupe automatiquement tous tes résultats d'optimisation calculés pour une stratégie donnée :

```python
from backtest_engine.global_analysis import generate_global_analysis

# Compile les sweet spots et meilleures métriques de tous les symboles d'un coup
generate_global_analysis(repo_root=".", strategy="hma_crossover")
```

Cette commande génère deux fichiers de synthèse dans `reports/local_optimizer/<strategy>/` :
- `global_summary.csv` : Le récapitulatif complet de toutes les configurations recommandées par action.
- `global_summary.html` : Un tableau interactif et visuel pour comparer facilement les performances de tes différents actifs.

<!-- Guidé par documentation/SKILL.md — sections: Technical Article Structure, Technical Writing Voice, Punctuation Guidelines, Avoiding AI-Generated Feel -->
