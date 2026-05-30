# Phase 4 — Synthèse WFA Hold-Out 1m & Recommandations

**Date d'exécution:** 2026-05-21
**Stratégie:** `noise_boundary_intraday`
**Granularité:** 1 minute
**Période:** rolling 2y IS / 1y OOS (dernier fold par ticker)

---

## 1. Résultats WFA Baseline (dernier fold)

| Ticker | Devise | Sharpe IS | Sharpe OOS | CAGR OOS | MDD OOS | Trades OOS | Verdict |
|--------|--------|-----------|------------|----------|---------|------------|---------|
| AMS.MC | EUR | -0.747 | **-0.295** | -69.3% | -86.7% | 20 | ❌ |
| GMAB | USD | 1.182 | **1.992** | +312.9% | -96.5% | 608 | ⚠️ |
| LOGI | CHF | -0.193 | **-0.190** | -49.5% | -75.3% | 9 | ❌ |
| NVO | DKK | -0.419 | **-0.041** | -30.7% | -61.9% | 12 | ❌ |
| NVS | CHF | 0.325 | **-0.158** | -90.2% | -96.6% | 41 | ❌ |
| SAP | EUR | 0.089 | **0.545** | +107.6% | -69.8% | 41 | ⚠️ |
| SHL.DE | EUR | -0.196 | **-0.864** | -65.1% | -69.2% | 4 | ❌ |
| ZEAL.CO | DKK | 2.384 | **4.715** | +721663% | -67.1% | 3129 | ⚠️ |

**Moyennes par devise:**
- **EUR** (3 tickers): Sharpe OOS = -0.205 → **dégradé**
- **CHF** (2 tickers): Sharpe OOS = -0.174 → **dégradé**
- **DKK** (2 tickers): Sharpe OOS = 2.337 → **tiré par ZEAL.CO**
- **USD** (1 ticker): Sharpe OOS = 1.992 → **acceptable**

**Sharpe OOS moyen global:** 0.713 (min=-0.864, max=4.715)

---

## 2. Diagnostic Principal

### 2.1 Trop peu de trades
Le nombre de trades OOS est extrêmement faible pour la plupart des tickers (4–41 trades sur 1 an). Pour comparaison, les actions indiennes testées précédemment généraient 300–3000 trades/an.

### 2.2 Bandes trop larges pour la volatilité réelle
L'analyse de volatilité journalière sur les périodes IS montre que la volatilité moyenne de ces actifs européens est faible (0.87%–3.0%). Avec `volatility_multiplier_enter=0.5`, les bandes d'entrée sont positionnées à ±(0.5 × volatilité). Pour un actif comme NVS (vol=0.87%), cela donne des bandes à ±0.43% — ce qui est rarement dépassé en une séance.

**Table de correspondance volatilité → trades:**

| Ticker | Volatilité journalière moyenne (IS) | Trades OOS (baseline) | Interprétation |
|--------|-----------------------------------|-----------------------|----------------|
| NVS | 0.87% | 41 | Bandes à ±0.43% — trop rarement atteintes |
| SAP | 1.23% | 41 | Bandes à ±0.62% — peu de franchissements |
| LOGI | 1.44% | 9 | Bandes à ±0.72% — très peu de franchissements |
| AMS.MC | 1.44% | 20 | Bandes à ±0.72% — rarement atteintes |
| SHL.DE | 1.59% | 4 | Bandes à ±0.80% — quasi jamais atteintes |
| NVO | 1.80% | 12 | Bandes à ±0.90% — rarement atteintes |
| GMAB | 2.09% | 608 | Bandes à ±1.05% — biotech volatile, plus de signaux |
| ZEAL.CO | 3.02% | 3129 | Bandes à ±1.51% — action très volatile, signaux fréquents |

**Conclusion:** Le paramètre `volatility_multiplier_enter=0.5` est adapté aux actifs à haute volatilité (ZEAL.CO, GMAB) mais beaucoup trop élevé pour les actifs à faible/moyenne volatilité (NVS, SAP, LOGI, etc.).

