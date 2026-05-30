# SheetsFinance Docs | ISIN, CUSIP & CIK Mapper

# [Code/Identifier Mapping](#/functions/map?id=codeidentifier-mapping)

The `SF_MAP()` function can be used to map/convert other global identifying codes (e.g. ISIN and CUSIP numbers) to stock ticker symbols. This can be handy when integrating SheetsFinance with other data sources that rely on alternative ways of identifying a financial product.

```
=SF_MAP(code, type, filter)
```

-   `code` is the code/identifier you want to map to a SheetsFinance ticker symbol.
-   `type` is the type of code you are mapping, e.g. ISIN, CUSIP or CIK numbers. Defaults to converting CUSIP codes if this parameter is omitted.
-   `filter` \[OPTIONAL\] only applicable for ISIN numbers. Enter either an exchange (e.g. `"nasdaq"`) or currency (e.g. `"usd"`) to filter the search results to the SheetsFinance ticker symbol that matches the given exchange or currency. If omitted and using `"isin"` as the `type` parameter, the function may return multiple results if the ISIN code is associated with multiple ticker symbols.

Available types:

-   `"isin"`
-   `"cusip"`
-   `"cik"`

> **IMPORTANT:** Ensure you enter the code as a string (enclosed in quotation) like so `"0000320193"` **not** as a number e.g. `0000320193`.

## [Examples](#/functions/map?id=examples)

### [Example 1 - Default CUSIP mapping](#/functions/map?id=example-1-default-cusip-mapping)

```
=SF_MAP("037833100")

AAPL
```

If the `type` parameter is omitted the `SF_MAP()` function will default to converting CUSIP codes

### [Example 2 - ISIN mapping with exchange](#/functions/map?id=example-2-isin-mapping-with-exchange)

```
=SF_MAP("US0378331005", "isin", "NASDAQ")

AAPL
```

### [Example 2 - CIK mapping](#/functions/map?id=example-2-cik-mapping)

```
=SF_MAP("0000320193", "cik")

AAPL
```

## Embedded Content