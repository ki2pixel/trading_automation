import os
import requests
from datetime import datetime
from decimal import Decimal
import pytz
import logging
from typing import Optional

logger = logging.getLogger("papertrader")

API_HOST = "marketflow-all-in-one-market-finance-api.p.rapidapi.com"
URL = f"https://{API_HOST}/v2/chart/price"

from backtest_engine.live.utils import TICKER_MAPPING, NETWORK_TIMEOUT_DEFAULT
from backtest_engine.live.connection import get_db_connection


def fetch_candles(mf_symbol, range_limit=1440):
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.error("[WarmUp] RAPIDAPI_KEY not set. Cannot proceed.")
        raise ValueError("[WarmUp] RAPIDAPI_KEY not set. Cannot proceed.")

    querystring = {"symbol": mf_symbol, "timeframe": "1", "range": str(range_limit)}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": API_HOST
    }

    try:
        response = requests.get(URL, headers=headers, params=querystring, timeout=NETWORK_TIMEOUT_DEFAULT)
        response.raise_for_status()
        data = response.json()

        candles = data.get("data", [])
        if not candles and isinstance(data, list):
            candles = data

        logger.info(f"[WarmUp] Récupéré {len(candles)} bougies pour {mf_symbol}")
        return candles

    except requests.exceptions.RequestException as e:
        logger.error(f"[WarmUp] Erreur API pour {mf_symbol} : {e}")
        return []

def get_t212_current_price(t212_ticker, conn) -> Optional[Decimal]:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT price FROM live_prices WHERE LOWER(ticker) = LOWER(%s)", (t212_ticker,))
            row = cur.fetchone()
            if row and row[0] is not None:
                return Decimal(str(row[0]))
    except Exception as e:
        logger.error(f"[WarmUp] Erreur récupération prix live pour {t212_ticker}: {e}")
    return None

def parse_and_insert(t212_ticker, candles, conn):
    live_price = get_t212_current_price(t212_ticker, conn)
    ratio = Decimal("1.0")

    if live_price and len(candles) > 0:
        for c in reversed(candles):
            last_close = Decimal(str(c.get("close", 0)))
            if last_close > 0:
                ratio = live_price / last_close
                logger.info(f"[WarmUp] Ratio d'ajustement de {ratio:.4f} appliqué pour {t212_ticker} (Live: {live_price}, API: {last_close})")
                break
    else:
        logger.info(f"[WarmUp] Aucun prix live trouvé dans la BDD pour {t212_ticker}, ratio 1.0 utilisé.")

    with conn.cursor() as cur:
        inserted = 0
        records = []
        for candle in candles:
            try:
                # Determine timestamp format (unix timestamp in seconds or ms)
                ts_val = candle.get("timestamp", candle.get("time"))
                if ts_val is None:
                    continue

                if isinstance(ts_val, (int, float)):
                    if ts_val > 1e11: # likely milliseconds
                        dt_val = datetime.fromtimestamp(ts_val / 1000.0, tz=pytz.utc)
                    else:
                        dt_val = datetime.fromtimestamp(ts_val, tz=pytz.utc)
                elif isinstance(ts_val, str):
                    dt_val = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                else:
                    continue

                open_val = Decimal(str(candle.get("open", 0))) * ratio
                high_val = Decimal(str(candle.get("high", 0))) * ratio
                low_val = Decimal(str(candle.get("low", 0))) * ratio
                close_val = Decimal(str(candle.get("close", 0))) * ratio

                if open_val == Decimal("0"):
                    continue

                records.append((t212_ticker.lower(), dt_val, open_val, high_val, low_val, close_val))
            except Exception as e:
                logger.exception(f"[WarmUp] Erreur parsing bougie {candle} pour {t212_ticker}: {e}")

        if records:
            try:
                cur.executemany("""
                    INSERT INTO live_candles_1m (ticker, timestamp_minute, open, high, low, close)
                    VALUES (%s, date_trunc('minute', %s::timestamptz), %s, %s, %s, %s)
                    ON CONFLICT (ticker, timestamp_minute)
                    DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close;
                """, records)
                inserted = len(records)
            except Exception as e:
                logger.exception(f"[WarmUp] Erreur insertion batch pour {t212_ticker}: {e}")

        conn.commit()
        logger.info(f"[WarmUp] {inserted} bougies insérées pour {t212_ticker}")

def run_warmup():
    logger.info("========================================")
    logger.info("Démarrage du Warm-Up (MarketFlow API)")
    logger.info("========================================")

    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.error("[WarmUp] RAPIDAPI_KEY not set. Cannot proceed.")
        raise ValueError("[WarmUp] RAPIDAPI_KEY not set. Cannot proceed.")

    try:
        with get_db_connection() as conn:
            for t212_ticker, mf_symbol in TICKER_MAPPING.items():
                logger.info(f"Traitement de {t212_ticker} (via {mf_symbol})...")
                candles = fetch_candles(mf_symbol, range_limit=1440)

                if candles:
                    parse_and_insert(t212_ticker, candles, conn)
    except Exception as e:
        logger.exception(f"[WarmUp] Erreur durant le warm-up : {e}")
        raise e

    logger.info("[WarmUp] Processus terminé.")

if __name__ == "__main__":
    run_warmup()
