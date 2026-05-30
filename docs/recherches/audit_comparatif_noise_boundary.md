# Rapport d'Audit Comparatif : Zarattini (MATLAB) → Ákos Maróy → `noise_boundary_intraday.py`

## Introduction
Ce document présente un audit documentaire et algorithmique approfondi de la stratégie **Noise Boundary Intraday** (Intraday Momentum). L'objectif est de reconstruire fidèlement la logique originale formulée sous MATLAB par **Carlo Zarattini et al.** (2024), de la confronter aux améliorations et aux optimisations d'**Ákos Maróy** (2025), puis d'évaluer la fidélité, la pertinence et les écarts de notre implémentation Python présente dans [noise_boundary_intraday.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategies/noise_boundary_intraday.py).

---

## 1. Extraction et Documentation de la Logique MATLAB de Zarattini

L'analyse du code MATLAB original de Zarattini montre une logique rigoureuse de modélisation de la volatilité intra-journalière ("zone de bruit") et de gestion de l'exposition. Voici les piliers de cette implémentation :

### A. Calcul de la volatilité intra-journalière (`sigma_open`)
La volatilité de Zarattini n'est pas une simple volatilité quotidienne historique. C'est une **courbe de bruit intra-journalière minute par minute** calculée comme suit :
1. **Écart à l'ouverture (`move_open`)** : Pour chaque minute $t$ de la journée (de 1 à 390, correspondant aux minutes écoulées depuis 09:30), on calcule l'écart absolu du cours par rapport à l'ouverture de la journée :
   $$\text{move\_open}_t = \left| \frac{\text{Close}_t}{\text{Open}_{9:30}} - 1 \right|$$
2. **Moyenne mobile (`sigma_open`)** : Pour chaque minute de la journée de trading (1 à 390), on calcule la moyenne mobile simple sur **14 jours** de la valeur `move_open` à cette minute spécifique des jours précédents.
3. **Lag de 1 jour** : Un lag de 1 jour (`lag_TS(..., 1)`) est appliqué pour s'assurer que la courbe de bruit de la journée en cours est uniquement basée sur les données historiques clôturées des 14 jours précédents. Elle modélise le profil type de l'expansion de la volatilité au fil de la journée.

### B. Ancrage et ajustement des bandes (`UB` / `LB`)
Pour éviter que les écarts d'ouverture (overnight gaps) ne déclenchent des signaux de momentum fictifs, les bandes sont dynamiquement ajustées par rapport à la clôture de la veille et aux dividendes :
1. **Clôture ajustée du dividende (`y_close`)** : La clôture de la veille est diminuée du dividende détaché aujourd'hui :
   $$\text{y\_close} = \text{y\_close\_raw} - \text{dividend}$$
2. **Bande supérieure (Upper Band - UB)** :
   $$\text{UB}_t = \max(\text{Open}_{9:30}, \text{y\_close}) \times (1 + \text{band\_mult} \times \text{sigma\_open}_t)$$
3. **Bande inférieure (Lower Band - LB)** :
   $$\text{LB}_t = \min(\text{Open}_{9:30}, \text{y\_close}) \times (1 - \text{band\_mult} \times \text{sigma\_open}_t)$$
   
*Note : Si le marché ouvre sur un gap haussier, la bande supérieure s'ancre sur le cours d'ouverture (Open), tandis que si le marché ouvre sur un gap baissier, la bande inférieure s'ancre sur l'Open.*

### C. Filtre VWAP à l'entrée
Pour valider le momentum directionnel, un filtre basé sur le Volume Weighted Average Price (VWAP) de la journée en cours est **strictement obligatoire** pour toute entrée :
- **Signal Long** : $\text{Close}_t > \text{UB}_t$ **ET** $\text{Close}_t > \text{VWAP}_t$
- **Signal Short** : $\text{Close}_t < \text{LB}_t$ **ET** $\text{Close}_t < \text{VWAP}_t$

### D. Fréquence de trading et rebalancement discret
La stratégie n'est pas évaluée de manière continue pour les entrées/sorties :
1. Les signaux ne sont vérifiés qu'aux minutes multiples de `trade_freq` (ex. toutes les 30 minutes : 10:00, 10:30, etc.).
2. L'exposition calculée à ces instants est maintenue constante (reportée) sur toutes les minutes intermédiaires.
3. Un lag de 1 période est appliqué à l'exposition (`lag_TS(exposure, 1)`) car le signal calculé à la clôture de la minute $t$ n'est appliqué pour le trading qu'au début de la minute $t+1$.

