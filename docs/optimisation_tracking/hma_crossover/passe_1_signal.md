# Audit de la Passe 1 : HMA Crossover (Signal Brut)

## 1. Objectif de la Passe
Évaluer l'edge directionnel brut du croisement des moyennes mobiles de Hull (HMA) sans sorties complexes (Passe 1).

## 2. Tableau Synthétique des Résultats

| Symbole | Timeframe | Itérations Éligibles | Meilleur Score (vs Buy & Hold) |
|---------|-----------|----------------------|-------------------------------|
| **AMS.MC** | 15m | 474 | -7.5800 % |
| **AMS.MC** | 45m | 590 | -5.7144 % |
| **AMS.MC** | 60m | 200 | -21.5456 % |
| **AMS.MC** | 120m | 636 | -26.3080 % |
| **AMS.MC** | 240m | 19 | -43.1899 % |
| **GMAB** | 15m | 400 | -6.4393 % |
| **GMAB** | 30m | 857 | **+5.6631 %** |
| **GMAB** | 45m | 670 | **+4.5009 %** |
| **GMAB** | 60m | 200 | -9.7826 % |
| **LOGI** | 10m | 31 | -458.9176 % |
| **LOGI** | 20m | 300 | -456.0283 % |
| **LOGI** | 30m | 35 | -457.6369 % |
| **LOGI** | 45m | 350 | -448.6636 % |
| **LOGI** | 60m | 104 | -467.3449 % |
| **LOGI** | 120m | 200 | -442.7563 % |
| **LOGI** | 240m | 200 | -459.4466 % |
| **NVO** | 10m | 200 | -27.6847 % |
| **NVO** | 15m | 200 | -26.1453 % |
| **NVO** | 20m | 250 | -19.3680 % |
| **NVO** | 30m | 837 | -21.3364 % |
| **NVO** | 45m | 720 | -22.7707 % |
| **NVO** | 60m | 450 | -24.6631 % |
| *Autres* | *Tous* | 0 | N/A |

> [!NOTE]
> Les actifs EVD.DE, FPE.DE, NVS, SAP, SHL.DE, et ZEAL.CO ont généré 0 itération.

## 3. Analyse des Sweet Spots Éligibles

- **GMAB - 30m** (Meilleure performance globale) :
  - **Paramètres** : `fast_len` = 27, `slow_len` = 110, `source_col` = "close", `confirm_on_close` = false.
  - **Métriques** : 83 trades clôturés, Sharpe = 2.0156, Sortino = 1.7453, PnL Net = 358.79%, Max Drawdown = -105.61%.

- **GMAB - 45m** (Alternative robuste) :
  - **Paramètres** : `fast_len` = 16, `slow_len` = 68, `source_col` = "close", `confirm_on_close` = false.
  - **Métriques** : 99 trades clôturés, Sharpe = 1.8372, Sortino = 1.6082, PnL Net = 348.34%, Max Drawdown = -105.58%.

- **AMS.MC - 45m** (Meilleure configuration Orange) :
  - **Paramètres** : `fast_len` = 13, `slow_len` = 55, `source_col` = "high", `confirm_on_close` = true.
  - **Métriques** : 620 trades, Sharpe = 0.6415, Sortino = 0.5827, PnL Net = 361.27%, Max Drawdown = -94.20%.

- **NVO - 20m** (Alternative Orange) :
  - **Paramètres** : `fast_len` = 15, `slow_len` = 105, `source_col` = "close", `confirm_on_close` = true.
  - **Métriques** : 138 trades, Sharpe = 1.1193, Sortino = 0.4838, PnL Net = 248.31%, Max Drawdown = -20.81% (Excellent contrôle du Drawdown).

## 4. Classification Thématique des Actifs

- 🟢 **Vert** : `GMAB` (30m, 45m) -> Edge directionnel valide, prêt pour la Passe 2.
- 🟡 **Orange** : `AMS.MC` (45m, 15m), `NVO` (20m, 30m) -> Éligible mais sous-performant par rapport au Buy & Hold en brut. Intéressant à conserver pour valider si les Passes 2 (Timing) et 3 (Exits complexes) renverseront la tendance.
- 🔴 **Rouge** : `LOGI` (Performance désastreuse) et tous les actifs à 0 itération -> À exclure des futures passes HMA Crossover pour éviter le sur-apprentissage sur du bruit.

## 5. Recommandations Stratégiques (Évolution de la Stratégie)

Conformément à la feuille de route (`README_OPTIMIZATION_ROADMAP.md`), la stratégie **HMA Crossover** est une stratégie de Catégorie A (Passe Unique). L'optimisation du signal de base est donc considérée comme **terminée**. 

Cependant, si nous décidons de faire évoluer le code source de cette stratégie pour améliorer ses performances (et justifier de nouvelles passes), voici les chantiers recommandés :

> [!TIP]
> **Passe 2 : Exits & Gestion du Risque (Stop-Loss / Take-Profit)**
> Le HMA Crossover classique étant très lent à sortir de position (attente du croisement inverse), il serait pertinent d'ajouter et d'optimiser des sorties asymétriques : un Stop-Loss (fixe ou ATR) et un Trailing-Stop pour sécuriser les profits des sweet spots (comme `GMAB`) bien avant le croisement inverse.

> [!TIP]
> **Passe 3 : Filtres de Régime de Marché (Anti-Range)**
> Les moyennes mobiles génèrent d'énormes pertes en période de range (cf. les résultats désastreux sur `LOGI`). Ajouter un filtre de régime (ex: RSI ou ADX) permettrait de bloquer les entrées lorsque le marché n'a pas de tendance claire.
