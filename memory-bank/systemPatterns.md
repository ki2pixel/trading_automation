# Modèles Système et Architecture

## Principes Généraux
- **Lisibilité et Fiabilité** : Priorité absolue, en accord avec les standards financiers du projet.
- **Séparation des Préoccupations (SoC)** : Isolation entre la logique de trading, la manipulation de données (I/O) et les connecteurs vers les brokers.
- **Typage Statique** : Utilisation rigoureuse des annotations de type Python (module `typing`) pour toutes les interfaces.

## Architecture Technique Réelle

### 1. Modèle de Traitement Mixte
L'architecture adopte une dualité de traitement fondamentalement séparée :
- **Approche Massivement Vectorisée** : Utilisée pour la génération d'indicateurs et le backtesting de masse, favorisant la vélocité via Pandas/Numpy.
- **Approche Orientée Événements (Event-Driven)** : Pilotée par le `simulation_kernel.py` et la boucle d'exécution du broker. Elle gère le routage d'ordres tick-par-tick ou bougie-par-bougie, isolant l'exécution live des traitements en batch.

### 2. Architecture de Concurrence & Performance
Pour répondre aux exigences de vitesse (notamment lors de l'optimisation bayésienne et WFA), le système s'appuie sur le multiprocessing natif.
Afin d'éviter les goulots d'étranglement dus au transfert de données entre processus (serialization pickle), l'architecture implémente un accès direct aux données via le module `shared_memory.py`. 
*Contrainte stricte : Les développements doivent garantir la thread-safety absolue lors de la création d'architectures concurrentes.*

### 3. Patterns de Données Canoniques
Les flux de données respectent un cycle de vie standardisé, défini dans `canonical.py` :
- Les données brutes issues de différentes sources (marché, broker) sont ingérées puis converties en structures normalisées canoniques.
- Le format d'écriture et de lecture finale s'appuie exclusivement sur des fichiers Parquet locaux. Cette architecture assure un chargement ultra-rapide en RAM (memory-mapped files) avec une consommation de stockage minimale.

### 4. Résilience API & Intégration Broker
Le module de routage (`broker.py`) intègre l'API Trading 212 avec un design pattern axé sur la tolérance aux pannes :
- **Logique de Retry** : Couverture des appels API instables par des systèmes de retry exponentiel.
- **Gestion des Exceptions Réseau** : Murs d'isolation contre les déconnexions intempestives, assurant que l'état local du portefeuille (exposition) reste cohérent même lors d'erreurs d'I/O de l'API REST.

## Patterns Technologiques Transversaux
- **Langage Principal** : Python.
- **Stockage de Données** : Fichiers Parquet locaux optimisés pour Pandas.
- **Tests** : Tests unitaires obligatoires (`pytest`) pour chaque composant et modèle comportemental (TDD/BDD). Respect strict des conventions de nommage `snake_case` et des docstrings.