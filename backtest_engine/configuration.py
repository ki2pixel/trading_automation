from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
from typing import Any, Literal


ParameterKind = Literal["numeric", "choice", "bool"]


@dataclass(frozen=True)
class StrategyParameterDefinition:
    name: str
    kind: ParameterKind
    value_type: str
    description: str
    default: object | None = None
    group: str = "Strategy"
    choices: list[str] | None = None
    default_start: float | int | None = None
    default_end: float | int | None = None
    default_step: float | int | None = None
    optimizable: bool = True
    active_if: dict[str, object] | None = None
    tags: list[str] | None = None

    def optimizer_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("default", None)
        payload.pop("optimizable", None)
        return payload


@dataclass(frozen=True)
class StrategyRuntimeConfig:
    strategy: str
    parameters: dict[str, object]
    backtest: dict[str, object]
    source_path: str | None = None


FEE_MODE_CHOICES = [
    "Parametric: hold until net covers fees",
    "Parametric: exit only, no forced reversal",
    "Disabled: always reverse/close on opposite signal",
]
TRADE_DIRECTION_CHOICES = ["Long & Short", "Long only", "Short only"]
SAFETY_APPLIES_TO_CHOICES = ["Both", "Long only", "Short only"]
SAFETY_STOP_MODE_CHOICES = [
    "Net loss only",
    "Max bars only",
    "Net loss OR max bars",
    "Net loss AND max bars",
]
SAFETY_MAX_NET_LOSS_MODE_CHOICES = ["Cash amount", "% of entry value"]


COMMON_V3_PARAMETERS: dict[str, StrategyParameterDefinition] = {
    "max_entry_price": StrategyParameterDefinition(
        name="max_entry_price",
        kind="numeric",
        value_type="float",
        description="Prix d'entrée maximal autorisé",
        default=300.0,
        group="V3 - Capped bucket model",
        default_start=100,
        default_end=10000,
        default_step=1000,
    ),
    "max_capital_bucket": StrategyParameterDefinition(
        name="max_capital_bucket",
        kind="numeric",
        value_type="float",
        description="Bucket de capital maximal réinvestissable",
        default=300.0,
        group="V3 - Capped bucket model",
        default_start=100,
        default_end=1000,
        default_step=100,
    ),
    "initial_capital_bucket": StrategyParameterDefinition(
        name="initial_capital_bucket",
        kind="numeric",
        value_type="float",
        description="Bucket de capital initial",
        default=300.0,
        group="V3 - Capped bucket model",
        default_start=100,
        default_end=1000,
        default_step=100,
    ),
    "trade_direction_mode": StrategyParameterDefinition(
        name="trade_direction_mode",
        kind="choice",
        value_type="str",
        description="Direction de trading autorisée",
        default="Long & Short",
        group="V3.3 - Trade direction",
        choices=TRADE_DIRECTION_CHOICES,
    ),
    "fee_mode": StrategyParameterDefinition(
        name="fee_mode",
        kind="choice",
        value_type="str",
        description="Comportement sur signal opposé et frais estimés",
        default="Parametric: hold until net covers fees",
        group="V3.2 - Fee / reversal filter",
        choices=FEE_MODE_CHOICES,
    ),
    "estimated_commission_per_order_long": StrategyParameterDefinition(
        name="estimated_commission_per_order_long",
        kind="numeric",
        value_type="float",
        description="Commission estimée par ordre LONG en devise de compte",
        default=0.0,
        group="V3.2 - Fee / reversal filter",
        default_start=0,
        default_end=5,
        default_step=0.5,
        tags=["long", "cost"],
    ),
    "estimated_commission_per_order_short": StrategyParameterDefinition(
        name="estimated_commission_per_order_short",
        kind="numeric",
        value_type="float",
        description="Commission estimée par ordre SHORT en devise de compte",
        default=3.0,
        group="V3.2 - Fee / reversal filter",
        default_start=0,
        default_end=5,
        default_step=0.5,
        tags=["short", "cost"],
    ),
    "estimated_slippage_per_side_long": StrategyParameterDefinition(
        name="estimated_slippage_per_side_long",
        kind="numeric",
        value_type="float",
        description="Slippage estimé par côté LONG en devise de compte",
        default=0.0,
        group="V3.2 - Fee / reversal filter",
        default_start=0,
        default_end=5,
        default_step=0.5,
        tags=["long", "cost"],
    ),
    "estimated_slippage_per_side_short": StrategyParameterDefinition(
        name="estimated_slippage_per_side_short",
        kind="numeric",
        value_type="float",
        description="Slippage estimé par côté SHORT en devise de compte",
        default=0.0,
        group="V3.2 - Fee / reversal filter",
        default_start=0,
        default_end=5,
        default_step=0.5,
        tags=["short", "cost"],
    ),
    "min_net_profit_after_costs": StrategyParameterDefinition(
        name="min_net_profit_after_costs",
        kind="numeric",
        value_type="float",
        description="Profit net minimal requis pour sortie/reversal sur signal opposé",
        default=0.0,
        group="V3.2 - Fee / reversal filter",
        default_start=0,
        default_end=20,
        default_step=1,
    ),
    "use_net_bracket_exits": StrategyParameterDefinition(
        name="use_net_bracket_exits",
        kind="bool",
        value_type="bool",
        description="Activer les sorties TP/SL nettes explicites",
        default=False,
        group="V3.2 - Explicit net exits",
        choices=["true", "false"],
    ),
    "take_profit_net_percent": StrategyParameterDefinition(
        name="take_profit_net_percent",
        kind="numeric",
        value_type="float",
        description="Take-profit net en % de la valeur d'entrée",
        default=10.0,
        group="V3.2 - Explicit net exits",
        default_start=1,
        default_end=20,
        default_step=1,
        active_if={"use_net_bracket_exits": True},
    ),
    "stop_loss_net_percent": StrategyParameterDefinition(
        name="stop_loss_net_percent",
        kind="numeric",
        value_type="float",
        description="Stop-loss net en % de la valeur d'entrée",
        default=10.0,
        group="V3.2 - Explicit net exits",
        default_start=1,
        default_end=20,
        default_step=1,
        active_if={"use_net_bracket_exits": True},
    ),
    "use_safety_stop": StrategyParameterDefinition(
        name="use_safety_stop",
        kind="bool",
        value_type="bool",
        description="Activer le safety stop de dernier recours",
        default=True,
        group="V3.2 - Safety stop",
        choices=["true", "false"],
    ),
    "safety_stop_applies_to": StrategyParameterDefinition(
        name="safety_stop_applies_to",
        kind="choice",
        value_type="str",
        description="Directions auxquelles le safety stop s'applique",
        default="Short only",
        group="V3.2 - Safety stop",
        choices=SAFETY_APPLIES_TO_CHOICES,
        active_if={"use_safety_stop": True},
    ),
    "safety_stop_mode": StrategyParameterDefinition(
        name="safety_stop_mode",
        kind="choice",
        value_type="str",
        description="Mode de déclenchement du safety stop",
        default="Net loss only",
        group="V3.2 - Safety stop",
        choices=SAFETY_STOP_MODE_CHOICES,
        active_if={"use_safety_stop": True},
    ),
    "safety_max_net_loss_mode": StrategyParameterDefinition(
        name="safety_max_net_loss_mode",
        kind="choice",
        value_type="str",
        description="Type de seuil de perte maximale safety stop",
        default="Cash amount",
        group="V3.2 - Safety stop",
        choices=SAFETY_MAX_NET_LOSS_MODE_CHOICES,
        active_if={"use_safety_stop": True},
    ),
    "safety_max_net_loss_cash": StrategyParameterDefinition(
        name="safety_max_net_loss_cash",
        kind="numeric",
        value_type="float",
        description="Perte nette maximale cash du safety stop",
        default=50.0,
        group="V3.2 - Safety stop",
        default_start=0,
        default_end=100,
        default_step=5,
        active_if={"use_safety_stop": True, "safety_max_net_loss_mode": "Cash amount"},
    ),
    "safety_max_net_loss_percent": StrategyParameterDefinition(
        name="safety_max_net_loss_percent",
        kind="numeric",
        value_type="float",
        description="Perte nette maximale safety stop en % de la valeur d'entrée",
        default=0.0,
        group="V3.2 - Safety stop",
        default_start=0,
        default_end=20,
        default_step=1,
        active_if={"use_safety_stop": True, "safety_max_net_loss_mode": "% of entry value"},
    ),
    "early_stop_drawdown_pct": StrategyParameterDefinition(
        name="early_stop_drawdown_pct",
        kind="numeric",
        value_type="float",
        description="Phase 2 Optimization: Max peak-to-trough equity drawdown % before early abort",
        default=50.0,
        group="Optimization Engine",
        default_start=10,
        default_end=90,
        default_step=10,
    ),
    "safety_max_bars_in_trade": StrategyParameterDefinition(
        name="safety_max_bars_in_trade",
        kind="numeric",
        value_type="int",
        description="Nombre maximal de barres en position pour le safety stop (0 = désactivé)",
        default=0,
        group="V3.2 - Safety stop",
        default_start=0,
        default_end=50,
        default_step=5,
        active_if={"use_safety_stop": True},
    ),
    "point_value": StrategyParameterDefinition(
        name="point_value",
        kind="numeric",
        value_type="float",
        description="Valeur du point/contrat",
        default=1.0,
        group="Execution assumptions",
        default_start=1,
        default_end=1,
        default_step=1,
        optimizable=False,
    ),
    "execute_on_next_bar": StrategyParameterDefinition(
        name="execute_on_next_bar",
        kind="bool",
        value_type="bool",
        description="Exécuter les ordres au prochain open pour approximer process_orders_on_close=false",
        default=True,
        group="Execution assumptions",
        choices=["true", "false"],
    ),
    "next_bar_execution_price_col": StrategyParameterDefinition(
        name="next_bar_execution_price_col",
        kind="choice",
        value_type="str",
        description="Colonne utilisée comme prix d'exécution next-bar",
        default="open",
        group="Execution assumptions",
        choices=["open", "high", "low", "close"],
    ),
    "apply_estimated_costs_to_realized_pnl": StrategyParameterDefinition(
        name="apply_estimated_costs_to_realized_pnl",
        kind="bool",
        value_type="bool",
        description="Déduire les coûts estimés du PnL réalisé local",
        default=True,
        group="Execution assumptions",
        choices=["true", "false"],
    ),
    "allow_fractional_quantity": StrategyParameterDefinition(
        name="allow_fractional_quantity",
        kind="bool",
        value_type="bool",
        description="Autoriser les fractions d'actions",
        default=True,
        group="Execution assumptions",
        choices=["true", "false"],
    ),
    "quantity_precision": StrategyParameterDefinition(
        name="quantity_precision",
        kind="numeric",
        value_type="int",
        description="Précision d'arrondi des quantités fractionnaires",
        default=6,
        group="Execution assumptions",
        default_start=0,
        default_end=6,
        default_step=1,
    ),
}


