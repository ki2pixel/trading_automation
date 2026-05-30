# SheetsFinance Docs | Sector PE

# [Historical Sector Average PE](#/functions/sectorPE?id=historical-sector-average-pe)

The `sectorPE` data type returns the average sector price-to-earnings ratio (PE) for the global exchange market on the date specified.

```
=SF(exchange, "sectorPE", sectors, date, options)
```

-   `exchange` is the symbol of the exchange (e.g., `"NSE"` or `"NASDAQ"`). You can check our [Available Markets](#/use/exchanges) to find the correct symbol.
-   `sectors` selects what sectors to display. Leave blank or use `"all"` to display all sectors. Chain together sectors with the `&` symbol to display more than one (e.g. `"Technology&Healthcare&Basic Materials"`). Note, sector names are case-sensitive and some include spaces.
-   `date` is the date for which you want to retrieve the data. The date should either be a date formatted Google Sheets object or a text string in the format of `YYYY-MM-DD` or `DD/MM/YYYY`.
-   `options` adjusts the formatting of the output. Set this field to `"NH"` for no header rows or `"-"` for reversed order. You can combine options with the `&` operator like so `"NH&-"`.

> **HOT TIP:** Use the [Function Generator](#/use/functionGenerator) to easily create this function and select the correct sectors.

The sectorPE `sectors` options are:

-   All (`"all"`)
-   Basic Materials (`"Basic Materials"`)
-   Communication Services (`"Communication Services"`)
-   Consumer Cyclical (`"Consumer Cyclical"`)
-   Consumer Defensive (`"Consumer Defensive"`)
-   Energy (`"Energy"`)
-   Financial Services (`"Financial Services"`)
-   Healthcare (`"Healthcare"`)
-   Industrials (`"Industrials"`)
-   Real Estate (`"Real Estate"`)
-   Technology (`"Technology"`)
-   Utilities (`"Utilities"`)

## [Examples](#/functions/sectorPE?id=examples)

### [Example 1 - Display all sectors, most recent date](#/functions/sectorPE?id=example-1-display-all-sectors-most-recent-date)

```
=SF("NASDAQ", "sectorPE")
```

![Sector PE Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/sectorPE_1.png "Sector PE Example 1")

---

### [Example 2 - Display several selected sectors, specific date](#/functions/sectorPE?id=example-2-display-several-selected-sectors-specific-date)

```
=SF("NASDAQ", "sectorPE", "Technology&Healthcare", "2022-01-01")
```

![Sector PE Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/sectorPE_2.png "Sector PE Example 2")

## Embedded Content