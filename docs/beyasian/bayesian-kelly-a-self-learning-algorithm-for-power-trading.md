Sometimes I wonder if Ferris Bueller had power trading aspirations when he famously said: "Life moves pretty fast; if you don't stop and look around once in a while, you could miss it." Commodities markets, especially power markets, are notoriously volatile. What's the occasional 10% one-day spike on a $10MM position among friends?

But, maybe, Ferris simply hadn't met Kelly (see: "Hey Kelly, Optimize My Portfolio"). In this article, we'll revisit the Kelly criterion and enhance it with Bayesian principles, creating an adaptive algorithm that learns from market movements. I'll introduce a complete Python implementation for algorithmic trading in volatile markets like power futures, show you how it performs with sample outputs, and interpret the results - when things go well and when they don't. After all, whether called Kelly or Chester, no trading strategy is foolproof."

**Defining Priors**

The key feature of our algorithmic trader is its self-refining nature. We start with a hypothesis about the probability that a futures contract price will increase tomorrow. This hypothesis can be based on historical time series, technical analysis, or weather forecasts.

We express this probability using two parameters: α and β, where α / (α + β) represents the probability of tomorrow's price increasing. So, if you expect a 20% chance of prices rising tomorrow, you might start with α = 1 and β = 4, since 1 / (1 + 4) = 20%. This gives us p = 0.20 and q = 1 - p = 0.80 in our beloved Kelly equation:

f* = (p × b - q × L) / (b × L)

With q being much larger than p, Kelly will likely recommend aggressively shorting the underlying asset on day one (remember: never go Full Kelly!).

So what makes this Bayesian? As new daily price data arrives - each day classified simply as "up" or "down" - we incrementally update our parameters:

*   **Up-day:** α → α + 1
*   **Down-day:** β → β + 1

For example: if prices increase, we revise α to 2, and our probability of an upward move becomes 2 / (2 + 4) = 33%. That's quite a jump from 20%, but it's expected: as we gather more data, this ratio gradually converges to its long-run value.

**Putting it to Work**

Now for the fun part: the algo trader! We'll start by breaking down each part of the program in order of dependency. The full code is available at the bottom of the article.

**PriceData (dataclass)**

This is a simple immutable container that encapsulates everything we need to know about a price series. I've chosen the `frozen=True` attribute to make instances immutable (once created, they can't be modified). This is a defensive programming practice that prevents unexpected changes to our data.

While the `prices` array is the only required field, including optional `dates` and `symbol` fields makes the data more self-documenting and facilitates working with multiple assets. The immutability ensures that our backtesting is reliable and reproducible - once loaded, the price data won't accidentally change during analysis.

```python
@dataclass(frozen=True)
class PriceData:
    """Immutable container for price data."""
    prices: np.ndarray
    dates: Optional[np.ndarray] = None
    symbol: Optional[str] = None
```

**TradeResult (dataclass)**

This class captures the essential information for each completed trade. By recording both the entry and exit prices alongside the position size, we're able to reconstruct the trade and verify the calculated gain or loss.

Again, immutability is key here: trade results should be a matter of record, not subject to change after the fact. This helps maintain an audit trail for post-analysis, and helps us avoid the "I would have made more if only had I ..." trap that so many traders fall into. Each `TradeResult` instance is an immutable record of what actually happened, not what we wish had happened or what we remember happening.

```python
@dataclass(frozen=True)
class TradeResult:
    """Immutable container for a single trade result."""
    entry_price: float
    exit_price: float
    position_size: float
    gain_loss: float
```

**PerformanceMetrics (dataclass)**

This distills the entire trading simulation into the key metrics that matter to traders and portfolio managers. While there are dozens of possible metrics we could track, I've focused on the handful that provide the most insight:

*   **Final capital and total return:** tell us the bottom-line performance
*   **Sharpe Ratio** balances returns against risk
*   **Maximum drawdown** reveals the worst-case scenario we experienced
*   **Win rate** indicates how often our predictions were correct
*   **Trades count** puts everything in context - was this performance based on 10 trades or 1,000?

These metrics tell a complete story about the trading strategy without overwhelming the user with information. The immutability ensures that our performance reports remain consistent across different analyses.

