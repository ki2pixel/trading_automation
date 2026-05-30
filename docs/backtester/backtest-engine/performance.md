# Pourquoi le moteur est-il aussi rapide ?

**TL;DR** : Grâce au calcul de score rapide, à l'arrêt précoce sur drawdown et à la mise en cache des indicateurs, le temps d'exécution de 100 000 simulations est passé de 6 heures à moins de 30 minutes.

Tu as configuré une optimisation sur 100 000 combinaisons de paramètres. Ton processeur chauffe, tes ventilateurs tournent à fond, et ton terminal t'annonce fièrement : *"Temps restant estimé : 6 heures"*. Tu réalises que tu vas perdre une après-midi entière à attendre qu'un simple script se termine.

Dans le trading algorithmique, la vitesse est un avantage concurrentiel. Plus tu es rapide pour tester tes idées, plus vite tu élimines les mauvaises stratégies pour te concentrer sur les meilleures. 

Voici les quatre techniques d'ingénierie que nous avons intégrées au moteur pour diviser le temps de calcul par 12.

---

## 1. Le calcul de score rapide (Fast Scoring)
Lors d'une optimisation de grande envergure, le moteur n'a pas besoin de générer tous les graphiques HTML, la courbe de capital complète et le détail de chaque trade pour les configurations médiocres qui perdent de l'argent.

Le module `backtest_engine/metrics.py` expose une fonction ultra-légère appelée `compute_fast_score()`. 

Pendant toute la phase de recherche (Grid ou Bayésienne), le moteur calcule uniquement cette version ultra-simplifiée pour classer les candidats (en évaluant simplement le profit net final, le taux de réussite ou le profit factor). 

Le calcul complet et lourd de l'ensemble des 40 métriques avancées ( Sharpe, Sortino, durée moyenne, commissions accumulées) n'est déclenché qu'une seule fois à la toute fin, uniquement sur la combinaison gagnante.

---

## 2. L'élagage par perte maximale (Early Stopping)
Si une combinaison de paramètres s'avère catastrophique et commence à vider ton capital dès les premières bougies de cours, à quoi bon continuer à simuler les années suivantes ?

Le moteur surveille le Drawdown (la perte maximale latente) en temps réel, transaction après transaction. Si ce Drawdown dépasse la limite que tu as fixée (par exemple 30%), la simulation est immédiatement avortée. 

Le candidat reçoit une note éliminatoire très négative et le moteur passe instantanément à la combinaison suivante sans gaspiller un seul cycle de processeur.

Pour activer cet élagage intelligent depuis ton terminal :

```bash
python3 -m backtest_engine optimize \
  --symbol BTCUSD \
  --param fast_len=5:60:1 \
  --param slow_len=20:120:1 \
  --early-stop-drawdown-pct 30
```

---

## 3. La mise en cache intelligente des indicateurs
Le calcul des indicateurs techniques complexes (comme une moyenne HMA sur des milliers de bougies) est l'étape la plus gourmande en calcul de ton processeur.

Dans une grille d'optimisation, de nombreuses combinaisons partagent exactement les mêmes réglages d'indicateurs mais diffèrent sur des variables de courtage ou de risque (par exemple, tester la même longueur HMA avec des commissions ou des tailles de positions différentes).

Le moteur intègre un système de cache au niveau du processus :
- Les fonctions d'indicateurs (pour HMA Crossover, PMax Explorer et Range Filter) calculent la courbe une seule fois et l'enregistrent en mémoire.
- Si une itération suivante demande exactement le même indicateur sur le même symbole, le moteur renvoie le résultat pré-calculé instantanément au lieu de refaire toutes les opérations mathématiques.
- Ce cache s'invalide et se nettoie automatiquement à chaque démarrage de tâche ou entre les différents cœurs CPU pour éviter toute corruption de données.

---

## 4. Le saut quantique de l'Optimizer Bayésien
En combinant ces optimisations de code avec la recherche bayésienne (Optuna), tu passes d'un calcul de force brute à une exploration scientifique. L'algorithme apprend de chaque échec précédent pour trouver la zone idéale en seulement 500 essais.

### Résumé des gains en situation réelle

| Mode d'exécution | 100 000 combinaisons de test | Résultats |
|------|-----------------------------------|----------|
| Mode Grid classique (force brute historique) | ~6 heures | Exhaustif mais insupportablement lent |
| Mode Grid + Fast Scoring, Arrêt précoce et Cache | ~30 à 45 minutes | Exhaustif et rapide |
| Mode Bayésien (500 essais ciblés) | ~3 à 5 minutes | Paramétrage quasi-optimal trouvé en un clin d'œil |