def get_v3_parameters(
    *,
    exclude: list[str] | None = None,
    overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, StrategyParameterDefinition]:
    """Helper to return V3 parameters with exclusions and specific dataclass overrides."""
    exclude_set = set(exclude or [])
    res: dict[str, StrategyParameterDefinition] = {}
    for name, param in COMMON_V3_PARAMETERS.items():
        if name in exclude_set:
            continue
        if overrides and name in overrides:
            param = replace(param, **overrides[name])
        res[name] = param
    return res


# HMA crossover parameter definitions
HMA_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "fast_len": StrategyParameterDefinition(
        name="fast_len",
        kind="numeric",
        value_type="int",
        description="Longueur de la HMA rapide",
        default=20,
        group="Indicator",
        default_start=5,
        default_end=30,
        default_step=5,
    ),
    "slow_len": StrategyParameterDefinition(
        name="slow_len",
        kind="numeric",
        value_type="int",
        description="Longueur de la HMA lente",
        default=55,
        group="Indicator",
        default_start=20,
        default_end=100,
        default_step=10,
    ),
    "source_col": StrategyParameterDefinition(
        name="source_col",
        kind="choice",
        value_type="str",
        description="Colonne de prix source utilisée par la HMA",
        default="close",
        group="Indicator",
        choices=["open", "high", "low", "close"],
    ),
    "confirm_on_close": StrategyParameterDefinition(
        name="confirm_on_close",
        kind="bool",
        value_type="bool",
        description="Confirmer les signaux à la clôture de bougie",
        default=True,
        group="Indicator",
        choices=["true", "false"],
    ),
    **get_v3_parameters(),
}


# Adaptive Volatility Trend parameter definitions
AVT_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "source": StrategyParameterDefinition(
        name="source",
        kind="choice",
        value_type="str",
        description="Source de prix pour l'indicateur adaptatif",
        default="close",
        group="Indicator",
        choices=["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"],
    ),
    "length": StrategyParameterDefinition(
        name="length",
        kind="numeric",
        value_type="int",
        description="Longueur de la moyenne mobile adaptative",
        default=21,
        group="Indicator",
        default_start=10,
        default_end=50,
        default_step=5,
    ),
    "atr_len": StrategyParameterDefinition(
        name="atr_len",
        kind="numeric",
        value_type="int",
        description="Longueur de l'ATR pour les bandes de volatilité",
        default=14,
        group="Indicator",
        default_start=7,
        default_end=28,
        default_step=7,
    ),
    "atr_mult": StrategyParameterDefinition(
        name="atr_mult",
        kind="numeric",
        value_type="float",
        description="Multiplicateur ATR pour les bandes",
        default=2.0,
        group="Indicator",
        default_start=1.0,
        default_end=4.0,
        default_step=0.5,
    ),
    "preset": StrategyParameterDefinition(
        name="preset",
        kind="choice",
        value_type="str",
        description="Préréglage de comportement de la stratégie",
        default="Default",
        group="Indicator",
        choices=["Conservative", "Default", "Aggressive", "Scalping"],
    ),
    "use_rsi_filter": StrategyParameterDefinition(
        name="use_rsi_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre RSI",
        default=True,
        group="Filters",
        choices=["true", "false"],
    ),
    "rsi_len": StrategyParameterDefinition(
        name="rsi_len",
        kind="numeric",
        value_type="int",
        description="Longueur du RSI",
        default=14,
        group="Filters",
        default_start=7,
        default_end=21,
        default_step=7,
        active_if={"use_rsi_filter": True},
    ),
    "rsi_overbought": StrategyParameterDefinition(
        name="rsi_overbought",
        kind="numeric",
        value_type="int",
        description="Seuil de surachat RSI",
        default=70,
        group="Filters",
        default_start=60,
        default_end=80,
        default_step=5,
        active_if={"use_rsi_filter": True},
    ),
    "rsi_oversold": StrategyParameterDefinition(
        name="rsi_oversold",
        kind="numeric",
        value_type="int",
        description="Seuil de survente RSI",
        default=30,
        group="Filters",
        default_start=20,
        default_end=40,
        default_step=5,
        active_if={"use_rsi_filter": True},
    ),
    "use_volume_filter": StrategyParameterDefinition(
        name="use_volume_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre de volume",
        default=True,
        group="Filters",
        choices=["true", "false"],
    ),
    "volume_ma_len": StrategyParameterDefinition(
        name="volume_ma_len",
        kind="numeric",
        value_type="int",
        description="Longueur de la moyenne de volume",
        default=20,
        group="Filters",
        default_start=10,
        default_end=50,
        default_step=10,
        active_if={"use_volume_filter": True},
    ),
    "volume_mult": StrategyParameterDefinition(
        name="volume_mult",
        kind="numeric",
        value_type="float",
        description="Multiplicateur de volume",
        default=1.5,
        group="Filters",
        default_start=0.5,
        default_end=3.0,
        default_step=0.2,
        active_if={"use_volume_filter": True},
    ),
    "efficiency_smoothing": StrategyParameterDefinition(
        name="efficiency_smoothing",
        kind="numeric",
        value_type="int",
        description="Lissage du ratio d'efficacité",
        default=5,
        group="Advanced",
        default_start=3,
        default_end=10,
        default_step=1,
    ),
    "min_signal_score": StrategyParameterDefinition(
        name="min_signal_score",
        kind="numeric",
        value_type="int",
        description="Score minimal pour confirmer un signal",
        default=40,
        group="Advanced",
        default_start=20,
        default_end=80,
        default_step=10,
    ),
    **get_v3_parameters(
        exclude=["execute_on_next_bar", "next_bar_execution_price_col"],
        overrides={
            "allow_fractional_quantity": {"optimizable": False},
            "quantity_precision": {"optimizable": False},
        },
    ),
}


