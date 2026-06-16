# Synthèse Stratégique : Lorentzian Classification

**Statut Actuel** : Passe 3 (Lissage & Exits) analysée. Stratégie 100% VALIDÉE.
**Prochaine Étape** : Déploiement en production / Paper Trading.

---

## 1. État de la Recherche

La stratégie **Lorentzian Classification** utilise un modèle Machine Learning non-paramétrique (KNN) basé sur la distance Lorentzienne pour classer les signaux à l'aide de 5 features techniques (RSI, WaveTrend, CCI, ADX, RSI2).

* **Passe 1 (KNN & Features)** : A mis en évidence le fait que le modèle brut était extrêmement puissant sur la détection directionnelle, mais générait de faux signaux insoutenables causant des Drawdowns profonds (notamment sur NVO).
* **Passe 2 (Filtres Macro)** : A été un triomphe. L'ajout des filtres de confirmation (ADX, EMA et Filtre de Régime) a purifié les signaux d'entrée. Le Drawdown de **NVO** a été divisé par 3 (tombant à -19%) tout en préservant un Alpha net de +1518 €. **GMAB** et **FPE.DE** affichent des Profit Factors superbes (jusqu'à 2.73) avec des Drawdowns infimes (< 2%), confirmant la viabilité de l'approche hybride ML + Macro.
* **Passe 3 (Lissage Nadaraya-Watson)** : A permis de peaufiner les points d'entrée finaux. Le Kernel a fait exploser le Profit Factor de **FPE.DE** à 2.68 et a encore réduit le Drawdown de **NVO** (tombant à un excellent -15.10%). Les sorties dynamiques (`use_dynamic_exits`) ont majoritairement été rejetées par l'optimiseur.

---

## 2. Planification et Intégration

### Configurations Finales (Prêtes pour la Production)

La campagne d'optimisation est terminée. Voici les configurations "Sweet Spots" validées incluant les 3 passes d'optimisation (Machine Learning + Contexte Macro + Lissage Statistique) :

🟢 **NVO (L'Équilibre Puissance/Risque)**
* **20m** : `neighbors_count: 17`, features passe 1 verrouillés, `use_volatility_filter: True`, `use_regime_filter: True`, `regime_threshold: -0.1`, autres filtres macro à `False`. Paramètres Kernel : `use_kernel_filter = True`, `kernel_h = 3`, `kernel_r = 12.5`, `kernel_x = 10`, `kernel_lag = 4`, `use_dynamic_exits = False`.

🟢 **GMAB (La Précision Maximale)**
* **30m** : `neighbors_count: 19`, features passe 1 verrouillés, `use_volatility_filter: True`, `use_regime_filter: True`, `regime_threshold: -0.5`, `use_adx_filter: True`, `adx_threshold: 16`, `use_ema_filter: True`, `ema_period: 164`. Paramètres Kernel : `use_kernel_filter = True`, `kernel_h = 3`, `kernel_r = 3.0`, `kernel_x = 37`, `kernel_lag = 5`, `use_dynamic_exits = False`.

🟢 **FPE.DE (La Sécurité Absolue)**
* **120m** : `neighbors_count: 3`, features passe 1 verrouillés, `use_volatility_filter: True`, `use_regime_filter: True`, `regime_threshold: -0.3`, `use_adx_filter: True`, `adx_threshold: 19`, autres filtres macro à `False`. Paramètres Kernel : `use_kernel_filter = True`, `kernel_h = 3`, `kernel_r = 2.8`, `kernel_x = 15`, `kernel_lag = 4`, `use_dynamic_exits = False`.



