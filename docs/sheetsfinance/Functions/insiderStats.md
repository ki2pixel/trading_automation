# SheetsFinance Docs | Insider Statistics

# [Insider Trading Statistics (US Only)](#/functions/insiderStats?id=insider-trading-statistics-us-only)

The `insiderStats` data type summaries all insider trading activity into clear and understandable statistics per quarter for the last 20+ years. The data is collated from the insider trading transactions as reported by the SEC and includes all the detail required to understand how insiders are trading the stock. This data is currently only available for US companies.

```
=SF(symbol, "insiderStats", metrics, year, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `metrics` selects what metrics to display (see options below), display all metrics by leaving blank or using `"all"`. Chain together as many metrics as you'd like using `&`, e.g., `"year&quarter&purchases&sales"`.
-   `year` is year or range of years for which you want to retrieve the data. You can enter a single year (e.g. `2024`) or a range of years (e.g. `2022-2024`). Defaults to the most recent year if not specified.
-   `options` adjusts the formatting of the output. Available options include: `"NH"` for no header rows and `"-"` for reversing the output. You can chain together as many options as you'd like using `&`, e.g., `"NH&-"`.

The Insider Statistics `metrics` options are:

-   All (`"all"`)
-   Year (`"year"`)
-   Quarter (`"quarter"`)
-   Acquired Transactions (`"acquiredTransactions"`)
-   Disposed Transactions (`"disposedTransactions"`)
-   Acquired/Disposed Ratio (`"acquiredDisposedRatio"`)
-   Total Acquired (`"totalAcquired"`)
-   Total Disposed (`"totalDisposed"`)
-   Average Acquired (`"averageAcquired"`)
-   Average Disposed (`"averageDisposed"`)
-   Total Purchases (`"totalPurchases"`)
-   Total Sales (`"totalSales"`)
-   CIK (`"cik"`)

> **IMPORTANT:**
> 
> -   The `insiderStats` data type is currently only available for US companies.

---

## [Examples](#/functions/insiderStats?id=examples)

#### [Example 1 - Display the most recent year's insider trading statistics](#/functions/insiderStats?id=example-1-display-the-most-recent-year39s-insider-trading-statistics)

```
=SF("AAPL", "insiderStats")
```

![Insider Stats Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/insiderStats_1.png "Insider Stats Example 1")

---

#### [Example 2 - Display several selected metrics, specific year](#/functions/insiderStats?id=example-2-display-several-selected-metrics-specific-year)

```
=SF("AAPL", "insiderStats", "year&quarter&totalAcquired&totalDisposed&acquiredDisposedRatio", "2022")
```

![Insider Stats Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/insiderStats_2.png "Insider Stats Example 2")

---

#### [Example 3 - Display all metrics, specific year range](#/functions/insiderStats?id=example-3-display-all-metrics-specific-year-range)

```
=SF("AAPL", "insiderStats", "all", "2019-2022")
```

![Insider Stats Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/insiderStats_3.png "Insider Stats Example 3")

## Embedded Content