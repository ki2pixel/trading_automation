# Architecture du Moteur de Paper Trading et Ingestion Live

**TL;DR**: Le système d'exécution s'appuie sur une séparation stricte entre l'ingestion temps réel des prix (écrite dans Redis/PostgreSQL) et la boucle d'évaluation synchrone du moteur de trading; cela permet de simuler avec précision et résilience des portefeuilles Trading 212 et Bybit EU.

Vous développez des stratégies quantitatives complexes en local. Vos backtests affichent des performances exceptionnelles sur l'historique de données. Vous décidez alors de sauter le pas vers le marché réel. Vous configurez un script simple qui boucle sur des requêtes HTTP pour acheter ou vendre en direct, et vous vous heurtez immédiatement à de multiples murs: latences d'API, coupures de réseau, ordres rejetés pour fractionnement non géré ou capital insuffisant; c'est le "baptême du feu" de la production.

Notre architecture de Paper Trading a été conçue pour éliminer ces frictions en agissant comme un véritable simulateur de vol financier avant tout déploiement de capital réel.

---

## Le simulateur de vol financier

Pour comprendre comment le système réagit sans risquer un seul centime, nous utilisons l'analogie d'un **simulateur de vol de pilotage**:

- Le cockpit et les commandes du pilote correspondent à l'interface de notre tableau de bord FastAPI/Web.
- Le moteur physique du simulateur (vent, gravité, aérodynamique) est représenté par notre base de données locale (PostgreSQL/Redis) et les vraies données de marché.
- Les pistes d'atterrissage et les connexions avec les bourses réelles sont modélisées par la double couche de connecteurs résilients de Trading 212 et Bybit EU.

Le code exécuté dans le simulateur de vol est le même que celui qui volera en conditions réelles; seules les sorties d'ordres vers les brokers sont redirigées vers des comptes de démonstration (Demo/Paper) ou simulées localement.

---

## Le flux d'exécution bi-broker

Le système d'exécution gère deux environnements de trading de manière isolée et simultanée:

```
                          +-----------------------------------+
                          |  Live Market Data Feed (Bybit/T212)|
                          +-----------------------------------+
                                            |
                                            v
                          +-----------------------------------+
                          |      run_ingestor.py (Web/Worker) |
                          +-----------------------------------+
                                     |             |
                         (Push)      v             v   (Upsert)
                        +-----------------+   +---------------------+
                        | Redis Cache     |   | PostgreSQL DB       |
                        | (Upstash Cloud) |   | (live_prices/       |
                        |                 |   |  live_candles_1m)   |
                        +-----------------+   +---------------------+
                                 |                       |
                       (Read)    +-----------+-----------+
                                             |
                                             v
                          +-----------------------------------+
                          |    run_paper_trader.py (Engine)   |
                          |  - Polling cycle 60 secondes      |
                          |  - Update NAV & Prices            |
                          |  - Run vectorbt strategy logic    |
                          |  - Evaluate exit rules            |
                          +-----------------------------------+
                                             |
                                             v
                          +-----------------------------------+
                          |     paper_portfolio_balance       |
                          |     paper_positions               |
                          |     paper_transactions            |
                          +-----------------------------------+
```

### 1. Ingestion des données de marché (`run_ingestor.py`)
Ce processus indépendant est chargé de collecter la donnée brute. Il tourne en tâche de fond et met à jour en continu:
- La table `live_prices` et le cache Redis pour les derniers prix observés (Ticks).
- La table `live_candles_1m` qui stocke les bougies historiques consolidées de 1 minute.

### 2. Évaluation et décision (`run_paper_trader.py`)
Le moteur principal (`PaperTradingEngine`) exécute un cycle périodique (boucle synchrone toutes les 60 secondes):
- **Calcul du NAV**: Il calcule la valeur liquidative totale du portefeuille en sommant le solde disponible (cash) et la valorisation des positions ouvertes (basée sur les prix du cache Redis, avec repli sur Postgres).
- **Consolidation temporelle**: Il extrait les 10 000 dernières bougies 1m de la base de données PostgreSQL, les rééchantillonne à la granularité cible de la stratégie (ex: 15m, 30m, 45m) et exécute la logique de détection de signaux.
- **Vérification des sorties**: En parallèle des signaux bruts générés par les indicateurs, le moteur instancie à chaque cycle un simulateur de courtier (`BrokerSimulator`) pour évaluer les règles de sortie avancées (Stop Loss, Take Profit, Trailing Stops, Safety Stops).

