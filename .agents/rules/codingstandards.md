# Standards de Code et Règles de Développement (Trading Automation)

## 1. Philosophie Générale
- **Lisibilité avant tout**: Le code est lu plus souvent qu'il n'est écrit. Privilégiez un code clair et explicite.
- **Fiabilité absolue**: Il s'agit d'une application financière. Les erreurs peuvent coûter de l'argent. La robustesse et la gestion rigoureuse des erreurs sont primordiales.
- **Testabilité**: Tout nouveau code doit être conçu pour être facilement testable (tests unitaires, tests d'intégration).

## 2. Standards Python (Backtest Engine & Scripts)
- **Typage Statique**: Utilisez systématiquement les annotations de type Python (`typing`). Chaque fonction, méthode et variable complexe doit être typée pour faciliter l'analyse statique (ex: `mypy`).
- **Style et Formatage (PEP 8)**: Respectez les conventions de style Python.
- **Docstrings**: Documentez toutes les classes, méthodes publiques et modules complexes. Chaque docstring doit expliquer l'objectif de la fonction, les arguments attendus et ce qu'elle retourne.
- **Gestion des Exceptions**: Ne capturez jamais les exceptions de manière générique et silencieuse (`except Exception: pass`). Soyez spécifique dans les types d'exceptions capturées et loggez toujours les erreurs avec le contexte approprié.
- **Logging**: Utilisez le module de logging au lieu de `print()`. Différenciez correctement les niveaux de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- **Gestion des Secrets**: L'écriture en dur ou la journalisation de clés privées et secrets API est strictement interdite. Utilisez exclusivement le masquage et les variables d'environnement.

## 3. Concurrence et Thread-Safety
- **États Partagés**: L'accès concurrent aux structures critiques (carnets d'ordres, allocations) crée des risques financiers. Utilisez des verrous explicites (`Lock`, `RLock`) lors des mutations d'états partagés.
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

## 6. Résilience Réseau et API
Les connexions aux exchanges sont instables par nature.
- **Timeouts**: Fixez des délais d'attente stricts pour chaque requête afin de prévenir le blocage silencieux des processus.
- **Rate Limiting**: Implémentez un mécanisme de backoff exponentiel pour anticiper et gérer les limitations de débit des courtiers.

## 7. Tests, Validation et Mocking
- **Tests (pytest)**: Écrivez systématiquement des tests pour les nouvelles fonctionnalités (dossier `tests/`).
- **Mocking Obligatoire**: L'exécution de requêtes réseau réelles vers des brokers pendant la CI/CD ou les tests locaux est formellement interdite. Utilisez des mocks (`pytest-mock`) ou des cassettes (`VCR.py`).
- **Non-Régression Financière**: Toute modification du moteur de backtest ou des stratégies doit être validée par une exécution de test pour s'assurer qu'il n'y a pas de régression non intentionnelle sur les métriques (ex: `aggregated_metrics.json`).

## 8. Base de Données et I/O
- **Efficacité**: Optimisez les lectures/écritures, en particulier lors du chargement des données financières (`financial_datasets/`). Préférez les traitements vectorisés (Pandas/NumPy) au bouclage natif lorsque cela est pertinent.
- **Intégrité des Données**: Assurez-vous que les données historiques manipulées par le moteur ne sont jamais altérées involontairement.

## 9. Bonnes Pratiques Git
- **Commits Atomiques**: Rédigez des petits commits clairs et indépendants.
- **Messages Conventionnels**: Suivez la nomenclature standard (ex: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`) pour faciliter la lecture de l'historique.