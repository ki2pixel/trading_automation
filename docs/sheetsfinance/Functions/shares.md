# SheetsFinance Docs | Historical Outstanding Shares and Float

# [Daily Historical Outstanding Shares and Float](#/functions/shares?id=daily-historical-outstanding-shares-and-float)

The `shares` function provides historical outstanding shares and float data for a given security. The data is available on a near daily basis with up to 3 years of data available. The outstanding shares and float data is useful for understanding the capital structure of a company and can be used to calculate various financial ratios and metrics. The `shares` function is run within the `SF_TIMESERIES` where the period argument is set to `"shares"`.

```
=SF_TIMESERIES("AAPL", startDate, endDate, "shares", metrics, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `startDate` is the starting date of the time series, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`
-   `endDate` is the ending date of the time series, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `metrics` select what metrics to output, this can be `"all"`, a single metric or a combination by chaining together as many metrics as you'd like using `&`, e.g., `"date&outstandingShares&floatShares"`.
-   `options` format options for the output. Currently 2 options available descending/ascending order and header/no header. The descending order can be specified with the inclusion of `"-"` and no header can be specified with `"NH"`, e.g., for no header and descending order enter `"-&NH"` for the `options` argument.

The `shares` metrics options are:

-   All (`"all"`)
-   Date (`"date"`)
-   Outstanding Shares (`"outstandingShares"`)
-   Float Shares (`"floatShares"`)
-   Free Float (`"freeFloat"`)

## [Examples](#/functions/shares?id=examples)

#### [Example 1 - Display all outstanding shares and float data](#/functions/shares?id=example-1-display-all-outstanding-shares-and-float-data)

```
=SF_TIMESERIES("AAPL", "2022-01-01", "2024-09-19", "shares", "all")
```

![Shares Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/timeseries_shares_1.png "Shares Example 1")

#### [Example 2 - Display selected metrics](#/functions/shares?id=example-2-display-selected-metrics)

```
=SF_TIMESERIES("AAPL", "2022-01-01", "2024-09-19", "shares", "date&outstandingShares&floatShares")
```

![Shares Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/timeseries_shares_2.png "Shares Example 2")

#### [Example 3 - Display single metric](#/functions/shares?id=example-3-display-single-metric)

```
=SF_TIMESERIES("AAPL", "2022-01-01", "2024-09-19", "shares", "floatShares")
```

![Shares Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/timeseries_shares_3.png "Shares Example 3")

## Embedded Content