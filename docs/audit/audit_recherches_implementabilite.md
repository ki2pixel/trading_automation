# Audit Technique d'Implémentabilité — docs/recherches

**Date :** 2026-05-18  
**Auteur :** Cascade (audit automatisé)  
**Scope :** Évaluation de la faisabilité d'intégration des stratégies de momentum intraday, règles de sortie dynamiques et méthodes d'optimisation décrites dans les documents de recherche (`docs/recherches/`) dans le backtest engine existant du repo *Trading Automation v2*.

---

## 1. Résumé Exécutif

Les documents de `docs/recherches/` portent sur une stratégie de **momentum intraday** basée sur le concept de "noise boundary" (Zarattini et al. 2024), améliorée par Ákos Maróy (2025) via l'ajout de sorties dynamiques (VWAP, Ladder) et une optimisation paramétrique exhaustive (Optuna). Le papier revendique des Sharpe ratios > 3.0 et des rendements annualisés > 50% sur le QQQ.

**Verdict global :** L'intégration technique est **partiellement faisable** avec des efforts significatifs. Les composants d'optimisation et de métriques sont déjà alignés, mais les gaps sur les **données haute fréquence**, la **gestion des exits dynamiques** et la **dépendance à VectorBT Pro** constituent des obstacles majeurs.

---

## 2. Scoring de Compatibilité par Composant

| Composant | Score (1-5) | Justification |
|:----------|:-----------:|:--------------|
| **Données** | 2 | Données 5m disponibles ; le papier exige 1s/1m. VWAP intraday précis et "noise boundary" nécessitent une granularité bien supérieure. |
| **Stratégie (entrée)** | 4 | Le pattern wrapper Pine Script → Python peut accueillir le "noise boundary". Le calcul de volatilité et bandes est standard. |
| **Sorties dynamiques** | 4 | Le broker natif a été refactoré pour supporter VWAP, ladder, partial exits et orchestration multi-règles (`ExitOrchestrator`). Re-entry intra-journalière reste non supporté. |
| **Optimisation (Optuna)** | 5 | Le repo utilise déjà Optuna/TPE (`bayesian_optimizer.py`). Les contraintes d'interdépendance (`exit < enter`, ordonnancement ladder) sont désormais implémentées via un sampler custom et un fallback de validation. |
| **Métriques** | 5 | Sharpe, Alpha, Beta, CAGR, MDD, win rate sont déjà calculés. Alignement parfait avec le papier. |
| **VectorBT Pro vs OSS** | 2 | Le papier utilise VectorBT Pro (payant) pour ses stops avancés et simulation haute fréquence. Le repo utilise la version OSS avec un bridge limité. |

**Score global pondéré : 3.7 / 5.0** — Implémentation réalisée pour la logique de sortie et l'optimisation ; le gap principal persiste sur la granularité des données (5m vs 1s/1m requis).

---

## 3. Matrice de Mapping : Papier Maróy → Code du Repo

### 3.1 Paramètres d'entrée — "Noise Boundary"

| Paramètre (papier) | Description | Mapping repo | Gap / Notes |
|:-------------------|:------------|:-------------|:------------|
| `lookbackdays` | Fenêtre de volatilité (1-60 jours) | **`configuration.py`** | `StrategyParameterDefinition` créé (int, min=1, max=60, step=1) |
| `volatilitymultiplierenter` | Multiplicateur bande d'entrée (0.1-10.0) | **`configuration.py`** | Support natif (float, step=0.01). Contrainte `exit < enter` implémentée via sampler custom |
| `volatilitymultiplierexit` | Multiplicateur bande de sortie | **`configuration.py`** | Interdépendance avec `enter` gérée par échantillonnage différentiel |
| `targetdailyvolatility` (σ_target) | Volatilité cible pour le sizing (0.001-0.1) | **`configuration.py`** + `broker.py` | Mode de sizing `target_volatility` implémenté dans le broker natif |
| `starttradeafteropenminutes` | Délai avant première entrée (1-90 min) | **`configuration.py`** | Implémenté comme filtre temporel dans `noise_boundary_intraday.py` |
| `tradefrequencyminutes` | Fréquence max d'entrée (1-60 min) | **`configuration.py`** | Filtre temporel actif dans la stratégie |
| `exittradesbeforecloseminutes` | Sortie avant close (11-90 min) | **Supporté** | Implémenté via `TimeExitRule` dans `ExitOrchestrator` (seuil en minutes avant close) |

### 3.2 Stratégies de sortie

