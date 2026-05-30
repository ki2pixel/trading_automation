"""
Test multi-tickers: polling batch des prix temps reel via /equity/portfolio
et ecriture CSV. Trading212 API (Beta) - Mode DEMO.

Usage:
    export T212_API_KEY_ID="ton_id"
    export T212_API_SECRET="ta_secret"

    # Test complet (place ordres + poll + vend + CSV)
    python3 test_multi_tickers.py --quantity 0.1

    # Polling uniquement (positions deja ouvertes)
    python3 test_multi_tickers.py --dry-run

    # Poll plus long
    python3 test_multi_tickers.py --duration 10 --interval 60

    # Ne pas vendre a la fin (garder les positions)
    python3 test_multi_tickers.py --no-cleanup

HORAIRES DE MARCHE PAR TICKER (Bourses reelles Trading212):
  GETTEX (07:30/08:00 - 22:00 CET, liquidite reduite en soiree):
    - GE9d_EQ  (Genmab)          ISIN: DK0010272202
    - 22Zd_EQ  (Zealand Pharma)  ISIN: DK0060257814

  DEUTSCHE BORSE XETRA (09:00 - 17:30 CET):
    - NOVCd_EQ (Novo Nordisk)      ISIN: DK0062498333
    - SHLd_EQ  (Siemens Health.)   ISIN: DE000SHL1006
    - EVDd_EQ  (CTS Eventim)       ISIN: DE0005470306
    - SAPd_EQ  (SAP)               ISIN: DE0007164600
    - FPEd_EQ  (Fuchs)             ISIN: DE000A3E5D56
    - LOGNs_EQ (Logitech)          ISIN: CH0025751329
    - NOTd1_EQ (Novartis)          ISIN: CH0012005267

  BOLSA DE MADRID (09:00 - 17:30 CET):
    - AMSe_EQ  (Amadeus IT)        ISIN: ES0109067019

  Hors ces horaires, les ordres restent en file d'attente.
  Le compte demo ne peut pas etre recharge via API (reset manuel dans l'app).

La watchlist est definie en constante ci-dessous.
"""

import argparse
import csv
import os
import sys
import time
import json
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth


# =============================================================================
# WATCHLIST (ISIN → Name)
# =============================================================================
WATCHLIST = {
    "DK0010272202": "GENMAB A/S",
    "DK0062498333": "NOVO NORDISK A/S",
    "DK0060257814": "ZEALAND PHARMA A/S",
    "DE000SHL1006": "SIEMENS HEALTHINEERS AG",
    "DE0005470306": "CTS EVENTIM AG & CO KGAA",
    "DE0007164600": "SAP SE",
    "DE000A3E5D56": "FUCHS SE",
    "CH0025751329": "LOGITECH INTERNATIONAL SA",
    "CH0012005267": "NOVARTIS AG",
    "ES0109067019": "AMADEUS IT GROUP SA",
}


# =============================================================================
# CLIENT T212
# =============================================================================
class Trading212Client:
    """Client minimal pour l'API officielle Trading212 avec Basic Auth."""

    def __init__(self, api_key_id: str, api_secret: str, host: str = "https://demo.trading212.com"):
        self.host = host
        self.auth = HTTPBasicAuth(api_key_id, api_secret)
        self.headers = {"Content-Type": "application/json"}
        self._last_request_time = 0
        self._min_delay = 2.5

    def _throttle(self, min_delay: float = None):
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

    def close_position(self, ticker: str, quantity: float):
        """Ferme une position en vendant (quantite negative)."""
        sell_qty = -abs(quantity)
        return self.place_market_order(ticker, sell_qty)


# =============================================================================
# UTILITAIRES
# =============================================================================
def resolve_tickers_from_isins(client: Trading212Client, isin_map: dict) -> dict:
    """
    Charge la liste des instruments et mappe les ISINs vers les tickers T212.
    Retourne: {isin: {'ticker': str, 'name': str, 'currency': str}}
    """
    print("\n[SETUP] Recuperation des instruments (mapping ISIN → Ticker)...")
    instruments = client.instruments()
    print(f"  {len(instruments)} instruments disponibles.")

    isin_to_ticker = {}
    not_found = []

    for isin, name in isin_map.items():
        found = None
        for inst in instruments:
            if inst.get("isin", "").upper() == isin.upper():
                found = inst
                break
        if found:
            isin_to_ticker[isin] = {
                "ticker": found.get("ticker"),
                "name": found.get("name", name),
                "currency": found.get("currencyCode", "?"),
                "type": found.get("type", "?"),
            }
            print(f"  OK  {isin} → {found.get('ticker')} ({found.get('name')})")
        else:
            not_found.append(isin)
            print(f"  KO  {isin} ({name}) → NON TROUVE")

    if not_found:
        print(f"\n  ATTENTION: {len(not_found)} ISIN(s) non trouve(s): {', '.join(not_found)}")

    return isin_to_ticker