# Range Filter parameter definitions
RANGE_FILTER_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "source_col": StrategyParameterDefinition(
        name="source_col",
        kind="choice",
        value_type="str",
        description="Colonne de prix source utilisée par le Range Filter",
        default="close",
        group="Indicator",
        choices=["open", "high", "low", "close"],
    ),
    "sampling_period": StrategyParameterDefinition(
        name="sampling_period",
        kind="numeric",
        value_type="int",
        description="Période d'échantillonnage pour le Range Filter",
        default=100,
        group="Indicator",
        default_start=50,
        default_end=200,
        default_step=10,
    ),
    "range_multiplier": StrategyParameterDefinition(
        name="range_multiplier",
        kind="numeric",
        value_type="float",
        description="Multiplicateur de range pour le Range Filter",
        default=3.0,
        group="Indicator",
        default_start=1.0,
        default_end=5.0,
        default_step=0.5,
    ),
    **get_v3_parameters(
        exclude=["execute_on_next_bar", "next_bar_execution_price_col"],
        overrides={
            "allow_fractional_quantity": {"optimizable": False},
            "quantity_precision": {"optimizable": False},
        },
    ),
}


# 3Commas Bot parameter definitions
THREECOMAS_BOT_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "long_trades": StrategyParameterDefinition(
        name="long_trades",
        kind="bool",
        value_type="bool",
        description="Activer les trades long",
        default=True,
        group="Trade variables",
    ),
    "short_trades": StrategyParameterDefinition(
        name="short_trades",
        kind="bool",
        value_type="bool",
        description="Activer les trades short",
        default=True,
        group="Trade variables",
    ),
    "use_limit": StrategyParameterDefinition(
        name="use_limit",
        kind="bool",
        value_type="bool",
        description="Utiliser une sortie limite",
        default=True,
        group="Trade variables",
    ),
    "trail_stop": StrategyParameterDefinition(
        name="trail_stop",
        kind="bool",
        value_type="bool",
        description="Utiliser le trailing stop ATR",
        default=False,
        group="Trade variables",
    ),
    "flip": StrategyParameterDefinition(
        name="flip",
        kind="bool",
        value_type="bool",
        description="Autoriser les trades de reversal",
        default=False,
        group="Trade variables",
    ),
    "set_max_drawdown": StrategyParameterDefinition(
        name="set_max_drawdown",
        kind="bool",
        value_type="bool",
        description="Activer la protection max drawdown",
        default=False,
        group="Trade variables",
    ),
    "rnr": StrategyParameterDefinition(
        name="rnr",
        kind="numeric",
        value_type="float",
        description="Ratio Reward:Risk",
        default=1.0,
        group="Risk Management",
        default_start=0.5,
        default_end=5.0,
        default_step=0.5,
    ),
    "risk_m": StrategyParameterDefinition(
        name="risk_m",
        kind="numeric",
        value_type="float",
        description="Multiplicateur de risque (ATR)",
        default=1.0,
        group="Risk Management",
        default_start=0.5,
        default_end=3.0,
        default_step=0.5,
    ),
    "swing_lookback": StrategyParameterDefinition(
        name="swing_lookback",
        kind="numeric",
        value_type="int",
        description="Lookback pour le swing high/low",
        default=5,
        group="Risk Management",
        default_start=1,
        default_end=20,
        default_step=2,
    ),
    "max_perc_dd": StrategyParameterDefinition(
        name="max_perc_dd",
        kind="numeric",
        value_type="float",
        description="Drawdown max autorisé (%)",
        default=20.0,
        group="Risk Management",
        default_start=5.0,
        default_end=50.0,
        default_step=5.0,
        active_if={"set_max_drawdown": True},
    ),
    "atr_len": StrategyParameterDefinition(
        name="atr_len",
        kind="numeric",
        value_type="int",
        description="Période de l'ATR",
        default=14,
        group="Risk Management",
        default_start=5,
        default_end=50,
        default_step=5,
    ),
    "trail_stop_size": StrategyParameterDefinition(
        name="trail_stop_size",
        kind="numeric",
        value_type="float",
        description="Multiplicateur ATR pour le trailing stop",
        default=1.0,
        group="Trailing Stop",
        default_start=0.5,
        default_end=3.0,
        default_step=0.5,
        active_if={"trail_stop": True},
    ),
    "rr_exit": StrategyParameterDefinition(
        name="rr_exit",
        kind="numeric",
        value_type="float",
        description="R:R pour déclencher le trailing stop",
        default=0.0,
        group="Trailing Stop",
        default_start=0.0,
        default_end=2.0,
        default_step=0.25,
        active_if={"trail_stop": True},
    ),
    "ma_type1": StrategyParameterDefinition(
        name="ma_type1",
        kind="choice",
        value_type="str",
        description="Type de la MA 1",
        default="EMA",
        group="MA Type",
        choices=["EMA", "HEMA", "SMA", "HMA", "WMA", "DEMA", "VWMA", "VWAP", "T3"],
    ),
    "ma_type2": StrategyParameterDefinition(
        name="ma_type2",
        kind="choice",
        value_type="str",
        description="Type de la MA 2",
        default="EMA",
        group="MA Type",
        choices=["EMA", "HEMA", "SMA", "HMA", "WMA", "DEMA", "VWMA", "VWAP", "T3"],
    ),
    "ma_length1": StrategyParameterDefinition(
        name="ma_length1",
        kind="numeric",
        value_type="int",
        description="Longueur de la MA 1",
        default=21,
        group="MA Settings",
        default_start=5,
        default_end=100,
        default_step=5,
    ),
    "ma_length2": StrategyParameterDefinition(
        name="ma_length2",
        kind="numeric",
        value_type="int",
        description="Longueur de la MA 2",
        default=50,
        group="MA Settings",
        default_start=10,
        default_end=200,
        default_step=10,
    ),
    **get_v3_parameters(
        overrides={
            "early_stop_drawdown_pct": {"default": None, "optimizable": False},
            "allow_fractional_quantity": {"optimizable": False},
            "quantity_precision": {"optimizable": False},
        }
    ),
}


# PMax Explorer parameter definitions
PMAX_EXPLORER_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "periods": StrategyParameterDefinition(
        name="periods",
        kind="numeric",
        value_type="int",
        description="ATR Length",
        default=10,
        group="Indicator",
        default_start=5,
        default_end=50,
        default_step=5,
    ),
    "multiplier": StrategyParameterDefinition(
        name="multiplier",
        kind="numeric",
        value_type="float",
        description="ATR Multiplier",
        default=3.0,
        group="Indicator",
        default_start=1.0,
        default_end=10.0,
        default_step=0.5,
    ),
    "mav": StrategyParameterDefinition(
        name="mav",
        kind="choice",
        value_type="str",
        description="Moving Average Type",
        default="EMA",
        group="Indicator",
        choices=["SMA", "EMA", "WMA", "TMA", "VAR", "WWMA", "ZLEMA", "TSF"],
    ),
    "length": StrategyParameterDefinition(
        name="length",
        kind="numeric",
        value_type="int",
        description="Moving Average Length",
        default=10,
        group="Indicator",
        default_start=5,
        default_end=50,
        default_step=5,
    ),
    "change_atr": StrategyParameterDefinition(
        name="change_atr",
        kind="bool",
        value_type="bool",
        description="Change ATR Calculation Method ?",
        default=True,
        group="Indicator",
        choices=["true", "false"],
    ),
    "source_col": StrategyParameterDefinition(
        name="source_col",
        kind="choice",
        value_type="str",
        description="Source Column",
        default="hl2",
        group="Indicator",
        choices=["open", "high", "low", "close", "hl2"],
    ),
    **get_v3_parameters(
        exclude=[
            "execute_on_next_bar",
            "next_bar_execution_price_col",
            "allow_fractional_quantity",
            "apply_estimated_costs_to_realized_pnl",
            "quantity_precision",
        ]
    ),
}


