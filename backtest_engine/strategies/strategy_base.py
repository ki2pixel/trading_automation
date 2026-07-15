from __future__ import annotations

from dataclasses import asdict
from typing import Any, Tuple
import pandas as pd
import numpy as np

class BaseStrategyRunner:
    """Base class for running backtest strategies, encapsulating common utilities."""

    @staticmethod
    def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and index for OHLCV data."""
        out = data.copy()
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in out.columns:
                raise ValueError(f"Missing required column: {col}")
        return out[["open", "high", "low", "close", "volume"]].copy()

    @staticmethod
    def _apply_overrides(config: Any, overrides: Any) -> Any:
        """Apply config overrides dynamically to a strategy configuration object."""
        if overrides is None:
            return config
        for key, value in asdict(overrides).items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        return config

    @staticmethod
    def _normalize_trades(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
        """Adapt broker.closed_trades_frame() to the format expected by compute_metrics."""
        if trades.empty:
            return pd.DataFrame(columns=[
                "entry_index", "exit_index", "side", "qty", "entry_price",
                "exit_price", "gross_pnl", "estimated_costs", "net_pnl",
                "bars_held", "exit_comment",
            ])

        out = trades.copy()
        out = out.rename(columns={
            "entry_time": "entry_index",
            "exit_time": "exit_index",
            "quantity": "qty",
            "commission": "estimated_costs",
        })

        bar_positions = pd.Series(
            np.arange(len(bars), dtype=np.int64), index=bars.index,
        )
        entry_pos = out["entry_index"].map(bar_positions)
        exit_pos = out["exit_index"].map(bar_positions)
        out["bars_held"] = (exit_pos - entry_pos).astype(float)

        for col in [
            "entry_index", "exit_index", "side", "qty", "entry_price",
            "exit_price", "gross_pnl", "estimated_costs", "net_pnl",
            "bars_held", "exit_comment",
        ]:
            if col not in out.columns:
                out[col] = np.nan

        return out[[
            "entry_index", "exit_index", "side", "qty", "entry_price",
            "exit_price", "gross_pnl", "estimated_costs", "net_pnl",
            "bars_held", "exit_comment",
        ]]

    @staticmethod
    def _build_state_from_broker(
        broker: Any,
        bars: pd.DataFrame,
        timestamps: pd.DatetimeIndex,
        close_arr: np.ndarray,
    ) -> pd.DataFrame:
        """Build state DataFrame (realized net PnL, unrealized PnL, position sizing) from broker."""
        n = len(bars)
        realized = np.zeros(n, dtype=np.float64)
        open_pnl = np.zeros(n, dtype=np.float64)
        pos_size = np.zeros(n, dtype=np.float64)
        pos_avg = np.zeros(n, dtype=np.float64)
        bar_positions = pd.Series(np.arange(n, dtype=np.int64), index=timestamps)

        for ct in broker.closed_trades:
            exit_ts = ct.exit_time
            if exit_ts in bar_positions.index:
                idx = bar_positions[exit_ts]
                realized[idx] += ct.net_pnl

        fill_by_bar: dict[object, list] = {}
        for fill in broker.fills:
            fill_by_bar.setdefault(fill.timestamp, []).append(fill)

        cur_qty = 0.0
        cur_avg = 0.0
        last_idx = 0
        pos_qty = np.zeros(n, dtype=np.float64)
        fill_indices = [bar_positions.get(ts, -1) for ts in fill_by_bar.keys()]
        fill_indices = sorted([i for i in fill_indices if i != -1])

        for idx in fill_indices:
            if idx > last_idx:
                pos_qty[last_idx:idx] = cur_qty
                pos_avg[last_idx:idx] = cur_avg
            ts = timestamps[idx]
            for fill in fill_by_bar[ts]:
                delta = fill.signed_quantity
                new_qty = cur_qty + delta
                if cur_qty == 0 or cur_qty * delta > 0:
                    total = abs(cur_qty) + abs(delta)
                    if total > 0:
                        cur_avg = (abs(cur_qty) * cur_avg + abs(delta) * fill.price) / total
                    cur_qty = new_qty
                else:
                    if new_qty == 0:
                        cur_qty = 0.0
                        cur_avg = 0.0
                    elif cur_qty * new_qty > 0:
                        cur_qty = new_qty
                    else:
                        cur_qty = new_qty
                        cur_avg = fill.price
            pos_qty[idx] = cur_qty
            pos_avg[idx] = cur_avg
            last_idx = idx + 1

        if last_idx < n:
            pos_qty[last_idx:n] = cur_qty
            pos_avg[last_idx:n] = cur_avg

        pos_size[:] = np.abs(pos_qty)
        mask = (pos_qty != 0) & (pos_avg > 0)
        if mask.any():
            active_indices = np.where(mask)[0]
            if broker.config.asset_currency == broker.config.account_currency:
                price_account = close_arr[active_indices]
            else:
                fx_arr = np.array([broker.fx_rate(timestamps[idx]) for idx in active_indices])
                price_account = close_arr[active_indices] * fx_arr
            side_mult = np.sign(pos_qty[active_indices])
            open_pnl[active_indices] = (price_account - pos_avg[active_indices]) * np.abs(pos_qty[active_indices]) * side_mult * broker.config.point_value

        return pd.DataFrame(
            {
                "realized_net_pnl_on_fill": realized,
                "estimated_net_if_closed_now": open_pnl,
                "position_abs_size": pos_size,
                "position_avg_price": pos_avg,
            },
            index=timestamps,
        )



class BaseBrokerStrategyRunner(BaseStrategyRunner):
    """Subclass for strategies using BrokerSimulator for bar-by-bar simulation."""

    @staticmethod
    def setup_broker_simulator(
        overrides: Any,
        initial_capital: float,
        account_currency: str | None,
        asset_currency: str | None,
        fx_rate_provider: Any,
    ) -> Tuple[Any, Any]:
        """Set up the BrokerSimulator and configure exit rules."""
        from ..broker import BrokerSimulator, BrokerConfig

        exec_col = overrides.next_bar_execution_price_col or "open"
        broker_config = BrokerConfig(
            initial_capital=initial_capital,
            execute_on_next_bar=overrides.execute_on_next_bar if overrides.execute_on_next_bar is not None else True,
            execution_price_col=exec_col,
            commission_fixed_long=overrides.estimated_commission_per_order_long,
            commission_fixed_short=overrides.estimated_commission_per_order_short,
            slippage_per_side_long=overrides.estimated_slippage_per_side_long if overrides.estimated_slippage_per_side_long is not None else 0.0,
            slippage_per_side_short=overrides.estimated_slippage_per_side_short if overrides.estimated_slippage_per_side_short is not None else 0.0,
            point_value=overrides.point_value if overrides.point_value is not None else 1.0,
            allow_fractional_quantity=overrides.allow_fractional_quantity if overrides.allow_fractional_quantity is not None else True,
            quantity_precision=overrides.quantity_precision,
            account_currency=account_currency if account_currency is not None else "EUR",
            asset_currency=asset_currency if asset_currency is not None else "EUR",
            fx_rate_provider=fx_rate_provider,
        )
        broker = BrokerSimulator(broker_config)

        # Exit rules
        exit_rules = []
        use_bracket = overrides.use_net_bracket_exits or getattr(overrides, "enable_stop_loss", False) or getattr(overrides, "enable_take_profit", False)
        if use_bracket:
            from ..broker import NetBracketExitRule
            tp = getattr(overrides, "take_profit_pct", None) if getattr(overrides, "enable_take_profit", False) else getattr(overrides, "take_profit_net_percent", None)
            sl = getattr(overrides, "stop_loss_pct", None) if getattr(overrides, "enable_stop_loss", False) else getattr(overrides, "stop_loss_net_percent", None)
            exit_rules.append(NetBracketExitRule(
                broker,
                tp_pct=tp,
                sl_pct=sl,
            ))

        if getattr(overrides, "enable_trailing_stop", False):
            from ..broker import TrailingStopExitRule
            exit_rules.append(TrailingStopExitRule(
                broker,
                trail_profit_pct=overrides.trail_profit_pct if overrides.trail_profit_pct is not None else 0.5,
                trail_loss_pct=overrides.trail_loss_pct if overrides.trail_loss_pct is not None else 0.5,
            ))

        if overrides.use_safety_stop if overrides.use_safety_stop is not None else False:
            from ..broker import SafetyStopExitRule
            exit_rules.append(SafetyStopExitRule(
                broker,
                applies_to=overrides.safety_stop_applies_to or "Both",
                mode=overrides.safety_stop_mode or "Net loss only",
                max_loss_mode=overrides.safety_max_net_loss_mode or "Cash amount",
                max_loss_cash=overrides.safety_max_net_loss_cash,
                max_loss_pct=overrides.safety_max_net_loss_percent,
                max_bars=overrides.safety_max_bars_in_trade or 0,
            ))

        if exit_rules:
            from ..broker import ExitOrchestrator
            broker.exit_orchestrator = ExitOrchestrator(exit_rules)

        return broker, broker_config
