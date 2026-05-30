# Résoudre les bugs du collecteur

**TL;DR** : Un problème avec ton tableur ? Voici comment débloquer les erreurs régionales, gérer les timeouts d'Apps Script ou comprendre pourquoi nous ajustons les splits d'actions côté Python plutôt que dans Sheets.

La collecte cloud via Google Apps Script et des APIs externes est une mécanique puissante, mais elle est soumise aux caprices du réseau et aux règles strictes de sécurité de Google. 

Un jour ou l'autre, tu vas rencontrer un bug : un tableur qui affiche une erreur bizarre, un fichier Drive qui ne se crée pas ou un téléchargement qui semble figé.

Voici un guide direct pour diagnostiquer et résoudre ces incidents en un clin d'œil.

---

## 1. Les erreurs d'affichage dans ton tableur Sheets

### L'erreur `#REF!` dans la feuille STAGING
Cette erreur se produit généralement lorsqu'une donnée résiduelle bloque le déploiement automatique d'une formule (le "spill"). 
- **La solution** : Ouvre la feuille `STAGING`, sélectionne toutes les cellules et efface tout. La feuille doit être totalement vide pour permettre au collecteur d'y injecter ses données temporaires.

### L'erreur `#ERROR!` ou formules bloquées
Si SheetsFinance affiche des erreurs sur tes formules, vérifie le paramètre `FORMULA_ARG_SEPARATOR` dans ta feuille `CONFIG`. 
- Si ton compte Google utilise des paramètres régionaux français, le séparateur de formule doit être un point-virgule (`;`).
- Si ton compte est en anglais, c'est une virgule (`,`).
- Tu peux régler ce paramètre sur `AUTO` pour laisser le script deviner le bon délimiteur.

---

## 2. Le script s'arrête ou semble figé (Timeouts Google)

Google limite strictement le temps d'exécution en continu d'un script Apps Script à 6 minutes. 

Si tu lances la collecte sur une trop longue période historique, le script va s'interrompre. C'est un comportement normal prévu par notre superviseur automatique.

### Comment optimiser les performances ?
- **Laisse le superviseur travailler** : Il a enregistré sa progression dans la feuille `CHECKPOINTS`. Il relancera automatiquement un nouveau cycle 30 secondes plus tard pour poursuivre le téléchargement là où il s'est arrêté.
- **Réduis la taille des vagues** : Si les coupures surviennent trop souvent, ouvre ta feuille `CONFIG` et diminue la valeur de `MAX_BARS_WINDOWS_PER_RUN` (par exemple, passe de `12` à `8`). Le script traitera moins de fenêtres à chaque cycle, réduisant le risque de dépassement de quota.

---

## 3. Comprendre la gestion des Splits et de l'ajustement des cours

Une question revient souvent : *"Pourquoi mes fichiers CSV bruts téléchargés sur mon Google Drive ne sont-ils pas ajustés des splits d'actions historiques ?"*

### La limitation de SheetsFinance
En intraday (barres de 5 minutes), les cours fournis par SheetsFinance sont toujours des cours **bruts** (non ajustés). Utiliser ces prix directement fausserait tes backtests locaux en simulant des chutes de cours imaginaires lors de chaque division d'action.

### Notre choix d'architecture (Le pipeline local)
Plutôt que d'essayer de coder un algorithme d'ajustement lourd et complexe dans Google Sheets (ce qui ralentirait considérablement la collecte), nous avons choisi une séparation stricte des rôles :
1. **Le Collecteur cloud reste simple** : Il télécharge les cours 5 minutes bruts ET récupère séparément les événements de splits historiques (sauvegardés dans `splits/{symbol}_splits.csv`).
2. **Le nettoyage se fait en local** : C'est notre commande locale Python **`build-canonical`** qui prend le relais. Elle lit ton fichier brut et ton fichier de splits, applique rétroactivement les coefficients de division sur les prix et les volumes historiques, et génère un Parquet propre.

Cette approche garantit une collecte ultra-rapide dans le cloud et des simulations scientifiquement fiables sur ta machine.

---

## 4. Astuce technique : Paires de devises inverses (FX)

Pour réaliser tes conversions multi-devises, le collecteur cherche à télécharger les taux de change historiques. Il demande d'abord la paire directe (par exemple, `USDEUR` pour convertir tes actions américaines vers ton compte en Euros).

Si SheetsFinance ne propose pas cette paire directe dans sa base de données, notre collecteur ne plante pas. 

Il tente automatiquement de télécharger la paire inverse (par exemple, `EURUSD`). Une fois les données récupérées, il applique une formule d'inversion mathématique sur chaque bougie pour reconstruire proprement la série demandée :
- `open = 1 / open_inverse`
- `close = 1 / close_inverse`
- Les valeurs les plus hautes (`high`) et les plus basses (`low`) sont inversées et permutées pour conserver la cohérence physique de la bougie OHLC.
