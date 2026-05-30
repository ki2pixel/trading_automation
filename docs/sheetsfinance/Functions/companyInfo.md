# SheetsFinance Docs | Company Info

# [Company Info](#/functions/companyInfo?id=company-info)

The companyInfo data type is used to deliver an overview of non-realtime company information. This includes things like the company name, sector, exchange, market cap, etc.

```
=SF(symbol, "companyInfo", metric, "", options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol. Check out the [Company Info Batch](#/functions/companyinfoBatch) function if you're after data on up to 2000 stocks at the same time!
-   `metric` selects what metric(s) to display (see options below), display all metrics by using `"all"`. Chain together as many metrics as you'd like using the `&` operator, e.g., `"name&exchange&sector"`.
-   `options` adjusts the formatting of the output. There is currently only one available option for company info data. You can set this field to `"NH"` for no header row when outputting multi-cell data.

> **SUGGESTION:** If you're after a large amount of company info data at once (e.g. in a watchlist or portfolio) consider using our [Company Info Batch](#/functions/companyinfoBatch) functionality.

The company info function has the following available metrics:

-   All (`"all"`)
-   Name (`"name"`)
-   Stock Exchange Symbol (`"exchange"`)
-   Stock Exchange Full Name (`"exchangeFullName"`)
-   Price Range (`"range"`)
-   Last Dividend (`"lastDividend"`)
-   Dividend Yield (`"divYield"`)
-   Beta (`"beta"`)
-   Reporting Currency (`"currency"`)
-   Industry (`"industry"`)
-   Sector (`"sector"`)
-   Country (`"country"`)
-   State (`"state"`)
-   City (`"city"`)
-   ZIP Code (`"zip"`)
-   Phone Number (`"phone"`)
-   ISIN (`"isin"`)
-   CUSIP (`"cusip"`)
-   CIK (`"cik"`)
-   Full-time Employees (`"fullTimeEmployees"`)
-   IPO Date (`"ipoDate"`)
-   CEO (`"ceo"`)
-   Company Website (`"website"`)
-   Company Summary (`"description"`)
-   Is ETF (`"isEtf"`)
-   Is ADR (`"isAdr"`)
-   Is Fund (`"isFund"`)
-   Is Actively Trading (`"isActivelyTrading"`)

## [Examples](#/functions/companyInfo?id=examples)

#### [Example 1 - Single metric (name)](#/functions/companyInfo?id=example-1-single-metric-name)

Set the metric to `"name"` for the full name of the financial asset.

```
=SF("AAPL", "companyInfo", "name")

Apple Inc.
```

#### [Example 2 - Single metric (Stock Exchange)](#/functions/companyInfo?id=example-2-single-metric-stock-exchange)

Set the metric to `"exchange"` for the exchange that asset is traded on.

```
=SF("AAPL", "companyInfo", "exchange")

NASDAQ
```

**Note:** Returns `CRYPTO` for all cryptocurrencies, `FOREX` for forex pairs, `INDEX` for indexes, `COMMODITY` for commodities, and `MUTUAL_FUND` for mutual funds.

#### [Example 3 - Multiple metrics](#/functions/companyInfo?id=example-3-multiple-metrics)

You can chain together multiple metrics using the `&` operator. This will return a multi-cell array with a header row included automatically. You can remove the header row by setting the options argument to `"NH"`.

```
=SF("AAPL", "companyInfo", "name&exchange&sector")
```

![Company Info Multiple Metrics](https://cdn.sheetsfinance.com/public-site/img/docs/companyInfo_3.png "Company Info Multiple Metrics")

#### [Example 4 - All metrics](#/functions/companyInfo?id=example-4-all-metrics)

Set the metric argument to `"all"` to return all available company info metrics.

```
=SF("AAPL", "companyInfo", "all")
```

![Company Info All Metrics](https://cdn.sheetsfinance.com/public-site/img/docs/companyInfo_4.png "Company Info All Metrics")

## Embedded Content