```python
@dataclass(frozen=True)
class PerformanceMetrics:
    """Immutable container for trading performance metrics."""
    final_capital: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    trades_count: int
```

**BayesianKellyTrader (dataclass)**

This is the heart of our implementation, bringing together Bayesian inference and Kelly criterion position sizing. Unlike the other classes, this one is mutable, evolving as it learns from market data.

The α and β parameters start with our prior beliefs about market direction, but they'll adapt over time. With equal initial values of 1.0, we're starting from a position of maximum uncertainty (a uniform prior), but we can adjust them based on existing market knowledge.

The `expected_gain` and `expected_loss` parameters represent our assumptions about the magnitude of price moves, while the `kelly_fraction` parameter acts as a safety mechanism. Even when Kelly gives us high conviction, limiting ourselves to a fraction of the recommended position size (typically 0.25 to 0.50) helps manage risk. This is our implementation of the trader's maxim: "Never go Full Kelly!"

```python
@dataclass
class BayesianKellyTrader:
    """Implements a Bayesian approach to Kelly Criterion for position sizing.
    Uses Bayesian updating of Beta distribution parameters to dynamically
    estimate win probability, and applies the Kelly formula to calculate
    optimal position sizes."""
    alpha: float = 1.0
    beta: float = 1.0
    expected_gain: float = 0.015
    expected_loss: float = 0.015
    kelly_fraction: float = 0.50
    probability_history: List[float] = field(default_factory=list)
    kelly_bet_history: List[float] = field(default_factory=list)
    price_data: Optional[PriceData] = None

    def __post_init__(self) -> None:
        """Validate initialization parameters."""
        if self.alpha <= 0 or self.beta <= 0:
            raise ValueError("Alpha and beta must be positive")
        if self.expected_gain <= 0:
            raise ValueError("Expected gain must be positive")
        if self.expected_loss <= 0:
            raise ValueError("Expected loss must be positive")
        if not 0 < self.kelly_fraction <= 1:
            raise ValueError("Kelly fraction must be between 0 and 1")

    def update_belief(self, price_up: bool) -> None:
        """Update the Bayesian belief based on price movement."""
        if price_up:
            self.alpha += 1
        else:
            self.beta += 1

    def get_win_probability(self) -> float:
        """Calculate the current win probability from the Beta distribution."""
        return self.alpha / (self.alpha + self.beta)

    def calculate_kelly_fraction(self) -> float:
        """Calculate the optimal Kelly position size."""
        p: float = self.get_win_probability()
        q: float = 1 - p
        b: float = self.expected_gain
        loss: float = self.expected_loss
        try:
            # Original Kelly formula
            kelly: float = (p * b - q * loss) / (b * loss)
            # Apply fractional Kelly to avoid overbetting
            kelly: float = np.clip(kelly, -1.0, 1.0) * self.kelly_fraction
            return kelly
        except ZeroDivisionError:
            logger.warning("Division by zero in Kelly calculation")
            return 0.0

    def process_data(self, price_data: PriceData) -> None:
        """Process a series of price data and update beliefs."""
        if len(price_data.prices) < 2:
            raise ValueError("Price data must contain at least 2 observations")
        # Store the price data
        self.price_data = price_data
        prices: np.ndarray = price_data.prices
        # Reset histories
        self.probability_history = []
        self.kelly_bet_history = []
        try:
            # Calculate returns
            returns: np.ndarray = np.diff(prices) / prices[:-1]
            # Process each day's return
            for ret in returns:
                # Store current probability and Kelly bet before update
                self.probability_history.append(self.get_win_probability())
                self.kelly_bet_history.append(self.calculate_kelly_fraction())
                # Update belief based on price movement
                self.update_belief(ret > 0)
        except Exception as e:
            logger.error(f"Error processing price data: {e}")
            raise

    def plot_results(self, rolling_window: int = 20) -> None:
        """Plot the results of the Bayesian updating process."""
        if self.price_data is None:
            raise ValueError("No price data has been processed")
        prices: np.ndarray = self.price_data.prices
        returns: np.ndarray = np.diff(prices) / prices[:-1]
        # Calculate rolling frequency estimate
        rolling_up_prob: np.ndarray = pd.Series(returns > 0).rolling(
            rolling_window).mean()
        plt.figure(figsize=(12, 8))
        # Plot 1: Win Probability Estimates
        plt.subplot(3, 1, 1)
        plt.plot(self.probability_history, label='Bayesian Estimate', color='blue', linewidth=2)
        plt.plot(rolling_up_prob, label=f'{rolling_window}-day Rolling', color='red', linestyle='--')
        plt.title('Win Probability Estimates')
        plt.ylabel('Probability')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Plot 2: Kelly Betting Fraction
        plt.subplot(3, 1, 2)
        plt.plot(self.kelly_bet_history, label='Kelly Fraction', color='green', linewidth=2)
        plt.title('Kelly Position Sizing')
        plt.ylabel('Fraction of Capital')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Plot 3: Price History
        plt.subplot(3, 1, 3)
        plt.plot(prices, label='Price', color='black')
        plt.title('Price History')
        plt.ylabel('Price')
        plt.xlabel('Trading Days')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def simulate_trading(self, initial_capital: float = 10000.0) -> PerformanceMetrics:
        """Simulate trading performance using the Bayesian Kelly approach."""
        if self.price_data is None:
            raise ValueError("No price data has been processed")
        if len(self.probability_history) < 1:
            raise ValueError("Insufficient probability history")
        prices: np.ndarray = self.price_data.prices
        returns: np.ndarray = np.diff(prices) / prices[:-1]
        # Initialize capital and tracking
        capital: float = initial_capital
        capital_history: List[float] = [capital]
        position_sizes: List[float] = []
        # Run trading simulation
        for i, ret in enumerate(returns[:-1]):  # Use all but last return
            # Use probability and Kelly fraction for next trade
            kelly: float = self.kelly_bet_history[i + 1]
            # Calculate position size
            position_size: float = capital * kelly
            position_sizes.append(position_size)
            # Update capital based on return
            capital = (1 + kelly * returns[i + 1]) * capital
            capital_history.append(capital)
        # Calculate performance metrics
        returns_series: pd.Series = pd.Series(np.diff(capital_history) / capital_history[:-1])
        try:
            metrics: PerformanceMetrics = PerformanceMetrics(
                final_capital=capital,
                total_return_pct=(capital / initial_capital - 1) * 100,
                sharpe_ratio=(returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0,
                max_drawdown_pct=(1 - pd.Series(capital_history).cummax() / pd.Series(capital_history)).max() * 100,
                win_rate_pct=(returns_series > 0).mean() * 100,
                trades_count=len(returns_series)
            )
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            raise
        # Create performance plot
        plt.figure(figsize=(12, 8))
        # Plot 1: Equity Curve
        plt.subplot(2, 1, 1)
        plt.plot(capital_history, label='Equity Curve', color='blue', linewidth=2)
        plt.title('Trading Simulation: Bayesian Kelly Strategy')
        plt.ylabel('Capital ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Plot 2: Position Sizes
        plt.subplot(2, 1, 2)
        plt.bar(range(len(position_sizes)), position_sizes, color='green', alpha=0.7)
        plt.title('Position Sizes')
        plt.ylabel('Position Size ($)')
        plt.xlabel('Trading Days')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        return metrics
```