# Bjorgum Double Tap parameter definitions
BJORGUM_TAP_PARAMETER_DEFINITIONS = {
    "dLong": StrategyParameterDefinition(
        name="dLong",
        kind="bool",
        value_type="bool",
        description="Detect long setups.",
        default=True,
        group="Detection and Trade Parameters",
    ),
    "dShort": StrategyParameterDefinition(
        name="dShort",
        kind="bool",
        value_type="bool",
        description="Detect short setups.",
        default=True,
        group="Detection and Trade Parameters",
    ),
    "FLIP": StrategyParameterDefinition(
        name="FLIP",
        kind="bool",
        value_type="bool",
        description="Allow entry in the opposite bias while already in a position.",
        default=True,
        group="Detection and Trade Parameters",
    ),
    "tol": StrategyParameterDefinition(
        name="tol",
        kind="numeric",
        value_type="float",
        description="The difference in height allowable for the signifcant points.",
        default=15.0,
        group="Detection and Trade Parameters",
        default_start=5.0,
        default_end=30.0,
        default_step=5.0,
    ),
    "length": StrategyParameterDefinition(
        name="length",
        kind="numeric",
        value_type="int",
        description="The length used to calcuate significant points.",
        default=50,
        group="Detection and Trade Parameters",
        default_start=10,
        default_end=100,
        default_step=10,
    ),
    "fib": StrategyParameterDefinition(
        name="fib",
        kind="numeric",
        value_type="float",
        description="The fib target extension projected from the neckline.",
        default=100.0,
        group="Detection and Trade Parameters",
        default_start=50.0,
        default_end=200.0,
        default_step=50.0,
    ),
    "stopPer": StrategyParameterDefinition(
        name="stopPer",
        kind="numeric",
        value_type="float",
        description="The fib extension of the pattern height measured from the point of invalidation.",
        default=0.0,
        group="Detection and Trade Parameters",
        default_start=0.0,
        default_end=100.0,
        default_step=10.0,
    ),
    "offset": StrategyParameterDefinition(
        name="offset",
        kind="numeric",
        value_type="int",
        description="The number of bars lines are extended into the future during an ongoing pattern.",
        default=30,
        group="Detection and Trade Parameters",
    ),
    "atrStop": StrategyParameterDefinition(
        name="atrStop",
        kind="bool",
        value_type="bool",
        description="Enables an ATR trailing stop once the target extension is breached.",
        default=False,
        group="Trailing Stop Parameters",
    ),
    "atrLength": StrategyParameterDefinition(
        name="atrLength",
        kind="numeric",
        value_type="int",
        description="The number of bars used in the ATR calculation.",
        default=14,
        group="Trailing Stop Parameters",
        default_start=7,
        default_end=21,
        default_step=7,
    ),
    "atrMult": StrategyParameterDefinition(
        name="atrMult",
        kind="numeric",
        value_type="float",
        description="The multiplier of the ATR value to subtract from the swing point.",
        default=1.0,
        group="Trailing Stop Parameters",
        default_start=1.0,
        default_end=3.0,
        default_step=0.5,
    ),
    "lookback": StrategyParameterDefinition(
        name="lookback",
        kind="numeric",
        value_type="int",
        description="The number of bars to look back to find a swing high or swing low.",
        default=5,
        group="Trailing Stop Parameters",
        default_start=3,
        default_end=15,
        default_step=2,
    ),
}

BJORGUM_DOUBLE_TAP_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    **BJORGUM_TAP_PARAMETER_DEFINITIONS,
    **get_v3_parameters(),
}


# Noise Boundary Intraday parameter definitions
NOISE_BOUNDARY_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "lookback_days": StrategyParameterDefinition(
        name="lookback_days",
        kind="numeric",
        value_type="int",
        description="Fenêtre de volatilité (jours)",
        default=20,
        group="Indicator",
        default_start=1,
        default_end=60,
        default_step=1,
    ),
    "volatility_multiplier_enter": StrategyParameterDefinition(
        name="volatility_multiplier_enter",
        kind="numeric",
        value_type="float",
        description="Multiplicateur bande d'entrée",
        default=2.0,
        group="Indicator",
        default_start=0.3,
        default_end=3.0,
        default_step=0.1,
    ),
    "volatility_multiplier_exit": StrategyParameterDefinition(
        name="volatility_multiplier_exit",
        kind="numeric",
        value_type="float",
        description="Multiplicateur bande de sortie",
        default=1.0,
        group="Indicator",
        default_start=0.1,
        default_end=3.0,
        default_step=0.1,
    ),
    "target_daily_volatility": StrategyParameterDefinition(
        name="target_daily_volatility",
        kind="numeric",
        value_type="float",
        description="Volatilité cible pour le sizing (Target Vol)",
        default=0.01,
        group="Indicator",
        default_start=0.001,
        default_end=0.1,
        default_step=0.001,
    ),
    "start_trade_after_open_minutes": StrategyParameterDefinition(
        name="start_trade_after_open_minutes",
        kind="numeric",
        value_type="int",
        description="Délai après l'ouverture (min)",
        default=15,
        group="Indicator",
        default_start=1,
        default_end=90,
        default_step=1,
    ),
    "trade_frequency_bars": StrategyParameterDefinition(
        name="trade_frequency_bars",
        kind="numeric",
        value_type="int",
        description="Fréquence max d'entrée (barres)",
        default=None,
        group="Indicator",
        default_start=1,
        default_end=20,
        default_step=1,
    ),
    "entry_on_high_low": StrategyParameterDefinition(
        name="entry_on_high_low",
        kind="bool",
        value_type="bool",
        description="Déclencher l'entrée sur high/low au lieu du close",
        default=False,
        group="Indicator",
        choices=["true", "false"],
    ),
    "allow_overnight": StrategyParameterDefinition(
        name="allow_overnight",
        kind="bool",
        value_type="bool",
        description="Autoriser le portage des positions overnight (swing)",
        default=False,
        group="Indicator",
        choices=["true", "false"],
    ),
    "use_vwap_filter": StrategyParameterDefinition(
        name="use_vwap_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre VWAP à l'entrée",
        default=True,
        group="Indicator",
        choices=["true", "false"],
    ),
    "exit_trades_before_close_minutes": StrategyParameterDefinition(
        name="exit_trades_before_close_minutes",
        kind="numeric",
        value_type="int",
        description="Sortie avant clôture (min)",
        default=15,
        group="Indicator",
        default_start=11,
        default_end=90,
        default_step=1,
    ),
    "exit_mode": StrategyParameterDefinition(
        name="exit_mode",
        kind="choice",
        value_type="str",
        description="Mode de sortie avancée",
        default="time_only",
        group="Exits",
        choices=["time_only", "vwap", "ladder", "combined"],
    ),
    "stoploss_ladder_step0": StrategyParameterDefinition(
        name="stoploss_ladder_step0",
        kind="numeric",
        value_type="float",
        description="Ladder SL seuil 1",
        default=-0.008,
        group="Exits",
        default_start=-0.02,
        default_end=-0.002,
        default_step=0.001,
    ),
    "stoploss_ladder_step1": StrategyParameterDefinition(
        name="stoploss_ladder_step1",
        kind="numeric",
        value_type="float",
        description="Ladder SL seuil 2",
        default=-0.015,
        group="Exits",
        default_start=-0.03,
        default_end=-0.005,
        default_step=0.001,
    ),
    "stoploss_ladder_ratio0": StrategyParameterDefinition(
        name="stoploss_ladder_ratio0",
        kind="numeric",
        value_type="float",
        description="Ladder SL ratio taille fermée à seuil 1",
        default=0.5,
        group="Exits",
        default_start=0.1,
        default_end=0.9,
        default_step=0.1,
    ),
    "takeprofit_ladder_step0": StrategyParameterDefinition(
        name="takeprofit_ladder_step0",
        kind="numeric",
        value_type="float",
        description="Ladder TP seuil 1",
        default=0.012,
        group="Exits",
        default_start=0.005,
        default_end=0.03,
        default_step=0.001,
    ),
    **get_v3_parameters(),
}


