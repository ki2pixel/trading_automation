import json

ASSET_CANDIDATES = {
    "ZEAL.CO": ["TIMd_EQ"],             # Zeal Network (Xetra, EUR)
    "NVO": ["NOVCd_EQ", "NVO_US_EQ"],   # Novo Nordisk
    "EVD.DE": ["EVDd_EQ"],              # CTS Eventim
    "GMAB": ["GE9d_EQ", "GMAB_US_EQ"],   # Genmab
    "FPE.DE": ["FPEd_EQ"],              # Fuchs
    "dpwdeeur": ["DPWd_EQ"],            # DHL Group (Deutsche Post)
    "teniteur": ["TW10d_EQ", "TS_US_EQ"], # Tenaris
    "akzanleur": ["AKZAa_EQ"],          # Akzo Nobel
    "daideeur": ["DAId_EQ", "DTGd_EQ"],  # Mercedes-Benz Group (formerly Daimler)
    "SAP": ["SAPd_EQ"],                 # SAP
    "mrkdeeur": ["MRKd_EQ"],            # Merck
    "AMS.MC": ["AMSe_EQ"],              # Amadeus IT
    "vnadeeur": ["VNAd_EQ"],            # Vonovia
    "acfreur": ["ACp_EQ"],              # Accor
    "lxsdeeur": ["LXSd_EQ"],            # Lanxess
    "randnleur": ["RANDa_EQ"],          # Randstad
    "rifreur": ["RUIp_EQ"],             # Rubis
    "abibeeur": ["ABI_BE_EQ"],          # AB InBev
    "belgbeeur": ["PROX_BE_EQ"],        # Proximus
    "cafreur": ["CAp_EQ"],              # Carrefour
    "NVS": ["NOTd1_EQ", "NVS_US_EQ", "NOVNs_EQ"] # Novartis
}

def main():
    with open("/tmp/t212_instruments.json", "r") as f:
        instruments = json.load(f)

    inst_map = {inst["ticker"]: inst for inst in instruments}

    print("Resolved mappings with details:")
    print("-" * 80)
    for asset, tickers in ASSET_CANDIDATES.items():
        print(f"Asset: {asset}")
        for ticker in tickers:
            inst = inst_map.get(ticker)
            if inst:
                print(f"  Ticker: {ticker:12} | Name: {inst.get('name'):35} | Currency: {inst.get('currencyCode'):4} | ISIN: {inst.get('isin')}")
            else:
                print(f"  Ticker: {ticker:12} | [NOT FOUND IN INSTRUMENTS]")

if __name__ == "__main__":
    main()
