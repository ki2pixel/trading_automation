# Rapport : MSL Friendly Trend - Passe Globale

## Objectif de la Passe
- **Type de Stratégie** : Catégorie A (Stratégie Simple à Passe Unique globale).
- **Paramètres cibles optimisés** : `length`, `mult`, `signal_mode`.

## Analyse Globale des Résultats
Un total de **18 448 itérations éligibles** a été identifié et traité sur 10 actifs. 
La stratégie, basée sur la dynamique de Market Structure Levels (MSL) et de Pullbacks, démontre des comportements très contrastés selon les actifs.

## Résultats par Catégorie d'Actifs

### 🟢 Les Validés (Edge Directionnel Net)

#### **NVO** (Novo Nordisk)
Présente un edge directionnel massif avec des performances nettes exceptionnelles (scores positifs de +28 à +64 sur presque tous les timeframes de 10m à 240m).
- **10m** : `length=149`, `mult=0.7`, `signal_mode=Close` | Score: +64.58, PnL: +1075.79, Max DD: -170.09, PF: 1.37, Trades: 1088
- **15m** : `length=110`, `mult=0.6`, `signal_mode=Close` | Score: +64.62, PnL: +1074.82, Max DD: -171.96, PF: 1.38, Trades: 942
- **20m** : `length=84`, `mult=0.5`, `signal_mode=Close` | Score: +63.61, PnL: +1066.39, Max DD: -238.07, PF: 1.40, Trades: 891
- **30m** : `length=57`, `mult=2.8`, `signal_mode=Close` | Score: +64.57, PnL: +1076.77, Max DD: -290.07, PF: 2.01, Trades: 169
- **45m** : `length=49`, `mult=2.1`, `signal_mode=Close` | Score: +56.77, PnL: +1002.73, Max DD: -279.50, PF: 1.80, Trades: 187
- **60m** : `length=15`, `mult=1.1`, `signal_mode=Live` | Score: +59.61, PnL: +1014.11, Max DD: -175.58, PF: 1.56, Trades: 281
- **120m** : `length=21`, `mult=1.1`, `signal_mode=Close` | Score: +49.93, PnL: +934.68, Max DD: -269.04, PF: 1.73, Trades: 179
- **240m** : `length=51`, `mult=1.5`, `signal_mode=Close` | Score: +28.23, PnL: +724.22, Max DD: -229.06, PF: 2.23, Trades: 54

#### **AMS.MC** (Amadeus IT Group)
Présente un edge validé et net (scores positifs de +11 à +17.5 sur les timeframes de 10m à 120m).
- **10m** : `length=113`, `mult=1.0`, `signal_mode=Close` | Score: +17.52, PnL: +80.80, Max DD: -21.13, PF: 1.32, Trades: 728
- **15m** : `length=66`, `mult=1.0`, `signal_mode=Live` | Score: +17.18, PnL: +78.70, Max DD: -20.20, PF: 1.31, Trades: 663
- **20m** : `length=49`, `mult=0.9`, `signal_mode=Live` | Score: +17.53, PnL: +80.87, Max DD: -17.91, PF: 1.33, Trades: 634
- **30m** : `length=34`, `mult=0.5`, `signal_mode=Close` | Score: +16.21, PnL: +71.25, Max DD: -21.20, PF: 1.28, Trades: 722
- **45m** : `length=20`, `mult=0.5`, `signal_mode=Live` | Score: +16.94, PnL: +74.34, Max DD: -18.80, PF: 1.31, Trades: 633
- **60m** : `length=74`, `mult=3.0`, `signal_mode=Close` | Score: +11.67, PnL: +21.70, Max DD: -18.28, PF: 1.30, Trades: 58
- **120m** : `length=140`, `mult=0.6`, `signal_mode=Close` | Score: +12.28, PnL: +30.90, Max DD: -15.61, PF: 1.42, Trades: 79

### 🟡 Mention Spéciale (Profil Conservateur)

#### **NVS** (Novartis)
Se distingue comme profil conservateur à fort profit factor malgré un score négatif face au Buy & Hold (PF > 2.0 et Max DD faibles sur 10m, 60m, 120m et 240m).
- **10m** : `length=11`, `mult=2.6`, `signal_mode=Live` | Score: -11.10, PnL: +71.51, Max DD: -12.67, PF: 2.05, Trades: 94
- **60m** : `length=47`, `mult=3.0`, `signal_mode=Close` | Score: -9.50, PnL: +90.98, Max DD: -12.57, PF: 2.46, Trades: 79
- **120m** : `length=100`, `mult=1.0`, `signal_mode=Close` | Score: -10.56, PnL: +86.65, Max DD: -13.12, PF: 1.84, Trades: 124
- **240m** : `length=13`, `mult=1.3`, `signal_mode=Close` | Score: -10.40, PnL: +83.03, Max DD: -19.59, PF: 2.62, Trades: 58

### 🔴 Les Rejetés (Absence d'Edge)
Les actifs suivants sont rejetés en raison de sous-performances prononcées ou de scores d'edge inadaptés :
- EVD.DE
- FPE.DE
- GMAB
- LOGI
- SAP
- SHL.DE
- ZEAL.CO

## Recommandations
Fin de l'optimisation pour cette stratégie (Passe unique accomplie avec succès). L'edge directionnel est clair pour NVO et AMS.MC, et le profil défensif de NVS justifie sa rétention. Passage en production recommandé pour les setups validés.
