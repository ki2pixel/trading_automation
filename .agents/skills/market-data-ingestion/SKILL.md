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
- **Mode Public-Only sans Clé (Render)**: Sur les environnements comme Render, l'ingestion des prix Bybit doit pouvoir s'exécuter sans clés privées configurées. Seuls les endpoints publics sont interrogés, et les endpoints signés ne doivent pas être appelés (lever une erreur ValueError explicite et contrôlée en cas de tentative).
- **Timeouts Réseau & Backoff Exponentiel**: Obligatoire pour toute interaction réseau. Chaque appel API doit comporter un timeout réseau centralisé (ex: `10.0`s). En cas de code `429 Too Many Requests` ou `5xx`, implémenter une logique de retries automatiques (ex: avec `tenacity` et backoff exponentiel).
- **Normalisation**: Les structures de données reçues de courtiers distincts doivent être standardisées avant d'entrer dans le pipeline ou la DB.
- **Nettoyage et Imputation**: Gérer les trous de liquidité. Ne jamais forwarder des valeurs `NaN` ou infinies. Si une bougie manque, imputer via Forward Fill ou interpoler selon le contexte.
- **Précision Financière (Live)**: Lors de l'ingestion de flux en direct destinés à l'exécution, les prix critiques (bid, ask, close) doivent être obligatoirement parsés en `decimal.Decimal` pour éviter toute perte de précision.
- **Robustesse Redis Pub/Sub**: Pour contrer les déconnexions silencieuses du réseau Aiven/Render, toute initialisation de client Redis pour Pub/Sub ou écoute de signaux doit activer le keepalive TCP (`socket_keepalive=True`) et définir un intervalle de health check régulier (ex: `health_check_interval=30`).

## 3. Schémas de Référence (Patterns)

### A. Gestion Résiliente des API REST (Rate Limiting & Timeouts)
```python
import asyncio
import logging
from typing import Optional, Dict, Any
from httpx import HTTPStatusError, RequestError, TimeoutException

logger = logging.getLogger(__name__)

async def fetch_with_backoff(client, url: str, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """
    Pattern obligatoire de backoff exponentiel pour l'ingestion.
    Utilise des exceptions réseau explicites, respecte le timeout de 10s par défaut
    et enregistre les traces de pile via logger.exception().
    """
    for attempt in range(max_retries):
        try:
            # Appel HTTP asynchrone avec timeout explicite de 10s
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
            
        except TimeoutException as e:
            wait_time = 2 ** attempt
            logger.warning(f"Timeout lors du fetch sur {url} (Tentative {attempt+1}/{max_retries}). Réessai dans {wait_time}s. Erreur: {e}")
            await asyncio.sleep(wait_time)
            
        except HTTPStatusError as e:
            # Ne réessayer que pour les codes 5xx (serveur) ou 429 (rate limit)
            if e.response.status_code == 429 or e.response.status_code >= 500:
                wait_time = 2 ** attempt
                logger.warning(f"Erreur HTTP {e.response.status_code} sur {url} (Tentative {attempt+1}/{max_retries}). Réessai dans {wait_time}s. Erreur: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.exception(f"Erreur HTTP fatale {e.response.status_code} sur {url}. Pas de réessai.")
                raise
                
        except RequestError as e:
            wait_time = 2 ** attempt
            logger.warning(f"Erreur réseau de transport sur {url} (Tentative {attempt+1}/{max_retries}). Réessai dans {wait_time}s. Erreur: {e}")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            # Capture de toute autre exception inattendue avec stacktrace complète
            logger.exception(f"Erreur inattendue non gérée lors du fetch sur {url}")
            raise
            
    logger.error(f"Échec critique de fetch_with_backoff sur {url} après {max_retries} tentatives.")
    raise ConnectionError(f"API inaccessible: {url} après {max_retries} tentatives.")
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
- Envoie les données persistantes à `local-parquet-storage`.
- Alimente directement en RAM le `indicator-generation` pour la création de signaux live.
