import os
import json
import asyncio
import logging
import collections
import threading
from datetime import timezone, datetime
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import contextmanager

router = APIRouter(prefix="/api")

# Global thread-safe logs buffer
log_buffer = collections.deque(maxlen=1000)
log_lock = threading.Lock()

class DequeLogHandler(logging.Handler):
    def emit(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        with log_lock:
            log_buffer.append(entry)

# Setup Logger
logger = logging.getLogger("papertrader")
logger.setLevel(logging.INFO)
deque_handler = DequeLogHandler()
logger.addHandler(deque_handler)

@contextmanager
def get_db_connection():
    from backtest_engine.live.connection import get_db_connection as get_pooled_conn
    try:
        with get_pooled_conn() as conn:
            yield conn
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


class ConfigUpdate(BaseModel):
    initial_capital: float
    initial_capital_bucket: float
    max_capital_bucket: float
    max_entry_price: float
    is_active: bool
    indicator_params: dict | None = None


class ConfigToggle(BaseModel):
    is_active: bool


# Helper functions for threadpool execution
def _get_portfolio_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT source, cash_balance, allocated_balance, total_nav, last_updated, secured_balance FROM paper_portfolio_balance")
            rows = cur.fetchall()
            portfolio = {}
            for r in rows:
                source = r[0]
                portfolio[source] = {
                    "cash_balance": float(r[1]),
                    "allocated_balance": float(r[2]),
                    "total_nav": float(r[3]),
                    "last_updated": r[4].replace(tzinfo=timezone.utc).isoformat() if r[4] else None,
                    "secured_balance": float(r[5])
                }
            for s in ('trading212', 'bybit'):
                if s not in portfolio:
                    portfolio[s] = {"cash_balance": 0.0, "allocated_balance": 0.0, "total_nav": 0.0, "last_updated": None, "secured_balance": 0.0}
            return portfolio

def _get_positions_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, asset, strategy_name, qty, entry_price, current_price, pnl, updated_at FROM paper_positions")
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "asset": r[1], "strategy_name": r[2], "qty": float(r[3]),
                    "entry_price": float(r[4]), "current_price": float(r[5]), "pnl": float(r[6]),
                    "updated_at": r[7].replace(tzinfo=timezone.utc).isoformat() if r[7] else None
                } for r in rows
            ]

def _get_transactions_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value FROM paper_transactions ORDER BY timestamp DESC LIMIT 100")
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "timestamp": r[1].replace(tzinfo=timezone.utc).isoformat() if r[1] else None, "asset": r[2],
                    "strategy_name": r[3], "action": r[4], "qty": float(r[5]), "price": float(r[6]),
                    "total_value": float(r[7])
                } for r in rows
            ]

