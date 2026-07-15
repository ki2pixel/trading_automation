import json

def get_instruments():
    cache_path = "/tmp/t212_instruments.json"
    with open(cache_path, "r") as f:
        return json.load(f)

def search_name_or_ticker(instruments, query):
    query = query.lower()
    results = []
    for inst in instruments:
        ticker = inst.get("ticker", "").lower()
        name = inst.get("name", "").lower()
        isin = inst.get("isin", "").lower()
        if query in ticker or query in name or query in isin:
            results.append(inst)
    return results

def main():
    instruments = get_instruments()

    queries = {
        "NVS": ["novartis", "CH0012005267"],
        "GMAB": ["genmab", "DK0010272202"],
        "teniteur": ["tenaris", "LU0156801721"],
    }

    for asset, terms in queries.items():
        print(f"\n=== Diagnostics for {asset} ===")
        seen = set()
        for term in terms:
            for inst in search_name_or_ticker(instruments, term):
                t = inst.get("ticker")
                if t not in seen:
                    seen.add(t)
                    print(f"  Ticker: {t:12} | Name: {inst.get('name'):35} | ISIN: {inst.get('isin')}")

if __name__ == "__main__":
    main()
