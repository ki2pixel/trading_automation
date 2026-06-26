# Audit Technique : Performance, Fiabilité et Sécurité des Logiques de Trading Backend

**TL;DR** : L'intégration d'un pool de connexions partagées et de Redis Upstash élimine les goulots d'étranglement réseau et les écritures bloquantes. **Cependant, la dépendance à un dictionnaire de tickers statique et l'absence de disjoncteur sur prix périmés menacent la stabilité opérationnelle.**

---

## Le Goulot d'Étranglement Réseau : Quand l'Event Loop S'effondre

Imaginez la situation : votre stratégie de trading tourne à haute fréquence. Le marché bouge rapidement. Soudain, l'ingesteur de prix doit insérer 20 nouvelles cotations dans la base de données. Sans pool de connexions, l'application initie une poignée de main TCP et une négociation SSL pour chaque ligne. L'Event Loop de FastAPI est bloqué ; les prix s'accumulent ; les requêtes HTTP expirent.

C'est le problème classique de la latence de connexion accumulée. Pour le résoudre, nous devons séparer l'accès rapide et éphémère du stockage lourd et permanent.

### L'Analogie du Facteur et des Boîtes aux Lettres

Pour comprendre cette architecture, utilisons l'analogie d'un système de distribution de courrier :
*   **Les Boîtes aux Lettres Express (Upstash Redis)** : Situées au coin de la rue. L'accès y est instantané et sans attente pour y déposer ou y lire un message rapide.
*   **Le Registre Central (Supabase PostgreSQL)** : Le bureau de poste principal. C'est là que l'on archive officiellement le courrier de façon permanente. S'y rendre nécessite de faire la queue et de remplir des formulaires.
*   **Le Facteur (L'Ingestor)** : Récupère les données fraîches chez le courtier (Trading 212) et les dépose instantanément dans la Boîte aux Lettres Express, tout en envoyant une copie au Registre Central pour archivage.
*   **Le Destinataire (Le Paper Trader)** : Lit les prix en priorité dans la Boîte aux Lettres Express. Il ne fait le déplacement au Registre Central qu'en cas de boîte vide.

---

## 1. Performance : Le Goulot Étrangleur de Connexion

L'initialisation répétée de connexions directes vers Supabase PostgreSQL génère une surcharge réseau colossale à chaque cycle de polling.

### ❌ Connexion Directe et Bloquante

Chaque appel réseau recrée une session, figeant le thread principal :

```python
# ❌ Mauvaise pratique : connexion unitaire et synchrone sans pool
def write_price(ticker, price):
    db_url = os.getenv("DATABASE_URL")
    # Négociation SSL/TCP à chaque appel
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("INSERT INTO prices ...")
    conn.commit()
    conn.close()
```

### ✅ Connexion Poolée et Cache Redis Asynchrone

Le client réutilise les connexions du pool et délègue l'I/O bloquant à un thread séparé :

```python
# ✅ Bonne pratique : utilisation du ThreadedConnectionPool et exécution asynchrone
import asyncio
from backtest_engine.live.connection import get_db_connection

async def update_prices_async(prices):
    # Délégation de l'opération bloquante SQL à un thread dédié
    await asyncio.to_thread(self._write_db_sync, prices)

def _write_db_sync(self, prices):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for ticker, price in prices.items():
                cur.execute("INSERT INTO trading212_prices ...")
            conn.commit()
```

---

## 2. Fiabilité : La Duplication Statique des Mappages

Le module d'ingestion contient un dictionnaire en dur pour la traduction des tickers (`TICKER_TRANSLATION`). Si un nouveau ticker est ajouté à la stratégie, le système l'ignorera ou échouera à le traduire, tandis que le résolveur dynamique possède déjà la logique appropriée.

### ❌ Dictionnaire Statique Redondant

Une double maintenance manuelle sujette aux erreurs :

```python
# ❌ Mauvaise pratique : duplication statique dans ingestor.py
TICKER_TRANSLATION = {
    'TIMd_EQ': 'ZEAL.CO',
    'NOVCd_EQ': 'NVO',
    # Si cette table diverge de resolver.py, les transactions échoueront
}
```

### ✅ Inversion Dynamique du Résolveur

Générer dynamiquement le mappage inverse à partir de la source unique du résolveur :

```python
# ✅ Bonne pratique : inversion dynamique à partir de la classe unique de vérité
from backtest_engine.live.trading212.resolver import Trading212TickerResolver

class Trading212PriceIngestor:
    def __init__(self, client, resolver: Trading212TickerResolver):
        self.client = client
        # Inversion automatique du dictionnaire statique du résolveur
        self.inverse_mapping = {v: k for k, v in resolver.STATIC_MAPPING.items()}
```

---

## 3. Fiabilité : Le Piège du Prix Périmé

Le moteur de Paper Trading peut lire des cotations expirées si l'ingesteur tombe en panne. Le Paper Trading continue d'évaluer le portefeuille avec des données obsolètes, faussant la performance simulée.

### ❌ Tolérance Aveugle à l'Obsolescence

Le système émet un avertissement simple mais utilise quand même le prix obsolète :

```python
# ❌ Mauvaise pratique : utilisation passive d'une donnée périmée
age = datetime.now(timezone.utc) - updated_at
if age > timedelta(minutes=3):
    print("WARNING: price is stale. Using it anyway.")
# Exécute la transaction sur un prix vieux de plusieurs heures
total_nav += (stale_price * qty)
```

### ✅ Disjoncteur sur Données Périmées

Le système doit rejeter l'évaluation ou suspendre le trading si le seuil de fraîcheur est dépassé :

```python
# ✅ Bonne pratique : levée d'exception ou suspension de la transaction
MAX_PRICE_AGE_SECONDS = 180

age_seconds = (datetime.now(timezone.utc) - updated_at).total_seconds()
if age_seconds > MAX_PRICE_AGE_SECONDS:
    raise ValueError(f"Circuit breaker active: price for {asset} is too stale ({age_seconds}s)")
```

---

## 4. Analyse Comparative des Choix d'Architecture

Le tableau ci-dessous synthétise les compromis appliqués à la gestion des données temps réel :

| Approche | Latence d'Accès | Persistance | Complexité Réseau | Risque Opérationnel |
| :--- | :--- | :--- | :--- | :--- |
| **Fichier JSON Local** | Ultra-faible (< 1ms) | Éphémère (Perdue au redémarrage Render) | Nulle (I/O local) | Concurrence d'accès en cas d'écritures simultanées |
| **Upstash Redis (Cache)** | Très faible (5-15ms) | Temporaire (TTL configurable) | Moyenne (Requêtes HTTPS/TLS) | Panne réseau tiers (limite de quota Upstash) |
| **Supabase PostgreSQL** | Élevée (50-120ms) | Durable (Transactions ACID) | Élevée (Gestion du pool requise) | Épuisement des connexions disponibles sur la DB |

---

## Idées Reçues : Le Cache Local n'est pas une Base de Données

Les développeurs considèrent souvent le cache local JSON comme un mécanisme de repli infaillible. C'est une erreur sur les environnements Cloud modernes comme Render. Les conteneurs Render possèdent un système de fichiers éphémère. À chaque déploiement ou redémarrage automatique, le fichier de cache JSON est détruit. Compter sur ce fichier pour maintenir un historique ou des états de prix constitue une faille critique. Seule la base de données SQL ou une instance Redis persistante externe garantit la survie des données.

---

## La Règle d'Or : Séparer l'Ingestion de l'Exécution

> **Règle d'Or** : L'écriture de données temps réel doit être asynchrone et découplée ; aucun ralentissement de l'API de commande ne doit impacter la lecture ou l'évaluation du portefeuille.