**generate_power_futures_prices (function)**

This function gives us a realistic testbed for our algorithm without requiring historical data. Power futures markets have distinctive characteristics that set them apart from financial markets: they don't follow random walks but instead exhibit mean reversion, time-dependent volatility, and occasional dramatic price spikes.

The simulation captures these key features:

1.  **Mean Reversion:** Prices gravitate toward expected spot levels as delivery approaches
2.  **Declining Volatility Curve:** Uncertainty decreases as we approach delivery date
3.  **Price Jumps:** Sudden spikes that reflect supply/demand shocks

While the math looks complex, it models a real-world phenomenon: futures contracts typically experience higher volatility far from delivery, but become more anchored to physical realities as delivery approaches. The price generation isn't just academic - it creates the challenging conditions our algorithm will face in production.

```python
def generate_power_futures_prices(
    T: int = 90,
    F0: float = 100.0,
    mu_final: float = 90.0,
    kappa: float = 0.3,
    sigma_initial: float = 0.20,
    sigma_final: float = 0.05,
    jump_lambda: float = 0.05,
    jump_mu: float = 0.02,
    jump_sigma: float = 0.03,
    dt: float = 1/252,
    seed: Optional[int] = 42
) -> np.ndarray:
    """Generate synthetic power futures prices using mean-reverting jump diffusion.
    Implements a stochastic process model for power futures with:
    - Mean reversion towards a time-dependent equilibrium level
    - Time-dependent volatility that decreases as delivery approaches
    - Jump component to simulate price spikes
    Args:
        T: Days until contract delivery.
        F0: Initial futures price.
        mu_final: Final expected spot/futures price at delivery.
        kappa: Mean reversion speed.
        sigma_initial: Initial volatility.
        sigma_final: Final volatility (lower closer to delivery).
        jump_lambda: Probability of jump per day.
        jump_mu: Mean jump size (2% upwards on average).
        jump_sigma: Standard deviation of jump size.
        dt: Daily increments (trading days).
        seed: Random seed for reproducibility.
    Returns:
        Array of simulated daily futures prices.
    """
    if seed is not None:
        np.random.seed(seed)
    days: int = int(T)
    prices: np.ndarray = np.zeros(days)
    prices[0] = F0
    for t in range(1, days):
        # Time-dependent mean and volatility
        time_factor: float = np.exp(-0.05 * t)
        # Exponential decay factor
        # Mean converges toward mu_final as t approaches T
        mu_t: float = mu_final + (F0 - mu_final) * time_factor
        # Volatility decreases as t approaches T
        sigma_t: float = sigma_final + (sigma_initial - sigma_final) * time_factor
        # Mean reversion drift
        drift: float = kappa * (mu_t - prices[t-1]) * dt
        # Continuous volatility component
        diffusion: float = sigma_t * np.sqrt(dt) * np.random.normal()
        # Jump component (Poisson arrival)
        jump: float = 0.0
        if np.random.rand() < jump_lambda * dt:
            # Log-normal jump size
            jump_size: float = np.random.lognormal(mean=jump_mu - 0.5*jump_sigma**2, sigma=jump_sigma) - 1.0
            jump = jump_size * prices[t-1]
        # Update price
        prices[t] = prices[t-1] + drift + diffusion + jump
        # Floor the price at 1.0
        prices[t] = max(1.0, prices[t])
    return prices
```

