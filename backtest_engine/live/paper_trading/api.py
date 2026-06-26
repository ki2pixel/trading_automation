import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from contextlib import contextmanager

router = APIRouter(prefix="/api")

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


# Helper functions for threadpool execution
def _get_portfolio_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT cash_balance, allocated_balance, total_nav, last_updated FROM paper_portfolio_balance LIMIT 1")
            row = cur.fetchone()
            if not row:
                return {"cash_balance": 0, "allocated_balance": 0, "total_nav": 0, "last_updated": None}
            return {
                "cash_balance": float(row[0]),
                "allocated_balance": float(row[1]),
                "total_nav": float(row[2]),
                "last_updated": row[3].isoformat() if row[3] else None
            }

def _get_positions_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, asset, strategy_name, qty, entry_price, current_price, pnl, updated_at FROM paper_positions")
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "asset": r[1], "strategy_name": r[2], "qty": float(r[3]),
                    "entry_price": float(r[4]), "current_price": float(r[5]), "pnl": float(r[6]),
                    "updated_at": r[7].isoformat() if r[7] else None
                } for r in rows
            ]

def _get_transactions_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value FROM paper_transactions ORDER BY timestamp DESC LIMIT 100")
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "timestamp": r[1].isoformat() if r[1] else None, "asset": r[2],
                    "strategy_name": r[3], "action": r[4], "qty": float(r[5]), "price": float(r[6]),
                    "total_value": float(r[7])
                } for r in rows
            ]

def _get_configs_sync():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, strategy_name, asset, timeframe, kelly_weight, 
                       initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, is_active, indicator_params, run_status
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
                    "status": "inactive" if not r[9] else (r[11] if r[11] else "active")
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
                        indicator_params = %s, run_status = %s
                    WHERE id = %s
                """, (payload.initial_capital, payload.initial_capital_bucket, 
                      payload.max_capital_bucket, payload.max_entry_price, payload.is_active,
                      params_json, run_status, config_id))
            else:
                cur.execute("""
                    UPDATE paper_strategy_configs 
                    SET initial_capital = %s, initial_capital_bucket = %s, 
                        max_capital_bucket = %s, max_entry_price = %s, is_active = %s,
                        run_status = %s
                    WHERE id = %s
                """, (payload.initial_capital, payload.initial_capital_bucket, 
                      payload.max_capital_bucket, payload.max_entry_price, payload.is_active,
                      run_status, config_id))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Config not found")
            return {"status": "success", "message": "Configuration updated"}


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