---

## Le pipeline de prix résilient

Pour éviter d'interrompre l'exécution à cause d'un incident réseau ou d'une API indisponible, le moteur de Paper Trading implémente une stratégie de repli à trois niveaux (fallbacks) lors de l'évaluation du prix d'un actif:

```
+-------------------------------------------------------------+
| Taper dans le Cache Redis (Upstash)                         |
| (Latence minimale, frais d'infrastructure réduits)         |
+-------------------------------------------------------------+
                               |
                        [Échec ou vide]
                               v
+-------------------------------------------------------------+
| Consulter la table PostgreSQL `live_prices`                |
| (Vérification de la fraîcheur; alerte si âge > 3 minutes)   |
+-------------------------------------------------------------+
                               |
                        [Échec ou vide]
                               v
+-------------------------------------------------------------+
| Utiliser le dernier prix connu enregistré dans la position |
| (paper_positions.current_price)                             |
+-------------------------------------------------------------+
```

---

## Idées reçues vs Réalité technique

### Le Testnet Bybit n'est pas le Paper Trading
Un grand nombre de développeurs quantitatifs tentent de connecter leur bot au domaine `testnet.bybit.com` et se heurtent à des erreurs de connexion ou d'authentification:

| Environnement | Testnet Bybit (Global) | Demo Trading (Bybit EU / Mainnet) |
|---|---|---|
| **Routage API** | `api-testnet.bybit.com` | `api-demo.bybit.com` |
| **Zone Géographique** | Géo-bloqué en France (Restricted IP) | Autorisé en Europe (Conformité MiCA) |
| **Liquidité** | Artificielle; carnets d'ordres vides | Haute fidélité; basée sur les carnets réels |
| **Création Clé API** | Compte Testnet isolé requis | Intégrée au compte de production unifié |

### REST API Polling vs WebSocket Streaming
Interroger périodiquement un endpoint HTTP pour obtenir les prix en continu est inefficace:

| Approche | REST API Polling | WebSocket Streaming |
|---|---|---|
| **Consommation de requêtes** | Élevée; risque d'erreurs 429 (Rate Limit) | Minimale; tunnel persistant asynchrone |
| **Fréquence** | Limitée par des intervalles (ex: 5s ou 60s) | Instantanée à chaque mise à jour du carnet |
| **Cas d'usage optimal** | Passage d'ordres; réconciliation comptable | Ingestion des flux de prix à haute fréquence |

---

## La configuration des exécutions

Voici comment structurer l'instanciation de l'authentification et des environnements pour éviter les erreurs d'incompatibilité de clé (Shard Mismatch):

### ❌ Mauvaise configuration: Mélanger les clés de production et de démo
```python
# Utilisation d'enpoints de démonstration avec une clé API Mainnet (Production)
session = HTTP(
    testnet=True, # Mauvais: Testnet est géo-bloqué et isolé
    api_key="MAINNET_API_KEY", # Provoquera une erreur 401 (API Key Invalid)
    api_secret="MAINNET_API_SECRET"
)
```

### ✅ Bonne configuration: Initialisation robuste bi-broker
```python
# Initialisation de Bybit pour le Paper Trading européen
session = HTTP(
    testnet=False, # Désactive le réseau de test géo-bloqué
    demo=True,     # Force le routage vers l'API de démonstration
    api_key=os.getenv("BYBIT_API_KEY"),
    api_secret=os.getenv("BYBIT_API_SECRET"),
    recv_window=10000 # Tolérance de latence augmentée pour Render
)
```

---

## Architecture Logicielle et Optimisations

