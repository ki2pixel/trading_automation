# Guide des Parametres de Backtest par Strategie

Ce document resume les parametres **strategiques** (logique d'entree/sortie) les plus pertinents a optimiser pour chaque strategie du moteur de backtest.

Les parametres de risk-management (`max_capital_bucket`, `trade_direction_mode`, `safety_stop_*`) sont communs a toutes les strategies ; ils peuvent faire l'objet d'une optimisation secondaire mais ne sont pas listes ici car identiques partout.

---

## HMA Crossover (reference)

Parametres deja optimises habituellement :

| Parametre      | Defaut | Type  | Plage suggeree | Description                              |
|----------------|--------|-------|----------------|------------------------------------------|
| `fast_len`     | 49     | int   | 9 - 55         | Longueur HMA rapide                      |
| `slow_len`     | 91     | int   | 55 - 200       | Longueur HMA lente                       |
| `source_col`   | close  | str   | close, hl2...  | Source de prix pour le calcul HMA        |
| `confirm_on_close` | true | bool | true/false  | Attendre la cloture pour confirmer signal |

---

## 1. Adaptive Volatility Trend

### Parametres core (haute priorite)

| Parametre              | Defaut | Type   | Plage suggeree        | Description                                           |
|------------------------|--------|--------|-----------------------|-------------------------------------------------------|
| `length`               | 21     | int    | 10 - 50               | Longueur de base de l'indicateur de tendance          |
| `atr_len`              | 14     | int    | 7 - 21                | Longueur ATR pour l'adaptation volatilite             |
| `atr_mult`             | 2.0    | float  | 1.0 - 3.5             | Multiplicateur ATR (plus haut = moins de signaux)     |
| `preset`               | Default| str    | Conservative/Default/Aggressive/Scalping | Prereglage global ; override length/atr_len/atr_mult si != Default |
| `efficiency_smoothing` | 5      | int    | 3 - 10                | Lissage du ratio d'efficience                         |
| `min_signal_score`     | 40     | int    | 20 - 70               | Score minimum pour valider un signal                  |

### Filtres optionnels (activation + valeurs)

| Parametre          | Defaut | Type  | Plage suggeree | Description                                      |
|--------------------|--------|-------|----------------|--------------------------------------------------|
| `use_rsi_filter`   | true   | bool  | true/false     | Active le filtre RSI                             |
| `rsi_len`          | 14     | int   | 7 - 21         | Longueur RSI                                     |
| `rsi_overbought`   | 70     | int   | 60 - 80        | Seuil surachat RSI                               |
| `rsi_oversold`     | 30     | int   | 20 - 40        | Seuil survente RSI                               |
| `use_volume_filter`| true   | bool  | true/false     | Active le filtre volume                          |
| `volume_mult`      | 1.2    | float | 0.8 - 2.0      | Multiplicateur volume (plus haut = plus strict)  |

**Conseil** : tester soit `preset=Default` + `length`/`atr_len`/`atr_mult` customises, soit les 4 presets entre eux.

---

## 2. Range Filter

Strategie tres legere, seulement 2 parametres core :

| Parametre           | Defaut | Type   | Plage suggeree | Description                                              |
|---------------------|--------|--------|----------------|----------------------------------------------------------|
| `sampling_period`   | 100    | int    | 50 - 200       | Periode d'echantillonnage (lookback)                     |
| `range_multiplier`  | 3.0    | float  | 1.5 - 5.0      | Multiplicateur de range (plus haut = zones plus larges) |
| `source_col`        | close  | str    | close, hl2...  | Source de prix                                           |

**Conseil** : ces 2 parametres determinant presque entierement le comportement. C'est la strategie la plus rapide a optimiser.

---

## 3. 3Commas-Bot

Strategie de crossover MA avec stops ATR dynamiques et trailing stop optionnel :

### Parametres core (haute priorite)

| Parametre      | Defaut | Type   | Plage suggeree        | Description                                              |
|----------------|--------|--------|-----------------------|----------------------------------------------------------|
| `ma_type1`     | EMA    | str    | EMA, SMA, HMA, WMA, DEMA, VWMA, VWAP, T3, HEMA | Type de la MA rapide (signal) |
| `ma_type2`     | EMA    | str    | EMA, SMA, HMA, WMA, DEMA, VWMA, VWAP, T3, HEMA | Type de la MA lente (tendance) |
| `ma_length1`   | 21     | int    | 5 - 100               | Longueur de la MA 1 (rapide)                             |
| `ma_length2`   | 50     | int    | 10 - 200              | Longueur de la MA 2 (lente)                              |
| `rnr`          | 1.0    | float  | 0.5 - 5.0             | Ratio Reward:Risk (take-profit vs stop-loss)             |
| `risk_m`       | 1.0    | float  | 0.5 - 3.0             | Multiplicateur ATR ajoute au stop                        |
| `swing_lookback`| 5     | int    | 1 - 20                | Lookback pour le swing high/low (base du stop)           |
| `atr_len`      | 14     | int    | 5 - 50                | Periode de calcul de l'ATR                               |

### Parametres secondaires

| Parametre        | Defaut | Type   | Plage suggeree | Description                                         |
|------------------|--------|--------|----------------|-----------------------------------------------------|
| `trail_stop`     | false  | bool   | true/false     | Activer le trailing stop ATR                        |
| `trail_stop_size`| 1.0    | float  | 0.5 - 3.0      | Multiplicateur ATR pour le trailing stop            |
| `rr_exit`        | 0.0    | float  | 0.0 - 2.0      | R:R a atteindre avant d'activer le trailing stop    |
| `flip`           | false  | bool   | true/false     | Autoriser les trades de reversal (long <-> short)   |
| `use_limit`      | true   | bool   | true/false     | Utiliser une sortie limite (take-profit)            |
| `long_trades`    | true   | bool   | true/false     | Activer les entrees long                            |
| `short_trades`   | true   | bool   | true/false     | Activer les entrees short                           |
| `set_max_drawdown`| false | bool   | true/false     | Activer la protection max drawdown                  |
| `max_perc_dd`    | 20.0   | float  | 5.0 - 50.0     | Drawdown max autorise (%)                           |

### Parametres de fee / safety stop (communs a toutes les strategies)

| Parametre                    | Defaut | Type   | Plage suggeree | Description                                         |
|------------------------------|--------|--------|----------------|-----------------------------------------------------|
| `trade_direction_mode`       | Long & Short | str | Long & Short / Long only / Short only | Direction de trading autorisée |
| `fee_mode`                   | Parametric: hold until net covers fees | str | 3 modes | Comportement sur signal opposé (reversal) |
| `estimated_commission_per_order_long` | 0.0 | float | 0 - 5 | Commission estimée par ordre LONG |
| `estimated_commission_per_order_short`| 3.0 | float | 0 - 5 | Commission estimée par ordre SHORT |
| `estimated_slippage_per_side_long`    | 0.0 | float | 0 - 5 | Slippage estimé par côté LONG |
| `estimated_slippage_per_side_short`   | 0.0 | float | 0 - 5 | Slippage estimé par côté SHORT |
| `min_net_profit_after_costs` | 0.0    | float  | 0 - 20         | Profit net minimal pour reversal (fee_mode) |
| `use_net_bracket_exits`      | false  | bool   | true/false     | Activer les sorties TP/SL nettes explicites |
| `take_profit_net_percent`    | 10.0   | float  | 1 - 20         | Take-profit net en % de la valeur d'entrée |
| `stop_loss_net_percent`      | 10.0   | float  | 1 - 20         | Stop-loss net en % de la valeur d'entrée |
| `use_safety_stop`            | true   | bool   | true/false     | Activer le safety stop de dernier recours |
| `safety_stop_applies_to`     | Short only | str | Both / Long only / Short only | Directions concernées par le safety stop |
| `safety_stop_mode`           | Net loss only | str | 4 modes | Mode de déclenchement du safety stop |
| `safety_max_net_loss_mode`   | Cash amount | str | Cash amount / % entry value | Type de seuil de perte |
| `safety_max_net_loss_cash`   | 50.0   | float  | 0 - 100        | Perte maximale cash |
| `safety_max_net_loss_percent`| 0.0    | float  | 0 - 20         | Perte maximale en % de la valeur d'entrée |
| `safety_max_bars_in_trade`   | 0      | int    | 0 - 50         | Nombre max de barres en position (0 = désactivé) |

**Conseil** : `ma_length1`/`ma_length2` et `ma_type1`/`ma_type2` sont les piliers (choix du couple de MAs). `rnr` et `risk_m` controlent le risk-management. Tester `trail_stop=true` avec `rr_exit=0.5` - `1.0` pour ameliorer les trades gagnants. Les paramètres `fee_mode` et `safety_stop` s'appliquent uniquement quand `flip=true` (reversal activé).

---

## 4. Bjorgum Double Tap

Stratégie de détection de patterns Double Top / Double Bottom avec objectifs et stops projetés depuis le neckline.

### Paramètres core (haute priorité)

| Paramètre      | Défaut | Type   | Plage suggérée | Description                                           |
|----------------|--------|--------|----------------|-------------------------------------------------------|
| `tol`          | 15.0   | float  | 5 - 30         | Tolérance de hauteur entre les pics (en % du pattern) |
| `length`       | 50     | int    | 10 - 100       | Longueur du pivot (lookback pour les highs/lows)      |
| `fib`          | 100.0  | float  | 50 - 200       | Extension Fibonacci de la cible (depuis le neckline)  |
| `stopPer`      | 0.0    | float  | 0 - 100        | Extension Fibonacci du stop (depuis le point haut/bas)|
| `dLong`        | true   | bool   | true/false     | Activer la détection des Double Bottom (long)         |
| `dShort`       | true   | bool   | true/false     | Activer la détection des Double Top (short)           |
| `FLIP`         | true   | bool   | true/false     | Autoriser l'entrée inverse alors qu'une position est déjà ouverte |

### Trailing Stop ATR (optionnel)

| Paramètre      | Défaut | Type   | Plage suggérée | Description                                           |
|----------------|--------|--------|----------------|-------------------------------------------------------|
| `atrStop`      | false  | bool   | true/false     | Activer le trailing stop ATR après atteinte de la cible |
| `atrLength`    | 14     | int    | 7 - 21         | Période de calcul de l'ATR                            |
| `atrMult`      | 1.0    | float  | 1.0 - 3.0      | Multiplicateur de l'ATR pour le trailing stop         |
| `lookback`     | 5      | int    | 3 - 15         | Lookback pour le swing high/low du trailing stop      |

**Conseil** : `tol` et `length` sont les piliers de la détection de pattern. Un `tol` bas (ex: 10) rend les patterns très stricts (moins de trades, plus fiables). Un `fib` à 100 correspond à un objectif 1:1 de la hauteur du pattern. Activer `atrStop=true` désactive le take-profit statique et passe en mode trailing dynamique.

---

## 5. PMax Explorer

Stratégie basée sur le croisement d'une Moyenne Mobile (MA) avec un PMax (Profit Maximizer, inspiré par ATR Trailing Stop).

### Parametres core (haute priorite)

| Parametre      | Defaut | Type   | Plage suggeree  | Description                                         |
|----------------|--------|--------|-----------------|-----------------------------------------------------|
| `periods`      | 10     | int    | 5 - 50          | Période de calcul de l'ATR (pour le stop PMax)      |
| `multiplier`   | 3.0    | float  | 1.0 - 10.0      | Multiplicateur ATR pour la distance du stop PMax    |
| `mav`          | EMA    | str    | SMA, EMA, WMA, TMA, VAR, WWMA, ZLEMA, TSF | Type de la Moyenne Mobile calculée          |
| `length`       | 10     | int    | 5 - 50          | Longueur de la Moyenne Mobile                       |
| `change_atr`   | true   | bool   | true/false      | Utilise le lissage RMA si `true` pour l'ATR, sinon SMA |
| `source_col`   | hl2    | str    | open, high, low, close, hl2 | Source de données de prix utilisée par les indicateurs |

**Conseil** : PMax Explorer est un système de suivi de tendance robuste. Expérimentez avec les différents types de moyennes mobiles (`mav`) car elles influencent grandement la vitesse à laquelle la tendance est identifiée. `VAR` ou `ZLEMA` peuvent être intéressants pour des signaux très rapides.

---

## 6. Noise Boundary Intraday

Stratégie intraday basée sur des bandes de volatilité dynamiques (bruit) construites à partir du range quotidien. Les entrées se font sur franchissement des bandes d'entrée ; les sorties sont gérées par un mode de sortie configurable (time, VWAP, ladder, combined).

### Paramètres core (haute priorité)

| Paramètre                     | Défaut | Type   | Plage suggérée | Description                                           |
|-------------------------------|--------|--------|----------------|-------------------------------------------------------|
| `lookback_days`               | 20     | int    | 1 - 60         | Fenêtre de volatilité en jours (lookback du range)  |
| `volatility_multiplier_enter` | 2.0    | float  | 0.3 - 3.0      | Multiplicateur de la bande d'entrée (doit être > exit)|
| `volatility_multiplier_exit`  | 1.0    | float  | 0.1 - 3.0      | Multiplicateur de la bande de sortie                 |
| `target_daily_volatility`     | 0.01   | float  | 0.001 - 0.1    | Volatilité cible pour le sizing (Target Vol)          |
| `start_trade_after_open_minutes`| 15   | int    | 1 - 90         | Délai après ouverture avant autorisation d'entrée     |
| `trade_frequency_bars`        | null   | int    | 1 - 20         | Fréquence max d'entrée en barres (désactivé par défaut) |
| `allow_overnight`             | false  | bool   | true/false     | Autorise le portage overnight (désactive TimeExitRule) |
| `use_vwap_filter`             | true   | bool   | true/false     | Active la condition d'entrée liée au VWAP              |
| `exit_trades_before_close_minutes`| 15 | int    | 11 - 90        | Sortie forcée avant la clôture (min, si non overnight) |
| `exit_mode`                   | time_only | str | time_only, vwap, ladder, combined | Mode de sortie avancée                    |

### Ladder exits (actifs si exit_mode = ladder ou combined)

| Paramètre                  | Défaut | Type   | Plage suggérée | Description                                           |
|----------------------------|--------|--------|----------------|-------------------------------------------------------|
| `stoploss_ladder_step0`    | -0.008 | float  | -0.02 - -0.002 | Ladder SL : seuil 1 (fraction du prix d'entrée)       |
| `stoploss_ladder_step1`    | -0.015 | float  | -0.03 - -0.005 | Ladder SL : seuil 2 (fraction du prix d'entrée)       |
| `stoploss_ladder_ratio0`   | 0.5    | float  | 0.1 - 0.9      | Ladder SL : fraction de position fermée au seuil 1     |
| `takeprofit_ladder_step0`  | 0.012  | float  | 0.005 - 0.03   | Ladder TP : seuil 1 (fraction du prix d'entrée)       |

### Paramètres de risk-management / sizing (communs)

| Paramètre                    | Défaut | Type   | Plage suggérée | Description                                         |
|------------------------------|--------|--------|----------------|-----------------------------------------------------|
| `max_entry_price`            | 300    | float  | 1 - 1000       | Prix max d'entrée autorisé                          |
| `max_capital_bucket`         | 300    | float  | 10 - 1000      | Capital max alloué par bucket                       |
| `initial_capital_bucket`     | 300    | float  | 10 - 1000      | Capital initial du bucket                           |
| `trade_direction_mode`       | Long & Short | str | Long & Short / Long only / Short only | Direction autorisée |
| `fee_mode`                   | Parametric: hold until net covers fees | str | 3 modes | Comportement sur signal opposé |
| `estimated_commission_per_order_long` | 0 | float | 0 - 5 | Commission estimée par ordre LONG |
| `estimated_commission_per_order_short`| 0 | float | 0 - 5 | Commission estimée par ordre SHORT |
| `estimated_slippage_per_side_long`    | 0 | float | 0 - 5 | Slippage estimé par côté LONG |
| `estimated_slippage_per_side_short`   | 0 | float | 0 - 5 | Slippage estimé par côté SHORT |
| `min_net_profit_after_costs` | 0      | float  | 0 - 20         | Profit net minimal pour reversal (fee_mode)         |
| `use_net_bracket_exits`      | false  | bool   | true/false     | Activer les sorties TP/SL nettes explicites         |
| `take_profit_net_percent`    | 10     | float  | 1 - 20         | Take-profit net en % de la valeur d'entrée          |
| `stop_loss_net_percent`      | 10     | float  | 1 - 20         | Stop-loss net en % de la valeur d'entrée            |
| `use_safety_stop`            | true   | bool   | true/false     | Activer le safety stop de dernier recours           |
| `safety_stop_applies_to`     | Short only | str | Both / Long only / Short only | Directions concernées |
| `safety_stop_mode`           | Net loss only | str | 4 modes | Mode de déclenchement du safety stop |
| `safety_max_net_loss_mode`   | Cash amount | str | Cash amount / % entry value | Type de seuil de perte |
| `safety_max_net_loss_cash`   | 50     | float  | 0 - 100        | Perte maximale cash                                 |
| `safety_max_net_loss_percent`| 0      | float  | 0 - 20         | Perte maximale en % de la valeur d'entrée           |
| `safety_max_bars_in_trade`   | 0      | int    | 0 - 50         | Nombre max de barres en position (0 = désactivé)    |

**Conseil** : `volatility_multiplier_enter` et `volatility_multiplier_exit` sont les piliers de la stratégie. La contrainte de validation impose `exit < enter`. Utilisez `trade_frequency_bars` pour spécifier le cooldown en nombre de barres si nécessaire (sans fréquence définie, l'évaluation se fait à chaque bougie, évitant tout désalignement de grille). `allow_overnight=true` permet le swing trading (portage overnight) tandis que `use_vwap_filter=false` permet d'assouplir les entrées en évitant le double filtre. Commencez avec `lookback_days=20` et ajustez la paire enter/exit pour calibrer la fréquence de trading. Le mode `exit_mode=time_only` est le plus simple ; `ladder` ou `combined` améliorent la gestion des profits et pertes partiels.

---

## 7. Cybernetic Trading (Transformée de Hilbert)

Stratégie basée sur le traitement de signal pour identifier dynamiquement la phase du cycle dominant.

### Paramètres core (haute priorité)

| Paramètre               | Défaut | Type   | Plage suggérée | Description                                           |
|-------------------------|--------|--------|----------------|-------------------------------------------------------|
| `hilbert_smooth_period` | 7      | int    | 4 - 20         | Lissage de base pour le calcul In-Phase/Quadrature    |
| `phase_mode_enabled`    | true   | bool   | true/false     | Gater les signaux selon le mode de marché (Cyclique)  |
| `require_cycling_bars`  | 1      | int    | 1 - 5          | Nombre de barres cycliques consécutives avant entrée  |

**Conseil** : Cette stratégie a un très petit espace de recherche. Le paramètre `hilbert_smooth_period` contrôle la réactivité globale. Activer `phase_mode_enabled` est crucial pour éviter de trader lors de forts mouvements tendanciels.

---

## 8. Smart Trader Geometric

Stratégie basée sur le framework géométrique isotrope (ICS), mesurant les distances et aires des prix par rapport aux extremums historiques sans lag temporel.

### Paramètres core (haute priorité)

| Paramètre               | Défaut | Type   | Plage suggérée | Description                                           |
|-------------------------|--------|--------|----------------|-------------------------------------------------------|
| `lookback_period`       | 23     | int    | 10 - 50        | Fenêtre de lookback pour définir le Ceiling et le Floor |
| `min_long_entry_slots`  | 1      | int    | 1 - 5          | Nombre minimum de slots valides (quorum) pour achat   |
| `min_short_entry_slots` | 1      | int    | 1 - 5          | Nombre minimum de slots valides (quorum) pour vente   |
| `signal_mode`           | Close  | str    | Close / Live   | Confirmation sur clôture ("Close") ou temps réel ("Live") |

**Conseil** : Le `lookback_period` définit la taille de la boîte géométrique (anchor). Un lookback court réagira très vite au bruit, un lookback long captera de vastes tendances. Ajuster les `slots` permet de durcir ou assouplir les conditions d'entrée (quorum).

---

## Recommandations Globales de Filtrage des Backtests

Les paramètres de filtrage des backtests (score, drawdown, etc.) ne doivent pas être identiques pour toutes les stratégies. L'horizon de temps et la logique de la stratégie imposent d'adapter ces critères.

- **Min trades clôturés** : Doit être ajusté à la fréquence de la stratégie.
  - *Intraday* (`noise_boundary_intraday`) : 100 trades minimum est parfait.
  - *Tendance* (`hma_crossover`, `pmax_explorer`, `adaptive_volatility_trend`) : Vise des mouvements longs. 30 à 50 trades suffisent sur un historique de quelques années.
- **Métrique de score** :
  - *En théorie* : Le suivi de tendance vise la surperformance pure, donc `return_vs_buy_hold_pct_points`. L'intraday et le DCA visent la régularité, donc `sharpe_ratio` est naturel.
  - *En pratique (Optimiseur)* : Pour `noise_boundary_intraday`, l'optimisation pure sur Sharpe peut conduire à l'inactivité (la stratégie maximise le ratio avec très peu de trades pour éviter tout risque). **L'utilisation de `return_vs_buy_hold_pct_points` est donc recommandée** pour forcer l'activité, à la condition stricte de la coupler avec une limite de drawdown (`max_drawdown_pct = -25` par exemple).
- **Max Drawdown** :
  - *Intraday* : Strict (-15% à -25%) pour contrer l'agressivité de l'optimisation sur le rendement.
  - *Tendance / DCA* : Plus tolérant (-25% à -30%) car le marché est volatil et ces stratégies subissent des retracements.
- **Min exposition** : 3% est une bonne limite basse pour éviter les stratégies hyper-optimisées qui ne font qu'un trade par an.
- **Min profit factor** : 1.25 est un excellent standard universel attestant d'un véritable avantage statistique.

### Résumé des paramètres de filtrage conseillés :

| Stratégie / Logique | Min Trades | Score Metric recommandé | Max Drawdown | Min Profit Factor |
| :--- | :--- | :--- | :--- | :--- |
| **`noise_boundary`** (Intraday) | 100+ | `return_vs_buy_hold_pct_points` | -15% à -25% | 1.25 |
| **`commas_bot`** (DCA / Grid) | 80+ | `sortino_ratio` | -25% | 1.25 |
| **`hma_crossover`** (Tendance) | 30 - 50 | `return_vs_buy_hold_pct_points` | -25% à -30% | 1.25 |
| **`pmax_explorer`** (Tendance) | 30 - 50 | `return_vs_buy_hold_pct_points` | -25% à -30% | 1.25 |
| **`adaptive_volatility`** (Tendance)| 30 - 50 | `return_vs_buy_hold_pct_points` | -25% à -30% | 1.25 |
| **`range_filter`** (Tendance) | 30 - 50 | `return_vs_buy_hold_pct_points` | -25% à -30% | 1.25 |
| **`bjorgum_double_tap`** (Pattern/Swing)| 30 - 50 | `return_vs_buy_hold_pct_points` | -25% à -30% | 1.25 |
| **`cybernetic_hilbert`** (Retournement) | 30 - 50 | `return_vs_buy_hold_pct_points` | -20% à -25% | 1.25 |
| **`smart_trader_geometric`** (Tendance) | 30 - 50 | `return_vs_buy_hold_pct_points` | -25% à -30% | 1.25 |

---

## Ordre de priorite global par strategie

| Strategie                     | Nb params core | Complexite d'optimisation |
|-------------------------------|----------------|---------------------------|
| Range Filter                  | 2              | Faible                    |
| HMA Crossover                 | 4              | Faible                    |
| Cybernetic Trading            | 3              | Faible                    |
| PMax Explorer                 | 6              | Faible-Moyenne            |
| Adaptive Volatility Trend     | 6-7            | Moyenne                   |
| Bjorgum Double Tap            | 7              | Moyenne-Elevee            |
| Noise Boundary Intraday       | 9              | Moyenne-Elevee            |
| 3Commas-Bot                   | 8              | Moyenne-Elevee            |
| Smart Trader Geometric        | 4              | Moyenne                   |

---

*Document mis à jour le 2026-06-06 suite au diagnostic de viabilité statistique et ajout de stratégies.*
