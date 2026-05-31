---
name: "local-parquet-storage"
description: "Expert en gestion locale et vectorisée de données de marché via Parquet"
---

# Spécialisation: local-parquet-storage

## 1. Rôle et Objectifs
L'agent en charge de cette spécialisation est responsable du stockage, de l'indexation et du requêtage hautement performant des données financières sur le disque local. Au lieu d'utiliser une base de données distante, le système s'appuie sur le format Parquet (`pyarrow` / `fastparquet`) pour garantir des I/O ultrarapides et une intégration native avec Pandas.

## 2. Principes Fondamentaux & Contraintes

- **Format Binaire (Parquet vs CSV)**: Ne jamais utiliser de fichiers `.csv` pour le stockage en production de séries temporelles (ticks, candles). Le format Parquet est obligatoire pour sa compression en colonnes et sa vitesse de lecture.
- **Indexation Temporelle**: Lors de la sauvegarde d'un DataFrame, s'assurer que l'index (ex: `time`) ou les colonnes de filtrage (ex: `symbol`) sont correctement typés (Datetime UTC).
- **Partitionnement par Dossiers**: Pour des datasets massifs (ex: ticks tick-par-tick sur plusieurs années), partitionner les fichiers physiquement sur le disque par année/mois ou par symbole (ex: `dataset/symbol=AAPL/year=2025/data.parquet`).
- **Lazy Loading / Memory Mapping**: Pour analyser de gros volumes sans saturer la RAM, utiliser les capacités de lecture par partitions (`pyarrow.dataset`) ou les lectures filtrées (`filters` dans `read_parquet`).

## 3. Schémas de Référence (Patterns)

### A. Sauvegarde Optmisée d'un DataFrame
```python
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def save_market_data(df: pd.DataFrame, file_path: str):
    """
    Sauvegarde un DataFrame Pandas au format Parquet avec compression Snappy.
    Le DataFrame doit avoir un DatetimeIndex.
    """
    # Vérification des types
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("L'index doit être un DatetimeIndex")
        
    # L'utilisation de engine='pyarrow' est recommandée pour la performance
    df.to_parquet(
        file_path, 
        engine='pyarrow',
        compression='snappy',
        index=True
    )
```

### B. Lecture Filtrée (Éviter le Out-of-Memory)
```python
import pandas as pd

def load_symbol_data(file_path: str, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Charge uniquement les données nécessaires depuis un gros fichier Parquet 
    sans charger le fichier complet en mémoire.
    """
    # pyarrow permet de filtrer pendant la lecture (pushdown predicates)
    filters = [
        ('symbol', '=', symbol),
        ('time', '>=', pd.Timestamp(start_date)),
        ('time', '<=', pd.Timestamp(end_date))
    ]
    
    # Seules les données correspondant au filtre atterrissent en RAM
    df = pd.read_parquet(
        file_path,
        engine='pyarrow',
        filters=filters
    )
    return df
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Fragmentation**: Sauvegarder un fichier parquet différent pour chaque petite mise à jour de 5 minutes (crée des milliers de petits fichiers qui détruisent les performances I/O). Toujours batcher (regrouper) les écritures.
- ❌ **Perte des Fuseaux Horaires**: Convertir un DataFrame avec des timestamps timezone-aware en timezone-naive avant la sauvegarde. Toujours conserver le fuseau horaire (idéalement UTC).
- ❌ **Over-Partitioning**: Créer trop de partitions (ex: un dossier par jour par symbole) pour de petits datasets, ce qui entraîne un surcoût lors de la lecture des métadonnées du dataset.

## 5. Interactions avec les autres Skills
- Persiste sur le disque les données nettoyées par `market-data-ingestion`.
- Alimente en mémoire massive le `backtesting-engine`.
