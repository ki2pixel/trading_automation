"""
Script de test pour l'API officielle Trading212 (Beta) - Mode DEMO.

AUTHENTIFICATION: Basic HTTP
  username = ID de la clé API
  password = Clé secrète

Usage:
    export T212_API_KEY_ID="ton_id"
    export T212_API_SECRET="ta_secret"
    python test_official_api.py
"""

import argparse
import os
import time
import requests
import json
from requests.auth import HTTPBasicAuth


class Trading212Client:
    """Client minimal pour l'API officielle Trading212 avec Basic Auth."""

    def __init__(self, api_key_id: str, api_secret: str):
        self.host = "https://demo.trading212.com"
        self.auth = HTTPBasicAuth(api_key_id, api_secret)
        self.headers = {"Content-Type": "application/json"}
        self._last_request_time = 0
        self._min_delay = 2.5  # Respect rate limit: 1 req / 2s minimum

    def _throttle(self):
        """Attendre si nécessaire pour respecter le rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()

    def _get(self, endpoint: str):
        self._throttle()
        url = f"{self.host}/api/v0{endpoint}"
        response = requests.get(url, auth=self.auth, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: dict = None):
        self._throttle()
        url = f"{self.host}/api/v0{endpoint}"
        response = requests.post(url, auth=self.auth, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def account_summary(self):
        return self._get("/equity/account/summary")

    def cash(self):
        return self._get("/equity/account/cash")

    def portfolio(self):
        return self._get("/equity/portfolio")

    def instruments(self):
        return self._get("/equity/metadata/instruments")

    def equity_orders(self):
        return self._get("/equity/orders")

    def exchanges(self):
        return self._get("/equity/metadata/exchanges")

    def place_market_order(self, ticker: str, quantity: float):
        payload = {"ticker": ticker, "quantity": quantity}
        return self._post("/equity/orders/market", payload)


def test_api(client: Trading212Client):
    print("=" * 60)
    print("TEST API OFFICIELLE TRADING212 (DEMO)")
    print(f"Host: {client.host}")
    print("=" * 60)

    endpoints = [
        ("Account Summary", client.account_summary),
        ("Cash", client.cash),
        ("Portfolio", client.portfolio),
        ("Exchanges", client.exchanges),
        ("Pending Orders", client.equity_orders),
    ]

    for idx, (name, method) in enumerate(endpoints, 1):
        print(f"\n[{idx}/{len(endpoints)}] {name}...")
        try:
            result = method()
            if isinstance(result, list):
                print(f"  OK: {len(result)} items")
                if result:
                    print(f"  Exemple: {json.dumps(result[0], indent=2)[:200]}")
            elif isinstance(result, dict):
                print(f"  OK: {json.dumps(result, indent=2)[:300]}")
            else:
                print(f"  OK: {result}")
        except requests.exceptions.HTTPError as e:
            print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"  ERREUR: {e}")

    # Instruments est volumineux (~10k+ items)
    print(f"\n[{len(endpoints)+1}/{len(endpoints)+1}] Instruments (liste complète)...")
    try:
        result = client.instruments()
        print(f"  OK: {len(result)} instruments disponibles")
        if result:
            print(f"  Exemple: {json.dumps(result[0], indent=2)[:300]}")
    except requests.exceptions.HTTPError as e:
        print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        print(f"  ERREUR: {e}")

    print("\n" + "=" * 60)
    print("TEST TERMINE")
    print("=" * 60)


def test_market_order_demo(client: Trading212Client):
    """
    Place un ordre market en DEMO.
    L'ordre est réel sur le compte demo (fonds virtuels).
    """
    print("\n" + "!" * 60)
    print("TEST ORDRE MARKET (DEMO)")
    print("!" * 60)

    # Ticker européen - à adapter selon disponibilités du compte demo
    ticker = "SAP_GY_EQ"
    quantity = 0.1

    try:
        result = client.place_market_order(ticker=ticker, quantity=quantity)
        print(f"  Ordre placé: {json.dumps(result, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:300]}")
    except Exception as e:
        print(f"  ERREUR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test API Officielle Trading212 (DEMO)")
    parser.add_argument("--api-key-id", default=os.getenv("T212_API_KEY_ID"), help="ID de la clé API")
    parser.add_argument("--api-secret", default=os.getenv("T212_API_SECRET"), help="Clé secrète")
    parser.add_argument("--market-order", action="store_true",
                        help="Tester le placement d'un ordre market (demo)")
    args = parser.parse_args()

    if not args.api_key_id or not args.api_secret:
        print("ERREUR: Fournir --api-key-id et --api-secret")
        print("  Ou définir les variables d'environnement:")
        print("    export T212_API_KEY_ID='ton_id'")
        print("    export T212_API_SECRET='ta_secret'")
        return

    print("Mode: DEMO (Paper Trading)")
    print("   Délai entre requêtes: 2.5s (rate limit compliance)\n")

    client = Trading212Client(api_key_id=args.api_key_id, api_secret=args.api_secret)

    test_api(client)

    if args.market_order:
        test_market_order_demo(client)


if __name__ == "__main__":
    main()
