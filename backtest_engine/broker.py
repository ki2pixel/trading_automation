from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Callable, Literal

import math

import pandas as pd


OrderSide = Literal["buy", "sell"]
OrderKind = Literal["market"]
CostSide = Literal["long", "short"]


@dataclass(frozen=True)
class BrokerConfig:
    """Execution assumptions shared by local strategy runners.

    The simulator intentionally starts small: market orders, optional next-bar
    open execution, fixed/relative commissions and long/short positions without
    margin accounting. It gives converted strategies a common target interface
    before their strategy-specific loops are fully migrated.
    """

    initial_capital: float = 1000.0
    execute_on_next_bar: bool = True
    execution_price_col: str = "open"
    commission_fixed: float = 0.0
    commission_rate: float = 0.0
    commission_fixed_long: float | None = None
    commission_fixed_short: float | None = None
    commission_min_long: float | None = None
    commission_min_short: float | None = None
    slippage_per_side_long: float = 0.0
    slippage_per_side_short: float = 0.0
    point_value: float = 1.0
    allow_fractional_quantity: bool = True
    quantity_precision: int | None = 6
    sizing_mode: Literal["fixed", "percent_of_equity", "target_volatility"] = "fixed"
    target_daily_volatility: float = 0.01
    max_leverage: float = 3.0
    volatility_lookback_days: int = 20
    account_currency: str = "EUR"
    asset_currency: str = "EUR"
    fx_rate_provider: Callable[[str, object], float] | None = None


@dataclass(frozen=True)
class Order:
    id: str
    side: OrderSide
    quantity: float
    kind: OrderKind = "market"
    comment: str = ""
    cost_side: CostSide | None = None


@dataclass(frozen=True)
class Fill:
    order_id: str
    timestamp: object
    side: OrderSide
    quantity: float
    price: float
    commission: float
    comment: str = ""
    cost_side: CostSide | None = None

    @property
    def signed_quantity(self) -> float:
        return self.quantity if self.side == "buy" else -self.quantity


@dataclass(frozen=True)
class Position:
    signed_quantity: float = 0.0
    average_price: float = math.nan

    @property
    def is_flat(self) -> bool:
        return self.signed_quantity == 0

    @property
    def side(self) -> str:
        if self.signed_quantity > 0:
            return "long"
        if self.signed_quantity < 0:
            return "short"
        return "flat"


@dataclass(frozen=True)
class ClosedTrade:
    entry_time: object
    exit_time: object
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    gross_pnl: float
    commission: float
    net_pnl: float
    entry_order_id: str
    exit_order_id: str
    exit_comment: str = ""
    is_partial_exit: bool = False
    parent_entry_order_id: str | None = None


@dataclass
class _OpenPositionEntry:
    timestamp: object
    order_id: str
    remaining_commission: float = 0.0
    fx_rate: float = 1.0

@dataclass(frozen=True)
class ExitAction:
    type: Literal["close", "partial"]
    quantity: float
    comment: str
    rule_name: str

class ExitRule(ABC):
    @abstractmethod
    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        pass

class TimeExitRule(ExitRule):
    def __init__(self, threshold_minutes: int, target_time: str | None = None):
        self.threshold_minutes = threshold_minutes
        self.target_time = target_time

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            return None
        if "minutes_until_close" in bar and bar["minutes_until_close"] <= self.threshold_minutes:
            return ExitAction("close", 0.0, "Time threshold reached", "TimeExitRule")
        if self.target_time and "timestamp" in bar:
            ts = bar["timestamp"]
            if hasattr(ts, "strftime"):
                if ts.strftime("%H:%M") >= self.target_time:
                    return ExitAction("close", 0.0, "Target time reached", "TimeExitRule")
        return None

class VWAPExitRule(ExitRule):
    def __init__(self, vwap_series: pd.Series):
        self.vwap_series = vwap_series

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            return None
        ts = bar.get("timestamp")
        if ts is None or ts not in self.vwap_series:
            return None
        vwap = self.vwap_series[ts]
        price = bar.get("close", 0.0)
        if position.signed_quantity > 0 and price < vwap:
             return ExitAction("close", 0.0, "VWAP Cross Down", "VWAPExitRule")
        elif position.signed_quantity < 0 and price > vwap:
             return ExitAction("close", 0.0, "VWAP Cross Up", "VWAPExitRule")
        return None

