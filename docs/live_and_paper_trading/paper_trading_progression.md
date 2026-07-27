# Suivi de Progression & Historique des Phases - Paper Trading

Ce document consigne l'historique des phases d'évaluation du moteur de Paper Trading, les métriques auditées, les diagnostics comportementaux et la feuille de route des ajustements de configuration.

---

## 📅 Chronologie des Phases

- **Phase 1 (30/06/2026 au 24/07/2026)** : Évaluation initiale multi-stratégies (87 trades clôturés, 9 actifs).
- **Phase 2 (À partir du 25/07/2026)** : Réajustement et basculement sur le portefeuille certifié des **53 setups d'Optuna** (8 actifs/stratégies champions, fermeture des positions Phase 1 pour remise à zéro du benchmark).

---

## 1. Phase 1 : Bilan Quantitative & Diagnostic Comportemental (30/06/2026 - 24/07/2026)

### A. Synthèse des Performances Globale (87 Trades Appariés FIFO)

| Métrique Financière / Quantitative | Valeur Reconstituée |
| :--- | :--- |
| **Période d'Évaluation** | **30 Juin 2026 au 24 Juillet 2026** |
| **Total Transactions DB** | **178 transactions** (174 clôturées + 4 ouvertes) |
| **Paires Achat/Vente Clôturées** | **87 trades complets** |
| **Win Rate (Taux de Réussite)** | **36.78 %** (32 Gagnants / 55 Perdants) |
| **PnL Brut / Net Trading 212 (€)** | **+71.52 €** (+23.84 % sur capital engagé par bucket) |
| **PnL Net Simulé (Bybit 0.10%)** | **+21.91 €** (Coût total des commissions : **49.61 €**) |
| **Gain Moyen (Average Win)** | **+6.06 €** (+2.25 %) |
| **Perte Moyenne (Average Loss)** | **-2.22 €** (-0.75 %) |
| **Payoff Ratio (Gain/Perte)** | **2.72** (Excellente asymétrie > 2.0) |
| **Profit Factor** | **1.58** (Gross Wins 194.02 € / Gross Losses 122.50 €) |
| **Espérance par Trade** | **+0.82 € / trade** (+0.35 %) |
| **Max Drawdown (Peak-to-Trough)** | **-38.76 €** |
| **Durée Moyenne de Rétention** | **21.07 heures** (1264.2 minutes) |

---

### B. Diagnostic d'Anomalie : Sur-Trading & Outlier SAP

1. **Impact d'un Outlier Positif Majeur** :
   - Un trade unique sur **SAP** le 06/07/2026 a généré **+91.76 € (+30.58 %)** en 34.76 minutes suite à un mouvement de prix brutal.
   - Hors cet outlier, les 86 autres trades cumulent un PnL de **-20.24 €**.
2. **Détection du Whipsawing (< 2 Heures)** :
   - **32 trades sur 87 (36.8 %)** ont été clôturés en moins de 2 heures.
   - En dehors de SAP, **31 de ces 32 trades ultra-courts sont perdants**, générant **-16.22 €** d'érosion sur faux signaux et mèches intraday.
3. **Fragilité des Stop-Loss Ultra-Serrés (0.5%)** :
   - Les Stop-Loss fixes de 0.5% (ex: `AMS.MC` 10m avec 0/7 wins) déclenchent des sorties prématurées sur le simple bruit du spread bid-ask ou des mèches sub-barres intraday.
   - À l'inverse, les setups possédant des Stop-Loss plus larges ou des timeframes plus mûrs (`randnleur` 10m avec SL 5.0% -> **+13.95 €**, `NVO` 45m -> **+8.45 €**) ont montré une excellente résilience.

---

## 2. Phase 2 : Plan d'Ajustement & Protocoles (À partir du 25/07/2026)

### A. Règle d'Ingénierie Quantique

Pour préserver l'avantage statistique sans dégrader les garanties de backtest :
- **Règle** : Aucune modification manuelle "au feeling" des hyperparamètres d'indicateurs.
- **Solution** : Basculer exclusivement sur les setups **déjà certifiés et consignés dans `docs/portfolio_deploiement_immediat.md`** (53 setups validés par Optuna & Walk-Forward Analysis).

---

### B. Sélection du Portefeuille Rectifié Phase 2 (8 Setups Champions)

Les 8 configurations suivantes ont été sélectionnées dans `docs/portfolio_deploiement_immediat.md` pour constituer le portefeuille certifié Phase 2 :

