import os
import json
import csv
import argparse
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path

# Actifs cibles avec indications de recherche locale et heuristiques
TARGET_ASSETS = {
    "akzanleur": {
        "search_name": "Akzo Nobel",
        "search_ticker": "AKZA",
        "preferred_currency": "EUR",
        "suffixes": ["AKZAa_EQ", "_NL_EQ", "AKZA_NL_EQ", "AKZAd_EQ"],
        "description_local": "Akzo Nobel NV",
        "isin_default": "NL0013267909",
        "t212_ticker_default": "AKZAa_EQ"
    },
    "dpwdeeur": {
        "search_name": "Deutsche Post",
        "search_ticker": "DPW",
        "preferred_currency": "EUR",
        "suffixes": ["DPWd_EQ", "DHLd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Deutsche Post AG",
        "isin_default": "DE0005552004",
        "t212_ticker_default": "DPWd_EQ"
    },
    "teniteur": {
        "search_name": "Tenaris",
        "search_ticker": "TEN",
        "preferred_currency": "EUR",
        "suffixes": ["TW10d_EQ", "TEN_IT_EQ", "TENd_EQ"],
        "description_local": "Tenaris SA",
        "isin_default": "LU2598331598",
        "t212_ticker_default": "TW10d_EQ"
    },
    "SAP": {
        "search_name": "SAP",
        "search_ticker": "SAP",
        "preferred_currency": "EUR",
        "suffixes": ["SAPd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "SAP SE",
        "isin_default": "DE0007164600",
        "t212_ticker_default": "SAPd_EQ"
    },
    "EVD.DE": {
        "search_name": "Evotec",
        "search_ticker": "EVT",
        "preferred_currency": "EUR",
        "suffixes": ["EVTd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Evotec SE",
        "isin_default": "DE0005664809",
        "t212_ticker_default": "EVTd_EQ"
    },
    "GMAB": {
        "search_name": "Genmab",
        "search_ticker": "GE9",
        "preferred_currency": "EUR",
        "suffixes": ["GE9d_EQ", "_DK_EQ", "GMAB_DK_EQ"],
        "description_local": "Genmab A/S",
        "isin_default": "DK0010272202",
        "t212_ticker_default": "GE9d_EQ"
    },
    "randnleur": {
        "search_name": "Randstad",
        "search_ticker": "RAND",
        "preferred_currency": "EUR",
        "suffixes": ["RANDa_EQ", "_NL_EQ", "RAND_NL_EQ", "RANDd_EQ"],
        "description_local": "Randstad NV",
        "isin_default": "NL0000379121",
        "t212_ticker_default": "RANDa_EQ"
    },
    "FPE.DE": {
        "search_name": "Fuchs",
        "search_ticker": "FPE",
        "preferred_currency": "EUR",
        "suffixes": ["FPEd_EQ", "FPE3d_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Fuchs SE",
        "isin_default": "DE000A3E5D56",
        "t212_ticker_default": "FPEd_EQ"
    },
    "NVO": {
        "search_name": "Novo Nordisk",
        "search_ticker": "NOV",
        "preferred_currency": "EUR",
        "suffixes": ["NOVCd_EQ", "NOVOb_DK_EQ", "NOVObd_EQ"],
        "description_local": "Novo Nordisk A/S",
        "isin_default": "DK0062498333",
        "t212_ticker_default": "NOVCd_EQ"
    },
    "NVS": {
        "search_name": "Novartis",
        "search_ticker": "NOV",
        "preferred_currency": "EUR",
        "suffixes": ["NOTd1_EQ", "NOVNs_EQ", "NOVN_CH_EQ", "NOVNd_EQ"],
        "description_local": "Novartis AG",
        "isin_default": "CH0012005267",
        "t212_ticker_default": "NOTd1_EQ"
    },
    "ZEAL.CO": {
        "search_name": "Zeal",
        "search_ticker": "ZEAL",
        "preferred_currency": "EUR",
        "suffixes": ["TIMd_EQ", "ZEALd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Zeal Network SE",
        "isin_default": "DE000ZEAL241",
        "t212_ticker_default": "TIMd_EQ"
    },
    "AMS.MC": {
        "search_name": "Amadeus IT",
        "search_ticker": "AMS",
        "preferred_currency": "EUR",
        "suffixes": ["AMSe_EQ", "AMS_ES_EQ", "AMSd_EQ"],
        "description_local": "Amadeus IT Group SA",
        "isin_default": "ES0109067019",
        "t212_ticker_default": "AMSe_EQ"
    },
    "daideeur": {
        "search_name": "Mercedes-Benz",
        "search_ticker": "DAI",
        "preferred_currency": "EUR",
        "suffixes": ["DAId_EQ", "MBGd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Daimler AG (Mercedes-Benz Group)",
        "isin_default": "DE0007100000",
        "t212_ticker_default": "DAId_EQ"
    },
    "acfreur": {
        "search_name": "Accor",
        "search_ticker": "AC",
        "preferred_currency": "EUR",
        "suffixes": ["ACp_EQ", "_FR_EQ", "AC_FR_EQ", "ACd_EQ"],
        "description_local": "Accor SA",
        "isin_default": "FR0000120404",
        "t212_ticker_default": "ACp_EQ"
    },
    "mrkdeeur": {
        "search_name": "Merck KGaA",
        "search_ticker": "MRK",
        "preferred_currency": "EUR",
        "suffixes": ["MRKd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Merck KGaA",
        "isin_default": "DE0006599905",
        "t212_ticker_default": "MRKd_EQ"
    },
    "vnadeeur": {
        "search_name": "Vonovia",
        "search_ticker": "VNA",
        "preferred_currency": "EUR",
        "suffixes": ["VNAd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Vonovia SE",
        "isin_default": "DE000A1ML7J1",
        "t212_ticker_default": "VNAd_EQ"
    },
    "rifreur": {
        "search_name": "Pernod Ricard",
        "search_ticker": "RI",
        "preferred_currency": "EUR",
        "suffixes": ["RIp_EQ", "_FR_EQ", "RI_FR_EQ", "RId_EQ"],
        "description_local": "Pernod-Ricard SA",
        "isin_default": "FR0000120693",
        "t212_ticker_default": "RIp_EQ"
    },
    "belgbeeur": {
        "search_name": "Proximus",
        "search_ticker": "BELG",
        "preferred_currency": "EUR",
        "suffixes": ["PROX_BE_EQ", "_BE_EQ", "BELG_BE_EQ"],
        "description_local": "Proximus SADP",
        "isin_default": "BE0003810273",
        "t212_ticker_default": "PROX_BE_EQ"
    },
    "abibeeur": {
        "search_name": "Anheuser-Busch",
        "search_ticker": "ABI",
        "preferred_currency": "EUR",
        "suffixes": ["ABI_BE_EQ", "_BE_EQ", "ABId_EQ"],
        "description_local": "Anheuser-Busch InBev SA/NV",
        "isin_default": "BE0974293251",
        "t212_ticker_default": "ABI_BE_EQ"
    },
    "lxsdeeur": {
        "search_name": "Lanxess",
        "search_ticker": "LXS",
        "preferred_currency": "EUR",
        "suffixes": ["LXSd_EQ", "_DE_EQ", "_GY_EQ"],
        "description_local": "Lanxess AG",
        "isin_default": "DE0005470405",
        "t212_ticker_default": "LXSd_EQ"
    },
    "cafreur": {
        "search_name": "Carrefour",
        "search_ticker": "CA",
        "preferred_currency": "EUR",
        "suffixes": ["CAp_EQ", "_FR_EQ", "CA_FR_EQ", "CAd_EQ"],
        "description_local": "Carrefour SA",
        "isin_default": "FR0000120172",
        "t212_ticker_default": "CAp_EQ"
    }
}

CACHE_FILE = Path("/home/kidpixel/trading_automation_v2/ressources/trading212/trading212-api-extended-main/instruments_cache.json")

def load_instruments(api_key_id, api_secret):
    """Charge la liste complète des instruments depuis l'API ou le cache local."""
    if CACHE_FILE.exists():
        print(f"Loading instruments from cache: {CACHE_FILE}")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    if not api_key_id or not api_secret:
        return None
        
    print("Fetching instruments from Trading 212 DEMO API...")
    url = "https://demo.trading212.com/api/v0/equity/metadata/instruments"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(api_key_id, api_secret), timeout=60)
        response.raise_for_status()
        instruments = response.json()
        
        # Enregistrer dans le cache
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(instruments, f, indent=2)
        print(f"Instruments saved to cache ({len(instruments)} loaded)")
        return instruments
    except Exception as e:
        print(f"API Request failed: {e}. Switching to offline mode.")
        return None

def perform_mapping(instruments):
    """Effectue la correspondance des 21 actifs avec les instruments T212 ou utilise les valeurs par défaut."""
    mappings = []
    
    if instruments is None:
        print("Using validated local mappings (Offline / Fallback mode)...")
        for local_id, info in TARGET_ASSETS.items():
            mappings.append({
                "local_id": local_id,
                "real_name": info["description_local"],
                "isin": info["isin_default"],
                "t212_ticker": info["t212_ticker_default"],
                "currency": info["preferred_currency"],
                "score": 100
            })
        return mappings

    for local_id, info in TARGET_ASSETS.items():
        search_n = info["search_name"].lower()
        search_t = info["search_ticker"].lower()
        pref_currency = info["preferred_currency"]
        suffixes = info["suffixes"]
        
        candidates = []
        for inst in instruments:
            t212_ticker = inst.get("ticker", "")
            t212_name = inst.get("name", "")
            t212_currency = inst.get("currencyCode", "")
            
            # 1. Vérifier si le nom ou le ticker correspond
            match_name = search_n in t212_name.lower()
            match_ticker = search_t in t212_ticker.lower()
            
            if match_name or match_ticker:
                score = 0
                
                # Bonus pour la devise correspondante
                if t212_currency.upper() == pref_currency.upper():
                    score += 10
                    
                # Bonus si le nom d'entreprise exact ou très proche correspond
                if search_n in t212_name.lower():
                    score += 5
                    if t212_name.lower().startswith(search_n):
                        score += 3
                        
                # Bonus pour les suffixes de ticker préférés
                for suff in suffixes:
                    if t212_ticker.lower().endswith(suff.lower()) or suff.lower() in t212_ticker.lower():
                        score += 5
                        break
                        
                # Malus pour les ADRs américaines si on cherche une européenne (sauf si USD est préféré)
                if pref_currency != "USD" and t212_ticker.endswith("_US_EQ"):
                    score -= 10
                    
                # Malus si la devise ne correspond pas du tout
                if t212_currency.upper() != pref_currency.upper():
                    score -= 5
                    
                candidates.append((score, inst))
                
        # Trier par score décroissant
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        if candidates:
            best_score, best_inst = candidates[0]
            mappings.append({
                "local_id": local_id,
                "real_name": best_inst.get("name"),
                "isin": best_inst.get("isin"),
                "t212_ticker": best_inst.get("ticker"),
                "currency": best_inst.get("currencyCode"),
                "score": best_score
            })
            print(f"Mapped: {local_id} -> {best_inst.get('ticker')} ({best_inst.get('name')}) [Score: {best_score}]")
        else:
            # Repli sur les valeurs par défaut
            mappings.append({
                "local_id": local_id,
                "real_name": info["description_local"],
                "isin": info["isin_default"],
                "t212_ticker": info["t212_ticker_default"],
                "currency": pref_currency,
                "score": 0
            })
            print(f"FAILED to map via API: {local_id} (using default: {info['t212_ticker_default']})")
            
    return mappings

def save_mappings(mappings):
    """Sauvegarde le mapping consolidé dans les formats structurés CSV et JSON."""
    dir_path = Path("/home/kidpixel/trading_automation_v2/ressources/trading212/trading212-api-extended-main")
    
    csv_file = dir_path / "t212_assets_mapping.csv"
    json_file = dir_path / "t212_assets_mapping.json"
    
    # Sauvegarde JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2)
    print(f"Mapping JSON enregistré dans {json_file}")
    
    # Sauvegarde CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Identifiant local", "Nom réel d'entreprise", "ISIN", "Ticker Trading 212", "Devise"])
        for m in mappings:
            writer.writerow([m["local_id"], m["real_name"], m["isin"], m["t212_ticker"], m["currency"]])
    print(f"Mapping CSV enregistré dans {csv_file}")

def load_dotenv():
    """Charge les variables d'environnement du fichier .env s'il existe à la racine du projet."""
    repo_root = Path(__file__).resolve().parents[3]
    env_path = repo_root / ".env"
    if env_path.is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("\"'")
                        # Ne pas écraser une variable d'environnement déjà définie
                        if key and key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier .env : {e}")

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Automatisation du mapping des tickers Trading 212")
    parser.add_argument("--api-key-id", default=os.getenv("T212_API_KEY_ID"), help="ID de la clé API")
    parser.add_argument("--api-secret", default=os.getenv("T212_API_SECRET"), help="Clé secrète")
    args = parser.parse_args()
    
    # Mettre à jour les variables d'environnement au cas où elles auraient été passées en argument de ligne de commande
    if args.api_key_id:
        os.environ["T212_API_KEY_ID"] = args.api_key_id
    if args.api_secret:
        os.environ["T212_API_SECRET"] = args.api_secret
    
    instruments = load_instruments(args.api_key_id or os.getenv("T212_API_KEY_ID"), args.api_secret or os.getenv("T212_API_SECRET"))
    mappings = perform_mapping(instruments)
    save_mappings(mappings)

if __name__ == "__main__":
    main()