class BoundaryExitRule(ExitRule):
    def __init__(self, upper_band: pd.Series, lower_band: pd.Series):
        self.upper_band = upper_band
        self.lower_band = lower_band

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            return None
        ts = bar.get("timestamp")
        if ts is None or ts not in self.upper_band or ts not in self.lower_band:
            return None
        upper = self.upper_band[ts]
        lower = self.lower_band[ts]
        price = bar.get("close", 0.0)
        if position.signed_quantity > 0 and price <= lower:
            return ExitAction("close", 0.0, "Lower Boundary crossed (SL)", "BoundaryExitRule")
        elif position.signed_quantity < 0 and price >= upper:
            return ExitAction("close", 0.0, "Upper Boundary crossed (SL)", "BoundaryExitRule")
        return None

class LadderExitRule(ExitRule):
    def __init__(self, steps: list[tuple[float, float]]):
        self.steps = steps
        self.executed_steps = set()

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            self.executed_steps.clear()
            return None
        
        avg_price = position.average_price
        if pd.isna(avg_price) or avg_price == 0:
            return None
        
        price = bar.get("close", 0.0)
        side_mult = 1.0 if position.signed_quantity > 0 else -1.0
        pct_change = (price - avg_price) / avg_price * side_mult
        
        for i, (threshold, qty_pct) in enumerate(self.steps):
            if i in self.executed_steps:
                continue
            
            if (threshold < 0 and pct_change <= threshold) or (threshold > 0 and pct_change >= threshold):
                self.executed_steps.add(i)
                qty = abs(position.signed_quantity) * qty_pct
                return ExitAction("partial", qty, f"Ladder Step {i+1}", "LadderExitRule")
                
        return None

class SequentialLadderExitRule(ExitRule):
    def __init__(self, stoploss_step0: float, stoploss_step1: float, takeprofit_step0: float, takeprofit_step1: float | None = None, takeprofit_ratio0: float = 0.5):
        self.stoploss_step0 = stoploss_step0
        self.stoploss_step1 = stoploss_step1
        self.takeprofit_step0 = takeprofit_step0
        self.takeprofit_step1 = takeprofit_step1
        self.takeprofit_ratio0 = takeprofit_ratio0
        self.current_step = 0

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            self.current_step = 0
            return None
        
        avg_price = position.average_price
        if pd.isna(avg_price) or avg_price == 0:
            return None
        
        price = bar.get("close", 0.0)
        side_mult = 1.0 if position.signed_quantity > 0 else -1.0
        pct_change = (price - avg_price) / avg_price * side_mult
        
        if self.current_step == 0:
            if pct_change <= self.stoploss_step0:
                return ExitAction("close", 0.0, "Ladder SL Step 0", "SequentialLadderExitRule")
            if pct_change >= self.takeprofit_step0:
                self.current_step = 1
                qty = abs(position.signed_quantity) * self.takeprofit_ratio0
                return ExitAction("partial", qty, "Ladder TP Step 0", "SequentialLadderExitRule")
        elif self.current_step == 1:
            if pct_change <= self.stoploss_step1:
                return ExitAction("close", 0.0, "Ladder SL Step 1", "SequentialLadderExitRule")
            if self.takeprofit_step1 is not None and pct_change >= self.takeprofit_step1:
                return ExitAction("close", 0.0, "Ladder TP Step 1", "SequentialLadderExitRule")
                
        return None

class NetBracketExitRule(ExitRule):
    def __init__(self, broker: BrokerSimulator, tp_pct: float | None = None, sl_pct: float | None = None):
        self.broker = broker
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            return None
        
        avg_price = position.average_price
        if pd.isna(avg_price) or avg_price == 0:
            return None
            
        qty = abs(position.signed_quantity)
        entry_position_value = avg_price * qty * self.broker.config.point_value
        
        # Calculate dynamic exit commission
        exit_comm = self.broker.commission_for(qty, bar["close"], cost_side=position.side)
        
        # Retrieve entry commission from the current trade
        entry_comm = self.broker._open_entry.remaining_commission if self.broker._open_entry else 0.0
        
        # Calculate gross PnL in account currency
        fx_rate = self.broker.fx_rate(bar.get("timestamp"))
        price_account = bar.get("close", 0.0) * fx_rate
        side_mult = 1.0 if position.signed_quantity > 0 else -1.0
        gross_pnl = (price_account - avg_price) * qty * side_mult * self.broker.config.point_value
        
        # Calculate net PnL (net of all commissions & slippage)
        net_pnl = gross_pnl - entry_comm - exit_comm
        
        if self.tp_pct is not None and self.tp_pct > 0:
            tp_threshold = entry_position_value * self.tp_pct / 100.0
            if net_pnl >= tp_threshold:
                return ExitAction("close", 0.0, f"Net TP reached ({self.tp_pct}%)", "NetBracketExitRule")
                
        if self.sl_pct is not None and self.sl_pct > 0:
            sl_threshold = entry_position_value * self.sl_pct / 100.0
            if net_pnl <= -sl_threshold:
                return ExitAction("close", 0.0, f"Net SL reached ({self.sl_pct}%)", "NetBracketExitRule")
                
        return None