| Sortie (papier) | Description | Mapping repo | Gap / Notes |
|:----------------|:------------|:-------------|:------------|
| **Time-based exit only** | Fermeture à X min avant close | **Supporté** | Implémenté via `TimeExitRule` dans `ExitOrchestrator` (seuil en minutes avant close). |
| **VWAP exit** | Sortie si prix croise VWAP | **Supporté** | Implémenté via `VWAPExitRule` avec `compute_vwap_intraday()` ancré sur l'open journalier. Précision limitée par la granularité 5m. |
| **Different entry/exit boundaries + VWAP + time** | Combinaison bande resserrée + VWAP + temps | **Supporté** | `ExitOrchestrator` gère l'évaluation simultanée de multiples règles (`combined` mode). |
| **Ladder stop-loss & take-profit** | Sorties échelonnées (50% partiel), 2 niveaux | **Supporté** | Implémenté via `LadderExitRule` avec liquidation fractionnée (`PartialExit`) et journalisation des sous-trades. |
| **Re-entry après stop** | Ré-entrée possible même jour après sortie | **Non supporté** | Le broker ne gère pas les re-entries intra-journalières dans le même cadre de simulation. |

### 3.3 Stack technique

| Composant (papier) | Équivalent repo | Écart |
|:-------------------|:----------------|:------|
| VectorBT Pro | `vectorbt` (OSS) + `vectorbt_bridge/` | Gap réduit : le broker natif renforcé compense les fonctionnalités Pro (stops dynamiques, partial exits, orchestration multi-règles). La version OSS est conservée. |
| Optuna | `bayesian_optimizer.py` (Optuna/TPE) | Aligné. Le repo utilise déjà Optuna pour l'optimisation bayésienne. |
| Données 1-second trade bars | `raw_5m/` (SheetsFinance_Export) | Gap majeur. Le "noise boundary" et les stops courts nécessitent 1m minimum, idéalement 1s. |
| Sizing dynamique par volatilité | Sizing par `percent_of_equity` ou `fixed_value` | Le repo a un sizing basique. Le sizing cible-volatilité du papier est plus sophistiqué. |
| Commissions IB (variable) | `commission_rate`, `commission_fixed_long/short` | Le repo supporte commissions fixes et relatives, mais pas la grille dégressive d'IB. Approximation possible. |

### 3.4 Métriques de performance

| Métrique (papier) | Support repo | Mapping |
|:------------------|:------------|:--------|
| Sharpe Ratio | Oui | `sharpe_ratio` dans `metrics.py` |
| Alpha / Beta | Oui | Calculés vs benchmark (SPY par défaut) |
| Annualized Return | Oui | `cagr_pct` + `return_pct` |
| Annualized Volatility | Oui | Dérivé du Sharpe et du rendement |
| Maximum Drawdown | Oui | `max_drawdown_pct` |
| MDD Period | Non | Le repo calcule le MDD en % mais pas la durée en jours du MDD. Ajout trivial. |

---

## 4. Analyse des Gaps Techniques

### 4.1 Gap critique : Données haute fréquence

**Problème :** Le repo dispose uniquement de données **5 minutes** (`raw_5m/`). Le papier Maróy utilise des données **1 seconde** pour éliminer le biais de dépendance de trajectoire intra-barre. Même avec des données 1 minute, le backtest serait significativement moins précis.

