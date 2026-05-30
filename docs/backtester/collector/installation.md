# Installer le collecteur SheetsFinance

**TL;DR** : Configure ton Google Sheet dédié en collant le script Apps Script fourni, puis clique sur "Setup collector workbook" dans le menu personnalisé pour créer tes dossiers de stockage Google Drive.

Tu veux démarrer ta collecte de données mais tu ne sais pas par où commencer ? Ne t'inquiète pas, l'installation est simple et ne nécessite aucune compétence en programmation. Tout se passe dans ton navigateur web en quelques minutes.

---

## Ce dont tu as besoin avant de commencer

- Un compte Google gratuit (avec accès à Sheets et Drive).
- L'extension **SheetsFinance** installée sur ton compte Google Sheets (tu peux la trouver dans le catalogue d'extensions Google Workspace).

---

## Les étapes pas-à-pas

### Étape 1 : Créer ton classeur de contrôle
Crée un tout nouveau fichier Google Sheets. Ce classeur servira uniquement à piloter ton collecteur ; évite d'y mélanger d'autres formules pour le garder léger.

### Étape 2 : Ouvrir l'éditeur de scripts Apps Script
Dans ton nouveau classeur Google Sheets, va dans le menu du haut et clique sur :
`Extensions -> Apps Script`

Une nouvelle page internet s'ouvre : c'est l'éditeur de code intégré de Google.

### Étape 3 : Coller le code du collecteur
1. Dans le projet Apps Script qui vient de s'ouvrir, tu devrais voir un fichier nommé `Code.gs`.
2. Efface tout le code vide présent par défaut.
3. Copie l'intégralité du code du collecteur situé dans notre fichier local : [SheetsFinance_Export.gs](file:///home/kidpixel/trading_automation_v2/Google_Apps_Script/SheetsFinance_Export.gs).
4. Colle-le dans l'éditeur en ligne de Google.
5. Clique sur la disquette en haut pour enregistrer ton projet.

### Étape 4 : Recharger ton Google Sheet
Ferme l'onglet Apps Script et recharge simplement la page de ton Google Sheets dans ton navigateur. Après quelques secondes, un tout nouveau menu personnalisé doit apparaître dans ta barre d'outils supérieure :
`SF Collector`

### Étape 5 : Initialiser l'arborescence
Dans le menu qui vient d'apparaître, clique sur :
`SF Collector -> 1. Setup collector workbook`

Google va te demander de valider des autorisations de sécurité (c'est normal, le script a besoin d'écrire des fichiers sur ton Google Drive à ta place). Valide-les. 

Une fois l'autorisation accordée, le script s'occupe de tout configurer à ta place :
- Il crée les feuilles de contrôle nécessaires dans ton tableur (`CONFIG`, `STAGING`, `CHECKPOINTS` et `LOGS`).
- Il crée automatiquement les dossiers de stockage correspondants sur ton Google Drive sous le dossier racine `SheetsFinance_Export/`.
