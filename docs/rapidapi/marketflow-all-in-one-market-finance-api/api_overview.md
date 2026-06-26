API Overview
============

MarketFlow is designed for fintech developers, market analysts, AI agents, and investors who need seamless access to global financial data --- all at highly competitive rates.

Gain real-time and historical market data for Stocks, ETFs, Cryptocurrencies, Commodities, Forex, Bonds, Futures, and more --- all through one unified API.

📋 Pricing & Usage Policy
-------------------------

### Free Plan

-   Monthly Quota: 500 requests/month
-   Overage Charges: $0.01 USD per request beyond the free quota
-   Example: If you make 1,500 requests in a month, you will be charged for 1,000 requests = $10.00 USD

### Important Notes

⚠️ All billing and usage tracking systems are managed entirely by RapidAPI.com

-   Usage data is automatically recorded by RapidAPI's infrastructure
-   We do not have control over billing, tracking, or request counting
-   For any billing disputes, usage questions, or refund requests, please contact [RapidAPI Support](https://rapidapi.com/support)

### Recommendations

-   Monitor your usage regularly through your RapidAPI dashboard
-   Implement rate limiting in your application to avoid unexpected charges
-   Consider upgrading to a paid plan if you need higher request volumes

* * * * *

Need Higher Limits?\
Upgrade to our paid plans for better rates and higher quotas. Contact us for enterprise pricing options.

About MarketFlow
----------------

MarketFlow is your all-in-one financial market API, empowering developers to build powerful financial applications, trading systems, analytics tools, and investment platforms.

Access accurate and timely data from 400,000+ symbols, covering 174+ exchanges across 62+ countries.

Our RESTful API is designed for simplicity and performance --- using clear, intuitive endpoints and standard HTTP GET parameters.

Responses are delivered in lightweight JSON format, ensuring effortless integration into any project or system.

Key Features
------------

### 🆕 Latest Updates (v1.0.5)

-   ETF Flows: New category with 9 endpoints for Bitcoin and Ethereum ETF tracking
    -   `/etf/bitcoin/flows`: Historical daily flow data for all Bitcoin spot ETFs (GBTC, IBIT, FBTC, ARKB, BITB, BTCO, HODL, BRRR, EZBC, BTCW, BTC)
    -   `/etf/bitcoin/overview`: Complete overview of all Bitcoin ETFs with AUM, market cap, price, volume, holdings, and management fees
    -   `/etf/bitcoin/heatmap`: Heatmap visualization data with price changes, volume, AUM, and BTC holdings in USD
    -   `/etf/bitcoin/summary`: Aggregate totals for all Bitcoin ETFs (total volume, market cap, AUM)
    -   `/etf/bitcoin/premium-discount`: Historical NAV vs market price premium/discount data per ETF
    -   `/etf/ethereum/flows`: Historical daily flow data for all Ethereum spot ETFs (ETHA, FETH, ETHW, TETH, ETHV, QETH, EZET, ETHE, ETH)
    -   `/etf/ethereum/overview`: Complete overview of all Ethereum ETFs with fund details and asset metrics
    -   `/etf/ethereum/heatmap`: Heatmap visualization data with price changes, volume, and ETH holdings
    -   `/etf/ethereum/summary`: Aggregate totals for all Ethereum ETFs (total volume, market cap, AUM)
    -   Per-ETF flow breakdown with net flow and asset price tracking

### 📜 Previous Updates (v1.0.4)

-   Market Data V2: New advanced chart data category with 5 powerful endpoints
    -   `/v2/how-to-use`: Complete step-by-step guide for using Market Data V2 endpoints
    -   `/v2/search/market`: Search for trading symbols across all markets (crypto, forex, stocks, commodities)
        -   Returns symbols in EXCHANGE:SYMBOL format for use in chart endpoints
        -   Support for 50+ exchanges globally
    -   `/v2/chart/price`: Get latest OHLCV price data with customizable timeframes
        -   Support for multiple timeframes: 1m-45m (minutes), 1h-4h (hours), D/W/M (daily/weekly/monthly)
        -   Configurable range: 1-5000 candles
        -   Timezone support for accurate time conversion
    -   `/v2/chart/historical`: Fetch historical data before a specific date
        -   Perfect for backtesting and historical analysis
        -   Date-based filtering with customizable range
    -   `/v2/chart/range`: Get data within a specific date range (from-to)
        -   Ideal for analyzing specific time periods
        -   Quarterly, yearly, or custom date range analysis
    -   Unified symbol format (EXCHANGE:SYMBOL) across all endpoints
    -   Support for crypto (BINANCE:BTCUSDT), forex (OANDA:XAUUSD), stocks (NASDAQ:AAPL), and more
    -   Multiple timeframe options from 1-minute to yearly data
    -   Timezone-aware data for global market analysis

### 📜 Previous Updates (v1.0.3)

-   Crypto Intelligence Endpoints: 3 new advanced cryptocurrency analysis tools
    -   `/crypto/walls`: Detect large orderbook walls (>3x average) to identify strong support and resistance levels
        -   Real-time bid/ask wall detection
        -   Automatic fallback between spot and futures markets
        -   60-second cache for near real-time analysis
    -   `/crypto/strong-trend`: Classify trending coins as strong_bullish (>5%), strong_bearish (<-5%), or neutral
        -   Combines trending data with 24h price performance
        -   Distinguishes FOMO-driven vs FUD-driven trends
        -   5-minute cache for optimal performance
    -   `/crypto/correlation`: Calculate Pearson correlation between cryptocurrencies
        -   30-day correlation analysis with top 5 altcoins (ETH, SOL, BNB, XRP, ADA)
        -   Identifies highly_correlated (>0.8), moderately_correlated (0.5-0.8), or decoupled (<0.5) pairs
        -   Helps find diversification opportunities and market decoupling patterns
        -   30-minute cache for historical stability

### 📜 Previous Updates (v1.0.2)

-   Smart Money Tracking: New category with 4 powerful endpoints for institutional investor analysis
    -   `/smartmoney/guru-consensus`: Find stocks held by multiple legendary investors (Buffett, Dalio, Ackman, etc.)
    -   `/smartmoney/guru-performance`: Track portfolio performance with unrealized P&L and win rate analysis
    -   `/smartmoney/institutional-flow`: Analyze buy/sell ratios to identify accumulation or distribution phases
    -   `/smartmoney/how-to-use`: Complete documentation and usage guide
    -   Track 15+ legendary investors including Warren Buffett, Ray Dalio, Bill Ackman, Michael Burry, and more
    -   Identify high-conviction stocks agreed upon by multiple investment gurus
    -   Monitor institutional sentiment and smart money movements
    -   Redis caching for optimal performance

### 📜 Previous Updates (v1.0.1)

-   Global Heatmap Endpoint: New `/global-heatmap` endpoint for cryptocurrency position breakdown analysis
    -   Get coin position breakdown by cohort segments (size and PnL)
    -   Support for all major cryptocurrencies (BTC, ETH, SOL, and more)
    -   30-minute cache for optimal performance
    -   Proxy rotation for reliable data fetching

### 📊 Comprehensive Market Data

-   Market Data: Real-time OHLC candles, time series data, and instrument search
-   Earnings Calendar: Track earnings announcements, dates, and detailed reports
-   Dividends Calendar: Monitor dividend events and payout information
-   IPO Calendar: Stay updated on new public offerings and market debuts
-   Stock Splits: Get notified about corporate actions and split events

### 👥 Investor Activity Tracking

-   Investor Portfolio: Access holdings data from top investors and fund managers
-   Trade Activity: Monitor buy/sell activities with detailed transaction history
-   Investor Directory: Comprehensive list of active investors and their profiles
-   Track institutional movements and smart money flows

### 🐋 Smart Money Tracking (NEW)

-   Guru Consensus: Find stocks held by 2+ legendary investors
-   Performance Analysis: Track portfolio performance with unrealized P&L, win rates, and best/worst performers
-   Institutional Flow: Analyze buy/sell ratios to identify accumulation or distribution phases
-   Market Sentiment: Detect bullish/bearish institutional sentiment
-   15+ Legendary Investors: Warren Buffett, Ray Dalio, Bill Ackman, Michael Burry, George Soros, Carl Icahn, and more
-   Identify high-conviction stocks agreed upon by multiple investment gurus
-   Monitor smart money movements and institutional rotation
-   Quarterly reporting with historical trend analysis

### 📈 ETF Flows

-   Bitcoin ETF Flows: Daily net flow data for all Bitcoin spot ETFs with per-ETF breakdown
-   Bitcoin ETF Overview: Fund details, AUM, market cap, price, volume, holdings, and management fees
-   Bitcoin ETF Heatmap: Price changes, volume, AUM, market cap, and BTC holdings visualization
-   Bitcoin ETF Summary: Aggregate total volume, market cap, and AUM across all Bitcoin ETFs
-   Bitcoin Premium/Discount: Historical NAV vs market price premium/discount tracking
-   Ethereum ETF Flows: Daily net flow data for all Ethereum spot ETFs with per-ETF breakdown
-   Ethereum ETF Overview: Fund details, AUM, market cap, price, volume, and holdings
-   Ethereum ETF Heatmap: Price changes, volume, AUM, and ETH holdings visualization
-   Ethereum ETF Summary: Aggregate total volume, market cap, and AUM across all Ethereum ETFs
-   Track institutional money flowing into/out of crypto ETFs

### 💰 Cryptocurrency Data

-   Crypto Events Calendar: Real-time cryptocurrency news and events
-   Crypto Details: In-depth information about digital assets
-   Trending Analysis: Top trending coins, NFTs, and categories from CoinGecko
-   Global Heatmap: Coin position breakdown by cohort segments (size and PnL analysis)
-   Orderbook Wall Detection: Identify large buy/sell walls for support/resistance analysis
-   Strong Trend Classification: Distinguish FOMO-driven bullish vs FUD-driven bearish trends
-   Correlation Matrix: Calculate crypto correlations for diversification strategies
-   Updated every 10 minutes for the latest market trends

### 🛠️ Technical Analysis Tools

-   15+ Technical Indicators: SMA, EMA, WMA, RSI, MACD, Bollinger Bands, Stochastic, ATR, ADX, Williams %R, CCI, MFI, OBV, VWAP, Ichimoku
-   Orderbook Analysis: Calculate orderbook imbalance ratios for liquidity analysis
-   VWAP Calculation: Volume-weighted average price from orderbook data
-   Liquidity Mapping: Identify price levels with high volume concentration
-   Support for both crypto and forex markets

API Categories
--------------

### 📈 Market Data

-   Search for instruments and available data providers
-   Retrieve OHLC candle data with multiple timeframe support (1m to 1d)
-   Access historical data with configurable limits (-500 to -10 candles)
-   Support for stocks, forex, commodities, and cryptocurrencies

### 📊 Market Data V2

-   Symbol Search: Find trading symbols across 50+ exchanges with unified EXCHANGE:SYMBOL format
-   Real-time Price Data: Get latest OHLCV data with multiple timeframe options (1m to 12M)
-   Historical Analysis: Fetch data before specific dates for backtesting
-   Date Range Filtering: Analyze specific time periods with from-to date parameters
-   Timezone Support: Accurate time conversion for global market analysis
-   Multi-Asset Support: Crypto, forex, stocks, commodities, and more
-   Flexible Timeframes: Minutes (1-45), hours (1-4), daily, weekly, monthly, quarterly, yearly
-   High Volume Data: Up to 5000 candles per request for comprehensive analysis

### 💼 Corporate Events

-   Earnings: Complete earnings calendar with detailed quarterly/annual reports
-   Dividends: Dividend payment schedules and historical payout data
-   IPOs: Initial public offering calendar and market debut information
-   Stock Splits: Corporate action events and split ratio details

### 👔 Investor Intelligence

-   Portfolio holdings from top investors (Warren Buffett, David Einhorn, Bill Ackman, and more)
-   Trade activity tracking with buy/sell filters
-   Quarterly report date support (Q1, Q2, Q3, Q4)
-   Time range analysis for historical trade patterns

### 🐋 Smart Money Tracking

-   Guru Consensus: Identify stocks held by multiple legendary investors simultaneously
-   Performance Tracking: Monitor portfolio performance with unrealized P&L calculations
-   Institutional Flow: Analyze buy/sell ratios to detect accumulation or distribution phases
-   Market Sentiment: Understand institutional sentiment (bullish/bearish/neutral)
-   Track 15+ legendary investors including Warren Buffett, Ray Dalio, Bill Ackman, Michael Burry, George Soros, and more
-   Find high-conviction stocks agreed upon by investment legends
-   Detect smart money movements before market trends
-   Quarterly reporting with historical comparison support

### 🪙 Cryptocurrency

-   Real-time crypto event calendar
-   Detailed cryptocurrency information and market data
-   Trending assets analysis (coins, NFTs, categories)
-   Global heatmap with position breakdown by cohort segments
-   Orderbook wall detection for support/resistance identification
-   Strong trend classification (bullish/bearish/neutral)
-   Correlation matrix for diversification analysis
-   Integration with CoinGecko and Binance for comprehensive coverage

### 🔧 Trading Tools

-   Technical indicator calculations with customizable parameters
-   Real-time orderbook data from Binance Derivatives
-   Liquidity zone identification for support/resistance levels
-   Market analysis tools for both retail and institutional traders

Technical Specifications
------------------------

### Response Format

-   Content Type: `application/json`
-   Encoding: UTF-8
-   Data Structure: Lightweight, nested JSON objects
-   Error Handling: Standardized error responses with descriptive messages

### Data Coverage

-   400,000+ Symbols: Stocks, ETFs, bonds, commodities, forex pairs
-   174+ Exchanges: Global market coverage
-   62+ Countries: International market access
-   Real-time & Historical: Both current and historical data available

Use Cases
---------

### 🏢 Trading Platforms

Build professional trading applications with real-time market data, technical indicators, and orderbook analysis.

### 📊 Analytics Dashboards

Create comprehensive market analysis tools with earnings calendars, dividend tracking, and investor activity monitoring.

### 🤖 AI & Machine Learning

Feed your AI models with structured, reliable market data for predictive analytics and algorithmic trading.

### 💼 Investment Tools

Develop portfolio management applications with investor tracking, corporate event monitoring, and market intelligence. Track smart money movements and identify high-conviction stocks from legendary investors.

### 📱 Mobile Applications

Power mobile trading apps with fast, cached responses and real-time market updates.

### 🔍 Research & Analysis

Access comprehensive historical data for backtesting, research, and market analysis.

Getting Started
---------------

1.  Browse Endpoints: Explore our organized API endpoints by category
2.  Test Requests: Use the interactive API documentation to test endpoints
3.  Integrate: Copy code snippets in your preferred programming language

Support & Documentation
-----------------------

-   How-to Guides: Step-by-step instructions for complex endpoints
-   Example Responses: Sample data for all endpoint types
-   Error Handling: Comprehensive error response documentation

⚠️ IMPORTANT: Monitor Your Usage
--------------------------------

You are responsible for monitoring your own API usage.

-   RapidAPI provides real-time usage dashboards
-   Set up alerts in your RapidAPI account to avoid overages
-   Implement proper error handling and rate limiting in your code
-   Test with small volumes before deploying to production

We are not responsible for charges incurred due to:

-   Lack of usage monitoring on your end
-   Missing rate limits in your application
-   Automated scripts running without oversight
-   Failure to read pricing terms

All charges are processed by RapidAPI. We have no control over billing.