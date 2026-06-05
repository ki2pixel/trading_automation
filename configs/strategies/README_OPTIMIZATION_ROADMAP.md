# Feuille de Route : Optimisation Séquentielle des Backtests

Ce guide détaille la procédure étape par étape pour optimiser les différentes stratégies du moteur de backtest. Son objectif est d'éviter l'explosion combinatoire (overfitting ou "curve-fitting") en divisant l'optimisation des stratégies complexes en plusieurs passes logiques.

**Règle d'or :** À la fin de chaque passe, analysez les résultats, repérez la combinaison la plus robuste (le "sweet spot"), et **fixez ces valeurs en dur** (dans votre fichier `.json` ou l'UI de l'optimiseur) avant de lancer la passe suivante sur les autres paramètres.

---

## Catégorie A : Stratégies Simples (1 Seule Passe)
*Ces stratégies ont un espace de recherche suffisamment petit pour que l'optimiseur puisse tout tester en une seule fois sans risque de sur-optimisation.*

### 1. Range Filter
- **Passe Unique (Globale)** : 
  - *À optimiser* : `sampling_period`, `range_multiplier`, `source_col`.

### 2. HMA Crossover
- **Passe Unique (Globale)** : 
  - *À optimiser* : `fast_len`, `slow_len`, `source_col`.
  - *À bloquer (optionnel)* : Garder `confirm_on_close = true`.

---

## Catégorie B : Stratégies Moyennes (2 Passes)
*Ces stratégies séparent la détection de tendance de base et les filtres/trailing stops associés.*

### 3. PMax Explorer
- **Passe 1 : Le Signal de Base**
  - *À optimiser* : `length`, `mav` (type de moyenne mobile), `source_col`.
  - *À bloquer* : Fixer `multiplier` à une valeur large (ex: 5.0) pour que le stop PMax ne coupe pas prématurément les positions et laisse respirer le signal.
  - *Objectif* : Trouver la meilleure Moyenne Mobile de base.
- **Passe 2 : Le Trailing Stop (PMax)**
  - *À bloquer* : Le meilleur couple `length` / `mav` trouvé en Passe 1.
  - *À optimiser* : `periods` (calcul ATR), `multiplier` (distance réelle du stop), `change_atr`.
  - *Objectif* : Ajuster le stop-loss suiveur parfait pour la tendance trouvée.

### 4. Adaptive Volatility Trend
- **Passe 1 : L'indicateur Core**
  - *À optimiser* : `length`, `atr_len`, `atr_mult`.
  - *À bloquer* : Désactiver les filtres (`use_rsi_filter = false`, `use_volume_filter = false`).
  - *Objectif* : Valider que le cœur de l'indicateur capte bien les tendances.
- **Passe 2 : Les Filtres**
  - *À bloquer* : Le trio `length`/`atr_len`/`atr_mult` trouvé en Passe 1.
  - *À optimiser* : `use_rsi_filter = true`, `rsi_len`, `rsi_overbought` / `oversold`. Même chose pour le filtre volume si pertinent.
  - *Objectif* : Vérifier si le filtrage améliore le ratio Gain/Risque.

---

## Catégorie C : Stratégies Complexes (3 Passes)
*Ces stratégies possèdent des logiques de money management, de trailing stops dynamiques et d'horaires d'exécution. Les diviser est **obligatoire**.*

### 5. Cybernetic Trading (Transformée de Hilbert)
*Note : Cette stratégie exploite l'algorithme génétique CMA-ES. Pour éviter de casser sa matrice de covariance avec des "falaises" mathématiques, **aucun paramètre booléen** (ex: `use_net_bracket_exits`) ne doit être inclus dans l'espace de recherche (search space). Ils doivent être fixés en dur.*

- **Passe 1 : Mode Tendance & TP/SL (Trend Mode)**
  - *À bloquer* : Fixer `phase_mode_enabled = false` (désactive le mode cyclique), `use_net_bracket_exits = true` (active les sorties PnL) et `use_safety_stop = false`.
  - *À optimiser* : `hilbert_smooth_period` (Int), `take_profit_net_percent` (Float) et `stop_loss_net_percent` (Float).
  - *Objectif* : Trouver la meilleure combinaison purement continue pour surfer les tendances avec un filet de sécurité (TP/SL).
- **Passe 2 : Mode Oscillation (Phase Mode)**
  - *À bloquer* : Fixer `phase_mode_enabled = true`. Reprendre le meilleur trio `[hilbert_smooth_period, TP, SL]` trouvé en Passe 1.
  - *À optimiser* : `require_cycling_bars` (Int).
  - *Objectif* : Affiner le filtre de trading de range (mean-reversion) sur les cycles dominants sans détruire le signal de base.
- **Passe 3 (Optionnelle) : Time Stop (Filtre Temporel)**
  - *À bloquer* : Tous les paramètres trouvés aux Passes 1 et 2. Fixer `use_safety_stop = true`.
  - *À optimiser* : `safety_max_bars_in_trade` (Int).
  - *Objectif* : Couper les positions qui stagnent trop longtemps (Time Stop) pour libérer le capital.

