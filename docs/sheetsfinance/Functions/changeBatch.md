# SheetsFinance Docs | Price Change Batch

# [Price Change Batch](#/functions/changeBatch?id=price-change-batch)

The `change` data type can be applied to multiple stocks at once to perform a batch request.

```
=SF(<range>, "change", metric, "", options)
```

-   `<range>` is a range of cells e.g. `A1:A100`. You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbols.
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

## [Examples](#/functions/changeBatch?id=examples)

### [Example 1 - Single metric batch](#/functions/changeBatch?id=example-1-single-metric-batch)

```
=SF(A2:A12, "change", "1D")
```

![Change Batch Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/changeBatch1.png "Change Batch Example 1")

### [Example 2 - Multiple metrics batch](#/functions/changeBatch?id=example-2-multiple-metrics-batch)

```
=SF(A2:A12, "change", "1D&5D&1M")
```

![Change Batch Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/changeBatch2.png "Change Batch Example 2")

### [Example 3 - All batch](#/functions/changeBatch?id=example-3-all-batch)

```
=SF(A2:A12, "change", "all")
```

![Change Batch Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/changeBatch3.png "Change Batch Example 3")

### [Example 4 - All batch with options](#/functions/changeBatch?id=example-4-all-batch-with-options)

```
=SF(A2:A12, "change", "all", "", "NH")
```

> **IMPORTANT:** Notice the placement of the formula in this case is adjacent to the first stock symbol to ensure the data output aligns with the stock symbols.

![Change Batch Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/changeBatch4.png "Change Batch Example 4")

## Embedded Content