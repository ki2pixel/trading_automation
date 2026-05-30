# What is overnight interest

When you hold a CFD position overnight, an overnight interest will apply. This interest reflects the cost of maintaining a leveraged position, as CFD trading involves borrowing funds.

How is overnight interest calculated?

#### Overnight interest depends on

*   **Market conditions:** interest rates, borrow fees (for shorts), and other instrument-specific costs.
*   **Static markup:** a fixed markup applied per instrument type.

#### Calculation formulas for the Daily overnight interest

**Forex (FX) - calculated on position size (base currency units)**

*   **Long (Buy):**Quantity × Long overnight interest rate
*   **Short (Sell):**Quantity × Short overnight interest rate

**Non-Forex products - calculated on notional value**

*   **Long (Buy):**Quantity × Price × Long overnight interest rate
*   **Short (Sell):**Quantity × Price × Short overnight interest rate

#### Currency and conversion

*   Overnight interest is shown and charged in your account currency.
*   For calculation purposes, we first compute it in:
    *   the base currency for FX pairs (e.g., EUR for EUR/USD), or
    *   the instrument currency for non-Forex products (e.g., GBP for Barclays),

and then convert it to your account currency using the current exchange rate.

*   In your account history, we also show the equivalent amount in the base/instrument currency for reference

📄 **Note**

Long and short overnight interest rates are subject to daily market fluctuations and change every day.

How does overnight interest affect my account?

If the overnight interest rate is negative, a financing fee is deducted from your CFD account. If the overnight interest rate is positive, funds are credited to your CFD account.

Where can I find overnight interest rates?

These rates update daily and can be found in the **Instrument Details** section.

When is interest applied?

On regular weekdays, overnight interest is applied at 22:00 GMT from Monday to Thursday for positions still open at that time. For weekend positions, the fee is charged at 22:00 GMT on Sunday.

💡Example: Calculating the Overnight Interest for a EUR/USD Position

In this example, the instrument is EUR/USD and the position type is Long (Buy). The position size is 10,000 units (EUR). The daily long overnight interest rate is -0.0189%.

Daily overnight interest:

Daily overnight interest = €10,000 × (-0.0189%)

Daily overnight interest = €10,000 x (-0.000189)

Amount charged (daily) ≈ -€1.89

💡Example: Calculating the Overnight Holding Cost for stocks

In this example, the instrument is Barclays and the position type is Short (Sell). The instrument price is £4.40, the position size is 100 shares, and the daily short overnight interest rate is -0.0251%.

Calculate the position value:

Position Value = 100 × £4.40

Position Value = £440
Calculate daily overnight interest:

Daily overnight interest = £440 × (-0.0251%)

Daily overnight interest = £440 x (-0.000251)

Amount charged (daily) ≈ -£0.11
