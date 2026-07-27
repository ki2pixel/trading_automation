import os
import json
import asyncio
import logging
import collections
import threading
import secrets
import time
import hmac
import hashlib
import uuid
from datetime import timezone, datetime
from decimal import Decimal
import asyncpg
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, model_validator, Field
from typing import Any
from backtest_engine.live.utils import is_crypto_asset

router = APIRouter(prefix="/api")


REDIS_CACHE_TIMEOUT = 0.5  # 500ms for cache get/set operations

def _is_production() -> bool:
    """Q3-FIX: Centralized production detection supporting both RENDER and ENVIRONMENT."""
    return (
        os.getenv("ENVIRONMENT", "").lower() == "production"
        or os.getenv("RENDER") is not None
    )

# Global thread-safe logs buffer with monotonic sequence counter (PT-09)
log_buffer = collections.deque(maxlen=1000)
log_lock = threading.Lock()
_log_seq_counter = 0
_log_seq_lock = threading.Lock()

class DequeLogHandler(logging.Handler):
    def emit(self, record):
        global _log_seq_counter
        with _log_seq_lock:
            _log_seq_counter += 1
            seq = _log_seq_counter
        entry = {
            "seq": seq,
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

    # Execution guard keys (EX-07)
    max_entry_price_buffer_pct: float | None = None   # default 0.30
    min_holding_bars: int | None = None               # default 3; 0 = MHP disabled
    atr_gate_enabled: bool | None = None              # default True
    atr_gate_length: int | None = None                # default 14
    atr_gate_lookback: int | None = None              # default 100
    atr_gate_percentile: float | None = None          # default 25.0
    atr_gate_min_bars: int | None = None              # default 20

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
    initial_capital: float = Field(gt=0)
    initial_capital_bucket: float = Field(gt=0)
    max_capital_bucket: float = Field(gt=0)
    max_entry_price: float = Field(gt=0)
    is_active: bool
    indicator_params: IndicatorParamsModel | None = None

    @model_validator(mode='after')
    def validate_bucket_ordering(self):
        if self.initial_capital_bucket > self.max_capital_bucket:
            raise ValueError("initial_capital_bucket must not exceed max_capital_bucket")
        return self


class ConfigToggle(BaseModel):
    is_active: bool


MARKET_HOURS_PATH = os.path.join(
    os.path.dirname(__file__), "../../../configs/market_hours.json"
)

def load_market_hours():
    try:
        with open(MARKET_HOURS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        logger.exception("[API] Error loading market hours")
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
                "SELECT source, paper_cash_balance, allocated_balance, total_nav, last_updated, secured_balance "
                "FROM paper_portfolio_balance"
            )
            portfolio = {}
            for r in rows:
                source = r["source"]
                portfolio[source] = {
                    "cash_balance": float(r["paper_cash_balance"]),
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
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching portfolio")
        raise


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
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching positions")
        raise


@router.get("/transactions")
async def get_transactions(limit: int = 50, offset: int = 0, cursor_timestamp: str | None = None, cursor_id: int | None = None, asset: str | None = None):
    pool = await _get_pool()
    try:
        limit = min(max(1, limit), 10000)
        offset = max(0, offset)
        cursor_dt = None
        if cursor_timestamp and cursor_id is not None:
            try:
                dt_str = cursor_timestamp
                if dt_str.endswith("Z"):
                    dt_str = dt_str[:-1] + "+00:00"
                cursor_dt = datetime.fromisoformat(dt_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid cursor_timestamp format")

        async with pool.acquire() as conn:
            if cursor_dt is not None and cursor_id is not None:
                if asset:
                    rows = await conn.fetch(
                        "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
                        "FROM paper_transactions WHERE (timestamp, id) < ($1, $2) AND LOWER(asset) = LOWER($3) ORDER BY timestamp DESC, id DESC LIMIT $4",
                        cursor_dt, cursor_id, asset, limit
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
                        "FROM paper_transactions WHERE (timestamp, id) < ($1, $2) ORDER BY timestamp DESC, id DESC LIMIT $3",
                        cursor_dt, cursor_id, limit
                    )
            else:
                if asset:
                    rows = await conn.fetch(
                        "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
                        "FROM paper_transactions WHERE LOWER(asset) = LOWER($1) ORDER BY timestamp DESC, id DESC LIMIT $2 OFFSET $3",
                        asset, limit, offset
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
                        "FROM paper_transactions ORDER BY timestamp DESC, id DESC LIMIT $1 OFFSET $2",
                        limit, offset
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
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching transactions")
        raise


@router.get("/evaluations")
async def get_evaluations(limit: int = 100, offset: int = 0, status: str | None = None, asset: str | None = None,
                          cursor_timestamp: str | None = None, cursor_id: int | None = None):
    pool = await _get_pool()
    try:
        limit = min(max(1, limit), 10000)
        offset = max(0, offset)
        cursor_dt = None
        if cursor_timestamp and cursor_id is not None:
            try:
                dt_str = cursor_timestamp
                if dt_str.endswith("Z"):
                    dt_str = dt_str[:-1] + "+00:00"
                cursor_dt = datetime.fromisoformat(dt_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid cursor_timestamp format")

        query = (
            "SELECT id, timestamp, strategy_name, asset, timeframe, price, "
            "signal_type, signal_triggered, status, fail_reason, details "
            "FROM paper_evaluations"
        )
        conditions = []
        params = []
        param_idx = 1

        # Composite cursor takes precedence over offset
        if cursor_dt is not None and cursor_id is not None:
            conditions.append(f"(timestamp, id) < (${param_idx}, ${param_idx + 1})")
            params.extend([cursor_dt, cursor_id])
            param_idx += 2

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

        if cursor_dt is not None and cursor_id is not None:
            query += f" ORDER BY timestamp DESC, id DESC LIMIT ${param_idx}"
            params.append(limit)
        else:
            query += f" ORDER BY timestamp DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.append(limit)
            params.append(offset)

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
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching evaluations")
        raise


@router.get("/configs")
async def get_configs():
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, strategy_name, asset, timeframe, kelly_weight, "
                "initial_capital, initial_capital_bucket, max_capital_bucket, "
                "max_entry_price, is_active, indicator_params, run_status, last_error, warmup_progress "
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
                    "warmup_progress": json.loads(r["warmup_progress"]) if isinstance(r["warmup_progress"], str) else r["warmup_progress"],
                    "market_open": is_market_open(r["asset"]),
                })
            return result
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching configs")
        raise


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
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error updating config")
        raise


@router.get("/candles")
async def get_candles(ticker: str, limit: int = 1000):
    from backtest_engine.live.connection import get_async_redis_client
    redis_client = None
    try:
        redis_client = get_async_redis_client()
    except Exception as e:
        logger.warning("[API] /candles: Redis client init failed: %s", e)

    limit = min(max(1, limit), 10000)
    cache_key = f"candles:{ticker.lower()}:{limit}"

    if redis_client:
        try:
            cached = await asyncio.wait_for(redis_client.get(cache_key), timeout=REDIS_CACHE_TIMEOUT)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug("[API] /candles: Redis cache read failed: %s", e)

    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT timestamp_minute, open, high, low, close "
                "FROM live_candles_1m "
                "WHERE LOWER(ticker) = LOWER($1) "
                "ORDER BY timestamp_minute DESC "
                "LIMIT $2",
                ticker, limit,
            )
            result = [
                {
                    "time": int(r["timestamp_minute"].replace(tzinfo=timezone.utc).timestamp()),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                } for r in reversed(rows)
            ]

            if redis_client and result:
                try:
                    await asyncio.wait_for(redis_client.setex(cache_key, 20, json.dumps(result)), timeout=REDIS_CACHE_TIMEOUT)
                except Exception as e:
                    logger.debug("[API] /candles: Redis cache write failed: %s", e)
                    
            return result
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching candles")
        raise


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
            last_price = None

            for r in rows:
                source = r["source"]
                max_updated = r["max_updated"]
                if not max_updated:
                    status_map[source] = {"status": "offline", "last_update": None, "seconds_ago": None}
                    continue
                
                if not last_price or max_updated > last_price:
                    last_price = max_updated

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

            # Fetch max timestamp from paper_transactions and paper_evaluations
            tx_row = await conn.fetchrow("SELECT MAX(timestamp) FROM paper_transactions")
            eval_row = await conn.fetchrow("SELECT MAX(timestamp) FROM paper_evaluations")
            
            last_tx = tx_row[0] if tx_row else None
            last_eval = eval_row[0] if eval_row else None
            
            # Format outputs
            last_tx_str = last_tx.replace(tzinfo=timezone.utc).isoformat() if last_tx else None
            last_eval_str = last_eval.replace(tzinfo=timezone.utc).isoformat() if last_eval else None
            
            if last_price:
                if last_price.tzinfo is None:
                    last_price = last_price.replace(tzinfo=timezone.utc)
                else:
                    last_price = last_price.astimezone(timezone.utc)
                last_price_str = last_price.isoformat()
            else:
                last_price_str = None
                
            status_map["last_transaction_time"] = last_tx_str
            status_map["last_evaluation_time"] = last_eval_str
            status_map["last_price_time"] = last_price_str

            return status_map
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error fetching heartbeat")
        raise
@router.get("/status/kill-switch")
async def get_kill_switch_state():
    from backtest_engine.live.kill_switch import get_kill_switch_status_async

    status = await get_kill_switch_status_async()
    return status.as_dict()


@router.post("/control/panic")
async def panic_close_all(request: Request):
    from backtest_engine.live.kill_switch import KillSwitchStateError, suspend_trading

    try:
        kill_switch_status = await suspend_trading(
            "Dashboard panic liquidation",
            "dashboard",
        )
    except KillSwitchStateError as exc:
        logger.exception("[API] Failed to synchronize panic suspension")
        raise HTTPException(
            status_code=503,
            detail="Unable to synchronize the Kill Switch state. Trading remains suspended.",
        ) from exc

    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Q2-FIX: Prevent indefinite lock wait on FOR UPDATE
                await conn.execute("SET LOCAL lock_timeout = '5000'")
                # 1. Lock all balance rows first (consistent with signal_executor lock ordering)
                await conn.execute("SELECT 1 FROM paper_portfolio_balance WHERE source = 'trading212' FOR UPDATE")
                await conn.execute("SELECT 1 FROM paper_portfolio_balance WHERE source = 'bybit' FOR UPDATE")

                # 2. Fetch positions with FOR UPDATE lock to prevent concurrent modifications
                positions = await conn.fetch(
                    "SELECT id, asset, strategy_name, qty, entry_price, current_price FROM paper_positions FOR UPDATE"
                )
                if not positions:
                    return {"status": "success", "closed_positions_count": 0, "kill_switch": kill_switch_status.as_dict()}

                # PT-10: Batch price lookup — single query instead of N+1 per position
                assets_lower = [pos["asset"].lower() for pos in positions]
                price_rows = await conn.fetch(
                    "SELECT ticker, price FROM live_prices WHERE LOWER(ticker) = ANY($1::text[])",
                    assets_lower,
                )
                price_map = {r["ticker"].lower(): Decimal(str(r["price"])) for r in price_rows if r["price"] is not None}

                closed_count = 0
                for pos in positions:
                    pos_id = pos["id"]
                    asset = pos["asset"]
                    strategy_name = pos["strategy_name"]
                    qty = Decimal(str(pos["qty"]))
                    entry_price = Decimal(str(pos["entry_price"]))

                    # Resolve price from batched lookup, fallback to position's stored price
                    live_price = price_map.get(asset.lower(), Decimal(str(pos["current_price"])))

                    source = 'bybit' if is_crypto_asset(asset) else 'trading212'
                    fee_rate = Decimal("0.0010") if source == 'bybit' else Decimal("0.0")

                    actual_revenue = qty * live_price
                    sell_fee = actual_revenue * fee_rate
                    net_revenue = actual_revenue - sell_fee

                    total_entry_cost = (qty * entry_price) * (Decimal("1.0") + fee_rate)
                    pnl = net_revenue - total_entry_cost

                    # 3. Delete position using RETURNING to verify we actually deleted it
                    deleted_pos = await conn.fetchrow(
                        "DELETE FROM paper_positions WHERE id = $1 RETURNING id",
                        pos_id
                    )
                    if not deleted_pos:
                        logger.warning(f"[PaperTrader] Position {pos_id} already closed/deleted by concurrent task. Skipping balance credit.")
                        continue

                    # 4. Update balance — PT-10: align with SELL standard: credit secured_balance for Bybit profits
                    if pnl > 0 and source == 'bybit':
                        # Query EUR/USD rate directly via asyncpg (sync get_eurusd_rate uses psycopg2)
                        eur_row = await conn.fetchrow("SELECT price FROM live_prices WHERE ticker = 'eurusd'")
                        eurusd_rate = Decimal(str(eur_row["price"])) if eur_row and eur_row["price"] else Decimal("1.08")
                        pnl_eur = pnl / eurusd_rate
                        await conn.execute(
                            "UPDATE paper_portfolio_balance "
                            "SET paper_cash_balance = paper_cash_balance + $1, "
                            "    secured_balance = secured_balance + $2, "
                            "    allocated_balance = GREATEST(0, allocated_balance - $3), "
                            "    last_updated = CURRENT_TIMESTAMP "
                            "WHERE source = $4",
                            total_entry_cost, pnl_eur, qty * entry_price, source,
                        )
                    else:
                        await conn.execute(
                            "UPDATE paper_portfolio_balance "
                            "SET paper_cash_balance = paper_cash_balance + $1, "
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

            # Invalidate perf_metrics cache for all closed assets (best-effort, outside DB txn)
            if closed_count > 0:
                try:
                    from backtest_engine.live.connection import get_async_redis_client
                    redis_client = get_async_redis_client()
                    if redis_client:
                        closed_assets = [pos["asset"] for pos in positions]
                        for asset in closed_assets:
                            try:
                                await asyncio.wait_for(
                                    redis_client.delete(f"perf_metrics:{asset.lower()}"),
                                    timeout=0.5,
                                )
                            except Exception as e:
                                logger.debug("[API] /panic: cache invalidation failed for %s: %s", asset, e)
                except Exception as e:
                    logger.debug("[API] /panic: Redis unavailable for cache invalidation: %s", e)

            return {
                "status": "success",
                "closed_positions_count": closed_count,
                "kill_switch": kill_switch_status.as_dict(),
            }
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error executing panic close all")
        raise


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
    except asyncpg.PostgresError as e:
        logger.exception("[API] Database error toggling config")
        raise


@router.get("/logs/stream")
async def stream_logs(request: Request):
    async def log_generator():
        # Send up to the last 100 logs from buffer for immediate context on connect
        last_sent_seq = 0
        with log_lock:
            buffered_logs = list(log_buffer)[-100:]
            if buffered_logs:
                last_sent_seq = buffered_logs[-1]["seq"]
            
        for log in buffered_logs:
            yield f"data: {json.dumps(log)}\n\n"
            
        while True:
            if await request.is_disconnected():
                logger.info("[API] Client disconnected from log stream. Stopping generator.")
                break
            await asyncio.sleep(0.5)
            new_logs = []
            with log_lock:
                # PT-09: Use monotonic seq counter instead of index-based tracking.
                # Index-based tracking breaks once deque(maxlen=1000) wraps around.
                for entry in log_buffer:
                    if entry["seq"] > last_sent_seq:
                        new_logs.append(entry)
                        last_sent_seq = entry["seq"]
            for log in new_logs:
                yield f"data: {json.dumps(log)}\n\n"
                
    return StreamingResponse(log_generator(), media_type="text/event-stream")


@router.get("/performance/metrics")
async def get_performance_metrics(ticker: str):
    from backtest_engine.live.connection import get_async_redis_client
    redis_client = None
    try:
        redis_client = get_async_redis_client()
    except Exception as e:
        logger.warning("[API] /performance/metrics: Redis client init failed: %s", e)


    # 1. Cache lookup
    if redis_client:
        try:
            cached = await asyncio.wait_for(redis_client.get(f"perf_metrics:{ticker.lower()}"), timeout=REDIS_CACHE_TIMEOUT)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug("[API] /performance/metrics: Redis cache read failed: %s", e)
            
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            # 1. Fetch configs to read initial capital
            config_row = await conn.fetchrow(
                "SELECT initial_capital FROM paper_strategy_configs WHERE LOWER(asset) = LOWER($1)",
                ticker
            )
            initial_capital = float(config_row["initial_capital"]) if config_row else 1000.0
            
            # 2. Fetch candles (limit 5000 to have a complete picture)
            candle_rows = await conn.fetch(
                "SELECT timestamp_minute, open, high, low, close "
                "FROM live_candles_1m "
                "WHERE LOWER(ticker) = LOWER($1) "
                "ORDER BY timestamp_minute DESC "
                "LIMIT 5000",
                ticker
            )
            candles = [
                {
                    "time": int(r["timestamp_minute"].replace(tzinfo=timezone.utc).timestamp()),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                } for r in reversed(candle_rows)
            ]
            
            if not candles:
                return {
                    "win_rate": 0.0,
                    "profit_factor": 1.0,
                    "max_drawdown": 0.0,
                    "current_drawdown": 0.0,
                    "net_profit": 0.0,
                    "total_trades": 0,
                    "strategy_curve": [],
                    "buy_hold_curve": []
                }
                
            # 3. Fetch Transactions matching this asset
            tx_rows = await conn.fetch(
                "SELECT timestamp, action, qty, price, total_value "
                "FROM paper_transactions "
                "WHERE LOWER(asset) = LOWER($1) "
                "ORDER BY timestamp ASC",
                ticker
            )
            
            txs = [
                {
                    "timestamp_ms": r["timestamp"].replace(tzinfo=timezone.utc).timestamp() * 1000,
                    "action": r["action"],
                    "qty": float(r["qty"]),
                    "price": float(r["price"]),
                    "total_value": float(r["total_value"])
                } for r in tx_rows
            ]
            
        # 2. Cache miss -> compute in thread pool (non-blocking)
        result = await asyncio.to_thread(
            _compute_performance_metrics_sync, initial_capital, candles, txs
        )
        
        # 3. Populate cache
        if redis_client:
            try:
                await asyncio.wait_for(redis_client.setex(f"perf_metrics:{ticker.lower()}", 300, json.dumps(result)), timeout=REDIS_CACHE_TIMEOUT)
            except Exception as e:
                logger.debug("[API] /performance/metrics: Redis cache write failed: %s", e)
                
        return result
        
    except asyncpg.PostgresError as e:
        logger.exception(f"[API] Database error fetching performance metrics for {ticker}")
        raise HTTPException(status_code=500, detail="Database error calculating performance metrics")


def _compute_performance_metrics_sync(initial_capital: float, candles: list, txs: list) -> dict:
    # 4. FIFO closed trade analysis
    buy_queue = []
    closed_trades = []
    
    for tx in txs:
        if tx["action"] == 'BUY':
            buy_queue.append({"qty": tx["qty"], "price": tx["price"]})
        elif tx["action"] == 'SELL':
            sell_qty = tx["qty"]
            total_buy_cost = 0.0
            
            while sell_qty > 0 and buy_queue:
                oldest_buy = buy_queue[0]
                if oldest_buy["qty"] <= sell_qty:
                    total_buy_cost += oldest_buy["qty"] * oldest_buy["price"]
                    sell_qty -= oldest_buy["qty"]
                    buy_queue.pop(0)
                else:
                    total_buy_cost += sell_qty * oldest_buy["price"]
                    oldest_buy["qty"] -= sell_qty
                    sell_qty = 0.0
                    
            sell_revenue = tx["total_value"]
            pnl = sell_revenue - total_buy_cost
            closed_trades.append({"pnl": pnl, "cost_basis": total_buy_cost})
            
    # Compute KPI metrics
    wins = 0
    total_profit = 0.0
    total_losses = 0.0
    net_profit = 0.0
    
    for t in closed_trades:
        pnl = t["pnl"]
        net_profit += pnl
        if pnl > 0:
            wins += 1
            total_profit += pnl
        else:
            total_losses += abs(pnl)
            
    total_trades = len(closed_trades)
    win_rate = float(wins) / total_trades if total_trades > 0 else 0.0
    
    if total_losses > 0:
        profit_factor = total_profit / total_losses
    else:
        profit_factor = None if total_profit > 0 else 1.0
        
    # 5. Reconstruct Account Value Curves over candle intervals
    cash = initial_capital
    qty = 0.0
    tx_idx = 0
    
    strategy_curve = []
    buy_hold_curve = []
    
    first_buy_price = None
    if txs and txs[0]["action"] == 'BUY':
        first_buy_price = txs[0]["price"]
        
    for c in candles:
        candle_time_ms = c["time"] * 1000
        
        # Process any transactions that occurred up to this candle's timestamp
        while tx_idx < len(txs) and txs[tx_idx]["timestamp_ms"] <= candle_time_ms:
            tx = txs[tx_idx]
            if tx["action"] == 'BUY':
                cash -= tx["total_value"]
                qty += tx["qty"]
                if first_buy_price is None:
                    first_buy_price = tx["price"]
            elif tx["action"] == 'SELL':
                cash += tx["total_value"]
                qty -= tx["qty"]
            tx_idx += 1
            
        current_nav = cash + qty * c["close"]
        strategy_curve.append({"time": c["time"], "value": current_nav})
        
        bh_nav = initial_capital
        if first_buy_price is not None and first_buy_price > 0:
            bh_nav = initial_capital * (c["close"] / first_buy_price)
        buy_hold_curve.append({"time": c["time"], "value": bh_nav})
        
    # Calculate Drawdowns
    peak = -float('inf')
    max_drawdown = 0.0
    current_drawdown = 0.0
    
    for pt in strategy_curve:
        val = pt["value"]
        if val > peak:
            peak = val
        dd = ((peak - val) / peak) * 100.0 if peak > 0 else 0.0
        if dd > max_drawdown:
            max_drawdown = dd
        current_drawdown = dd
        
    # Replace infinity with None for standard JSON compliance
    pf_val = None if profit_factor == float('inf') or profit_factor is None else profit_factor
    
    return {
        "win_rate": win_rate,
        "profit_factor": pf_val,
        "max_drawdown": max_drawdown,
        "current_drawdown": current_drawdown,
        "net_profit": net_profit,
        "total_trades": total_trades,
        "strategy_curve": strategy_curve,
        "buy_hold_curve": buy_hold_curve
    }


@router.post("/control/resume")
async def resume_trading(request: Request):
    from backtest_engine.live.kill_switch import KillSwitchStateError, resume_trading as resume_kill_switch

    try:
        kill_switch_status = await resume_kill_switch("dashboard")
    except KillSwitchStateError as exc:
        logger.exception("[API] Failed to synchronize Kill Switch resume")
        raise HTTPException(
            status_code=503,
            detail="Unable to synchronize the Kill Switch state. Trading remains suspended.",
        ) from exc

    return {
        "status": "success",
        "message": "Trading resumed",
        "kill_switch": kill_switch_status.as_dict(),
    }


# --- Authentication Helpers and Endpoints ---

_hmac_secret: str | None = None
_hmac_lock = threading.Lock()

def get_hmac_secret() -> str:
    global _hmac_secret
    if _hmac_secret is None:
        with _hmac_lock:
            if _hmac_secret is None:
                secret = os.getenv("HMAC_SECRET")
                if not secret:
                    import sys
                    is_testing = "pytest" in sys.modules or "unittest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
                    if _is_production() and not is_testing:
                        raise ValueError("Configuration Error: HMAC_SECRET environment variable is missing!")
                    else:
                        secret = secrets.token_hex(32)
                        os.environ["HMAC_SECRET"] = secret
                _hmac_secret = secret
    return _hmac_secret

def create_session_token(username: str, expires: int, secret: str, jti: str | None = None) -> tuple[str, str]:
    """Returns (token, jti). jti is generated if not provided."""
    if jti is None:
        jti = uuid.uuid4().hex
    message = f"{username}:{expires}:{jti}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"{username}:{expires}:{jti}:{sig}", jti

def verify_session_token(token: str, secret: str) -> tuple[bool, str | None, int | None]:
    """Returns (valid, username, expires)."""
    try:
        parts = token.split(":", 3)
        if len(parts) == 4:
            username, expires_str, jti, sig = parts
        elif len(parts) == 3:
            # Legacy tokens (pre-jti) — username:expires:sig
            username, expires_str, sig = parts
            jti = None
        else:
            return False, None, None
        expires = int(expires_str)
        if expires < time.time():
            return False, None, None
        message = f"{username}:{expires_str}"
        if jti:
            message += f":{jti}"
        message = message.encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return True, username, expires
        return False, None, None
    except Exception:
        return False, None, None


SESSION_TTL_SECONDS = 12 * 3600       # 12 hours
SESSION_REFRESH_WINDOW = 4 * 3600     # Re-sign when less than 4h remain
SESSION_COOKIE_MAX_AGE = SESSION_TTL_SECONDS

async def _is_session_revoked(jti: str) -> bool:
    """Check Redis for a revoked jti."""
    if not jti:
        return False
    try:
        from backtest_engine.live.connection import get_async_redis_client
        redis_client = get_async_redis_client()
        if redis_client:
            result = await asyncio.wait_for(
                redis_client.exists(f"session_revoked:{jti}"), timeout=1.0
            )
            return bool(result)
    except Exception:
        pass
    return False

async def _revoke_session(jti: str, ttl: int) -> None:
    """Insert jti into Redis revocation set with residual TTL."""
    if not jti:
        return
    try:
        from backtest_engine.live.connection import get_async_redis_client
        redis_client = get_async_redis_client()
        if redis_client:
            await asyncio.wait_for(
                redis_client.setex(f"session_revoked:{jti}", ttl, "1"), timeout=1.0
            )
    except Exception as e:
        logger.warning("[Session] Failed to revoke jti %s: %s", jti, e)

def get_paper_trader_credentials() -> tuple[str, str]:
    user = os.getenv("PAPER_TRADER_USER", "admin")
    pwd = os.getenv("PAPER_TRADER_PASSWORD")
    if not pwd:
        import sys
        is_testing = "pytest" in sys.modules or "unittest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
        if is_testing:
            pwd = "test_password"
        else:
            raise ValueError("Configuration Error: PAPER_TRADER_PASSWORD environment variable is missing!")
    return user, pwd

@router.get("/csrf-token")
def get_csrf_token(request: Request, response: Response):
    token = request.cookies.get("csrftoken")
    if not token:
        token = secrets.token_hex(32)
        is_prod = _is_production()
        response.set_cookie(
            key="csrftoken",
            value=token,
            max_age=30 * 24 * 3600,
            path="/",
            httponly=True,
            secure=is_prod,
            samesite="strict"
        )
    return {"csrf_token": token}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: Request):
    content_type = request.headers.get("content-type", "")
    username = None
    password = None
    is_form = False

    if "application/x-www-form-urlencoded" in content_type:
        is_form = True
        import urllib.parse
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")
        form_data = urllib.parse.parse_qs(body_str)
        username = form_data.get("username", [None])[0]
        password = form_data.get("password", [None])[0]
    else:
        try:
            payload = await request.json()
            username = payload.get("username")
            password = payload.get("password")
        except Exception:
            return JSONResponse(
                content={"status": "error", "message": "Invalid request body"},
                status_code=400
            )

    try:
        expected_user, expected_password = get_paper_trader_credentials()
    except ValueError as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

    user_ok = hmac.compare_digest(username or "", expected_user)
    pass_ok = hmac.compare_digest(password or "", expected_password)
    if not (user_ok and pass_ok):
        if is_form:
            return RedirectResponse(url="/login.html?error=true", status_code=303)
        return JSONResponse(
            content={"status": "error", "message": "Invalid username or password"},
            status_code=401
        )

    expires = int(time.time()) + SESSION_TTL_SECONDS
    token, jti = create_session_token(username, expires, get_hmac_secret())

    is_prod = _is_production()

    if is_form:
        response = RedirectResponse(url="/", status_code=303)
    else:
        response = JSONResponse(content={"status": "success", "message": "Logged in successfully"})

    response.set_cookie(
        key="paper_trader_session",
        value=token,
        max_age=SESSION_COOKIE_MAX_AGE,
        expires=expires,
        path="/",
        domain=None,
        secure=is_prod,
        httponly=True,
        samesite="strict"
    )
    return response

@router.post("/logout")
async def logout(request: Request):
    # Extract jti from session token and revoke it
    session_token = request.cookies.get("paper_trader_session")
    if session_token:
        try:
            parts = session_token.split(":", 3)
            if len(parts) >= 3:
                jti = parts[2] if len(parts) == 4 else None
                if jti:
                    token_expires = int(parts[1])
                    residual_ttl = max(0, token_expires - int(time.time()))
                    if residual_ttl > 0:
                        await _revoke_session(jti, residual_ttl)
        except (ValueError, IndexError):
            pass

    response = RedirectResponse(url="/login.html", status_code=303)
    response.delete_cookie(key="paper_trader_session", path="/")
    return response
