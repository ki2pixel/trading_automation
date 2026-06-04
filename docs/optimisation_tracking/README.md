# Suivi et Consignation des Optimisations

Ce répertoire centralise les résultats d'analyse issus de l'optimisation séquentielle (en plusieurs passes) des stratégies de trading.
L'objectif est de garder une trace des décisions prises (les "sweet spots") à chaque étape pour éviter l'explosion combinatoire et le sur-apprentissage (overfitting).

## Méthodologie

Conformément à la feuille de route (`configs/strategies/README_OPTIMIZATION_ROADMAP.md`), chaque stratégie est divisée en plusieurs passes logiques :
1. **Passe 1** : Validation du signal brut (Moyennes mobiles, Bandes de volatilité, etc.)
2. **Passe 2** : Gestion de l'activité, filtres (RSI, VWAP) ou Timing (Intraday)
3. **Passe 3** : Gestion avancée des sorties (Trailing Stops, Ladder, Risk-Management)

### Structure des dossiers

Stratégies documentées :
- `pmax_explorer/` : Suivi de tendance avec Trailing Stop ATR (Passe 1 et 2 complétées)
- `hma_crossover/` : Suivi de tendance par croisement de moyennes mobiles de Hull (Stratégie à 1 passe, complétée)
- `3commas_bot/` : Croisement de MAs (Passe 1, 2 et 3 complétées)

Chaque stratégie dispose de son propre sous-dossier contenant :
- Un fichier par passe (ex: `passe_1_signal.md`) qui détaille les résultats de l'optimiseur, les symboles et timeframes performants, et les paramètres retenus.
- Un fichier `synthese_strategie.md` qui consolide **uniquement** les paramètres validés et figés en dur pour les prochaines passes.

## Critères d'analyse d'une Passe

Lorsqu'une passe est terminée (ex: `/mnt/venv_ext4/trading_automation_v2/reports/...`), on vérifie :
1. **Le nombre d'itérations éligibles** : S'il est de 0, cela signifie souvent que les filtres du backtest (`min_closed_trades`, `max_drawdown_pct`) étaient trop stricts pour un signal brut, ou que la timeframe n'est pas adaptée au symbole.
2. **La robustesse du score** : On cherche des zones de paramètres stables plutôt que des pics isolés.
3. **Le comportement par actif (Symbol/Timeframe)** : Les stratégies intraday réagissent très différemment selon la liquidité et la volatilité du sous-jacent.

## Outil d'Analyse Automatique

Pour vous faire gagner du temps lors de l'analyse d'une nouvelle passe (où des dizaines de dossiers de rapports sont générés), un script Python réutilisable a été créé : `analyze_reports.py`. 

Il parcourt récursivement tous les sous-dossiers (par symbole et par run) et produit un tableau récapitulatif montrant le nombre d'itérations éligibles et le meilleur score trouvé pour chaque unité de temps (Timeframe).

### Utilisation

Depuis la racine du projet, exécutez le script en lui passant le chemin du répertoire de la stratégie à analyser :

```bash
python3 docs/optimisation_tracking/analyze_reports.py /mnt/venv_ext4/trading_automation_v2/reports/local_optimizer/NOM_DE_LA_STRATEGIE
```

**Exemple d'affichage :**
```text
Analyse des rapports dans : /mnt/venv_ext4/.../noise_boundary_intraday
Symbol     | Timeframe | Eligible Iterations | Best Score
-----------------------------------------------------------------
AMS.MC     | 120m      | 239                 | 183.1899
AMS.MC     | 60m       | 432                 | 156.7088
EVD.DE     | 60m       | 0                   | N/A
```
Ce résumé vous permet de savoir instantanément quels symboles ou timeframes justifient qu'on s'y attarde pour définir les paramètres de la passe suivante.
