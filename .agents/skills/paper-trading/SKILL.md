---
name: "paper-trading"
description: "Expert en simulation de trading temps réel, sécurité et optimisation de base de données en Paper Trading local."
---

# Spécialisation: paper-trading

## 1. Rôle et Objectifs
L'agent incarnant cette spécialisation est garant de la robustesse, de la sécurité et des performances du moteur de simulation de trading local (`PaperTradingEngine` associé au `SignalExecutor`). Ce moteur interagit en temps réel avec Redis (réception des signaux) et PostgreSQL (persistance de l'état des portefeuilles et des ordres) pour exécuter des ordres virtuels tout en conservant une logique et un comportement proches de l'exécution Live (calcul de la NAV, gestion des slippages, des commissions, et des flux de signaux).

## 2. Principes Fondamentaux & Contraintes

- **Double Pile de Connexion SQL** (Centralisée dans `connection.py`) :
  - **Pile Asynchrone (`asyncpg`)** : Réservée exclusivement aux endpoints et middlewares de l'API FastAPI afin de maximiser la réactivité et le débit sous forte concurrence.
  - **Pile Synchrones (`psycopg2`)** : Réservée aux daemons de calcul longs, aux backtests, et au Paper Trading Engine tournant en tâche de fond pour garantir la thread-safety et éviter la complexité de l'asynchronisme distribué.
- **Mécanisme SQL Anti-N+1** : Interdiction absolue de réaliser des boucles de requêtes individuelles par actif pour la valorisation. Les mises à jour de la Net Asset Value (NAV) doivent être vectorisées en utilisant des sélections groupées via la clause `IN ($1, $2...)` et des transactions groupées.
- **Timeouts Réseau & Robustesse** : Tout appel HTTP sortant vers des APIs tierces doit obligatoirement inclure un timeout explicite (10s par défaut). Gérer les exceptions métiers via des classes dédiées (`SignalExecutionError`, `PortfolioUpdateError`) et interdire les captures génériques du type `except Exception` non documentées ou sans traçabilité.
- **Sécurité et Authentification FastAPI** :
  - **Session HMAC** : Authentification par Cookie de Session signé via HMAC-SHA256 (utilisant `HMAC_SECRET` et validant `PAPER_TRADER_PASSWORD`).
  - **Double Submit Cookie CSRF** : Protection CSRF stricte par vérification croisée du cookie `csrftoken` et du header HTTP `X-CSRFToken`.
  - **Headers de Sécurité** : Application stricte des en-têtes CORS restrictifs, Content Security Policy (CSP) stricte, HSTS, X-Content-Type-Options et X-Frame-Options.
- **Validation Strict et Typée (Pydantic)** : Toutes les configurations de stratégies et paramètres d'indicateurs doivent utiliser la validation stricte des types primitifs de Pydantic et être configurées avec `extra='allow'` afin de pouvoir évoluer sans planter le parser.
- **Erreurs Anonymisées** : Utilisation d'un utilitaire global `safe_error_response` interceptant les exceptions système au niveau de l'API FastAPI. Il enregistre la stacktrace réelle complète côté serveur avec un UUID de corrélation unique, et renvoie au client web une réponse d'erreur générique anonymisée contenant cet UUID.

## 3. Schémas de Référence (Patterns)

