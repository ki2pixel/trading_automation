# What is a Rollover?

A rollover transfers an open CFD position on an expiring futures contract to the next available contract automatically. This enables you to maintain positions beyond contract expiration without the need to manually re-enter the market. This reduces market disruptions and ensures continuous liquidity.

How does the rollover process work?

When a futures contract reaches its expiry date, we automatically close open positions on the expiring contract and reopen them on the next contract at the prevailing market prices.

**Example:**

*   Quantity: 100

*   Opening price: $71.76

*   Expiring future sell / buy price: $71.80 / $71.84

*   Next future sell / buy price: $73.87 / $73.90

**For a long position:**

The position is closed at a result of 100 x ($71.80 - $71.76) = $4.00

The new position is opened with a result of 100 x ($73.87 - $73.90) = -$3.00

**For a short position:**

The position is closed at a result of -100 x ($71.84 - $71.76) = -$8.00

The new positions is opened with a result of -100 x ($73.87 - $73.90) = $3.00

📄 **Note**

As the new contract has a different market price than the old contract, the average price of your position will change with a rollover.

What does the rollover cost?

We do not charge any extra fees for the rollover itself. You will only incur the costs you would incur for manually closing and reopening the position. This includes the spread and potential Foreign Exchange (FX) fees that apply if the instrument currency differs from your account currency. FX market fluctuations will impact the cost of opening the new position.