def cleanup_positions(client: Trading212Client):
    """
    Recupere le portfolio et vend toutes les positions ouvertes.
    Retourne (vendus, echecs).
    """
    print("\n[CLEANUP] Fermeture des positions ouvertes...")
    try:
        portfolio = client.portfolio()
    except Exception as e:
        print(f"  ERREUR lors de la recuperation du portfolio: {e}")
        return [], []

    sold = []
    failed = []

    for idx, item in enumerate(portfolio, 1):
        ticker = item.get("ticker", "N/A")
        qty = item.get("quantity", item.get("ownedQuantity", 0))
        if not qty or qty <= 0:
            continue
        print(f"  [{idx}/{len(portfolio)}] Vente {ticker} x {qty}...", end=" ")
        try:
            result = client.close_position(ticker, qty)
            print(f"OK (ID={result.get('id', 'N/A')})")
            sold.append({"ticker": ticker, "quantity": qty, "order_id": result.get("id")})
        except requests.exceptions.HTTPError as e:
            print(f"ERREUR HTTP {e.response.status_code}: {e.response.text[:120]}")
            failed.append(ticker)
        except Exception as e:
            print(f"ERREUR: {e}")
            failed.append(ticker)

    if sold:
        print("  Attente 5s pour execution des ventes...")
        time.sleep(5)
    print(f"  {len(sold)} position(s) vendue(s), {len(failed)} echec(s).")
    return sold, failed


def place_orders(client: Trading212Client, tickers: dict, quantity: float):
    """
    Place un ordre market pour chaque ticker.
    tickers: {isin: {'ticker': str, ...}}
    """
    print(f"\n[ORDERS] Placement de {len(tickers)} ordres market (qty={quantity})...")
    placed = []
    failed = []

    for idx, (isin, info) in enumerate(tickers.items(), 1):
        ticker = info["ticker"]
        print(f"  [{idx}/{len(tickers)}] {ticker} ({info['name']})...", end=" ")
        try:
            result = client.place_market_order(ticker=ticker, quantity=quantity)
            print(f"OK (ID={result.get('id', 'N/A')})")
            placed.append({
                "isin": isin,
                "ticker": ticker,
                "name": info["name"],
                "order_id": result.get("id"),
                "status": result.get("status", "?"),
            })
        except requests.exceptions.HTTPError as e:
            print(f"ERREUR HTTP {e.response.status_code}: {e.response.text[:120]}")
            failed.append(isin)
        except Exception as e:
            print(f"ERREUR: {e}")
            failed.append(isin)

    print(f"\n  {len(placed)} ordre(s) place(s), {len(failed)} echec(s).")
    return placed, failed


def extract_portfolio_data(portfolio: list, isin_map: dict, ticker_to_isin: dict) -> list:
    """
    Extrait les donnees de prix depuis /portfolio.
    Retourne une liste de dicts prete pour le CSV.
    """
    rows = []
    for item in portfolio:
        ticker = item.get("ticker", "N/A")
        isin = ticker_to_isin.get(ticker, "UNKNOWN")
        name = isin_map.get(isin, ticker)

        rows.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "isin": isin,
            "name": name,
            "quantity": item.get("quantity", item.get("ownedQuantity", "N/A")),
            "average_price": item.get("averagePrice", "N/A"),
            "current_price": item.get("currentPrice", item.get("lastPrice", item.get("price", "N/A"))),
            "ppl": item.get("ppl", item.get("result", "N/A")),
            "currency": item.get("currencyCode", "N/A"),
        })
    return rows


