from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Type

from .strategies.hma_crossover import (
    HMAConfigOverrides,
    run_hma_crossover,
    load_hma_overrides_from_config,
    hma_overrides_from_mapping,
    clear_hma_feature_cache,
    vectorbt_prescan as hma_vectorbt_prescan,
)
from .strategies.pmax_explorer import (
    PMaxExplorerConfigOverrides,
    run_pmax_explorer,
    load_pmax_overrides_from_config,
    pmax_overrides_from_mapping,
    clear_pmax_explorer_feature_cache,
    vectorbt_prescan as pmax_vectorbt_prescan,
)
from .strategies.adaptive_volatility_trend import (
    AVTConfigOverrides,
    run_adaptive_volatility_trend,
    load_avt_overrides_from_config,
    avt_overrides_from_mapping,
    vectorbt_prescan as avt_vectorbt_prescan,
)
from .strategies.range_filter import (
    RangeFilterConfigOverrides,
    run_range_filter,
    load_rf_overrides_from_config,
    rf_overrides_from_mapping,
    clear_range_filter_feature_cache,
    vectorbt_prescan as range_filter_vectorbt_prescan,
)
from .strategies.commas_bot import (
    CommasBotConfigOverrides,
    run_3commas_bot,
    load_commas_bot_overrides_from_config,
    commas_bot_overrides_from_mapping,
    vectorbt_prescan as commas_bot_vectorbt_prescan,
)
from .strategies.bjorgum_double_tap import (
    BjorgumDoubleTapConfigOverrides,
    run_bjorgum_double_tap,
    load_bjorgum_double_tap_overrides_from_config,
    bjorgum_double_tap_overrides_from_mapping,
    clear_bjorgum_double_tap_feature_cache,
    vectorbt_prescan as bjorgum_vectorbt_prescan,
)
from .strategies.noise_boundary_intraday import (
    NoiseBoundaryConfigOverrides,
    run_noise_boundary_intraday,
    load_noise_boundary_overrides_from_config,
    noise_boundary_overrides_from_mapping,
    vectorbt_prescan as noise_boundary_vectorbt_prescan,
)
from .strategies.cybernetic_hilbert import (
    CyberneticHilbertConfigOverrides,
    run_cybernetic_hilbert,
    load_cybernetic_hilbert_overrides_from_config,
    cybernetic_hilbert_overrides_from_mapping,
    vectorbt_prescan as cybernetic_hilbert_vectorbt_prescan,
)
from .strategies.smart_trader_geometric import (
    SmartTraderGeometricConfigOverrides,
    run_smart_trader_geometric,
    load_smart_trader_geometric_overrides_from_config,
    smart_trader_geometric_overrides_from_mapping,
    vectorbt_prescan as stg_vectorbt_prescan,
)

@dataclass
class StrategyInfo:
    name: str
    config_override_class: Type[Any]
    run_function: Callable[..., Any]
    load_overrides_function: Callable[[Any], tuple[Any, dict[str, Any]]]
    overrides_from_mapping_function: Callable[[dict[str, Any] | None], Any]
    indicators: list[str]
    vectorbt_prescan: Callable[..., list[Any]] | None = None
    clear_feature_cache: Callable[[], None] | None = None


class StrategyRegistry:
    _registry: dict[str, StrategyInfo] = {}

    @classmethod
    def register(cls, info: StrategyInfo) -> None:
        cls._registry[info.name] = info

    @classmethod
    def get(cls, name: str) -> StrategyInfo:
        info = cls._registry.get(name)
        if info is None:
            raise ValueError(f"Strategy {name!r} is not registered in StrategyRegistry")
        return info

    @classmethod
    def all(cls) -> dict[str, StrategyInfo]:
        return dict(cls._registry)

    @classmethod
    def list_strategies(cls) -> list[str]:
        return list(cls._registry.keys())


