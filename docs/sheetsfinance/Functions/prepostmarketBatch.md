# SheetsFinance Docs | Pre and Post Market Batch (US Only)

# [Pre and Post Market Batch (US Only)](#/functions/prepostmarketBatch?id=pre-and-post-market-batch-us-only)

The `prePostMarket` can also be used in a batch format to access multiple stocks at the same time. Use this to track pre and post market movements of hundreds to thousands of stocks at the same time.

```
=SF(<range>, "prePostMarket", metrics, "", options)
```

-   `<range>` is a range of cells e.g. `A1:A100`. You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbols.
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
-   Timestamp (`"timestamp"`)

## [Examples](#/functions/prepostmarketBatch?id=examples)

### [Example 1 - Batch all metrics](#/functions/prepostmarketBatch?id=example-1-batch-all-metrics)

```
=SF(A1:A30, "prePostMarket")
```

![Pre Post Market Batch Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/prePostMarketBatch_1.png "Pre Post Market Batch Example 1")

### [Example 2 - Batch specific metrics](#/functions/prepostmarketBatch?id=example-2-batch-specific-metrics)

```
=SF("AAPL", "prePostMarket", "ask&bid&timestamp")
```

![Pre Post Market Batch Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/prePostMarketBatch_2.png "Pre Post Market Batch Example 2")

## Embedded Content