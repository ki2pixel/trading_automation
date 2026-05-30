# Trading212 API Officielle — Documentation

> **Date:** 13 mai 2026
> **Contexte:** Exploration et validation de l'API officielle Trading212 (Beta) pour l'automatisation du trading.

---

## Vue d'ensemble

L'API officielle Trading212 est une API REST en **beta** réservée aux comptes **Invest** et **Stocks ISA**. Elle ne supporte **pas** les comptes CFD.

| Caractéristique | Valeur |
|----------------|--------|
| Protocole | REST / HTTPS |
| Version | v0 (beta) |
| Authentification | Basic HTTP (ID clé + Secret) |
| Environnements | `live.trading212.com` uniquement (demo nécessite switch UI) |
| Rate limit lecture | 1 req / 5s (account/summary) |
| Rate limit ordres | 1 req / 2s (limit/stop), 50 req/min (market) |

---

## Scripts de test

### `diagnose_api.sh`

Script de diagnostic rapide pour valider l'authentification et l'accessibilité des environnements.

**Usage:**
```bash
export T212_API_KEY_ID="ton_id"
export T212_API_SECRET="ta_secret"
./diagnose_api.sh
```

**Résultats attendus (demo OK):**
```
Test DEMO avec Basic Auth:    Status: 200
Test LIVE avec Basic Auth:    Status: 401  # clé liée au demo uniquement
```

**Résultats attendus (live OK):**
```
Test DEMO avec Basic Auth:    Status: 401  # clé liée au live uniquement
Test LIVE avec Basic Auth:    Status: 200
```

> **Important:** La clé API est liée à l'environnement actif au moment de sa génération. Pour tester en demo, switch le compte T212 vers "Entraînement" (Practice) **avant** de générer la clé.

---

### `test_official_api.py`

Script Python complet pour tester les endpoints principaux de l'API.

**Usage:**
```bash
export T212_API_KEY_ID="ton_id"
export T212_API_SECRET="ta_secret"
python test_official_api.py
```

**Avec ordre market (demo):**
```bash
python test_official_api.py --market-order
```

**Endpoints testés:**
- `GET /api/v0/equity/account/summary` — Résumé du compte
- `GET /api/v0/equity/account/cash` — Solde cash
- `GET /api/v0/equity/portfolio` — Positions ouvertes
- `GET /api/v0/equity/metadata/exchanges` — Bourses disponibles
- `GET /api/v0/equity/orders` — Ordres en attente
- `GET /api/v0/equity/metadata/instruments` — Liste des instruments (~15 000+)

**Caractéristiques:**
- Rate limiting automatique (2.5s entre requêtes)
- Gestion des erreurs HTTP
- Affichage formaté des réponses JSON

---

## Authentification

L'API utilise **Basic HTTP Authentication** (pas Bearer token).

| Paramètre | Source |
|-----------|--------|
| Username | "ID de la clé API" dans Settings → API (Beta) |
| Password | "Clé secrète" dans Settings → API (Beta) |

**Header généré:**
```
Authorization: Basic base64(api_key_id:api_secret)
```

**Exemple avec curl:**
```bash
curl -u "API_KEY_ID:API_SECRET" \
  https://demo.trading212.com/api/v0/equity/account/summary
```

---

## Découvertes clés

### 1. Pas d'environnement demo public

Contrairement à la documentation, `demo.trading212.com` n'accepte les requêtes que si la clé a été générée **après** avoir switché le compte en mode "Entraînement".

### 2. Clés liées à l'environnement

Une clé générée en mode "Réel" ne fonctionne pas sur le demo, et vice-versa.

### 3. Rate limits stricts

| Type | Limite |
|------|--------|
| Account summary | 1 req / 5s |
| Limit/Stop orders | 1 req / 2s |
| Market orders | 50 req / min |

### 4. 15 482 instruments

L'endpoint `/instruments` retourne **15 482 tickers** incluant actions, ETF, et autres instruments. Format du ticker: `TICKER_EXCHANGE_SUFFIX` (ex: `AAPL_US_EQ`).

---

## Limitations de l'API (beta)

- **Pas de streaming** : pas de WebSocket pour les prix temps réel
- **Non-idempotence** : renvoyer une requête d'ordre peut créer un doublon
- **Pas de compte CFD** : réservé aux comptes Invest/ISA
- **Pas d'historique de prix** : pas d'endpoint pour récupérer les chandeliers (OHLC)
- **Monodevise** : les ordres sont exécutés dans la devise principale du compte uniquement

---

## Architecture recommandée

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  Backtest Engine │────→│  Trading212Client   │────→│  T212 API (REST)│
│  (Python)        │     │  (Basic Auth)       │     │  demo/live      │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
        │
        ↓
┌─────────────────┐
│  Data Provider  │  ← Kaggle, Yahoo Finance, etc. (prix historiques)
│  (OHLC 5m/1d)   │
└─────────────────┘
```

**Flux:**
1. Le backtest engine génère les signaux (HMA crossover)
2. `Trading212Client` place les ordres via l'API REST
3. Les prix historiques proviennent d'une source externe (pas de l'API T212)

---

## Fichiers de référence

- `api.json` — Spécification OpenAPI complète (schemas, endpoints, rate limits)
- `test_official_api.py` — Script de test fonctionnel
- `diagnose_api.sh` — Script de diagnostic rapide

---

## Prochaines étapes

- [ ] Tester le placement d'un ordre market en demo
- [ ] Identifier les tickers européens pertinents pour la stratégie HMA
- [ ] Intégrer `Trading212Client` dans le backtest engine
- [ ] Implémenter la gestion des erreurs et le retry avec backoff
- [ ] Documenter le mapping des tickers T212 vers les données externes
