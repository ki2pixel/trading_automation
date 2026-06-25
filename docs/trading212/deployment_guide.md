# Guide de Déploiement du Trading 212 Price Ingestor sur Render

Ce guide décrit les étapes nécessaires pour configurer et déployer le service `Trading212PriceIngestor` sur la plateforme Render de manière continue (CI/CD) via GitHub Actions.

---

## Étape 1 : Rendre le package GHCR public (ou configurer les accès Render)

Par défaut, les images publiées sur GitHub Container Registry (GHCR) sont privées. Pour que Render puisse tirer l'image sans identifiants supplémentaires, vous devez rendre le package public :

1. Allez sur votre profil GitHub, puis dans l'onglet **Packages**.
2. Sélectionnez le package `trading212-price-ingestor`.
3. Allez dans **Package settings** (Paramètres du package).
4. Faites défiler jusqu'à la section **Danger Zone** et cliquez sur **Change visibility** (Modifier la visibilité).
5. Choisissez **Public** et confirmez en saisissant le nom du package.

---

## Étape 2 : Créer le Service sur Render

1. Connectez-vous sur [dashboard.render.com](https://dashboard.render.com).
2. Cliquez sur **New +** en haut à droite.
3. Choisissez le type de service approprié selon votre choix d'architecture :
   - **Web Service** : Si vous souhaitez exposer l'endpoint HTTP `/prices` pour que d'autres services externes interrogent les prix (`T212_INGESTOR_MODE=web`).
   - **Background Worker** : Si vous souhaitez faire tourner l'ingesteur uniquement en tâche de fond sans exposition de port (`T212_INGESTOR_MODE=worker`).
4. Sélectionnez **Deploy from an existing image** (Déployer depuis une image existante).
5. Saisissez l'URI de l'image de votre conteneur GHCR :
   ```
   ghcr.io/<votre-nom-utilisateur-github>/trading212-price-ingestor:latest
   ```
   *(Remplacez `<votre-nom-utilisateur-github>` par votre identifiant GitHub réel en minuscules).*

---

## Étape 3 : Configurer les Variables d'Environnement sur Render

Dans l'onglet **Environment** de votre service Render, ajoutez les variables suivantes :

| Variable | Valeur Recommandée | Description |
| :--- | :--- | :--- |
| `T212_API_KEY_ID` | `[Votre Clé]` | **Secret** - Identifiant de clé API Trading 212. |
| `T212_API_SECRET` | `[Votre Secret]` | **Secret** - Secret de clé API Trading 212. |
| `T212_ENV` | `demo` ou `live` | Environnement Trading 212 (`demo` par défaut). |
| `T212_INGESTOR_MODE` | `web` ou `worker` | Mode de service (`worker` par défaut). Utilisez `web` pour exposer l'API FastAPI. |
| `T212_BOOTSTRAP` | `true` ou `false` | Activer le bootstrap automatique des micro-positions au lancement (`false` par défaut). |
| `T212_BOOTSTRAP_QTY` | `0.0001` (à ajuster) | Taille par défaut d'une micro-position de bootstrap. Augmentez à `0.01` ou `0.1` si les ordres sont rejetés avec un code d'erreur 400. |
| `T212_MICRO_POSITION_THRESHOLD` | (Optionnel) | Seuil de filtrage du tracker pour masquer les positions de bootstrap (s'aligne automatiquement sur `T212_BOOTSTRAP_QTY` si non défini). |
| `T212_POLLING_INTERVAL` | `60` | Intervalle en secondes entre chaque récupération de prix. |
| `T212_PRICE_CACHE_PATH` | `/app/cache/t212_prices.json` | Chemin interne du cache (laissé par défaut dans Docker). |

### Si vous utilisez le mode `Web Service` :
- Render détectera automatiquement le port `8080` exposé par le Dockerfile.
- Configurez le **Health Check Path** (chemin de vérification de santé) sur : `/health`.

---

## Diagnostic & Résolution d'Erreurs Communes (Erreur 400 sur orders/market)

Si vous activez `T212_BOOTSTRAP=true` et observez des erreurs du type :
`[Trading212Client] Request failed after 3 attempts: 400 Client Error: Bad Request`

Cela indique généralement que l'ordre de bootstrap a été rejeté par Trading 212 pour l'une des raisons suivantes :
1. **Valeur minimale d'ordre non atteinte** : Trading 212 impose souvent un montant d'ordre minimum de 1.00 unité de votre devise de compte (ex : €1.00 ou £1.00). Si la quantité de `0.0001` action d'un actif vaut moins de €1.00 (ex : 0.0001 * €25 = €0.0025), l'ordre est rejeté.
2. **Précision de quantité invalide** : Certains instruments n'autorisent pas 4 décimales de précision.

**Solution** :
Ajustez la variable `T212_BOOTSTRAP_QTY` dans l'onglet **Environment** de Render à une valeur supérieure (par exemple `0.01` ou `0.1` selon les prix de vos actifs cibles) de sorte que la valeur totale de l'ordre dépasse le minimum requis de 1.00.


---

## Étape 4 : Configurer le Déploiement Continu (CI/CD) sur GitHub

Une fois le service Render créé, vous devez configurer le webhook pour permettre à GitHub d'avertir Render de recharger l'image dès qu'une nouvelle version est compilée :

1. Sur le dashboard Render, allez dans les **Settings** (Paramètres) de votre service nouvellement créé.
2. Faites défiler jusqu'à la section **Deploy Hook** (Lien de déploiement).
3. Copiez l'URL fournie (format: `https://api.render.com/deploy/srv-...`).
4. Allez sur votre dépôt GitHub.
5. Allez dans **Settings** > **Secrets and variables** > **Actions**.
6. Cliquez sur **New repository secret** (Nouveau secret de dépôt).
7. Nommez le secret : `RENDER_DEPLOY_HOOK_URL`.
8. Collez l'URL de déploiement copiée de Render dans le champ valeur.
9. Enregistrez.

Désormais, à chaque push sur la branche principale (`main` ou `master`), GitHub Actions compilera l'image, la publiera sur GHCR, puis déclenchera automatiquement la mise à jour sur Render !
