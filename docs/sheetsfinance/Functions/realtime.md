# SheetsFinance Docs | Realtime

# [Real-time](#/functions/realtime?id=real-time)

The real-time data type delivers current pricing information on over 80,000 financial assets globally 🚀 This is the go-to function for your portfolios or watchlists. The real-time data is second-accurate for selected exchanges, see [Available Markets](#/use/exchanges) for more information. The data is output as a single cell if fully specified or as a multi-cell array if multiple metrics are selected.

```
=SF(symbol, "realTime", metric, "", options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol. Check out the [Real-time Batch](#/functions/realtimeBatch) function if you're after real-time data on up to 2000 stocks at the same time!
-   `metric` selects what metrics to display (see options below), display all metrics by using `"all"`. If this argument is ommitted the function defaults to current real-time price (`"price"`), see example 1 below. Chain together as many metrics as you'd like using `&`, e.g., `"price&open&previousClose"`.
-   `options` adjusts the formatting of the output. There is currently only one available option for real-time data. You can set this field to `"NH"` for no header row for a multi-cell output.

The real-time function has the following metrics:

-   All (`"all"`)
-   Current Price (`"price"`)
-   Open (`"open"`)
-   Previous Close (`"previousClose"`)
-   Change (`"change"`)
-   Change % (`"changesPercentage"`)
-   Day Low (`"dayLow"`)
-   Day High (`"dayHigh"`)
-   Volume (`"volume"`)
-   Quote Timestamp (`"timestamp"`)
-   Name (`"name"`)
-   Exchange (`"exchange"`)
-   Market Cap (`"marketCap"`)
-   Year High (`"yearHigh"`)
-   Year Low (`"yearLow"`)
-   Price Avg 50 (`"priceAvg50"`)
-   Price Avg 200 (`"priceAvg200"`)
-   Avg Volume (`"avgVolume"`) - **Note:** This is 3-month average volume
-   Earnnings Announce Date (`"earningsAnnouncement"`)
-   P/E Ratio (`"pe"`)
-   EPS (ttm) (`"eps"`)
-   Shares Outstanding (`"sharesOutstanding"`)

> **HOT TIP:** If you're after a large amount of real-time data at once (e.g. in a watchlist) consider using our [Real-time Batch](#/functions/realtimeBatch) functionality.

## [Examples](#/functions/realtime?id=examples)

### [Example 1 - Current Price](#/functions/realtime?id=example-1-current-price)

Set the subtype to `"price"` for the current price quote for the stock, coin or ETF.

```
=SF("AAPL", "realTime", "price")

125.43
```

Current price is the default return of the real-time function so a faster way to get the same information is the neater:

```
=SF("AAPL")

125.43
```

### [Example 2 - Single metric](#/functions/realtime?id=example-2-single-metric)

Set the subtype to a single metric, e.g.`"open"`, for the day's opening price for the stock.

```
=SF("AAPL", "realTime", "open")

127.82
```

Data is returned as a single-cell number.

### [Example 3 - Multiple metrics](#/functions/realtime?id=example-3-multiple-metrics)

Chain together metrics with th `&` operator to return multiple columns of data at once. A header row is included automatically. See example 5 for removing the header row.

```
=SF("AAPL", "realTime", "price&previousClose&changesPercentage&volume")
```

![RealTime Multiple Metrics](https://cdn.sheetsfinance.com/public-site/img/docs/realTime_3.png "RealTime Multiple Metrics")

### [Example 4 - All metrics](#/functions/realtime?id=example-4-all-metrics)

Dump all available real-time metrics into a multi-cell array. A header row is included automatically.

```
=SF("AAPL", "realTime", "all")
```

![RealTime All Metrics](https://cdn.sheetsfinance.com/public-site/img/docs/realTime_4.png "RealTime All Metrics")

### [Example 5 - Multiple metrics, no header row](#/functions/realtime?id=example-5-multiple-metrics-no-header-row)

Here we've added `"NH"` as the options argument to remove the header row. **Note:** The extra `""` must be included as a placeholder for preceeding argument.

```
=SF("AAPL", "realTime", "price&previousClose&changesPercentage&volume", "", "NH")
```

![RealTime no header row](https://cdn.sheetsfinance.com/public-site/img/docs/realTime_5.png "RealTime no header row")

## Embedded Content