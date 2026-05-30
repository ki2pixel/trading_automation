# Exploration Granularité 5m — Rapport Hold-out (SAP & LOGI)

Ce rapport présente les résultats de l'**Étape 4** de notre plan de ré-audit, explorant la robustesse de la stratégie `noise_boundary_intraday` à la granularité **5 minutes** par rapport à la granularité **1 minute**.

---

## 1. Résultats Comparatifs 1m vs 5m (OOS : 2023-04-16 → 2024-04-16)

Voici la comparaison directe des performances sur la période hors-échantillon (OOS) entre la granularité 1 minute et la granularité 5 minutes pour **SAP** et **LOGI**.

| Ticker | Résolution | Sharpe OOS | CAGR OOS (%) | MDD OOS (%) | Nombre de Trades |
| --- | --- | --- | --- | --- | --- |
| **SAP** | 1 minute | **0.571** | 38.939% | -15.531% | **294** |
| **SAP** | 5 minutes | **0.615** | **39.242%** | **-14.273%** | 258 |
| --- | --- | --- | --- | --- | --- |
| **LOGI** | 1 minute | **0.713** | — | — | 41 |
| **LOGI** | 5 minutes | **0.737** | 0.487% | -0.140% | 2 |

---

## 2. Analyse Approfondie des Résultats

### A. SAP : La force de la réduction du bruit sur le 5m
Pour **SAP**, la transition de 1m à 5m est un succès total :
- **Sharpe en hausse** : Le Sharpe OOS grimpe de **0.571** à **0.615**.
- **Drawdown en baisse** : Le Max Drawdown se réduit de **-15.53%** à **-14.27%**.
- **Trades stables** : La fréquence de trading reste très robuste avec **258 trades** sur l'année (soit environ 1 trade par jour de bourse), contre **294** sur le 1m.
- **Raison technique** : À la granularité 1m, les micro-variations de cours créent de faux signaux de cassure (noise) qui déclenchent des entrées hâtives suivies de stop-outs rapides (notamment via la règle `BoundaryExit` ou le premier palier du `Ladder`). Le filtre 5m lisse ces micro-bruits, validant des cassures de bandes plus significatives et plus directionnelles.

### B. LOGI : Le piège de l'asphyxie des signaux sur le 5m
Pour **LOGI**, les résultats démontrent une dynamique radicalement différente :
- **Asphyxie totale** : À la granularité 5m, le modèle n'a exécuté que **2 trades** sur toute l'année (CAGR de 0.487%), contre **41 trades** à la granularité 1m.
- **Raison technique** : LOGI possède un profil de volatilité intrajournalière plus nerveux et des mouvements plus brutaux et brefs. Les bandes calculées à partir de sa volatilité historique sont plus larges. En résolvant à 5m, le prix moyen/close des barres de 5m repasse très vite à l'intérieur des bandes, effaçant la détection des breakouts rapides de quelques minutes. La stratégie se retrouve ainsi "asphyxiée" par manque de réactivité.

---

## 3. Recommandations et Synthèse
Ces résultats confirment que **le choix du timeframe ne doit pas être global, mais doit dépendre du profil de l'actif** :
1. **Actifs à faible volatilité et tendance stable (ex: SAP)** : Privilégier la granularité **5 minutes** pour éliminer le bruit haute fréquence, maximiser le Sharpe, et réduire le stress sur le portefeuille.
2. **Actifs nerveux à breakouts rapides (ex: LOGI)** : Conserver la granularité **1 minute** pour capter les impulsions rapides avant le retour à la moyenne des bandes.

---
*Rapport généré le 2026-05-22*
