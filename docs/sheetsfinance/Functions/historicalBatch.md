# SheetsFinance Docs | Historical EOD Batch

# [Batch Historical EOD Data](#/functions/historicalBatch?id=batch-historical-eod-data)

Perhaps one of the more subtle yet powerful SheetsFinance features. The `historical` function is batchable, meaning you can pull historical EOD data for 1000s of symbols at the same time. This is particularly useful for backtesting, portfolio analysis, and other data-intensive tasks.

```
=SF(<range>, "historical", metrics, date, options)
```

-   `<range>` is a range of cells e.g. `A1:A100`. You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbols.
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

> **IMPORTANT:**
> 
> -   If the date entered is a weekend then the data for the most recent trading day will be returned.
> -   The function doesn't account for all global public holidays or other non-trading days so if you get a "no data" error just check that the stock was open for trading that day!
> -   Similarly to our other batch functions, if only one symbol and metric is provided, the output will be a single value. If multiple symbols or metrics are provided, the output will include a header row. You can remove this header row by adding the `"NH"` option.
> -   Length of batch depends upon your plan level, see our [pricing page](https://sheetsfinance.com/pricing) for more details.

---

## [Examples](#/functions/historicalBatch?id=examples)

### [Single metric, multiple stocks (AAPL, MSFT, NVDA, GOOG, NKE, V open 28 July 2021)](#/functions/historicalBatch?id=single-metric-multiple-stocks-aapl-msft-nvda-goog-nke-v-open-28-july-2021)

```
=SF(A2:A7, "historical", "open", "2021-07-28")
```

![Historical Batch Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/historicalBatch_1.png "Historical Batch Example 1")

### [Multiple metrics, multiple stocks (AAPL, MSFT, NVDA, GOOG, NKE, V open, high, low, close, volume 28 July 2021)](#/functions/historicalBatch?id=multiple-metrics-multiple-stocks-aapl-msft-nvda-goog-nke-v-open-high-low-close-volume-28-july-2021)

```
=SF(A2:A7, "historical", "open&high&low&close&volume", "2021-07-28")
```

![Historical Batch Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/historicalBatch_2.png "Historical Batch Example 2")

## Embedded Content