### A. Calcul et Mise à Jour Bulk de la NAV (Sans N+1, Synchrone)
```python
import logging
from decimal import Decimal
from typing import List, Dict
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

class PortfolioUpdateError(Exception):
    """Exception levée en cas d'échec de la mise à jour d'un portefeuille."""
    pass

def update_portfolio_nav_bulk(conn, portfolio_ids: List[int], prices: Dict[str, Decimal]) -> None:
    """
    Met à jour la NAV de plusieurs portefeuilles en minimisant les allers-retours SQL (Anti-N+1).
    Utilise la connexion synchrone psycopg2.
    """
    if not portfolio_ids:
        return

    try:
        with conn.cursor() as cur:
            # 1. Sélectionner toutes les positions pour les portefeuilles cibles en une seule requête
            cur.execute(
                """
                SELECT portfolio_id, asset, qty 
                FROM positions 
                WHERE portfolio_id IN %s
                """,
                (tuple(portfolio_ids),)
            )
            positions = cur.fetchall()

            # Consolidation des valeurs des positions par portefeuille
            portfolio_vals = {pid: Decimal("0.0") for pid in portfolio_ids}
            for pid, asset, qty in positions:
                price = prices.get(asset, Decimal("0.0"))
                portfolio_vals[pid] += qty * price

            # 2. Récupérer le cash de chaque portefeuille en une seule requête
            cur.execute(
                """
                SELECT id, cash 
                FROM portfolios 
                WHERE id IN %s
                """,
                (tuple(portfolio_ids),)
            )
            portfolios_cash = cur.fetchall()

            # Ajouter le cash au calcul final de la NAV
            for pid, cash in portfolios_cash:
                portfolio_vals[pid] += cash

            # 3. Effectuer la mise à jour des NAV en base de données en une seule transaction
            for pid, nav_val in portfolio_vals.items():
                cur.execute(
                    """
                    UPDATE portfolios 
                    SET nav = %s, updated_at = NOW() 
                    WHERE id = %s
                    """,
                    (nav_val, pid)
                )
            
            conn.commit()
            logger.info(f"Mise à jour bulk de la NAV réussie pour {len(portfolio_ids)} portefeuilles.")

    except psycopg2.Error as e:
        conn.rollback()
        logger.exception("Échec SQL lors de la mise à jour bulk de la NAV")
        raise PortfolioUpdateError(f"Impossible de recalculer la NAV : {e}") from e
```

### B. Validation Sécurisée Pydantic des Paramètres d'Indicateurs
```python
from pydantic import BaseModel, Field, root_validator
from typing import Dict, Any

class StrategyIndicatorConfig(BaseModel):
    indicator_name: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Flexibilité pour les nouveaux indicateurs
        allow_mutation = False # Immutabilité recommandée

    @root_validator(pre=True)
    def validate_safe_primitives(cls, values):
        """
        Garantit que seuls des types primitifs sécurisés sont transmis
        pour éviter les injections d'objets complexes.
        """
        params = values.get("parameters", {})
        if isinstance(params, dict):
            for key, val in params.items():
                if not isinstance(val, (int, float, str, bool, type(None))):
                    raise ValueError(
                        f"Type de paramètre non autorisé pour '{key}': {type(val)}. "
                        "Seuls les types primitifs (int, float, str, bool, None) sont admis."
                    )
        return values
```

### C. Gestion fastapi des Erreurs Anonymisées (`safe_error_response`)
```python
import uuid
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

def safe_error_response(request: Request, exc: Exception) -> JSONResponse:
    """
    Middleware ou gestionnaire d'exception global FastAPI qui anonymise les erreurs
    pour le frontend tout en conservant la stacktrace complète dans les logs du serveur.
    """
    correlation_id = str(uuid.uuid4())
    
    # Log de la stacktrace complète côté serveur
    logger.exception(
        f"Exception non gérée détectée [Correlation ID: {correlation_id}] "
        f"lors du traitement de la requête {request.method} {request.url.path}"
    )

    # Réponse propre et anonyme pour le frontend
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Une erreur système inattendue est survenue.",
            "correlation_id": correlation_id
        }
    )
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Requêtes N+1** : Lancer un `SELECT` ou `UPDATE` de portefeuille à l'intérieur d'une boucle itérant sur les signaux ou actifs.
- ❌ **Fuites de Stacktrace (Information Disclosure)** : Retourner directement les messages d'erreurs bruts ou les détails de la pile d'exécution Python aux requêtes HTTP du frontend.
- ❌ **Mélange des piles de connexions** : Utiliser la connexion synchrone `psycopg2` dans le contexte asynchrone FastAPI (bloquant le thread de l'event loop) ou inversement.
- ❌ **Validation permissive** : Ignorer la validation des types de paramètres passés aux indicateurs de stratégie ou admettre des objets complexes/sérialisés instables.

## 5. Interactions avec les autres Skills
- Reçoit les signaux normalisés et les données de marché de `market-data-ingestion`.
- Évalue l'ordre via `execution-order-routing` en vérifiant la cohérence des comptes virtuels.
- Applique les règles de contrôle des risques (ex: taille maximale des positions) issues de `risk-money-management`.
