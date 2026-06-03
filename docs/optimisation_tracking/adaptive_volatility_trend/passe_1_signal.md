# Rapport : Adaptive Volatility Trend - Passe 1 (Le Signal de Base)

**Date d'analyse** : 02 Juin 2026
**Objectif de la Passe** : Valider l'indicateur Core de tendance adaptative par volatilité sans filtres. Les filtres optionnels (`use_rsi_filter = false`, `use_volume_filter = false`) sont bloqués.
**Paramètres cibles optimisés** : `length`, `atr_len`, `atr_mult`.

---

## 1. Analyse Globale des Résultats

Le tableau suivant présente la synthèse consolidée des résultats par actif :

| Actif | TF | Éligibles | Score (vs B&H) | Net PnL | Profit Factor | Max DD | Trades | Paramètres |
|---|---|---|---|---|---|---|---|---|
| **NVS** | 10m | 400 | **+14.45%** | 328.70 | 1.82 | -51.31 | 255 | `len=26, atr_len=11, atr_mult=2.0` |
| **NVS** | 45m | 350 | **+10.47%** | 292.14 | 2.88 | -38.93 | 68 | `len=22, atr_len=12, atr_mult=2.2` |
| **NVS** | 15m | 200 | **+9.56%** | 278.70 | 1.64 | -88.63 | 222 | `len=30, atr_len=21, atr_mult=1.6` |
| **NVS** | 20m | 132 | **+8.46%** | 264.68 | 1.51 | -68.88 | 309 | `len=11, atr_len=12, atr_mult=2.1` |
| **NVS** | 60m | 200 | **+7.92%** | 266.66 | 2.78 | -55.26 | 58 | `len=17, atr_len=7, atr_mult=3.7` |
| **NVS** | 30m | 200 | **+2.13%** | 208.70 | 1.81 | -68.74 | 76 | `len=29, atr_len=10, atr_mult=1.6` |
| **NVS** | 5m | 148 | **+1.16%** | 193.15 | 1.29 | -69.15 | 430 | `len=29, atr_len=15, atr_mult=4.0` |
| **GMAB** | 5m | 136 | **+1.11%** | 311.52 | 1.57 | -161.16 | 197 | `len=36, atr_len=28, atr_mult=3.2` |
| **EVD.DE** | 5m | 450 | -5.96% | 259.15 | 1.85 | -47.50 | 161 | `len=23, atr_len=25, atr_mult=3.2` |
| **EVD.DE** | 15m | 250 | -8.06% | 232.14 | 2.24 | -52.82 | 69 | `len=23, atr_len=9, atr_mult=2.8` |
| **EVD.DE** | 20m | 200 | -13.97% | 171.20 | 1.70 | -63.02 | 79 | `len=12, atr_len=8, atr_mult=2.3` |
| **NVO** | 1m | 200 | -16.18% | 274.63 | 2.50 | -24.51 | 248 | `len=28, atr_len=8, atr_mult=3.0` |
| **AMS.MC** | 10m | 250 | -27.22% | 304.32 | 1.55 | -127.30 | 182 | `len=33, atr_len=8, atr_mult=1.4` |
| **SHL.DE** | 30m | 200 | -91.39% | 475.45 | 3.02 | -64.78 | 93 | `len=24, atr_len=21, atr_mult=1.5` |
| **ZEAL.CO** | 1m | 200 | -114.33% | 270.36 | 2.22 | -49.40 | 139 | `len=34, atr_len=22, atr_mult=1.6` |
| **SAP** | 30m | 200 | -158.13% | 460.91 | 1.90 | -93.45 | 222 | `len=10, atr_len=28, atr_mult=1.5` |
| **LOGI** | 15m | 200 | -420.24% | 680.33 | 3.76 | -57.75 | 84 | `len=42, atr_len=11, atr_mult=3.6` |
| **FPE.DE** | *Toutes* | 0 | N/A | N/A | N/A | N/A | N/A | Aucun |

---

## 2. Analyse Narrative

* **L'échec de FPE.DE** : L'actif est totalement rejeté avec **0 itération éligible** sur toutes les timeframes. Cela s'explique par l'incapacité de la stratégie sur cet actif à satisfaire les contraintes strictes du moteur (comme le `min_closed_trades = 50` ou `max_drawdown = -25%`). 
* **L'Edge Directionnel de NVS** : On observe un comportement directionnel fort et une robustesse de la tendance sur **NVS**, qui sur-performe par rapport au Buy & Hold sur l'ensemble des timeframes (10m, 15m, 20m, 30m, 45m, 60m et 5m). La tendance est très nette, avec un meilleur score sur 10m (+14.45%).
* **Le Bruit sur le Reste du Panel** : La plupart des actifs étudiés souffrent du manque de filtrage lors de cette Passe 1. Sans filtres (ex: RSI, volume), la stratégie génère de multiples faux signaux en phase de range, d'où les sous-performances globales observées (scores négatifs face au B&H). Seul **GMAB** parvient à limiter la casse et affiche un léger edge sur 5m (+1.11%).

---

## 3. Recommandations pour la Passe 2

1. **Validation et Gels d'Actifs** : 
   * Valider uniquement **NVS** (timeframes 10m, 15m, 20m, 45m, 60m) et **GMAB** (5m) pour la Passe 2.
   * Exclure ou geler les autres actifs qui génèrent trop de faux signaux.
2. **Configurations pour la Passe 2** :
   * **Bloquer les configurations core trouvées** : Geler les paramètres `length`, `atr_len` et `atr_mult` sur les valeurs identifiées lors de cette Passe 1.
   * **Paramètres à optimiser (Filtres)** : Planifier l'optimisation des filtres additionnels (RSI et volume) pour nettoyer les faux signaux et améliorer l'entrée en tendance.
