# Smart Trader, Episode 1 | Unified Matrix - Implementation Brief

## Objective
Convert the Pine Script strategy "Smart Trader, Episode 1" to Python and integrate it into the existing backtesting engine.

## Core Mechanics
1. **Volume Engine (Split)**:
   - **Geometry Mode**: Approximates buy/sell volume using the candle body (open, high, low, close).
   - **Intrabar (Precise) Mode**: Relies on strict intrabar data validity.
2. **Rank Scanner**:
   - Slides over `universal_len` to identify Highest Buyers (HB), Highest Sellers (HS), Lowest Buyers (LB), Lowest Sellers (LS).
3. **PathTracker Attrition**:
   - Measures consumption of volume power (buyer/seller momentum) over time.
4. **Trend Channel**:
   - Performs a linear regression on 5 equal segments of the lookback window.
5. **Trade Signals**:
   - Generates signals (LONG, SHORT, NO_TRADE) based on power decay, cumulative delta, and post-event momentum.

## Target Files
1. `pine_scripts_convert_to_python/strategy/smart_trader_ep1.py`: Contains the standalone vectorized Python conversion of the Pine Script logic.
2. `backtest_engine/strategies/smart_trader_ep1.py`: The strategy class wrapper integrating with the BrokerSimulator.
3. `configs/strategies/smart_trader_ep1.default.json`: Default configuration for the strategy.
4. `tests/test_smart_trader_ep1.py`: Unit tests validating the mathematical calculations (e.g., volume split, rank scanner, linear regression) and the strategy execution.

## Requirements
- Full NumPy vectorization to eliminate O(N) loops.
- Compliance with `codingstandards.md`.
- No regressions on the existing engine.
