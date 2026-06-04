# Fast Filesystem Operations

> **Expertise** : Édition chirurgicale de fichiers, optimisation token, recherche efficace, manipulation précise de codebase.

## Quick Start

### Mental Model

Fast Filesystem Ops optimise chaque opération fichier pour minimiser l'usage de tokens :
- Édition ciblée avec `edit_file` (via le serveur `filesystem-agent`)
- Recherche intelligente avec `fast_search_files`
- Lecture multiple avec `fast_read_multiple_files`
- Évitement des chargements inutiles

### Workflow obligatoire

1. **Localisation** : `fast_search_files` pour trouver les cibles
2. **Lecture minimale** : `fast_read_multiple_files` uniquement des sections nécessaires
3. **Édition chirurgicale** : `edit_file` pour modifications précises
4. **Validation** : Vérification minimale des changements

### Patterns d'utilisation

#### Pour modification de fonction spécifique

1. **Localiser la fonction** :
   - Si vous cherchez un fichier par son nom (substring match) : utiliser `fast_search_files(directory="/home/kidpixel/trading_automation_v2", pattern="calculations")`.
   - Si vous cherchez du contenu textuel (regex) : utiliser `grep_search(SearchPath="/home/kidpixel/trading_automation_v2", Query="def calculateTotal")`.

2. **Lire uniquement le fichier contenant la fonction** :
   `fast_read_multiple_files(paths=["/home/kidpixel/trading_automation_v2/src/calculations.py"])`

3. **Éditer chirurgicalement** (remplacer la séquence exacte de lignes) :
   `edit_file(path="/home/kidpixel/trading_automation_v2/src/calculations.py", edits=[{"oldText": "def calculateTotal():\n    return 0", "newText": "def calculateTotal():\n    return 100"}])`

#### Pour refactoring multi-fichiers

1. **Rechercher toutes les occurrences** (du contenu textuel) :
   `grep_search(SearchPath="/home/kidpixel/trading_automation_v2", Query="deprecated_function")`

2. **Lire les fichiers** :
   `fast_read_multiple_files(paths=["/home/kidpixel/trading_automation_v2/file1.js", "/home/kidpixel/trading_automation_v2/file2.js"])`

3. **Éditer chaque occurrence chirurgicalement** :
   `edit_file(path="/home/kidpixel/trading_automation_v2/file1.js", edits=[{"oldText": "deprecated_function()", "newText": "new_function_call()"}])`
   `edit_file(path="/home/kidpixel/trading_automation_v2/file2.js", edits=[{"oldText": "deprecated_function()", "newText": "new_function_call()"}])`

## Production-safe patterns

### Recherche de fichiers par nom (fast-filesystem)

Pour trouver l'emplacement de fichiers par leur nom :
```json
// Exemple d'appel fast_search_files (substring match sur le nom du fichier)
{
  "directory": "/home/kidpixel/trading_automation_v2",
  "pattern": "calculations"
}
```

### Recherche de contenu textuel (ripgrep-agent)

Pour rechercher des patterns à l'intérieur du code, utilisez toujours `grep_search` :
```json
// Exemple d'appel grep_search
{
  "SearchPath": "/home/kidpixel/trading_automation_v2",
  "Query": "class UserController",
  "CaseInsensitive": true
}
```

### Lecture chirurgicale (fast-filesystem)

```json
// Lecture de plusieurs fichiers en une fois
{
  "paths": [
    "/home/kidpixel/trading_automation_v2/backtest_engine/data.py",
    "/home/kidpixel/trading_automation_v2/backtest_engine/configuration.py"
  ]
}
```

### Édition précise (filesystem-agent)

```json
// Exemple d'édition chirurgicale par remplacement de bloc textuel exact
{
  "path": "/home/kidpixel/trading_automation_v2/src/app.js",
  "edits": [
    {
      "oldText": "const port = 3000;",
      "newText": "const port = 8080;"
    }
  ]
}
```

