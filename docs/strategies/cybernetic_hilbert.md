# Stratégie Cybernetic Trading (Transformée de Hilbert)

**TL;DR** : Le marché n'est pas un cycle fixe ; c'est une onde dynamique. La transformée de Hilbert de John Ehlers isole le cycle dominant pour nous permettre de trader les points de retournement sans subir de retard (lag).

J'essayais d'optimiser les moyennes mobiles standards, et j'ai réalisé que le problème ne venait pas des paramètres, mais du lag. Les MM introduisent un retard par nature. Il fallait plutôt considérer le marché comme une onde pour identifier ses véritables cycles.

Voici ce que j'ai compris : si l'on sépare le marché en une onde sinusoïdale (Sine) et une onde d'avance (Lead Sine), on peut détecter le point de retournement exact du cycle dominant avant même que le prix ne le confirme.

## Le problème des oscillateurs fixes

On confond souvent l'analyse cyclique avec les oscillateurs de momentum.

### ❌ L'approche à période fixe
```python
# Hypothèse d'un cycle de 14 périodes pour tous les régimes de marché
rsi = calculate_rsi(close, period=14)
stoch = calculate_stochastic(close, period=14)
```

### ✅ L'approche Cybernétique
```python
# Calcul dynamique de la période du cycle dominant via la Transformée de Hilbert
sine, lead_sine, dc_period = _hilbert_transform_core(close_prices)
```

## Comment ça marche : La Transformée de Hilbert

La transformée de Hilbert (`_hilbert_transform_core`) est complexe (complexité cyclomatique F) car elle effectue un traitement de signal sur des données financières. Elle transforme la série de prix en un nombre complexe (composantes In-Phase et Quadrature) pour calculer l'angle de phase du cycle.

1. **Calcul de la phase** : On calcule l'angle de phase du prix actuel par rapport au cycle.
2. **Sine et Lead Sine** : 
   - **Sine Wave** : Le sinus de l'angle de phase.
   - **Lead Wave** : Le sinus de l'angle de phase avancé de 45 degrés.
3. **Cycle Dominant (DC)** : En suivant le changement de phase, on déduit la période réelle et actuelle du cycle.

## La Logique de la Stratégie

La stratégie (`run_cybernetic_hilbert`) s'appuie sur ces composants :

* **Signal d'achat** : Quand la Lead Wave croise à la baisse la Sine Wave (détection de creux).
* **Signal de vente** : Quand la Lead Wave croise à la hausse la Sine Wave (détection de sommet).
* **Filtre de Mode de Phase** : Les trades sont conditionnés ; on n'exécute que lorsque le marché est en régime "Cyclique", ignorant les périodes de tendance où les oscillateurs donnent de faux signaux.

## Intégration : POSIX SHM & Optimisation Bayésienne

Le traitement du signal étant lourd en calculs, les tableaux principaux sont alloués via `shm_allocators.py` pour garantir l'efficacité du multiprocessing. Cela permet à l'Optimiseur Bayésien de tester rapidement différentes valeurs de `smooth_period_factor` sur des années de données tick par tick (1-minute) sans épuiser la mémoire.

| Composant | Approche Standard | Approche Cybernétique |
| --------- | ----------------- | ------------------- |
| **Cycle** | Statique (ex: 14) | Dynamique (Calculé) |
| **Mémoire** | Pandas Series | Tableaux Numpy POSIX SHM |
| **Focus** | Tendance / Momentum | Points de Retournement Cycliques |

## La règle d'or : Tradez le cycle, pas le lag
Quand le marché ondule, anticipez le virage. Quand il tend, restez à l'écart.

---
_Note : Guidé par documentation/SKILL.md — sections: TL;DR, Problem-First, ❌/✅ Comparison, Trade-offs, Golden Rule._
