# SheetsFinance Docs | Historical Earnings

# [Earnings](#/functions/earnings?id=earnings)

The `earnings` function allows you to access the historical estimate and actual earnings per share (EPS) and revenue reported on a quarterly basis. The EPS figure is the non-GAAP, before non-reoccuring items (BNRI) EPS. If you are after the GAAP/reported EPS please see the [Income Statement](#/functions/historicalFinancials?id=income-statement). This data can be used to simply calculate the EPS surprise per quarter. A series of [examples](#/functions/earnings?id=examples) are provided below.

```
=SF(symbol, "earnings", metrics, date, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `metrics` is the specific data you're after for example `"ask"` or `"ask&bid&timestamp"`. You can leave this blank or set it to `"all"` to output ALL available data. You can also chain together multiple ratios using the `&` operator, for example `"ask&bid"`. See the list of available metrics below.
-   `date` is either the year (`YYYY`), range of years (`YYYY-YYYY`) or `"ttm"`. This controls what historical earnings data is returned.
-   `options` adjusts the formatting of the output. Set this field to `"NH"` for no header rows or `"-"` for reversed order. You can combine options with the `&` operator like so `"NH&-"`.

> **IMPORTANT:**
> 
> -   Earnings data covers most major global markets but may bit limited for smaller exchanges. Please contact us if data you are after is not currently available.
> -   The EPS is the non-GAAP, before non-reoccuring items (BNRI) EPS. If you are after the GAAP/reported EPS please see the [Income Statement](#/functions/historicalFinancials?id=income-statement).
> -   If the `date` argument is omitted the function will default to the trailing twelve months of data (TTM)
> -   If the `metrics` argument is omitted the function will default to `all`.

The `earnings` data type has the following metrics to select from:

-   All (`"all"`)
-   Date (`"date"`)
-   EPS Actual (`"eps"`)
-   EPS Estimated (`"epsEstimated"`)
-   Revenue Actual (`"revenue"`)
-   Revenue Estimated (`"revenueEstimated"`)

## [Examples](#/functions/earnings?id=examples)

### [Example 1 - All metrics, trailing twelve months (TTM)](#/functions/earnings?id=example-1-all-metrics-trailing-twelve-months-ttm)

```
=SF("AAPL", "earnings")
```

![Earnings Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/earnings_1.png "Earnings Example 1")

### [Example 2 - Specific metrics, TTM](#/functions/earnings?id=example-2-specific-metrics-ttm)

```
=SF("AAPL", "earnings", "date&eps&revenue")
```

![Earnings Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/earnings_2.png "Earnings Example 2")

### [Example 3 - All metrics, range of years](#/functions/earnings?id=example-3-all-metrics-range-of-years)

```
=SF("AAPL", "earnings", "all", "2020-2023")
```

![Earnings Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/earnings_3.png "Earnings Example 3")

### [Example 4 - All metrics, single year](#/functions/earnings?id=example-4-all-metrics-single-year)

```
=SF("AAPL", "earnings", "all", 2022)
```

![Earnings Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/earnings_4.png "Earnings Example 4")

### [Example 5 - Specific metrics, single year, no header](#/functions/earnings?id=example-5-specific-metrics-single-year-no-header)

```
=SF("AAPL", "earnings", "date&eps&epsEstimated", 2022, "NH")
```

![Earnings Example 5](https://cdn.sheetsfinance.com/public-site/img/docs/earnings_5.png "Earnings Example 5")

## Embedded Content