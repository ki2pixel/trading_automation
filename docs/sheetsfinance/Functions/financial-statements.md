# SheetsFinance Docs | Financial Statements

# [Financial Statements](#/functions/financial-statements?id=financial-statements)

🚀 **Update (November 2025):** You are viewing the latest financial statements documentation, to view legacy documentation for the deprecated statement functions see [Historical Financial Statements (Deprecated)](/docs#/functions/historicalFinancials).

SheetsFinance provides access to 30+ years of consolidated annual, quarterly and TTM (trailing twelve months) financial statements using the `SF()` function. The function allows you to pull historical income statements, balance sheets, and cash flow statements for 80,000+ global companies directly into your spreadsheet.

This page outlines how all three (3) types of financial statements can be pulled in using the `SF()` function but detailed information and examples for each individual statement can be found on their respective pages: [Income Statement](#/functions/income-statement), [Balance Sheet](#/functions/balancesheet-statement) and [Cash Flow Statement](#/functions/cashflow-statement).

```
=SF(symbol, type, metrics, year(s), options)
```

-   `symbol` - The ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` - The type of financial statement you want to pull in. See [Type](#/functions/financial-statements?id=type) section below for more information.
-   `metrics` - The specific line items of that financial statement you are after. See [Metrics](#/functions/financial-statements?id=metrics) section below for more information.
-   `year(s)` - The year, range of years or date for the financial statement. See [Year(s)](#/functions/financial-statements?id=years) section below for more information.
-   `options` - Additional options for adjusting the way data is called or formatted. See [Options](#/functions/financial-statements?id=options) section below for more information.

## [Type](#/functions/financial-statements?id=type)

The `type` is made up of the base statement type and then followed by a suffix which indicates quarterly or TTM data. The base statement types are:

-   `"income"` - Income Statement (See [Income Statement](#/functions/income-statement) for more details)
-   `"balancesheet"` - Balance Sheet (See [Balance Sheet](#/functions/balancesheet-statement) for more details)
-   `"cashflow"` - Cash Flow Statement (See [Cash Flow Statement](#/functions/cashflow-statement) for more details)

The suffixes that can be used with each base statement type are:

-   No suffix - Annual data (e.g. `"income"` for annual income statement)
-   `"Q"` - All quarterly data (e.g. `"incomeQ"` for all quarterly income statements)
-   `"QX"` - Specific quarter data (e.g., `Q1`, `Q2`, `Q3`, `Q4`) (e.g. `"incomeQ2"` for all Q2 income statements)
-   `"TTM"` - Trailing Twelve Months data (e.g. `"incomeTTM"` for trailing twelve months income statement) - see [TTM Data](#/functions/financial-statements?id=ttm-data) section below for more information.

## [Metrics](#/functions/financial-statements?id=metrics)

The `metrics` parameter allows you to specify which line items of the financial statement you want to pull in. Options include:

-   Leaving blank or entering `"all"` to output the entire statement
-   Specifying individual line items such as `"revenue"` for the income statement
-   Chaining together multiple line items using the `&` operator, for example, `"calendarYear&revenue&netIncome&eps"`.

The available metrics/line items for each statement are outlined on their respective pages: [Income Statement](#/functions/income-statement), [Balance Sheet](#/functions/balancesheet-statement) and [Cash Flow Statement](#/functions/cashflow-statement).

> **⚠️ Caution:** Where possible, it is recommended to **not** use `"all"`, as statement structures may change over time. Use the `"all"` option to explore the available statement data and once you know what you're after, chain together the specific items you require to future-proof your spreadsheet.

> **💡 Tip:** The order in which you chain metrics is the order in which they are displayed.

## [Year(s)](#/functions/financial-statements?id=years)

The `year(s)` parameter can be specified in the following ways:

-   Specific Year - e.g., `"2020"` to return the financial statement for that year.
-   Range of Years - e.g., `"2015-2020"` to return multiple years of financial statements in one call.
-   `"ttm"` - to return the most recent TTM statement (for base statement types only, e.g. `"income"`, `"balancesheet"`, `"cashflow"`).
-   Specific date - e.g., `"2020-06-30"`. This can be used in two cases: (1) when generating a historical TTM statement as of that date (e.g. `"incomeTTM"`), or (2) when pulling quarterly data (with `Q` or `QX` suffix) in conjunction with the `"calYear"` option to return the specific quarter that includes that date. In the second case you can also enter only a year and month, for example `"2020-03"` to return the quarter that includes March 2020.

> **💡 Tip:** Omitting the `year(s)` parameter will default to the most recent annual/quarterly statement, for example, if you call `SF("AAPL", "income")` without specifying the year(s), it will return the most recent annual income statement, or `SF("AAPL", "incomeQ")` will return the most recent quarterly income statement.

## [Options](#/functions/financial-statements?id=options)

> **💡 Tip:** Options can be chained using the `&` operator, e.g. `"NH&NLI"`.

The options parameter can be used to adjust the way data is accessed and/or formatted. The available options are:

-   `"NH"` - No header rows.
-   `"NLI"` - No line item labels.
-   `"-"` - Reverse the year ordering (i.e., change the output to most recent to oldest).
-   `"calYear"` - When pulling data search our database by calendar year instead of fiscal year. By default, SheetsFinance returns financial statements based on the company's fiscal year. For example, if a company's fiscal year ends in June, the 2020 fiscal year statement would cover the period from July 2019 to June 2020. By using the `"calYear"` option, you can request financial statements based on the calendar year (January to December). This is particularly useful for comparing companies with different fiscal years or for aligning financial data with calendar-year-based analyses.
-   `"pad"` - When pulling quarterly data, this option will pad the output with empty columns for years or quarters that do not exist. For example, if you pull quarterly income statements for a company that has IPOd recently, using this option will ensure that all quarters from the earliest to the latest are represented in the output, even if some quarters have no data. This helps maintain a consistent structure in your data when comparing multiple companies or time periods.

## [TTM Data](#/functions/financial-statements?id=ttm-data)

There are a few ways to access TTM (trailing twelve months) data using the `SF()` function:

1.  Using the base statement type with `"ttm"` in the `year(s)` parameter for the latest TTM data. For example, `SF("AAPL", "income", "all", "ttm")` will return the most recent TTM income statement.
2.  Using the `TTM` suffix in the `type` parameter for historical TTM data as of a specific date. You can then enter:
    -   A year or range of years to get TTM statements per quarter for those years. For example, `SF("AAPL", "incomeTTM", "all", "2018-2020")` will return TTM income statements for each quarter from 2018 to 2020.
    -   A specific date to get the TTM statement as of that date. For example, `SF("AAPL", "incomeTTM", "all", "2020-06-30")` will return the TTM income statement as of June 30, 2020. Or, more generally, a year and month, e.g., `"2020-03"` to get the TTM statement as of March 2020.

## Embedded Content