### E. Dimensionnement des positions (Sizing)
Zarattini propose deux méthodes basées sur l'AUM à la clôture de la veille ($AUM_{d-1}$) et le prix d'ouverture de la journée en cours ($\text{Open}_{9:30}$) :
1. **Full Notional** : Leverage fixe de 1.
   $$\text{Shares} = \text{round}\left( \frac{\text{AUM}_{d-1}}{\text{Open}_{9:30}}, 0 \right)$$
2. **Volatility Target (`vol_target`)** : Le levier s'adapte à la volatilité historique quotidienne sur 14 jours du SPY ($spx\_vol$), plafonné par un levier maximum :
   $$\text{Leverage} = \min\left(\frac{\text{target\_vol}}{\text{spx\_vol}}, \text{max\_leverage}\right)$$
   $$\text{Shares} = \text{round}\left( \frac{\text{AUM}_{d-1}}{\text{Open}_{9:30}} \times \text{Leverage}, 0 \right)$$
   *(Dans le papier, $\text{target\_vol} = 2\%$ et $\text{max\_leverage} = 4$)*.

### F. Calcul du PnL et structure des coûts
Le PnL est calculé minute par minute sur l'exposition active :
- **PnL brut** : $\sum (\text{exposure}_t \times (\text{Close}_t - \text{Close}_{t-1})) \times \text{Shares}$
- **Commissions** : $0,0035$ USD par action, avec un minimum de $0,35$ USD par transaction (ordre de rebalancement ou de sortie).
- Les trades ouverts restants sont systématiquement clôturés à la fin de la journée.

---

## 2. Analyse du Papier d'Ákos Maróy (Réinterprétation & Améliorations)

Dans son étude d'avril 2025, Ákos Maróy propose une réinterprétation moderne de la stratégie Noise Boundary en exploitant un outil de backtest vectoriel de pointe (**VectorBT Pro**) et en appliquant une optimisation globale des hyperparamètres (**Optuna**).

### A. Paramètres optimisés par Maróy (Synthèse des Résultats)
Maróy démontre que la stratégie originale peut être considérablement optimisée en s'adaptant à des horizons plus courts et à des techniques de sortie avancées. Le tableau suivant présente les performances des meilleures configurations sur l'ETF **QQQ** (période 2014-2024, barres de 1 seconde) :

| Stratégie d'Exit | Sharpe Ratio | Alpha | Beta | Ann. Return | Ann. Vol | Max DD |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Boundary & VWAP #1** | 2.11 | 26% | -4% | 37% | 17% | 18% |
| **Boundary with diff. exit #1** | 2.76 | 36% | -6% | 51% | 19% | 22% |
| **VWAP #1 (Exclusif)** | 3.16 | 39% | 1% | 58% | 18% | 15% |
| **VWAP & Ladder #1** | 3.08 | 31% | -1% | 45% | 15% | 11% |
| **Ladder #1 (Exclusif)** | **3.34** | **41%** | -5% | **60%** | 19% | **13%** |

*Constat majeur : Les stratégies utilisant les sorties en VWAP et/ou Ladder (stop suiveur par paliers) surclassent très largement le modèle à sortie temporelle simple de Zarattini, atteignant des Sharpe > 3,0.*

### B. Différences de formulation introduites par Maróy
1. **Sorties Élaborées (Exit Strategies)** :
   - **Sortie VWAP** : Clôture immédiate dès que le cours croise le VWAP à contre-tendance.
   - **Sortie de bande différenciée** : Utilisation d'une bande de sortie (exit) plus étroite que la bande d'entrée (entry) pour verrouiller plus vite les gains ou limiter les pertes.
   - **Sortie Ladder (Échelle)** : Stratégie à 2 paliers avec vente partielle de 50% au premier objectif de profit (Step 0) et remontée du stop loss au prix d'entrée (breakeven) pour la quantité restante. Les seuils de profit/perte sont définis par rapport à un paramètre de risque global $r = 2\%$ de l'AUM.
2. **Résolution temporelle et exécution fine** :
   - Passage de barres de 1 minute à des **barres de 1 seconde**.
   - Utilisation des extrêmes de barre (High pour entrée Long / sortie Short ; Low pour entrée Short / sortie Long) pour valider les déclenchements, au lieu du seul cours de clôture.
3. **Dimensionnement dynamically ajusté** :
   - Calcul des parts sur la base du cours actuel lors du trade ($\text{Price}_t$) et non sur le cours d'ouverture ($\text{Open}_{9:30}$).
   - Remplacement de l'AUM par la marge disponible actualisée ($\text{AM}$), avec prise en compte de contraintes asymétriques réalistes : marge exigée de **25% pour les longs** (levier max 4.0x) et **30% pour les shorts** (levier max 3.33x).
