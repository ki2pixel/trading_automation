# Walkthrough : Moteur de Screening Statistique et Qualification des Actifs

Ce document résume l'implémentation et la validation du cadre quantitatif de screening pour les nouveaux actifs.

---

## 1. Modifications Apportées

Nous avons mis en œuvre les composants suivants :
1.  **Dépendances Externes** : Ajout de `scipy` et `statsmodels` à [requirements-backtest-engine.txt](file:///home/kidpixel/trading_automation_v2/requirements-backtest-engine.txt) et installation réussie dans l'environnement.
2.  **Module Noyau de Screening** : Création de [screening.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/screening.py) contenant les fonctions de calcul vectorisé de :
    *   L'exposant de Hurst ($H$)
    *   La statistique ADF et sa $p$-value (via `statsmodels`)
    *   La demi-vie d'Ornstein-Uhlenbeck ($\tau$)
    *   La distance de Mahalanobis (via `scipy`)
    *   La volatilité historique réalisée et l'ADV quotidien en devise.
3.  **Générateur de Baseline** : Création et exécution du script [generate_baselines.py](file:///home/kidpixel/trading_automation_v2/scripts/generate_baselines.py) qui extrait les signatures des 9 actifs phares existants (en gérant les résolutions 1m et 5m) et calcule la matrice de covariance globale. Ce script a généré le fichier de configuration de référence [baselines_signatures.json](file:///home/kidpixel/trading_automation_v2/configs/baselines_signatures.json).
4.  **CLI de Screening Parallélisé** : Création du script [screen_candidates.py](file:///home/kidpixel/trading_automation_v2/scripts/screen_candidates.py) capable de scanner l'ensemble des candidats du portefeuille en parallèle (jusqu'à 15 workers), de filtrer les doublons temporels, et de produire le rapport final.

---

## 2. Validation et Tests Automatisés

Nous avons créé une suite complète de tests unitaires dans [test_screening.py](file:///home/kidpixel/trading_automation_v2/tests/test_screening.py).

### Résultats des Tests Pytest
La commande de validation a retourné un succès total :
```bash
PYTHONPATH=. pytest tests/test_screening.py -v
```
```text
tests/test_screening.py::test_calculate_hurst_exponent PASSED            [ 16%]
tests/test_screening.py::test_calculate_adf_statistic PASSED             [ 33%]
tests/test_screening.py::test_calculate_half_life PASSED                 [ 50%]
tests/test_screening.py::test_get_mahalanobis_distance PASSED            [ 66%]
tests/test_screening.py::test_calculate_adv_currency PASSED              [ 83%]
tests/test_screening.py::test_calculate_realized_volatility PASSED       [100%]
============================== 6 passed in 0.79s ===============================
```

---

## 3. Résultats du Screening Manuel (LOGI)

Nous avons lancé le screening complet sur l'ensemble de notre univers d'actifs, y compris le symbole candidat `LOGI`.

Le script a généré le fichier [screening_report.md](file:///home/kidpixel/trading_automation_v2/reports/screening_report.md) avec les conclusions suivantes :
*   **Qualifié** : Le symbole **LOGI** a été validé à **15 minutes** pour la stratégie `hmm_regime_filter` avec une distance de Mahalanobis $D_M = 2.35 \le 2.5$. Son profil statistique est compatible (Hurst $H = 0.50$, ADV = 3 223 M€, 10.5 ans d'historique).
*   **Exclusion de FPE.DE** : Exclu pour non-respect du critère de liquidité (ADV de 0.42M€ $< 1.0$M€ minimum requis pour l'admission de nouveaux actifs).
*   **Éligibilité des autres configurations** : Les 8 autres actifs de référence se situent bien dans la zone d'acceptation idéale (distance de Mahalanobis $D_M = 0.00$ sur leur TF/stratégie nominale).

---

## 4. Résultats du Screening des Nouveaux Symboles

Un deuxième screening a été effectué sur l'univers de 189 nouveaux symboles 1m, en excluant les actifs de référence et `LOGI` déjà qualifiés. Le rapport complet est disponible dans [screening_report_new_symbols.md](file:///home/kidpixel/trading_automation_v2/reports/screening_report_new_symbols.md).

**Observations clés :**
*   **Nombreux actifs qualifiés** : Plus d'une centaine de configurations (symbole/timeframe/stratégie) sont éligibles.
*   **Dominance de `hmm_regime_filter`** : Un grand nombre d'actifs présentent des distances de Mahalanobis très faibles ($D_M < 1.0$) pour cette stratégie (ex: `rmsfreur`, `mrkdeeur`, `dpwdeeur`, `capfreur`, etc.).
*   **Stratégie `cybernetic_hilbert`** : Plusieurs actifs se qualifient avec succès pour cette stratégie (ex: `orafreur`, `raceiteur`, `basdeeur`).
*   Tous les candidats retenus respectent scrupuleusement l'ADV minimum de 1 M€ et possèdent un historique validé de plus d'1 an.
