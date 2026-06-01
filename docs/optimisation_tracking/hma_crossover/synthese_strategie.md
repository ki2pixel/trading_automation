# Synthèse Stratégique : HMA Crossover

**Statut Actuel** : Analyse terminée (Stratégie à 1 passe). Configurations figées et validées.  
**Prochaine Étape** : Intégration en production live.

---

## 1. État de la Recherche

La stratégie **HMA Crossover** est une approche de suivi de tendance basée sur le croisement de deux moyennes mobiles de Hull (Hull Moving Average). En tant que stratégie de Catégorie A, elle nécessite une seule passe d'optimisation.

Les résultats de cette optimisation montrent que :
* La stratégie souffre sur les actifs très hachés ou en range prolongé (scores négatifs face au Buy & Hold pour la majorité des actifs testés).
* Un "Edge" net a été identifié et validé sur **FPE.DE**, **NVS**, et **GMAB**.
* Les zones de paramètres (fast_len et slow_len) sont restées stables sur plusieurs timeframes consécutifs (particulièrement pour FPE.DE entre 30m et 120m), confirmant la robustesse du signal.

---

## 2. Planification et Intégration Finale

### Configurations Validées (Setup HMA Crossover)
* **FPE.DE 30m** : `fast_len=40`, `slow_len=98`, `source_col=high`, `confirm_on_close=True` (Score: 9.4680)
* **NVS 120m** : `fast_len=10`, `slow_len=153`, `source_col=low`, `confirm_on_close=False` (Score: 7.9580)
* **GMAB 45m** : `fast_len=16`, `slow_len=68`, `source_col=low`, `confirm_on_close=False` (Score: 4.5009)

### Étape Suivante
L'optimisation de la stratégie HMA Crossover est considérée comme achevée. Les configurations ci-dessus sont prêtes à être intégrées au sein du moteur de production live.