class SafetyStopExitRule(ExitRule):
    def __init__(
        self,
        broker: BrokerSimulator,
        applies_to: str = "Both",
        mode: str = "Net loss only",
        max_loss_mode: str = "Cash amount",
        max_loss_cash: float | None = None,
        max_loss_pct: float | None = None,
        max_bars: int = 0,
    ):
        self.broker = broker
        self.applies_to = applies_to
        self.mode = mode
        self.max_loss_mode = max_loss_mode
        self.max_loss_cash = max_loss_cash
        self.max_loss_pct = max_loss_pct
        self.max_bars = max_bars
        self.bars_in_trade = 0

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        if position.is_flat:
            self.bars_in_trade = 0
            return None
        
        # Check if the safety stop applies to this position direction
        is_long = position.signed_quantity > 0
        is_short = position.signed_quantity < 0
        
        safety_direction_allowed = (
            self.applies_to == "Both"
            or (self.applies_to == "Long only" and is_long)
            or (self.applies_to == "Short only" and is_short)
        )
        if not safety_direction_allowed:
            return None
            
        # Increment bars in trade count
        self.bars_in_trade += 1
        
        avg_price = position.average_price
        if pd.isna(avg_price) or avg_price == 0:
            return None
            
        qty = abs(position.signed_quantity)
        
        # Calculate loss trigger
        safety_loss_triggered = False
        if self.mode in ("Net loss only", "Net loss OR max bars", "Net loss AND max bars"):
            entry_position_value = avg_price * qty * self.broker.config.point_value
            exit_comm = self.broker.commission_for(qty, bar["close"], cost_side=position.side)
            entry_comm = self.broker._open_entry.remaining_commission if self.broker._open_entry else 0.0
            
            fx_rate = self.broker.fx_rate(bar.get("timestamp"))
            price_account = bar.get("close", 0.0) * fx_rate
            side_mult = 1.0 if position.signed_quantity > 0 else -1.0
            gross_pnl = (price_account - avg_price) * qty * side_mult * self.broker.config.point_value
            net_pnl = gross_pnl - entry_comm - exit_comm
            
            if self.max_loss_mode == "Cash amount":
                threshold = float(self.max_loss_cash) if self.max_loss_cash is not None else 0.0
            else:
                threshold = entry_position_value * (self.max_loss_pct if self.max_loss_pct is not None else 0.0) / 100.0
                
            if threshold > 0 and net_pnl <= -threshold:
                safety_loss_triggered = True
                
        # Check bars trigger
        safety_bars_triggered = False
        if self.mode in ("Max bars only", "Net loss OR max bars", "Net loss AND max bars"):
            if self.max_bars > 0 and self.bars_in_trade >= self.max_bars:
                safety_bars_triggered = True
                
        # Combine triggers based on mode
        safety_stop_triggered = False
        if self.mode == "Net loss only":
            safety_stop_triggered = safety_loss_triggered
        elif self.mode == "Max bars only":
            safety_stop_triggered = safety_bars_triggered
        elif self.mode == "Net loss OR max bars":
            safety_stop_triggered = safety_loss_triggered or safety_bars_triggered
        elif self.mode == "Net loss AND max bars":
            safety_stop_triggered = safety_loss_triggered and safety_bars_triggered
            
        if safety_stop_triggered:
            return ExitAction("close", 0.0, f"Safety Stop triggered ({self.mode})", "SafetyStopExitRule")
            
        return None

class ExitOrchestrator:
    def __init__(self, rules: list[ExitRule]):
        self.rules = rules

    def evaluate(self, bar: dict, position: Position) -> ExitAction | None:
        actions = []
        for rule in self.rules:
            action = rule.evaluate(bar, position)
            if action:
                actions.append(action)
        if not actions:
            return None
        
        close_actions = [a for a in actions if a.type == "close"]
        if close_actions:
            return close_actions[0]
        
        actions.sort(key=lambda a: a.quantity, reverse=True)
        return actions[0]


