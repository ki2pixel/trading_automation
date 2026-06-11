# Rapport : Momentum-based ZigZag (avec QQE) - Passe 3 (Trailing Stop & Pyramidage)

**Date d'analyse** : 11 Juin 2026
**Objectif de la Passe** : Évaluer l'impact d'un Trailing Stop (protection dynamique des gains) sur l'efficience de la stratégie, en complément des Stop Loss et Take Profit fixes validés en Passe 2.
**Paramètres figés** : Base QQE (Passe 1) + Asymétrie SL/TP (Passe 2).

---

## 1. Analyse Globale des Résultats

L'introduction d'un Trailing Stop a un **impact fortement négatif** sur les performances globales de la stratégie Momentum-based ZigZag. Le modèle dynamique vient court-circuiter l'asymétrie de risque validée lors de la Passe 2, coupant prématurément les "winners" avant qu'ils n'atteignent les larges Take Profits (souvent > 10%).

La volatilité inhérente aux forts mouvements de momentum provoque des retracements qui déclenchent le Trailing Stop. Bien que cela sécurise techniquement un léger profit, cela ampute sévèrement le PnL global par rapport à la méthode "Hit or Miss" du Stop Loss chirurgical couplé au Take Profit éloigné.

---

## 2. Dégradation des Métriques (Exemples)

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

## 3. Conclusion Définitive
La nature même du *Momentum-based ZigZag (avec QQE)* est d'identifier des impulsions directionnelles fortes mais potentiellement heurtées. Le Trailing Stop est contre-productif car il transforme la volatilité intra-trend en sorties prématurées.

**Décision technique : Le Trailing Stop est rejeté pour cette stratégie.**
L'optimisation globale de Momentum-based ZigZag est définitivement clôturée en retenant **exclusivement la configuration de la Passe 2** :
- Un Stop Loss fixe très serré.
- Un Take Profit fixe très ample.
- Aucune gestion dynamique intra-trade.
