# Rapport de Vérification et de Fidélité : Zarattini Original vs. `noise_boundary_intraday`

**Auteurs** : Antigravity Quant Team  
**Date d'émission** : 24 mai 2026  
**Statut** : Validé et Clôturé  

Ce rapport présente l'audit documentaire et algorithmique approfondi ainsi que les résultats des tests de régression automatisés menés sur notre implémentation Python de la stratégie **Noise Boundary Intraday** confrontée au code original MATLAB de **Carlo Zarattini et al.** (`backtesting_beatthemarket.py`).

---

## 1. Confirmation de l'Intégration des 4 Corrections de l'Audit

Nous confirmons que les quatre chantiers correctifs identifiés dans l'audit initial ont bien été intégrés dans notre code Python ([noise_boundary_intraday.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategies/noise_boundary_intraday.py) et [broker.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/broker.py)) :

1. **Calcul de `sigma_open`** : La courbe de bruit intra-journalière minute par minute est correctement calculée. Notre implémentation utilise une matrice de pivotement par heure de la journée et date, ce qui est mathématiquement équivalent à la logique de groupement par minute de Zarattini, avec un décalage d'un jour (`shift(1)`) pour écarter tout biais d'anticipation.
2. **Ancrage dynamique (Gaps Overnight)** : Le code intègre parfaitement l'ancrage dynamique sur la borne maximale ou minimale entre le prix d'ouverture (`Open`) et la clôture de la veille (`prev_close`) :
   - Bande supérieure ancrée sur `max(Open, prev_close)`.
   - Bande inférieure ancrée sur `min(Open, prev_close)`.
3. **Filtre VWAP à l'entrée** : Les conditions d'entrée en position appliquent strictement le filtre de tendance VWAP intra-journalier :
   - Signal Long valide uniquement si `price > UB` **ET** `price > VWAP`.
   - Signal Short valide uniquement si `price < LB` **ET** `price < VWAP`.
4. **Plafonnement du sizing (Broker)** : La méthode `broker.calculate_position_size` n'annule plus le trade lorsque le levier théorique requis pour atteindre la volatilité cible dépasse le levier maximal configuré (`max_leverage`). Le broker écrête désormais proprement la taille de la position au levier maximum autorisé et exécute la transaction.

---

## 2. Divergences Résiduelles Identifiées

Notre vérification croisée approfondie a révélé cinq écarts résiduels entre l'implémentation originale et la nôtre. Le tableau ci-dessous les répertorie avec une évaluation de leur niveau d'impact :

| Réf | Axe algorithmique / Divergence | Description technique | Niveau d'impact |
| :--- | :--- | :--- | :---: |
| **A** | **Sizing Volatility Mismatch** | L'original utilise la volatilité historique **quotidienne** des rendements sur 15 jours (`spy_dvol`) pour dimensionner les positions. Notre code passe la volatilité **intra-journalière** (`sigma_open`) au broker pour le sizing, ce qui sur-dimensionne massivement les positions au début de la journée. | **CRITIQUE** |
| **B** | **Minute execution lag (1-bar shift)**| L'original évalue le signal à la minute $t-1$ (ex: 09:59) pour initier la position à la minute $t$ (ex: 10:00). Notre code évalue le signal à la minute $t$ (ex: 10:00) sous réserve de `trade_freq` et exécute l'ordre à la minute $t+1$ (ex: 10:01) via `execute_on_next_bar=True`. | **MAJEUR** |
| **C** | **Commission structure discrepancy** | L'original applique un plancher de frais par ordre : `max(0.35, 0.0035 * shares)`. Notre broker applique un montant fixe par transaction (`commission_fixed_long`), qui ne s'ajuste pas au nombre d'actions négociées. | **MAJEUR** |
| **D** | **min_periods dans rolling** | L'original utilise `min_periods = lookback - 1` pour le rolling de `sigma_open`, lui permettant de démarrer le trading un jour plus tôt. Notre code utilise le `min_periods` par défaut (soit égal au `window`). | **MINEUR** |
| **E** | **Ajustement dividende** | L'original retranche les dividendes du cours de clôture de la veille pour ancrer les bandes : `y_close = y_close_raw - dividend`. Notre code n'applique pas cet ajustement sur l'ancrage. | **MINEUR** |

---

## 3. Focus : Le Point Critique du Sizing de Volatilité

Cette divergence constitue la cause principale des écarts de performance constatés en backtest :