class BrokerSimulator:
    """Minimal deterministic broker simulator for local backtests."""

    def __init__(self, config: BrokerConfig | None = None) -> None:
        self.config = config or BrokerConfig()
        self.cash = float(self.config.initial_capital)
        self.position = Position()
        self.fills: list[Fill] = []
        self.closed_trades: list[ClosedTrade] = []
        self._open_entry: _OpenPositionEntry | None = None
        self.exit_orchestrator: ExitOrchestrator | None = None

    def fx_rate(self, timestamp: object) -> float:
        if self.config.asset_currency == self.config.account_currency:
            return 1.0
        if self.config.fx_rate_provider is None:
            return 1.0
        try:
            rate = float(self.config.fx_rate_provider(self.config.asset_currency, timestamp))
            if math.isnan(rate) or math.isclose(rate, 0.0, abs_tol=1e-9):
                return 1.0
            return rate
        except Exception:  # NOSONAR
            return 1.0

    def evaluate_exits(self, bar: dict) -> ExitAction | None:
        if self.position.is_flat or not self.exit_orchestrator:
            return None
        if self._open_entry is not None and self._open_entry.timestamp == bar.get("timestamp"):
            return None
        action = self.exit_orchestrator.evaluate(bar, self.position)
        if action:
            qty = abs(self.position.signed_quantity) if action.type == "close" else action.quantity
            side: OrderSide = "sell" if self.position.signed_quantity > 0 else "buy"
            order = Order(
                id=f"exit_{action.rule_name}_{bar.get('timestamp', 'none')}",
                side=side,
                quantity=qty,
                kind="market",
                comment=action.comment
            )
            price = bar.get(self.config.execution_price_col, 0.0)
            self.fill_order(order, bar.get("timestamp", None), price)
        return action

    def calculate_position_size(self, price: float, equity: float, realized_volatility: float | None = None, bars_for_vol: pd.DataFrame | None = None, timestamp: object | None = None) -> float:
        if self.config.sizing_mode == "fixed":
            size = 1.0
        elif self.config.sizing_mode == "percent_of_equity":
            size = equity * 0.1 / price  # Basic default if needed
        elif self.config.sizing_mode == "target_volatility":
            if realized_volatility is not None and realized_volatility > 0 and not pd.isna(realized_volatility):
                vol = realized_volatility
            else:
                if bars_for_vol is None or len(bars_for_vol) < 2:
                    return 1.0
                
                # Optimization: avoid computing pct_change on the entire history.
                # We only need the tail of size (lookback + 2) to get the tail returns.
                lookback = self.config.volatility_lookback_days
                tail_bars = bars_for_vol['close'].iloc[-(lookback + 2):]
                returns = tail_bars.pct_change().dropna()
                
                if len(returns) < 2:
                    return 1.0
                vol = returns.tail(lookback).std()
                if vol == 0 or pd.isna(vol):
                    return 1.0
            
            size = (equity * self.config.target_daily_volatility) / (price * vol)
        else:
            size = 1.0

        # Hard cap of leverage: if implied leverage (notional / equity) > max_leverage, cap size
        if size > 0:
            fx_rate = self.fx_rate(timestamp) if timestamp is not None else 1.0
            price_account = float(price) * fx_rate
            denom = price_account * float(self.config.point_value)
            if denom > 0 and equity > 0:
                max_size = (equity * self.config.max_leverage) / denom
                size = min(size, max_size)
            else:
                size = 0.0

        return size

    def normalize_quantity(self, quantity: float) -> float:
        if pd.isna(quantity) or quantity <= 0:
            return 0.0
        qty = float(quantity)
        if not self.config.allow_fractional_quantity:
            qty = math.floor(qty)
        if self.config.quantity_precision is not None:
            qty = round(qty, self.config.quantity_precision)
        return max(qty, 0.0)

    def commission_for(self, quantity: float, price: float, cost_side: CostSide | None = None) -> float:
        notional = abs(quantity) * float(price) * float(self.config.point_value)
        fixed = float(self.config.commission_fixed)
        rate_comm = notional * float(self.config.commission_rate)
        slippage = 0.0
        if cost_side == "long":
            fixed = float(self.config.commission_fixed_long if self.config.commission_fixed_long is not None else fixed)
            slippage = float(self.config.slippage_per_side_long)
            if self.config.commission_min_long is not None:
                rate_comm = max(self.config.commission_min_long, rate_comm)
        elif cost_side == "short":
            fixed = float(self.config.commission_fixed_short if self.config.commission_fixed_short is not None else fixed)
            slippage = float(self.config.slippage_per_side_short)
            if self.config.commission_min_short is not None:
                rate_comm = max(self.config.commission_min_short, rate_comm)
        return fixed + slippage + rate_comm

    def fill_order(self, order: Order, timestamp: object, price: float) -> Fill | None:
        if order.kind != "market":
            raise ValueError(f"Unsupported order kind: {order.kind}")
        quantity = self.normalize_quantity(order.quantity)
        if quantity <= 0 or pd.isna(price) or price <= 0:
            return None

        fx_rate = self.fx_rate(timestamp)
        price_account = float(price) * fx_rate
        commission = self.commission_for(quantity, price_account, cost_side=order.cost_side)
        fill = Fill(
            order_id=order.id,
            timestamp=timestamp,
            side=order.side,
            quantity=quantity,
            price=price_account,
            commission=commission,
            comment=order.comment,
            cost_side=order.cost_side,
        )
        self._apply_fill(fill)
        self.fills.append(fill)
        return fill

    def _apply_fill(self, fill: Fill) -> None:
        previous_qty = self.position.signed_quantity
        delta_qty = fill.signed_quantity
        new_qty = previous_qty + delta_qty
        self.cash -= delta_qty * fill.price * float(self.config.point_value) + fill.commission

        if previous_qty == 0 or previous_qty * delta_qty > 0:
            total_abs_qty = abs(previous_qty) + abs(delta_qty)
            avg_price = (
                (abs(previous_qty) * (self.position.average_price if previous_qty else 0.0))
                + abs(delta_qty) * fill.price
            ) / total_abs_qty
            self.position = Position(new_qty, avg_price)
            if previous_qty == 0:
                self._open_entry = _OpenPositionEntry(fill.timestamp, fill.order_id, fill.commission, self.fx_rate(fill.timestamp))
            elif self._open_entry is not None:
                self._open_entry.remaining_commission += fill.commission
            else:
                self._open_entry = _OpenPositionEntry(fill.timestamp, fill.order_id, fill.commission, self.fx_rate(fill.timestamp))
            return

        closing_qty = min(abs(previous_qty), abs(delta_qty))
        side_multiplier = 1.0 if previous_qty > 0 else -1.0
        gross = (fill.price - self.position.average_price) * closing_qty * side_multiplier * float(self.config.point_value)
        entry = self._open_entry or _OpenPositionEntry(fill.timestamp, fill.order_id, 0.0)
        allocated_entry_commission = entry.remaining_commission * (closing_qty / max(abs(previous_qty), 1e-12))
        closing_fill_ratio = closing_qty / max(fill.quantity, 1e-12)
        allocated_exit_commission = fill.commission * closing_fill_ratio
        total_commission = allocated_entry_commission + allocated_exit_commission
        
        is_partial = (previous_qty * new_qty > 0) and (abs(new_qty) < abs(previous_qty))
        self.closed_trades.append(
            ClosedTrade(
                entry_time=entry.timestamp,
                exit_time=fill.timestamp,
                side="long" if previous_qty > 0 else "short",
                quantity=closing_qty,
                entry_price=self.position.average_price,
                exit_price=fill.price,
                gross_pnl=gross,
                commission=total_commission,
                net_pnl=gross - total_commission,
                entry_order_id=entry.order_id,
                exit_order_id=fill.order_id,
                exit_comment=fill.comment,
                is_partial_exit=is_partial,
                parent_entry_order_id=entry.order_id if is_partial else None,
            )
        )
        if self._open_entry is not None:
            self._open_entry.remaining_commission = max(0.0, self._open_entry.remaining_commission - allocated_entry_commission)

        if new_qty == 0:
            self.position = Position()
            self._open_entry = None
        elif previous_qty * new_qty > 0:
            self.position = Position(new_qty, self.position.average_price)
        else:
            self.position = Position(new_qty, fill.price)
            reversal_entry_commission = fill.commission * (abs(new_qty) / max(fill.quantity, 1e-12))
            self._open_entry = _OpenPositionEntry(fill.timestamp, fill.order_id, reversal_entry_commission, self.fx_rate(fill.timestamp))

    def mark_to_market_equity(self, price: float, timestamp: object | None = None) -> float:
        if self.position.is_flat or pd.isna(price):
            return self.cash
        fx_rate = self.fx_rate(timestamp) if timestamp is not None else 1.0
        price_account = float(price) * fx_rate
        return self.cash + self.position.signed_quantity * price_account * float(self.config.point_value)

    def fills_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(fill) for fill in self.fills])

    def closed_trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(trade) for trade in self.closed_trades])
