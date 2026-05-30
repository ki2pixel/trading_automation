# SheetsFinance Docs | Performance Optimisation

# [Best Practices for Performance Optimisation with SheetsFinance](#/use/performance-optimisation?id=best-practices-for-performance-optimisation-with-sheetsfinance)

_Last updated: November 2025_

SheetsFinance is designed to efficiently retrieve financial data directly into your Google Sheets. However, due to it's default nature as a Google Sheets extension it must abide by the limitations and behaviors of Google Sheets, which can sometimes lead to suboptimal performance if not managed correctly. This guide outlines best practices and strategies to optimise your usage of SheetsFinance, ensuring faster load times, reduced API quota consumption, and an overall smoother experience.

In this guide we will cover six key strategies:

1.  [Manage Background Refreshing Strategically](#/use/performance-optimisation?id=1-manage-background-refreshing-strategically)
2.  [Use Batch Functions for Multiple Symbols](#/use/performance-optimisation?id=2-use-batch-functions-for-multiple-symbols)
3.  [Chain Metrics Together](#/use/performance-optimisation?id=3-chain-metrics-together)
4.  [Request Multiple Years at Once](#/use/performance-optimisation?id=4-request-multiple-years-at-once)
5.  [Minimise Dynamic Function Usage](#/use/performance-optimisation?id=5-minimise-dynamic-function-usage)
6.  [Evaluate Third-Party Extensions](#/use/performance-optimisation?id=6-evaluate-third-party-extensions)

All of these strategies work toward the same goal:

```
Less Function Calls = Better Performance + Lower Quota Usage ✅
```

## [1\. Manage Background Refreshing Strategically](#/use/performance-optimisation?id=_1-manage-background-refreshing-strategically)

### [The Problem](#/use/performance-optimisation?id=the-problem)

Google Sheets automatically performs background refreshes on **all open spreadsheet files**, including sheets that aren't currently visible or active. If you have multiple sheets within a single file, each containing SheetsFinance functions, Google will refresh all of them periodically—even if you're only working on one sheet at a time.

### [Why This Matters](#/use/performance-optimisation?id=why-this-matters)

-   **Quota Consumption**: Background refreshes consume your daily Google external request quota unnecessarily, read more about Google Sheets quotas under [Limits](#/?id=limits).
-   **Performance Impact**: Multiple sheets refreshing simultaneously can slow down your entire spreadsheet
-   **Redundant Calls**: You may be making the same API calls multiple times across different sheets

### [Best Practices](#/use/performance-optimisation?id=best-practices)

**Split analyses across multiple spreadsheet files** rather than using multiple sheets within a single file:

-   Keep your real-time trading dashboard in one file
-   Store historical analysis in a separate file
-   Maintain company fundamentals research in another file

**Close files when not in use** to prevent background refreshing:

-   Only keep files open that you're actively working with
-   Bookmark frequently-used files for easy access

**Audit your functions** across all sheets:

-   Check for duplicate or redundant SheetsFinance functions
-   Remove functions from sheets you're no longer using
-   Consider consolidating data calls into a "raw data" sheet that feeds other sheets via cell references

**Example Structure:**

```
❌ Bad: One file with multiple sheets
- MyFinanceAnalysis.xlsx
  ├── Real-time Dashboard (refreshing constantly)
  ├── Historical Data (refreshing constantly)
  └── Watchlist (refreshing constantly)

✅ Good: Separate files
- RealTimeDashboard.xlsx (open only during trading hours)
- HistoricalAnalysis.xlsx (open when needed)
- Watchlist.xlsx (open when screening stocks)
```

---

## [2\. Use Batch Functions for Multiple Symbols](#/use/performance-optimisation?id=_2-use-batch-functions-for-multiple-symbols)

### [The Power of Batch Processing](#/use/performance-optimisation?id=the-power-of-batch-processing)

One of SheetsFinance's most powerful features is the ability to retrieve data for hundreds or even **thousands** of symbols with a single function call. This dramatically reduces API calls and improves performance.

### [How It Works](#/use/performance-optimisation?id=how-it-works)

Instead of writing individual functions for each ticker symbol:

**❌ Inefficient Approach:**

```
=SF("AAPL", "realTime", "price")
=SF("MSFT", "realTime", "price")
=SF("GOOGL", "realTime", "price")
... (1,000 more rows)
```

_This creates 1,003 separate API calls_

Write a single function for multiple symbols (listed in cells `A1:A1000` in this example):

**✅ Efficient Approach:**

```
=SF(A1:A1000, "realTime", "price&volume")
```

_This creates just 1 API call for 1,000 symbols each with 2 data points (2,000 data points total!)_

### [Batch Function Types](#/use/performance-optimisation?id=batch-function-types)

SheetsFinance offers batch processing for multiple data types, for example:

**Real-time Batch**

-   Get live prices, volumes, and market data for multiple symbols
-   Syntax: `=SF(A1:A100, "realTime", "price&volume&marketCap")`

**Company Info Batch**

-   Retrieve company fundamentals, descriptions, and static data
-   Syntax: `=SF(A1:A100, "companyInfo", "sector&industry&description")`

**Price Change Batch**

-   Calculate performance metrics across multiple symbols
-   Syntax: `=SF(A1:A100, "priceChange", "1D&1M&YTD")`

### [Performance Benefits](#/use/performance-optimisation?id=performance-benefits)

Approach

Symbols

API Calls

Quota Used

Individual

1,000

1,000

1,000

Batch

1,000

1

1

**Savings**

—

**99.9%**

**99.9%**

---

## [3\. Chain Metrics Together](#/use/performance-optimisation?id=_3-chain-metrics-together)

### [What is Metric Chaining?](#/use/performance-optimisation?id=what-is-metric-chaining)

Most SheetsFinance functions allow you to request multiple data points in a single function call using the chaining operator (`&`). This returns multiple columns of data from one API request.

### [Syntax](#/use/performance-optimisation?id=syntax)

```
=SF("TICKER", "dataType", "metric1&metric2&metric3")
```

### [Practical Examples](#/use/performance-optimisation?id=practical-examples)

**Real-time Data:**

```
=SF("AAPL", "realTime", "price&eps&volume")
```

Returns three columns: current price, earnings per share, and trading volume

**Statement Data:**

```
=SF("TSLA", "incomeQ", "date&period&revenue&netIncome&eps")
```

Returns five rows/line-times from the statement

**Combined with Batch Processing:**

```
=SF(A2:A100, "realTime", "price&change&changePercent&volume&marketCap")
```

Returns data for 99 symbols across 5 metrics = 495 data points in 1 API call !!

### [Benefits](#/use/performance-optimisation?id=benefits)

-   **Fewer API Calls**: Get 10+ metrics with one function instead of 10 functions
-   **Faster Performance**: Single API request is faster than multiple requests
-   **Easier Maintenance**: Update one formula instead of many
-   **Better Organisation**: Related data stays together in adjacent columns

---

## [4\. Request Multiple Years at Once](#/use/performance-optimisation?id=_4-request-multiple-years-at-once)

### [The Feature](#/use/performance-optimisation?id=the-feature)

Rather than creating separate functions for each year of historical data, SheetsFinance allows you to specify a **year range** that returns multiple years in a single function call.

### [Syntax](#/use/performance-optimisation?id=syntax-1)

```
=SF("TICKER", "dataType", "metric", "YYYY-YYYY")
```

### [Examples](#/use/performance-optimisation?id=examples)

**Income Statement Over Time:**

```
=SF("AAPL", "income", "all", "2000-2023")
```

Returns all income statement items for 24 years

**Specific Metrics:**

```
=SF("MSFT", "income", "revenue&netIncome&eps", "2015-2024")
```

Returns 10 years of revenue, net income, and EPS data

### [Supported Functions](#/use/performance-optimisation?id=supported-functions)

This feature works with all functions that support the year parameters, for example:

-   **Financial Statements - Income Statement**: `income`
-   **Financial Statements - Balance Sheet**: `balancesheet`
-   **Financial Statements - Cash Flow**: `cashflow`
-   **Key Ratios**: `ratios`
-   **Growth**: `growth`
-   (...and more)

---

## [5\. Minimise Dynamic Function Usage](#/use/performance-optimisation?id=_5-minimise-dynamic-function-usage)

### [Understanding the Problem](#/use/performance-optimisation?id=understanding-the-problem)

Google Sheets includes several "dynamic" functions that automatically recalculate frequently:

-   `TODAY()` - Returns the current date
-   `NOW()` - Returns the current date and time
-   `RAND()` - Returns a random number

**The Issue**: Every time these functions recalculate, they trigger a cascade of recalculations in any formulas that reference them—including your SheetsFinance functions.

### [Impact on Performance](#/use/performance-optimisation?id=impact-on-performance)

If you use `TODAY()` in multiple cells, each connected to SheetsFinance functions:

```
❌ Inefficient:
Cell A1: =SF_TIMESERIES("AAPL", TODAY()-365, TODAY())
Cell K1: =SF("MSFT", "historical", "close", TODAY()-30)
Cell M1: =SF("GOOGL", "incomeQ", "all", YEAR(TODAY()))
```

Each time `TODAY()` recalculates, all three SheetsFinance functions reload, potentially consuming quota unnecessarily.

### [Best Practice: Call Once, Reference Everywhere](#/use/performance-optimisation?id=best-practice-call-once-reference-everywhere)

**✅ Efficient Approach:**

1.  **Call the dynamic function once** in a dedicated cell:
    
    ```
    Cell B1: =TODAY()
    ```
    
2.  **Reference that cell** in all your formulas:
    
    ```
    Cell A1: =SF_TIMESERIES("AAPL", $B$1-365, $B$1)
    Cell K1: =SF("MSFT", "historical", "close", $B$1-30)
    Cell M1: =SF("GOOGL", "incomeQ", "all", YEAR($B$1))
    ```
    

Note the `$B$1` absolute reference—this ensures the reference doesn't change when copying the formula.

### [Benefits](#/use/performance-optimisation?id=benefits-1)

-   **Reduced Recalculations**: Functions only reload when the date actually changes
-   **Improved Performance**: Fewer cascading updates
-   **Quota Conservation**: Prevents redundant API calls
-   **Easier Updates**: Change the date in one place to affect all formulas

---

## [6\. Evaluate Third-Party Extensions](#/use/performance-optimisation?id=_6-evaluate-third-party-extensions)

### [The Hidden Cost of Multiple Extensions](#/use/performance-optimisation?id=the-hidden-cost-of-multiple-extensions)

While Google Sheets supports multiple add-ons and extensions working simultaneously, not all extensions are built with the same level of optimization. Some extensions may:

-   Make redundant API calls
-   Lack proper caching mechanisms
-   Trigger unnecessary recalculations
-   Consume shared quota inefficiently

### [SheetsFinance Optimisation Features](#/use/performance-optimisation?id=sheetsfinance-optimisation-features)

SheetsFinance is specifically designed with quota efficiency in mind:

**Intelligent Caching:**

-   Non-real-time data (company info, historical financials) is cached in multiple stages both locally and server-side
-   Subsequent calls to the same data often don't consume additional quota
-   Cache automatically refreshes on an appropriate schedule

**Request Batching:**

-   Multiple symbols handled in single API calls
-   Automatic grouping of similar requests
-   optimised payload sizes

### [Questions to Ask About Other Extensions](#/use/performance-optimisation?id=questions-to-ask-about-other-extensions)

If you're using multiple financial data extensions, evaluate them:

1.  **Does it cache data?** Or does it make a new API call every time?
2.  **Can it handle batch requests?** Or does each symbol require a separate call?
3.  **Does it run auto-refreshing under the hood?** Or only when you explicitly request data?
4.  **Is it actively maintained?** Outdated extensions may have inefficient code
5.  **Do you actually need it?** Can SheetsFinance handle the same tasks?

### [Audit Your Extensions](#/use/performance-optimisation?id=audit-your-extensions)

**Steps to review installed add-ons:**

1.  Go to **Extensions** → **Add-ons** → **Manage add-ons**
2.  Review each financial data extension
3.  Remove extensions you're not actively using
4.  Test SheetsFinance performance with and without other extensions enabled

---

## [Summary](#/use/performance-optimisation?id=summary)

Optimising your SheetsFinance usage comes down to six key principles:

1.  **Split files** to control background refreshing
2.  **Batch symbols** to minimise API calls
3.  **Chain metrics** to get more data per request
4.  **Request year ranges** instead of individual years
5.  **Call dynamic functions once** and reference them
6.  **Audit extensions** to ensure efficient quota usage

By following these guidelines, you'll enjoy faster spreadsheets, conserve your daily quota, and get more value from SheetsFinance.

---

## [Need Help?](#/use/performance-optimisation?id=need-help)

-   **Documentation**: [Full SheetsFinance documentation](#/use/performance-optimisation?id)
-   **Support**: Contact [support@sheetsfinance.com](mailto:support@sheetsfinance.com)
-   **Community**: Join our [Discord Server](https://discord.gg/DQr3J4QHqR) for tips and discussions

## Embedded Content