# What is a value-based order? (CFD)

A value-based order lets you specify the exact market value you want for a CFD position rather than entering a specific quantity.

How does a value-based order work?

Once you enter the total value (e.g., £10,000), the system calculates the quantity based on the latest market price. If placing a market order, the trade executes immediately at the best available price. If placing a limit or stop order, the trade is executed once the market reaches your specified price.

What types of orders support value-based trading?

*   Market orders
*   Limit orders
*   Stop orders
*   Modifying positions

❗️ **Important**

Take Profit and Stop Loss orders do not support value-based trading.

Can I place a value-based order outside of market hours?

You can do so only for Limit & Stop orders. For market orders, the value-based order is only available during regular trading hours.

What is the minimum and maximum trade size for value-based orders?

*   **Minimum trade value:** Defined by the platform’s minimum trade value setting.
*   **Maximum trade value:** Based on the maximum allowable value for the specific instrument and your available margin.

What happens if the market price changes before execution?

For market orders, the final execution price may differ slightly due to price movement. Your total value remains the same, but the quantity may adjust. For limit/stop orders, the order remains pending until the market reaches your specified price.

How are value-based orders calculated in different currencies?

If you trade an instrument quoted in a different currency from your account currency, the system automatically converts the value using the latest mid exchange rate.

💡 **Example**

You place a £5,000 value order in Apple (AAPL) with:

*   Account currency: GBP
*   GBP/USD mid rate: 1.2500
*   Leverage: 5:1 (20% margin requirement)

Calculations:

*   Convert value from GBP to USD:

£5,000 × 1.2500 = $6,250

*   Calculate margin in USD:

$6,250 × 20% = $1,250

*   Convert margin to GBP:

$1,250 ÷ 1.2500 = £1,000 locked as margin

What happens if my trade value results in a fractional quantity?

We support fractional trading, so your order will be executed as close as possible to the exact calculated quantity.

Can I modify or cancel a value-based order?

*   **Market Orders:** Cannot be modified or cancelled once placed, as they are executed immediately at the best available price.
*   **Limit/Stop Orders:** Can be modified or cancelled before execution, as they remain pending until the market reaches the specified price.

Are value-based orders available on all CFD instruments?

Yes, they are available across all supported CFDs, including stocks, futures, forex, and commodities.