| Actif | Stratégie | Timeframe | Presets & Paramètres d'Indicateurs Certifiés | Rendement Mensuel Théorique | Role dans le Portefeuille |
| :--- | :--- | :---: | :--- | ---: | :--- |
| **`ZEAL.CO`** | `cybernetic_hilbert` | **45m** | `hilbert_smooth_period: 12, SL: 1.0%, TP: 12.0%` | **56.73 € / mois** | Fer de lance performance (Sharpe 3.36) |
| **`NVO`** | `momentum_based_zigzag` | **45m** | `rsi_period: 8, qqe_factor: 2.0, SL: 0.5%, TP: 11.9%` | **18.18 € / mois** | Swing trend-following mûr |
| **`GMAB`** | `3commas_bot` | **60m** | `ma_type1: DEMA, ma_type2: HMA, ma1: 8, ma2: 10` | **8.78 € / mois** | Croisement de moyennes mobiles lissées |
| **`dpwdeeur`** | `adaptive_volatility_trend` | **45m** | `length: 45, atr_len: 10, rsi_len: 10, atr_mult: 3.9` | **6.88 € / mois** | Filtre de volatilité adaptatif (Sharpe 1.22) |
| **`teniteur`** | `3commas_bot` | **30m** | `ma_type1: HEMA, ma_type2: SMA, ma1: 5, ma2: 38` | **6.83 € / mois** | Suivi de tendance moyen terme |
| **`akzanleur`** | `adaptive_volatility_trend` | **30m** | `length: 25, atr_len: 12, rsi_len: 7, atr_mult: 3.5` | **5.65 € / mois** | Régime de volatilité régulier (Sharpe 1.24) |
| **`SAP`** | `momentum_based_zigzag` | **30m** | `rsi_period: 25, qqe_factor: 5.6, SL: 4.8%, TP: 13.4%` | **2.29 € / mois** | Validation terrain Phase 1 confirmée |
| **`randnleur`** | `momentum_based_zigzag` | **10m** | `rsi_period: 18, qqe_factor: 6.0, SL: 5.0%, TP: 13.4%` | **0.84 € / mois** | Resilient sur 10m grâce au SL large 5% |

---

### C. Protocole de Clôture des Positions & Remise à Zéro (Clean Slate)

Afin d'étalonner la Phase 2 sur une base 100% vierge et mesurable :

1. **Clôture au Prix du Marché** : Clôturer les 4 positions ouvertes (`daideeur`, `AMS.MC`, `belgbeeur`, `randnleur`) au prix du marché actuel et insérer les transactions `SELL` d'achèvement de la Phase 1.
2. **Nettoyage de `paper_positions`** : Vider la table des positions actives.
3. **Mise à Jour de `paper_strategy_configs`** :
   - Désactiver toutes les anciennes configurations Phase 1 (`is_active = False`).
   - Activer et insérer les 8 configurations certifiées ci-dessus (`is_active = True`).
4. **Initialisation des Buckets de Capital** : Réinitialiser chaque bucket de capital par stratégie à **300.00 €**.

---

## 3. Pistes d'Amélioration & Automatisation Future (Feuille de Route)

### A. Garde-Fou Dynamique de Prix (`Max Entry Price` Automatique)
**✅ Intégré — 2026-07-27**

- **Problématique** : Actuellement, le paramètre `max_entry_price` est un nombre fixe en BDD (ex: 50.00 €, 100.00 €, 200.00 €, 300.00 €) servant de filtre anti-anomalie de cours (*bad data spike*). En cas de bull-run prolongé sur plusieurs mois, un ajustement manuel peut être nécessaire si le cours réel dépasse ce plafond.
- **Solution implémentée** :
  - Cap dynamique = `close_veille × (1 + buffer_pct)` avec buffer par défaut `+30 %` (`max_entry_price_buffer_pct`).
  - Repli automatique sur la limite statique BDD si la clôture de veille est incalculable.
  - Module : `backtest_engine/live/paper_trading/execution_guards.py:resolve_max_entry_price()`.
  - Surcharge via `indicator_params.max_entry_price_buffer_pct` (API Pydantic).

### B. Contrôles d'Exécution Génériques au Niveau `SignalExecutor`
**✅ Intégré — 2026-07-27**

1. **Minimum Holding Period (MHP)** : Intégrer un garde-fou universel interdisant la clôture d'une position par signal inverse si moins de 3 bougies consécutives se sont écoulées depuis l'ouverture (hors déclenchement du Stop-Loss dur).
   - **Implémenté** : `is_exit_blocked_by_mhp()` + `count_bars_since_entry()`. MHP=3 par défaut (`min_holding_bars`). Portée limitée aux signaux inverses (SL/TP/trailing prioritaires). `opened_at` ajouté à `paper_positions` (migration V3). Colonne `opened_at` renseignée à l'INSERT BUY (`CURRENT_TIMESTAMP`).
2. **Filtre de Régime de Volatilité (ATR Gate)** : Bloquer les déclenchements de signaux lorsque le marché évolue dans un canal de volatilité extrêmement resserré (ATR < 25e percentile).
   - **Implémenté** : `is_entry_blocked_by_atr_gate()` — ATR Wilder, lookback 100 bougies, percentile P25 par défaut. Fail-open si < 20 bougies fermées. Surcharge via `indicator_params.atr_gate_*`.
