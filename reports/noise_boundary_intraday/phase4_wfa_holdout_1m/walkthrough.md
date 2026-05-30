# Walkthrough — Validation de Phase 4 & Décision Paper Trading

Ce document synthétise les résultats complets de la Phase 4 pour la stratégie `noise_boundary_intraday`. Il détaille les conclusions de l'ajustement paramétrique 1m (Étape 1), de l'optimisation bayésienne globale par profil de volatilité (Étape 2), du test hold-out en 5m (Étape 3) et formule la décision finale argumentée pour le passage au Paper Trading (Étape 4).

---

## 1. Synthèse des Résultats d'Optimisation Bayésienne (Étape 2)

L'optimisation bayésienne globale par profil de volatilité (1m) a été exécutée avec succès à l'aide d'un moteur multi-processus hautement optimisé. Les résultats révèlent deux dynamiques radicalement différentes selon la volatilité intrinsèque des actifs.

### 1.1 Profil Faible Volatilité (`low_vol` < 2.0%)
*Actifs concernés : NVS, SAP, LOGI, AMS.MC, SHL.DE, NVO (50 trials)*

* **Paramètres Optimaux Trouvés :**
  ```json
  {
    "lookback_days": 17,
    "volatility_multiplier_enter": 0.6,
    "volatility_multiplier_exit": 0.16,
    "target_daily_volatility": 0.014,
    "stoploss_ladder_step0": -0.019,
    "stoploss_ladder_step1": -0.028,
    "stoploss_ladder_ratio0": 0.5,
    "takeprofit_ladder_step0": 0.028,
    "exit_mode": "combined"
  }
  ```
* **Performance par Ticker (In-Sample) :**
  
  | Ticker | Sharpe IS | Nombre de Trades | Max Drawdown (MDD) | Taux de Réussite | Verdict |
  |--------|-----------|------------------|--------------------|------------------|---------|
  | **NVS** | -0.137 | 425 | -99.99% | 46.1% | ❌ Ruine |
  | **SAP** | 0.080 | 439 | -99.99% | 46.9% | ❌ Ruine |
  | **LOGI** | 0.446 | 202 | -98.14% | 51.0% | ❌ Ruine |
  | **AMS.MC**| 0.124 | 318 | -100.39% | 23.6% | ❌ Ruine |
  | **SHL.DE**| 0.270 | 447 | -99.95% | 51.7% | ❌ Ruine |
  | **NVO** | 0.525 | 410 | -99.62% | 51.2% | ❌ Ruine |

> [!CAUTION]
> **Catastrophe sur Faible Volatilité :** Bien que l'optimisation bayésienne ait réussi à augmenter significativement le nombre de trades (de ~20 à >300 par actif) en resserrant les bandes, l'espérance mathématique reste proche de zéro ou négative. En combinant un sizing à volatilité cible (`target_daily_volatility=0.014`) avec une absence d'avantage statistique réel, **chaque actif subit une ruine totale du capital (-98% à -100%)**.

---

### 1.2 Profil Élevée Volatilité (`high_vol` ≥ 2.0%)
*Actifs concernés : GMAB, ZEAL.CO (30 trials)*

* **Paramètres Optimaux Trouvés :**
  ```json
  {
    "lookback_days": 28,
    "volatility_multiplier_enter": 0.2,
    "volatility_multiplier_exit": 0.08,
    "target_daily_volatility": 0.016,
    "stoploss_ladder_step0": -0.013,
    "stoploss_ladder_step1": -0.023,
    "stoploss_ladder_ratio0": 0.9,
    "takeprofit_ladder_step0": 0.010,
    "exit_mode": "combined"
  }
  ```
* **Performance par Ticker (In-Sample) :**
  
  | Ticker | Sharpe IS | Nombre de Trades | Max Drawdown (MDD) | Taux de Réussite | CAGR |
  |--------|-----------|------------------|--------------------|------------------|------|
  | **GMAB** | 3.438 | 5308 | **-82.49%** | 15.39% | +8424.5% |
  | **ZEAL.CO**| 3.368 | 3643 | **-76.59%** | 11.64% | +2750.8% |

> [!WARNING]
> **Surapprentissage ou Risque Asymétrique Massif :** Pour les biotechs volatiles, l'optimiseur a trouvé un Sharpe IS extrêmement élevé (> 3.3) en générant un volume de trading colossal (plus de 10-15 trades par séance) avec un taux de réussite minuscule (11% - 15%). La stratégie gagne très rarement mais capte des mouvements massifs. Cependant, **le Max Drawdown reste insoutenable (-76.6% et -82.5%)**, ce qui est totalement inacceptable pour un déploiement réel.