**run_demo (function)**

This function ties everything together, providing a simple entry point to test our trading system. It's designed with sensible defaults that can be overridden for experimentation. This is particularly useful for sensitivity analysis - testing how different prior beliefs or risk parameters affect performance.

In the example call at the bottom of the file, we start with a slightly bearish prior (α=1, β=4, suggesting a 20% chance of upward price movement), which reflects the typical backwardation seen in many power markets. We also take a conservative approach with a quarter-Kelly position sizing, acknowledging the inherent volatility in these markets.

The function returns the trader instance and performance metrics, making it easy to examine the algorithm's behavior and results. This simple interface hides the complexity of the implementation while providing all the functionality needed for practical testing and refinement.

Visualization options make it easy to see how the algorithm's beliefs evolve over time - a crucial feature for building intuition about how Bayesian updating responds to different market conditions. This isn't just a black-box algorithm; it's a transparent system whose decision-making process can be observed and understood.

```python
def run_demo(
    show_plots: bool = True,
    alpha_prior: float = 1.0,
    beta_prior: float = 4.0,
    expected_gain: float = 0.015,
    expected_loss: float = 0.015,
    kelly_fraction: float = 0.25,
    initial_capital: float = 10000.0,
    price_params: Optional[Dict[str, Any]] = None
) -> Tuple[BayesianKellyTrader, PerformanceMetrics]:
    """Run a demonstration of the Bayesian Kelly trading approach.
    Args:
        show_plots: Whether to display the visualization plots.
        alpha_prior: Prior parameter for "up" moves.
        beta_prior: Prior parameter for "down" moves.
        expected_gain: Expected percentage gain on winning trades.
        expected_loss: Expected percentage loss on losing trades.
        kelly_fraction: Fraction of full Kelly to use.
        initial_capital: Initial capital for simulation.
        price_params: Optional parameters for price generation.
    Returns:
        Tuple of (trader instance, performance metrics).
    """
    try:
        # Initialize the trader
        trader: BayesianKellyTrader = BayesianKellyTrader(
            alpha=alpha_prior,
            beta=beta_prior,
            expected_gain=expected_gain,
            expected_loss=expected_loss,
            kelly_fraction=kelly_fraction
        )
        # Generate power futures prices
        params: Dict = price_params or {}
        prices: np.ndarray = generate_power_futures_prices(**params)
        # Create a price data object
        price_data: PriceData = PriceData(
            prices=prices,
            symbol="ERCOT_NORTH_AUG"
        )
        # Process the data
        trader.process_data(price_data)
        # Plot the results if requested
        if show_plots:
            trader.plot_results(rolling_window=20)
        # Simulate trading performance
        performance: PerformanceMetrics = trader.simulate_trading(initial_capital=initial_capital)
        # Print performance metrics
        print("\nPerformance Metrics:")
        for field_name, field_value in performance.__dict__.items():
            print(f"{field_name.replace('_', '').title()}: {field_value:.2f}")
        return trader, performance
    except Exception as e:
        logger.error(f"Error running demonstration: {e}")
        raise
```

