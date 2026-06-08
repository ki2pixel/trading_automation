Dual RSI DCA --- Long Strategy

🔷 What it does:\
This is a long-only DCA framework that combines two independent RSI conditions on a low timeframe --- one gates the base entry (oversold reversal), one arms the take-profit (overbought rotation) --- with a bounded five-level averaging-order ladder for adverse price action. The structure is built for assets that move in fast oversold-overbought oscillations on intraday timeframes (mid-cap altcoins, meme-class tokens, DEX-flow pairs), where the goal is to catch a momentum flip up, accumulate on continued weakness within a strict envelope, and rotate out on the next momentum flip down once minimum profit is realized.\
- Base entry: RSI(14) on 3m crossing UP through 31 (oversold reversal)\
- Exit: RSI(14) on 3m crossing DOWN through 69 AND profit ≥ 2.4% from average\
- 5 averaging orders with geometric size (×1.25) and deviation (×1.3) progression\
- NO stop loss --- risk is structurally capped by the bounded position-size ladder (base + all AOs ≈ 9.93% of equity at default settings)\
- Single-position pyramid (max one open cycle at a time)

🔷 Who is it for:\
Active intraday traders who follow fast-oscillating instruments and want a rule-based way to time entries off oversold-reversal moments rather than chasing breakouts.\
DCA-bot operators who route TradingView signals to a connected automated execution layer via webhook alerts.\
Traders who prefer structurally bounded risk over stop-loss-based protection --- the position-size ladder caps maximum capital deployment by design.\
Anyone who wants the exit decision driven by momentum (RSI crossing down 69) rather than a fixed % target, while still requiring a minimum profit floor.

🔷 How does it work:\
Long Entry: When the 3m RSI(14) crosses UP through 31 on a confirmed bar, the strategy opens a base long position sized at 0.9% of equity (90 USDT on a 10k account). The cross-up captures the moment momentum exits the oversold zone --- a structural reversal signal that is more reliable than buying inside the oversold zone itself (where weakness can persist indefinitely).\
Averaging Orders: When price drops below the cumulative deviation thresholds from base entry, additional orders fill in sequence. The five-step ladder uses a geometric deviation progression (1.3% × 1.3 multiplier per step) and geometric sizing (110 USDT × 1.25 multiplier per step). Cumulative deviation levels are approximately: AO1 -1.30%, AO2 -2.99%, AO3 -5.19%, AO4 -8.04%, AO5 -11.76%. Each fill weighs the position toward the lower end, dragging the average entry down so the exit signal can fire at a higher absolute price.\
Exit Management: The exit fires when two conditions are simultaneously satisfied: (1) the 3m RSI(14) crosses DOWN through 69 (momentum rotating out of overbought), AND (2) current price is at least 2.4% above the position's average entry. Without the profit gate, the exit would close losing positions on every overbought rotation, defeating the DCA logic. With the gate, the exit only fires when momentum-rotation aligns with realized profit.\
No stop loss --- the ladder structure provides risk containment by capping maximum capital deployment per cycle. If price continues falling past AO5 (-11.76%), no further orders fill; the open position holds until price recovers and the exit conditions trigger.

🔷 Why it's unique:\
Dual independent RSI gating --- most DCA scripts use a single trigger for both entry and exit, which creates ambiguity in trending regimes. Here, entry and exit are gated by separate threshold crosses on the same RSI series --- one armed at the bottom of the range (cross up 31), the other at the top (cross down 69). This decouples the two decisions and gives the strategy a cleaner behavioral profile in regime transitions.\
Bounded risk envelope --- total capital at risk across base + all AOs is fixed by design at ~9.93% of equity at default sizing, falling within TradingView's recommended 5--10% per-trade band. No stop loss is needed because the ladder itself caps deployment.\
Bot integration --- all order events ship webhook-ready JSON payloads (entry, AO add-funds, close-at-market). Bot ID, Email Token, and pair label are exposed as inputs for direct routing to an automated execution endpoint.

🔷 Considerations Before Using the Indicator:

Market & Timeframe: This strategy is calibrated for assets with active intraday oscillations on a 3-minute base timeframe --- typically mid-cap altcoins or DEX-traded tokens with high relative volatility. The default pair (USDT_HYPE) reflects that calibration. Higher-timeframe operation requires re-evaluating the RSI levels and deviation ladder for the asset's actual volatility profile. Quiet majors (BTC, ETH) on 3m will produce far fewer signals and may not generate meaningful sample sizes within a reasonable test period.

Limitations: No stop loss. If the asset enters a sustained downtrend that breaks below the -11.76% AO5 level without recovering, the position holds unrealized losses until either price recovers or the user manually closes. This is the explicit trade-off of the bounded-ladder approach --- predictable maximum capital exposure, but no automated exit on regime breakdown. Pair this strategy with manual regime validation: do not deploy during macro de-risk events, exchange outages, or token-specific catastrophic news.

Backtesting & Demo Testing: Always validate the entry/exit RSI thresholds and AO ladder on the specific instrument and recent volatility regime. Token volatility profiles change rapidly --- what worked last quarter may not work this quarter. Re-test on your own venue using venue-specific commission and slippage. Demo-trade for at least one month before any live deployment. Past performance is not indicative of future results.

Parameter Adjustments: Commission defaults to 0.08% (taker reference for active venues). Adjust for your venue --- Binance Spot ~0.10%, Bybit Spot ~0.10%, Coinbase Advanced ~0.50%, OKX Spot ~0.08%. The 5-AO ladder and the size/deviation multipliers should be sized so that the worst-case ladder fill does not exceed your personal risk budget. Recalculate the cumulative deviation envelope manually before live deployment.

