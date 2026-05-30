"""
Script de test pour le polling des prix temps reel via /equity/positions
et /equity/portfolio sur l'API Trading212 (Beta) - Mode DEMO.

Le script:
  1. Identifie le ticker T212 exact depuis un nom ou ISIN.
  2. Place un ordre market test (petite quantite) pour ouvrir une position.
  3. Polling toutes les minutes pendant 5 min sur /positions et /portfolio.
  4. Logge les prix courants, P&L, et headers de rate limit.

Usage:
    export T212_API_KEY_ID="ton_id"
    export T212_API_SECRET="ta_secret"
    python test_realtime_positions.py --name "SAP SE"
    python test_realtime_positions.py --isin "DE0007164600"
    python test_realtime_positions.py --ticker "SAP_GY_EQ"  # si deja connu
"""

import argparse
import os
import sys
import time
import json
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth


class Trading212Client:
    """Client minimal pour l'API officielle Trading212 avec Basic Auth."""

    def __init__(self, api_key_id: str, api_secret: str, host: str = "https://demo.trading212.com"):
        self.host = host
        self.auth = HTTPBasicAuth(api_key_id, api_secret)
        self.headers = {"Content-Type": "application/json"}
        self._last_request_time = 0
        self._min_delay = 2.5  # Respect rate limit general

    def _throttle(self, min_delay: float = None):
        """Attendre si necessaire pour respecter le rate limit."""
        delay = min_delay if min_delay is not None else self._min_delay
        elapsed = time.time() - self._last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.time()

    def _get(self, endpoint: str, min_delay: float = None):
        self._throttle(min_delay)
        url = f"{self.host}/api/v0{endpoint}"
        response = requests.get(url, auth=self.auth, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response

    def _post(self, endpoint: str, data: dict = None, min_delay: float = None):
        self._throttle(min_delay)
        url = f"{self.host}/api/v0{endpoint}"
        response = requests.post(url, auth=self.auth, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        return response

    def account_summary(self):
        return self._get("/equity/account/summary", min_delay=5.0).json()

    def cash(self):
        return self._get("/equity/account/cash", min_delay=5.0).json()

    def portfolio(self):
        return self._get("/equity/portfolio", min_delay=1.0).json()

    def positions(self):
        return self._get("/equity/positions", min_delay=1.0).json()

    def instruments(self):
        return self._get("/equity/metadata/instruments", min_delay=50.0).json()

    def place_market_order(self, ticker: str, quantity: float):
        payload = {"ticker": ticker, "quantity": quantity}
        return self._post("/equity/orders/market", payload, min_delay=2.0).json()


def find_ticker_by_isin(instruments: list, isin: str):
    """Recherche un instrument par ISIN exact."""
    isin_upper = isin.upper()
    for inst in instruments:
        if inst.get("isin", "").upper() == isin_upper:
            return inst
    return None


def find_ticker_by_name(instruments: list, name_query: str):
    """Recherche un instrument par nom (insensible a la casse, match partiel)."""
    query = name_query.lower()
    words = query.split()

    # Passage 1: match exact de tous les mots
    for inst in instruments:
        name = inst.get("name", "").lower()
        short_name = inst.get("shortName", "").lower()
        target = f"{name} {short_name}"
        if all(word in target for word in words):
            return inst

    # Passage 2: inclusion de la chaine complete
    for inst in instruments:
        name = inst.get("name", "").lower()
        short_name = inst.get("shortName", "").lower()
        if query in name or query in short_name:
            return inst

    # Passage 3: match sur le premier mot (le plus significatif)
    if words:
        first_word = words[0]
        for inst in instruments:
            name = inst.get("name", "").lower()
            short_name = inst.get("shortName", "").lower()
            if first_word == name or first_word == short_name or first_word in name.split():
                return inst

    # Passage 4: retourne le meilleur candidat par scoring
    best = find_best_matches_by_name(instruments, name_query, max_results=1)
    return best[0] if best else None


def find_best_matches_by_name(instruments: list, name_query: str, max_results: int = 10):
    """Retourne les meilleurs candidats par nom pour aider l'utilisateur."""
    query = name_query.lower()
    words = query.split()
    scored = []

    for inst in instruments:
        name = inst.get("name", "").lower()
        short_name = inst.get("shortName", "").lower()
        score = 0
        if query == name or query == short_name:
            score = 100
        elif query in name or query in short_name:
            score = 50
        else:
            matched_words = sum(1 for w in words if w in name or w in short_name)
            score = matched_words * 10
            # Bonus si le premier mot match exact
            if words and (words[0] == name or words[0] == short_name):
                score += 25

        if score > 0:
            scored.append((score, inst))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [inst for _, inst in scored[:max_results]]


def print_rate_limit_headers(response):
    """Affiche les headers de rate limit si presents."""
    headers = ["x-ratelimit-limit", "x-ratelimit-period",
               "x-ratelimit-remaining", "x-ratelimit-reset", "x-ratelimit-used"]
    for h in headers:
        val = response.headers.get(h)
        if val:
            print(f"    {h}: {val}")


def extract_price_info(data: dict, label: str):
    """Extrait et affiche les infos de prix depuis une position ou un portfolio item."""
    # /portfolio fields
    ticker = data.get("ticker", "N/A")
    quantity = data.get("quantity", data.get("ownedQuantity", "N/A"))
    average_price = data.get("averagePrice", "N/A")
    current_price = data.get("currentPrice", data.get("lastPrice", data.get("price", "N/A")))
    ppl = data.get("ppl", data.get("result", "N/A"))

    # /positions fields (structure differente)
    if ticker == "N/A":
        ticker = data.get("instrument", {}).get("ticker", "N/A")
    if quantity == "N/A":
        quantity = data.get("quantity", "N/A")
    if average_price == "N/A":
        average_price = data.get("averagePrice", "N/A")
    if current_price == "N/A":
        current_price = data.get("currentPrice", data.get("price", "N/A"))
    if ppl == "N/A":
        ppl = data.get("ppl", data.get("result", "N/A"))

    print(f"    [{label}] {ticker} | Qty: {quantity} | Avg: {average_price} | Current: {current_price} | P&L: {ppl}")
    return {
        "ticker": ticker,
        "quantity": quantity,
        "average_price": average_price,
        "current_price": current_price,
        "ppl": ppl,
    }


def run_realtime_test(client: Trading212Client, ticker: str, quantity: float):
    """Execute le test complet: ordre + polling 5 minutes."""

    print("=" * 70)
    print("TEST PRIX TEMPS REEL - TRADING212 DEMO")
    print("=" * 70)

    # --- 1. Point de controle: cash et resume ---
    print("\n[1/3] Verification du compte demo...")
    try:
        cash = client.cash()
        print(f"  Solde cash: {json.dumps(cash, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:200]}")
        return
    except Exception as e:
        print(f"  ERREUR: {e}")
        return

    # --- 2. Placement de l'ordre market ---
    print(f"\n[2/3] Placement ordre market TEST: {ticker} x {quantity}")
    print("  (!) Ordre reel sur compte demo (fonds virtuels)")
    try:
        order_result = client.place_market_order(ticker=ticker, quantity=quantity)
        print(f"  Ordre place: {json.dumps(order_result, indent=2)}")
        order_id = order_result.get("id", "N/A")
        print(f"  Order ID: {order_id}")
    except requests.exceptions.HTTPError as e:
        print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:300]}")
        return
    except Exception as e:
        print(f"  ERREUR: {e}")
        return

    # Attendre que l'ordre s'execute
    print("  Attente 5s pour execution de l'ordre...")
    time.sleep(5)

    # --- 3. Polling 5 minutes ---
    print("\n[3/3] Polling /positions et /portfolio toutes les 60s pendant 5min")
    print("-" * 70)

    for i in range(1, 6):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n--- Iteration {i}/5 | {now} ---")

        # /equity/positions
        try:
            resp = client._get("/equity/positions", min_delay=1.0)
            positions = resp.json()
            print(f"  /positions: {len(positions)} position(s)")
            print_rate_limit_headers(resp)
            for pos in positions:
                info = extract_price_info(pos, "POS")
        except requests.exceptions.HTTPError as e:
            print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"  ERREUR: {e}")

        # /equity/portfolio
        try:
            resp = client._get("/equity/portfolio", min_delay=1.0)
            portfolio = resp.json()
            print(f"  /portfolio: {len(portfolio)} item(s)")
            print_rate_limit_headers(resp)
            for item in portfolio:
                info = extract_price_info(item, "PFL")
        except requests.exceptions.HTTPError as e:
            print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"  ERREUR: {e}")

        if i < 5:
            print(f"  Attente 60s avant prochaine iteration...")
            time.sleep(60)

    print("\n" + "=" * 70)
    print("TEST TERMINE")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Test polling prix temps reel via positions/portfolio (Trading212 DEMO)"
    )
    parser.add_argument("--api-key-id", default=os.getenv("T212_API_KEY_ID"), help="ID de la cle API")
    parser.add_argument("--api-secret", default=os.getenv("T212_API_SECRET"), help="Cle secrete")
    parser.add_argument("--name", help="Nom de l'entreprise (ex: 'SAP SE')")
    parser.add_argument("--isin", help="ISIN exact (ex: DE0007164600)")
    parser.add_argument("--ticker", help="Ticker T212 direct (ex: SAP_GY_EQ)")
    parser.add_argument("--quantity", type=float, default=0.1, help="Quantite pour l'ordre test (defaut: 0.1)")
    args = parser.parse_args()

    if not args.api_key_id or not args.api_secret:
        print("ERREUR: Fournir --api-key-id et --api-secret")
        print("  Ou definir les variables d'environnement:")
        print("    export T212_API_KEY_ID='ton_id'")
        print("    export T212_API_SECRET='ta_secret'")
        sys.exit(1)

    client = Trading212Client(api_key_id=args.api_key_id, api_secret=args.api_secret)

    # --- Resoudre le ticker T212 ---
    target_ticker = args.ticker

    if not target_ticker:
        if not args.isin and not args.name:
            print("ERREUR: Specifier --ticker, --isin ou --name pour identifier l'instrument.")
            sys.exit(1)

        print("Recuperation de la liste des instruments (peut prendre ~5s)...")
        try:
            instruments = client.instruments()
            print(f"{len(instruments)} instruments charges.")
        except Exception as e:
            print(f"ERREUR lors du chargement des instruments: {e}")
            sys.exit(1)

        if args.isin:
            inst = find_ticker_by_isin(instruments, args.isin)
            if inst:
                target_ticker = inst.get("ticker")
                print(f"Trouve par ISIN: {inst.get('name')} -> {target_ticker}")
            else:
                print(f"ERREUR: Aucun instrument trouve pour l'ISIN {args.isin}")
                sys.exit(1)
        elif args.name:
            inst = find_ticker_by_name(instruments, args.name)
            if inst:
                target_ticker = inst.get("ticker")
                print(f"Trouve par nom: {inst.get('name')} -> {target_ticker}")
                print(f"  ISIN: {inst.get('isin')}, Devise: {inst.get('currencyCode')}, Type: {inst.get('type')}")
            else:
                print(f"Aucun instrument exact trouve pour le nom '{args.name}'")
                print("\nMeilleurs candidats:")
                for idx, cand in enumerate(find_best_matches_by_name(instruments, args.name), 1):
                    print(f"  [{idx}] {cand.get('ticker')} | {cand.get('name')} | ISIN: {cand.get('isin')}")
                print("\nEssayez avec --ticker <TICKER> ou --isin <ISIN>")
                sys.exit(1)

    print(f"\nTicker cible: {target_ticker} | Quantite: {args.quantity}")
    run_realtime_test(client, target_ticker, args.quantity)


if __name__ == "__main__":
    main()
