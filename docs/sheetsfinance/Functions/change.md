# SheetsFinance Docs | Price Change

# [Price Change](#/functions/change?id=price-change)

The `change` data type is the fastest way to quickly return percentage price change data over standardised time periods such as 1 day or 3 months. It is important to note that if multiple metrics are selected then the output of the data will be an array (multi-cell). In SheetsFinance fashion the `change` data type is also "batch-able" see our [Price Change Batch](#/functions/changeBatch) for how you can apply the function to multiple (up to 200!) stocks at once.

```
=SF(symbol, "change", metric, "", options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker code.
-   `metric` selects what metrics to display (see options below), display all metrics by leaving blank or using `"all"`. Chain together as many metrics as you'd like using `&`, e.g., `"1D&5D&1M"`.
-   `options` adjusts the formatting of the output. There are two available options, you can set this field to `"NH"` for no header row and/or `"decimal"` to return the change as a decimal rather than a percentage. Combine options with `&`, e.g., `"NH&decimal"`.

The price change `metric` options are:

-   All (`"all"`)
-   1 Day (`"1D"`)
-   5 Days (`"5D"`)
-   1 Month (`"1M"`)
-   3 Months (`"3M"`)
-   6 Months (`"6M"`)
-   Year to date (`"ytd"`)
-   1 Year (`"1Y"`)
-   3 Years (`"6Y"`)
-   5 Years (`"5Y"`)
-   10 Years (`"10Y"`)
-   Max (`"max"`) - this is the total price change since inception.

Returns: percentage price change over that period (e.g. `0.59` which is 0.59%)

> **Metric Chaining:** Remember like with many of our available functions you can chain metrics together with the `&` operator. For example `"1Y&3Y&5Y"` or `"1D&5D"`. Having multiple metrics will result in an array output (multi-cell output) with a header row included by default. You can remove the header row by applying the `"NH"` option.

> **IMPORTANT:** If you're including options, don't forget to include the blank 4th function parameter (`""`) before the options parameter (5th parameter). This must be included as other data types (e.g. `"historical"`) use the `SF()` function as well and this spot is generally reserved for a year or date. Entering something in this field will have no impact on the output.

## [Examples](#/functions/change?id=examples)

### [Example 1 - Single metric](#/functions/change?id=example-1-single-metric)

```
=SF("AAPL", "change", "1D")

0.59
```

### [Example 2 - Multiple metrics](#/functions/change?id=example-2-multiple-metrics)

```
=SF("AAPL", "change", "1D&5D&1M")

[multi-cell array]
```

![Change Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/change2.png "Change Example 2")

### [Example 3 - All metrics](#/functions/change?id=example-3-all-metrics)

```
=SF("AAPL", "change", "all")

[multi-cell array]
```

![Change Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/change3.png "Change Example 3")

### [Example 4 - Multiple metrics with options](#/functions/change?id=example-4-multiple-metrics-with-options)

```
=SF("AAPL", "change", "1M&3M&6M", "", "NH")

[multi-cell array]
```

![Change Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/change4.png "Change Example 4")

## Embedded Content