# Cybernetic Hilbert Transform parameter definitions (Ehlers' signal processing)
CYBERNETIC_HILBERT_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "hilbert_smooth_period": StrategyParameterDefinition(
        name="hilbert_smooth_period",
        kind="numeric",
        value_type="int",
        description="WMA smoothing factor for the detrending stage of the Hilbert Transform",
        default=7,
        group="Indicator",
        default_start=4,
        default_end=20,
        default_step=1,
    ),
    "phase_mode_enabled": StrategyParameterDefinition(
        name="phase_mode_enabled",
        kind="bool",
        value_type="bool",
        description="Enable cycling/trending phase mode filter (only trade in Cycling regime)",
        default=True,
        group="Indicator",
        choices=["true", "false"],
    ),
    "require_cycling_bars": StrategyParameterDefinition(
        name="require_cycling_bars",
        kind="numeric",
        value_type="int",
        description="Minimum consecutive cycling bars required before entry signal is valid",
        default=1,
        group="Indicator",
        default_start=1,
        default_end=5,
        default_step=1,
    ),
    **get_v3_parameters(),
}


# Smart Trader Geometric parameter definitions
SMART_TRADER_GEOMETRIC_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "signal_mode": StrategyParameterDefinition(
        name="signal_mode",
        kind="choice",
        value_type="str",
        description="Mode de signalisation",
        default="Close",
        group="Indicator",
        choices=["Close", "Live"],
    ),
    "lookback_period": StrategyParameterDefinition(
        name="lookback_period",
        kind="numeric",
        value_type="int",
        description="Période de lookback pour l'ICS",
        default=23,
        group="Indicator",
        default_start=10,
        default_end=50,
        default_step=1,
    ),
    "min_long_entry_slots": StrategyParameterDefinition(
        name="min_long_entry_slots",
        kind="numeric",
        value_type="int",
        description="Minimum slots requis pour Long Entry",
        default=1,
        group="Quorum Logic",
        default_start=1,
        default_end=10,
        default_step=1,
    ),
    "min_short_entry_slots": StrategyParameterDefinition(
        name="min_short_entry_slots",
        kind="numeric",
        value_type="int",
        description="Minimum slots requis pour Short Entry",
        default=1,
        group="Quorum Logic",
        default_start=1,
        default_end=10,
        default_step=1,
    ),
    **get_v3_parameters(),
}


# Lorentzian Classification ML parameter definitions
LORENTZIAN_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "neighbors_count": StrategyParameterDefinition(
        name="neighbors_count",
        kind="numeric",
        value_type="int",
        description="Nombre de voisins K pour le KNN",
        default=8,
        group="ML",
        default_start=4,
        default_end=16,
        default_step=2,
    ),
    "max_bars_back": StrategyParameterDefinition(
        name="max_bars_back",
        kind="numeric",
        value_type="int",
        description="Profondeur historique maximale pour la recherche KNN",
        default=2000,
        group="ML",
        default_start=500,
        default_end=2000,
        default_step=500,
    ),
    "feature_count": StrategyParameterDefinition(
        name="feature_count",
        kind="numeric",
        value_type="int",
        description="Nombre de features (2-5)",
        default=5,
        group="ML",
        default_start=2,
        default_end=5,
        default_step=1,
    ),
    "f1_param_a": StrategyParameterDefinition(
        name="f1_param_a",
        kind="numeric",
        value_type="int",
        description="Feature 1 (RSI) longueur",
        default=14,
        group="Features",
        default_start=7,
        default_end=21,
        default_step=7,
    ),
    "f1_param_b": StrategyParameterDefinition(
        name="f1_param_b",
        kind="numeric",
        value_type="int",
        description="Feature 1 (RSI) lissage EMA",
        default=1,
        group="Features",
        default_start=1,
        default_end=5,
        default_step=1,
    ),
    "f2_param_a": StrategyParameterDefinition(
        name="f2_param_a",
        kind="numeric",
        value_type="int",
        description="Feature 2 (WaveTrend) longueur canal",
        default=10,
        group="Features",
        default_start=5,
        default_end=15,
        default_step=5,
    ),
    "f2_param_b": StrategyParameterDefinition(
        name="f2_param_b",
        kind="numeric",
        value_type="int",
        description="Feature 2 (WaveTrend) longueur moyenne",
        default=11,
        group="Features",
        default_start=5,
        default_end=21,
        default_step=2,
    ),
    "f3_param_a": StrategyParameterDefinition(
        name="f3_param_a",
        kind="numeric",
        value_type="int",
        description="Feature 3 (CCI) longueur",
        default=20,
        group="Features",
        default_start=10,
        default_end=30,
        default_step=5,
    ),
    "f3_param_b": StrategyParameterDefinition(
        name="f3_param_b",
        kind="numeric",
        value_type="int",
        description="Feature 3 (CCI) lissage EMA",
        default=1,
        group="Features",
        default_start=1,
        default_end=5,
        default_step=1,
    ),
    "f4_param_a": StrategyParameterDefinition(
        name="f4_param_a",
        kind="numeric",
        value_type="int",
        description="Feature 4 (ADX) longueur",
        default=20,
        group="Features",
        default_start=10,
        default_end=30,
        default_step=5,
    ),
    "f4_param_b": StrategyParameterDefinition(
        name="f4_param_b",
        kind="numeric",
        value_type="int",
        description="Feature 4 (ADX) paramètre secondaire",
        default=2,
        group="Features",
        default_start=1,
        default_end=5,
        default_step=1,
    ),
    "f5_param_a": StrategyParameterDefinition(
        name="f5_param_a",
        kind="numeric",
        value_type="int",
        description="Feature 5 (RSI2) longueur",
        default=9,
        group="Features",
        default_start=5,
        default_end=14,
        default_step=1,
    ),
    "f5_param_b": StrategyParameterDefinition(
        name="f5_param_b",
        kind="numeric",
        value_type="int",
        description="Feature 5 (RSI2) lissage EMA",
        default=1,
        group="Features",
        default_start=1,
        default_end=5,
        default_step=1,
    ),
    "use_volatility_filter": StrategyParameterDefinition(
        name="use_volatility_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre de volatilité",
        default=True,
        group="Filters",
        choices=["true", "false"],
    ),
    "use_regime_filter": StrategyParameterDefinition(
        name="use_regime_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre de régime",
        default=True,
        group="Filters",
        choices=["true", "false"],
    ),
    "regime_threshold": StrategyParameterDefinition(
        name="regime_threshold",
        kind="numeric",
        value_type="float",
        description="Seuil du filtre de régime",
        default=-0.1,
        group="Filters",
        default_start=-0.5,
        default_end=0.0,
        default_step=0.1,
    ),
    "use_adx_filter": StrategyParameterDefinition(
        name="use_adx_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre ADX",
        default=False,
        group="Filters",
        choices=["true", "false"],
    ),
    "adx_threshold": StrategyParameterDefinition(
        name="adx_threshold",
        kind="numeric",
        value_type="int",
        description="Seuil du filtre ADX",
        default=20,
        group="Filters",
        default_start=15,
        default_end=30,
        default_step=5,
    ),
    "use_ema_filter": StrategyParameterDefinition(
        name="use_ema_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre EMA tendance",
        default=False,
        group="Filters",
        choices=["true", "false"],
    ),
    "ema_period": StrategyParameterDefinition(
        name="ema_period",
        kind="numeric",
        value_type="int",
        description="Période EMA pour filtre de tendance",
        default=200,
        group="Filters",
        default_start=50,
        default_end=200,
        default_step=50,
    ),
    "use_sma_filter": StrategyParameterDefinition(
        name="use_sma_filter",
        kind="bool",
        value_type="bool",
        description="Activer le filtre SMA tendance",
        default=False,
        group="Filters",
        choices=["true", "false"],
    ),
    "sma_period": StrategyParameterDefinition(
        name="sma_period",
        kind="numeric",
        value_type="int",
        description="Période SMA pour filtre de tendance",
        default=200,
        group="Filters",
        default_start=50,
        default_end=200,
        default_step=50,
    ),
    "use_kernel_filter": StrategyParameterDefinition(
        name="use_kernel_filter",
        kind="bool",
        value_type="bool",
        description="Trader avec la régression kernel",
        default=True,
        group="Kernel",
        choices=["true", "false"],
    ),
    "kernel_h": StrategyParameterDefinition(
        name="kernel_h",
        kind="numeric",
        value_type="int",
        description="Fenêtre de lookback du kernel",
        default=8,
        group="Kernel",
        default_start=4,
        default_end=16,
        default_step=2,
    ),
    "kernel_r": StrategyParameterDefinition(
        name="kernel_r",
        kind="numeric",
        value_type="float",
        description="Poids relatif du kernel",
        default=8.0,
        group="Kernel",
        default_start=4.0,
        default_end=16.0,
        default_step=2.0,
    ),
    "kernel_x": StrategyParameterDefinition(
        name="kernel_x",
        kind="numeric",
        value_type="int",
        description="Niveau de régression kernel",
        default=25,
        group="Kernel",
        default_start=10,
        default_end=50,
        default_step=5,
    ),
    "kernel_lag": StrategyParameterDefinition(
        name="kernel_lag",
        kind="numeric",
        value_type="int",
        description="Décalage kernel pour détection de croisement",
        default=2,
        group="Kernel",
        default_start=1,
        default_end=5,
        default_step=1,
    ),
    "use_kernel_smoothing": StrategyParameterDefinition(
        name="use_kernel_smoothing",
        kind="bool",
        value_type="bool",
        description="Activer le lissage kernel amélioré",
        default=False,
        group="Kernel",
        choices=["true", "false"],
    ),
    "use_dynamic_exits": StrategyParameterDefinition(
        name="use_dynamic_exits",
        kind="bool",
        value_type="bool",
        description="Utiliser les sorties dynamiques basées sur le kernel",
        default=False,
        group="Exits",
        choices=["true", "false"],
    ),
    **get_v3_parameters(),
}

