# JSON Query Expert

> **Expertise** : Manipulation chirurgicale de JSON massifs, extraction précise via JSONPath, optimisation token pour fichiers de configuration.

## Quick Start

### Mental Model

JSON Query Expert utilise le pattern "Sniper" pour les fichiers JSON :
- Jamais de chargement complet de fichiers > 1000 lignes
- Extraction ciblée avec `json_query_query_json`
- Localisation précise avant édition
- Modification chirurgicale avec `edit_file`

### Workflow obligatoire

1. **Inspection** : `json_query_query_json` pour localiser les données
2. **Localisation** : Trouver les lignes exactes dans le fichier
3. **Édition** : `edit_file` pour modification ciblée
4. **Validation** : Vérification minimale du résultat

### Patterns d'utilisation

#### Pour modification de configuration

1. **Lire le fichier de configuration** (par exemple `package.json`) :
   Utiliser `fast_read_file` (ou `read_text_file`).
2. **Interroger la configuration cible avec JSON Query** :
   Appeler `json_query_query_json(json_data=config_object, query="$.scripts.dev")`.
3. **Éditer chirurgicalement** :
   Appeler `edit_file(path="package.json", edits=[{"oldText": "\"dev\": \"old command\",", "newText": "\"dev\": \"vite --port 3000\","}])`.

## Production-safe patterns

### Pattern "Sniper" pour fichiers massifs

❌ **Incorrect** : Charger un énorme fichier JSON (>1000 lignes) dans le contexte système pour inspection manuelle ou via simple lecture.

✅ **Correct** (Pattern "Sniper") :
1. Charger le fichier JSON avec `fast_read_file` (ou lire des portions ciblées).
2. Extraire la branche nécessaire via `json_query_query_json(json_data=massive_json, query="$.components[0].props")`.
3. Localiser la chaîne exacte et appeler `edit_file` pour remplacer le bloc nécessaire.

### Recherche et validation avant modification

Pour les structures JSON complexes :
- Valider le chemin JSONPath désiré : `json_query_query_json(json_data=config_data, query="$.database.connections[0].host")`.
- Extraire toutes les clés pour cartographier le schéma : `json_query_search_keys(json_data=config_data)`.
- Trouver des valeurs spécifiques par leur clé : `json_query_search_values(json_data=config_data, key="port")`.

## Token optimization strategies

### Traitement des fichiers JSON volumineux (>1000 lignes)

- **RÈGLE D'OR** : Ne jamais charger entièrement les JSON massifs dans le prompt de discussion de l'assistant si possible.
- Pour les fichiers massifs comme `aggregated_metrics.json` ou les fichiers d'historique dans `financial_datasets/`, utilisez le parsing en streaming $O(1)$ RAM (comme `ijson` ou une lecture chunkée) au runtime Python. Le chargement complet via `json.load()` est strictement interdit sur les fichiers massifs de backtest pour éviter les pics de consommation RAM.

## Common gotchas

### Erreurs de syntaxe JSONPath

- Toujours utiliser le préfixe de racine `$` (ex : `$.root.array[0].property`).
- Les expressions de chemin relatives (ne commençant pas par `$`) ne sont pas valides pour `json_query_query_json`.

### Modifications invalidant le JSON

- Après toute modification via `edit_file` sur un fichier JSON, validez toujours que le JSON résultant reste syntaxiquement correct (en essayant de le parser ou en effectuant une requête JSONPath test dessus).

## API Reference

### Outils de Requêtage JSON

- `json_query_query_json(json_data, query)` : Exécute une requête JSONPath `query` sur l'objet ou tableau `json_data` et retourne les correspondances.
- `json_query_search_keys(json_data)` : Retourne la liste complète de toutes les clés de l'objet ou tableau `json_data` (aplatie).
- `json_query_search_values(json_data, key)` : Trouve et retourne toutes les valeurs associées à la clé `key` à n'importe quel niveau de profondeur dans `json_data`.

### Outil d'Édition Fichier

- `edit_file(path, edits, dryRun)` : Modifie le fichier à l'emplacement `path` en remplaçant exactement les chaînes définies dans le tableau `edits` (`oldText` -> `newText`).

## Debugging checklist

- Confirmer que le fichier JSON est valide avant requêtes
- Vérifier la syntaxe JSONPath (commence par $)
- Tester les requêtes sur petits échantillons d'abord
- Valider que les lignes localisées existent vraiment
- Contrôler la syntaxe JSON après modifications

## When to use this skill

- **Fichiers de configuration** : package.json, tsconfig.json, manifest.json
- **Traductions i18n** : Fichiers de traduction volumineux
- **Données structurées** : JSON > 1000 lignes
- **Configurations complexes** : webpack, babel, eslint configs
- **Métadonnées** : lock files, caches, états sérialisés
- **API responses** : Fichiers de mock ou fixtures

## Integration patterns

### Avec Fast Filesystem
Utilise `edit_file` pour appliquer les modifications après avoir déterminé la portion exacte de texte à modifier.

### Avec Sequential Thinking
Utilise `sequentialthinking_tools` pour valider la structure logique des données avant d'effectuer les modifications de schéma JSON.

### Avec Shrimp Task Manager
Utilise pour manipuler les fichiers JSON de backlog ou de configuration de tâches de manière ciblée.

## File type specific strategies

### package.json
```bash
json_query_query_json package.json "$.scripts"
json_query_search_keys package.json "dependencies"
```

### Fichiers de configuration de backtest
```bash
json_query_query_json backtest_config.json "$.strategies"
json_query_search_keys backtest_config.json "parameters"
```

### tsconfig.json
```bash
json_query_query_json tsconfig.json "$.compilerOptions"
json_query_search_keys tsconfig.json "include"
```

### i18n files
```bash
json_query_query_json locales.json "$.fr.pages[*].title"
json_query_search_keys locales.json "*.buttons.*"
```