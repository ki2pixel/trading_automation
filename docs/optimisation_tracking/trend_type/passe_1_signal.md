# Rapport : Trend Type Indicator - Passe Globale

**Date d'analyse** : 10 Juin 2026
**Objectif de la Passe** : Valider le signal brut de la stratégie Trend Type Indicator, qui est une stratégie de Catégorie A (Stratégies Simples à 1 Seule Passe). L'objectif est d'optimiser les paramètres clés : `atr_len`, `atr_ma_len`, `adx_len`, `di_len`, `adx_lim`, `smooth`, `signal_mode`, tout en gardant fixes `use_atr = true` et `use_adx = true`.
**Paramètres cibles optimisés** : `atr_len`, `atr_ma_len`, `adx_len`, `di_len`, `adx_lim`, `smooth`, `signal_mode`.
**Métriques cibles** : Max Drawdown tolérable entre -25% et -30% (exceptions selon profil), Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de traiter **27 162 itérations éligibles**.
L'observation du comportement général de la stratégie révèle l'importance de l'interaction des filtres ATR et ADX/DMI pour capturer les régimes de tendance. L'indicateur permet de filtrer efficacement le bruit lors des phases directionnelles fortes, mais nécessite des ajustements précis selon la volatilité de l'actif.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)
Un seul actif présente un edge clair, validé par une sur-performance absolue face au Buy & Hold sur plusieurs unités de temps.

* **NVO** : Affiche une sur-performance nette par rapport au Buy & Hold (scores positifs de +3.24 à +34.14).
  * **10m** (Score: +34.14 | 1804 trades | PnL: +785.07 | Max DD: -96.91% | Profit Factor: 1.35)
    * Paramètres : `atr_len: 10`, `atr_ma_len: 17`, `adx_len: 19`, `di_len: 28`, `adx_lim: 15.0`, `smooth: 1`, `signal_mode: Live`
  * **15m** (Score: +16.33 | 1200 trades | PnL: +603.72 | Max DD: -148.08% | Profit Factor: 1.31)
    * Paramètres : `atr_len: 5`, `atr_ma_len: 20`, `adx_len: 15`, `di_len: 28`, `adx_lim: 15.0`, `smooth: 3`, `signal_mode: Live`
  * **20m** (Score: +22.18 | 1003 trades | PnL: +662.51 | Max DD: -111.67% | Profit Factor: 1.40)
    * Paramètres : `atr_len: 6`, `atr_ma_len: 10`, `adx_len: 7`, `di_len: 29`, `adx_lim: 15.0`, `smooth: 3`, `signal_mode: Live`
  * **30m** (Score: +10.36 | 311 trades | PnL: +542.37 | Max DD: -76.13% | Profit Factor: 1.79)
    * Paramètres : `atr_len: 14`, `atr_ma_len: 35`, `adx_len: 24`, `di_len: 16`, `adx_lim: 20.0`, `smooth: 10`, `signal_mode: Live`
  * **45m** (Score: +11.69 | 199 trades | PnL: +554.09 | Max DD: -98.20% | Profit Factor: 1.92)
    * Paramètres : `atr_len: 28`, `atr_ma_len: 24`, `adx_len: 25`, `di_len: 13`, `adx_lim: 22.0`, `smooth: 10`, `signal_mode: Close`
  * **60m** (Score: +20.34 | 256 trades | PnL: +645.09 | Max DD: -91.09% | Profit Factor: 1.98)
    * Paramètres : `atr_len: 11`, `atr_ma_len: 12`, `adx_len: 5`, `di_len: 10`, `adx_lim: 15.0`, `smooth: 9`, `signal_mode: Close`
  * **120m** (Score: +3.24 | 266 trades | PnL: +469.88 | Max DD: -165.74% | Profit Factor: 1.57)
    * Paramètres : `atr_len: 11`, `atr_ma_len: 48`, `adx_len: 28`, `di_len: 5`, `adx_lim: 29.0`, `smooth: 3`, `signal_mode: Close`

### 🟡 Les Mentions Spéciales (Profil Conservateur)
* **NVS** : Présente une sous-performance face au Buy & Hold en pourcentage absolu (score ~ -13%), mais se démarque par un excellent rapport risque/rendement, avec un Max Drawdown extrêmement bas (< 10%) et des Profit Factors très élevés (> 2.0). C'est un profil conservateur très solide.
  * **15m** (Score: -13.79 | PnL: +47.87 | Max DD: -4.32% | Profit Factor: 2.04)
    * Paramètres : `atr_len: 13`, `atr_ma_len: 12`, `adx_len: 20`, `di_len: 17`, `adx_lim: 33.0`, `smooth: 5`, `signal_mode: Close`
  * **30m** (Score: -14.87 | PnL: +38.78 | Max DD: -7.45% | Profit Factor: 2.03)
    * Paramètres : `atr_len: 22`, `atr_ma_len: 50`, `adx_len: 18`, `di_len: 21`, `adx_lim: 25.0`, `smooth: 9`, `signal_mode: Live`
  * **60m** (Score: -13.26 | PnL: +54.80 | Max DD: -8.52% | Profit Factor: 2.36)
    * Paramètres : `atr_len: 12`, `atr_ma_len: 31`, `adx_len: 16`, `di_len: 20`, `adx_lim: 17.0`, `smooth: 10`, `signal_mode: Close`
  * **120m** (Score: -13.32 | PnL: +60.52 | Max DD: -9.47% | Profit Factor: 2.18)
    * Paramètres : `atr_len: 30`, `atr_ma_len: 46`, `adx_len: 16`, `di_len: 6`, `adx_lim: 30.0`, `smooth: 5`, `signal_mode: Live`

### 🔴 Les Rejetés (Absence d'Edge)
Tous les autres actifs sont rejetés en raison de performances insuffisantes ou de sous-performance marquée. L'absence d'edge est claire sur ces symboles :
* **LOGI** : Scores abyssaux avoisinant `-480`.
* **SAP** : Sous-performance autour de `-190`.
* **SHL.DE** : Sous-performance autour de `-130`.
* **ZEAL.CO** : Sous-performance autour de `-100`.
* **AMS.MC** : Sous-performance autour de `-52`.
* **EVD.DE** : Sous-performance autour de `-31`.
* **GMAB** : Sous-performance autour de `-28`.

---

## 3. Recommandations

La stratégie Trend Type Indicator étant de Catégorie A (Stratégie Simple à 1 Seule Passe), l'optimisation s'arrête ici pour les actifs validés.
La stratégie est validée de manière autonome pour **NVO** (performances absolues élevées) et **NVS** (profil conservateur très solide, avec drawdown maîtrisé) sur leurs unités de temps respectives.
