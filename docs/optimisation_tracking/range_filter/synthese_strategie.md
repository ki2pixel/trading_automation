# Synthèse : Range Filter

Ce document consigne les paramètres "bloqués" à l'issue de la passe unique d'optimisation (Catégorie A). Ces paramètres doivent être fixés dans le fichier `.json` de configuration pour exécuter la stratégie en production ou paper-trading.

## Passe Unique : Optimisation Globale
*(Validation du filtre de range - Filtres de backtest standards)*

L'analyse a révélé que la stratégie Range Filter n'est performante que sur certains actifs spécifiques (GMAB, FPE.DE). Les autres actifs du portfolio génèrent des rendements lourdement inférieurs au "Buy & Hold".

Voici les "Sweet Spots" validés à figer en dur dans vos configurations de backtest pour un déploiement :

**Pour GMAB - *Excellent rendement absolu et forte robustesse***
* **Timeframe 20m** (Meilleur compromis volume d'itérations/rendement)
  * `sampling_period` = 93
  * `range_multiplier` = 3.9
  * `source_col` = "high"
* **Timeframe 30m** (Alternative solide)
  * `sampling_period` = 71
  * `range_multiplier` = 3.7
  * `source_col` = "close"

**Pour FPE.DE - *Rendement modéré***
* **Timeframe 45m** (Le plus robuste statistiquement)
  * `sampling_period` = 152
  * `range_multiplier` = 3.8
  * `source_col` = "open"
* **Timeframe 240m** (Alternative Swing)
  * `sampling_period` = 197
  * `range_multiplier` = 1.8
  * `source_col` = "high"

> [!NOTE]  
> **Optimisation Terminée** 🎉. S'agissant d'une stratégie de Catégorie A (une seule passe requise), tous les paramètres figurant dans ce document constituent les configurations définitives "Sweet Spots" pour lancer la stratégie Range Filter en production ou en Paper Trading. Les autres actifs (AMS.MC, EVD.DE, LOGI, NVO, NVS, SAP, SHL.DE, ZEAL.CO) sont écartés de cette stratégie.
