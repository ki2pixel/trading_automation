---
name: sequentialthinking-logic
description: Expert en raisonnement décomposé. Force l'usage de sequentialthinking_tools pour valider la logique de backtest, le flux de signaux et la thread-safety des architectures de trading complexes.
---

# Sequential Thinking Logic

> **Expertise** : Raisonnement décomposé, validation logique, analyse étape par étape, pensée structurée pour architectures de trading complexes.

## Quick Start

### Mental Model

Sequential Thinking Logic décompose les problèmes complexes en séquences logiques validées :
- Analyse du flux de données (Indicateurs -> Signaux -> Ordres)
- Validation de la thread-safety (Lock, RLock) pour les états partagés (ex: carnet d'ordres)
- Identification des points de défaillance dans les exécutions asynchrones (asyncio)
- Construction de chaînes de raisonnement robustes pour l'optimisation bayésienne

### Workflow obligatoire

1. **Décomposition** : Identifier les composants logiques principaux (Pipeline de données, Moteur d'exécution, etc.)
2. **Validation** : Utiliser l'outil MCP `sequentialthinking_tools` pour chaque étape de la réflexion
3. **Chaînage** : Connecter les étapes en une séquence cohérente (ex: Génération de signal -> Validation risque -> Exécution)
4. **Test logique** : Valider les hypothèses (edge cases financiers, latence)

### Patterns d'utilisation

#### Pour l'architecture du Backtest Engine

```json
// Appel de l'outil séquentiel pour décomposer l'architecture
{
  "thought": "Décomposition de l'architecture du backtest : Flux de ticks -> Indicateurs -> Signaux -> Gestion des risques -> Exécution",
  "thoughtNumber": 1,
  "totalThoughts": 5,
  "nextThoughtNeeded": true
}
```

#### Pour validation de thread-safety

```json
// Validation de l'accès concurrent au carnet d'ordres
{
  "thought": "Analyse de la thread-safety : Le thread de websockets asynchrones met à jour le carnet pendant que le moteur de stratégie lit les prix. Un RLock est requis autour de l'objet OrderBook.",
  "thoughtNumber": 2,
  "totalThoughts": 5,
  "nextThoughtNeeded": true
}
```

## Production-safe patterns

### Validation systématique

Pour chaque composant logique (ex: un nouvel indicateur) :

1. Définir le problème mathématique et les contraintes de mémoire (ex: vectorisation requise).
2. Vérifier comment les données sont consommées sans créer de RAM spikes.
3. Valider la sortie de l'indicateur face aux NaNs et valeurs extrêmes.

### Pipeline de Trading

Pattern spécifique pour l'automatisation :

- **Data Ingestion** : Validation du parsing des ticks asynchrones.
- **Signal Generation** : Validation de la logique mathématique (sans boucles `iterrows`).
- **Order Execution** : Validation du cycle de vie de l'ordre (Pending, Filled, Cancelled) et gestion des rejets API.

### Gestion des erreurs logiques

- Identifier les points de défaillance (ex: coupure réseau pendant une transaction).
- Analyser les cas limites (ex: slippage extrême, gap d'ouverture).
- Valider la logique de reconnexion et de réconciliation de l'état du portfolio.

## Common gotchas

### Séquences incomplètes

- Toujours valider le début ET la fin de chaque séquence de trading (de la réception du tick au PnL mis à jour).
- Les points de décision (Risk Management) doivent couvrir tous les cas (fonds insuffisants, limite d'exposition).

### Problèmes d'asynchronisme

- Risque de race conditions si l'état (positions, balance) est muté sans lock.
- Toujours vérifier que les appels réseau (`asyncio`) ne bloquent pas l'event loop principal (le moteur de stratégie).

### Vectorisation vs Boucles

- Interdiction d'utiliser des itérations natives sur des séries temporelles longues.
- Penser systématiquement en opérations matricielles pour éviter les fuites de mémoire (RAM spikes).

## API Reference

### Commandes principales

L'outil principal est l'outil MCP `sequentialthinking_tools`.

Arguments clés de `sequentialthinking_tools` :
- `thought` : La réflexion détaillée ou l'étape logique actuelle.
- `thoughtNumber` : Le numéro de la réflexion courante.
- `totalThoughts` : Le nombre total estimé de réflexions.
- `nextThoughtNeeded` : Booléen indiquant si une réflexion supplémentaire est requise.

## Debugging checklist

- Confirmer que chaque étape logique du backtest a une entrée temporelle stricte (éviter le look-ahead bias).
- Vérifier que les points de décision de la stratégie sont déterministes.
- Tester mentalement les cas de forte volatilité ou de données manquantes.
- Valider la bonne gestion des verrous pour chaque ressource partagée.

## When to use this skill

- **Moteur de Backtest** : Conception du pipeline d'événements.
- **Logique de Stratégie** : Flux mathématiques et signaux de trading.
- **Exécution Asynchrone** : Gestion des websockets et des requêtes API REST concurrentes.
- **Optimisation Bayésienne** : Structuration de l'espace de recherche et gestion de la mémoire.
- **Debugging logique** : Analyse de raisonnement défaillant causant des pertes virtuelles ou des RAM spikes.

## Integration patterns

### Avec Shrimp Task Manager

Utilise après `analyze_task` pour valider la décomposition logique des algorithmes de trading.

### Avec Fast Filesystem

Utilise pour valider la logique avant les éditions chirurgicales avec `edit_file`.