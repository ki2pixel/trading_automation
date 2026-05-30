# What does my account-margin status show

Margin Health, also known as the Margin Indicator, shows the percentage of your cash available. It helps you monitor your account's financial status and determine whether you can open new positions.

How is the margin calculated?

Margin reflects how much of your available funds are being used to support open CFD positions. Your total funds include:

*   **Free Cash:** Funds available for trading. This amount is continuously updated based on your unrealised profit or loss.

*   **Unrealised P&L:** Floating profit or loss from open positions. It directly affects your Free Cash in real-time.

*   **Margin:** The portion of funds reserved to keep your current positions open. Margin requirements are continuously updated based on current market prices.

We apply different formulas depending on your account status:

*   **Above 50%:**

Account Status = (Total Funds / (Total Funds + Margin)) x 100
*   **Below 50%:**

Account Status = (Total Funds / Margin) × 50

📄 **Note**

A status below 50% means you have no free funds available and can’t open new positions until your margin improves.

How is the margin reserved?

We reserve margin based on the direction of your trade:

*   **Buy (long):** Margin is reserved using the Buy price (Ask)
*   **Sell (short):** Margin is reserved using the Sell price (Bid)

The amount reserved depends on the trade value and the leverage applied to the instrument.

For all CFDs except Forex, such as stocks, futures, and commodities, the margin is determined by dividing the trade value (exposure) of the position by the leverage. If your account currency differs from the currency of the instrument, the amount is then converted to your account currency using the mid-market exchange rate.

Only Forex CFDs are handled differently — the margin is always calculated in the base currency of the pair before conversion.

💡 **Example CFD on Stocks**

You open a Buy position on Tesla (USD) at a Buy price of $200, using 1:5 leverage.

*   **Trade value:** $1,000
*   **Required margin:** $1,000 ÷ 5 = $200

If your account currency is EUR, the system converts the margin from USD to EUR using the mid-market FX rate (average of bid and ask).

*   **Example mid-rate:** 1.10 USD/EUR
*   **Reserved margin:** $200 ÷ 1.10 = ~€181.82

💡 **Example CFD on Forex**

You open a Buy position on EUR/USD (trading €10,000), using 1:30 leverage.

*   **Trade value:** €10,000
*   **Required margin:** €10,000 ÷ 30 = €333.33

If your account currency is GBP, the margin is converted from EUR to GBP using the mid-market FX rate.

*   **Example mid-rate:** 0.85 EUR/GBP
*   **Reserved margin:** €333.33 × 0.85 = ~£283.33

This method is used only for Forex CFDs, where the margin is always calculated based on the pair's base currency.

This amount is reserved from your free cash - it still forms part of your total funds but is not available for opening new positions.

What do different margin levels mean?

Your margin status indicates the financial state of your account. It helps you understand whether you have available funds to open new positions, or whether action is needed to reduce risk.

*   **✅ Above 50% - Sufficient free funds**

You have free funds available and can open new positions. No immediate action is required.

💡 **Example**

*   **Total Funds:** €1,000
*   **Margin:** €400

Account Status = €1,000 / (€1,000 + €400) = 71.4%

*   **⚠️ Below 50% – No Free Funds**

All your funds are tied up in open positions. You cannot open new trades unless your margin status improves. At this level, there are no free funds available. You may consider reducing exposure or adding funds.

💡 **Example**

*   **Total Funds:** €400
*   **Margin:** €600

Account Status = (€400 / €600) × 50 = 33.3%

*   **📩 At 45% – Margin Call**

You will receive an email notification that your margin level is low. If your margin status falls below 45%, an automated margin call email will be sent. This is your opportunity to take action — such as adding funds or reducing your exposure — before automatic position closure is triggered.

💡 **Example**

*   **Total Funds:** €450
*   **Margin:** €750

Account Status = (€450 / €750) × 50 = 30%

*   **❗ At 25% or below – Automatic Position Closure**

When a stop-out is triggered, we will first attempt to close the position selected by your chosen strategy partially. If closing only a part of the position is enough to restore your margin level, we will do so. If a partial closure is insufficient, the entire position will be closed.

Additionally, to provide a protective buffer and help prevent multiple liquidation events quickly, the process aims to restore your margin level to slightly above the required threshold. We add a 5% margin buffer, meaning the liquidation will aim to restore your margin level to approximately 30%.

💡 **Example**

*   **Total Funds:** €200
*   **Margin:** €1,000

Account Status = (€200 / €1,000) × 50 = 10%

❗️ **Important**

During periods of high market volatility, positions may be closed without prior notice to prevent a negative balance.
