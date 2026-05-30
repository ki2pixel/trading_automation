# Consolider ses optimisations : Le module Global Analysis

**TL;DR** : Le module `global_analysis.py` regroupe, compare et synthétise les recommandations d'optimisation de tous tes symboles en un seul tableau HTML interactif et stylisé.

Tu as optimisé ta stratégie HMA Crossover sur 15 actions différentes (dont `GMAB`, `LOGI` et `ZEAL.CO`). Pour chaque symbole, l'optimizer t'a généré un sous-dossier rempli de fichiers JSON, de rapports et de courbes. 

À cet instant, tu te retrouves face à un problème pratique : comment comparer ces performances d'un seul coup d'œil ? Comment savoir quelle action offre le meilleur ratio de Sharpe ou le drawdown le plus faible avec cette stratégie ? Ouvrir 15 dossiers différents et recopier manuellement les chiffres dans un tableur est fastidieux.

Le module **Global Analysis** est fait pour cela. Il parcourt automatiquement tes dossiers d'optimisation, extrait les meilleures configurations et te génère une synthèse interactive unique.

---

## Le flux de fonctionnement

Une fois tes optimisations terminées, le script scanne récursivement le répertoire de ta stratégie sous `reports/local_optimizer/<strategy>/`. 

Pour chaque symbole rencontré, il extrait :
- Le meilleur run absolu (la performance maximale théorique).
- Le run recommandé (situé au centre de la zone de stabilité géométrique).
- Les sweet spots associés aux indicateurs, avec leur niveau de confiance.

Il compile ensuite ces informations dans deux fichiers uniques situés sous `reports/local_optimizer/<strategy>/`.

---

## Les formats de sortie

### 1. Le rapport interactif (`global_summary.html`)
C'est un tableau HTML stylisé et interactif. C'est l'outil parfait pour ta comparaison visuelle. Tu peux trier les colonnes en un clic pour voir instantanément :
- Quels symboles obtiennent les ratios Sharpe les plus robustes (`REC_SHARPE`).
- Si l'écart de profit entre le meilleur run absolu (`BEST_PNL`) et le run recommandé (`REC_PNL`) est acceptable.
- Quels sont les sweet spots de paramètres pour chaque action.

### 2. Le fichier de données brut (`global_summary.parquet`)
Un fichier Parquet compressé avec Zstandard (`zstd`). Si tu aimes faire tes propres analyses sous Python (avec Pandas) ou dans des outils de Business Intelligence (BI) comme Tableau ou PowerBI, c'est le format idéal pour charger toutes les métriques en une milliseconde.

---

## Utilisation en pratique

### Par le code Python
Pour intégrer la génération de la synthèse dans tes scripts d'automatisation :

```python
from backtest_engine.global_analysis import generate_global_analysis

# Compile les résultats pour HMA Crossover
result_paths = generate_global_analysis(
    repo_root=".",
    strategy="hma_crossover"
)

print(result_paths)
# Affiche les liens :
# {
#   "parquet": "reports/local_optimizer/hma_crossover/global_summary.parquet",
#   "html": "reports/local_optimizer/hma_crossover/global_summary.html"
# }
```

### Via l'API REST FastAPI
Si tu utilises l'interface web, tu n'as même pas besoin d'ouvrir ton terminal. Le serveur FastAPI expose un endpoint dédié qui déclenche le calcul de la synthèse à la volée et te renvoie les fichiers d'un simple clic :

- **`GET /api/global-analysis/{strategy}`** : Déclenche la compilation et renvoie les liens de téléchargement vers le Parquet et l'HTML interactif.
