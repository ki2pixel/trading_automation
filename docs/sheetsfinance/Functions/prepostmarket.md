# SheetsFinance Docs | Pre and Post Market (US Only)

# [Pre and Post Market Data (US Only)](#/functions/prepostmarket?id=pre-and-post-market-data-us-only)

The `prePostMarket` function allows you to access the latest data on pre-market and post-market movements for US-based assets. A series of [examples](#/functions/prepostmarket?id=examples) are provided below.

```
=SF(symbol, "prePostMarket", metrics, "", options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `metrics` is the specific data you're after for example `"ask"` or `"ask&bid&timestamp"`. You can leave this blank or set it to `"all"` to output ALL available data. You can also chain together multiple ratios using the `&` operator, for example `"ask&bid"`. See the list of available metrics below.
-   `options` adjusts the formatting of the output. There is only one available option for `prePostMarket`. Set this field to `"NH"` for no header rows.

> **HOT TIPS:**
> 
> -   Use the options parameter to remove the header row.

> **IMPORTANT:** Pre and post market data is currently only available for US equities.

The `prePostMarket` data type has the following metrics to select from:

-   Ask (`"ask"`)
-   Bid (`"bid"`)
-   Ask Size (`"askSize"`)
-   Bid Size (`"bidSize"`)
-   Volume (`"volume"`)
-   Timestamp (`"timestamp"`)

## [Examples](#/functions/prepostmarket?id=examples)

### [Example 1 - All metrics](#/functions/prepostmarket?id=example-1-all-metrics)

```
=SF("AAPL", "prePostMarket")
```

![Pre Post Market Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/prePostMarket_1.png "Pre Post Market Example 1")

### [Example 2 - Specific metrics](#/functions/prepostmarket?id=example-2-specific-metrics)

```
=SF("AAPL", "prePostMarket", "ask&bid&timestamp")
```

![Pre Post Market Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/prePostMarket_2.png "Pre Post Market Example 2")

### [Example 3 - Specific metrics and no header row](#/functions/prepostmarket?id=example-3-specific-metrics-and-no-header-row)

```
=SF("AAPL", "prePostMarket", "ask&bid&timestamp", "", "NH")
```

![Pre Post Market Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/prePostMarket_3.png "Pre Post Market Example 3")

### [Example 4 - Single Metric](#/functions/prepostmarket?id=example-4-single-metric)

```
=SF("AAPL", "prePostMarket", "ask")

169.76
```

## Embedded Content