# Static Registration of all 8 strategies
StrategyRegistry.register(
    StrategyInfo(
        name="hma_crossover",
        config_override_class=HMAConfigOverrides,
        run_function=run_hma_crossover,
        load_overrides_function=load_hma_overrides_from_config,
        overrides_from_mapping_function=hma_overrides_from_mapping,
        indicators=["hma_fast", "hma_slow"],
        vectorbt_prescan=hma_vectorbt_prescan,
        clear_feature_cache=clear_hma_feature_cache,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="pmax_explorer",
        config_override_class=PMaxExplorerConfigOverrides,
        run_function=run_pmax_explorer,
        load_overrides_function=load_pmax_overrides_from_config,
        overrides_from_mapping_function=pmax_overrides_from_mapping,
        indicators=["mavg", "pmax"],
        vectorbt_prescan=pmax_vectorbt_prescan,
        clear_feature_cache=clear_pmax_explorer_feature_cache,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="adaptive_volatility_trend",
        config_override_class=AVTConfigOverrides,
        run_function=run_adaptive_volatility_trend,
        load_overrides_function=load_avt_overrides_from_config,
        overrides_from_mapping_function=avt_overrides_from_mapping,
        indicators=["avt_adaptive_trend", "avt_upper_band", "avt_lower_band"],
        vectorbt_prescan=avt_vectorbt_prescan,
        clear_feature_cache=None,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="range_filter",
        config_override_class=RangeFilterConfigOverrides,
        run_function=run_range_filter,
        load_overrides_function=load_rf_overrides_from_config,
        overrides_from_mapping_function=rf_overrides_from_mapping,
        indicators=["rf_high", "rf_low", "rf_avg"],
        vectorbt_prescan=range_filter_vectorbt_prescan,
        clear_feature_cache=clear_range_filter_feature_cache,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="3commas_bot",
        config_override_class=CommasBotConfigOverrides,
        run_function=run_3commas_bot,
        load_overrides_function=load_commas_bot_overrides_from_config,
        overrides_from_mapping_function=commas_bot_overrides_from_mapping,
        indicators=["ma1", "ma2", "atr"],
        vectorbt_prescan=commas_bot_vectorbt_prescan,
        clear_feature_cache=None,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="bjorgum_double_tap",
        config_override_class=BjorgumDoubleTapConfigOverrides,
        run_function=run_bjorgum_double_tap,
        load_overrides_function=load_bjorgum_double_tap_overrides_from_config,
        overrides_from_mapping_function=bjorgum_double_tap_overrides_from_mapping,
        indicators=["sLow", "sHigh", "atr", "pattern_tp", "pattern_sl"],
        vectorbt_prescan=bjorgum_vectorbt_prescan,
        clear_feature_cache=clear_bjorgum_double_tap_feature_cache,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="noise_boundary_intraday",
        config_override_class=NoiseBoundaryConfigOverrides,
        run_function=run_noise_boundary_intraday,
        load_overrides_function=load_noise_boundary_overrides_from_config,
        overrides_from_mapping_function=noise_boundary_overrides_from_mapping,
        indicators=["upper_enter", "lower_enter", "upper_exit", "lower_exit", "daily_open"],
        vectorbt_prescan=noise_boundary_vectorbt_prescan,
        clear_feature_cache=None,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="cybernetic_hilbert",
        config_override_class=CyberneticHilbertConfigOverrides,
        run_function=run_cybernetic_hilbert,
        load_overrides_function=load_cybernetic_hilbert_overrides_from_config,
        overrides_from_mapping_function=cybernetic_hilbert_overrides_from_mapping,
        indicators=["sine_wave", "lead_wave", "phase_mode", "dominant_cycle"],
        vectorbt_prescan=cybernetic_hilbert_vectorbt_prescan,
        clear_feature_cache=None,
    )
)

StrategyRegistry.register(
    StrategyInfo(
        name="smart_trader_geometric",
        config_override_class=SmartTraderGeometricConfigOverrides,
        run_function=run_smart_trader_geometric,
        load_overrides_function=load_smart_trader_geometric_overrides_from_config,
        overrides_from_mapping_function=smart_trader_geometric_overrides_from_mapping,
        indicators=["Ceil distance", "Ctr distance", "Flr distance", "PnU distance", "PnD distance"],
        vectorbt_prescan=stg_vectorbt_prescan,
        clear_feature_cache=None,
    )
)

