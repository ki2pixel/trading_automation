# Standards de Code et Règles de Développement (Trading Automation)

## 1. Philosophie Générale
- **Lisibilité avant tout**: Le code est lu plus souvent qu'il n'est écrit. Privilégiez un code clair et explicite.
- **Fiabilité absolue**: Il s'agit d'une application financière. Les erreurs peuvent coûter de l'argent. La robustesse et la gestion rigoureuse des erreurs sont primordiales.
- **Testabilité**: Tout nouveau code doit être conçu pour être facilement testable (tests unitaires, tests d'intégration).

## 2. Standards Python (Backtest Engine & Scripts)
- **Typage Statique**: Utilisez systématiquement les annotations de type Python (`typing`). Chaque fonction, méthode et variable complexe doit être typée pour faciliter l'analyse statique (ex: `mypy`).
- **Précision Financière (CRITIQUE)**: L'utilisation de `float` natifs pour représenter des montants, des prix ou des tailles de lots est **strictement interdite** en raison des approximations d'arrondis. Utilisez exclusivement `decimal.Decimal` pour toute la logique financière et les calculs de PnL.
- **Style et Formatage (PEP 8)**: Respectez les conventions de style Python.
- **Docstrings**: Documentez toutes les classes, méthodes publiques et modules complexes. Chaque docstring doit expliquer l'objectif de la fonction, les arguments attendus et ce qu'elle retourne.
- **Gestion des Exceptions**: Ne capturez jamais les exceptions de manière générique et silencieuse (`except Exception: pass`). Soyez spécifique dans les types d'exceptions capturées et loggez toujours les erreurs avec le contexte approprié.
- **Logging Transactionnel et Audit**: Pour la logique de routage et d'exécution d'ordres, le logging ne sert pas qu'au debug, il garantit la traçabilité légale. Les exécutions d'ordres doivent générer des logs structurés (format JSON) incluant a minima : `timestamp_utc`, `order_id`, `symbole`, `quantité`, `prix` et `statut`. Différenciez correctement les niveaux de log classiques (`DEBUG`, `INFO`, etc.).
- **Gestion des Secrets**: L'écriture en dur ou la journalisation de clés privées et secrets API est strictement interdite. Utilisez exclusivement le masquage et les variables d'environnement.

## 3. Concurrence et Thread-Safety
- **États Partagés**: L'accès concurrent aux structures critiques (carnets d'ordres, portefeuilles, allocations) crée des risques de fuite financière. Utilisez des verrous explicites (`Lock`, `asyncio.Lock`) lors des mutations d'états partagés.
- **Prévention des Deadlocks**: En environnement multi-threadé/asynchrone, imposez un ordre d'acquisition strict si plusieurs verrous sont nécessaires simultanément, et définissez toujours des timeouts d'acquisition (`timeout` ou `wait_for`).
- **Réconciliation d'État**: N'assumez jamais que l'état local du moteur est parfaitement synchronisé avec le broker de manière asynchrone. Implémentez des réconciliations périodiques avec la source de vérité externe.
- **Asynchronisme**: Utilisez `asyncio` pour la gestion des I/O réseau; les appels bloquants sont interdits dans la boucle d'exécution principale.

## 4. Traitement Vectorisé et Optimisation (Pandas/NumPy)
L'optimisation bayésienne manipule des volumes massifs de données historiques. Une mauvaise gestion entraîne rapidement des pics de RAM (OOM).
- **Vectorisation**: L'itération native (`iterrows`, boucles `for`) est interdite sur les DataFrames de backtest. Privilégiez les opérations vectorisées.
- **Gestion Mémoire**: Libérez explicitement les gros objets en mémoire entre les passes d'optimisation. Surveillez l'empreinte RAM.
- **Robustesse des Données**: Traitez de manière proactive les `NaN` et valeurs infinies (`inf`). Corrigez systématiquement les `SettingWithCopyWarning` en utilisant `.copy()` ou `.loc`.

