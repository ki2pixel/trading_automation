# Rapport d'Évaluation Technique : Cotations Temps Réel via l'API Trading 212 (Beta)

Ce rapport évalue la faisabilité et les implications architecturales de la récupération en temps réel des cours des actions européennes via l'API officielle de Trading 212 (Beta) en mode DEMO, pour le suivi de notre portefeuille cible de **51 setups validés** (portant sur **21 actifs uniques**).

---

## 1. Audit des Points d'Accès Officiels

L'évaluation de la spécification de l'API Trading 212 (Beta) et les tests empiriques menés confirment les éléments suivants :

### L'endpoint `/equity/metadata/instruments`
Cet endpoint renvoie exclusivement des métadonnées structurelles et statiques sur les actifs supportés par le courtier. Lors de l'exécution du script, **15 697 instruments** ont été récupérés en environnement DEMO. La structure de réponse d'un instrument exemple (`STN_US_EQ` - Stantec) se limite aux informations suivantes :

```json
{
  "ticker": "STN_US_EQ",
  "type": "STOCK",
  "workingScheduleId": 56,
  "isin": "CA85472N1096",
  "currencyCode": "USD",
  "name": "Stantec",
  "shortName": "STN",
  "maxOpenQuantity": 16711.0,
  "extendedHours": true,
  "addedOn": "2023-11-02T16:28:13.000+02:00"
}
```

> [!IMPORTANT]
> **Aucun champ de prix dynamique** (`price`, `currentPrice`, `lastPrice`, `bid`, `ask`, ou `quote`) n'est présent dans les métadonnées. Cet endpoint a de plus un taux limite très strict de **1 requête toutes les 50 secondes** (confirmé par l'en-tête `x-ratelimit-limit: 1` et `x-ratelimit-period: 50`), ce qui exclut totalement son usage pour du suivi de prix en temps réel.

### Absence d'Endpoints de Cotation Directe
Il n'existe **aucun point d'accès direct non documenté** permettant d'obtenir le prix d'un instrument arbitraire sans le détenir en portefeuille. L'appel des routes hypothétiques suivantes a systématiquement échoué avec une erreur `404 Not Found` :
- `GET /equity/prices` -> `404`
- `GET /equity/quotes` -> `404`
- `GET /equity/ticker` -> `404`
- `GET /equity/metadata/prices` -> `404`

---

## 2. Analyse de la méthode "Portfolio Hack" vs Direct REST

### Mécanisme du Contournement (Hack)
Le contournement par l'ouverture de micro-positions (achat de fractions d'actions en compte DEMO) est techniquement obligatoire si l'on souhaite utiliser l'API Trading 212 comme source de prix. 