TREND_TYPE_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "use_atr": StrategyParameterDefinition(
        name="use_atr",
        kind="bool",
        value_type="bool",
        description="use_atr parameter",
        default=True,
        group="Indicator",
    ),
    "atr_len": StrategyParameterDefinition(
        name="atr_len",
        kind="numeric",
        value_type="int",
        description="atr_len parameter",
        default=14,
        group="Indicator",
    ),
    "atr_ma_len": StrategyParameterDefinition(
        name="atr_ma_len",
        kind="numeric",
        value_type="int",
        description="atr_ma_len parameter",
        default=20,
        group="Indicator",
    ),
    "use_adx": StrategyParameterDefinition(
        name="use_adx",
        kind="bool",
        value_type="bool",
        description="use_adx parameter",
        default=True,
        group="Indicator",
    ),
    "adx_len": StrategyParameterDefinition(
        name="adx_len",
        kind="numeric",
        value_type="int",
        description="adx_len parameter",
        default=14,
        group="Indicator",
    ),
    "di_len": StrategyParameterDefinition(
        name="di_len",
        kind="numeric",
        value_type="int",
        description="di_len parameter",
        default=14,
        group="Indicator",
    ),
    "adx_lim": StrategyParameterDefinition(
        name="adx_lim",
        kind="numeric",
        value_type="float",
        description="adx_lim parameter",
        default=25.0,
        group="Indicator",
    ),
    "smooth": StrategyParameterDefinition(
        name="smooth",
        kind="numeric",
        value_type="int",
        description="smooth parameter",
        default=3,
        group="Indicator",
    ),
    "signal_mode": StrategyParameterDefinition(
        name="signal_mode",
        kind="choice",
        value_type="str",
        description="signal_mode parameter",
        default="Close",
        group="Indicator",
        choices=["Close", "Live"],
    ),
    **get_v3_parameters(),
}

MSL_TREND_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "length": StrategyParameterDefinition(
        name="length",
        kind="numeric",
        value_type="int",
        description="length parameter",
        default=70,
        group="Indicator",
    ),
    "mult": StrategyParameterDefinition(
        name="mult",
        kind="numeric",
        value_type="float",
        description="mult parameter",
        default=1.2,
        group="Indicator",
    ),
    "signal_mode": StrategyParameterDefinition(
        name="signal_mode",
        kind="choice",
        value_type="str",
        description="signal_mode parameter",
        default="Close",
        group="Indicator",
        choices=["Close", "Live"],
    ),
    **get_v3_parameters(),
}

PIVOT_RETEST_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "pivot_timeframe": StrategyParameterDefinition(
        name="pivot_timeframe",
        kind="choice",
        value_type="str",
        description="pivot_timeframe parameter",
        default="D",
        group="Indicator",
        choices=["D"],
    ),
    "retest_bars": StrategyParameterDefinition(
        name="retest_bars",
        kind="numeric",
        value_type="int",
        description="retest_bars parameter",
        default=5,
        group="Indicator",
    ),
    "signal_mode": StrategyParameterDefinition(
        name="signal_mode",
        kind="choice",
        value_type="str",
        description="signal_mode parameter",
        default="Close",
        group="Indicator",
        choices=["Close", "Live"],
    ),
    **get_v3_parameters(),
}

