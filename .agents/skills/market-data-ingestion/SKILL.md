---
name: "market-data-ingestion"
description: "Spécialiste de la collecte et de la normalisation des flux de marché"
---

# Spécialisation: market-data-ingestion

## 1. Rôle et Objectifs
L'agent incarnant cette spécialisation est chargé de collecter, normaliser et distribuer les données de marché (ticks, order books, candles).
L'ingestion doit être résiliente (tolérance aux pannes réseau), conforme aux limitations de l'API (Rate Limiting), et assurer une propreté mathématique des données (gestion des valeurs aberrantes).

## 2. Principes Fondamentaux & Contraintes

- **WebSockets pour le Temps Réel**: Privilégier les connexions WebSocket persistantes pour les flux temps réel. Utiliser les API REST uniquement pour les requêtes historiques ou les snapshots de récupération.
- **Backoff Exponentiel**: Obligatoire pour toute interaction réseau. Si une API (ex: Trading 212) renvoie un `429 Too Many Requests` ou un `5xx`, implémenter un retry intelligent.
- **Normalisation**: Les structures de données reçues de courtiers distincts doivent être standardisées avant d'entrer dans le pipeline du moteur de backtest ou de la DB.
- **Nettoyage et Imputation**: Gérer les trous de liquidité. Ne jamais forwarder des valeurs `NaN` ou infinies. Si une bougie manque, imputer via Forward Fill ou interpoler selon le contexte.

## 3. Schémas de Référence (Patterns)

### A. Gestion Résiliente des API REST (Rate Limiting)
```python
import asyncio
import logging
from typing import Optional, Dict, Any

async def fetch_with_backoff(url: str, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """
    Pattern obligatoire de backoff exponentiel pour l'ingestion.
    Respecte les coding standards sur l'asynchronisme et la fiabilité.
    """
    for attempt in range(max_retries):
        try:
            # Remplacer par l'appel aiohttp réel
            # response = await session.get(url)
            # response.raise_for_status()
            # return await response.json()
            pass
        except Exception as e:
            wait_time = 2 ** attempt
            logging.warning(f"Échec de connexion API ({e}). Tentative {attempt+1}/{max_retries}. Attente {wait_time}s.")
            await asyncio.sleep(wait_time)
            
    logging.error(f"Échec critique de fetch_with_backoff sur {url} après {max_retries} tentatives.")
    raise ConnectionError(f"API inaccessible: {url}")
```

### B. Déduplication et Nettoyage des Outliers (Pandas)
```python
import pandas as pd
import numpy as np

def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie un DataFrame de données de marché.
    """
    # 1. Déduplication basée sur le timestamp
    df = df[~df.index.duplicated(keep='last')]
    
    # 2. Imputation: Forward fill pour les trous mineurs
    df.ffill(inplace=True)
    
    # 3. Suppression des valeurs aberrantes (Z-score sur les rendements)
    # Exemple très simplifié: retirer les variations irréalistes > 50% en un tick
    returns = df['close'].pct_change()
    outliers = returns.abs() > 0.5
    if outliers.any():
        df.loc[outliers, 'close'] = np.nan
        df['close'].ffill(inplace=True) # Remplace l'outlier par le dernier prix valide
        
    return df
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ Lancer une boucle `while True` sans `asyncio.sleep()` ou mécanisme de throttling.
- ❌ Ignorer les événements de déconnexion WebSocket sans logique de reconnexion (reconnect-on-close).
- ❌ Stocker les données "brutes" sans validation de schéma. Pydantic ou des Dataclasses typées doivent toujours valider la payload JSON.
- ❌ Logger des tokens d'authentification API dans les logs lors des erreurs réseau.

## 5. Interactions avec les autres Skills
- Envoie les données persistantes à `database-supabase-postgres`.
- Alimente directement en RAM le `indicator-generation` pour la création de signaux live.
