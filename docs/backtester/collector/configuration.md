# Configurer tes listes de collecte (Watchlist)

**TL;DR** : La feuille `CONFIG` de ton classeur pilote tout ton collecteur. Définis tes actions cibles (`WATCHLIST`), tes devises et tes fenêtres historiques tout en ajustant la vitesse pour ne pas bloquer tes quotas d'API chez Google.

Tu as initialisé ton classeur de collecte. C'est parfait. Mais maintenant, tu es face à la feuille `CONFIG` et tu te demandes comment la paramétrer au mieux sans provoquer des plantages d'API ou saturer la mémoire de ton tableur Google.

Le collecteur est conçu pour être très respectueux des limites imposées par SheetsFinance et par l'environnement cloud de Google. 

Voici comment configurer tes paramètres clés pour garantir une collecte fluide et sans interruption.

---

## Les paramètres essentiels à adapter

### 1. La cible de collecte
- **`WATCHLIST`** : La liste des actions ou paires que tu veux récupérer, séparées par des virgules (ex: `AAPL,MSFT,GMAB`).
- **`START_DATE`** / **`END_DATE`** : Ta fenêtre historique d'évaluation. Utilise le format strict `YYYY-MM-DD`.

### 2. Le rythme de collecte (Pour éviter les timeouts Google)
Google limite l'exécution d'un script Apps Script à 6 minutes consécutives. Si tu tentes de télécharger 5 ans de données intraday en une seule fois, le script s'arrêtera au milieu à cause d'un timeout de sécurité. 

Pour contourner cela, le collecteur découpe l'historique en petites fenêtres temporelles (batches) et utilise des checkpoints pour enregistrer son avancement :
- **`BARS_WINDOW_DAYS`** : Fixé à `7`. SheetsFinance limite le téléchargement des barres de 5 minutes à des fenêtres de 7 jours maximum par requête. Laisse cette valeur par défaut.
- **`MAX_BARS_WINDOWS_PER_RUN`** : Le nombre de fenêtres de 7 jours traitées à chaque cycle d'exécution (généralement entre `8` et `12`). Si ton script s'arrête souvent par timeout, diminue cette valeur.
- **`RESPECTFUL_PAUSE_MS`** : Pause obligatoire en millisecondes entre deux requêtes (généralement `2000` à `5000` ms) pour ne pas te faire bannir temporairement par les serveurs de SheetsFinance pour excès d'appels.

### 3. La gestion des devises
- **`TARGET_CURRENCIES`** : Les devises dans lesquelles tu veux pouvoir convertir tes prix (ex : `EUR,USD`). Le collecteur téléchargera automatiquement les taux de change historiques correspondants (ex : la paire `USDEUR`) pour permettre à ton moteur local de réaliser des backtests multi-devises réalistes.

---

## Exemple de configuration idéale (Production testée)

Voici une configuration type qui offre un excellent compromis entre vitesse de téléchargement et stabilité de connexion face aux quotas de Google :

```text
WATCHLIST = AAPL,GMAB,LOGI
START_DATE = 2024-01-01
END_DATE = 2025-01-01
BARS_PERIOD = 5min
BARS_WINDOW_DAYS = 7
SPLITS_WINDOW_DAYS = 90
FX_WINDOW_DAYS = 7
BARS_METRICS = date&open&high&low&close&volume
SPLITS_METRICS = date&symbol&numerator&denominator&ratio
FX_METRICS = date&open&high&low&close
TIME_SERIES_OPTIONS = NH
SPLITS_OPTIONS = NH
FX_OPTIONS = NH
TARGET_CURRENCIES = EUR,USD
FORMULA_ARG_SEPARATOR = ;
MAX_BARS_WINDOWS_PER_RUN = 10
MAX_SPLITS_WINDOWS_PER_RUN = 4
MAX_FX_WINDOWS_PER_RUN = 8
MAX_RETRIES_PER_BATCH = 3
RETRY_BACKOFF_MS = 5000
AUTO_NEXT_CYCLE_DELAY_SECONDS = 30
```

> [!IMPORTANT]
> Ne modifie pas la valeur de `BARS_PERIOD` (qui doit impérativement rester sur `5min`) et conserve `FX_WINDOW_DAYS = 7`. Ce sont des contraintes strictes imposées par l'API SheetsFinance pour pouvoir accéder aux données de cours intraday historiques.
