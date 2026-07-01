# Synthèse Stratégique : Cybernetic Hilbert

**Date** : 18 Juin 2026 (Mise à jour avec la campagne d'extension)
**Statut** : Optimisation Terminée pour tous les actifs qualifiés (Passes 1, 2 et 3).

## Objectif Global
La stratégie `cybernetic_hilbert` repose sur la transformée de Hilbert de John Ehlers, permettant d'extraire la tendance fondamentale du prix et d'identifier les cycles de marché.
L'optimisation s'effectue en deux passes pour isoler efficacement les paramètres d'enveloppe de tendance avant d'appliquer les filtres cycliques de phase.

---

## 1. Bilan de la Passe 1 (Trend Mode)
La Passe 1 a permis de calibrer la stratégie dans son mode tendance de base.
* **Résultat** : Un edge clair a été identifié sur **NVO (45m)**, **ZEAL.CO (multiples unités de temps dont 15m, 20m, 30m, 45m, 60m)**, ainsi que sur les nouveaux actifs **LXSDEEUR (60m)** et **MRKDEEUR (45m)**.
* **Action** : Les paramètres `hilbert_smooth_period`, `take_profit_net_percent` et `stop_loss_net_percent` sont désormais validés et figés pour ces actifs.

---

## 2. Bilan de la Passe 2 (Phase Mode)
La Passe 2 visait à activer la détection cyclique (Phase Mode) avec optimisation du paramètre `require_cycling_bars`.

* **Résultat** : Rejet total (0 itération éligible) sur tous les actifs (NVO, ZEAL.CO, LXSDEEUR, MRKDEEUR). L'activation du filtre cyclique détruit l'Edge de tendance.
* **Action** : Le Mode Phase est définitivement écarté pour l'ensemble des actifs qualifiés.

---

## 3. Bilan de la Passe 3 (Time Stop)
La Passe 3 (optionnelle) visait à couper les trades stagnants pour libérer le capital.

* **Résultat** : L'optimiseur a défini `safety_max_bars_in_trade: 0` comme étant optimal pour tous les actifs testés. Couper les trades prématurément sur un critère de temps n'apporte aucune amélioration des métriques de risque ou de rendement.
* **Action** : Le Time Stop est écarté (`use_safety_stop = false`).

---

## 4. Configuration Finale Retenue (Production Actions)
La stratégie `cybernetic_hilbert` sera exploitée **exclusivement en Trend Mode** (`phase_mode_enabled = false`, `use_safety_stop = false`) en utilisant les configurations validées lors de la Passe 1 pour :
* **NVO** (45m)
* **ZEAL.CO** (15m, 20m, 30m, 45m, 60m)
* **LXSDEEUR** (60m)
* **MRKDEEUR** (45m)

---

## 5. Synthèse Spécifique aux Actifs Crypto

Contrairement au segment des actions, le segment crypto valide l'intérêt du **Phase Mode** (Mode Oscillation) pour certains actifs et démontre l'apport du **Time Stop** pour réguler le risque sur d'autres.

### Configurations Finales Retenues (Production Crypto)
Les 7 configurations cryptos validées se répartissent comme suit pour l'intégration en production :

#### A. Segment Oscillation (Phase Mode Activé)
Ce segment utilise les retournements cycliques de phase avec une barrière de confirmation d'une bougie, offrant des drawdowns ultra-limités (inférieurs à -1.0% sur APT/DOT) :
* **APTUSDT (10min)** : `phase_mode_enabled = true`, `require_cycling_bars = 1`, `use_safety_stop = false`, `hilbert_smooth_period = 12`, `take_profit_net_percent = 18.0`, `stop_loss_net_percent = 1.0`. (Score: `+92.20`, PF: 2.450, DD: -0.17%).
* **DOTUSDT (10min)** : `phase_mode_enabled = true`, `require_cycling_bars = 1`, `use_safety_stop = true`, `safety_max_bars_in_trade = 5`, `hilbert_smooth_period = 10`, `take_profit_net_percent = 20.0`, `stop_loss_net_percent = 1.0`. (Score: `+48.06`, PF: 2.019, DD: -0.86%).
* **DOTUSDT (45min)** : `phase_mode_enabled = true`, `require_cycling_bars = 1`, `use_safety_stop = false`, `hilbert_smooth_period = 8`, `take_profit_net_percent = 19.0`, `stop_loss_net_percent = 1.0`. (Score: `+48.35`, PF: 2.232, DD: -0.60%).
* **LTCUSDT (30min)** : `phase_mode_enabled = true`, `require_cycling_bars = 1`, `use_safety_stop = false`, `hilbert_smooth_period = 9`, `take_profit_net_percent = 20.0`, `stop_loss_net_percent = 1.0`. (Score: `+87.80`, PF: 2.772, DD: -2.71%).

#### B. Segment Tendance (Trend Mode Activé avec Time Stop)
Ce segment exploite les mouvements de tendance pure (Passe 1) renforcés par un coupe-circuit temporel (Time Stop) pour réduire la stagnation dans le marché :
* **ETHUSDT (45min)** : `phase_mode_enabled = false`, `use_safety_stop = true`, `safety_max_bars_in_trade = 5`, `hilbert_smooth_period = 9`, `take_profit_net_percent = 19.0`, `stop_loss_net_percent = 1.0`. (Score: `+6960.36`, PF: 1.527, DD: -10.06%).
* **DOTUSDT (1h)** : `phase_mode_enabled = false`, `use_safety_stop = true`, `safety_max_bars_in_trade = 50`, `hilbert_smooth_period = 6`, `take_profit_net_percent = 19.0`, `stop_loss_net_percent = 1.0`. (Score: `+99.05`, PF: 1.655, DD: -1.26%).
* **LTCUSDT (45min)** : `phase_mode_enabled = false`, `use_safety_stop = true`, `safety_max_bars_in_trade = 20`, `hilbert_smooth_period = 12`, `take_profit_net_percent = 20.0`, `stop_loss_net_percent = 1.0`. (Score: `+674.09`, PF: 1.563, DD: -8.70%).