**Model Output**

**Model Beliefs and Price Action**

<img>Model Beliefs and Price Action</img>

*   **Top Panel:** Our win probability estimates gradually converges from our initial skeptical 20% prior to a more balanced 45% view. The Bayesian estimate (blue line) offers a much more stable assessment than the reactive 20-day rolling average (red line), reflecting the power of our approach. While the rolling average jumps with recent data, our Bayesian model provides a steadier signal by incorporating all historical information.
*   **Middle Panel:** The consistent -25% position size from our quarter-Kelly (kelly_fraction=0.25), so that even as the win probability fluctuates between 35-50%, the position sizing remains remarkably consistent, exactly what we want for a disciplined trading strategy.
*   **Bottom Panel:** A choppy downtrend from around $130/MWh to $118/MWh. Even with numerous rallies and sideways periods, the algorithm correctly maintains its short position throughout these fluctuations, showing that it's targeting the long-term trend rather than getting shaken out by short-term noise.

**Trading Performance and Position Sizing**

<img>Trading Performance and Position Sizing</img>

*   **Top Panel:** a successful outcome, modestly growing our initial $10,000 capital to approximately $10,150 over the 90-day period. The path wasn't linear, with several drawdowns, with the largest around days 5-10 and another around day 75.
*   **Bottom Panel:** The position sizes are the dollar value of our consistent -25% allocation. With $10,000 initial capital, this translates to approximately -$2,500 positions throughout the simulation, reflecting disciplined risk management and how our conservative fractional Kelly approach prevents the wild swings in allocation that often lead to account blowups.

**Margin Calls (or "When You Get Priors Wrong")**

Here's the thing about Bayesian Kelly - and all Bayesian models for that matter. You are always at the mercy of your priors. The chart shows what would have happened had we (for whatever reason) simply swapped our initial priors to α = 4 and β = 1. In short: you got lucky at first, as prices did spike, which reinforced your already-bullish priors and drove you long for the first 20 days. Then, mean reversion took over, but by then the damage was done: the initial positive bias from your first priors kept you from switching to a bearish outlook. The result? A 30% win rate (vs. 53% in the previous example) and 2.5% loss (vs. +1.07). Not a good look.

<img>Margin Calls (or "When You Get Priors Wrong")</img>

**A Final Word**

So, before you quit your job to build a Bayesian Kelly power trading empire, though keep in mind that this approach has its own minefield of pitfalls - including misestimating your initial priors. Still, I hope you found this article useful, as you continue your adventure in quantitative finance.

As always, happy trading, and may your priors be ever in your favor!

**Full Code**