4. **Simplification** : Suppression des ajustements de dividendes sur le cours de clôture de la veille.

### C. Écarts conceptuels majeurs
- **Régime temporel hybride** : Chez Zarattini, l'intégralité du système est discrète (rebalancement et signal toutes les 30 minutes). Chez Maróy, **les entrées restent discrètes** (cadencées par la fréquence de trading, ex. toutes les 30 minutes), mais **les sorties sont continues** (analysées à chaque seconde grâce aux règles VWAP et Ladder).
- **Lookback court** : Les paramètres optimisés de Maróy révèlent que le lookback optimal de volatilité n'est pas de 14 ou 90 jours, mais extrêmement court (**de 2 à 8 jours**), permettant à la bande de bruit de s'adapter presque instantanément aux changements récents de régime de marché.

---

## 3. Audit de `noise_boundary_intraday.py` et du Simulator

L'analyse de notre code Python [noise_boundary_intraday.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategies/noise_boundary_intraday.py) confrontée aux deux cadres théoriques met en lumière des forces structurelles évidentes mais aussi des **divergences de logique critiques** qui altèrent significativement la fidélité de nos backtests par rapport à Zarattini et Maróy.

### A. Volet Volatilité & Profil Intra-journalier : DIVERGENCE CRITIQUE
- **MATLAB (Zarattini/Maróy)** : Utilise `sigma_open`, une **courbe de bruit intra-journalière** de dimension $1 \times 390$ qui s'élargit progressivement au fil de la journée pour modéliser le profil naturel d'expansion de la volatilité intraday depuis l'ouverture.
- **Python (Notre code)** :
  ```python
  daily_close = bars["close"].resample("D").last().dropna()
  daily_returns = daily_close.pct_change()
  daily_vol = daily_returns.rolling(window=lookback_days).std()
  # Mappé directement sur toute la journée
  mapped_vol = daily_vol_for_today.reindex(normalized_index).values
  ```
  Notre code calcule un écart-type glissant des **rendements quotidiens**, qu'il applique comme un scalaire constant pour toute la journée.
