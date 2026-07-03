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
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Any
from backtest_engine.live.utils import is_crypto_asset

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


async def _get_pool():
    """Get the asyncpg pool. Raises HTTPException if unavailable."""
    from backtest_engine.live.connection import get_async_pool
    try:
        return await get_async_pool()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


class IndicatorParamsModel(BaseModel):
    """
    Validated indicator parameters for paper trading strategy configs.

    Common engine keys are typed explicitly. Strategy-specific keys
    from overrides_from_mapping_function are allowed via extra='allow'
    but all values must be primitive types (no nested dicts/lists).
    """
    model_config = ConfigDict(extra='allow')

    # Precision & currency keys (used directly by engine.py)
    quantity_precision: int | None = None
    account_currency: str | None = None
    asset_currency: str | None = None
    point_value: float | None = None

    # Bracket exit keys
    use_net_bracket_exits: bool | None = None
    enable_stop_loss: bool | None = None
    enable_take_profit: bool | None = None
    take_profit_pct: float | None = None
    stop_loss_pct: float | None = None
    take_profit_net_percent: float | None = None
    stop_loss_net_percent: float | None = None

    # Trailing stop keys
    enable_trailing_stop: bool | None = None
    trail_profit_pct: float | None = None
    trail_loss_pct: float | None = None

    # Safety stop keys
    use_safety_stop: bool | None = None
    safety_stop_applies_to: str | None = None
    safety_stop_mode: str | None = None
    safety_max_net_loss_mode: str | None = None
    safety_max_net_loss_cash: float | None = None
    safety_max_net_loss_percent: float | None = None
    safety_max_bars_in_trade: int | None = None

    @model_validator(mode='before')
    @classmethod
    def validate_primitive_types(cls, data: Any) -> Any:
        """Reject nested dicts/lists in any input fields to prevent injection."""
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    raise ValueError(
                        f"Nested structures are not allowed in indicator_params (key: {k}), got {type(v).__name__}"
                    )
        return data


class ConfigUpdate(BaseModel):
    initial_capital: float
    initial_capital_bucket: float
    max_capital_bucket: float
    max_entry_price: float
    is_active: bool
    indicator_params: IndicatorParamsModel | None = None


class ConfigToggle(BaseModel):
    is_active: bool


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

from backtest_engine.live.utils import is_market_open as _utils_is_market_open

def is_market_open(asset: str) -> bool:
    return _utils_is_market_open(asset, _market_hours)


# ─── Async API Endpoints (asyncpg) ───────────────────────────────────────────

@router.get("/portfolio")
async def get_portfolio():
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT source, cash_balance, allocated_balance, total_nav, last_updated, secured_balance "
                "FROM paper_portfolio_balance"
            )
            portfolio = {}
            for r in rows:
                source = r["source"]
                portfolio[source] = {
                    "cash_balance": float(r["cash_balance"]),
                    "allocated_balance": float(r["allocated_balance"]),
                    "total_nav": float(r["total_nav"]),
                    "last_updated": r["last_updated"].replace(tzinfo=timezone.utc).isoformat() if r["last_updated"] else None,
                    "secured_balance": float(r["secured_balance"]),
                }
            for s in ('trading212', 'bybit'):
                if s not in portfolio:
                    portfolio[s] = {"cash_balance": 0.0, "allocated_balance": 0.0, "total_nav": 0.0, "last_updated": None, "secured_balance": 0.0}
            return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/positions")
async def get_positions():
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, asset, strategy_name, qty, entry_price, current_price, pnl, updated_at "
                "FROM paper_positions"
            )
            return [
                {
                    "id": r["id"], "asset": r["asset"], "strategy_name": r["strategy_name"],
                    "qty": float(r["qty"]), "entry_price": float(r["entry_price"]),
                    "current_price": float(r["current_price"]), "pnl": float(r["pnl"]),
                    "updated_at": r["updated_at"].replace(tzinfo=timezone.utc).isoformat() if r["updated_at"] else None,
                } for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/transactions")
async def get_transactions():
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
                "FROM paper_transactions ORDER BY timestamp DESC LIMIT 100"
            )
            return [
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"].replace(tzinfo=timezone.utc).isoformat() if r["timestamp"] else None,
                    "asset": r["asset"], "strategy_name": r["strategy_name"],
                    "action": r["action"], "qty": float(r["qty"]),
                    "price": float(r["price"]), "total_value": float(r["total_value"]),
                } for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/evaluations")