```python
"""Bayesian Kelly Trader for Power Markets.
This module implements a Bayesian approach to the Kelly Criterion for position
sizing in power market futures trading. It continuously updates probability
estimates using Bayesian inference and computes optimal position sizes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import beta
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PriceData:
    """Immutable container for price data."""
    prices: np.ndarray
    dates: Optional[np.ndarray] = None
    symbol: Optional[str] = None

@dataclass(frozen=True)
class TradeResult:
    """Immutable container for a single trade result."""
    entry_price: float
    exit_price: float
    position_size: float
    gain_loss: float

@dataclass(frozen=True)
class PerformanceMetrics:
    """Immutable container for trading performance metrics."""
    final_capital: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    trades_count: int

@dataclass
class BayesianKellyTrader:
    """Implements a Bayesian approach to Kelly Criterion for position sizing.
    Uses Bayesian updating of Beta distribution parameters to dynamically
    estimate win probability, and applies the Kelly formula to calculate
    optimal position sizes."""
    alpha: float = 1.0
    beta: float = 1.0
    expected_gain: float = 0.015
    expected_loss: float = 0.015
    kelly_fraction: float = 0.50
    probability_history: List[float] = field(default_factory=list)
    kelly_bet_history: List[float] = field(default_factory=list)
    price_data: Optional[PriceData] = None

    def __post_init__(self) -> None:
        """Validate initialization parameters."""
        if self.alpha <= 0 or self.beta <= 0:
            raise ValueError("Alpha and beta must be positive")
        if self.expected_gain <= 0:
            raise ValueError("Expected gain must be positive")
        if self.expected_loss <= 0:
            raise ValueError("Expected loss must be positive")
        if not 0 < self.kelly_fraction <= 1:
            raise ValueError("Kelly fraction must be between 0 and 1")

    def update_belief(self, price_up: bool) -> None:
        """Update the Bayesian belief based on price movement."""
        if price_up:
            self.alpha += 1
        else:
            self.beta += 1

    def get_win_probability(self) -> float:
        """Calculate the current win probability from the Beta distribution."""
        return self.alpha / (self.alpha + self.beta)

    def calculate_kelly_fraction(self) -> float:
        """Calculate the optimal Kelly position size."""
        p: float = self.get_win_probability()
        q: float = 1 - p
        b: float = self.expected_gain
        loss: float = self.expected_loss
        try:
            # Original Kelly formula
            kelly: float = (p * b - q * loss) / (b * loss)
            # Apply fractional Kelly to avoid overbetting
            kelly: float = np.clip(kelly, -1.0, 1.0) * self.kelly_fraction
            return kelly
        except ZeroDivisionError:
            logger.warning("Division by zero in Kelly calculation")
            return 0.0

    def process_data(self, price_data: PriceData) -> None:
        """Process a series of price data and update beliefs."""
        if len(price_data.prices) < 2:
            raise ValueError("Price data must contain at least 2 observations")
        # Store the price data
        self.price_data = price_data
        prices: np.ndarray = price_data.prices
        # Reset histories
        self.probability_history = []
        self.kelly_bet_history = []
        try:
            # Calculate returns
            returns: np.ndarray = np.diff(prices) / prices[:-1]
            # Process each day's return
            for ret in returns:
                # Store current probability and Kelly bet before update
                self.probability_history.append(self.get_win_probability())
                self.kelly_bet_history.append(self.calculate_kelly_fraction())
                # Update belief based on price movement
                self.update_belief(ret > 0)
        except Exception as e:
            logger.error(f"Error processing price data: {e}")
            raise

    def plot_results(self, rolling_window: int = 20) -> None:
        """Plot the results of the Bayesian updating process."""
        if self.price_data is None:
            raise ValueError("No price data has been processed")
        prices: np.ndarray = self.price_data.prices
        returns: np.ndarray = np.diff(prices) / prices[:-1]
        # Calculate rolling frequency estimate
        rolling_up_prob: np.ndarray = pd.Series(returns > 0).rolling(
            rolling_window).mean()
        plt.figure(figsize=(12, 8))
        # Plot 1: Win Probability Estimates
        plt.subplot(3, 1, 1)
        plt.plot(self.probability_history, label='Bayesian Estimate', color='blue', linewidth=2)
        plt.plot(rolling_up_prob, label=f'{rolling_window}-day Rolling', color='red', linestyle='--')
        plt.title('Win Probability Estimates')
        plt.ylabel('Probability')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Plot 2: Kelly Betting Fraction
        plt.subplot(3, 1, 2)
        plt.plot(self.kelly_bet_history, label='Kelly Fraction', color='green', linewidth=2)
        plt.title('Kelly Position Sizing')
        plt.ylabel('Fraction of Capital')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Plot 3: Price History
        plt.subplot(3, 1, 3)
        plt.plot(prices, label='Price', color='black')
        plt.title('Price History')
        plt.ylabel('Price')
        plt.xlabel('Trading Days')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def simulate_trading(self, initial_capital: float = 10000.0) -> PerformanceMetrics:
        """Simulate trading performance using the Bayesian Kelly approach."""
        if self.price_data is None:
            raise ValueError("No price data has been processed")
        if len(self.probability_history) < 1:
            raise ValueError("Insufficient probability history")
        prices: np.ndarray = self.price_data.prices
        returns: np.ndarray = np.diff(prices) / prices[:-1]
        # Initialize capital and tracking
        capital: float = initial_capital
        capital_history: List[float] = [capital]
        position_sizes: List[float] = []
        # Run trading simulation
        for i, ret in enumerate(returns[:-1]):  # Use all but last return
            # Use probability and Kelly fraction for next trade
            kelly: float = self.kelly_bet_history[i + 1]
            # Calculate position size
            position_size: float = capital * kelly
            position_sizes.append(position_size)
            # Update capital based on return
            capital = (1 + kelly * returns[i + 1]) * capital
            capital_history.append(capital)
        # Calculate performance metrics
        returns_series: pd.Series = pd.Series(np.diff(capital_history) / capital_history[:-1])
        try:
            metrics: PerformanceMetrics = PerformanceMetrics(
                final_capital=capital,
                total_return_pct=(capital / initial_capital - 1) * 100,
                sharpe_ratio=(returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0,
                max_drawdown_pct=(1 - pd.Series(capital_history).cummax() / pd.Series(capital_history)).max() * 100,
                win_rate_pct=(returns_series > 0).mean() * 100,
                trades_count=len(returns_series)
            )
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            raise
        # Create performance plot
        plt.figure(figsize=(12, 8))
        # Plot 1: Equity Curve
        plt.subplot(2, 1, 1)
        plt.plot(capital_history, label='Equity Curve', color='blue', linewidth=2)
        plt.title('Trading Simulation: Bayesian Kelly Strategy')
        plt.ylabel('Capital ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Plot 2: Position Sizes
        plt.subplot(2, 1, 2)
        plt.bar(range(len(position_sizes)), position_sizes, color='green', alpha=0.7)
        plt.title('Position Sizes')
        plt.ylabel('Position Size ($)')
        plt.xlabel('Trading Days')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        return metrics

def generate_power_futures_prices(
    T: int = 90,
    F0: float = 100.0,
    mu_final: float = 90.0,
    kappa: float = 0.3,
    sigma_initial: float = 0.20,
    sigma_final: float = 0.05,
    jump_lambda: float = 0.05,
    jump_mu: float = 0.02,
    jump_sigma: float = 0.03,
    dt: float = 1/252,
    seed: Optional[int] = 42
) -> np.ndarray:
    """Generate synthetic power futures prices using mean-reverting jump diffusion.
    Implements a stochastic process model for power futures with:
    - Mean reversion towards a time-dependent equilibrium level
    - Time-dependent volatility that decreases as delivery approaches
    - Jump component to simulate price spikes
    Args:
        T: Days until contract delivery.
        F0: Initial futures price.
        mu_final: Final expected spot/futures price at delivery.
        kappa: Mean reversion speed.
        sigma_initial: Initial volatility.
        sigma_final: Final volatility (lower closer to delivery).
        jump_lambda: Probability of jump per day.
        jump_mu: Mean jump size (2% upwards on average).
        jump_sigma: Standard deviation of jump size.
        dt: Daily increments (trading days).
        seed: Random seed for reproducibility.
    Returns:
        Array of simulated daily futures prices.
    """
    if seed is not None:
        np.random.seed(seed)
    days: int = int(T)
    prices: np.ndarray = np.zeros(days)
    prices[0] = F0
    for t in range(1, days):
        # Time-dependent mean and volatility
        time_factor: float = np.exp(-0.05 * t)
        # Exponential decay factor
        # Mean converges toward mu_final as t approaches T
        mu_t: float = mu_final + (F0 - mu_final) * time_factor
        # Volatility decreases as t approaches T
        sigma_t: float = sigma_final + (sigma_initial - sigma_final) * time_factor
        # Mean reversion drift
        drift: float = kappa * (mu_t - prices[t-1]) * dt
        # Continuous volatility component
        diffusion: float = sigma_t * np.sqrt(dt) * np.random.normal()
        # Jump component (Poisson arrival)
        jump: float = 0.0
        if np.random.rand() < jump_lambda * dt:
            # Log-normal jump size
            jump_size: float = np.random.lognormal(mean=jump_mu - 0.5*jump_sigma**2, sigma=jump_sigma) - 1.0
            jump = jump_size * prices[t-1]
        # Update price
        prices[t] = prices[t-1] + drift + diffusion + jump
        # Floor the price at 1.0
        prices[t] = max(1.0, prices[t])
    return prices

def run_demo(
    show_plots: bool = True,
    alpha_prior: float = 1.0,
    beta_prior: float = 4.0,
    expected_gain: float = 0.015,
    expected_loss: float = 0.015,
    kelly_fraction: float = 0.25,
    initial_capital: float = 10000.0,
    price_params: Optional[Dict[str, Any]] = None
) -> Tuple[BayesianKellyTrader, PerformanceMetrics]:
    """Run a demonstration of the Bayesian Kelly trading approach.
    Args:
        show_plots: Whether to display the visualization plots.
        alpha_prior: Prior parameter for "up" moves.
        beta_prior: Prior parameter for "down" moves.
        expected_gain: Expected percentage gain on winning trades.
        expected_loss: Expected percentage loss on losing trades.
        kelly_fraction: Fraction of full Kelly to use.
        initial_capital: Initial capital for simulation.
        price_params: Optional parameters for price generation.
    Returns:
        Tuple of (trader instance, performance metrics).
    """
    try:
        # Initialize the trader
        trader: BayesianKellyTrader = BayesianKellyTrader(
            alpha=alpha_prior,
            beta=beta_prior,
            expected_gain=expected_gain,
            expected_loss=expected_loss,
            kelly_fraction=kelly_fraction
        )
        # Generate power futures prices
        params: Dict = price_params or {}
        prices: np.ndarray = generate_power_futures_prices(**params)
        # Create a price data object
        price_data: PriceData = PriceData(
            prices=prices,
            symbol="ERCOT_NORTH_AUG"
        )
        # Process the data
        trader.process_data(price_data)
        # Plot the results if requested
        if show_plots:
            trader.plot_results(rolling_window=20)
        # Simulate trading performance
        performance: PerformanceMetrics = trader.simulate_trading(initial_capital=initial_capital)
        # Print performance metrics
        print("\nPerformance Metrics:")
        for field_name, field_value in performance.__dict__.items():
            print(f"{field_name.replace('_', '').title()}: {field_value:.2f}")
        return trader, performance
    except Exception as e:
        logger.error(f"Error running demonstration: {e}")
        raise

if __name__ == "__main__":
    # Example usage with default parameters
    trader, metrics = run_demo(
        alpha_prior=1.0,
        beta_prior=4.0,
        expected_gain=0.015,
        expected_loss=0.015,
        kelly_fraction=0.25,
        price_params={
            'T': 90,
            'FO': 125.0,
            'mu_final': 90.0,
            'kappa': 0.5,
            'sigma_initial': 0.35,
            'sigma_final': 0.15,
            'jump_lambda': 0.03,
            'jump_mu': 0.03,
            'jump_sigma': 0.05,
            'seed': 42
        }
    )