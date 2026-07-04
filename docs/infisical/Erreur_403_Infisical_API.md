# Analyse et solutions pour l’erreur 403 lors de la récupération de secrets Infisical

Lorsqu’une **Machine Identity** Infisical (rôle *Viewer*) tente de récupérer les secrets via l’API, plusieurs points doivent être vérifiés : d’une part les **paramètres de requête** (en particulier l’identifiant ou slug du projet), et d’autre part les **permissions** accordées à l’identité sur l’environnement cible. Dans votre cas, vous obtenez systématiquement un **403 Forbidden** pour l’environnement `dev` malgré les droits de lecture (« Read Value ») du rôle Viewer.  

Les causes les plus probables sont les suivantes :

- **Paramètre *workspaceSlug* vs *workspaceId*** : Sur Infisical Cloud (SaaS), le endpoint `GET /api/v3/secrets/raw` attend généralement un **workspaceSlug** (le slug du projet) plutôt qu’un ID UUID. Dans la documentation Infisical et dans des exemples officiels, on utilise en effet l’URL de la forme `...?workspaceSlug=<votre-slug>&environment=<env>&secretPath=/`. Par exemple :  
  ```
  curl -H "Authorization: Bearer <token>" \
      "https://app.infisical.com/api/v3/secrets/raw?workspaceSlug=<project-slug>&environment=dev&secretPath=/"
  ```  
  Si on fournit *uniquement* `workspaceId=...` (UUID) au lieu de `workspaceSlug`, le serveur Infisical Cloud peut ne pas reconnaître correctement le projet. Cela conduit alors à un refus d’accès (403), car l’API considère que la requête n’est pas valide pour ce projet. En résumé, *assurez-vous d’utiliser le paramètre `workspaceSlug` (le slug du projet Infisical) dans la requête GET des secrets*.  

- **Correspondance du slug d’environnement** : Vérifiez que le paramètre `environment=dev` correspond exactement au *slug* de l’environnement « Development » configuré dans Infisical. Dans la capture de projet que vous avez fournie, l’environnement « Development » a bien pour slug `dev`, donc ce point est correct. Il n’y a pas de restriction générale qui bloquerait le rôle Viewer seulement sur certains environnements : le rôle *Viewer* s’applique **à tous les environnements** du projet par défaut. Ainsi, l’erreur 403 sur `dev` n’est pas due à un blocage implicite – plutôt à un problème de paramètres ou de permissions précises.  

En synthèse, la cause la plus probable est que l’API ne reçoit pas le bon identifiant de projet. Pour la formule Cloud, utilisez **workspaceSlug**. Vous pouvez tester ainsi :  
```bash
curl -H "Authorization: Bearer <token>" \
     "https://app.infisical.com/api/v3/secrets/raw?workspaceSlug=<votre-slug>&environment=dev&secretPath=/"
```  
Cela devrait renvoyer la liste des secrets (ou un objet JSON vide) au lieu du 403. Par comparaison, la documentation Infisical montre clairement l’usage de `workspaceSlug` dans une requête GET des secrets via API.

## Rôles et permissions Infisical (Viewer)

Infisical distingue *rôles organisationnels* et *rôles projet*. Votre Machine Identity a le rôle **Viewer** au niveau du projet. Selon la documentation officielle **RBAC**, ce rôle *« Viewer: Read-only access to all resources within the project. Viewers cannot create, edit, or delete any resources.»*. Autrement dit, un Viewer peut lire les secrets dans **tous les environnements** du projet. Il n’existe pas de blocage implicite sur l’environnement `dev` ; si le rôle est bien actif, il doit théoriquement fonctionner partout.

Toutefois, sur l’offre Cloud gratuite, on ne peut pas créer de rôles personnalisés. Pour pallier des permissions plus fines, Infisical propose les **Additional Privileges** (« Privileges additionnels ») qui s’ajoutent au rôle de base. Par exemple, on peut explicitement accorder la lecture des secrets dans un environnement donné, même si le rôle de base devrait déjà l’inclure. Voici comment cela peut aider :

- **Additional Privilege sur l’environnement `dev`** : Vous pouvez, via l’UI (ou l’API) ajouter une « permission additionnelle » ciblant l’environnement `dev`. Par exemple, un privilège JSON pourrait ressembler à ceci :  
  ```json
  {
    "identityId": "<id-de-votre-identity>",
    "projectId": "<id-de-votre-projet>",
    "slug": "read-secrets-dev",
    "permissions": [
      {
        "subject": "secrets",
        "action": ["read", "readValue"],
        "conditions": {
          "environment": { "$eq": "dev" }
        }
      }
    ]
  }
  ```  
  Ce privilège accorde explicitement à l’identité la permission **read** et **readValue** sur les secrets, mais uniquement lorsque `environment` est égal à `"dev"`. En pratique, on configure cela depuis la page *Access Controls* du projet, en cliquant sur *Add Additional Privileges* pour votre identity. Infisical souligne qu’on peut ainsi donner un accès fin (par chemin de secret, environnement, etc.) sans créer de nouveau rôle. Dans votre cas, ajouter un tel privilège pour `dev` garantirait que l’identité a bien les droits nécessaires même si, de base, le rôle Viewer devrait suffire.  

## Conclusion et recommandations

En résumé : **vérifiez d’abord les paramètres de la requête API**. Utilisez `workspaceSlug=<slug-du-projet>` (et non l’UUID) pour l’appel GET des secrets. Cela corrigera probablement le 403, car l’API retrouvera correctement le projet et ses environnements. Ensuite, confirmez que l’identité est bien ajoutée au projet avec le rôle *Viewer*. Si nécessaire, utilisez les *Additional Privileges* pour affiner l’accès sur l’environnement `dev`. 

Ainsi, sans créer de rôle personnalisé (impossible en formule gratuite), l’identité pourra lire les secrets en `dev`. Avec ces ajustements, la requête GET de secrets devrait fonctionner sans renvoyer 403.

**Sources :** Documentation Infisical (RBAC et exemples d’API), et guide Infisical sur les Additional Privileges. Ces ressources confirment que le rôle *Viewer* permet la lecture dans tous les environnements et que l’API attend un `workspaceSlug` dans les requêtes GET de secrets.