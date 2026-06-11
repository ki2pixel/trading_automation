# Synthèse Stratégique : Momentum-based ZigZag (avec QQE)

**Statut Actuel** : Campagne d'optimisation (Passes 1 à 3) totalement achevée. Rejet du Trailing Stop. Stratégie validée sur l'asymétrie de la Passe 2.
**Prochaine Étape** : Déploiement en paper trading ou live.

---

## 1. État de la Recherche

La Passe 1 avait pour but d'optimiser le socle de signaux d'entrée via le QQE et les niveaux RSI (`rsi_period`, `qqe_factor`, `rsi_smoothing`, `ob`, `os`, `signal_mode`), sans l'aide de Stop Loss ou de Take Profit.

Les résultats confirment une grande précision des entrées lorsque la stratégie est adaptée à la volatilité intrinsèque de chaque actif via l'ajustement du Timeframe. L'edge optimal se situe majoritairement sur des timeframes allant de **1 minute à 120 minutes**.
Seul **NVO (sur 45m)** a réussi à battre le Buy & Hold sans mécanisme de sortie (score : +109.88), mais un groupe solide de valeurs très "prometteuses" (ZEAL.CO, GMAB, SAP...) présente des Sharpe ratios allant jusqu'à 2.05 sur des timeframes courts, nécessitant des prises de profits (Passe 2) pour transformer cet edge de signal en véritable sur-performance absolue.

---

## 2. Planification et Intégration

### Configurations Validées à Bloquer pour la Passe 2

* **NVO [45m]** : `rsi_period=8`, `qqe_factor=2.0`, `rsi_smoothing=4`, `ob=82.0`, `os=10.0`, `signal_mode="Close"`
* **ZEAL.CO [1m]** : `rsi_period=19`, `qqe_factor=4.8`, `rsi_smoothing=2`, `ob=71.0`, `os=25.0`, `signal_mode="Close"`
* **SAP [30m]** : `rsi_period=25`, `qqe_factor=5.6`, `rsi_smoothing=15`, `ob=79.0`, `os=18.0`, `signal_mode="Live"`
* **LOGI [120m]** : `rsi_period=8`, `qqe_factor=2.5`, `rsi_smoothing=14`, `ob=76.0`, `os=17.0`, `signal_mode="Live"`
* **GMAB [1m]** : `rsi_period=12`, `qqe_factor=5.0`, `rsi_smoothing=13`, `ob=67.0`, `os=32.0`, `signal_mode="Close"`
* **SHL.DE [45m]** : `rsi_period=17`, `qqe_factor=1.6`, `rsi_smoothing=2`, `ob=66.0`, `os=34.0`, `signal_mode="Close"`
* **AMS.MC [10m]** : `rsi_period=14`, `qqe_factor=2.5`, `rsi_smoothing=3`, `ob=66.0`, `os=35.0`, `signal_mode="Live"`
* **NVS [5m]** : `rsi_period=17`, `qqe_factor=4.9`, `rsi_smoothing=4`, `ob=65.0`, `os=32.0`, `signal_mode="Live"`
* **EVD.DE [45m]** : `rsi_period=7`, `qqe_factor=4.5`, `rsi_smoothing=13`, `ob=90.0`, `os=12.0`, `signal_mode="Close"`
* **FPE.DE [20m]** : `rsi_period=7`, `qqe_factor=2.0`, `rsi_smoothing=10`, `ob=68.0`, `os=21.0`, `signal_mode="Live"`

### Étape Suivante (Passe 2 : Achevée)
L'optimisation des mécanismes de sortie pure (Passe 2) a été menée avec succès, révélant la nécessité d'une asymétrie forte : des Take Profits très amples (souvent supérieurs à 9%) combinés à des Stop Loss serrés (0.5% à 4.5%).

**Configurations Finales Validées (Issues de la Passe 2) :**
* **NVO** : `stop_loss_pct=0.5`, `take_profit_pct=11.9`
* **ZEAL.CO** : `stop_loss_pct=3.9`, `take_profit_pct=9.6`
* **AMS.MC** : `stop_loss_pct=0.5`, `take_profit_pct=15.0`
* **GMAB** : `stop_loss_pct=4.4`, `take_profit_pct=14.9`
* **EVD.DE** : `stop_loss_pct=0.6`, `take_profit_pct=9.8`
* **SAP** : `stop_loss_pct=4.8`, `take_profit_pct=13.4`
* **SHL.DE** : `stop_loss_pct=4.3`, `take_profit_pct=11.2`
* **LOGI** : `stop_loss_pct=2.9`, `take_profit_pct=14.9`
* **NVS** : `stop_loss_pct=2.7`, `take_profit_pct=8.6`
* **FPE.DE** : `stop_loss_pct=4.2`, `take_profit_pct=12.0`

### Étape Suivante (Passe 3 : Rejetée)
La Passe 3 a consisté à tester la protection dynamique des gains (Trailing Stop). Les résultats ont été **catégoriques : le Trailing Stop dégrade massivement les performances** (baisse sévère du Sharpe Ratio et du PnL global, ex: NVO passe d'un Sharpe 1.89 à 0.74). La volatilité intra-trend inhérente au momentum déclenche des sorties prématurées, empêchant la stratégie d'atteindre ses larges Take Profits.

### Conclusion Globale
La stratégie *Momentum-based ZigZag* est intégralement validée et optimisée. Elle capture excellemment les impulsions (swings) sur les petites unités de temps via une mécanique "Hit or Miss" stricte : des Stop Loss chirurgicaux et des cibles de gain extrêmes, sans aucune gestion dynamique. La campagne d'optimisation est officiellement clôturée.