async def get_evaluations(limit: int = 100, status: str | None = None, asset: str | None = None):
    pool = await _get_pool()
    try:
        limit = min(max(1, limit), 10000)

        query = (
            "SELECT id, timestamp, strategy_name, asset, timeframe, price, "
            "signal_type, signal_triggered, status, fail_reason, details "
            "FROM paper_evaluations"
        )
        conditions = []
        params = []
        param_idx = 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        if asset:
            conditions.append(f"asset = ${param_idx}")
            params.append(asset)
            param_idx += 1

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY timestamp DESC LIMIT ${param_idx}"
        params.append(limit)

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"].replace(tzinfo=timezone.utc).isoformat() if r["timestamp"] else None,
                    "strategy_name": r["strategy_name"],
                    "asset": r["asset"],
                    "timeframe": r["timeframe"],
                    "price": float(r["price"]) if r["price"] is not None else None,
                    "signal_type": r["signal_type"],
                    "signal_triggered": r["signal_triggered"],
                    "status": r["status"],
                    "fail_reason": r["fail_reason"],
                    "details": json.loads(r["details"]) if isinstance(r["details"], str) else (r["details"] if r["details"] else {}),
                } for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/configs")
async def get_configs():
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, strategy_name, asset, timeframe, kelly_weight, "
                "initial_capital, initial_capital_bucket, max_capital_bucket, "
                "max_entry_price, is_active, indicator_params, run_status, last_error "
                "FROM paper_strategy_configs ORDER BY id ASC"
            )
            result = []
            for r in rows:
                indicator_params = r["indicator_params"]
                # asyncpg returns JSONB as Python dict/list directly
                if isinstance(indicator_params, str):
                    indicator_params = json.loads(indicator_params)
                elif indicator_params is None:
                    indicator_params = {}

                result.append({
                    "id": r["id"], "strategy_name": r["strategy_name"],
                    "asset": r["asset"], "timeframe": r["timeframe"],
                    "kelly_weight": float(r["kelly_weight"]),
                    "initial_capital": float(r["initial_capital"]),
                    "initial_capital_bucket": float(r["initial_capital_bucket"]),
                    "max_capital_bucket": float(r["max_capital_bucket"]),
                    "max_entry_price": float(r["max_entry_price"]),
                    "is_active": r["is_active"],
                    "indicator_params": indicator_params,
                    "status": "inactive" if not r["is_active"] else (r["run_status"] if r["run_status"] else "active"),
                    "last_error": r["last_error"],
                    "market_open": is_market_open(r["asset"]),
                })
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.put("/configs/{config_id}")
async def update_config(config_id: int, payload: ConfigUpdate):
    pool = await _get_pool()
    try:
        run_status = "active" if payload.is_active else "inactive"
        async with pool.acquire() as conn:
            if payload.indicator_params is not None:
                params_json = json.dumps(payload.indicator_params.model_dump(exclude_none=True))
                result = await conn.execute(
                    "UPDATE paper_strategy_configs "
                    "SET initial_capital = $1, initial_capital_bucket = $2, "
                    "    max_capital_bucket = $3, max_entry_price = $4, is_active = $5, "
                    "    indicator_params = $6, run_status = $7, last_error = NULL "
                    "WHERE id = $8",
                    payload.initial_capital, payload.initial_capital_bucket,
                    payload.max_capital_bucket, payload.max_entry_price, payload.is_active,
                    params_json, run_status, config_id,
                )
            else:
                result = await conn.execute(
                    "UPDATE paper_strategy_configs "
                    "SET initial_capital = $1, initial_capital_bucket = $2, "
                    "    max_capital_bucket = $3, max_entry_price = $4, is_active = $5, "
                    "    run_status = $6, last_error = NULL "
                    "WHERE id = $7",
                    payload.initial_capital, payload.initial_capital_bucket,
                    payload.max_capital_bucket, payload.max_entry_price, payload.is_active,
                    run_status, config_id,
                )
            # asyncpg execute returns status string like "UPDATE 1"
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Config not found")
            return {"status": "success", "message": "Configuration updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/candles")
