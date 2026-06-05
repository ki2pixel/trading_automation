# Synthèse Stratégique : Cybernetic Hilbert

**Date** : 05 Juin 2026
**Statut** : Optimisation Terminée (Passes 1, 2 et 3).

## Objectif Global
La stratégie `cybernetic_hilbert` repose sur la transformée de Hilbert de John Ehlers, permettant d'extraire la tendance fondamentale du prix et d'identifier les cycles de marché.
L'optimisation s'effectue en deux passes pour isoler efficacement les paramètres d'enveloppe de tendance avant d'appliquer les filtres cycliques de phase.

---

## 1. Bilan de la Passe 1 (Trend Mode)
La Passe 1 a permis de calibrer la stratégie dans son mode tendance de base.
* **Résultat** : Un edge clair a été identifié sur **NVO (45m)** et **ZEAL.CO (multiples unités de temps dont 15m, 20m, 30m, 45m, 60m)**.
* **Action** : Les paramètres `hilbert_smooth_period`, `take_profit_net_percent` et `stop_loss_net_percent` sont désormais validés et figés pour ces actifs.

---

## 2. Bilan de la Passe 2 (Phase Mode)
La Passe 2 visait à activer la détection cyclique (Phase Mode) avec optimisation du paramètre `require_cycling_bars`.

* **Résultat** : Rejet total (0 itération éligible) sur NVO et ZEAL.CO. L'activation du filtre cyclique détruit l'Edge de tendance.
* **Action** : Le Mode Phase est définitivement écarté pour ces actifs.

---

## 3. Bilan de la Passe 3 (Time Stop)
La Passe 3 (optionnelle) visait à couper les trades stagnants pour libérer le capital.

* **Résultat** : L'optimiseur a défini `safety_max_bars_in_trade: 0` comme étant optimal. Couper les trades prématurément sur un critère de temps n'apporte aucune amélioration des métriques de risque ou de rendement.
* **Action** : Le Time Stop est écarté (`use_safety_stop = false`).

---

## 4. Configuration Finale Retenue (Production)
La stratégie `cybernetic_hilbert` sera exploitée **exclusivement en Trend Mode** (`phase_mode_enabled = false`, `use_safety_stop = false`) en utilisant les configurations validées lors de la Passe 1 pour NVO (45m) et ZEAL.CO (15m, 20m, 30m, 45m, 60m).
