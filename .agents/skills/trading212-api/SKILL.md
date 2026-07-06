---
name: trading212-api
description: "Expert en intégration et routage d'ordres via l'API Trading 212 (v0) avec support multi-environnements et idempotence."
---

# Spécialisation: trading212-api

## 1. Rôle et Objectifs
L'agent possédant cette compétence gère les interactions de bas niveau avec l'API officielle de Trading 212 (Invest et Stocks ISA). Il assure la connexion, la gestion des environnements (Demo et Live), le rate-limiting client, l'idempotence des ordres et le mapping des tickers pour respecter les contraintes de devise unique du compte.

## 2. Principes Fondamentaux & Contraintes

- **Environnements & URLs**:
  - Demo : `https://demo.trading212.com/api/v0` (Paper Trading, tests)
  - Live : `https://live.trading212.com/api/v0` (Trading réel)
  - Sélectionnés dynamiquement via la variable d'environnement `T212_ENV` (valeurs `demo` ou `live`).
- **Sécurisation et Isolation (Failsafe SHA256)**:
  - Validation stricte des hashes SHA256 des clés Bybit/T212 pour interdire formellement le mélange d'environnements (utiliser une clé de Demo en Prod ou inversement). Les hashes attendus sont configurés via `EXPECTED_T212_DEMO_KEY_HASH` et `EXPECTED_T212_LIVE_KEY_HASH`.
- **Contrainte de Devise Unique (EUR)**:
  - Le compte Trading 212 utilise une devise unique (ex: EUR). Afin d'éviter les rejets de transaction pour les devises non supportées en direct, tous les actifs doivent être mappés vers des instruments libellés dans cette devise (ex: Novartis en USD `NVS` ou CHF `NOVNs_EQ` est mappé vers `NOTd1_EQ` en EUR sur Xetra via `resolver.py` et la table statique `T212_STATIC_MAPPING` définie dans `utils.py`).
- **Idempotence & Réconciliation**:
  - Les requêtes d'ordres ne sont pas nativement idempotentes sur l'API Trading 212. L'idempotence est garantie par un verrou Redis SETNX `lock:t212:order:{ticker}` expirat dans 15 secondes.
  - Avant de soumettre ou de retenter un ordre en échec, effectuer une réconciliation en interrogeant les positions en cours (`get_positions()`) et comparer la quantité actuelle avec la quantité attendue pour éviter les exécutions en doublon.
- **Gestion du Rate-Limiting & Timeouts**:
  - Limite officielle : 50 requêtes/minute.
  - Implémenter un throttling côté client (pacing de 1.2s minimum entre les requêtes vers les endpoints d'ordre).
  - Timeout réseau explicite obligatoire de 10s (`NETWORK_TIMEOUT_DEFAULT = 10.0`).
  - Utiliser la bibliothèque `tenacity` pour gérer les retries automatiques exclusivement sur les erreurs temporaires (codes HTTP 429 et >=500).

## 3. Schémas de Référence (Patterns)

### A. Configuration Multi-Environnement & Failsafe SHA256
```python
import os
import hashlib

class Trading212Config:
    def __init__(self):
        self.env = os.getenv("T212_ENV", "demo").lower()
        if self.env == "live":
            self.api_key_id = os.getenv("T212_LIVE_API_KEY_ID")
            self.api_secret = os.getenv("T212_LIVE_API_SECRET")
            self.base_url = "https://live.trading212.com"
        else:
            self.api_key_id = os.getenv("T212_DEMO_API_KEY_ID")
            self.api_secret = os.getenv("T212_DEMO_API_SECRET")
            self.base_url = "https://demo.trading212.com"

    def validate(self):
        if not self.api_key_id or not self.api_secret:
            raise ValueError("Credentials Trading 212 manquantes.")
            
        key_hash = hashlib.sha256(self.api_secret.encode("utf-8")).hexdigest()
        expected_live_hash = os.getenv("EXPECTED_T212_LIVE_KEY_HASH")
        expected_demo_hash = os.getenv("EXPECTED_T212_DEMO_KEY_HASH")
        
        if self.env == "live" and expected_demo_hash and key_hash == expected_demo_hash:
            raise ValueError("CRITICAL: Clé de Demo détectée en environnement Live !")
        if self.env != "live" and expected_live_hash and key_hash == expected_live_hash:
            raise ValueError("CRITICAL: Clé Live détectée en environnement Demo/Testnet !")
```

### B. Routage avec Verrou Redis et Réconciliation Pré-Trade
```python
import time
from decimal import Decimal
from tenacity import Retrying, stop_after_attempt, wait_random_exponential, retry_if_exception

class Trading212Client:
    def __init__(self, config, redis_client):
        self.config = config
        self.redis = redis_client
        self.base_delay = 1.2 # 1.2s pour respecter les 50 req/min

    def place_market_order(self, ticker: str, quantity: Decimal) -> dict:
        lock_key = f"lock:t212:order:{ticker}"
        
        # 1. Acquisition du verrou Redis
        if self.redis:
            if not self.redis.set(lock_key, "locked", ex=15, nx=True):
                raise ValueError(f"Ordre concurrent bloqué pour le ticker {ticker}")
                
        try:
            # 2. Récupération des positions pour la réconciliation initiale
            initial_qty = self.get_position_qty(ticker)
            
            payload = {"ticker": ticker, "quantity": float(quantity)}
            
            # 3. Retry Loop avec réconciliation pré-tentative
            for attempt in range(3):
                if attempt > 0:
                    current_qty = self.get_position_qty(ticker)
                    expected_qty = initial_qty + quantity
                    if abs(current_qty - expected_qty) < Decimal("1e-7"):
                        # Ordre déjà exécuté lors de la tentative précédente
                        return {"ticker": ticker, "status": "FILLED", "reconciled": True}
                
                try:
                    time.sleep(self.base_delay) # Pacing
                    response = requests.post(
                        f"{self.config.base_url}/api/v0/equity/orders/market",
                        json=payload,
                        auth=(self.config.api_key_id, self.config.api_secret),
                        timeout=10.0
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    if attempt == 2:
                        raise e
        finally:
            if self.redis:
                self.redis.delete(lock_key)
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Requêtes en rafale (Bursting)**: Envoyer plusieurs ordres en parallèle sans pacing client de 1.2s minimum, provoquant des erreurs 429.
- ❌ **Ignorer la Devise du Compte**: Envoyer des ordres sur des instruments en USD ou CHF directement sur un compte libellé en EUR sans utiliser le mapping statique `T212_STATIC_MAPPING`.
- ❌ **Absence de Timeout**: Laisser les requêtes HTTP sans paramètre de timeout explicite, ce qui peut bloquer indéfiniment le thread d'exécution.

## 5. Interactions avec les autres Skills
- Reçoit l'instruction de routage depuis `execution-order-routing`.
- Collabore avec `paper-trading` pour s'assurer que la validation et les retours d'API Trading 212 simulés correspondent parfaitement au comportement réel du courtier.
