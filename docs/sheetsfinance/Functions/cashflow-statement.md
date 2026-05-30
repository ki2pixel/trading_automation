# Cash Flow

# [Cash Flow Statement](#/functions/cashflow-statement?id=cash-flow-statement)

🚀 **Update (November 2025):** You are viewing the latest cash flow statement documentation, to view legacy documentation for the deprecated cash flow statement function see [Historical Financial Statements (Deprecated)](/docs#/functions/historicalFinancials).

You can access 30+ years of standardised annual, quarterly and TTM (trailing twelve months) cash flow statements using the `SF()` function with the base type of `"cashflow"`.

```
=SF(symbol, type, metrics, year(s), options)
```

-   `symbol` - The ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` - The type of financial statement you want to pull in. See [Type](#/functions/cashflow-statement?id=type) section below for more information.
-   `metrics` - The specific line items of the cash flow statement you are after. See [Metrics](#/functions/cashflow-statement?id=metrics) section below for full list.
-   `year(s)` - The year, range of years or date for the financial statement. See [Year(s)](#/functions/cashflow-statement?id=years) section for more information.
-   `options` - Additional options for adjusting the way data is called or formatted. See [Options](#/functions/cashflow-statement?id=options) section below for more information.

#### [](#/functions/cashflow-statement?id=jump-to-examples-darr)[Jump to Examples ↓](#/functions/cashflow-statement?id=examples)

## [Type](#/functions/cashflow-statement?id=type)

The `type` is made up of the base statement type and then followed by a suffix which indicates quarterly or TTM data. For the cash flow statement, the base statement type is: `"cashflow"`. The suffixes that can be used with the base statement type are:

-   No suffix - Annual data (e.g. `"cashflow"` for annual cash flow statement)
-   `"Q"` - All quarterly data (e.g. `"cashflowQ"` for all quarterly cash flow statements)
-   `"QX"` - Specific quarter data (e.g., `Q1`, `Q2`, `Q3`, `Q4`) (e.g. `"cashflowQ2"` for all Q2 cash flow statements)
-   `"TTM"` - Trailing Twelve Months data (e.g. `"cashflowTTM"` for trailing twelve months cash flow statement) - see [TTM Data](#/functions/cashflow-statement?id=ttm-data) section below for more information.

## [Metrics](#/functions/cashflow-statement?id=metrics)

The available metrics/line items for the cash flow statement are as follows:

-   All (`"all"`)
-   Date (`"date"`)
-   Symbol (`"symbol"`)
-   Reported Currency (`"reportedCurrency"`)
-   CIK (`"cik"`)
-   Filing Date (`"filingDate"`)
-   Accepted Date (`"acceptedDate"`)
-   Fiscal Year (`"fiscalYear"`)
-   Period (`"period"`)
-   Net Income (`"netIncome"`)
-   Depreciation And Amortization (`"depreciationAndAmortization"`)
-   Deferred Income Tax (`"deferredIncomeTax"`)
-   Stock Based Compensation (`"stockBasedCompensation"`)
-   Change In Working Capital (`"changeInWorkingCapital"`)
-   Accounts Receivables (`"accountsReceivables"`)
-   Inventory (`"inventory"`)
-   Accounts Payables (`"accountsPayables"`)
-   Other Working Capital (`"otherWorkingCapital"`)
-   Other Non Cash Items (`"otherNonCashItems"`)
-   Net Cash Provided By Operating Activities (`"netCashProvidedByOperatingActivities"`)
-   Investments In Property Plant And Equipment (`"investmentsInPropertyPlantAndEquipment"`)
-   Acquisitions Net (`"acquisitionsNet"`)
-   Purchases Of Investments (`"purchasesOfInvestments"`)
-   Sales Maturities Of Investments (`"salesMaturitiesOfInvestments"`)
-   Other Investing Activities (`"otherInvestingActivities"`)
-   Net Cash Provided By Investing Activities (`"netCashProvidedByInvestingActivities"`)
-   Net Debt Issuance (`"netDebtIssuance"`)
-   Long Term Net Debt Issuance (`"longTermNetDebtIssuance"`)
-   Short Term Net Debt Issuance (`"shortTermNetDebtIssuance"`)
-   Net Stock Issuance (`"netStockIssuance"`)
-   Net Common Stock Issuance (`"netCommonStockIssuance"`)
-   Common Stock Issuance (`"commonStockIssuance"`)
-   Common Stock Repurchased (`"commonStockRepurchased"`)
-   Net Preferred Stock Issuance (`"netPreferredStockIssuance"`)
-   Net Dividends Paid (`"netDividendsPaid"`)
-   Common Dividends Paid (`"commonDividendsPaid"`)
-   Preferred Dividends Paid (`"preferredDividendsPaid"`)
-   Other Financing Activities (`"otherFinancingActivities"`)
-   Net Cash Provided By Financing Activities (`"netCashProvidedByFinancingActivities"`)
-   Effect Of Forex Changes On Cash (`"effectOfForexChangesOnCash"`)
-   Net Change In Cash (`"netChangeInCash"`)
-   Cash At End Of Period (`"cashAtEndOfPeriod"`)
-   Cash At Beginning Of Period (`"cashAtBeginningOfPeriod"`)
-   Operating Cash Flow (`"operatingCashFlow"`)
-   Capital Expenditure (`"capitalExpenditure"`)
-   Free Cash Flow (`"freeCashFlow"`)
-   Income Taxes Paid (`"incomeTaxesPaid"`)
-   Interest Paid (`"interestPaid"`)

## [Year(s)](#/functions/cashflow-statement?id=years)

The `year(s)` parameter can be specified in the following ways:

-   Specific Year - e.g., `"2020"` to return the cash flow for that year.
-   Range of Years - e.g., `"2015-2020"` to return multiple years of cash flows in one call.
-   `"ttm"` - to return the most recent TTM cash flow.
-   Specific date - e.g., `"2020-06-30"`. This can be used in two cases: (1) when generating a historical TTM statement as of that date (e.g. `"cashflowTTM"`), or (2) when pulling quarterly data (with `Q` or `QX` suffix) in conjunction with the `"calYear"` option to return the specific quarter that includes that date. In the second case you can also enter only a year and month, for example `"2020-03"` to return the quarter for March 2020.

> **💡 Tip:** Omitting the `year(s)` parameter will default to the most recent annual/quarterly statement, for example, if you call `SF("AAPL", "cashflow")` without specifying the year(s), it will return the most recent annual cash flow, or `SF("AAPL", "cashflowQ")` will return the most recent quarterly cash flow.

## [Options](#/functions/cashflow-statement?id=options)

> **💡 Tip:** Options can be chained using the `&` operator, e.g. `"NH&NLI"`.

The options parameter can be used to adjust the way data is accessed and/or formatted. The available options are:

-   `"NH"` - No header rows.
-   `"NLI"` - No line item labels.
-   `"-"` - Reverse the year ordering (i.e., change the output to most recent to oldest).
-   `"calYear"` - When pulling data search our database by calendar year instead of fiscal year. By default, SheetsFinance returns financial statements based on the company's fiscal year. For example, if a company's fiscal year ends in June, the 2020 fiscal year statement would cover the period from July 2019 to June 2020. By using the `"calYear"` option, you can request financial statements based on the calendar year (January to December). This is particularly useful for comparing companies with different fiscal years or for aligning financial data with calendar-year-based analyses.
-   `"pad"` - When pulling quarterly data, this option will pad the output with empty columns for years or quarters that do not exist. For example, if you pull quarterly income statements for a company that has IPOd recently, using this option will ensure that all quarters from the earliest to the latest are represented in the output, even if some quarters have no data. This helps maintain a consistent structure in your data when comparing multiple companies or time periods.

## [TTM Data](#/functions/cashflow-statement?id=ttm-data)

There are a few ways to access TTM (trailing twelve months) data using the `SF()` function:

1.  Using the base statement type with `"ttm"` in the `year(s)` parameter for the latest TTM data. For example, `SF("AAPL", "cashflow", "all", "ttm")` will return the most recent TTM cash flow statement.
2.  Using the `TTM` suffix in the `type` parameter for historical TTM data as of a specific date. You can then enter:
    -   A year or range of years to get TTM statements per quarter for those years. For example, `SF("AAPL", "cashflowTTM", "all", "2018-2020")` will return TTM cash flows for each quarter from 2018 to 2020.
    -   A specific date to get the TTM statement as of that date. For example, `SF("AAPL", "cashflowTTM", "all", "2020-06-30")` will return the TTM cash flow as of June 30, 2020. Or, more generally, a year and month, e.g., `"2020-03"` to get the TTM statement as of March 2020.

## [Examples](#/functions/cashflow-statement?id=examples)

### [Example 1: Most recent annual cash flow with all metrics](#/functions/cashflow-statement?id=example-1-most-recent-annual-cash-flow-with-all-metrics)

```
=SF("AAPL", "cashflow")
```

![Example 1 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_1.png "Example 1 - Cash flow Statement")

### [Example 2: Most recent TTM cashflow with selected metrics, no header](#/functions/cashflow-statement?id=example-2-most-recent-ttm-cashflow-with-selected-metrics-no-header)

```
=SF("AAPL", "cashflow", "period&cashAtBeginningOfPeriod&freeCashFlow&cashAtEndOfPeriod", "ttm", "NH")
```

![Example 2 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_2.png "Example 2 - Cash flow Statement")

### [Example 3: A range of annual cash flows for specific years, all metrics, no header option and in reversed year order](#/functions/cashflow-statement?id=example-3-a-range-of-annual-cash-flows-for-specific-years-all-metrics-no-header-option-and-in-reversed-year-order)

> **💡 Tip:** The `"NH"` option removes the header row of dates/years from the output. The `"-"` option reverses the year order to most recent to oldest. Combine both with `&`.

```
=SF("AAPL", "cashflow", "all", "2015-2020", "NH&-")
```

![Example 3 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_3.png "Example 3 - Cash flow Statement")

### [Example 4: Single value - annual free cash flow in 2023](#/functions/cashflow-statement?id=example-4-single-value-annual-free-cash-flow-in-2023)

> **💡 Tip:** When a value is fully specified with a single metric and year, no header or line item labels are included in the output.

```
=SF("AAPL", "cashflow", "freeCashFlow", "2023")
```

![Example 4 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_4.png "Example 4 - Cash flow Statement")

### [Example 5: TTM cash flow as of a specific date with all metrics](#/functions/cashflow-statement?id=example-5-ttm-cash-flow-as-of-a-specific-date-with-all-metrics)

```
=SF("AAPL", "cashflowTTM", "all", "2020-06-30")
```

![Example 5 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_5.png "Example 5 - Cash flow Statement")

### [Example 6: Quarterly cash flows for a specific quarter across multiple years, selected metrics](#/functions/cashflow-statement?id=example-6-quarterly-cash-flows-for-a-specific-quarter-across-multiple-years-selected-metrics)

```
=SF("AAPL", "cashflowQ2", "date&cashAtBeginningOfPeriod&freeCashFlow&cashAtEndOfPeriod", "2018-2020")
```

![Example 6 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_6.png "Example 6 - Cash flow Statement")

### [Example 7: Quarterly statements for a specific calendar year instead of fiscal year](#/functions/cashflow-statement?id=example-7-quarterly-statements-for-a-specific-calendar-year-instead-of-fiscal-year)

> **💡 Tip:** The `"calYear"` option adjusts the search to calendar years instead of fiscal years.

```
=SF("AAPL", "cashflowQ", "all", "2020", "calYear")
```

![Example 7 - Cash flow Statement](https://cdn.sheetsfinance.com/public-site/img/docs/cashflow_7.png "Example 7 - Cash flow Statement")

## Embedded Content