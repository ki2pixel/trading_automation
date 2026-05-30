# Balance Sheet

# [Balance Sheet Statement](#/functions/balancesheet-statement?id=balance-sheet-statement)

🚀 **Update (November 2025):** You are viewing the latest balance sheet statement documentation, to view legacy documentation for the deprecated balance sheet statement function see [Historical Financial Statements (Deprecated)](/docs#/functions/historicalFinancials).

You can access 30+ years of standardised annual, quarterly and TTM (trailing twelve months) balance sheet statements using the `SF()` function with the base type of `"balancesheet"`.

```
=SF(symbol, type, metrics, year(s), options)
```

-   `symbol` - The ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` - The type of financial statement you want to pull in. See [Type](#/functions/balancesheet-statement?id=type) section below for more information.
-   `metrics` - The specific line items of the balance sheet statement you are after. See [Metrics](#/functions/balancesheet-statement?id=metrics) section below for full list.
-   `year(s)` - The year, range of years or date for the financial statement. See [Year(s)](#/functions/balancesheet-statement?id=years) section for more information.
-   `options` - Additional options for adjusting the way data is called or formatted. See [Options](#/functions/balancesheet-statement?id=options) section below for more information.

#### [](#/functions/balancesheet-statement?id=jump-to-examples-darr)[Jump to Examples ↓](#/functions/balancesheet-statement?id=examples)

## [Type](#/functions/balancesheet-statement?id=type)

The `type` is made up of the base statement type and then followed by a suffix which indicates quarterly or TTM data. For the balance sheet statement, the base statement type is: `"balancesheet"`. The suffixes that can be used with the base statement type are:

-   No suffix - Annual data (e.g. `"balancesheet"` for annual balance sheet statement)
-   `"Q"` - All quarterly data (e.g. `"balancesheetQ"` for all quarterly balance sheet statements)
-   `"QX"` - Specific quarter data (e.g., `Q1`, `Q2`, `Q3`, `Q4`) (e.g. `"balancesheetQ2"` for all Q2 balance sheet statements)
-   `"TTM"` - Trailing Twelve Months data (e.g. `"balancesheetTTM"` for trailing twelve months balance sheet statement) - see [TTM Data](#/functions/balancesheet-statement?id=ttm-data) section below for more information.

## [Metrics](#/functions/balancesheet-statement?id=metrics)

The available metrics/line items for the balance sheet statement are as follows:

-   All (`"all"`)
-   Date (`"date"`)
-   Symbol (`"symbol"`)
-   Reported Currency (`"reportedCurrency"`)
-   CIK (`"cik"`)
-   Filing Date (`"filingDate"`)
-   Accepted Date (`"acceptedDate"`)
-   Fiscal Year (`"fiscalYear"`)
-   Period (`"period"`)
-   Cash And Cash Equivalents (`"cashAndCashEquivalents"`)
-   Short Term Investments (`"shortTermInvestments"`)
-   Cash And Short Term Investments (`"cashAndShortTermInvestments"`)
-   Net Receivables (`"netReceivables"`)
-   Accounts Receivables (`"accountsReceivables"`)
-   Other Receivables (`"otherReceivables"`)
-   Inventory (`"inventory"`)
-   Prepaids (`"prepaids"`)
-   Other Current Assets (`"otherCurrentAssets"`)
-   Total Current Assets (`"totalCurrentAssets"`)
-   Property Plant Equipment Net (`"propertyPlantEquipmentNet"`)
-   Goodwill (`"goodwill"`)
-   Intangible Assets (`"intangibleAssets"`)
-   Goodwill And Intangible Assets (`"goodwillAndIntangibleAssets"`)
-   Long Term Investments (`"longTermInvestments"`)
-   Tax Assets (`"taxAssets"`)
-   Other Non Current Assets (`"otherNonCurrentAssets"`)
-   Total Non Current Assets (`"totalNonCurrentAssets"`)
-   Other Assets (`"otherAssets"`)
-   Total Assets (`"totalAssets"`)
-   Total Payables (`"totalPayables"`)
-   Account Payables (`"accountPayables"`)
-   Other Payables (`"otherPayables"`)
-   Accrued Expenses (`"accruedExpenses"`)
-   Short Term Debt (`"shortTermDebt"`)
-   Capital Lease Obligations Current (`"capitalLeaseObligationsCurrent"`)
-   Tax Payables (`"taxPayables"`)
-   Deferred Revenue (`"deferredRevenue"`)
-   Other Current Liabilities (`"otherCurrentLiabilities"`)
-   Total Current Liabilities (`"totalCurrentLiabilities"`)
-   Long Term Debt (`"longTermDebt"`)
-   Capital Lease Obligations Non Current (`"capitalLeaseObligationsNonCurrent"`)
-   Deferred Revenue Non Current (`"deferredRevenueNonCurrent"`)
-   Deferred Tax Liabilities Non Current (`"deferredTaxLiabilitiesNonCurrent"`)
-   Other Non Current Liabilities (`"otherNonCurrentLiabilities"`)
-   Total Non Current Liabilities (`"totalNonCurrentLiabilities"`)
-   Other Liabilities (`"otherLiabilities"`)
-   Capital Lease Obligations (`"capitalLeaseObligations"`)
-   Total Liabilities (`"totalLiabilities"`)
-   Treasury Stock (`"treasuryStock"`)
-   Preferred Stock (`"preferredStock"`)
-   Common Stock (`"commonStock"`)
-   Retained Earnings (`"retainedEarnings"`)
-   Additional Paid In Capital (`"additionalPaidInCapital"`)
-   Accumulated Other Comprehensive Income Loss (`"accumulatedOtherComprehensiveIncomeLoss"`)
-   Other Total Stockholders Equity (`"otherTotalStockholdersEquity"`)
-   Total Stockholders Equity (`"totalStockholdersEquity"`)
-   Total Equity (`"totalEquity"`)
-   Minority Interest (`"minorityInterest"`)
-   Total Liabilities And Total Equity (`"totalLiabilitiesAndTotalEquity"`)
-   Total Investments (`"totalInvestments"`)
-   Total Debt (`"totalDebt"`)
-   Net Debt (`"netDebt"`)

## [Year(s)](#/functions/balancesheet-statement?id=years)

The `year(s)` parameter can be specified in the following ways:

-   Specific Year - e.g., `"2020"` to return the balance sheet for that year.
-   Range of Years - e.g., `"2015-2020"` to return multiple years of balance sheets in one call.
-   `"ttm"` - to return the most recent TTM balance sheet.
-   Specific date - e.g., `"2020-06-30"`. This can be used in two cases: (1) when generating a historical TTM statement as of that date (e.g. `"balancesheetTTM"`), or (2) when pulling quarterly data (with `Q` or `QX` suffix) in conjunction with the `"calYear"` option to return the specific quarter that includes that date. In the second case you can also enter only a year and month, for example `"2020-03"` to return the quarter for March 2020.

> **💡 Tip:** Omitting the `year(s)` parameter will default to the most recent annual/quarterly statement, for example, if you call `SF("AAPL", "balancesheet")` without specifying the year(s), it will return the most recent annual balance sheet, or `SF("AAPL", "balancesheetQ")` will return the most recent quarterly balance sheet.

## [Options](#/functions/balancesheet-statement?id=options)

> **💡 Tip:** Options can be chained using the `&` operator, e.g. `"NH&NLI"`.

The options parameter can be used to adjust the way data is accessed and/or formatted. The available options are:

-   `"NH"` - No header rows.
-   `"NLI"` - No line item labels.
-   `"-"` - Reverse the year ordering (i.e., change the output to most recent to oldest).
-   `"calYear"` - When pulling data search our database by calendar year instead of fiscal year. By default, SheetsFinance returns financial statements based on the company's fiscal year. For example, if a company's fiscal year ends in June, the 2020 fiscal year statement would cover the period from July 2019 to June 2020. By using the `"calYear"` option, you can request financial statements based on the calendar year (January to December). This is particularly useful for comparing companies with different fiscal years or for aligning financial data with calendar-year-based analyses.
-   `"pad"` - When pulling quarterly data, this option will pad the output with empty columns for years or quarters that do not exist. For example, if you pull quarterly income statements for a company that has IPOd recently, using this option will ensure that all quarters from the earliest to the latest are represented in the output, even if some quarters have no data. This helps maintain a consistent structure in your data when comparing multiple companies or time periods.

## [TTM Data](#/functions/balancesheet-statement?id=ttm-data)

There are a few ways to access TTM (trailing twelve months) data using the `SF()` function:

1.  Using the base statement type with `"ttm"` in the `year(s)` parameter for the latest TTM data. For example, `SF("AAPL", "balancesheet", "all", "ttm")` will return the most recent TTM balance sheet statement.
2.  Using the `TTM` suffix in the `type` parameter for historical TTM data as of a specific date. You can then enter:
    -   A year or range of years to get TTM statements per quarter for those years. For example, `SF("AAPL", "balancesheetTTM", "all", "2018-2020")` will return TTM balance sheets for each quarter from 2018 to 2020.
    -   A specific date to get the TTM statement as of that date. For example, `SF("AAPL", "balancesheetTTM", "all", "2020-06-30")` will return the TTM balance sheet as of June 30, 2020. Or, more generally, a year and month, e.g., `"2020-03"` to get the TTM statement as of March 2020.

## [Examples](#/functions/balancesheet-statement?id=examples)

### [Example 1: Most recent annual balance sheet with all metrics](#/functions/balancesheet-statement?id=example-1-most-recent-annual-balance-sheet-with-all-metrics)

```
=SF("AAPL", "balancesheet")
```

![Example 1 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_1.png "Example 1 - Balance Sheet")

### [Example 2: Single value - most recent quarterly total assets (MRQ)](#/functions/balancesheet-statement?id=example-2-single-value-most-recent-quarterly-total-assets-mrq)

> **💡 Tip:** When a value is fully specified with a single metric and year, no header or line item labels are included in the output.

```
=SF("AAPL", "balancesheetQ", "totalAssets")
```

![Example 2 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_2.png "Example 2 - Balance Sheet")

### [Example 3: A range of quarterly balance sheets with specific metrics](#/functions/balancesheet-statement?id=example-3-a-range-of-quarterly-balance-sheets-with-specific-metrics)

```
=SF("AAPL", "balancesheetQ", "totalAssets&totalLiabilities&shareholderEquity", "2022-2024")
```

![Example 3 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_3.png "Example 3 - Balance Sheet")

### [Example 4: A range of annual balance sheets for specific years, all metrics](#/functions/balancesheet-statement?id=example-4-a-range-of-annual-balance-sheets-for-specific-years-all-metrics)

```
=SF("AAPL", "balancesheet", "all", "2019-2024")
```

![Example 4 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_4.png "Example 4 - Balance Sheet")

### [Example 5: Most recent TTM balance sheet with selected metrics and no line item labels](#/functions/balancesheet-statement?id=example-5-most-recent-ttm-balance-sheet-with-selected-metrics-and-no-line-item-labels)

> **💡 Tip:** The `"NLI"` option removes the line item labels from the output, this can be useful for simplifying the data presentation and placing statements side-by-side.

```
=SF("AAPL", "balancesheet", "totalAssets&totalLiabilities&shareholderEquity", "ttm", "NLI")
```

![Example 5 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_5.png "Example 5 - Balance Sheet")

### [Example 6: Quarterly balance sheets for a specific quarter across multiple years](#/functions/balancesheet-statement?id=example-6-quarterly-balance-sheets-for-a-specific-quarter-across-multiple-years)

```
=SF("AAPL", "balancesheetQ2", "all", "2018-2020")
```

![Example 6 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_6.png "Example 6 - Balance Sheet")

### [Example 7: Quarterly statements for a specific calendar year (instead of fiscal year)](#/functions/balancesheet-statement?id=example-7-quarterly-statements-for-a-specific-calendar-year-instead-of-fiscal-year)

> **💡 Tip:** The `calYear` option adjusts the search to calendar years instead of fiscal years.

```
=SF("AAPL", "balancesheetQ", "all", "2020", "calYear")
```

![Example 7 - Balance Sheet](https://cdn.sheetsfinance.com/public-site/img/docs/balancesheet_7.png "Example 7 - Balance Sheet")

## Embedded Content