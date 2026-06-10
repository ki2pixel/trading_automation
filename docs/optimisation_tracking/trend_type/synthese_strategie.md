# Synthèse Stratégique : Trend Type Indicator

**Statut Actuel** : Analyse terminée (Stratégie à 1 passe). Configurations figées et validées.  
**Prochaine Étape** : Intégration en production live.

---

## 1. État de la Recherche

La stratégie **Trend Type Indicator** est une approche de suivi de tendance s'appuyant sur l'interaction des filtres ATR et ADX/DMI pour identifier les régimes de marché directionnels. En tant que stratégie de Catégorie A, elle nécessite une seule passe d'optimisation globale.

Les résultats de l'optimisation (sur 27 162 itérations éligibles) montrent que :
* Un "Edge" net a été identifié et validé sur **NVO**, le seul actif affichant une sur-performance absolue face au Buy & Hold sur une large gamme de timeframes (de 10m à 120m).
* **NVS** représente une Mention Spéciale : bien qu'il sous-performe le Buy & Hold en absolu, il offre un profil conservateur remarquable avec un Max Drawdown minimal (< 10%) et un Profit Factor excellent (> 2.0).
* Les autres actifs testés (AMS.MC, EVD.DE, GMAB, LOGI, SAP, SHL.DE, ZEAL.CO) ont été rejetés en raison de sous-performances significatives ou d'un rapport risque/rendement inadapté.

---

## 2. Planification et Intégration Finale

### Configurations Validées (Setup Trend Type Indicator)

#### NVO (Sur-Performance Absolue)
* **10m** : `atr_len=10`, `atr_ma_len=17`, `adx_len=19`, `di_len=28`, `adx_lim=15.0`, `smooth=1`, `signal_mode=Live` (Score: +34.14)
* **15m** : `atr_len=5`, `atr_ma_len=20`, `adx_len=15`, `di_len=28`, `adx_lim=15.0`, `smooth=3`, `signal_mode=Live` (Score: +16.33)
* **20m** : `atr_len=6`, `atr_ma_len=10`, `adx_len=7`, `di_len=29`, `adx_lim=15.0`, `smooth=3`, `signal_mode=Live` (Score: +22.18)
* **30m** : `atr_len=14`, `atr_ma_len=35`, `adx_len=24`, `di_len=16`, `adx_lim=20.0`, `smooth=10`, `signal_mode=Live` (Score: +10.36)
* **45m** : `atr_len=28`, `atr_ma_len=24`, `adx_len=25`, `di_len=13`, `adx_lim=22.0`, `smooth=10`, `signal_mode=Close` (Score: +11.69)
* **60m** : `atr_len=11`, `atr_ma_len=12`, `adx_len=5`, `di_len=10`, `adx_lim=15.0`, `smooth=9`, `signal_mode=Close` (Score: +20.34)
* **120m** : `atr_len=11`, `atr_ma_len=48`, `adx_len=28`, `di_len=5`, `adx_lim=29.0`, `smooth=3`, `signal_mode=Close` (Score: +3.24)

#### NVS (Profil Conservateur)
* **15m** : `atr_len=13`, `atr_ma_len=12`, `adx_len=20`, `di_len=17`, `adx_lim=33.0`, `smooth=5`, `signal_mode=Close` (Score: -13.79 | Max DD: -4.32% | PF: 2.04)
* **30m** : `atr_len=22`, `atr_ma_len=50`, `adx_len=18`, `di_len=21`, `adx_lim=25.0`, `smooth=9`, `signal_mode=Live` (Score: -14.87 | Max DD: -7.45% | PF: 2.03)
* **60m** : `atr_len=12`, `atr_ma_len=31`, `adx_len=16`, `di_len=20`, `adx_lim=17.0`, `smooth=10`, `signal_mode=Close` (Score: -13.26 | Max DD: -8.52% | PF: 2.36)
* **120m** : `atr_len=30`, `atr_ma_len=46`, `adx_len=16`, `di_len=6`, `adx_lim=30.0`, `smooth=5`, `signal_mode=Live` (Score: -13.32 | Max DD: -9.47% | PF: 2.18)

### Étape Suivante
L'optimisation de la stratégie Trend Type Indicator est considérée comme achevée. Les configurations ci-dessus sont prêtes à être intégrées au sein du moteur de production live.