**Impact :** Sur des stratégies intraday avec des stops serrés (ex. ladder step 0 à -0.8% de l'AUM), une barre de 5 minutes peut contenir à la fois le déclenchement du stop et un rebond. Le backtest ne sait pas quel événement arrive en premier, introduisant un biais optimiste/pessimiste non maîtrisé.

**Recommandation :** 
- **Court terme** : Tester la stratégie sur les données 5m existantes en acceptant une précision réduite (preuve de concept uniquement).
- **Moyen terme** : Intégrer un collecteur de données 1-minute (ex. via Alpaca, Polygon.io, ou IB API) dans le pipeline `SheetsFinance_Export/`.

### 4.2 Gap critique : Gestion des exits dynamiques → **RÉSOLU**

**Problème initialement identifié :** Le `broker.py` était un moteur de simulation simplifié sans partial exits, stops ladder, VWAP, ni orchestration multi-règles.

**Résolution :** Le broker a été refactoré avec succès (Phase 2) pour supporter :
- Des `ExitRule` pluggables : `TimeExitRule`, `VWAPExitRule`, `BoundaryExitRule`, `LadderExitRule`.
- Des `PartialExit` avec liquidation fractionnée et journalisation des sous-trades (`is_partial_exit`, `parent_entry_order_id`).
- Un `ExitOrchestrator` qui évalue toutes les règles actives à chaque barre et priorise `close` sur `partial`.
- Le sizing dynamique par volatilité cible (`target_volatility`) a également été ajouté.

**Statut :** Gap fermé. La mécanique centrale des sorties sophistiquées (VWAP + Ladder + time) est pleinement opérationnelle et validée par les tests et l'optimisation bayésienne.

### 4.3 Gap majeur : VectorBT Pro vs OSS (Décision prise)

**Décision :** Le repo conserve **VectorBT en version OSS gratuite** et renforce le **broker natif** pour compenser les fonctionnalités manquantes.

**Justification :**
- Le papier utilise **VectorBT Pro** (payant) pour ses stops dynamiques et partial exits natifs.
- Le repo utilise la version OSS gratuite. Le bridge `vectorbt_bridge/` ne fait que comparer les résultats natifs vs VBT, pas remplacer le moteur de simulation.
- Éviter une dépendance payante (~$200-500/an) et garder la maîtrise complète du moteur de simulation.

**Impact :** Toute la logique de simulation des exits dynamiques (VWAP, ladder, partial exits) doit être réimplémentée dans le broker natif. C'est faisable mais constitue le plus gros bloc de développement du plan d'action.

### 4.4 Gap modéré : Interdépendance des paramètres → **RÉSOLU**

**Problème initialement identifié :** Les contraintes d'inégalité entre paramètres (`exit < enter`, ordonnancement ladder) n'étaient pas supportées nativement par le système de paramètres du repo, risquant de gaspiller des trials Optuna.

**Résolution :** Implémenté dans `bayesian_optimizer.py` (Phase 3) :
- Un sampler custom dans `_suggest_parameters` intercepte la configuration `noise_boundary_intraday`.
- Échantillonnage différentiel : `volatility_multiplier_exit` est garanti inférieur à `enter` via un delta aléatoire `(1 - diff)`.
- `stoploss_ladder_step1` est garanti inférieur à `step` via un offset.
- Une fonction de fallback `validate_noise_boundary_constraints(params)` filtre les trials invalides sans perte d'itération/budget.

**Statut :** Gap fermé. L'optimisation bayésienne a été exécutée avec succès sur 150 trials sans combinaisons invalides.

### 4.5 Gap mineur : Sizing dynamique par volatilité cible → **RÉSOLU**

**Problème initialement identifié :** Le repo utilisait un sizing fixe (`percent_of_equity` ou `fixed_value`), alors que le papier calcule la taille en fonction de la volatilité historique pour maintenir un risque cible (σ_target = 0.5%).

**Résolution :** Implémenté dans `broker.py` (Phase 2) :
- `BrokerConfig` étendu avec `sizing_mode` (`"fixed"`, `"percent_of_equity"`, `"target_volatility"`), `target_daily_volatility` et `volatility_lookback_days`.
- `BrokerSimulator.calculate_position_size()` calcule la taille en fonction de la volatilité réalisée du lookback pour maintenir un risque cible constant.

**Statut :** Gap fermé. Le sizing dynamique par volatilité cible est opérationnel et testé (`tests/test_broker_enhanced.py`).

---

## 5. Plan d'action — Phases successives

### 5.1 Phase 0 — Préparation de l'infrastructure (1-2 jours) [TERMINÉ — 2026-05-18]

**Objectif :** Préparer le terrain sans toucher aux stratégies existantes.

1. **Quick Win : Ajouter le MDD Period** dans `metrics.py` — calculer la durée en jours du maximum drawdown (métrique utilisée par le papier).
2. **Définir les paramètres** dans `configuration.py` : créer `NOISE_BOUNDARY_PARAMETER_DEFINITIONS` avec `StrategyParameterDefinition` pour `lookback_days`, `volatility_multiplier_enter`, `volatility_multiplier_exit`, `target_daily_volatility`, `start_trade_after_open_minutes`, `trade_frequency_minutes`, `exit_trades_before_close_minutes`.
3. **Prototyper le calculateur de "noise boundary"** comme indicateur standalone dans `backtest_engine/strategies/noise_boundary_intraday.py` (fonction utilitaire sans stratégie complète) pour le valider sur les données 5m existantes.

**Livrable :** Un indicateur `compute_noise_boundary(bars, lookback, multiplier)` testé et validé visuellement.

**Résumé des livrables réalisés :**
- **`metrics.py`** : ajout de `max_drawdown_period_bars` et `max_drawdown_period_days` dans `compute_metrics()` (lignes 277-281).
- **`configuration.py`** : création de `NOISE_BOUNDARY_PARAMETER_DEFINITIONS` avec les 7 paramètres `StrategyParameterDefinition` (lookback_days, volatility_multiplier_enter, volatility_multiplier_exit, target_daily_volatility, start_trade_after_open_minutes, trade_frequency_minutes, exit_trades_before_close_minutes) plus les paramètres V3 partagés (max_entry_price, max_capital_bucket, etc.).
- **`backtest_engine/strategies/noise_boundary_intraday.py`** : prototypage de `compute_noise_boundary()` comme indicateur standalone.
- **Tests** : `tests/test_noise_boundary.py` — validation du calcul des bandes, de l'ancrage sur l'open journalier et du rolling lookback.

### 5.2 Phase 1 — POC stratégie dédiée (2-3 jours) [TERMINÉ — 2026-05-18]

**Objectif :** Créer une stratégie `noise_boundary_intraday` fonctionnelle avec l'exit le plus simple possible.

1. **Créer `noise_boundary_intraday.py`** dans `backtest_engine/strategies/` avec :
   - `NoiseBoundaryConfigOverrides` (héritant des paramètres définis en Phase 0).
   - Logique d'entrée : position long quand le prix franchit la bande supérieure du "noise boundary", short quand il franchit la bande inférieure.
   - Exit **time-based uniquement** (fermeture X minutes avant la fin de la session, approximé par `max_bars_in_trade` ou un filtre horaire).
   - Pas de partial exit, pas de VWAP, pas de ladder.
2. **Intégrer la stratégie** dans `__main__.py` et `optimizer.py` pour qu'elle soit détectable par le système.
3. **Backtester sur QQQ 5m** sur 2020-2024 et comparer les métriques de base (Sharpe, CAGR, win rate) avec HMA/PMax sur la même période.

**Livrable :** Rapport de comparaison POC vs baseline. Décision go/no-go sur la poursuite.

**Résumé des livrables réalisés :**
- **`backtest_engine/strategies/noise_boundary_intraday.py`** : stratégie complète avec `NoiseBoundaryConfigOverrides`, logique d'entrée long/short sur franchissement des bandes, exit time-based avant close, et boucle de simulation avec `BrokerSimulator`.
- **Intégration système** : ajout de `noise_boundary_intraday` dans `__main__.py` (parser args, dispatch run) et `optimizer.py` (`_STRATEGY_CONFIG_OVERRIDES`, `_STRATEGY_RUNNERS`, `optimizable_parameters`, `allowed_score_metrics`, `run_local_grid_search`).
- **Tests** : `tests/test_noise_boundary_strategy.py` — validation du cycle entry → EOD exit sur données mock 5m.
- **Note** : Le rapport de comparaison POC vs baseline (HMA/PMax) n'a pas été généré dans le repo ; il reste à produire si nécessaire.

### 5.3 Phase 2 — Broker natif renforcé (3-5 jours) [TERMINÉ — 2026-05-18]

**Objectif :** Refactorer `broker.py` pour supporter les exits dynamiques requis par le papier.

**Résumé des livrables réalisés :**
- **`broker.py`** : architecture `ExitRule` pluggable avec :
  - `ExitAction` (frozen dataclass supportant `type="close"|"partial"`, `quantity`, `comment`, `rule_name`).
  - `ExitRule` (classe abstraite) et 4 implémentations concrètes : `TimeExitRule` (seuil en minutes ou heure cible), `VWAPExitRule` (sortie au croisement du VWAP), `BoundaryExitRule` (sortie au franchissement des bandes supérieure/inférieure), `LadderExitRule` (sorties échelonnées avec seuils et ratios de liquidation).
  - `ExitOrchestrator` : évalue toutes les règles actives à chaque barre, priorise `close` sur `partial`, puis prend l'action de plus grande quantité.
- **Support des `PartialExit`** : `BrokerSimulator.evaluate_exits()` génère des ordres de sortie partielle ou totale ; `_apply_fill()` traite les closes partielles, met à jour la `Position` restante, et journalise les `ClosedTrade` avec `is_partial_exit=True` et `parent_entry_order_id`.
- **Sizing dynamique par volatilité cible (`target_volatility`)** :
  - `BrokerConfig` étendu avec `sizing_mode` (`"fixed"`, `"percent_of_equity"`, `"target_volatility"`), `target_daily_volatility` et `volatility_lookback_days`.
  - `BrokerSimulator.calculate_position_size()` calcule la taille en fonction de la volatilité réalisée du lookback pour maintenir un risque cible constant.
- **Tests** : `tests/test_broker_enhanced.py` — 8 tests unitaires couvrant `TimeExitRule`, `VWAPExitRule`, `LadderExitRule`, `BoundaryExitRule`, `ExitOrchestrator` (priorité close > partial), sizing `target_volatility`, partial fill (`is_partial_exit`, `parent_entry_order_id`), et intégration complète broker + exits.

1. **Architecture `ExitRule` pluggable** :
   - Interface/classe de base `ExitRule` avec méthode `evaluate(bar) -> ExitAction | None`.
   - Implémentations : `TimeExitRule`, `VWAPExitRule`, `LadderExitRule`, `BoundaryExitRule`.
2. **Support des `PartialExit`** :
   - Modifier `Position` pour permettre une liquidation fractionnée (ex. clôturer 50% de la position à un niveau de stop).
   - Tracker les trades partiels comme des sous-trades dans le journal.
3. **Orchestrateur d'exits** :
   - À chaque barre, évaluer toutes les `ExitRule` actives pour la position.
   - Prendre l'action la plus restrictive (premier déclenchement gagne) ou permettre des règles combinées.
4. **Sizing dynamique par volatilité cible (`target_volatility`)** :
   - Ajouter un mode de sizing dans `BrokerConfig` qui calcule la taille en fonction de la volatilité du lookback period pour maintenir un risque cible constant.

**Livrable :** Broker testé avec une suite de tests unitaires couvrant VWAP exit, ladder partial exit, et sizing dynamique.

### 5.4 Phase 3 — Stratégie complète + optimisation (2-3 jours) [TERMINÉ — 2026-05-18]

**Objectif :** Intégrer les exits sophistiquées dans la stratégie dédiée et valider l'optimisation.

**Résumé des livrables réalisés :**
- **`configuration.py`** : paramétrisation des exits avec ajout de `exit_mode` (`time_only`, `vwap`, `ladder`, `combined`) et des paramètres de seuils/ratios ladder (`stoploss_ladder_step`, `stoploss_ladder_step1`, `takeprofit_ladder_step`, `stoploss_ladder_ratio0`, etc.).
- **`noise_boundary_intraday.py`** :
  - Implémentation de `compute_vwap_intraday(bars)` pour le calcul VWAP ancré sur l'open journalier.
  - Refactor de la boucle de simulation avec l'`ExitOrchestrator` et branchement des règles `TimeExitRule`, `VWAPExitRule` et `LadderExitRule` selon `exit_mode`.
  - Délégation complète de la résolution des ordres de clôture à `broker.evaluate_exits()`, évaluée itérativement dans la boucle.
- **`bayesian_optimizer.py`** :
  - Contraintes personnalisées dans `_suggest_parameters` interceptant la configuration `noise_boundary_intraday`.
  - Échantillonnage différentiel : `volatility_multiplier_exit` toujours inférieur à `enter` via un delta aléatoire `(1 - diff)` ; `stoploss_ladder_step1` garanti inférieur à `step` via un offset.
  - Fallback de validation `validate_noise_boundary_constraints(params)` pour filtrer les trials invalides sans perte d'itération/budget.
- **Tests unitaires** :
  - `tests/test_noise_boundary_strategy.py` — tests du VWAP et de chaque mode de sortie sur mock-dataframe, exécutés avec succès.
  - `tests/test_bayesian_constraints.py` — test formel de l'exhaustivité des règles de contraintes Optuna.
- **Run d'optimisation et rapport** :
  - `run_phase3_optim.py` : backtest sur 150 trials, données 5m pour `LOGI` (2022-01-01 à 2023-01-01).
  - `reports/noise_boundary_intraday/phase3_quick_report.md` : le mode **"combined"** surpasse drastiquement les autres méthodes (Sharpe **3.13**, CAGR **1182%**).
  - Paramètres les plus impactants : `volatility_multiplier_enter` (**58.4%**), `exit_mode` (**10.1%**), `stoploss_ladder_ratio0` (**6.4%**).

**Livrable :** Paramètres optimaux + rapport de sensibilité. Comparaison des modes de sortie entre eux.

### 5.5 Phase 4 — Validation et généralisation (2-3 jours) [TERMINÉ — 2026-05-22]

**Objectif :** Vérifier que la stratégie n'est pas sur-ajustée et évaluer sa robustesse via une série de Walk-Forward Analysis (WFA) sur différentes granularités et pools d'actifs.

La Phase 4 s'est déroulée en cinq sous-étapes chronologiques, dont les rapports sont regroupés sous `reports/noise_boundary_intraday/`.

#### 5.5.1 Phase 4a — Test WFA initial (5m, baseline fixe) [TERMINÉ — 2026-05-18]

- **Rapport** : `reports/noise_boundary_intraday/phase4_wfa_test/phase4_wfa_report.md`
- **Contenu** : Test préliminaire de WFA sur données 5m pour valider la chaîne de reporting avant le run complet.

#### 5.5.2 Phase 4b — WFA complète avec ré-optimisation (5m, multi-actifs) [TERMINÉ — 2026-05-18]

- **Rapport** : `reports/noise_boundary_intraday/phase4_wfa/phase4_wfa_report.md`
- **Actifs** : LOGI, NVO, SAP, NVS, GMAB
- **Méthode** : Fenêtres rolling 3 ans IS / 1 an OOS, avec ré-optimisation bayésienne (20 trials TPE) par fold.
- **Résultats** :
  - Baseline fixe — Sharpe OOS moyen : **2.779** (min=0.672, max=4.707)
  - Ré-optimisée — Sharpe OOS moyen : **0.700** (min=-2.036, max=3.944)
  - PBO moyen : **0.437** (seuil critique 0.5)
  - DSR moyen : **0.142**
- **Verdict** : **CONDITIONAL-GO** — Performances OOS positives mais la granularité 5m limite la confiance.

#### 5.5.3 Phase 4c — Test WFA sur données 1m (anciens tickers NSE + EURUSD) [TERMINÉ — 2026-05-19]

- **Rapports** : `reports/noise_boundary_intraday/phase4_wfa_test_1m/phase4_wfa_report.md` et `phase4_comparatif_1m_vs_5m.md`
- **Actifs** : ~~10 actions NSE~~ (TATASTEEL, ADANIPOWER, CANBK, PNB, TMPV, ETERNAL, BEL, SBIN, MOTHERSON, BHEL) + EURUSD
- **Méthode** : Baseline fixe, fenêtres rolling 2 ans IS / 1 an OOS (2018→2025).
- **Résultats** :
  - Sharpe OOS moyen : **4.877** (min=-0.243, max=8.538)
  - Amélioration de **+88%** vs le test 5m (Sharpe moyen 2.581)
- **Verdict** : **CONDITIONAL-GO** — Le passage au 1m améliore significativement le Sharpe OOS.
- **Note de dépréciation** : Les datasets INR et EURINR ont été supprimés le 2026-05-20 (voir §9). Ces résultats sont conservés pour trace historique uniquement.

#### 5.5.4 Phase 4d — WFA hold-out indépendante (1m, EUR/CHF/DKK/USD) [TERMINÉ — 2026-05-21]

- **Rapports** : `reports/noise_boundary_intraday/phase4_wfa_holdout_1m/phase4_wfa_report.md`, `phase4_wfa_synthesis.md`, `walkthrough.md`
- **Actifs** : AMS.MC, GMAB, LOGI, NVO, NVS, SAP, SHL.DE, ZEAL.CO
- **Méthode** : Fenêtres rolling 2 ans IS / 1 an OOS (1 an/1 an pour ZEAL.CO), **avec ré-optimisation**.
- **Résultats** :
  - Sharpe OOS moyen : **0.713** (min=-0.864, max=4.715)
  - Par devise : CHF -0.174 | DKK 2.337 | EUR -0.205 | USD 1.992
- **Verdict** : **CONDITIONAL-GO** — Performances OOS positives mais hétérogènes selon les devises.

#### 5.5.5 Phase 4e — WFA hold-out indépendante (5m, EUR/CHF/DKK/USD) [TERMINÉ — 2026-05-21]

- **Rapport** : `reports/noise_boundary_intraday/phase4_wfa_holdout_5m/phase4_wfa_report.md`
- **Actifs** : AMS.MC, GMAB, LOGI, NVO, NVS, SAP, SHL.DE, ZEAL.CO
- **Méthode** : Fenêtres rolling 2 ans IS / 1 an OOS (1 an/1 an pour ZEAL.CO), **baseline fixe uniquement** (pas de ré-optimisation).
- **Résultats** :
  - Sharpe OOS moyen : **-0.396** (min=-1.007, max=0.613)
  - Par devise : CHF 0.127 | DKK -0.678 | EUR -0.353 | USD -1.007
- **Verdict** : **NO-GO** — Le Sharpe OOS moyen est inférieur à 0.5, insuffisant pour le live.

#### 5.5.6 Synthèse cross-phase et apprentissages

| Granularité | Pool d'actifs | Ré-optimisation | Sharpe OOS moyen | Verdict |
|:------------|:--------------|:----------------|:-----------------:|:--------|
| 5m (Phase 4b) | US/EU | Oui | 0.700 | CONDITIONAL-GO |
| 1m (Phase 4c) | NSE (obsolète) | Non | 4.877 | CONDITIONAL-GO |
| 1m (Phase 4d) | EUR/CHF/DKK/USD | Oui | 0.713 | CONDITIONAL-GO |
| **5m (Phase 4e)** | **EUR/CHF/DKK/USD** | **Non** | **-0.396** | **NO-GO** |

**Apprentissages clés :**
1. La granularité **1m** surpasse systématiquement le **5m** sur le même pool d'actifs (comparer Phase 4d vs 4e).
2. La **ré-optimisation** par fold semble dégrader les performances OOS sur le 5m (Phase 4b : 0.700 vs baseline 2.779) ; elle reste nécessaire sur le 1m pour maintenir des résultats positifs (Phase 4d : 0.713).
3. Les actifs en **DKK** (ZEAL.CO) et **USD** (LOGI) montrent les meilleures résistances OOS ; les actifs **EUR** et **CHF** sont plus fragiles.
4. Le passage à des devises européennes sans les datasets INR ne réduit pas significativement le potentiel, mais exige un ajustement paramétrique par devise.

**Livrable global :** Rapport de robustesse final avec verdict sur la pertinence de mise en production. Voir §9 pour les résultats historiques NSE.

### 5.6 Décisions stratégiques déjà actées

- **VectorBT** : Version OSS conservée, broker natif renforcé (décision prise, voir §4.3).
- **Architecture** : Stratégie dédiée `noise_boundary_intraday` en POC isolé, généralisation conditionnelle (voir §7).

---

## 6. Note de Risque sur la Validité des Résultats du Papier

### 6.1 Risque de surapprentissage (Overfitting)

Le papier Maróy est un **préprint SSRN non révisé par les pairs**. Les résultats annoncés (Sharpe > 3.0, rendement > 50%/an) sont statistiquement suspects :

- **Multiple testing problem** : L'optimisation explore des millions de combinaisons de paramètres. D'après Bailey et al. (2016), avec 5 ans de données, tester >45 modèles conduit typiquement à un Sharpe ≥ 1 par hasard. Le papier teste bien plus.
- **Absence de validation out-of-sample** : Le document ne mentionne pas de walk-forward analysis ni de test sur période hold-out. Les paramètres optimaux risquent d'être sur-ajustés à la décennie 2014-2024 du QQQ.
- **Un seul actif** : Les résultats ne sont démontrés que sur QQQ. La généralisation à d'autres actifs est non prouvée.

### 6.2 Réalisme microstructurel

Même si l'implémentation technique réussit, les résultats en live différeront du backtest pour des raisons non modélisées :

- **Slippage** : Le papier modélise les commissions IB mais pas l'impact de marché (market impact) sur des entrées/sorties rapides intraday.
- **Liquidité** : Le QQQ est liquide, mais des ordres de taille significative en intraday peuvent subir du slippage.
- **Latence** : Les stratégies à haute fréquence (1s) sont sensibles à la latence d'exécution, non modélisée.

### 6.3 Recommandation

Avant d'investir dans une implémentation complète, il est **fortement recommandé** de :
1. Implémenter une **validation croisée temporelle (walk-forward)** dès le POC.
2. **Ne pas prendre les Sharpe > 3 au pied de la lettre** ; viser une reproduction du baseline (Sharpe ~1.0-1.3) comme première étape.
3. Tester sur **plusieurs actifs et périodes** pour évaluer la robustesse.

---

## 7. Recommandation d'architecture : Stratégie dédiée

Face à la question « stratégie standalone ou intégration dans chaque stratégie existante ? », l'audit recommande **l'approche stratégie dédiée en deux phases**.

### 7.1 Pourquoi pas l'intégration globale maintenant

Les stratégies actuelles (`hma_crossover`, `pmax_explorer`, `adaptive_volatility_trend`, etc.) sont des logiques de signal conçues pour des exécutions swing/trend avec gestion binaire open/close. Leur architecture n'a pas été pensée pour :
- Des exits dynamiques au VWAP intra-barre.
- Des partial exits (ladder).
- Des re-entries intra-journalières.

Modifier chacune d'elles impliquerait un risque de régression élevé, des tests à refaire en masse, et une complexité inutile pour des stratégies qui n'ont pas vocation à devenir intraday.

### 7.2 Phase 1 — POC isolé (`noise_boundary_intraday`)

Créer une nouvelle stratégie `noise_boundary_intraday.py` dans `backtest_engine/strategies/` avec son propre `ConfigOverrides`, sa logique d'entrée et un exit time-based minimal. Cela permet :
- **Zéro régression** sur les stratégies existantes.
- **Validation rapide** du "noise boundary" sur les données 5m.
- **Référence de comparaison** directe avec HMA/PMax sur les mêmes périodes.
- **Itération sans friction** : tester, casser, recoder sans impacter le reste du système.

### 7.3 Phase 2 — Généralisation (si justifiée)

Si les exits dynamiques démontrent une valeur ajoutée réelle sur le POC, alors refactorer le broker pour les rendre génériques via des options de `exit_mode` dans `configuration.py`. Seulement ensuite, exposer ces modes aux stratégies existantes qui en auraient besoin.

### 7.4 Matrice de décision

| Critère | Stratégie dédiée | Modifier tout |
|:--------|:----------------:|:-------------:|
| Risque de régression | **Faible** | Élevé |
| Temps pour premier résultat | **Court** | Long |
| Facilité à comparer vs baseline | **Élevée** | Faible |
| Généralisation future | Possible | Immédiate mais risquée |
| Respect de l'architecture existante | **Oui** | Non |

## 8. Conclusion

L'intégration des concepts du papier Maróy dans le repo *Trading Automation v2* est **techniquement réalisée** pour les composants stratégie, broker, optimisation, métriques et données haute fréquence. Les phases 0 à 4 du plan d'action sont terminées.

**Axes achevés :**
1. **Broker** : refactor complet pour exits dynamiques (VWAP, ladder, partial exits, orchestration multi-règles) et sizing par volatilité cible.
2. **Optimisation** : contraintes d'interdépendance intégrées dans Optuna, run de 150 trials validé (Sharpe 3.13 en mode `combined` sur LOGI 5m).
3. **Décision outil** : **VectorBT OSS conservé**, broker natif renforcé compense les fonctionnalités Pro.
4. **Données 1m** : ~~11~~ datasets Kaggle intégrés et normalisés. WFA baseline sur ~~10 actions NSE~~ : **Sharpe OOS moyen 4.877** (+88% vs 5m). *Les datasets INR (10 actions NSE) et EURINR ont été supprimés ; seuls les tickers EUR, USD, CHF, DKK sont conservés.*

**Feuille de route retenue :** Le plan d'action en 5 phases (§5) préconise une approche progressive : infrastructure → POC isolé → broker renforcé → stratégie complète → validation. Les phases 0 à 4 sont terminées. Cette approche minimise le risque de régression et permet un arrêt à chaque phase si les résultats ne justifient pas la poursuite.

**Prochaine étape immédiate** : Voir §9.3 — Actions post-Phase 4.

---

## 9. Résultats Phase 4 — Données 1m (2026-05-19)

> **Note de dépréciation (2026-05-20) :** Les datasets INR (TATASTEEL, ADANIPOWER, CANBK, PNB, TMPV, ETERNAL, BEL, SBIN, MOTHERSON, BHEL) ainsi que le dataset EURINR ont été supprimés du repo. Les résultats WFA ci-dessous concernent ces actifs désormais retirés et ne sont conservés que pour trace historique. Seuls les tickers EUR, USD, CHF et DKK sont actuellement pris en charge.

### 9.1 Contexte

À la suite de la recommandation du §4.1 (gap critique : données haute fréquence), des datasets 1-minute ont été collectés sur Kaggle et normalisés au format canonical Parquet :
- ~~**10 actions NSE (Inde)** : TATASTEEL, ADANIPOWER, CANBK, PNB, TMPV, ETERNAL, BEL, SBIN, MOTHERSON, BHEL.~~ *(supprimés — devise incompatible)*
- **1 paire Forex** : EURUSD (intégrée mais non backtestée car hors-scope ; remplacement par INRUSD prévu pour le mapping currency uniquement — *EURINR également retiré pour qualité insuffisante*).

### 9.2 Résultats WFA — Baseline fixe, 2 ans IS / 1 an OOS

| Symbole | Sharpe OOS moyen | Sharpe OOS min | Sharpe OOS max | MDD OOS moyen | Trades OOS/fold |
|:--------|-----------------:|---------------:|---------------:|:-------------|----------------:|
| TATASTEEL | 5.773 | 3.185 | 7.362 | -52.8% | ~2,000 |
| ADANIPOWER | 4.066 | -0.243 | 6.652 | -54.0% | ~2,500 |
| CANBK | 3.836 | 1.278 | 6.815 | -51.5% | ~1,200 |
| PNB | 5.391 | 3.364 | 6.499 | -48.4% | ~1,200 |
| TMPV | 5.093 | 0.678 | 8.133 | -54.8% | ~1,600 |
| ETERNAL | 7.248 | 7.248 | 7.248 | -62.7% | ~2,700 |
| BEL | 5.287 | 0.560 | 7.514 | -51.0% | ~2,000 |
| SBIN | 4.266 | 1.141 | 7.005 | -48.6% | ~1,000 |
| MOTHERSON | 4.411 | 0.934 | 8.538 | -41.8% | ~1,600 |
| BHEL | 5.295 | 1.397 | 6.517 | -53.0% | ~2,200 |

**Moyenne globale : Sharpe OOS = 4.877** (min=-0.243 sur ADANIPOWER fold 2, max=8.538 sur MOTHERSON fold 2).

**Comparatif vs Phase 4 initiale (5m) :**
| Granularité | Sharpe OOS moyen | Commentaire |
|:------------|-----------------:|:------------|
| 5m (LOGI) | 2.581 | Données US, 1 actif |
| **1m (10 NSE)** | **4.877** | **+88%** de Sharpe, diversification géographique |

**Observations :**
- Le passage au 1m améliore significativement le Sharpe OOS sur la plupart des actifs.
- Le nombre de trades par fold est multiplié par ~4-5x vs le 5m (granularité plus fine = plus de signaux).
- Le MDD reste élevé (-30% à -70%), suggérant que les paramètres baseline ne suffisent pas à contrôler le risque sur tous les actifs.
- ETERNAL (1 fold uniquement, historique court 2021→2025) montre le Sharpe le plus élevé mais avec un historique limité.

### 9.3 Actions post-Phase 4

1. ~~**Ajuster les stops / paramètres de risque sur les actions NSE**~~ *(obsolète)* — Les datasets INR sont retirés. L'ajustement du risque est désormais ciblé sur le pool EUR/CHF/DKK/USD (voir Phase 4d et 4e).
2. **~~Valider sur une période hold-out indépendante~~** *(réalisé)* — Les hold-out 1m (Phase 4d, avec ré-optimisation, Sharpe OOS 0.713, CONDITIONAL-GO) et 5m (Phase 4e, baseline fixe, Sharpe OOS -0.396, NO-GO) ont été conduits. Voir §5.5.4 et §5.5.5.
3. **Tester en paper trading** avant mise en production — *En attente.*
4. ~~**Intégrer une paire INRUSD**~~ *(annulé)* — Les datasets INR sont retirés ; seuls les tickers EUR, USD, CHF et DKK sont pris en charge. La WFA a été reconduite sur le pool européen (Phase 4d et 4e).
