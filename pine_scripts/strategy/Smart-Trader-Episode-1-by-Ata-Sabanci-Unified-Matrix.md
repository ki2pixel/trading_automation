Jan 4
⚠️ **CRITICAL: READ BEFORE USING** ⚠️

This strategy is **100% VOLUME-BASED** and requires **Lower Timeframe (LTF) intrabar data** for accurate calculations. Please understand the following limitations before using:

**📊 DATA ACCURACY LEVELS:**
• **1T (Tick)** — Most accurate, real volume distribution per tick
• **1S (1 Second)** — Reasonably accurate approximation
• **15S (15 Seconds)** — Good approximation, longer historical data available
• **1M (1 Minute)** — Rough approximation, maximum historical data range

**⚠️ BACKTEST & REPLAY LIMITATIONS:**
• TradingView's Strategy Tester uses historical LTF data which may be limited depending on your subscription plan
• Replay mode results may differ from live trading due to data availability
• For longer backtest periods, use higher LTF settings (15S or 1M)
• Not all symbols/exchanges support tick-level data
• Crypto and Forex typically have better LTF data availability than stocks

**💡 A NOTE ON TOOLS:**
Successful trading requires proper tools. Higher TradingView plans provide access to more historical intrabar data, which directly impacts the accuracy of volume-based calculations. More precise volume data leads to more reliable signals. Consider this when evaluating your trading infrastructure.


**WHY "EPISODE 1"?**

This strategy is titled "Episode 1" because it focuses exclusively on **Highest Buyers (HB)** — a single but powerful concept in volume analysis.

**The Philosophy:**
A single high-volume buying event can tell us a story about market psychology:
• Where did the biggest buyers enter?
• How much of their power remains?
• Are sellers consuming their advantage?
• At what rate is the balance shifting?

By focusing on just ONE aspect of volume analysis, traders can deeply understand how a buying surge affects future price action before moving to more complex multi-factor analysis.

**The Reality:**
This script alone is approximately **2000 lines of code** — and it only analyzes buyers. A comprehensive system covering all aspects (sellers, combined analysis, multi-timeframe correlation) would be significantly larger and computationally heavier. Breaking this into focused modules allows for:
• Deeper understanding of each component
• Lighter, more responsive scripts
• Educational progression from simple to complex


**OVERVIEW**

Smart Trader EP1 is a volume-based trading strategy that tracks the balance of power between buyers and sellers through the lens of the **Highest Buyers event**. Unlike traditional indicators that rely on price patterns or mathematical formulas, this strategy analyzes *actual volume flow* to identify who is in control of the market.

The core philosophy is simple: **markets move when one side (buyers or sellers) exhausts their power while the opposing side accumulates strength.** By measuring this power shift in real-time, the strategy identifies high-probability entry and exit points.


**HOW IT WORKS**

**1. Volume Engine**
The strategy splits each candle's volume into buying volume and selling volume using intrabar data. In *Intrabar (Precise)* mode, it uses actual tick-by-tick or second-by-second data to calculate the exact buy/sell distribution. In *Geometry* mode, it approximates based on candle structure (close position within the range).

**2. Event Detection**
Within the lookback window, the strategy identifies key events:
• **HB (Highest Buyers)** — The candle with maximum buying volume (potential resistance when exhausted)
• **HS (Highest Sellers)** — The candle with maximum selling volume (potential support when exhausted)
• **LB (Lowest Buyers)** — The candle with minimum buying volume (buyer absence)
• **LS (Lowest Sellers)** — The candle with minimum selling volume (seller absence)

These events create dynamic support and resistance levels based on actual volume, not arbitrary price levels.

**3. Power Tracking (Attrition Model)**
For the Highest Buyers event (HB), the strategy tracks:
• **Start Power (X)** — The initial buying volume at the HB event
• **Consumed Power (Y)** — How much selling volume has accumulated since the event
• **Remaining Power (Z)** — Start Power minus Consumed Power (X - Y)
• **Opponent Dominance** — When Remaining Power goes negative (Z < 0), sellers have overtaken buyers

Think of it like a battle: buyers establish a position (HB), and sellers gradually consume their power. When buyers' power is exhausted (Remaining Power ≤ 0), sellers have taken control.

**4. Depletion Markers**
Visual markers appear on the chart when power reaches critical thresholds:
• **🔋** — Buyers consumed 100% (Remaining = 0)
• **🚨** — Buyers consumed 200% (Opponent Dominance = 100%)
• **🪫** — Sellers consumed 100%
• **⚠️** — Sellers consumed 200%

**5. Cumulative Delta**
Beyond tracking power at specific events, the strategy calculates the cumulative buy volume minus sell volume since the HB event. This shows the *net flow* of money:
• **Positive Delta** — More buying than selling since HB (bullish pressure)
• **Negative Delta** — More selling than buying since HB (bearish pressure)

**6. Trend Channel**
A 5-point linear regression channel identifies the current trend:
• **UPTREND** — Both upper and lower channel lines slope upward
• **DOWNTREND** — Both lines slope downward
• **RANGING** — Mixed or flat slopes