- **Impact majeur** : Nos bandes d'entrée/sortie sont **parfaitement horizontales et statiques** tout au long de la journée de trading. Elles ne s'élargissent pas au fil du temps. Cela signifie que le seuil de bruit à franchir à 09:35 (5 minutes après l'ouverture) est identique à celui de 15:30, ce qui contredit totalement le principe fondateur de la "zone de bruit" temporelle de Zarattini.

### B. Volet Ancrage des Bandes : DIVERGENCE MAJEURE
- **MATLAB (Zarattini)** : S'ancre au maximum ou minimum de l'Open et de la clôture de la veille ajustée :
  $$\text{UB} = \max(\text{Open}, \text{y\_close\_adj}) \times (1 + \text{mult} \times \sigma)$$
- **Python (Notre code)** :
  ```python
  results["upper_enter"] = daily_open * (1 + multiplier_enter * mapped_vol)
  results["lower_enter"] = daily_open * (1 - multiplier_enter * mapped_vol)
  ```
  Notre code s'ancre **uniquement** sur le cours d'ouverture de la journée (`daily_open`).
- **Impact majeur** : Les overnight gaps ne sont absolument pas gérés. Si une action ouvre sur un fort gap haussier, notre code s'ancre sur ce prix d'ouverture élevé sans incorporer le gap dans la bande de bruit. Inversement, si le gap est inclus ou non, cela modifie radicalement les signaux d'ouverture et génère des signaux erronés.

### C. Filtre VWAP à l'entrée : DIVERGENCE MAJEURE
- **MATLAB (Zarattini)** : Le filtre `price > VWAP` (long) ou `price < VWAP` (short) est intégré à la condition de signal d'entrée.
- **Python (Notre code)** :
  ```python
  if not np.isnan(upper) and long_trigger > upper and direction in ("Long & Short", "Long only"):
      qty = broker.calculate_position_size(...)
  ```
  Le filtre VWAP n'est **jamais vérifié à l'entrée** dans notre code Python. La série VWAP is uniquement calculée et injectée pour les règles de sortie (`VWAPExitRule`).
- **Impact majeur** : La stratégie peut entrer en position longue au-dessus de la bande supérieure alors même que le cours est sous le VWAP (marché baissier), ce qui contredit le filtre de tendance primaire exigé par Zarattini.

### D. Algorithme de Dimensionnement (Sizing) & Rejet de Levier : DIVERGENCE CONTEXTUELLE
- **MATLAB (Zarattini)** : Plafonne le levier à `max_leverage` via la fonction `min(...)` mais exécute toujours le trade.
- **Python (Notre code dans `broker.py`)** :
  ```python
  if size > 0:
      ...
      leverage = notional / equity
      if leverage > self.config.max_leverage:
          return 0.0
  ```
  Si le levier nécessaire pour cibler la volatilité dépasse `max_leverage`, notre robot **refuse purement et simplement d'entrer en position** (taille nulle) plutôt que de plafonner la taille au levier maximal disponible. Cela fausse drastiquement les statistiques de backtest en sautant des opportunités clés.

### E. Robustesse de la Logique de Sortie (Exits) : POINT FORT UNIQUE
S'il y a un domaine où notre implémentation surclasse Zarattini et s'aligne fidèlement sur Ákos Maróy, c'est l'**ExitOrchestrator** de notre [broker.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/broker.py) :
- Les classes `VWAPExitRule`, `BoundaryExitRule`, `LadderExitRule`, et `SequentialLadderExitRule` sont extrêmement élégantes et fidèles.
- Le cycle de vie d'une position longue ou courte avec prises de bénéfices partielles à 50% (`is_partial_exit`) et déplacement dynamique du stop loss au prix moyen d'achat (`average_price`) est programmé de manière impeccable et correspond exactement à la spécification mathématique des "Ladder exits" du papier de Maróy.

---

## 4. Synthèse et Recommandations (Non-Exécutives)

### Évaluation Globale de la Cohérence
Le moteur de backtest actuel souffre d'un paradoxe : sa structure de simulation d'ordres et son orchestrateur de sorties (`ExitOrchestrator`) sont **hautement fidèles** et robustes, capables de reproduire les meilleures idées d'Ákos Maróy. En revanche, **le moteur de génération de signaux et de bandes d'entrée est mathématiquement déconnecté** des travaux originaux de Zarattini et des hypothèses de réplication de Maróy.

En l'état actuel, nos résultats de backtests Python ne peuvent pas coïncider avec les performances documentées dans la littérature financière car nos bandes d'entrées sont fixes (au lieu d'être dynamiquement croissantes en intraday) et le filtre de tendance VWAP est absent à l'entrée.

---

### Recommandations d'Améliorations (Feuille de Route Logicielle)

Pour rendre notre implémentation rigoureusement conforme à la chaîne théorique **Zarattini → Maróy**, nous suggérons les chantiers correctifs suivants (sans modification directe du code dans le cadre de cet audit) :

1. **Implémenter le vrai profil de volatilité intra-journalier (`sigma_open`)** : Remplacer le calcul global journalier dans `compute_noise_boundary` par un groupement par minute depuis l'ouverture (1-390).
2. **Corriger l'ancrage et la gestion des overnight gaps** : Modifier le calcul des limites `UB` et `LB` en introduisant le cours de clôture de la veille ajusté pour les dividendes.
3. **Activer le filtre VWAP obligatoire à l'entrée** : Ajouter la condition VWAP dans la validation du signal d'entrée.
4. **Assouplir le dimensionnement des positions (Sizing Leverage Cap)** : Remplacer le rejet de l'ordre par un écrêtage de la quantité au levier maximum autorisé.

---
**Auteurs de l'audit** : Antigravity Quant Team  
**Date d'émission** : 23 mai 2026  
**Statut** : Clôturé - Entièrement implémenté et validé le 23 mai 2026.

---

### Suivi d'Implémentation & Clôture (23 mai 2026)

Conformément à la feuille de route recommandée, les 4 chantiers correctifs ont été déployés et validés avec succès :

1. **Calcul de `sigma_open`** : Le profil type d'expansion de la volatilité intra-journalière est désormais fidèlement modélisé à chaque minute écoulée depuis l'ouverture du jour.
2. **Ancrage dynamique (Gaps Overnight)** : Les bandes d'entrée et de sortie s'ancrent dynamiquement sur `max(Open, prev_close)` pour le côté supérieur et `min(Open, prev_close)` pour le côté inférieur, protégeant ainsi le modèle contre le faux momentum des overnight gaps.
3. **Filtre VWAP à l'entrée** : Condition `close > VWAP` (ou `high > VWAP`) appliquée inconditionnellement aux entrées.
4. **Plafonnement du sizing (Broker)** : Suppression du rejet d'ordre. Le simulateur de broker écrête la quantité cible de sorte à ne jamais dépasser le levier maximum configuré tout en exécutant la position.