### 6. 3Commas-Bot
- **Passe 1 : Le Signal (Croisement MAs)**
  - *À optimiser* : `ma_type1`, `ma_type2`, `ma_length1`, `ma_length2`.
  - *À bloquer* : `trail_stop = false`, et fixez `rnr = 1.0`, `risk_m = 1.0`.
  - *Objectif* : S'assurer que le signal de croisement offre un véritable avantage statistique brut.
- **Passe 2 : Risk-Management de base**
  - *À bloquer* : Les Moyennes Mobiles trouvées en Passe 1.
  - *À optimiser* : `rnr` (Take Profit), `risk_m` (Stop Loss ATR), `swing_lookback`.
  - *Objectif* : Maximiser le profit statique sans trailing stop.
- **Passe 3 : Trailing Stop Dynamique**
  - *À bloquer* : Les MAs de la Passe 1 et le `risk_m` de la Passe 2.
  - *À optimiser* : `trail_stop = true`, `trail_stop_size`, `rr_exit`.
  - *Objectif* : Laisser courir les gains une fois la cible initiale atteinte.

### 7. Bjorgum Double Tap
- **Passe 1 : Détection du Pattern**
  - *À optimiser* : `tol` (tolérance géométrique), `length` (pivot), `dLong`, `dShort`.
  - *À bloquer* : Fixer les cibles très loin (`fib = 100` ou plus, `stopPer = 0`) et désactiver l'ATR stop (`atrStop = false`).
  - *Objectif* : S'assurer que l'algorithme identifie de *vrais* Double Tops/Bottoms rentables.
- **Passe 2 : Cibles & Stops Statiques**
  - *À bloquer* : `tol` et `length` de la Passe 1.
  - *À optimiser* : `fib` (Niveau de Take Profit Fibonacci), `stopPer` (Stop Loss).
  - *Objectif* : Trouver le meilleur ratio de sortie statique.
- **Passe 3 : Trailing Stop ATR**
  - *À bloquer* : Le pattern et les cibles statiques.
  - *À optimiser* : `atrStop = true`, `atrLength`, `atrMult`.
  - *Objectif* : Sécuriser les gains sur les très grands mouvements.

### 8. Noise Boundary Intraday
- **Passe 1 : Le Signal Volatilité Brut**
  - *À optimiser* : `lookback_days`, `volatility_multiplier_enter`, `volatility_multiplier_exit`.
  - *À bloquer* : Mode de sortie basique (`exit_mode = time_only`), Safety stop OFF, filtres VWAP OFF.
  - *Objectif* : Prouver que le breakout de ces bandes de volatilité possède un edge directionnel.
- **Passe 2 : Activité et Timing**
  - *À bloquer* : Les bandes trouvées en Passe 1.
  - *À optimiser* : `trade_frequency_bars`, `start_trade_after_open_minutes`, `entry_on_high_low`.
  - *Objectif* : Calibrer la fréquence des trades (ni trop peu, ni trop de bruit).
- **Passe 3 : Sorties Complexes**
  - *À bloquer* : Bandes et Timing des Passes 1 & 2.
  - *À optimiser* : `exit_mode` (`ladder`, `vwap`, `combined`) et les paramètres de `ladder` (steps, ratios).
  - *Objectif* : Capturer des profits partiels en intraday pour lisser la courbe de gains (Sharpe Ratio).

### 9. Smart Trader Geometric
*Note : Cette stratégie utilisant l'optimisation bayésienne continue, les paramètres catégoriques ou booléens (`signal_mode`, bracket exits) doivent être traités séparément pour éviter de briser la continuité mathématique de l'algorithme d'optimisation.*

- **Passe 1 : Géométrie et Quorum (Core)**
  - *À bloquer* : Fixer `signal_mode = "Close"`, désactiver les safety stops et `use_net_bracket_exits = false`.
  - *À optimiser* : `lookback_period` (Int), `min_long_entry_slots` (Int), `min_short_entry_slots` (Int).
  - *Objectif* : Trouver la structure géométrique de base qui génère les meilleurs signaux directionnels purs.
- **Passe 2 : Risk-Management & Exits**
  - *À bloquer* : Le trio `lookback` et `slots` trouvé en Passe 1. Fixer `use_net_bracket_exits = true`.
  - *À optimiser* : `take_profit_net_percent` (Float), `stop_loss_net_percent` (Float).
  - *Objectif* : Optimiser les objectifs de gains mathématiques sur le squelette validé.
- **Passe 3 (Optionnelle) : Mode de Signal**
  - *À bloquer* : Tous les paramètres précédents.
  - *À optimiser* : Tester avec `signal_mode = "Live"` vs `"Close"`.
  - *Objectif* : Voir si l'exécution intra-barre (Live) améliore le rendement en réduisant le slippage implicite d'attente de clôture.

---
*Si à une étape N, vous ne trouvez aucun résultat positif, cela signifie souvent que l'étape N-1 n'était pas assez robuste. Il faut alors revenir en arrière et tester un autre "sweet spot" issu de l'étape précédente.*