def _get_evaluations_sync(limit: int = 100, status: str | None = None, asset: str | None = None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, timestamp, strategy_name, asset, timeframe, price, signal_type, signal_triggered, status, fail_reason, details
                FROM paper_evaluations
            """
            conditions = []
            params = []
            
            if status:
                conditions.append("status = %s")
                params.append(status)
            if asset:
                conditions.append("asset = %s")
                params.append(asset)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1].replace(tzinfo=timezone.utc).isoformat() if r[1] else None,
                    "strategy_name": r[2],
                    "asset": r[3],
                    "timeframe": r[4],
                    "price": float(r[5]) if r[5] is not None else None,
                    "signal_type": r[6],
                    "signal_triggered": r[7],
                    "status": r[8],
                    "fail_reason": r[9],
                    "details": r[10] if r[10] else {}
                } for r in rows
            ]

MARKET_HOURS_PATH = os.path.join(
    os.path.dirname(__file__), "../../../configs/market_hours.json"
)

def load_market_hours():
    try:
        with open(MARKET_HOURS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[API] Error loading market hours: {e}")
        return {}

_market_hours = load_market_hours()

def is_market_open(asset: str) -> bool:
    if asset.lower().endswith("usdt"):
        return True
        
    if asset not in _market_hours:
        return False
        
    config = _market_hours[asset]
    timezone_name = config.get("timezone")
    
    import datetime as dt
    from datetime import datetime
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
            
    if local_time.weekday() >= 5:
        return False
        
    current_time_str = local_time.strftime("%H:%M")
    return config["open"] <= current_time_str <= config["close"]

def _get_configs_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, strategy_name, asset, timeframe, kelly_weight, 
                       initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, is_active, indicator_params, run_status, last_error
                FROM paper_strategy_configs
                ORDER BY id ASC
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "strategy_name": r[1], "asset": r[2], "timeframe": r[3],
                    "kelly_weight": float(r[4]), "initial_capital": float(r[5]),
                    "initial_capital_bucket": float(r[6]), "max_capital_bucket": float(r[7]),
                    "max_entry_price": float(r[8]), "is_active": r[9],
                    "indicator_params": r[10] if r[10] else {},
                    "status": "inactive" if not r[9] else (r[11] if r[11] else "active"),
                    "last_error": r[12],
                    "market_open": is_market_open(r[2])
                } for r in rows
            ]

def _update_config_sync(config_id: int, payload: ConfigUpdate):
    import json
    run_status = "active" if payload.is_active else "inactive"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if payload.indicator_params is not None:
                params_json = json.dumps(payload.indicator_params)
                cur.execute("""
                    UPDATE paper_strategy_configs 
                    SET initial_capital = %s, initial_capital_bucket = %s, 
                        max_capital_bucket = %s, max_entry_price = %s, is_active = %s,
                        indicator_params = %s, run_status = %s, last_error = NULL
                    WHERE id = %s
                """, (payload.initial_capital, payload.initial_capital_bucket, 
                      payload.max_capital_bucket, payload.max_entry_price, payload.is_active,
                      params_json, run_status, config_id))
            else:
                cur.execute("""
                    UPDATE paper_strategy_configs 
                    SET initial_capital = %s, initial_capital_bucket = %s, 
                        max_capital_bucket = %s, max_entry_price = %s, is_active = %s,
                        run_status = %s, last_error = NULL
                    WHERE id = %s
                """, (payload.initial_capital, payload.initial_capital_bucket, 
                      payload.max_capital_bucket, payload.max_entry_price, payload.is_active,
                      run_status, config_id))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Config not found")
            return {"status": "success", "message": "Configuration updated"}


def _get_candles_sync(ticker: str, limit: int = 1000):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp_minute, open, high, low, close 
                FROM live_candles_1m 
                WHERE LOWER(ticker) = LOWER(%s) 
                ORDER BY timestamp_minute DESC 
                LIMIT %s
            """, (ticker, limit))
            rows = cur.fetchall()
            return [
                {
                    "time": int(r[0].replace(tzinfo=timezone.utc).timestamp()),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4])
                } for r in reversed(rows)
            ]


def _get_price_feed_status_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT source, MAX(updated_at) 
                FROM live_prices 
                GROUP BY source
            """)
            rows = cur.fetchall()
            now = datetime.now(timezone.utc)
            status_map = {}
            for source, max_updated in rows:
                if not max_updated:
                    status_map[source] = {"status": "offline", "last_update": None, "seconds_ago": None}
                    continue
                if max_updated.tzinfo is None:
                    max_updated = max_updated.replace(tzinfo=timezone.utc)
                else:
                    max_updated = max_updated.astimezone(timezone.utc)
                seconds_ago = (now - max_updated).total_seconds()
                
                if seconds_ago < 30:
                    status = "fresh"
                elif seconds_ago < 120:
                    status = "stale"
                else:
                    status = "offline"
                    
                status_map[source] = {
                    "status": status,
                    "last_update": max_updated.isoformat(),
                    "seconds_ago": seconds_ago
                }
            for s in ('trading212', 'bybit'):
                if s not in status_map:
                    status_map[s] = {"status": "offline", "last_update": None, "seconds_ago": None}
            return status_map


def _panic_close_all_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, asset, strategy_name, qty, entry_price, current_price FROM paper_positions")
            positions = cur.fetchall()
            
            from backtest_engine.live.connection import get_redis_client
            redis_client = get_redis_client()
            
            closed_count = 0
            for pos_id, asset, strategy_name, qty, entry_price, current_price in positions:
                qty = Decimal(str(qty))
                entry_price = Decimal(str(entry_price))
                
                live_price = None
                if redis_client:
                    try:
                        redis_val = redis_client.get(f"price:{asset.lower()}")
                        if redis_val is not None:
                            live_price = Decimal(str(redis_val))
                    except Exception:
                        pass
                if live_price is None:
                    cur.execute("SELECT price FROM live_prices WHERE ticker = %s", (asset.lower(),))
                    price_row = cur.fetchone()
                    if price_row:
                        live_price = Decimal(str(price_row[0]))
                if live_price is None:
                    live_price = Decimal(str(current_price))
                    
                source = 'bybit' if asset.lower().endswith("usdt") else 'trading212'
                fee_rate = Decimal("0.0010") if source == 'bybit' else Decimal("0.0")
                
                actual_revenue = qty * live_price
                sell_fee = actual_revenue * fee_rate
                net_revenue = actual_revenue - sell_fee
                
                total_entry_cost = (qty * entry_price) * (Decimal("1.0") + fee_rate)
                pnl = net_revenue - total_entry_cost
                
                # Delete position
                cur.execute("DELETE FROM paper_positions WHERE id = %s", (pos_id,))
                
                # Update balance
                cur.execute("""
                    UPDATE paper_portfolio_balance 
                    SET cash_balance = cash_balance + %s,
                        allocated_balance = GREATEST(0, allocated_balance - %s),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE source = %s
                """, (net_revenue, qty * entry_price, source))
                
                # Insert transaction
                cur.execute("""
                    INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value, timestamp)
                    VALUES (%s, %s, 'SELL', %s, %s, %s, CURRENT_TIMESTAMP)
                """, (asset, strategy_name, qty, live_price, net_revenue))
                
                # Log evaluation
                details_json = json.dumps({
                    "qty": float(qty),
                    "entry_price": float(entry_price),
                    "revenue": float(net_revenue),
                    "pnl": float(pnl),
                    "exit_reason": "PANIC_CLOSE"
                })
                cur.execute("""
                    INSERT INTO paper_evaluations (strategy_name, asset, timeframe, price, signal_type, signal_triggered, status, fail_reason, details, timestamp)
                    VALUES (%s, %s, '1m', %s, 'EXIT', TRUE, 'EXECUTED', 'PANIC CLOSE ALL', %s::jsonb, CURRENT_TIMESTAMP)
                """, (strategy_name, asset, live_price, details_json))
                
                logger.warning(f"[PaperTrader] PANIC CLOSE: Sold {qty} units of {asset} @ {live_price} € (PnL: {pnl} €)")
                closed_count += 1
                
            conn.commit()
            return {"status": "success", "closed_positions_count": closed_count}


def _toggle_config_sync(config_id: int, is_active: bool):
    run_status = "active" if is_active else "inactive"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE paper_strategy_configs 
                SET is_active = %s, run_status = %s, last_error = NULL
                WHERE id = %s
            """, (is_active, run_status, config_id))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Config not found")
            return {"status": "success", "message": f"Config active status set to {is_active}"}


