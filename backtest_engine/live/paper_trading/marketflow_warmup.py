import os
import requests
import psycopg2
from datetime import datetime, timedelta
import pytz

# RapidAPI configuration
API_KEY = os.getenv("RAPIDAPI_KEY", "62fd8a4295msh8bb906bd3512057p1c112cjsn626a14c8fcd7")
API_HOST = "marketflow-all-in-one-market-finance-api.p.rapidapi.com"
URL = f"https://{API_HOST}/v2/chart/price"

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

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[WarmUp] DATABASE_URL non définie. Impossible de se connecter.")
        return None
    return psycopg2.connect(db_url)

def fetch_candles(mf_symbol, range_limit=1440):
    querystring = {"symbol": mf_symbol, "timeframe": "1", "range": str(range_limit)}
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }
    
    try:
        response = requests.get(URL, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # The exact response schema depends on the API, usually it's an array of objects or an object with 'data'
        # Assuming typical OHLCV response from MarketFlow v2
        # If response structure is known, adjust here. 
        # Typically: {"data": [{"timestamp": 1234567890, "open": 100, "high": 105, "low": 95, "close": 102}, ...]}
        # Or array of arrays: [[timestamp, open, high, low, close, volume], ...]
        # We will parse the array assuming it's in data
        
        candles = data.get("data", [])
        if not candles and isinstance(data, list):
            candles = data
            
        print(f"[WarmUp] Récupéré {len(candles)} bougies pour {mf_symbol}")
        return candles
        
    except requests.exceptions.RequestException as e:
        print(f"[WarmUp] Erreur API pour {mf_symbol} : {e}")
        return []

def get_t212_current_price(t212_ticker, conn):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT price FROM trading212_prices WHERE ticker = %s", (t212_ticker,))
            row = cur.fetchone()
            if row:
                return float(row[0])
    except Exception as e:
        print(f"[WarmUp] Erreur récupération prix live pour {t212_ticker}: {e}")
    return None

def parse_and_insert(t212_ticker, candles, conn):
    live_price = get_t212_current_price(t212_ticker, conn)
    ratio = 1.0
    
    if live_price and len(candles) > 0:
        for c in reversed(candles):
            last_close = float(c.get("close", 0))
            if last_close > 0:
                ratio = live_price / last_close
                print(f"[WarmUp] Ratio d'ajustement de {ratio:.4f} pour {t212_ticker} (Live: {live_price}, API: {last_close})")
                break

    with conn.cursor() as cur:
        inserted = 0
        for candle in candles:
            try:
                # Determine timestamp format (unix timestamp in seconds or ms)
                ts_val = candle.get("timestamp", candle.get("time"))
                if ts_val is None:
                    continue
                    
                if isinstance(ts_val, (int, float)):
                    if ts_val > 1e11: # likely milliseconds
                        dt = datetime.fromtimestamp(ts_val / 1000.0, tz=pytz.utc)
                    else:
                        dt = datetime.fromtimestamp(ts_val, tz=pytz.utc)
                elif isinstance(ts_val, str):
                    dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                else:
                    continue
                
                open_val = float(candle.get("open", 0)) * ratio
                high_val = float(candle.get("high", 0)) * ratio
                low_val = float(candle.get("low", 0)) * ratio
                close_val = float(candle.get("close", 0)) * ratio
                
                if open_val == 0:
                    continue

                cur.execute("""
                    INSERT INTO trading212_candles_1m (ticker, timestamp_minute, open, high, low, close)
                    VALUES (%s, date_trunc('minute', %s::timestamptz), %s, %s, %s, %s)
                    ON CONFLICT (ticker, timestamp_minute) 
                    DO UPDATE SET 
                        open = EXCLUDED.open, 
                        high = EXCLUDED.high, 
                        low = EXCLUDED.low, 
                        close = EXCLUDED.close;
                """, (t212_ticker, dt, open_val, high_val, low_val, close_val))
                
                inserted += 1
            except Exception as e:
                # print(f"Erreur parsing bougie {candle}: {e}")
                pass
                
        conn.commit()
        print(f"[WarmUp] {inserted} bougies insérées pour {t212_ticker}")

def run_warmup():
    print("========================================")
    print("Démarrage du Warm-Up (MarketFlow API)")
    print("========================================")
    
    conn = get_db_connection()
    if not conn:
        return
        
    for t212_ticker, mf_symbol in TICKER_MAPPING.items():
        print(f"\nTraitement de {t212_ticker} (via {mf_symbol})...")
        candles = fetch_candles(mf_symbol, range_limit=1440)
        
        if candles:
            parse_and_insert(t212_ticker, candles, conn)
            
    conn.close()
    print("\n[WarmUp] Processus terminé.")

if __name__ == "__main__":
    run_warmup()