async def get_candles(ticker: str, limit: int = 1000):
    pool = await _get_pool()
    try:
        limit = min(max(1, limit), 10000)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT timestamp_minute, open, high, low, close "
                "FROM live_candles_1m "
                "WHERE LOWER(ticker) = LOWER($1) "
                "ORDER BY timestamp_minute DESC "
                "LIMIT $2",
                ticker, limit,
            )
            return [
                {
                    "time": int(r["timestamp_minute"].replace(tzinfo=timezone.utc).timestamp()),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                } for r in reversed(rows)
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/status/heartbeat")
async def get_heartbeat():
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT source, MAX(updated_at) AS max_updated "
                "FROM live_prices GROUP BY source"
            )
            now = datetime.now(timezone.utc)
            status_map = {}
            for r in rows:
                source = r["source"]
                max_updated = r["max_updated"]
                if not max_updated:
                    status_map[source] = {"status": "offline", "last_update": None, "seconds_ago": None}
                    continue
                if max_updated.tzinfo is None:
                    max_updated = max_updated.replace(tzinfo=timezone.utc)
                else:
                    max_updated = max_updated.astimezone(timezone.utc)
                seconds_ago = (now - max_updated).total_seconds()

                if seconds_ago < 30:
                    feed_status = "fresh"
                elif seconds_ago < 120:
                    feed_status = "stale"
                else:
                    feed_status = "offline"

                status_map[source] = {
                    "status": feed_status,
                    "last_update": max_updated.isoformat(),
                    "seconds_ago": seconds_ago,
                }
            for s in ('trading212', 'bybit'):
                if s not in status_map:
                    status_map[s] = {"status": "offline", "last_update": None, "seconds_ago": None}
            return status_map
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.post("/control/panic")
async def panic_close_all():
    pool = await _get_pool()
    try:
        from backtest_engine.live.connection import get_redis_client
        redis_client = get_redis_client()

        async with pool.acquire() as conn:
            async with conn.transaction():
                positions = await conn.fetch(
                    "SELECT id, asset, strategy_name, qty, entry_price, current_price FROM paper_positions"
                )

                closed_count = 0
                for pos in positions:
                    pos_id = pos["id"]
                    asset = pos["asset"]
                    strategy_name = pos["strategy_name"]
                    qty = Decimal(str(pos["qty"]))
                    entry_price = Decimal(str(pos["entry_price"]))

                    # Get live price from Redis → DB → fallback
                    live_price = None
                    if redis_client:
                        try:
                            redis_val = redis_client.get(f"price:{asset.lower()}")
                            if redis_val is not None:
                                live_price = Decimal(str(redis_val))
                        except Exception:
                            pass
                    if live_price is None:
                        price_row = await conn.fetchrow(
                            "SELECT price FROM live_prices WHERE ticker = $1",
                            asset.lower(),
                        )
                        if price_row:
                            live_price = Decimal(str(price_row["price"]))
                    if live_price is None:
                        live_price = Decimal(str(pos["current_price"]))

                    source = 'bybit' if is_crypto_asset(asset) else 'trading212'
                    fee_rate = Decimal("0.0010") if source == 'bybit' else Decimal("0.0")

                    actual_revenue = qty * live_price
                    sell_fee = actual_revenue * fee_rate
                    net_revenue = actual_revenue - sell_fee

                    total_entry_cost = (qty * entry_price) * (Decimal("1.0") + fee_rate)
                    pnl = net_revenue - total_entry_cost

                    # Delete position
                    await conn.execute("DELETE FROM paper_positions WHERE id = $1", pos_id)

                    # Update balance
                    await conn.execute(
                        "UPDATE paper_portfolio_balance "
                        "SET cash_balance = cash_balance + $1, "
                        "    allocated_balance = GREATEST(0, allocated_balance - $2), "
                        "    last_updated = CURRENT_TIMESTAMP "
                        "WHERE source = $3",
                        net_revenue, qty * entry_price, source,
                    )

                    # Insert transaction
                    await conn.execute(
                        "INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value, timestamp) "
                        "VALUES ($1, $2, 'SELL', $3, $4, $5, CURRENT_TIMESTAMP)",
                        asset, strategy_name, qty, live_price, net_revenue,
                    )

                    # Log evaluation
                    details_json = json.dumps({
                        "qty": float(qty),
                        "entry_price": float(entry_price),
                        "revenue": float(net_revenue),
                        "pnl": float(pnl),
                        "exit_reason": "PANIC_CLOSE",
                    })
                    await conn.execute(
                        "INSERT INTO paper_evaluations "
                        "(strategy_name, asset, timeframe, price, signal_type, signal_triggered, status, fail_reason, details, timestamp) "
                        "VALUES ($1, $2, '1m', $3, 'EXIT', TRUE, 'EXECUTED', 'PANIC CLOSE ALL', $4::jsonb, CURRENT_TIMESTAMP)",
                        strategy_name, asset, live_price, details_json,
                    )

                    logger.warning(f"[PaperTrader] PANIC CLOSE: Sold {qty} units of {asset} @ {live_price} € (PnL: {pnl} €)")
                    closed_count += 1

            return {"status": "success", "closed_positions_count": closed_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.put("/configs/{config_id}/toggle")
async def toggle_config(config_id: int, payload: ConfigToggle):
    pool = await _get_pool()
    try:
        run_status = "active" if payload.is_active else "inactive"
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE paper_strategy_configs "
                "SET is_active = $1, run_status = $2, last_error = NULL "
                "WHERE id = $3",
                payload.is_active, run_status, config_id,
            )
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Config not found")
            return {"status": "success", "message": f"Config active status set to {payload.is_active}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


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
