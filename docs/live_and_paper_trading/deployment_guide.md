# Guide de Déploiement : Ingesteur de Prix & Moteur de Paper Trading

**TL;DR**: Ce guide fournit la procédure pas-à-pas pour configurer et déployer les modules temps réel (`run_ingestor.py` et `run_paper_trader.py`) sur Render; il explique également la gestion du double stockage Redis (Upstash) et PostgreSQL.

Vous avez validé vos stratégies quantitatives en local. Vos fichiers Parquet de données historiques sont à jour et vos indicateurs calculés sont prêts. Vous souhaitez maintenant faire tourner vos algorithmes en continu sur un serveur distant (Render); mais vous vous heurtez aux configurations complexes: blocages géographiques des serveurs Bybit (erreur 403), clés d'API déclarées invalides (erreur 401) ou quotas Redis Upstash épuisés au bout de quelques heures de fonctionnement.

Ce document décrit comment déployer l'infrastructure live de manière stable et résiliente en contournant ces obstacles techniques.

---

## 1. Topologie de Déploiement Render

Pour exploiter le système en production, vous devez déployer deux services distincts:

1. **Le Service Ingesteur** (`run_ingestor.py`):
   - **Type**: Web Service (si vous exposez l'API FastAPI des prix via `/prices`) ou Background Worker (si vous écrivez uniquement dans Redis/PostgreSQL sans port ouvert).
   - **Rôle**: Récupère les ticks de prix toutes les minutes auprès de Trading 212 et Bybit EU, consolidant les prix réels.
2. **Le Service Paper Trader** (`run_paper_trader.py`):
   - **Type**: Web Service.
   - **Rôle**: Maintient le tableau de bord HTML/JS interactif pour piloter les setups, exécute le cycle périodique d'évaluation des stratégies, et enregistre les ordres virtuels dans la base de données PostgreSQL.

---

## 2. Variables d'Environnement

Configurez les variables suivantes dans l'onglet **Environment** de vos services Render:

### Base de données et Cache
- `DATABASE_URL`: URL de connexion PostgreSQL (ex: Supabase); stocke les configurations de stratégies, le solde des portefeuilles, l'historique des transactions et les évaluations.
- `REDIS_URL`: URL du serveur Redis principal (ex: Upstash).
- `REDIS_URL_2` (Optionnel): URL du serveur Redis secondaire utilisé pour le basculement automatique (failover).
- `REDIS_API` / `REDIS_2_API` (Optionnel): Clés d'API développeur Upstash pour vérifier l'épuisement des quotas mensuels.
- `UPSTASH_EMAIL` / `UPSTASH_2_EMAIL` (Optionnel): Adresses email rattachées aux bases de données Upstash.

### Ingesteur de Prix (`run_ingestor.py`)
- `T212_INGESTOR_MODE`: `web` (pour exposer l'endpoint `/prices` sur FastAPI) ou `worker` (mode tâche de fond).
- `T212_POLLING_INTERVAL`: `60` (intervalle d'ingestion en secondes).
- `T212_BOOTSTRAP`: `true` ou `false` (activer le bootstrap des micro-positions sur Trading 212 au lancement).
- `T212_BOOTSTRAP_QTY`: `0.0001` (ajuster si des erreurs 400 surviennent à cause d'une valeur d'ordre inférieure à la devise minimale).
- `T212_INGESTOR_ENV`: `demo` ou `live` (permet de découpler l'ingesteur de prix; par exemple `demo` pour l'ingesteur et `live` pour le reste du moteur).

### Moteur de Paper Trading (`run_paper_trader.py`)
- `PAPER_TRADER_POLLING_INTERVAL`: `60` (fréquence de boucle du moteur en secondes).
- `PORT`: `8081` (port d'écoute par défaut).
- `PAPER_TRADER_PASSWORD`: Le mot de passe utilisateur requis pour se connecter à l'interface d'administration.
- `HMAC_SECRET`: Le secret de signature des jetons HMAC (déclarez une clé hexadécimale forte d'au moins 32 octets).
- `T212_PAPER_ROUTING_ENABLED`: `true` ou `false` (activer le routage réel des ordres sur le compte de démonstration Trading 212).

### Identifiants API Trading 212
- `T212_API_KEY_ID`: Votre identifiant de clé d'API Trading 212.
- `T212_API_SECRET`: Votre clé secrète Trading 212.
- `T212_ENV`: `demo` ou `live` (définit l'environnement global d'exécution du moteur).

### Identifiants API Bybit EU
- `BYBIT_API_KEY`: Votre clé d'API de démonstration Bybit.
- `BYBIT_API_SECRET`: Votre clé secrète Bybit de démonstration.

---

## 3. Contournement des Limitations Géographiques et WAF

Les serveurs cloud subissent des filtrages drastiques auprès des serveurs Bybit. Appliquez rigoureusement les deux règles architecturales suivantes pour éviter les blocages:

### Règle 1: Localisation géographique du serveur (Erreur 403)
Bybit bloque les requêtes provenant des instances cloud localisées aux États-Unis. Lors de la création de vos services sur Render, sélectionnez impérativement la région **Frankfurt (Germany)**. L'Allemagne est située dans la zone de licence autorisée de Bybit EU, ce qui évite le géo-blocage du CDN (Akamai/Cloudflare).

### Règle 2: Association à une application tierce (Erreur 401/403)
La réglementation européenne (MiCA) oblige Bybit EU à brider la création de clés d'API autonomes libres:
1. Lors de la création de vos clés sur le portail Bybit EU (en mode **Demo Trading**), sélectionnez l'option **Connect to Third-Party Applications**.
2. Dans la liste déroulante des applications autorisées, choisissez **Siebly SDK** (SDK open-source accrédité).
3. Définissez les droits d'accès sur **Read-Write** et activez les autorisations pour le module **Unified Trading** (Spot, USDT/USDC Derivatives).
4. Cette procédure force la validation de votre clé API en contournant l'obligation de lier votre compte à une plateforme d'automatisation payante.

---

## 4. Pipeline de Cache et Résilience Upstash

Le fichier [connection.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/connection.py) intègre un client personnalisé `FailoverRedisClient` pour contourner la limitation des plans Upstash gratuits (10 000 requêtes journalières):

```
+------------------------------------------+
| Requête de lecture/écriture de prix      |
+------------------------------------------+
                     |
                     v
+------------------------------------------+
| Le client vérifie le quota restant       |
| via l'API développeur Upstash            |
+------------------------------------------+
        |                          |
   [Quota épuisé]            [Quota saphir OK]
        |                          |
        v                          v
+------------------+       +------------------+
| Basculement sur  |       | Exécution sur    |
| `REDIS_URL_2`    |       | `REDIS_URL`      |
+------------------+       +------------------+
```

Ce basculement transparent évite l'interruption de la boucle de Paper Trading et prévient le crash des exécutions lors des pics de volatilité.

---

## 5. Gestion des Dépendances et Images Docker

Pour optimiser les ressources lors du déploiement en production et réduire la taille de l'image Docker finale, le fichier global unique des dépendances a été partitionné en trois profils distincts :
*   **[requirements-base.txt](file:///home/kidpixel/trading_automation_v2/requirements-base.txt)** : Contient les paquets d'infrastructure et d'accès aux données partagés (Pandas, Numpy, Ruff, Pydantic v2).
*   **[requirements-backtest.txt](file:///home/kidpixel/trading_automation_v2/requirements-backtest.txt)** : Regroupe les bibliothèques lourdes requises pour la simulation locale et l'optimisation (Optuna, Scikit-learn, Scipy, Matplotlib, VectorBT).
*   **[requirements-live.txt](file:///home/kidpixel/trading_automation_v2/requirements-live.txt)** : Cible exclusivement l'exécution en temps réel (FastAPI, Uvicorn, asyncpg, Redis).

### Choix de déploiement Render
Lors du déploiement sur Render, configurez le script d'installation (`Build Command`) pour installer uniquement les dépendances nécessaires au moteur d'exécution en direct, ce qui réduit de plus de 60% la taille de l'environnement virtuel installé :
```bash
pip install -r requirements-base.txt -r requirements-live.txt
```
Cette isolation évite de charger les paquets de calcul scientifique (VectorBT, Optuna) inutilisés en production, accélérant le temps de démarrage et de déploiement de l'instance.
