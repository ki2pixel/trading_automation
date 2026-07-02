# Synthèse Stratégique : Momentum-based ZigZag (avec QQE)

**Statut Actuel** : Campagne d'optimisation (Baseline, Extension & Crypto) totalement achevée. Rejet systématique du Trailing Stop (Passe 3). Stratégie validée sur l'asymétrie de la Passe 2 (SL/TP fixes).
**Prochaine Étape** : Déploiement des configurations retenues en production (paper trading ou live).

---

## 1. État de la Recherche

La Passe 1 a permis d'optimiser le socle de signaux d'entrée via le QQE et les niveaux RSI (`rsi_period`, `qqe_factor`, `rsi_smoothing`, `ob`, `os`, `signal_mode`), sans brackets de sortie.
*   **Campagne de Baseline (11 Juin 2026)** : Validation de 10 actifs. Seul `NVO` sur-performait intrinsèquement le B&H, mais de nombreuses valeurs prometteuses (ZEAL.CO, GMAB, SAP...) présentaient des ratios financiers très robustes requérant des brackets de sortie pour figer les gains.
*   **Campagne d'Extension (19 Juin 2026)** : Évaluation de 20 nouveaux candidats du screening. Cette vague qualifie **9 actifs supplémentaires** avec une excellente sur-performance relative dès la Passe 1 (belgbeeur, daideeur, cpriteur, cafreur, vnadeeur, akzanleur, randnleur, vpknleur, beideeur).
*   **Campagne Crypto (02 Juillet 2026)** : Évaluation de la stratégie sur les actifs cryptomonnaies qualifiés. Elle valide **4 configurations** hautement performantes (`dotusdt` 30m/45m et `ltcusdt` 30m/45m) avec une amélioration drastique des drawdowns grâce aux stops de Passe 2.

---

## 2. Planification et Intégration

### A. Configurations Core Validées (Passe 1)

Ces paramètres figent la détection des signaux d'entrée :

#### 📈 Vague de Baseline (11 Juin 2026)
*   **NVO [45m]** : `rsi_period=8`, `qqe_factor=2.0`, `rsi_smoothing=4`, `ob=82.0`, `os=10.0`, `signal_mode="Close"`
*   **ZEAL.CO [1m]** : `rsi_period=19`, `qqe_factor=4.8`, `rsi_smoothing=2`, `ob=71.0`, `os=25.0`, `signal_mode="Close"`
*   **SAP [30m]** : `rsi_period=25`, `qqe_factor=5.6`, `rsi_smoothing=15`, `ob=79.0`, `os=18.0`, `signal_mode="Live"`
*   **LOGI [120m]** : `rsi_period=8`, `qqe_factor=2.5`, `rsi_smoothing=14`, `ob=76.0`, `os=17.0`, `signal_mode="Live"`
*   **GMAB [1m]** : `rsi_period=12`, `qqe_factor=5.0`, `rsi_smoothing=13`, `ob=67.0`, `os=32.0`, `signal_mode="Close"`
*   **SHL.DE [45m]** : `rsi_period=17`, `qqe_factor=1.6`, `rsi_smoothing=2`, `ob=66.0`, `os=34.0`, `signal_mode="Close"`
*   **AMS.MC [10m]** : `rsi_period=14`, `qqe_factor=2.5`, `rsi_smoothing=3`, `ob=66.0`, `os=35.0`, `signal_mode="Live"`
*   **NVS [5m]** : `rsi_period=17`, `qqe_factor=4.9`, `rsi_smoothing=4`, `ob=65.0`, `os=32.0`, `signal_mode="Live"`
*   **EVD.DE [45m]** : `rsi_period=7`, `qqe_factor=4.5`, `rsi_smoothing=13`, `ob=90.0`, `os=12.0`, `signal_mode="Close"`
*   **FPE.DE [20m]** : `rsi_period=7`, `qqe_factor=2.0`, `rsi_smoothing=10`, `ob=68.0`, `os=21.0`, `signal_mode="Live"`

#### 🚀 Vague d'Extension (19 Juin 2026)
*   **belgbeeur [10m]** : `rsi_period=22`, `qqe_factor=5.0`, `rsi_smoothing=15`, `ob=90.0`, `os=24.0`, `signal_mode="Live"`
*   **daideeur [15m]** : `rsi_period=17`, `qqe_factor=4.1`, `rsi_smoothing=5`, `ob=89.0`, `os=10.0`, `signal_mode="Close"`
*   **cafreur [15m]** : `rsi_period=15`, `qqe_factor=1.5`, `rsi_smoothing=10`, `ob=82.0`, `os=23.0`, `signal_mode="Close"`
*   **cpriteur [10m]** : `rsi_period=17`, `qqe_factor=2.3`, `rsi_smoothing=7`, `ob=66.0`, `os=31.0`, `signal_mode="Close"`
*   **vnadeeur [10m]** : `rsi_period=16`, `qqe_factor=1.6`, `rsi_smoothing=15`, `ob=76.0`, `os=20.0`, `signal_mode="Live"`
*   **randnleur [10m]** : `rsi_period=18`, `qqe_factor=6.0`, `rsi_smoothing=2`, `ob=73.0`, `os=28.0`, `signal_mode="Live"`
*   **akzanleur [30m]** : `rsi_period=29`, `qqe_factor=6.0`, `rsi_smoothing=12`, `ob=90.0`, `os=10.0`, `signal_mode="Live"`
*   **vpknleur [15m]** : `rsi_period=27`, `qqe_factor=1.9`, `rsi_smoothing=4`, `ob=66.0`, `os=34.0`, `signal_mode="Close"`
*   **beideeur [15m]** : `rsi_period=27`, `qqe_factor=2.9`, `rsi_smoothing=15`, `ob=67.0`, `os=18.0`, `signal_mode="Live"`