# Async routes delegating to the sync helpers
@router.get("/portfolio")
async def get_portfolio():
    try:
        return await asyncio.to_thread(_get_portfolio_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_positions():
    try:
        return await asyncio.to_thread(_get_positions_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def get_transactions():
    try:
        return await asyncio.to_thread(_get_transactions_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evaluations")
async def get_evaluations(limit: int = 100, status: str | None = None, asset: str | None = None):
    try:
        return await asyncio.to_thread(_get_evaluations_sync, limit, status, asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs")
async def get_configs():
    try:
        return await asyncio.to_thread(_get_configs_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/configs/{config_id}")
async def update_config(config_id: int, payload: ConfigUpdate):
    try:
        return await asyncio.to_thread(_update_config_sync, config_id, payload)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles")
async def get_candles(ticker: str, limit: int = 1000):
    try:
        return await asyncio.to_thread(_get_candles_sync, ticker, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/heartbeat")
async def get_heartbeat():
    try:
        return await asyncio.to_thread(_get_price_feed_status_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control/panic")
async def panic_close_all():
    try:
        return await asyncio.to_thread(_panic_close_all_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configs/{config_id}/toggle")
async def toggle_config(config_id: int, payload: ConfigToggle):
    try:
        return await asyncio.to_thread(_toggle_config_sync, config_id, payload.is_active)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stream")
async def stream_logs():
    async def log_generator():
        # Send up to the last 100 logs from buffer for immediate context on connect
        last_sent_idx = 0
        with log_lock:
            history_start = max(0, len(log_buffer) - 100)
            buffered_logs = list(log_buffer)[history_start:]
            last_sent_idx = history_start + len(buffered_logs)
            
        for log in buffered_logs:
            yield f"data: {json.dumps(log)}\n\n"
            
        while True:
            await asyncio.sleep(0.5)
            new_logs = []
            with log_lock:
                current_len = len(log_buffer)
                if current_len > last_sent_idx:
                    start_idx = current_len - (current_len - last_sent_idx)
                    if start_idx < 0:
                        start_idx = 0
                    new_logs = list(log_buffer)[start_idx:]
                    last_sent_idx = current_len
            for log in new_logs:
                yield f"data: {json.dumps(log)}\n\n"
                
    return StreamingResponse(log_generator(), media_type="text/event-stream")