### 2.3 MDD catastrophique
Le drawdown maximum atteint -60% à -96% sur presque tous les tickers. Cela indique que même quand la stratégie génère des trades, le sizing (`target_daily_volatility=0.018`) est trop agressif et les pertes sont amplifiées.

---

## 3. Recommandations Paramétriques

### 3.1 Ajustement par profil de volatilité
Plutôt qu'un paramètre fixe universel, il est recommandé d'adapter `volatility_multiplier_enter` à la volatilité historique de l'actif:

| Profil de volatilité | `volatility_multiplier_enter` recommandé | Exemples |
|----------------------|------------------------------------------|----------|
| Très faible (< 1.0%) | 0.20 – 0.30 | NVS (0.87%) |
| Faible (1.0% – 1.5%) | 0.25 – 0.35 | SAP, LOGI, AMS.MC |
| Moyenne (1.5% – 2.5%)| 0.30 – 0.50 | SHL.DE, NVO, GMAB |
| Élevée (> 2.5%) | 0.40 – 0.60 | ZEAL.CO |

### 3.2 Réduction du sizing
Réduire `target_daily_volatility` de 0.018 à **0.010–0.012** pour limiter le MDD. Un MDD de -60% à -96% est inacceptable pour le trading en production.

### 3.3 Paramètres suggérés (approche conservatrice)

Pour les actifs EUR/CHF à faible volatilité:
```python
{
    "lookback_days": 17,
    "volatility_multiplier_enter": 0.25,  # vs 0.50 baseline
    "volatility_multiplier_exit": 0.08,   # vs 0.10 baseline
    "target_daily_volatility": 0.012,     # vs 0.018 baseline
    "exit_mode": "combined",
    "stoploss_ladder_step0": -0.015,
    "stoploss_ladder_step1": -0.020,
    "stoploss_ladder_ratio0": 0.8,
    "takeprofit_ladder_step0": 0.020,
}
```

### 3.4 Alternative : granularité 5m
Les résultats précédents (actions indiennes) ont montré un Sharpe OOS moyen de 4.877 en 5m. Tester la même stratégie en 5m sur ces 8 tickers pourrait montrer une meilleure robustesse car :
- Les bandes sont moins bruitées à 5m
- Le nombre de faux signaux est réduit
- Le sizing est mieux calibré

---

## 4. Verdict

### Évaluation des critères de Phase 4

| Critère | Statut | Commentaire |
|---------|--------|-------------|
| Validation hold-out | ✅ Fait | 8 tickers, dernier fold, 1m |
| Baseline Sharpe > 0.5 | ❌ Non | Seuls GMAB (1.99), ZEAL.CO (4.72), SAP (0.55) dépassent 0.5 |
| MDD acceptable (< 30%) | ❌ Non | Tous les tickers ont MDD > 60% |
| Nombre de trades suffisant | ❌ Non | 6/8 tickers ont < 50 trades/an |
| Stabilité par devise | ❌ Non | EUR et CHF fortement négatifs |

### Verdict final : **NO-GO** (avec piste CONDITIONAL-GO)

**NO-GO en l'état** — Les paramètres baseline de Phase 3 ne sont pas adaptés à ces actifs en 1m. Les performances sont catastrophiques pour EUR et CHF, et le MDD est trop élevé partout.

**CONDITIONAL-GO possible si :**
1. Les paramètres sont ajustés par profil de volatilité (cf. §3)
2. Le sizing est réduit pour limiter le MDD sous 30%
3. Une nouvelle validation WFA est effectuée avec les paramètres ajustés
4. La granularité 5m est explorée comme alternative

---

## 5. Prochaines Étapes Recommandées

1. **Ajustement paramétrique :** Tester les paramètres suggérés au §3.3 sur SAP (EUR) et LOGI (CHF) avec un backtest OOS rapide.
2. **Optimisation bayésienne :** Lancer une optimisation ciblée (50–100 trials) par profil de volatilité (faible vs élevée) plutôt que par devise.
3. **Test 5m :** Exécuter le même hold-out WFA en 5m pour comparer la robustesse.
4. **Paper trading :** Si les paramètres ajustés montrent un Sharpe OOS > 0.8 et MDD < 30%, lancer le paper trading sur 2–4 semaines.
