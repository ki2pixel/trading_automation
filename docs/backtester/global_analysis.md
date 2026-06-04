# Analyse Globale (Global Analysis)

**TL;DR** : Ne lisez pas 50 rapports JSON éparpillés pour comprendre si votre stratégie est bonne. Le module d'Analyse Globale agglomère les résultats d'optimisation de chaque actif dans une seule vue HTML dynamique.

Vous venez de terminer l'optimisation bayésienne de votre stratégie sur 30 paires de devises. Vous avez 30 dossiers remplis de fichiers JSON et CSV. Vous souhaitez savoir quels actifs performent le mieux et si les paramètres optimaux sont stables à travers les marchés. Vous commencez à ouvrir chaque fichier à la main pour copier les valeurs de Ratio de Sharpe dans un tableur.

C'est la fragmentation des résultats. Lorsqu'on opère à l'échelle d'un portefeuille, évaluer une stratégie un actif à la fois est inefficace et propice aux erreurs.

Pour pallier cela, le module `global_analysis.py` scanne tous les résultats et génère un tableau de bord HTML unifié.

### ❌ L'Approche Manuelle

Analyser les données actif par actif :

1. Ouvrir le rapport JSON de l'EUR/USD.
2. Noter le Profit Factor et le DSR.
3. Répéter l'opération pour 29 autres paires.
4. Tenter de déduire une tendance générale.

### ✅ L'Approche par Synthèse Globale

Générer un tableau de bord interactif d'une simple ligne de commande :

```python
# Agrège tous les répertoires de résultats dans un tableau triable
generate_global_analysis(strategy="hma_crossover", output_dir="reports/local_optimizer")
```

## L'Architecture du Rapport

Le module `global_analysis.py` parcourt la structure de répertoires des rapports d'optimisation et extrait les données des fichiers `optimization_summary.json` et `best_parameters.json`. 

Au lieu de dépendre d'un serveur web lourd (comme Flask ou Streamlit) pour visualiser ces données, il génère un simple fichier HTML statique. Ce fichier inclut du JavaScript "vanilla" pour permettre le tri des colonnes directement dans le navigateur du client.

### Compromis de Visualisation

| Approche | Dépendances Requises | Interactivité | Vitesse de Déploiement |
| -------- | -------------------- | ------------- | ---------------------- |
| Serveur Web (Streamlit/Dash) | ❌ Fortes (Python/Serveur) | ✅ Avancée | ❌ Lente |
| HTML Statique Généré | ✅ Aucune (Navigateur) | ❌ Basique (tri) | ✅ Instantanée |

## La Règle d'Or : Zéro Dépendance pour les Rapports

Les rapports de performance doivent être portables. Si vous devez installer un environnement virtuel complet juste pour lire les résultats d'un backtest, votre système de reporting est trop complexe. Un fichier HTML statique s'ouvre partout.
