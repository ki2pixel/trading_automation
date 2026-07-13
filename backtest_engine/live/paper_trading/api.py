import os
import json
import asyncio
import logging
import collections
import threading
from datetime import timezone, datetime
from decimal import Decimal
import asyncpg
from fastapi import APIRouter, HTTPException, Request
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
async def get_transactions(limit: int = 50, offset: int = 0):
    pool = await _get_pool()
    try:
        limit = min(max(1, limit), 10000)
        offset = max(0, offset)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
                "FROM paper_transactions ORDER BY timestamp DESC LIMIT $1 OFFSET $2",
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
async def get_evaluations(limit: int = 100, offset: int = 0, status: str | None = None, asset: str | None = None):
    pool = await _get_pool()
    try:
        limit = min(max(1, limit), 10000)
        offset = max(0, offset)

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
    from backtest_engine.live.connection import get_redis_client
    redis_client = None
    try:
        redis_client = get_redis_client()
    except Exception:
        pass
        
    limit = min(max(1, limit), 10000)
    cache_key = f"candles:{ticker.lower()}:{limit}"
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

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
                    redis_client.setex(cache_key, 20, json.dumps(result))
                except Exception:
                    pass
                    
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
@router.post("/control/panic")
async def panic_close_all():
    from backtest_engine.live.kill_switch import set_trading_suspended
    set_trading_suspended(True)
    
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # 1. Lock all balance rows first (consistent with signal_executor lock ordering)
                await conn.execute("SELECT 1 FROM paper_portfolio_balance WHERE source = 'trading212' FOR UPDATE")
                await conn.execute("SELECT 1 FROM paper_portfolio_balance WHERE source = 'bybit' FOR UPDATE")

                # 2. Fetch positions with FOR UPDATE lock to prevent concurrent modifications
                positions = await conn.fetch(
                    "SELECT id, asset, strategy_name, qty, entry_price, current_price FROM paper_positions FOR UPDATE"
                )

                closed_count = 0
                for pos in positions:
                    pos_id = pos["id"]
                    asset = pos["asset"]
                    strategy_name = pos["strategy_name"]
                    qty = Decimal(str(pos["qty"]))
                    entry_price = Decimal(str(pos["entry_price"]))

                    # Resolve price exclusively from live_prices in DB (using asyncpg, non-blocking)
                    live_price = None
                    price_row = await conn.fetchrow(
                        "SELECT price FROM live_prices WHERE LOWER(ticker) = $1",
                        asset.lower(),
                    )
                    if price_row and price_row["price"] is not None:
                        live_price = Decimal(str(price_row["price"]))
                    else:
                        live_price = Decimal(str(pos["current_price"]))

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
                        # The position was already deleted by another concurrent transaction/thread
                        logger.warning(f"[PaperTrader] Position {pos_id} already closed/deleted by concurrent task. Skipping balance credit.")
                        continue

                    # 4. Update balance
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
        last_sent_idx = 0
        with log_lock:
            history_start = max(0, len(log_buffer) - 100)
            buffered_logs = list(log_buffer)[history_start:]
            last_sent_idx = history_start + len(buffered_logs)
            
        for log in buffered_logs:
            yield f"data: {json.dumps(log)}\n\n"
            
        while True:
            if await request.is_disconnected():
                logger.info("[API] Client disconnected from log stream. Stopping generator.")
                break
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


@router.get("/performance/metrics")
async def get_performance_metrics(ticker: str):
    from backtest_engine.live.connection import get_redis_client
    redis_client = None
    try:
        redis_client = get_redis_client()
    except Exception:
        pass
        
    # 1. Cache lookup
    if redis_client:
        try:
            cached = redis_client.get(f"perf_metrics:{ticker.lower()}")
            if cached:
                return json.loads(cached)
        except Exception:
            pass
            
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
                redis_client.setex(f"perf_metrics:{ticker.lower()}", 300, json.dumps(result))
            except Exception:
                pass
                
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
async def resume_trading():
    from backtest_engine.live.kill_switch import set_trading_suspended
    set_trading_suspended(False)
    
    # Also clear Redis flag
    from backtest_engine.live.connection import get_redis_client
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.delete("trading:suspended")
        except Exception as e:
            logger.error(f"[API] Failed to delete suspend flag in Redis: {e}")
            
    return {"status": "success", "message": "Trading resumed"}
