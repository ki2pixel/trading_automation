# SheetsFinance Docs | Institutional Holders

# [Institutional Holders](#/functions/instHolders?id=institutional-holders)

The `instHolders` data type returns a breakdown of institutional holders of a stock.

```
=SF(symbol, "instHolders", metric, date, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `metric` selects what metrics to display (see options below), display all metrics by leaving blank or using `"all"`. Chain together as many metrics as you'd like using `&`, e.g., `"asset&weightPercentage"`.
-   `date` is the date of the institutional holdings data. Leaving this empty will return the latest data. If the specified date is not found in the dataset then the data returned will be next available date before the date provided. Institutional holdings data is updated quarterly, therefore quarterly dates are recommended. You can return a list of the available dates by specifying `"dateOptions"` as the metric.
-   `options` adjusts the formatting of the output. Available options include: `"NH"` for no header rows, `"-"` for reversing the output, `"ob=XXX"`for ordering the output by a specific metric, e.g. `"ob=shares"` to order the data by `shares` in descending order and `"limit=X"` to limit the number of rows returned to X rows. You can chain together as many options as you'd like using `&`, e.g., `"ob=change&limit=10&-"`.

The ETF Holdings `metric` options are:

-   All (`"all"`)
-   Holder (`"holder"`)
-   Shares (`"shares"`)
-   Date Reported (`"dateReported"`)
-   Change (`"change"`)
-   dateOptions (`"dateOptions"`) - only returns a list of available dates for the stock. This can be used as a reference for further analysis.

> **Important:** Institutional Holders data does not have global coverage, only selected major markets are included.

## [Examples](#/functions/instHolders?id=examples)

#### [Example 1 - All latest holders data](#/functions/instHolders?id=example-1-all-latest-holders-data)

```
=SF("AAPL","instHolders")
```

![Institutional Holders Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/instHolders_1.png "Institutional Holders Example 1")

#### [Example 2 - Latest holders data ordered by number of shares](#/functions/instHolders?id=example-2-latest-holders-data-ordered-by-number-of-shares)

```
=SF("AAPL","instHolders","all", "", "ob=shares")
```

![Institutional Holders Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/instHolders_2.png "Institutional Holders Example 1")

#### [Example 3 - Historical holders data ordered by change in shares](#/functions/instHolders?id=example-3-historical-holders-data-ordered-by-change-in-shares)

```
=SF("AAPL","instHolders","all","2022-10-01", "ob=change")
```

![Institutional Holders Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/instHolders_3.png "Institutional Holders Example 1")

## Embedded Content