The strategy also tracks where the HB event occurred within this channel (TOP, UPPER, MIDDLE, LOWER, BOTTOM) to contextualize the signal.

**7. Nearest Event Analysis**
The strategy identifies which event is closest to the current candle and analyzes the price action *after* that event:
• How many bullish vs bearish candles followed?
• Does post-event momentum confirm or contradict the event type?

This prevents false signals when, for example, a bearish event occurs but is immediately followed by strong bullish candles.


**SIGNAL LOGIC**

**🟢 LONG Signal Conditions:**
• Uptrend with positive cumulative delta and buyers accumulating
• At channel bottom/lower with strong buyer power remaining
• After a bearish event (HS) with bullish post-event momentum (reversal signal)
• Ranging market with positive delta and strong power

**🔴 SHORT Signal Conditions:**
• Downtrend with negative cumulative delta and sellers in control
• Opponent Dominance (buyer power exhausted) with bearish momentum
• Buyer Trap: HB at TOP in uptrend but power exhausted and delta negative
• After a bullish event (HB) with bearish post-event momentum (trap signal)

**⏳ NO_TRADE Conditions:**
• Conflicting signals (e.g., bearish event but bullish post-momentum)
• Ranging market without clear direction
• Mixed power readings
• Price position contradicts signal direction


**STRATEGY EXECUTION**

**Entry Rules:**
• Enter LONG when signal is "LONG" and conditions are valid
• Enter SHORT when signal is "SHORT" and conditions are valid
• **Pyramid**: Up to 2 entries allowed in the same direction (configurable)
• Each entry uses 10% of equity by default
• Only one entry per confirmed candle (prevents multiple fills)

**Stop Loss (Event Line Based):**
• **LONG positions**: Stop Loss placed below the HS line (seller support level)
• **SHORT positions**: Stop Loss placed above the HB line (buyer resistance level)
• A small buffer percentage is added to prevent premature stops

**Take Profit (Event Line Based):**
• **LONG positions**: Take Profit near the HB line (buyer resistance target)
• **SHORT positions**: Take Profit near the HS line (seller support target)
• A small buffer percentage ensures realistic fill expectations

**Exit Rules:**
• Exit LONG when signal changes to SHORT
• Exit SHORT when signal changes to LONG
• **NO_TRADE signal = HOLD** (do not exit, wait for clear direction)
• SL/TP orders remain active regardless of signal changes


**SETTINGS GUIDE**

**⚙️ General Settings:**
• *Calculation Method* — Choose between Intrabar (Precise) or Geometry (approximation)
• *Intrabar Resolution* — LTF for volume data (1T, 1S, 15S, 1M)
• *Lookback Length* — Window for scanning events (10-150 bars)
• *Timezone Offset* — Adjust clock display to your local time

**📊 Matrix Display Settings:**
• *Show Unified Matrix* — Toggle the information dashboard
• *Show Event Lines* — Toggle horizontal lines at event prices
• *Panel Size/Position* — Customize dashboard appearance
• *Projection Bars* — Extend event lines into the future
• *Depletion Threshold* — Percentage for depletion markers (default: 100%)

**🏷️ Rank Labels Settings:**
• *Show Rank Labels (HB/HS)* — Display labels on highest volume candles
• *Show Low Labels (LB/LS)* — Display labels on lowest volume candles
• *Ranks Count* — Number of rankings to display (1-5)

**📐 Trend Channel Settings:**
• *Show Trend Channel* — Toggle the 5-point regression channel
• *Line Color/Fill/Width/Style* — Customize channel appearance

**🎯 Trade Signal Settings:**
• *Long: Min Remaining Power %* — Minimum buyer power for LONG signal (default: 50%)
• *Short: Max Remaining Power %* — Maximum power for SHORT signal (default: 30%)
• *Opponent Dominance Threshold* — When to consider power "exhausted" (default: 0%)
• *Max Decay Angle* — Maximum consumption rate for valid entries (default: 60°)

**📈 Strategy Execution Settings:**
• *Enable Strategy* — Turn automatic trading on/off
• *Allow LONG/SHORT* — Enable or disable specific directions
• *Max Pyramid Entries* — Maximum entries in same direction (1-3)
• *SL Buffer %* — Distance below/above event line for stop loss (default: 0.15%)
• *TP Buffer %* — Distance from event line for take profit (default: 0.05%)


**VISUAL ELEMENTS**

**Chart Labels:**
• **#1 HB** — Highest Buyers (rank label on candle high)
• **#1 HS** — Highest Sellers (rank label on candle low)
• **#1 LB** — Lowest Buyers (rank label on candle high)
• **#1 LS** — Lowest Sellers (rank label on candle low)
• **🔋 / 🚨** — Buyer power depletion markers
• **🪫 / ⚠️** — Seller power depletion markers

**Event Lines:**
• **Blue horizontal lines** — HB price levels (buyer entry points)
• **Red horizontal lines** — HS price levels (seller entry points)
• **Cyan lines** — LB price levels
• **Orange lines** — LS price levels
• **Dashed extensions** — Projected levels into future bars

