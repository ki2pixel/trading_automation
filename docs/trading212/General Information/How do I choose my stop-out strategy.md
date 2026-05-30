# How do I choose my stop-out strategy

You can choose the order in which your CFD positions are closed during a stop-out event to give you more control over your risk management. This article explains how the new stop-out strategies work and how to select the one that best suits your trading strategy.

📄 **Note**

The Stop-out strategy selection feature will be available in Trading 212's app (version 7.88.0) and web platform starting July 31, 2025.

What is a stop-out event?

A stop-out is a safety measure mandated by financial regulators that automatically closes open positions when your account’s margin level falls to 25% or below. This action helps to protect you from further losses and prevents your account balance from going negative. The stop-out strategy determines the precise order in which these positions are closed.

How can I set my stop-out strategy?

You can set your preferred liquidation model directly in the app:

1.   Go to Settings
2.   Tap on Trading preferences
3.   Select Stop-out strategy
4.   Choose your preferred model from the list.

How does the stop-out logic work?

When a stop-out is triggered, we will first attempt to close the position selected by your chosen strategy partially. If closing only a part of the position is enough to restore your margin level, we will do so. If a partial closure is insufficient, the entire position will be closed.

Additionally, to provide a protective buffer and help prevent multiple liquidation events quickly, the process aims to restore your margin level to slightly above the required threshold. We add a 5% margin buffer, meaning the liquidation will aim to restore your margin level to approximately 30%.

What are the different types of stop-out strategies?

*   **Largest used margin first**is a strategy that prioritises closing the position using the most margin first. This is designed to restore your margin level with the minimum number of closed trades. This strategy does not close them symmetrically when you have opposing positions in the same instrument, i.e., long and short. The system treats them as individual positions and will close the one using the highest margin first, then liquidate the other if needed.

*   **LIFO (Last-In, First-Out)** is a strategy that prioritises closing the newest positions in your portfolio first. The last trade you opened will be the first to be liquidated.

*   **FIFO (First-In, First-Out)**is the opposite of LIFO and it’s the default strategy. It prioritises closing the oldest positions in your portfolio first. The trades you’ve held open the longest will be the first to close.

*   **Losers first**is a strategy that prioritises closing your least profitable positions first. It will close the trades with the largest negative result (or smallest profit) to manage losing positions during a stop-out.

*   **Winners first** is a strategy that prioritises closing your most profitable positions first. The aim is to secure profits from your successful trades to free up margin.

How do the strategies work in practice? [💡Example]

To understand how each model works, let's imagine a client has the following three open positions when a stop-out is triggered.

Position Opened Profit/Loss Margin used
Position A: Gold 5 days ago+€250 (Winner)€500 (Largest Margin)
Position B: EUR/USD 2 days ago-€100 (Loser)€300
Position C: UK100 3 hours ago+€50€150 (Lowest Margin)

Here is which position would be chosen for liquidation by each strategy first:

*   **Largest used margin first****Result:****Position A (Gold)** would be closed first.

**Reason:** It uses the most margin (€500), so closing it has the most significant impact on restoring the margin level.

*   **LIFO (Last-In, First-Out)****Result:****Position C (UK100)** would be closed first.

**Reason:** It was the most recently opened position (3 hours ago).

*   **FIFO (First-In, First-Out)****Result:****Position A (Gold)** would be closed first.

**Reason:** It is the oldest position in the portfolio (5 days ago).

*   **Losers first****Result:****Position B (EUR/USD)** would be closed first.

**Reason:** It is the only position with a loss (-€100).

*   **Winners first****Result:****Position A (Gold)** would be closed first.

**Reason:** It is the most profitable position (+€250).
