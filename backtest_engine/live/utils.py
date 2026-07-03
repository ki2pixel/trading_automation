import os
import json
from datetime import datetime
import datetime as dt

def is_crypto_asset(asset: str) -> bool:
    """
    Centralized utility to check if an asset is a cryptocurrency.
    Matches Bybit crypto assets ending in 'usdt' or 'usdc' (case-insensitive).
    """
    if not asset or not isinstance(asset, str):
        return False
    return asset.lower().endswith(("usdt", "usdc"))

# Static validated mappings for the 21 unique assets to T212 EUR tickers
T212_STATIC_MAPPING = {
    "ZEAL.CO": "TIMd_EQ",             # Zeal Network (Xetra, EUR)
    "NVO": "NOVCd_EQ",                 # Novo Nordisk (Xetra, EUR)
    "EVD.DE": "EVDd_EQ",               # CTS Eventim (Xetra, EUR)
    "GMAB": "GE9d_EQ",                 # Genmab (Xetra, EUR)
    "FPE.DE": "FPEd_EQ",               # Fuchs (Xetra, EUR)
    "dpwdeeur": "DPWd_EQ",             # DHL Group / Deutsche Post (Xetra, EUR)
    "teniteur": "TW10d_EQ",             # Tenaris (Xetra, EUR)
    "akzanleur": "AKZAa_EQ",           # Akzo Nobel (Amsterdam, EUR)
    "daideeur": "DAId_EQ",             # Mercedes-Benz Group / Daimler (Xetra, EUR)
    "SAP": "SAPd_EQ",                  # SAP (Xetra, EUR)
    "mrkdeeur": "MRKd_EQ",             # Merck KGaA (Xetra, EUR)
    "AMS.MC": "AMSe_EQ",               # Amadeus IT (Madrid, EUR)
    "vnadeeur": "VNAd_EQ",             # Vonovia (Xetra, EUR)
    "acfreur": "ACp_EQ",               # Accor (Paris, EUR)
    "lxsdeeur": "LXSd_EQ",             # LANXESS (Xetra, EUR)
    "randnleur": "RANDa_EQ",           # Randstad (Amsterdam, EUR)
    "rifreur": "RUIp_EQ",              # Rubis (Paris, EUR)
    "abibeeur": "ABI_BE_EQ",           # AB InBev (Brussels, EUR)
    "belgbeeur": "PROX_BE_EQ",         # Proximus (Brussels, EUR)
    "cafreur": "CAp_EQ",               # Carrefour (Paris, EUR)
    "NVS": "NOTd1_EQ"                  # Novartis (Xetra, EUR)
}

# Ticker Mapping: Trading 212 -> MarketFlow format (EXCHANGE:SYMBOL)
TICKER_MAPPING = {
    "ZEAL.CO": "FWB:TIMA",  # Zeal Network
    "NVO": "NYSE:NVO",
    "EVD.DE": "FWB:EVD",
    "GMAB": "NASDAQ:GMAB",
    "FPE.DE": "FWB:FPE",
    "SAP": "FWB:SAP",
    "NVS": "NYSE:NVS",
    "AMS.MC": "BME:AMS",
    "dpwdeeur": "FWB:DPW",
    "teniteur": "MIL:TEN",
    "akzanleur": "EURONEXT:AKZA",
    "daideeur": "FWB:MBG",
    "mrkdeeur": "FWB:MRK",
    "vnadeeur": "FWB:VNA",
    "acfreur": "EURONEXT:AC",
    "lxsdeeur": "FWB:LXS",
    "randnleur": "EURONEXT:RAND",
    "rifreur": "EURONEXT:RI",
    "abibeeur": "EURONEXT:ABI",
    "belgbeeur": "EURONEXT:PROX", # Proximus
    "cafreur": "EURONEXT:CA"
}

_market_hours_cache = None

def load_market_hours() -> dict:
    path = os.path.join(os.path.dirname(__file__), "../../configs/market_hours.json")
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[utils] Error loading market hours from {path}: {e}")
        return {}

def get_market_hours() -> dict:
    global _market_hours_cache
    if _market_hours_cache is None:
        _market_hours_cache = load_market_hours()
    return _market_hours_cache

def is_market_open(asset: str, market_hours: dict = None, current_time: datetime = None) -> bool:
    """
    Check if the market is open for a given asset based on Mon-Fri and defined hours,
    or 24/7 if it is a crypto asset.
    """
    if is_crypto_asset(asset):
        return True
        
    if market_hours is None:
        market_hours = get_market_hours()
        
    if not market_hours or asset not in market_hours:
        return False
        
    config = market_hours[asset]
    if config.get("is_crypto", False) or config.get("exchange") == "CRYPTO":
        return True
        
    timezone_name = config.get("timezone")
    
    if current_time is not None:
        utc_now = current_time
    else:
        utc_now = datetime.now(dt.timezone.utc)
    
    local_time = None
    if timezone_name:
        try:
            from zoneinfo import ZoneInfo
            local_time = utc_now.astimezone(ZoneInfo(timezone_name))
        except Exception:
            try:
                import pytz
                local_time = utc_now.astimezone(pytz.timezone(timezone_name))
            except Exception:
                pass
                
    if local_time is None:
        tz_offset_str = config.get("tz_offset", "+00:00")
        sign = 1 if tz_offset_str[0] == "+" else -1
        try:
            hours_offset = int(tz_offset_str[1:3])
            mins_offset = int(tz_offset_str[4:6])
            import pytz
            local_time = utc_now.astimezone(pytz.FixedOffset(sign * (hours_offset * 60 + mins_offset)))
        except Exception:
            local_time = utc_now
            
    # Check if it's weekend (Monday = 0, Sunday = 6)
    if not config.get("is_crypto", False) and config.get("exchange") != "CRYPTO":
        if local_time.weekday() >= 5:
            return False
            
    current_time_str = local_time.strftime("%H:%M")
    return config["open"] <= current_time_str <= config["close"]