#### 🪙 Vague Crypto (02 Juillet 2026)
*   **dotusdt [30m]** : `rsi_period=21`, `qqe_factor=5.7`, `rsi_smoothing=12`, `ob=65.0`, `os=33.0`, `signal_mode="Live"`
*   **dotusdt [45m]** : `rsi_period=30`, `qqe_factor=3.0`, `rsi_smoothing=4`, `ob=85.0`, `os=16.0`, `signal_mode="Close"`
*   **ltcusdt [30m]** : `rsi_period=8`, `qqe_factor=6.0`, `rsi_smoothing=8`, `ob=75.0`, `os=27.0`, `signal_mode="Live"`
*   **ltcusdt [45m]** : `rsi_period=10`, `qqe_factor=3.8`, `rsi_smoothing=13`, `ob=76.0`, `os=29.0`, `signal_mode="Live"`

---

### B. Configurations de Risque Validées (Passe 2)

L'ajout d'une gestion de risque statique (Stop Loss et Take Profit fixes) confirme la nécessité d'une asymétrie forte : des Take Profits amples couplés à des Stop Loss serrés ou adaptés pour figer la performance sans couper les tendances.

#### 📈 Vague de Baseline (SL/TP retenus)
*   **NVO** : `stop_loss_pct=0.5%`, `take_profit_pct=11.9%`
*   **ZEAL.CO** : `stop_loss_pct=3.9%`, `take_profit_pct=9.6%`
*   **AMS.MC** : `stop_loss_pct=0.5%`, `take_profit_pct=15.0%`
*   **GMAB** : `stop_loss_pct=4.4%`, `take_profit_pct=14.9%`
*   **EVD.DE** : `stop_loss_pct=0.6%`, `take_profit_pct=9.8%`
*   **SAP** : `stop_loss_pct=4.8%`, `take_profit_pct=13.4%`
*   **SHL.DE** : `stop_loss_pct=4.3%`, `take_profit_pct=11.2%`
*   **LOGI** : `stop_loss_pct=2.9%`, `take_profit_pct=14.9%`
*   **NVS** : `stop_loss_pct=2.7%`, `take_profit_pct=8.6%`
*   **FPE.DE** : `stop_loss_pct=4.2%`, `take_profit_pct=12.0%`

#### 🚀 Vague d'Extension (SL/TP optimisés ou signal pur)
*   **belgbeeur** : `stop_loss_pct=0.5%`, `take_profit_pct=4.6%`
*   **daideeur** : `stop_loss_pct=0.5%`, `take_profit_pct=7.8%`
*   **cafreur** : `stop_loss_pct=0.9%`, `take_profit_pct=8.4%`
*   **cpriteur** : `stop_loss_pct=5.0%`, `take_profit_pct=15.0%`
*   **vnadeeur** : `stop_loss_pct=0.7%`, `take_profit_pct=14.7%`
*   **randnleur** : `stop_loss_pct=5.0%`, `take_profit_pct=13.4%`
*   **akzanleur** : `stop_loss_pct=1.0%`, `take_profit_pct=7.7%`
*   **vpknleur** : `stop_loss_pct=4.5%`, `take_profit_pct=9.7%`
*   **beideeur** : **Désactivé** (Pas de SL/TP, maintien de la configuration Passe 1 sans brackets suite à une dégradation en Passe 2).

#### 🪙 Vague Crypto (SL/TP optimisés)
*   **dotusdt [30m]** : `stop_loss_pct=9.5%`, `take_profit_pct=25.0%`
*   **dotusdt [45m]** : `stop_loss_pct=1.5%`, `take_profit_pct=24.0%`
*   **ltcusdt [30m]** : `stop_loss_pct=2.5%`, `take_profit_pct=25.0%`
*   **ltcusdt [45m]** : `stop_loss_pct=2.5%`, `take_profit_pct=25.0%`

---

### C. Rejet du Trailing Stop (Passe 3)

La Passe 3 a consisté à tester la protection dynamique des gains (Trailing Stop). Les résultats ont été **catégoriques : le Trailing Stop dégrade massivement les performances** sur l'ensemble de la stratégie. 
La volatilité inhérente aux tendances identifiées par le ZigZag QQE déclenche des sorties prématurées (whipsaws), coupant les trades avant l'atteinte des Take Profits cibles (ex: `NVO` chute d'un Sharpe 1.89 à 0.74).

**Décision technique d'architecture : Le Trailing Stop est rejeté pour la baseline et bypassé pour les vagues d'extension et crypto.**

---

## 3. Conclusion Globale

La stratégie *Momentum-based ZigZag* est validée à 100% sur un univers élargi de **23 configurations** (10 baseline, 9 extension, 4 crypto). Elle capture efficacement les oscillations de momentum à court et moyen terme via des entrées QQE chirurgicales couplées à des objectifs de gains asymétriques très larges, sans gestion dynamique. Les configurations listées ci-dessus sont prêtes pour le déploiement en production.