🔷 STRATEGY PROPERTIES\
Symbol: BYBIT:HYPEUSDT.P (HYPE Perpetual Contract). Strategy is generic and works on any liquid pair with sufficient 3m oscillation amplitude.\
Timeframe: 3m chart (signals are computed on 3m via security() with no repaint --- lookahead off, cross detected at host-bar granularity).\
Test Period: Feb 23, 2026 --- May 20, 2026 (≈ 86 days / 3 months).\
Initial Capital: 10,000 USDT default. Base + 5 AOs sized so total ladder ≈ 9.93% of equity.\
Order Size per Trade: base 90 USDT; AO1 110 USDT; AO2 137.5 USDT; AO3 171.88 USDT; AO4 214.84 USDT; AO5 268.55 USDT.\
Commission: 0.08% --- adjust to match your venue's taker rate.\
Slippage: 3 ticks --- typical taker execution on liquid altcoin pairs.\
Margin for Long and Short Positions: 100% (1× leverage assumed; no margin amplification).\
Indicator Settings: Default Configuration.\
Entry RSI: 14 length, cross up 31 on 3m\
Exit RSI: 14 length, cross down 69 on 3m\
Min profit gate: 2.4% from average\
AO count: 5\
First AO deviation: 1.3%\
Deviation step multiplier: 1.3\
Order size multiplier: 1.25\
Strategy: Long Only.

🔷 STRATEGY RESULTS\
⚠️ Remember, past results do not guarantee future performance.\
Net Profit: +450.18 USDT (+4.50%)\
Max Drawdown: 74.88 USDT (0.73%)\
Total Closed Trades: 121\
Percent Profitable: 82.64% (100 / 121)\
Profit Factor: 11.703

Reference TradingView Pine backtest on BYBIT:HYPEUSDT.P (3m chart), Feb 23 --- May 20, 2026 (≈ 86 days). The reference period captures HYPE's choppy intraday oscillation phase after the early-2026 drawdown, which is structurally favorable for a dual-RSI cycle strategy --- RSI repeatedly cycled between the 31 and 69 thresholds, producing dense fill opportunities. The unusually high Profit Factor (11.7) and Win Rate (82.6%) reflect this regime fit and should NOT be extrapolated to all conditions: in trending regimes (sustained up- or down-moves) the RSI rotation signals fire less frequently and the bounded ladder may hold positions through extended unrealized drawdowns. The test ran on perpetual data with 0.08% commission and 3-tick slippage, which is conservative relative to actual Bybit linear taker rates (~0.055%). Re-test on your own venue with venue-specific commission and slippage before live deployment.

🔷 How to Use It:\
🔸 Adjust Settings: Set the base and AO sizes so that the worst-case full-ladder fill is within your personal per-trade risk budget. The default 0.9% base + 5 geometric AOs lands at ~9.93% of equity --- scale linearly to your account size. Confirm RSI thresholds match the asset's actual range: some pairs oscillate between 25/75, others between 35/65 --- re-calibrate based on the last 1--3 months of intraday RSI behavior.

🔸 Results Review: Verify Maximum Drawdown stays within your personal risk budget. The strategy has no stop loss, so the worst-case unrealized loss occurs when all 5 AOs fill at -11.76% and price continues to fall. Calculate this scenario explicitly: if the ladder fills entirely and the asset drops a further X% beyond AO5, what is your unrealized P&L? That number is your hard floor --- confirm you are comfortable with it before going live.

🔸 Create alerts to trigger the connected bot: The strategy exposes three alert events --- entry (base order open), AO add-funds (averaging-order fill), close-at-market (full exit on RSI rotation + min-profit gate). Configure the alert in TradingView with the webhook URL pointing to your bot's signal endpoint. Bot ID, Email Token, and Pair label are exposed in the script inputs and substituted into the JSON payload automatically.

🔷 INDICATOR SETTINGS\
Base Order Size (USDT) --- Notional of the base entry order.\
Use LIMIT for Base --- Toggle market vs limit entry on the base order.\
Averaging Orders per Trade --- Total number of AOs in the ladder (default 5).\
First AO Size (USDT) --- Notional of the first AO; subsequent AOs scale by Order Size Multiplier.\
Deviation to First AO (%) --- Drop from base entry to fire AO1.\
Deviation Step Multiplier --- Multiplier applied to each subsequent step (geometric progression of deviations).\
Order Size Multiplier --- Multiplier applied to each subsequent AO notional (geometric progression of sizes).\
Entry RSI --- Timeframe, length, and cross-up level for the base entry gate.\
Exit RSI --- Timeframe, length, and cross-down level for the exit gate.\
Minimum Profit (%) --- Profit floor; the exit signal only fires once price is ≥ this above average entry.\
Limit Backtest Period --- Optional date filter for the strategy run.\
DCA Bot Webhook --- Bot ID, Email Token, and Pair label for routing to the connected execution layer.\
Visualization --- Toggles for the DCA ladder lines, fill labels, and status table.

👨🏻‍💻💭 We hope this tool helps enhance your trading. Your feedback is invaluable, so feel free to share any suggestions for improvements or new features you'd like to see implemented.

__\
The information and publications within the 3Commas TradingView account are not meant to be and do not constitute financial, investment, trading, or other types of advice or recommendations supplied or endorsed by 3Commas and any of the parties acting on behalf of 3Commas, including its employees, contractors, ambassadors, etc.