## Token optimization strategies

### Éviter les chargements massifs

❌ **Incorrect** : Charger l'intégralité d'un grand fichier de code (>1000 lignes) avec `read_file` ou `fast_read_file` lorsque seule une fonction est ciblée.

✅ **Correct** :
1. Localiser la ligne avec `grep_search`.
2. Lire uniquement une portion limitée avec `view_file` (arguments `StartLine` et `EndLine`).
3. Modifier chirurgicalement avec `edit_file` en ciblant le bloc exact.

### Recherche avant lecture

Toujours localiser le code précis avant de lire :
1. **Localiser** : `grep_search` avec la requête désirée.
2. **Lire** : `view_file` sur le fichier retourné pour le contexte immédiat (ex: 20-30 lignes).
3. **Modifier** : `edit_file` avec le texte exact à remplacer.

## Common gotchas

### Fichiers volumineux (>1000 lignes)

- **RÈGLE D'OR** : Ne jamais charger entièrement les fichiers volumineux.
- Pour les fichiers JSON massifs, utilisez les outils de `json-query` en passant la structure JSON sous `json_data`.
- Pour le code source volumineux, localisez d'abord avec `grep_search` et lisez des lignes ciblées via `view_file`.

### Éditions en cascade

Pour modifier plusieurs fichiers, procédez séquentiellement :
1. Obtenez la liste des fichiers via `grep_search`.
2. Lisez les zones ciblées.
3. Exécutez `edit_file` pour chaque fichier l'un après l'autre (les modifications doivent rester séquentielles).

## API Reference

### Outils principaux

- `fast_search_files(directory, pattern)` : Trouve les chemins de fichiers dont le nom contient `pattern` sous `directory`.
- `fast_read_multiple_files(paths)` : Lit le contenu textuel complet de la liste de fichiers fournie dans `paths`.
- `edit_file(path, edits, dryRun)` : Applique des modifications basées sur le remplacement de chaînes de caractères exactes (`oldText` -> `newText`).
- `grep_search(SearchPath, Query, IsRegex, MatchPerLine, CaseInsensitive, Includes)` : Utilise RipGrep pour rechercher du contenu textuel à l'intérieur des fichiers d'un dossier.

## Debugging checklist

- Confirmer que la recherche retourne les bons fichiers avant lecture
- Vérifier que le texte recherché avec `edit_file` correspond exactement (caractères et indentations)
- Tester les patterns de recherche sur de petits dossiers d'abord
- Valider que les éditions ne cassent pas la syntaxe du fichier
- Contrôler l'usage token après chaque opération

## When to use this skill

- **Fichiers volumineux** : Quand les fichiers dépassent 1000 lignes
- **Modifications ciblées** : Pour changer des fonctions spécifiques
- **Refactoring** : Quand plusieurs fichiers nécessitent des changements
- **Recherche globale** : Pour trouver des patterns dans tout le codebase
- **Optimisation token** : Quand l'usage de tokens est critique
- **Édition chirurgicale** : Pour modifications précises sans effets de bord

## Integration patterns

### Avec Memory Bank Protocol
- **Accès Strict** : Utilisez EXCLUSIVEMENT les outils `fast_read_file`, `edit_file`, `fast_write_file` avec des chemins absolus pour accéder aux fichiers de `memory-bank/`.
- **Interdiction Formelle** : NE JAMAIS lire l'intégralité du répertoire `memory-bank/` ni lire d'autres fichiers de mémoire si la tâche est triviale.

### Avec Sequential Thinking

Utilise `sequentialthinking_tools` pour valider la logique des modifications avant édition.

### Avec Shrimp Task Manager

Utilise pour implémenter les tâches générées par Shrimp Task Manager de manière optimisée.

### Avec JSON Query

Utilise `json_query_query_json` pour filtrer les données JSON avant traitement.