## 5. Architecture et Structure
- **Séparation des Préoccupations (SoC)**: Maintenez une séparation claire entre la logique de trading/calcul (stratégies, indicateurs), la plomberie (connexions API, BDD) et l'I/O.
- **Configuration**: Ne codez jamais les paramètres en dur. Utilisez les fichiers de configuration dédiés (dossier `configs/`) ou les variables d'environnement.
- **Dépendances**: Limitez strictement l'introduction de nouvelles dépendances externes. Toute nouvelle librairie doit être justifiée et enregistrée dans `requirements-backtest-engine.txt`.

## 6. Résilience Réseau et API (Live Execution)
Les connexions aux exchanges sont instables par nature.
- **Timeouts**: Fixez des délais d'attente stricts pour chaque requête afin de prévenir le blocage silencieux des processus.
- **Rate Limiting**: Implémentez un mécanisme de backoff exponentiel pour anticiper et gérer les limitations de débit des courtiers.
- **Reconnexion WebSockets**: Tout client WebSocket doit intégrer nativement un mécanisme de Heartbeat (ping/pong) et une logique de reconnexion automatique/silencieuse avec ré-abonnement aux flux de marché en cas de coupure.
- **Ordres "Fantômes" (Idempotence)**: En cas de timeout réseau lors de l'envoi d'un ordre, le statut réel de l'ordre est inconnu. Le système doit automatiquement interroger l'API avec un `client_order_id` unique pour vérifier son exécution avant toute nouvelle tentative.

## 7. Tests, Validation et Mocking
- **Tests (pytest)**: Écrivez systématiquement des tests pour les nouvelles fonctionnalités (dossier `tests/`).
- **Mocking Obligatoire**: L'exécution de requêtes réseau réelles vers des brokers pendant la CI/CD ou les tests locaux est formellement interdite. Utilisez des mocks (`pytest-mock`) ou des cassettes (`VCR.py`).
- **Non-Régression Financière**: Toute modification du moteur de backtest ou des stratégies doit être validée par une exécution de test pour s'assurer qu'il n'y a pas de régression non intentionnelle sur les métriques (ex: `aggregated_metrics.json`).

## 8. Stockage Local (Parquet) et I/O de Données Historiques
- **Format et Compression**: Utilisez exclusivement le format `.parquet` avec compression `snappy` (pour la vitesse) ou `zstd` (pour le stockage froid) pour historiser les données de marché tick-level ou minute.
- **Partitionnement Stratégique**: Partitionnez les gros volumes de données par `symbole` puis par `année/mois` (ex: `symbol=AAPL/year=2023/month=10/`). Cela permet aux requêtes Pandas/Polars de ne charger que le sous-ensemble strict en mémoire.
- **Versionnage des Schémas**: Les types de données (`dtypes`) Parquet doivent être stricts. Toute modification d'indicateurs ou de format de colonnes doit s'accompagner d'un versionnage explicite du schéma (ex: `v2_features`) pour prévenir la corruption du backtest.
- **Efficacité**: Optimisez les lectures/écritures. Préférez les traitements vectorisés aux boucles natives.

## 9. Bonnes Pratiques Git
- **Commits Atomiques**: Rédigez des petits commits clairs et indépendants.
- **Messages Conventionnels**: Suivez la nomenclature standard (ex: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`) pour faciliter la lecture de l'historique.

## 10. Risk & Money Management (Garde-fous)
- **Pre-Trade Checks**: Aucun ordre de marché ne doit être envoyé au courtier sans avoir franchi une barrière de validation synchrone (Vérification de la marge disponible, de l'exposition maximale autorisée sur l'actif, et de l'absence d'ordres en conflit).
- **Circuit Breakers (Kill-switches)**: Implémentez des limites dures au niveau global de l'application (ex: Max Drawdown journalier atteint, pic anormal de requêtes d'ordres par seconde). En cas de franchissement, le système doit rejeter toute nouvelle demande et se placer en mode "Close-Only" (fermeture de positions uniquement).