- **Dans le modèle original** : La volatilité historique $spx\_vol$ est constante tout au long de la journée de trading (c'est l'écart-type des rendements quotidiens sur 15 jours, ex: $1.5\%$). Le levier calculé est stable (ex: $0.02 / 0.015 = 1.33x$).
- **Dans notre implémentation** : La volatilité passée au broker est `sigma_open` (l'écart absolu cumulé depuis l'ouverture). Cette valeur commence proche de $0$ à 09:35 (ex: $0.07\%$) et n'augmente que très progressivement. En conséquence, le levier théorique calculé à l'ouverture est démesurément élevé (ex: $0.02 / 0.0007 = 28.5x$).
- **Impact** : Ce levier astronomique est systématiquement écrêté par le cap de levier maximal du broker (`max_leverage = 4.0x`). Cela signifie que notre robot négocie presque systématiquement avec le levier maximal disponible en début de journée, s'exposant à un risque de capital beaucoup plus fort et dénaturant le ciblage de volatilité théorique de Zarattini.

---

## 4. Résultats des Tests de Régression

Les tests de régression automatisés implémentés dans `tests/regression/test_zarattini_fidelity.py` valident scientifiquement ces observations sur un dataset synthétique de 15 jours :

### a. `test_a_indicator_equivalence` (SUCCÈS)
- **Objectif** : Valider la conformité mathématique de la courbe de volatilité `sigma_open` et des bandes `UB`/`LB`.
- **Constat** : Une fois les phases d'initialisation passées (à partir du jour 6, en raison de l'écart `min_periods`), **les valeurs de volatilité et les bandes UB et LB calculées par les deux moteurs sont rigoureusement identiques** (tolérance de $10^{-8}$).
- **Validation** : Le pivot matriciel optimisé en Python reproduit à la perfection la logique MATLAB originale.

### b. `test_b_entry_signal_comparison` (SUCCÈS)
- **Objectif** : Valider les déclencheurs bruts bar-par-bar.
- **Constat** : Les signaux d'entrée bruts (franchissement de bande + filtre VWAP) correspondent exactement à chaque minute du dataset, confirmant la fidélité de notre logique de signal.

### c. `test_c_sizing_volatility_investigation` (SUCCÈS)
- **Objectif** : Mesurer l'écart de sizing lié au choix de la volatilité.
- **Constat** (Jour 8 sur dataset synthétique) :
  - Volatilité quotidienne originale (`spy_dvol`) : $1.635\%$, Levier original : $1.22x$, Actions : **1211**.
  - Notre volatilité intra-journalière à 09:35 : $0.074\%$, Levier : **4.00x** (Capped), Actions : **3961**.
  - Notre volatilité intra-journalière à 12:30 : $0.558\%$, Levier : **3.58x**, Actions : **3548**.
- **Validation** : Ce test démontre que notre robot prend des positions **3.2 fois plus grandes** que le modèle de Zarattini à l'ouverture, confirmant le point critique de sizing.

### d. `test_d_simplified_strategy_regression` (SUCCÈS)
- **Objectif** : Valider le PnL brut et le timing de l'exposition.
- **Constat** :
  - La divergence de sizing et le décalage temporel de 1 minute créent des écarts de PnL massifs d'un jour à l'autre.
  - La désynchronisation temporelle de 1 minute est confirmée : à 10:00, le modèle de Zarattini a déjà activé son exposition suite au signal calculé à 09:59. Notre modèle évalue le signal à 10:00 et n'ouvre la position qu'à 10:01 (barre suivante), manquant le PnL de la première minute.

---

## 5. Recommandations d'Action

Pour amener notre outil à un niveau de réplication parfait avec les travaux de Zarattini tout en conservant les optimisations avancées de Maróy, nous recommandons le plan d'action suivant :

1. **Introduire un sélecteur de volatilité pour le dimensionnement** :
   - Ajouter un paramètre `sizing_volatility_type: Literal["daily", "intraday"]` dans les configurations de stratégie.
   - En mode `"daily"`, calculer l'écart-type glissant quotidien des rendements sur la période de lookback et l'utiliser comme dénominateur constant pour toute la journée.
2. **Harmoniser le timing des signaux (Lag de 1 minute)** :
   - Ajuster la logique de trading discrète pour que les signaux soient évalués sur la barre de clôture précédant la période de trading de fréquence (ex: évaluer à la minute $t-1$ pour une exécution à $t$).
3. **Mettre à niveau le modèle de commission du Broker** :
   - Permettre la configuration d'une commission avec plancher minimal proportionnelle aux actions dans `broker.py` : `max(min_comm, commission_rate * shares)`.
4. **Intégrer les dividendes dans l'ancrage** :
   - Incorporer une série de dividendes quotidiens au sein de `compute_noise_boundary` pour corriger `prev_close` lors du détachement du coupon.