def write_csv_header(csv_path: str):
    """Ecrit l'en-tete CSV une seule fois."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "ticker", "isin", "name",
            "quantity", "average_price", "current_price", "ppl", "currency"
        ])
        writer.writeheader()


def append_csv_rows(csv_path: str, rows: list):
    """Ajoute des lignes au CSV existant."""
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "ticker", "isin", "name",
            "quantity", "average_price", "current_price", "ppl", "currency"
        ])
        writer.writerows(rows)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================
def run_multi_ticker_test(client: Trading212Client, tickers: dict, quantity: float,
                          duration_min: int, interval_sec: int, csv_path: str,
                          dry_run: bool = False, cleanup: bool = True):
    """
    Execute le test multi-tickers complet.
    """
    print("=" * 70)
    print("TEST MULTI-TICKERS - TRADING212 DEMO")
    print(f"Tickers: {len(tickers)} | Duration: {duration_min}min | Interval: {interval_sec}s")
    print(f"CSV output: {csv_path}")
    if dry_run:
        print("MODE DRY-RUN: pas de placement d'ordres (polling positions existantes)")
    print("=" * 70)

    # --- 1. Point de controle ---
    print("\n[1/4] Verification du compte demo...")
    try:
        cash = client.cash()
        print(f"  Free: {cash.get('free', 'N/A')} | Total: {cash.get('total', 'N/A')}")
    except Exception as e:
        print(f"  ERREUR: {e}")
        return

    # --- 2. Placement des ordres (si pas dry-run) ---
    if not dry_run:
        placed, failed = place_orders(client, tickers, quantity)
        if failed:
            print(f"\n  ATTENTION: {len(failed)} ordre(s) en echec. On continue quand meme.")
        if placed:
            print("  Attente 5s pour execution des ordres...")
            time.sleep(5)
    else:
        print("\n[2/4] DRY-RUN: pas de placement d'ordres. On utilise les positions existantes.")
        time.sleep(1)

    # --- 3. Initialisation CSV ---
    print(f"\n[3/4] Initialisation du fichier CSV: {csv_path}")
    write_csv_header(csv_path)

    # --- 4. Polling loop ---
    print(f"\n[4/4] Polling /portfolio toutes les {interval_sec}s pendant {duration_min}min")
    print("-" * 70)

    isin_map = {isin: info["name"] for isin, info in tickers.items()}
    ticker_to_isin = {info["ticker"]: isin for isin, info in tickers.items()}

    for i in range(1, duration_min + 1):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n--- Iteration {i}/{duration_min} | {now} ---")

        try:
            portfolio = client.portfolio()
            print(f"  /portfolio: {len(portfolio)} item(s)")

            if portfolio:
                rows = extract_portfolio_data(portfolio, isin_map, ticker_to_isin)
                append_csv_rows(csv_path, rows)
                for row in rows:
                    print(f"    {row['ticker']!s:12s} | Qty: {row['quantity']!s:>5s} | "
                          f"Avg: {row['average_price']!s:>8s} | "
                          f"Current: {row['current_price']!s:>8s} | P&L: {row['ppl']!s}")
            else:
                print("    Portfolio vide (aucune position ouverte).")

        except requests.exceptions.HTTPError as e:
            print(f"  ERREUR HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"  ERREUR: {e}")

        if i < duration_min:
            print(f"  Attente {interval_sec}s...")
            time.sleep(interval_sec)

    # --- 5. Cleanup: vendre les positions ---
    if cleanup and not dry_run:
        cleanup_positions(client)
    elif cleanup and dry_run:
        print("\n[CLEANUP] Skip (dry-run: positions non placees par ce script).")
    else:
        print("\n[CLEANUP] Desactive (--no-cleanup). Positions conservees.")

    print("\n" + "=" * 70)
    print("TEST TERMINE")
    print(f"Donnees sauvegardees dans: {csv_path}")
    if cleanup and not dry_run:
        cash = client.cash()
        print(f"Cash restant: {cash.get('free', 'N/A')} | Total: {cash.get('total', 'N/A')}")
    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Test multi-tickers: polling batch + export CSV (Trading212 DEMO)"
    )
    parser.add_argument("--api-key-id", default=os.getenv("T212_API_KEY_ID"), help="ID cle API")
    parser.add_argument("--api-secret", default=os.getenv("T212_API_SECRET"), help="Cle secrete")
    parser.add_argument("--quantity", type=float, default=0.1,
                        help="Quantite par ordre (defaut: 0.1)")
    parser.add_argument("--duration", type=int, default=5,
                        help="Nombre d'iterations/minutes (defaut: 5)")
    parser.add_argument("--interval", type=int, default=60,
                        help="Intervalle entre iterations en secondes (defaut: 60)")
    parser.add_argument("--csv", default=None,
                        help="Chemin du fichier CSV de sortie (defaut: auto-genere)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Ne pas placer d'ordres, utiliser les positions existantes")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Ne pas vendre les positions a la fin du test")
    args = parser.parse_args()

    if not args.api_key_id or not args.api_secret:
        print("ERREUR: Fournir --api-key-id et --api-secret")
        print("  Ou definir les variables d'environnement:")
        print("    export T212_API_KEY_ID='ton_id'")
        print("    export T212_API_SECRET='ta_secret'")
        sys.exit(1)

    # CSV auto-genere si non specifie
    csv_path = args.csv
    if not csv_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"t212_multi_ticker_{timestamp}.csv"
    csv_path = os.path.abspath(csv_path)

    client = Trading212Client(api_key_id=args.api_key_id, api_secret=args.api_secret)

    # --- Resolution ISIN → Ticker ---
    tickers = resolve_tickers_from_isins(client, WATCHLIST)
    if not tickers:
        print("ERREUR: Aucun ticker resolu. Verifiez les ISINs.")
        sys.exit(1)

    run_multi_ticker_test(
        client=client,
        tickers=tickers,
        quantity=args.quantity,
        duration_min=args.duration,
        interval_sec=args.interval,
        csv_path=csv_path,
        dry_run=args.dry_run,
        cleanup=not args.no_cleanup,
    )


if __name__ == "__main__":
    main()
