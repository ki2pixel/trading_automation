# Rapport : Momentum-based ZigZag (avec QQE) - Passe 3 (Trailing Stop & Pyramidage)

**Date d'analyse** : 19 Juin 2026
**Objectif de la Passe** : Évaluer l'impact d'un Trailing Stop (protection dynamique des gains) sur l'efficience de la stratégie, en complément des Stop Loss et Take Profit fixes validés en Passe 2.
**Paramètres figés** : Base QQE (Passe 1) + Asymétrie SL/TP (Passe 2).

---

## 1. Analyse Globale des Résultats

L'impact du Trailing Stop a été évalué sur deux vagues d'actifs de la campagne :
*   **Vague de Baseline (11 Juin 2026)** : L'introduction d'un Trailing Stop a eu un **impact fortement négatif** sur les performances globales. Le modèle dynamique vient court-circuiter l'asymétrie de risque validée lors de la Passe 2, coupant prématurément les "winners" avant qu'ils n'atteignent les larges Take Profits (souvent > 10%). La volatilité inhérente aux forts mouvements de momentum provoque des retracements qui déclenchent le Trailing Stop. Bien que cela sécurise techniquement un léger profit, cela ampute sévèrement le PnL global par rapport à la méthode "Hit or Miss" du Stop Loss chirurgical couplé au Take Profit éloigné.
*   **Vague d'Extension (19 Juin 2026)** : Suite aux conclusions sans appel de la baseline, **la Passe 3 a été bypassée par décision d'architecture**. L'analyse empirique a démontré que la structure de retour sur momentum du ZigZag QQE n'est pas compatible avec des seuils de suivi dynamiques. Afin d'éviter le sur-apprentissage (overfitting) et d'accélérer le cycle de mise en production, les configurations stabilisées en Passe 2 (ou Passe 1 pour `beideeur`) sont directement retenues.

---

## 2. Dégradation des Métriques sur la Baseline (Exemples)

* **NVO (45m)** : 
  * *Passe 2 (Sans Trailing)* : PnL +1977.43 | Sharpe 1.89 | Profit Factor 2.60 | Score: +154.24
  * **Passe 3 (Avec Trailing)** : PnL +298.81 | Sharpe 0.74 | Profit Factor 1.33 | Score: -14.32
  * *Chute absolue de performance. Le trailing (Activation à 4.1%, Retrait à 1.4%) a "étouffé" les trades.*

* **EVD.DE (45m)** :
  * *Passe 2 (Sans Trailing)* : PnL +8.45 | Sharpe 1.96 | Profit Factor 3.58 | Score: -30.50
  * **Passe 3 (Avec Trailing)** : PnL +1.36 | Sharpe 0.99 | Profit Factor 1.69 | Score: -31.22

* **AMS.MC (10m)** :
  * *Passe 2 (Sans Trailing)* : Sharpe 1.86 | Score: -42.44
  * **Passe 3 (Avec Trailing)** : Sharpe 0.89 | Score: -55.33

---

## 3. Vague d'Extension (19 Juin 2026) : Rationale du Bypass

La décision de ne pas exécuter l'optimisation de Passe 3 pour les 9 nouveaux candidats d'extension s'appuie sur trois piliers :
1.  **Uniformité du comportement de la stratégie** : La nature même de l'indicateur QQE combiné au ZigZag repose sur la capture de swings directionnels nets. Un trailing stop réagit de manière trop sensible à la volatilité intra-bougie sur les unités de temps cibles (10m - 30m).
2.  **Protection contre le sur-apprentissage** : Ajouter deux degrés de liberté supplémentaires (`trail_activation` et `trail_distance`) sur des séries temporelles courtes présente un risque majeur de courbe fittée.
3.  **Performances robustes en Passe 2** : Des actifs comme `daideeur` (Sharpe 2.67) et `belgbeeur` (Sharpe 2.18) affichent des métriques d'efficience exceptionnelles en Passe 2, validant la pertinence de l'asymétrie fixe de type "Hit or Miss".

---

## 4. Conclusion Définitive

**Décision technique : Le Trailing Stop est rejeté pour l'ensemble de la stratégie Momentum-based ZigZag (Baseline & Extension).**

L'optimisation globale est officiellement clôturée en retenant :
- L'asymétrie de la **Passe 2** pour les 8 actifs d'extension qualifiés et les actifs historiques.
- La configuration de **Passe 1 (sans TP/SL)** pour le cas particulier de **beideeur**.
- Aucune gestion dynamique intra-trade (Trailing Stop désactivé).