ADAPTIVE_TREND_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "La": StrategyParameterDefinition(
        name="La",
        kind="numeric",
        value_type="float",
        description="La parameter",
        default=0.02,
        group="Indicator",
    ),
    "De": StrategyParameterDefinition(
        name="De",
        kind="numeric",
        value_type="float",
        description="De parameter",
        default=0.03,
        group="Indicator",
    ),
    "cutout": StrategyParameterDefinition(
        name="cutout",
        kind="numeric",
        value_type="int",
        description="cutout parameter",
        default=0,
        group="Indicator",
    ),
    "robustness": StrategyParameterDefinition(
        name="robustness",
        kind="choice",
        value_type="str",
        description="robustness parameter",
        default="Medium",
        group="Indicator",
        choices=["Medium"],
    ),
    "Long_threshold": StrategyParameterDefinition(
        name="Long_threshold",
        kind="numeric",
        value_type="float",
        description="Long_threshold parameter",
        default=0.1,
        group="Indicator",
    ),
    "Short_threshold": StrategyParameterDefinition(
        name="Short_threshold",
        kind="numeric",
        value_type="float",
        description="Short_threshold parameter",
        default=-0.1,
        group="Indicator",
    ),
    "ema_len": StrategyParameterDefinition(
        name="ema_len",
        kind="numeric",
        value_type="int",
        description="ema_len parameter",
        default=28,
        group="Indicator",
    ),
    "ema_w": StrategyParameterDefinition(
        name="ema_w",
        kind="numeric",
        value_type="float",
        description="ema_w parameter",
        default=1.0,
        group="Indicator",
    ),
    "hull_len": StrategyParameterDefinition(
        name="hull_len",
        kind="numeric",
        value_type="int",
        description="hull_len parameter",
        default=28,
        group="Indicator",
    ),
    "hma_w": StrategyParameterDefinition(
        name="hma_w",
        kind="numeric",
        value_type="float",
        description="hma_w parameter",
        default=1.0,
        group="Indicator",
    ),
    "wma_len": StrategyParameterDefinition(
        name="wma_len",
        kind="numeric",
        value_type="int",
        description="wma_len parameter",
        default=28,
        group="Indicator",
    ),
    "wma_w": StrategyParameterDefinition(
        name="wma_w",
        kind="numeric",
        value_type="float",
        description="wma_w parameter",
        default=1.0,
        group="Indicator",
    ),
    "dema_len": StrategyParameterDefinition(
        name="dema_len",
        kind="numeric",
        value_type="int",
        description="dema_len parameter",
        default=28,
        group="Indicator",
    ),
    "dema_w": StrategyParameterDefinition(
        name="dema_w",
        kind="numeric",
        value_type="float",
        description="dema_w parameter",
        default=1.0,
        group="Indicator",
    ),
    "lsma_len": StrategyParameterDefinition(
        name="lsma_len",
        kind="numeric",
        value_type="int",
        description="lsma_len parameter",
        default=28,
        group="Indicator",
    ),
    "lsma_w": StrategyParameterDefinition(
        name="lsma_w",
        kind="numeric",
        value_type="float",
        description="lsma_w parameter",
        default=1.0,
        group="Indicator",
    ),
    "kama_len": StrategyParameterDefinition(
        name="kama_len",
        kind="numeric",
        value_type="int",
        description="kama_len parameter",
        default=28,
        group="Indicator",
    ),
    "kama_w": StrategyParameterDefinition(
        name="kama_w",
        kind="numeric",
        value_type="float",
        description="kama_w parameter",
        default=1.0,
        group="Indicator",
    ),
    "signal_mode": StrategyParameterDefinition(
        name="signal_mode",
        kind="choice",
        value_type="str",
        description="signal_mode parameter",
        default="Close",
        group="Indicator",
        choices=["Close", "Live"],
    ),
    **get_v3_parameters(),
}

MOMENTUM_ZIGZAG_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "rsi_period": StrategyParameterDefinition(
        name="rsi_period",
        kind="numeric",
        value_type="int",
        description="rsi_period parameter",
        default=14,
        group="Indicator",
    ),
    "qqe_factor": StrategyParameterDefinition(
        name="qqe_factor",
        kind="numeric",
        value_type="float",
        description="qqe_factor parameter",
        default=4.238,
        group="Indicator",
    ),
    "rsi_smoothing": StrategyParameterDefinition(
        name="rsi_smoothing",
        kind="numeric",
        value_type="int",
        description="rsi_smoothing parameter",
        default=5,
        group="Indicator",
    ),
    "ob": StrategyParameterDefinition(
        name="ob",
        kind="numeric",
        value_type="float",
        description="ob parameter",
        default=80.0,
        group="Indicator",
    ),
    "os": StrategyParameterDefinition(
        name="os",
        kind="numeric",
        value_type="float",
        description="os parameter",
        default=20.0,
        group="Indicator",
    ),
    "signal_mode": StrategyParameterDefinition(
        name="signal_mode",
        kind="choice",
        value_type="str",
        description="signal_mode parameter",
        default="Close",
        group="Indicator",
        choices=["Close", "Live"],
    ),
    "enable_stop_loss": StrategyParameterDefinition(
        name="enable_stop_loss",
        kind="bool",
        value_type="bool",
        description="enable_stop_loss parameter",
        default=False,
        group="Indicator",
    ),
    "stop_loss_pct": StrategyParameterDefinition(
        name="stop_loss_pct",
        kind="numeric",
        value_type="float",
        description="stop_loss_pct parameter",
        default=0.0,
        group="Indicator",
    ),
    "enable_take_profit": StrategyParameterDefinition(
        name="enable_take_profit",
        kind="bool",
        value_type="bool",
        description="enable_take_profit parameter",
        default=False,
        group="Indicator",
    ),
    "take_profit_pct": StrategyParameterDefinition(
        name="take_profit_pct",
        kind="numeric",
        value_type="float",
        description="take_profit_pct parameter",
        default=0.0,
        group="Indicator",
    ),
    "enable_trailing_stop": StrategyParameterDefinition(
        name="enable_trailing_stop",
        kind="bool",
        value_type="bool",
        description="enable_trailing_stop parameter",
        default=False,
        group="Indicator",
    ),
    "trail_profit_pct": StrategyParameterDefinition(
        name="trail_profit_pct",
        kind="numeric",
        value_type="float",
        description="trail_profit_pct parameter",
        default=0.0,
        group="Indicator",
    ),
    "trail_loss_pct": StrategyParameterDefinition(
        name="trail_loss_pct",
        kind="numeric",
        value_type="float",
        description="trail_loss_pct parameter",
        default=0.0,
        group="Indicator",
    ),
    "enable_pyramiding": StrategyParameterDefinition(
        name="enable_pyramiding",
        kind="bool",
        value_type="bool",
        description="enable_pyramiding parameter",
        default=False,
        group="Indicator",
    ),
    "max_pyramid_layers": StrategyParameterDefinition(
        name="max_pyramid_layers",
        kind="numeric",
        value_type="int",
        description="max_pyramid_layers parameter",
        default=1,
        group="Indicator",
    ),
    **get_v3_parameters(),
}

HMM_REGIME_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "obs_len": StrategyParameterDefinition(
        name="obs_len",
        kind="numeric",
        value_type="int",
        description="obs_len parameter",
        default=14,
        group="Indicator",
    ),
    "stat_len": StrategyParameterDefinition(
        name="stat_len",
        kind="numeric",
        value_type="int",
        description="stat_len parameter",
        default=28,
        group="Indicator",
    ),
    "mu_k": StrategyParameterDefinition(
        name="mu_k",
        kind="numeric",
        value_type="float",
        description="mu_k parameter",
        default=1.5,
        group="Indicator",
    ),
    "stick": StrategyParameterDefinition(
        name="stick",
        kind="numeric",
        value_type="float",
        description="stick parameter",
        default=0.9,
        group="Indicator",
    ),
    "confirm_bars": StrategyParameterDefinition(
        name="confirm_bars",
        kind="numeric",
        value_type="int",
        description="confirm_bars parameter",
        default=2,
        group="Indicator",
    ),
    "dom_thresh": StrategyParameterDefinition(
        name="dom_thresh",
        kind="numeric",
        value_type="float",
        description="dom_thresh parameter",
        default=0.5,
        group="Indicator",
    ),
    **get_v3_parameters(),
}


STRATEGY_PARAMETER_DEFINITIONS = {
    "hma_crossover": HMA_PARAMETER_DEFINITIONS,
    "pmax_explorer": PMAX_EXPLORER_PARAMETER_DEFINITIONS,
    "adaptive_volatility_trend": AVT_PARAMETER_DEFINITIONS,
    "range_filter": RANGE_FILTER_PARAMETER_DEFINITIONS,
    "3commas_bot": THREECOMAS_BOT_PARAMETER_DEFINITIONS,
    "bjorgum_double_tap": BJORGUM_DOUBLE_TAP_PARAMETER_DEFINITIONS,
    "noise_boundary_intraday": NOISE_BOUNDARY_PARAMETER_DEFINITIONS,
    "cybernetic_hilbert": CYBERNETIC_HILBERT_PARAMETER_DEFINITIONS,
    "smart_trader_geometric": SMART_TRADER_GEOMETRIC_PARAMETER_DEFINITIONS,
    "lorentzian_classification": LORENTZIAN_PARAMETER_DEFINITIONS,
    "trend_type": TREND_TYPE_PARAMETER_DEFINITIONS,
    "msl_trend": MSL_TREND_PARAMETER_DEFINITIONS,
    "pivot_retest": PIVOT_RETEST_PARAMETER_DEFINITIONS,
    "adaptive_trend_classification": ADAPTIVE_TREND_PARAMETER_DEFINITIONS,
    "momentum_based_zigzag": MOMENTUM_ZIGZAG_PARAMETER_DEFINITIONS,
    "hmm_regime_filter": HMM_REGIME_PARAMETER_DEFINITIONS,
}


