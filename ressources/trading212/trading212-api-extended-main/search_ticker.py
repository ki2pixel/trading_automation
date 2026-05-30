"""
Recherche de tickers dans la liste des instruments T212.

Usage:
    export T212_API_KEY_ID="ton_id"
    export T212_API_SECRET="ta_secret"
    
    python search_ticker.py --name "SAP"        # recherche par nom
    python search_ticker.py --isin "DE0007164600"  # recherche par ISIN
    python search_ticker.py --country "DE"      # tickers allemands
    python search_ticker.py --ticker "SAP"      # recherche par ticker (partiel)
"""

import argparse
import os
import requests
from requests.auth import HTTPBasicAuth


def get_instruments(api_key_id: str, api_secret: str):
    """Récupère la liste complète des instruments."""
    url = "https://demo.trading212.com/api/v0/equity/metadata/instruments"
    import time; time.sleep(2.5); response = requests.get(url, auth=HTTPBasicAuth(api_key_id, api_secret), timeout=60)
    response.raise_for_status()
    return response.json()


def search_by_name(instruments: list, query: str):
    """Recherche par nom (insensible à la casse)."""
    query = query.lower()
    results = []
    for inst in instruments:
        name = inst.get("name", "").lower()
        short_name = inst.get("shortName", "").lower()
        if query in name or query in short_name:
            results.append(inst)
    return results


def search_by_isin(instruments: list, isin: str):
    """Recherche par ISIN exact."""
    results = []
    for inst in instruments:
        if inst.get("isin", "").upper() == isin.upper():
            results.append(inst)
    return results


def search_by_ticker(instruments: list, ticker_query: str):
    """Recherche par ticker (partiel, insensible à la casse)."""
    query = ticker_query.lower()
    results = []
    for inst in instruments:
        ticker = inst.get("ticker", "").lower()
        if query in ticker:
            results.append(inst)
    return results


def search_by_country(instruments: list, country_code: str):
    """Recherche par pays (ex: 'DE', 'FR', 'US')."""
    # Sur T212, le pays est souvent dans le suffixe du ticker (ex: _GY_EQ = Germany/Xetra)
    # Ou on peut inférer depuis le workingScheduleId
    code = country_code.upper()
    results = []
    for inst in instruments:
        ticker = inst.get("ticker", "")
        # Heuristique: les tickers allemands ont souvent _GY_EQ ou _DE_EQ
        if f"_{code}_" in ticker.upper() or ticker.upper().endswith(f"_{code}_EQ"):
            results.append(inst)
    return results


def print_results(results: list, max_results: int = 10):
    """Affiche les résultats de recherche."""
    if not results:
        print("Aucun résultat trouvé.")
        return

    print(f"\n{len(results)} résultat(s) trouvé(s). Affichage des {min(max_results, len(results))} premiers:\n")

    for idx, inst in enumerate(results[:max_results], 1):
        print(f"[{idx}] {inst.get('ticker', 'N/A')}")
        print(f"    Nom:     {inst.get('name', 'N/A')}")
        print(f"    ISIN:    {inst.get('isin', 'N/A')}")
        print(f"    Type:    {inst.get('type', 'N/A')}")
        print(f"    Devise:  {inst.get('currencyCode', 'N/A')}")
        print(f"    Max Qty: {inst.get('maxOpenQuantity', 'N/A')}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Recherche de tickers Trading212")
    parser.add_argument("--api-key-id", default=os.getenv("T212_API_KEY_ID"), help="ID de la clé API")
    parser.add_argument("--api-secret", default=os.getenv("T212_API_SECRET"), help="Clé secrète")
    parser.add_argument("--name", help="Rechercher par nom d'entreprise")
    parser.add_argument("--isin", help="Rechercher par ISIN")
    parser.add_argument("--ticker", help="Rechercher par ticker (partiel)")
    parser.add_argument("--country", help="Rechercher par code pays (ex: DE, FR, US)")
    parser.add_argument("--max", type=int, default=10, help="Nombre max de résultats (défaut: 10)")
    args = parser.parse_args()

    if not args.api_key_id or not args.api_secret:
        print("ERREUR: Fournir --api-key-id et --api-secret")
        return

    if not any([args.name, args.isin, args.ticker, args.country]):
        print("ERREUR: Spécifier au moins un critère de recherche (--name, --isin, --ticker, --country)")
        return

    print("Récupération de la liste des instruments...")
    try:
        instruments = get_instruments(args.api_key_id, args.api_secret)
        print(f"{len(instruments)} instruments chargés.\n")
    except Exception as e:
        print(f"ERREUR: {e}")
        return

    results = []
    if args.name:
        print(f"Recherche par nom: '{args.name}'")
        results = search_by_name(instruments, args.name)
    elif args.isin:
        print(f"Recherche par ISIN: '{args.isin}'")
        results = search_by_isin(instruments, args.isin)
    elif args.ticker:
        print(f"Recherche par ticker: '{args.ticker}'")
        results = search_by_ticker(instruments, args.ticker)
    elif args.country:
        print(f"Recherche par pays: '{args.country}'")
        results = search_by_country(instruments, args.country)

    print_results(results, args.max)


if __name__ == "__main__":
    main()