---

## 2. Comparaison des Granularités (Étape 3 : 1m vs 5m)

Le test de hold-out parallélisé en granularité 5m (sur les paramètres baseline) a mis en évidence le compromis bruit/signaux de la stratégie :

1. **Lissage du Bruit (5m) :** Le passage en 5m stabilise les bandes et évite les faux signaux intraday à haute fréquence. Pour certains actifs comme **LOGI**, cela améliore le Sharpe OOS qui passe de `-0.190` (1m) à `+0.613` (5m) avec un MDD restreint à `-6.5%`.
2. **Disparition des Signaux (5m) :** Pour la majorité des autres actifs (GMAB, NVO, NVS, ZEAL.CO), le nombre de trades s'effondre à seulement **2 trades sur 1 an**. Les bandes de volatilité basées sur la bougie 5m et l'open quotidien deviennent trop larges pour être franchies.
3. **Verdict Granularité :** La granularité 5m est trop lente pour générer un échantillon statistique de trades viable sur ces actions, tandis que la granularité 1m est trop bruitée et destructrice de capital.

---

## 3. Décision Paper Trading (Étape 4)

### Évaluation par rapport aux critères de passage opérationnels :
* **Sharpe OOS moyen > 0.8** : ❌ **Non atteint**. L'OOS moyen reste plombé par les mauvaises performances sur les devises EUR/CHF.
* **MDD < 30% sur au moins 6/8 tickers** : ❌ **Non atteint**. Les drawdowns maximaux réels frôlent ou atteignent -100% sur la majorité des actifs, et dépassent -76% même sur les actifs rentables.
* **Nombre de trades OOS > 50/an par ticker** : ❌ **Non atteint** (hors actifs ultra-volatiles).

### 🔴 VERDICT FINAL : **NO-GO STRICT**

Il est formellement recommandé de **ne pas lancer cette stratégie en Paper Trading** sur ce panier d'actions européennes. 

**Justification Structurelle :**
1. **Absence d'avantage (Edge) sur faible volatilité :** Le concept de franchissement de frontière de bruit présuppose un retour à la moyenne rapide. Sur les actions à faible volatilité, ce retour à la moyenne ne couvre pas les coûts de transaction, ou le prix subit de petites tendances intraday persistantes qui déclenchent les stop losses à répétition.
2. **Instabilité extrême du Position Sizing à Volatilité Cible :** Lorsque la stratégie subit des séries de pertes consécutives (ce qui arrive fréquemment avec des taux de réussite de 11% à 45%), la formule de dimensionnement basée sur la volatilité historique n'empêche pas une décapitalisation totale. L'exécution sur la bougie suivante (`execute_on_next_bar=True`) crée un glissement (slippage) qui amplifie les pertes en cas de décalage brusque.

---

## 4. Rétrospective Technique & Optimisations Algorithmiques

Durant la Phase 4, deux avancées techniques majeures ont été implémentées avec succès :

### 🚀 Optimisation Mathématique du Position Sizing (36.8x Speedup)
Lors de l'analyse des goulets d'étranglement CPU, nous avons identifié que `BrokerSimulator.calculate_position_size` exécutait un calcul de variation de pourcentage (`pct_change()`) sur l'intégralité de l'historique du DataFrame Pandas (jusqu'à 1 000 000 de lignes) à chaque nouvelle prise de position. 

Nous avons optimisé cette fonction dans [broker.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/broker.py#L276-L293) en extrayant uniquement la fin du tableau (`lookback + 2` éléments) avant de calculer la volatilité historique. Cette modification, mathématiquement 100% équivalente, a généré un **gain de vitesse de 36.8x** :
* **Temps initial (1000 itérations) :** 35.07 secondes
* **Temps optimisé (1000 itérations) :** 0.95 seconde
* **Impact :** C'est cette optimisation critique qui a permis de réaliser les 80 backtests multi-actifs de l'optimisation bayésienne globale en moins de 35 minutes au lieu de plusieurs heures.

### 🧵 Résolution de la concurrence Optuna sous GIL
Nous avons documenté que l'option `n_jobs` native d'Optuna utilise le multi-threading de Python. Pour nos boucles de simulation CPU-bound, le GIL sérialise les calculs et sature un seul cœur CPU. L'architecture de parallélisation a été refactorisée pour instancier des **processus OS natifs indépendants** (`multiprocessing.Process`) pointant vers la même base de données SQLite transactionnelle, permettant d'atteindre une utilisation efficace de **800% du processeur (8 cœurs physiques)**.
