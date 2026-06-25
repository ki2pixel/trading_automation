import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2

router = APIRouter(prefix="/api")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

class ConfigUpdate(BaseModel):
    initial_capital: float
    initial_capital_bucket: float
    max_capital_bucket: float
    max_entry_price: float
    is_active: bool

@router.get("/portfolio")
def get_portfolio():
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
def get_positions():
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
def get_transactions():
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs")
def get_configs():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, strategy_name, asset, timeframe, kelly_weight, 
                           initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, is_active
                    FROM paper_strategy_configs
                    ORDER BY id ASC
                """)
                rows = cur.fetchall()
                return [
                    {
                        "id": r[0], "strategy_name": r[1], "asset": r[2], "timeframe": r[3],
                        "kelly_weight": float(r[4]), "initial_capital": float(r[5]),
                        "initial_capital_bucket": float(r[6]), "max_capital_bucket": float(r[7]),
                        "max_entry_price": float(r[8]), "is_active": r[9]
                    } for r in rows
                ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/configs/{config_id}")
def update_config(config_id: int, payload: ConfigUpdate):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE paper_strategy_configs 
                    SET initial_capital = %s, initial_capital_bucket = %s, 
                        max_capital_bucket = %s, max_entry_price = %s, is_active = %s
                    WHERE id = %s
                """, (payload.initial_capital, payload.initial_capital_bucket, 
                      payload.max_capital_bucket, payload.max_entry_price, payload.is_active, config_id))
                conn.commit()
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Config not found")
                return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
