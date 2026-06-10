# Synthèse Stratégique : MSL Friendly Trend

## Statut Actuel & Prochaine Étape
- **Statut** : Optimisation terminée (Passe unique).
- **Prochaine étape** : Figer les configurations validées pour intégration finale en live.

## État de la Recherche
L'analyse approfondie de la stratégie **MSL Friendly Trend** a permis d'évaluer 18 448 itérations éligibles réparties sur 10 actifs. L'objectif était de capturer un edge directionnel clair basé sur les niveaux de structure de marché (MSL) et les pullbacks.

Cette campagne d'optimisation (Catégorie A, passe globale) a mis en évidence des comportements distincts : des edges massifs (notamment sur NVO et AMS.MC) avec des scores très largement au-dessus du Buy & Hold, et un profil conservateur solide (NVS) garantissant un profit factor très élevé pour un faible Max Drawdown. Les autres actifs, jugés instables ou non adaptés à la stratégie, ont été écartés pour éviter tout sur-apprentissage.

## Configurations Validées (Sweet Spots)

### NVO (Novo Nordisk)
- **10m** : `length=149`, `mult=0.7`, `signal_mode=Close`, `use_safety_stop=false`
- **15m** : `length=110`, `mult=0.6`, `signal_mode=Close`, `use_safety_stop=false`
- **20m** : `length=84`, `mult=0.5`, `signal_mode=Close`, `use_safety_stop=false`
- **30m** : `length=57`, `mult=2.8`, `signal_mode=Close`, `use_safety_stop=false`
- **45m** : `length=49`, `mult=2.1`, `signal_mode=Close`, `use_safety_stop=false`
- **60m** : `length=15`, `mult=1.1`, `signal_mode=Live`, `use_safety_stop=false`
- **120m** : `length=21`, `mult=1.1`, `signal_mode=Close`, `use_safety_stop=false`
- **240m** : `length=51`, `mult=1.5`, `signal_mode=Close`, `use_safety_stop=false`

### AMS.MC (Amadeus IT Group)
- **10m** : `length=113`, `mult=1.0`, `signal_mode=Close`, `use_safety_stop=false`
- **15m** : `length=66`, `mult=1.0`, `signal_mode=Live`, `use_safety_stop=false`
- **20m** : `length=49`, `mult=0.9`, `signal_mode=Live`, `use_safety_stop=false`
- **30m** : `length=34`, `mult=0.5`, `signal_mode=Close`, `use_safety_stop=false`
- **45m** : `length=20`, `mult=0.5`, `signal_mode=Live`, `use_safety_stop=false`
- **60m** : `length=74`, `mult=3.0`, `signal_mode=Close`, `use_safety_stop=false`
- **120m** : `length=140`, `mult=0.6`, `signal_mode=Close`, `use_safety_stop=false`

### NVS (Novartis)
- **10m** : `length=11`, `mult=2.6`, `signal_mode=Live`, `use_safety_stop=false`
- **60m** : `length=47`, `mult=3.0`, `signal_mode=Close`, `use_safety_stop=false`
- **120m** : `length=100`, `mult=1.0`, `signal_mode=Close`, `use_safety_stop=false`
- **240m** : `length=13`, `mult=1.3`, `signal_mode=Close`, `use_safety_stop=false`
