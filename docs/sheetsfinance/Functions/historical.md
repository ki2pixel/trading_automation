# SheetsFinance Docs | Historical EOD

# [Historical EOD Data](#/functions/historical?id=historical-eod-data)

The `historical` data type allows you to directly access historical End of Day (EOD) data from the last 30+ years. The `historical` function accepts batching, so you can also use it to pull EOD data points for 1000s of symbols at the same time. Read more on batching under [Historical EOD Batch](#/functions/historicalBatch).

```
=SF(symbol(s), "historical", metrics, date, options)
```

-   `symbol(s)` is the ticker symbol(s) of the financial asset(s) (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol. You can also reference a range of tickers (e.g. `A1:A100`), read more on batching under [Historical EOD Batch](#/functions/historicalBatch).
-   `metrics` is the historical metric(s) you are after, for example `"open"`. You can leave this blank or set it to `"all"` to output ALL available historical metrics. You can also chain together multiple metrics using the `&` operator, for example `"open&high&low&close"`. See the full list of available metrics below.
-   `date` is the date for the historical EOD data, e.g., `"2025-02-05"`. If the date entered is a weekend then the data for the most recent trading day will be returned. The function doesn't account for all global public holidays or other non-trading days so if you get a "no data" error just check that the stock was open for trading that day!
-   `options` adjusts the formatting of the output. There are two available options. (1) `"NH"` for no header row, or (2) `"includeWeekends"` to include weekends in the output (particularly useful for assets that trade closer to 24/7 such as FOREX or crypto). These options can be chained together with the `&` operator, for example `"NH&includeWeekends"`.

The `historical` data type has the following metrics to select from:

-   Open (`"open"`)
-   High (`"high"`)
-   Low (`"low"`)
-   Close (`"close"`)
-   Close (Adj.) (`"adjClose"`)
-   Volume (`"volume"`)
-   Market Capitalisation (`"marketCap"`) - Cannot be batched, see [Historical Market Capitalisation](#/functions/historicalMarketCap) for more details.

> **IMPORTANT:**
> 
> -   If the date entered is a weekend then the data for the most recent trading day will be returned.
> -   The function doesn't account for all global public holidays or other non-trading days so if you get a "no data" error just check that the stock was open for trading that day!
> -   Similarly to our other batch functions, if only one symbol and metric is provided, the output will be a single value. If multiple symbols or metrics are provided, the output will include a header row. You can remove this header row by adding the `"NH"` option.

---

## [Examples](#/functions/historical?id=examples)

### [Single metric, single stock (AAPL open 28 July 2021)](#/functions/historical?id=single-metric-single-stock-aapl-open-28-july-2021)

```
=SF("AAPL", "historical", "open", "2021-07-28")
```

![Historical Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/historical_1.png "Historical Example 1")

### [Multiple metrics, single stock (AAPL open, high, low, close 28 July 2021)](#/functions/historical?id=multiple-metrics-single-stock-aapl-open-high-low-close-28-july-2021)

```
=SF("AAPL", "historical", "open&high&low&close", "2021-07-28")
```

![Historical Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/historical_2.png "Historical Example 2")

### [Single metric, multiple (batch) stocks (AAPL, MSFT close 28 July 2021) -](#/functions/historical?id=single-metric-multiple-batch-stocks-aapl-msft-close-28-july-2021-read-more-on-batching) [Read more on Batching](#/functions/historicalBatch)

```
=SF(A2:A3, "historical", "close", "2021-07-28")
```

![Historical Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/historical_3.png "Historical Example 3")

## Embedded Content