DEFAULT_BACKTEST_PROPERTIES: dict[str, object] = {
    "base_currency": "Default",
    "initial_capital": 1000.0,
    "default_order_size": {"value": 100.0, "type": "percent_of_equity"},
    "pyramiding": 0,
    "commission": {"value": 0.0, "type": "percent"},
    "verify_price_for_limit_orders": 0,
    "slippage": 0.0,
    "margin_long": 100.0,
    "margin_short": 100.0,
    "early_stop_drawdown_pct": 50.0,
}


def normalize_backtest_properties(values: dict[str, object] | None = None) -> dict[str, object]:
    """Return TradingView-like backtest properties with a typed default order size.

    Older local configs stored ``default_order_size`` as a bare number. TradingView
    models it as a pair made of the value and sizing mode (e.g.
    ``percent_of_equity``). Keep backward compatibility by upgrading numeric
    values to the typed representation.
    """
    normalized = {**DEFAULT_BACKTEST_PROPERTIES, **(values or {})}
    default_order_size = normalized.get("default_order_size")
    if isinstance(default_order_size, dict):
        normalized["default_order_size"] = {
            "value": float(default_order_size.get("value", 100.0)),
            "type": str(default_order_size.get("type", "percent_of_equity")),
        }
    else:
        normalized["default_order_size"] = {
            "value": float(default_order_size if default_order_size is not None else 100.0),
            "type": "percent_of_equity",
        }
    commission = normalized.get("commission")
    if isinstance(commission, dict):
        normalized["commission"] = {
            "value": float(commission.get("value", 0.0)),
            "type": str(commission.get("type", "percent")),
        }
    else:
        normalized["commission"] = {
            "value": float(commission if commission is not None else 0.0),
            "type": "percent",
        }
    normalized["base_currency"] = str(normalized.get("base_currency") or "Default")
    normalized["early_stop_drawdown_pct"] = float(normalized.get("early_stop_drawdown_pct", 50.0))
    return normalized


def parameter_definitions(strategy: str = "hma_crossover", *, optimizable_only: bool = False) -> dict[str, StrategyParameterDefinition]:
    try:
        definitions = STRATEGY_PARAMETER_DEFINITIONS[strategy]
    except KeyError as exc:
        raise ValueError(f"Unsupported strategy: {strategy}") from exc
    if optimizable_only:
        return {name: definition for name, definition in definitions.items() if definition.optimizable}
    return definitions


def default_strategy_parameters(strategy: str = "hma_crossover") -> dict[str, object]:
    return {name: definition.default for name, definition in parameter_definitions(strategy).items() if definition.default is not None}


def coerce_parameter_value(strategy: str, name: str, value: object) -> object:
    definition = parameter_definitions(strategy).get(name)
    if definition is None:
        raise ValueError(f"Unsupported parameter for {strategy}: {name}")
    if value is None:
        return None
    if definition.value_type == "bool":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
        raise ValueError(f"Parameter {name} expects a boolean value, got {value!r}")
    if definition.value_type == "int":
        number = float(str(value).strip())
        if number != int(number):
            raise ValueError(f"Parameter {name} expects an integer value, got {value!r}")
        return int(number)
    if definition.value_type == "float":
        return float(str(value).strip())
    text = str(value)
    if definition.choices is not None and text not in definition.choices:
        raise ValueError(f"Invalid choice for {name}: {text!r}; allowed: {definition.choices}")
    return text


def coerce_strategy_parameters(strategy: str, values: dict[str, object], *, ignore_unknown: bool = False) -> dict[str, object]:
    coerced: dict[str, object] = {}
    definitions = parameter_definitions(strategy)
    for name, value in values.items():
        if value in (None, ""):
            continue
        if name not in definitions:
            if ignore_unknown:
                continue
            raise ValueError(f"Unsupported parameter for {strategy}: {name}")
        coerced[name] = coerce_parameter_value(strategy, name, value)
    return coerced


def load_strategy_config(path: str | Path, strategy: str | None = None) -> StrategyRuntimeConfig:
    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Strategy config must be a JSON object")
    config_strategy = str(payload.get("strategy") or strategy or "hma_crossover")
    if strategy is not None and config_strategy != strategy:
        raise ValueError(f"Config strategy {config_strategy!r} does not match requested strategy {strategy!r}")
    raw_parameters = payload.get("parameters") or {}
    if not isinstance(raw_parameters, dict):
        raise ValueError("Strategy config field 'parameters' must be an object")
    raw_backtest = payload.get("backtest") or {}
    if not isinstance(raw_backtest, dict):
        raise ValueError("Strategy config field 'backtest' must be an object")
    return StrategyRuntimeConfig(
        strategy=config_strategy,
        parameters=coerce_strategy_parameters(config_strategy, raw_parameters, ignore_unknown=True),
        backtest=normalize_backtest_properties(raw_backtest),
        source_path=str(config_path),
    )


def _base_values(strategy: str, values: dict[str, object]) -> dict[str, object]:
    base = default_strategy_parameters(strategy)
    base.update({key: value for key, value in values.items() if value is not None})
    return base


def inactive_parameter_names(strategy: str, values: dict[str, object]) -> set[str]:
    merged = _base_values(strategy, values)
    inactive: set[str] = set()

    if not bool(merged.get("use_net_bracket_exits", False)):
        inactive.update({"take_profit_net_percent", "stop_loss_net_percent"})

    if not bool(merged.get("use_safety_stop", True)):
        inactive.update(
            {
                "safety_stop_applies_to",
                "safety_stop_mode",
                "safety_max_net_loss_mode",
                "safety_max_net_loss_cash",
                "safety_max_net_loss_percent",
                "safety_max_bars_in_trade",
            }
        )
    else:
        safety_mode = merged.get("safety_stop_mode")
        if safety_mode == "Net loss only":
            inactive.add("safety_max_bars_in_trade")
        elif safety_mode == "Max bars only":
            inactive.update({"safety_max_net_loss_mode", "safety_max_net_loss_cash", "safety_max_net_loss_percent"})
        max_loss_mode = merged.get("safety_max_net_loss_mode")
        if max_loss_mode == "Cash amount":
            inactive.add("safety_max_net_loss_percent")
        elif max_loss_mode == "% of entry value":
            inactive.add("safety_max_net_loss_cash")

        direction = merged.get("trade_direction_mode")
        applies_to = merged.get("safety_stop_applies_to")
        if direction == "Long only" and applies_to == "Short only":
            inactive.update({"safety_stop_applies_to", "safety_stop_mode", "safety_max_net_loss_mode", "safety_max_net_loss_cash", "safety_max_net_loss_percent", "safety_max_bars_in_trade"})
        elif direction == "Short only" and applies_to == "Long only":
            inactive.update({"safety_stop_applies_to", "safety_stop_mode", "safety_max_net_loss_mode", "safety_max_net_loss_cash", "safety_max_net_loss_percent", "safety_max_bars_in_trade"})

    direction = merged.get("trade_direction_mode")
    if direction == "Long only":
        inactive.update({"estimated_commission_per_order_short", "estimated_slippage_per_side_short"})
    elif direction == "Short only":
        inactive.update({"estimated_commission_per_order_long", "estimated_slippage_per_side_long"})

    return inactive


def active_parameter_values(strategy: str, values: dict[str, object]) -> dict[str, object]:
    inactive = inactive_parameter_names(strategy, values)
    return {name: value for name, value in values.items() if name not in inactive}


def canonical_parameter_key(strategy: str, values: dict[str, object]) -> str:
    active = active_parameter_values(strategy, values)
    return json.dumps(active, sort_keys=True, default=str, ensure_ascii=False)
