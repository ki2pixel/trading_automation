from __future__ import annotations
from pathlib import Path
from typing import Any

def setup_currency_and_fx_provider(
    symbol: str,
    timeframe_minutes: int | str,
    repo_root: Path | None = None,
    overrides: Any | None = None,
    default_account_currency: str = "EUR",
) -> tuple[str, str, Any]:
    """Helper to build fx rate provider and load asset/account currency.
    
    Returns (account_currency, asset_currency, fx_rate_provider)
    """
    fx_rate_provider = getattr(overrides, "fx_rate_provider", None) if overrides else None
    asset_currency = getattr(overrides, "asset_currency", None) if overrides else None
    account_currency = getattr(overrides, "account_currency", None) if overrides else None

    if account_currency is None:
        account_currency = default_account_currency

    if repo_root is not None and fx_rate_provider is None:
        from ..data import build_fx_rate_provider
        from ..canonical import load_symbol_currency_map
        fx_rate_provider = build_fx_rate_provider(
            repo_root, symbol, account_currency=account_currency, timeframe_minutes=timeframe_minutes
        )
        if fx_rate_provider is not None and asset_currency is None:
            currency_map = load_symbol_currency_map(repo_root, timeframe_minutes)
            asset_currency = currency_map.get(symbol, account_currency).upper()
            
    if asset_currency is None:
        asset_currency = account_currency
        
    return account_currency, asset_currency, fx_rate_provider