### 1. Séparation Infrastructure vs Logique Métier (Single Responsibility)
Pour garantir la robustesse et la testabilité du moteur, la logique d'exécution a été scindée en deux modules distincts :
*   **Orchestration de boucle (`engine.py`)** : Il gère les aspects d'infrastructure comme la planification du cycle de 60 secondes, les configurations de connexion à Redis et PostgreSQL, et le démarrage des clients brokers.
*   **Exécuteur Métier (`signal_executor.py`)** : Il contient la logique pure de trading. Il effectue l'évaluation des signaux, le calcul du NAV, la mise à jour des positions en mémoire, et l'orchestration des fermetures de positions. Cette séparation permet de tester la logique de trading de manière isolée avec des objets simulés (mocks).

### 2. Gestion Concurrente et Pool Asynchrone (Performance DB)
La base de données PostgreSQL subit des accès concurrents importants de la part des API FastAPI et des workers synchrones :
*   **Accès API Asynchrone** : Les points d'accès FastAPI dans [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py) exploitent un pool de connexions asynchrones via `asyncpg`. Le client récupère les connexions via `get_async_pool()` dans [connection.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/connection.py), évitant tout blocage I/O.
*   **Workers Synchrones** : Les tâches de fond (backtest, ingestion) conservent le pilote `psycopg2` via `get_sync_connection()`.
*   **Résolution du pattern N+1** : La fonction de mise à jour du NAV (`_update_portfolio_nav`) a été optimisée; elle n'interroge plus la base de données pour chaque position individuellement. Elle effectue désormais une requête SQL groupée (`SELECT ... WHERE ticker IN (...)`) puis met à jour les lignes par lot, réduisant le temps d'exécution par un facteur de 5.

### 3. Sécurisation Critique de l'Interface
L'API exposée est renforcée contre les menaces d'intrusion web :
*   **Protection CSRF (Double Submit Cookie)** : Un middleware intercepte toutes les requêtes d'écriture (`POST`, `PUT`, `DELETE`). Il génère un cookie sécurisé et valide la correspondance avec le header personnalisé `X-CSRFToken` envoyé par le frontend.
*   **Headers CORS et CSP Stricts** : Le middleware CORS restreint explicitement les requêtes aux domaines autorisés (pas d'utilisation du joker `*`). Les en-têtes de sécurité bloquent le détournement d'iframe (`X-Frame-Options: DENY`), le reniflage de type MIME (`X-Content-Type-Options: nosniff`) et forcent l'utilisation de canaux chiffrés (HSTS).
*   **Signature de Token HMAC** : Les clés de signature des jetons de session ne reposent plus sur le mot de passe utilisateur. Au démarrage du serveur, un secret HMAC robuste et éphémère de 32 octets est généré via `secrets.token_hex(32)`.
*   **Validation Pydantic** : Les paramètres des stratégies reçus par l'API (`indicator_params`) sont validés à l'entrée par un modèle Pydantic strict (`IndicatorParamsModel`), bloquant les injections de clés ou les types invalides.

### 4. Robustesse et Traçabilité des Erreurs
Le traitement des exceptions est conçu pour simplifier le diagnostic tout en protégeant les informations sensibles :
*   **Exceptions Métier Spécifiques** : Les exceptions génériques `except Exception` ont été remplacées par des filtres précis (`ConnectionError`, `asyncpg.PostgresError`, `ValueError`).
*   **Masquage des Erreurs en Production** : Lorsqu'une défaillance serveur survient, l'utilisateur reçoit une réponse sécurisée : `"An internal error occurred. Reference: {uuid}"`.
*   **UUID de Corrélation** : L'erreur complète est enregistrée dans les logs système accompagnée de cet UUID unique, permettant au développeur de retrouver instantanément la trace d'exécution sans divulguer le schéma de base de données ou les variables d'environnement sur le réseau.
*   **Timeouts Réseau Explicites** : Tous les appels HTTP vers des APIs tierces intègrent un timeout explicite (10 secondes par défaut) pour éviter le blocage indéfini des threads d'exécution.

---

## The Golden Rule

> **Règle d'or**: Ne laissez jamais un système de trading décider d'une taille de transaction sans une validation active de ses contraintes de liquidité; la gestion du risque doit valider chaque quantité calculée avant la transmission de l'ordre.