**Trend Channel:**
• **Orange lines** — Upper and lower channel boundaries (5-point regression)
• **Orange fill** — Channel area (90% transparency)

**Matrix Dashboard (6 rows):**
• Row 1: Header with symbol, LTF setting, and local clock
• Row 2: Volume snapshot (Total, Buy, Sell, Delta)
• Row 3: Column headers
• Row 4: Highest Buyers data (Age, Start Power, Consumed, Remaining, Decay, ETA)
• Row 5: Highest Sellers data
• Row 6: Signal Evaluation (Trend, Zone, Nearest Event, Signal, Reason)

**Strategy Markers:**
• **Green triangle up** — LONG entry
• **Red triangle down** — SHORT entry
• **Faded triangles** — Pyramid entries
• **Colored lines** — SL (red) and TP (green) levels when in position


**BEST PRACTICES**

**For Maximum Accuracy:**
1. Use **1T (tick)** or **1S** intrabar resolution when available
2. Trade liquid markets with good volume data (crypto majors, forex majors, high-volume stocks)
3. Use smaller lookback length (20-30) to ensure all bars have valid LTF data
4. Monitor the "Intrabar Valid Bars" counter in the matrix header
5. If you see data warnings, reduce lookback or increase LTF resolution

**For Longer Backtests:**
1. Use **15S or 1M** intrabar resolution for more historical data
2. Increase lookback length if needed
3. Understand that accuracy decreases with higher LTF settings
4. Consider using Geometry mode for very long backtests (approximation but always available)

**Understanding the Signals:**
• Pay attention to the signal *reasoning* shown in the matrix — it explains WHY
• **NO_TRADE** means the system sees conflicting factors — respect this caution
• Event lines act as dynamic S/R — they update as new volume events occur
• Cumulative Delta (Δ) often provides early warning of trend changes

**Risk Management:**
• The default 10% per entry with max 2 pyramids = 20% maximum exposure
• Event-line-based SL/TP provides logical levels based on actual volume events
• Always verify signals with your own analysis before trading


**INTERPRETING THE MATRIX**

**Power Status Examples:**
• *Remaining Power: 75%* — Buyers still have most of their strength
• *Remaining Power: 25%* — Buyers nearly exhausted, watch for reversal
• *Opponent Dominance: -50%* — Sellers have consumed 150% of buyer power (strong bearish)

**Decay Angle:**
• *Low angle (0-30°)* — Slow consumption, power lasting longer
• *High angle (60-90°)* — Rapid consumption, expect quick exhaustion

**ETA to Parity:**
• Shows estimated bars until Remaining Power reaches zero
• *"Overtaken"* with 🚨 means sellers have already dominated


**LIMITATIONS & DISCLAIMER**

**Technical Limitations:**
• Requires sufficient historical LTF data (varies by TradingView plan and symbol)
• Intrabar (Precise) mode may show invalid data warnings on symbols with limited history
• Strategy tester may not have access to the same LTF data as live trading
• Maximum 500 lines and 500 labels (TradingView platform limits)

**Important Notes:**
• This strategy focuses on **Highest Buyers only** — it does not analyze all market factors
• Past performance does not guarantee future results
• Volume data quality varies significantly between symbols and exchanges
• The strategy's signals are analytical tools, not trading recommendations

**Risk Disclaimer:**
This strategy is provided for **educational and informational purposes only**. Trading involves substantial risk of loss and is not suitable for all investors.

• Always use proper risk management
• Never risk more than you can afford to lose
• Backtest results may differ significantly from live trading
• You are solely responsible for your trading decisions


**TECHNICAL SPECIFICATIONS**

• Pine Script Version: 6
• Calculation: calc_on_every_tick=true, use_bar_magnifier=true
• Default Capital: 10,000
• Default Position Size: 10% of equity
• Maximum Lines: 500
• Maximum Labels: 500
• External Library: TradingView/ta/10 (for requestUpAndDownVolume)


*Smart Trader EP1 — Understanding Volume, One Event at a Time*
Jan 6
Release Notes
Update: Confirmed-Bar Ranking Snapshot (HB/HS/LB/LS)

What changed
• The HB/HS/LB/LS ranking scan is now finalized only after the candle closes (confirmed bar).
• During a live / forming candle, the script keeps showing the last confirmed snapshot instead of re-ranking on every tick.

Why this change
Because the script runs with tick-level updates, a newly opened candle can briefly show “lowest” events (LB/LS) simply because volume is still developing from near-zero at the start of the bar.
This update removes that early-bar artifact by locking the ranking snapshot on candle close, making events and labels more stable and trustworthy.

What you’ll notice
• No more instant LB/LS flashes at the start of each new candle.
• Rank labels and event lines look more stable with less visual jumping.
• The core logic remains the same — only the commit timing of the ranking snapshot changed.

Note
This does not change the Volume Engine logic (Intrabar Precise vs Geometry). It only changes when the HB/HS/LB/LS snapshot is committed.