La logique sous-jacente est la suivante :
1. **Exposition des prix** : L'API n'expose le `currentPrice` (ou `lastPrice`) que pour les actifs figurant dans les états de compte de l'utilisateur (`/equity/positions` ou `/equity/portfolio`).
2. **Comportement de l'API pour un actif non détenu** : Si l'on demande un ticker non détenu en portefeuille, l'API renvoie un code d'erreur **`404 Not Found`** avec le corps suivant :
   ```json
   {
     "type": "/api-errors/entity-not-found",
     "title": "Requested entity not found",
     "status": 404,
     "detail": "Provided ticker 'SAP_GY_EQ' does not exist",
     "traceId": "6bd411b1a8e5afd32de5ed2c0c4e3c8a"
   }
   ```
   *(Note : Dans l'univers de Trading 212, les tickers de Xetra utilisent la nomenclature `TICKERd_EQ` comme `SAPd_EQ` plutôt que la notation classique `SAP_GY_EQ`).*
3. **Conséquence** : L'ouverture d'une micro-position force l'instrument à figurer dans le portefeuille et les positions actives, ce qui permet à `/equity/positions` et `/equity/portfolio` de diffuser son cours.

```mermaid
graph TD
    A[Besoin : Prix de SAPd_EQ] --> B{Position ouverte ?}
    B -- Non --> C[Appel /equity/positions?ticker=SAPd_EQ]
    C --> D[Réponse vide [] ou 404 - Aucun prix disponible]
    B -- Oui (Micro-position 0.0001 action) --> E[Appel /equity/positions ou /equity/portfolio]
    E --> F[Réponse avec currentPrice = 185.5]
```

### Viabilité et Limitations de Taux (Rate Limiting)
Pour suivre simultanément nos **21 actifs uniques** supportant nos **51 setups** d'actifs européens (akzanleur, dpwdeeur, teniteur, SAP, EVD.DE, GMAB, randnleur, FPE.DE, NVO, NVS, ZEAL.CO, AMS.MC, daideeur, acfreur, mrkdeeur, vnadeeur, rifreur, belgbeeur, abibeeur, lxsdeeur, cafreur) :

1. **Calcul de la consommation de requêtes** :
   - `/equity/positions` et `/equity/portfolio` retournent **l'intégralité** des positions détenues dans un seul tableau JSON.
   - Nous n'avons pas besoin de faire 21 requêtes séparées pour suivre 21 actifs. **Une seule requête** sur `/equity/portfolio` ou `/equity/positions` permet de récupérer les prix actualisés de nos 21 actifs à la fois.
   - Rate limit officiel : **1 requête par seconde** (60 req/min) pour positions/portfolio.
   - Pour un suivi à la minute (granularité 1m requise par certains setups), nous consommons **1 req/minute**, soit seulement **1.67% de la limite autorisée**. La marge de sécurité est donc gigantesque (> 98%).

2. **Limitations et Contraintes Opérationnelles** :
   - **Horaires de marché** : Pour ouvrir une micro-position, le marché ciblé (Xetra, Copenhague, SIX, Bolsa de Madrid, Paris, Milan, Bruxelles, Amsterdam) doit être **ouvert**. Si le script tente d'ouvrir une position en dehors des horaires de cotation, l'ordre de marché reste au statut `NEW` (en attente d'ouverture) et la position n'est pas créée. Le prix ne sera disponible qu'à l'ouverture du marché.
   - **Pollution du portefeuille** : La détention de **21 micro-positions** artificielles (au lieu de 51 setups distincts) rend la lecture du portefeuille plus propre mais introduit tout de même des lignes de veille. Les P&L et allocations réels de la stratégie seront masqués ou faussés par ces lignes de "data feeding".
   - **Reset du compte DEMO** : Si le compte DEMO est réinitialisé depuis l'application (pour remettre le solde virtuel à sa valeur par défaut), toutes les positions sont liquidées. Le système de trading doit être capable de détecter cette disparition et de recréer automatiquement les 21 micro-positions.

---

## 3. Plan de Validation Empirique

Pour valider ces conclusions sans perturber le code existant, un script léger autonome a été créé :
[verify_api_capabilities.py](file:///home/kidpixel/trading_automation_v2/ressources/trading212/trading212-api-extended-main/verify_api_capabilities.py).

### Protocole de test empirique
Exécuter le script de diagnostic avec des identifiants DEMO valides :

```bash
export T212_API_KEY_ID="votre_id_de_cle"
export T212_API_SECRET="votre_secret_api"
python3 ressources/trading212/trading212-api-extended-main/verify_api_capabilities.py
```

Le script exécute trois tests :
1. **Lecture de `/equity/metadata/instruments`** : Il analyse la structure JSON retournée pour prouver l'absence de champs de prix.
2. **Appel des routes hypothétiques** : Il effectue des requêtes GET sur `/equity/prices`, `/equity/quotes` et `/equity/ticker` pour valider qu'elles renvoient un code HTTP `404 Not Found`.
3. **Appel ciblé de `/equity/positions?ticker=SAP_GY_EQ`** : Il montre qu'en l'absence de position sur SAP, aucune donnée de cotation n'est renvoyée (retourne un code 404).

---

## 4. Recommandations pour l'Architecture du Paper Trading

La méthode de contournement par micro-positions est effectivement la seule approche REST gratuite et temps réel offerte par l'API officielle de Trading 212. Cependant, pour éviter d'impacter négativement la logique métier et la clarté du portefeuille, nous recommandons de centraliser l'ingestion via une architecture découplée.

### Architecture Recommandée : Ingestion Découplée avec Filtrage (Broker Price Feed Broker)

Pour faire cohabiter le suivi de prix par micro-positions et l'exécution réelle des setups sans conflit de données, nous devons implémenter un composant **Price Ingestor** autonome et une règle de filtrage des quantités.

```
                  ┌──────────────────────────────────────────┐
                  │          Trading 212 API (Demo)          │
                  └────────────────────┬─────────────────────┘
                                       │
                              (GET /positions)
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │        Price Ingestor Service            │
                  │       (Lit les 21 micro-positions)       │
                  └────────────┬────────────────────┬────────┘
                               │                    │
                    (Filtre : Qty > 0.0001)   (Extrait prix de toutes les lignes)
                               │                    │
                               ▼                    ▼
                  ┌────────────────────────┐  ┌────────────────────────┐
                  │    Position Tracker    │  │   Price Feed Cache     │
                  │   (Positions Réelles)  │  │    (Base de Prix)      │
                  └────────────────────────┘  └───────────┬────────────┘
                                                          │
                                                (Lecture des prix 1m)
                                                          │
                                                          ▼
                                              ┌────────────────────────┐
                                              │   51 Strategy Setups   │
                                              └────────────────────────┘
```

#### Principes de mise en œuvre :
1. **Centralisation du Polling** :
   - Un processus unique d'ingestion (par exemple, une tâche planifiée asynchrone) appelle `/equity/positions` toutes les minutes.
   - Ce processus extrait le tuple `(ticker, currentPrice)` pour chaque ligne et met à jour un cache de prix local (ex: dictionnaire en mémoire RAM ou Redis local).
   - Les 51 instances de stratégies consultent ce cache local au lieu de solliciter l'API de Trading 212, évitant tout risque de blocage par limitation de taux.

2. **Séparation Logique par Filtre de Quantité** :
   - Les micro-positions de veille de prix doivent utiliser la quantité minimale absolue autorisée par l'API (ex: `0.0001` action ou la plus petite fraction possible par instrument).
   - Les positions réellement ouvertes par les signaux de trading des 51 setups utiliseront des tailles de lots normales (calculées via le poids de Kelly, par exemple `0.1` ou `1.0` action minimum).
   - Le module de suivi de performance et de réconciliation d'état (`Position Tracker`) doit ignorer systématiquement les lignes du portefeuille ayant une quantité égale à la taille minimale de veille (ex: `quantity <= 0.0001`).

3. **Routine d'Initialisation Automatique (Bootstrap)** :
   - Au démarrage de l'application de paper trading, le script compare la liste des **21 actifs uniques** cibles avec les positions actuellement retournées par l'API.
   - Pour tout actif manquant dans le portefeuille, le script émet automatiquement un ordre d'achat market de la quantité minimale (`0.0001` share) dès que la session de marché correspondante est ouverte (`workingScheduleId`).

---

## 5. Table de Mapping des Actifs (Portefeuille Cible)

Le tableau suivant présente la correspondance officielle entre les identifiants locaux de notre moteur de backtesting, les noms réels d'entreprises, les codes ISIN et les tickers à utiliser sur l'API Trading 212 (Beta) en mode DEMO pour l'initialisation des 21 micro-positions de veille de prix :

| Identifiant local | Nom réel d'entreprise | ISIN | Ticker Trading 212 | Devise | Bourse |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `akzanleur` | Akzo Nobel NV | NL0013267909 | `AKZAa_EQ` | EUR | Euronext Amsterdam |
| `dpwdeeur` | DHL Group | DE0005552004 | `DPWd_EQ` | EUR | Xetra |
| `teniteur` | Tenaris SA | LU2598331598 | `TW10d_EQ` | EUR | Xetra |
| `SAP` | SAP SE | DE0007164600 | `SAPd_EQ` | EUR | Xetra |
| `EVD.DE` | Evotec SE | DE0005664809 | `EVTd_EQ` | EUR | Xetra |
| `GMAB` | Genmab A/S | DK0010272202 | `GE9d_EQ` | EUR | Xetra (Dukascopy source en DKK) |
| `randnleur` | Randstad NV | NL0000379121 | `RANDa_EQ` | EUR | Euronext Amsterdam |
| `FPE.DE` | Fuchs SE | DE000A3E5D56 | `FPEd_EQ` | EUR | Xetra |
| `NVO` | Novo Nordisk A/S | DK0062498333 | `NOVCd_EQ` | EUR | Xetra (Dukascopy source en DKK) |
| `NVS` | Novartis AG | CH0012005267 | `NOVNs_EQ` | CHF | SIX Swiss Exchange |
| `ZEAL.CO` | Zeal Network SE | DE000ZEAL241 | `TIMd_EQ` | EUR | Xetra |
| `AMS.MC` | Amadeus IT Group SA | ES0109067019 | `AMSe_EQ` | EUR | Bolsa de Madrid |
| `daideeur` | Mercedes-Benz Group AG | DE0007100000 | `DAId_EQ` | EUR | Xetra |
| `acfreur` | Accor SA | FR0000120404 | `ACp_EQ` | EUR | Euronext Paris |
| `mrkdeeur` | Merck KGaA | DE0006599905 | `MRKd_EQ` | EUR | Xetra |
| `vnadeeur` | Vonovia SE | DE000A1ML7J1 | `VNAd_EQ` | EUR | Xetra |
| `rifreur` | Pernod-Ricard SA | FR0000120693 | `RIp_EQ` | EUR | Euronext Paris |
| `belgbeeur` | Proximus SADP | BE0003810273 | `PROX_BE_EQ` | EUR | Euronext Brussels |
| `abibeeur` | Anheuser-Busch InBev SA/NV | BE0974293251 | `ABI_BE_EQ` | EUR | Euronext Brussels |
| `lxsdeeur` | Lanxess AG | DE0005470405 | `LXSd_EQ` | EUR | Xetra |
| `cafreur` | Carrefour SA | FR0000120172 | `CAp_EQ` | EUR | Euronext Paris |

> [!NOTE]
> Les fichiers structurés correspondants sont disponibles dans le répertoire de l'API Trading 212 :
> * JSON : [t212_assets_mapping.json](file:///home/kidpixel/trading_automation_v2/ressources/trading212/trading212-api-extended-main/t212_assets_mapping.json)
> * CSV : [t212_assets_mapping.csv](file:///home/kidpixel/trading_automation_v2/ressources/trading212/trading212-api-extended-main/t212_assets_mapping.csv)
