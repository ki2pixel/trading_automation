# SheetsFinance Docs | Technical Analysis

# [Technical Analysis](#/functions/technicals?id=technical-analysis)

Technical analysis is achieved using the `SF_TECHNICAL()` function. The function allows for the generation of a specified technical analysis layered over the historical price data of a stock, crypto or ETF. You are able to define a timeframe and apply the analysis with a specific period of that timeframe. For example, a 20-day SMA with daily data or a 20-minute SMA with minute-by-minute intra-day data.

```
=SF_TECHNICAL(stock, type, timeframe, startDate, endDate, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` is the analysis type chained together (using the `&` operator) with the additional display items you want to include in your output. The available analysis types are available below. Remember to include the period, for example `sma20` would be a Simple Moving Average (SMA) applied over 20 periods. Some examples are `"sma20&all"`, `"ema50&date&close"` and `"williams100&date&high&low"`.
-   `timeframe` defines the candle/bin/granularity size, for example `"daily"`, `"1min"` or `"30min"`. All timeframe options are outlined below.
-   `startDate` is the starting date of the time series, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`
-   `endDate` is the ending date of the time series, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `options` adjusts the formatting of the output. There are currently two available options, you can set this field to `"NH"` for no header row and reverse the order of the output with `"-"`. You can combine options with the `&` operator, for example `"NH&-"`.

> **IMPORTANT:** See [how to use the type parameter correctly](#/functions/technicals?id=how-to-use-the-type-parameter-correctly) below for a more detailed explanation on how to construct the `type` correctly.

The analysis options for `type` are:

-   Simple Moving Average (`"sma"`)
-   Exponential Moving Average (`"ema"`)
-   Weighted Moving Average (`"wma"`)
-   Double Exponential Moving Average (`"dema"`)
-   Triple Exponential Moving Average (`"tema"`)
-   Williams %R (`"williams"`)
-   Relative Strength Index Indicator (`"rsi"`)
-   Average Directional Index (`"adx"`)
-   Standard Deviation (`"standardDeviation"`)

The additional display options for `type` are:

-   All (`"all"`)
-   Date (`"date"`)
-   Open (`"open"`)
-   High (`"high"`)
-   Low (`"low"`)
-   Close (`"close"`)
-   Volume (`"volume"`)

The `timeframe` options are:

-   Daily (`"daily"`)
-   1 minute (`"1min"`)
-   5 minutes (`"5min"`)
-   15 minutes (`"15min"`)
-   30 minutes (`"30min"`)
-   1 hour (`"1hour"`)
-   4 hour (`"4hour"`)

## [How to use the `type` parameter correctly](#/functions/technicals?id=how-to-use-the-type-parameter-correctly)

All the magic happens in the `type` parameter of the `SF_TECHNICALS()` function. There are three key parts to it:

1.  Analysis type
2.  Period
3.  Additional display items

These three items are combined as follows:

```
[Analysis type][Period]&[Additional display 1]&[Additional display item 2]...
```

For example if you want a Simple Moving Average (SMA) applied over 20 periods and you'd like to generate the time-series along side the date and close price then your `type` parameter would be as follows:

```
20sma&date&close
```

If you want an Exponential Moving Average (EMA) applied over 100 periods and you'd like to generate all available display items then your `type` parameter would be as follows:

```
100ema&all
```

## [Examples](#/functions/technicals?id=examples)

Okay this all sounds a bit complex so here are some really easy examples to get you started.

### [Example 1 - 20 day SMA with all parameters](#/functions/technicals?id=example-1-20-day-sma-with-all-parameters)

```
=SF_TECHNICAL("AAPL", "20sma&all", "daily", "2022-01-01", "2022-11-26")
```

![Technicals Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/technicals1.png "Technicals Example 1")

### [Example 2 - 100 day EMA with only date and close](#/functions/technicals?id=example-2-100-day-ema-with-only-date-and-close)

```
=SF_TECHNICAL("AAPL", "50ema&date&close", "daily", "2022-01-01", "2022-11-26")
```

![Technicals Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/technicals2.png "Technicals Example 2")

### [Example 3 - 10 minute intra-day Williams %R with all parameters](#/functions/technicals?id=example-3-10-minute-intra-day-williams-r-with-all-parameters)

```
=SF_TECHNICAL("AAPL", "10williams&all", "1min", "2022-01-01", "2022-11-26")
```

![Technicals Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/technicals3.png "Technicals Example 3")

### [Example 4 - 4 hour intra-day TEMA with date and close, no headers](#/functions/technicals?id=example-4-4-hour-intra-day-tema-with-date-and-close-no-headers)

```
=SF_TECHNICAL("AAPL", "4tema&date&close", "1hour", "2022-01-01", "2022-11-26", "NH")
```

![Technicals Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/technicals4.png "Technicals Example 4")

## Embedded Content