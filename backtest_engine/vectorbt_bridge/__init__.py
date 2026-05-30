"""VectorBT bridge for exploring complementarity with backtest_engine.

This package provides adapters to run backtest_engine strategies through
VectorBT's portfolio simulation, enabling comparison and potential enrichment.
"""

from .data_adapter import load_sheetsfinance_to_vectorbt
from .strategy_bridge import run_strategy_via_vectorbt, compare_results

__all__ = ["load_sheetsfinance_to_vectorbt", "run_strategy_via_vectorbt", "compare_results"]
