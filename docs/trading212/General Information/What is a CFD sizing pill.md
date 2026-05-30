# What is a CFD sizing pill

We are gradually rolling out this feature to an increasing number of users.

The pills suggest a quantity or value you can place, based on your free funds (the money available to use as margin).

How do the sizing pills work?

### New positions

*   **25%**→ uses 25% of your free funds as margin
*   **50%**→ uses 50% of your free funds
*   **75%**→ uses 75% of your free funds
*   **100%**→ uses 98% of your free funds

💡 **Example**

You have €1,000 in free funds.

*   Tap 50% → We prefill a size that uses about a €500 margin for this instrument.
*   Tap 100% → We target €980 (98%) to add a buffer.

### Opposite side trades (Hedging)

When you open a trade in the opposite direction of an existing position, the order can be funded in two ways:

1.   **Offset up to your current position size:**this part usually needs no extra margin.
2.   **Your free funds:** for any size beyond your current position.

#### A) If you have no free cash

We size only from your existing position:

*   **25%**→ 25% of your current position
*   **50%**→ 50% of your current position
*   **75%**→ 75% of your current position
*   **100%**→ 100% of your current position

💡 **Example**

You hold Buy 100. With no free funds, tapping 25% on Sell suggests 25; 50% → 50; 75% → 75; 100% → 100.

#### B) If you have free cash

We split the pill across both parts:

*   **25%**→ 25% of (your current position + what your free funds can open)
*   **50%** → 50% of (current position + free‑funds)
*   **75%** → 75% of (current position + free‑funds)
*   **100%** → 100% of your current position + 98% of what your free funds can open

💡 **Example**

You hold Buy 100, and your free funds could open 10 more units.

*   25% → 25% × (100 + 10) = 27.5
*   50% → 50% × (100 + 10) = 55
*   75% → 75% × (100 + 10) = 82.5
*   100% → 100% × 100 + 98% × 10 = 109.8

#### C) Close or partially close a position

When you want to reduce or close a position, we base the pills on the quantity of your position.

What each pill does?

*   **25%** → prefill to close 25% of the position (partial close)
*   **50%** → prefill to close 50% of the position (partial close)
*   **75%**→ prefill to close 75% of the position (partial close)
*   **100%** → prefill to close 100% of the position (full closе)

💡 **Example**

You hold 80 units:

*   50% → we prefill 40 units to close.
*   100% → we prefill 80 units (full close).

Why does the 100% pill use only 98%?

To protect you from fast price changes. The 2% buffer makes it less likely that the order becomes unplaceable between tap and submit. In extreme moves, you may still need to adjust.

Does this work for both value and quantity orders?

Yes. We prefill either value or quantity - both map to the same target margin use.

What if the price moves after I tap a pill?

Prices can move. If the order becomes too large for your updated free funds, we’ll tell you. Tap the pill again or reduce the size.

What if I type my own number?

You can choose your own order size by entering it manually and without using a sizing pill.
