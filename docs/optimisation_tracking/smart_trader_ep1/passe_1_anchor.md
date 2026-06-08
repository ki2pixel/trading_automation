# Rapport : Smart Trader Episode 1 - Passe 1 (L'Anchor et les Puissances)

**Date d'analyse** : 08 Juin 2026
**Objectif de la Passe** : Isoler la longueur idéale de la fenêtre de volume (`universal_len`) et les seuils de déclenchement (`long_power_min`, `short_power_max`) pour détecter les anomalies de pression acheteuse/vendeuse sur le timeframe 1 minute.
**Paramètres figés** : `calc_method = "Geometry (Source File)"`, buffers à 0.0.
**Métrique cible** : `return_vs_buy_hold_pct_points`
**Univers** : AMS.MC, GMAB, LOGI, NVO, NVS, SAP, SHL.DE, ZEAL.CO (Timeframe 1m).

---

## 1. Analyse Globale des Résultats

L'analyse de cette Passe 1 a mené à un résultat catégorique : **0 itération éligible** sur l'ensemble des 8 tickers pour les 1000 itérations du TPE Optimizer. Toutes les itérations ont été rejetées (`INELIGIBLE_CONSTRAINTS`), principalement en raison du seuil de `min_profit_factor >= 1.25` qui n'a jamais été atteint (la majorité oscillant autour de 0.99 à 1.05).

Une inspection approfondie des logs (`results.json`) révèle une hyperactivité extrême de la stratégie lorsqu'elle est soumise à ses paramètres bruts. Par exemple, sur **SAP**, certaines combinaisons (ex: `universal_len: 23`, `long_power_min: 60.0`) ont généré plus de **223 000 trades** sur la période backtestée. 

### Attribution de la contre-performance :
1. **Sur-exposition au bruit micro-structurel** : Sur un timeframe de 1 minute, les seuils de `long_power_min` testés (de 50.0 à 100.0) déclenchent des signaux à la moindre fluctuation locale du carnet d'ordres, résultant en un sur-trading destructeur.
2. **Absence de filtrage structurel** : L'anomalie de volume seule (l'Anchor) n'a pas d'espérance mathématique positive (`win_rate` ~49.3%, `average_win_loss_ratio` ~0.97) si elle n'est pas corrélée au comportement post-cassure (le Decay). L'edge directionnel brut est dilué dans le bruit.

---

## 2. Résultats par Catégorie d'Actifs

### 🔴 Rejetés (Aucun paramètre valide)
L'entièreté du spectre des actifs a échoué à produire une seule itération franchissant les contraintes de base du Risk Management. 
* **SAP**, **LOGI**, **AMS.MC**, **GMAB**, **NVO**, **NVS**, **SHL.DE**, **ZEAL.CO** : Le Profit Factor plafonne mathématiquement à ~1.0. Le Drawdown observé dépasse les -130% de manière théorique en raison du PnL cumulé négatif provoqué par l'accumulation infinitésimale de pertes statistiques sur plusieurs centaines de milliers de trades.

---

## 3. Recommandations Stratégiques pour la Suite

L'échec de la Passe 1 de `smart_trader_ep1` illustre l'avertissement de la roadmap d'optimisation : *"Si à une étape N, vous ne trouvez aucun résultat positif, cela signifie souvent que l'étape N-1 n'était pas assez robuste."*

Cependant, dans le cas précis de `smart_trader_ep1`, l'étape 1 (le signal brut de volume) est par nature instable sur du 1 minute. Il est statistiquement impossible d'isoler ce paramètre en créant un avantage sans activer le filtre comportemental de la Passe 2.

**Actions correctives recommandées pour débloquer la campagne :**

1. **Fusionner la Passe 1 et la Passe 2** : 
   Relancer une optimisation bayésienne qui inclut simultanément les paramètres d'Anchor (`universal_len`, `long_power_min`) ET les paramètres du filtre de décroissance PathTracker (`opp_dom_threshold`, `max_decay_angle`). Le signal d'anomalie de volume n'a de sens que si la rétention du mouvement est contrôlée immédiatement après le breakout.
   
2. **Restriction de l'Espace de Recherche (Search Space)** : 
   Afin de guider l'optimiseur et réduire le temps de calcul face à l'explosion combinatoire, il est conseillé de restreindre la recherche de `long_power_min` à des valeurs extrêmes (ex: 75.0 à 100.0). Cela forcera l'algorithme à ne cibler que les véritables anomalies de volume majeures, réduisant le nombre de trades de 200k+ à un volume réaliste et institutionnel.

3. **Statut de la Passe 3** : 
   Suspendre le passage à la Passe 3 (Risk-Management & Buffers) tant qu'un **Edge Core** (Sortino asymétrique > 0.50) n'est pas identifié via la nouvelle Passe 1+2 combinée.
