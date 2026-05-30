# SheetsFinance Docs | Company Growth

# [Company Growth](#/functions/growth?id=company-growth)

The `growth` function delivers percentage growth metrics for an asset from a specified year or quarter. This includes, for example, the percentage growth of company financials such as net income and gross profit, or the growth of important per share statistics such as EPS. The `growth` function also includes multi-year growth metrics such as 3, 5 and 10 year revenue per share growth. In this case, the figure is calculated as the absolute percentage change of that metric over the period, e.g., 3 year revenue per share growth in 2022 is the percentage change in revenue per share from 3 years ago (2019) to today. A series of [examples](#/functions/growth?id=examples) are provided below.

```
=SF(symbol, type, metrics, year(s), options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` is where you specify which type of growth data you are after, leave it as just`"growth"` for annual growth data, or append the specific quarter for quarterly growth data. For example, enter `"growthQ1"` for Q1 growth data, or `"growthQ2"` for Q2 growth data.
-   `metrics` is the growth metric(s) you are after, for example `"revenueGrowth"` or `"revenueGrowth&ebitgrowth&dividendsperShareGrowth"`. You can leave this blank or set it to `"all"` to output ALL available growth metrics. You can also chain together multiple metrics using the `&` operator, for example `"ebitgrowth&dividendsperShareGrowth"`. See the full list of over 30 available growth metrics below.
-   `year` is the year for the growth data, e.g., `"2020"`. This can also be set to a range of years, e.g. `"2010-2020"` to return multiple years of growth data, both quarterly and annual, in one call.
-   `options` adjusts the formatting of the output. There are currently four (5) available options. (1) `"NH"` for no header rows, (2) `"NLI"` for no line item labels, (3) `"-"` to reverse the year ordering, (4) `"calYear"` which adjusts the search to calendar years instead of fiscal years and (5) `"pad"` which adds padding of empty columns to the output for missing years or quarters. These options can be chained together with the `&` operator, for example `"NH&NLI&-"`.

> **HOT TIPS:**
> 
> -   You can enter a range of years for both annual and quarterly growth data, e.g., `"2015-2021"` and get multiple years output side-by-side.
> -   Use the options parameter to reverse the year ordering, remove the header and/or line item labels.
> -   If you input a range of years and don't specify the quarter number, e.g. `=SF("AAPL", "growthQ", "all", "2010-2020")` you will be returned **all** quarters for each year in the range.

> **IMPORTANT:**
> 
> -   If you do not provide the `year` parameter this function will default to the most recently reported annual or quarterly growth data.
> -   Data is outputed in raw/decimal format, therefore 0.106 = 10.6%.

The `growth` data type has the following metrics to select from:

-   All (`"all"`)
-   Revenue Growth (`"revenueGrowth"`)
-   Gross Profit Growth (`"grossProfitGrowth"`)
-   EBIT Growth (`"ebitgrowth"`)
-   Operating Income Growth (`"operatingIncomeGrowth"`)
-   Net Income Growth (`"netIncomeGrowth"`)
-   EPS Growth (`"epsgrowth"`)
-   EPS Diluted Growth (`"epsdilutedGrowth"`)
-   Weighted Average Shares Growth (`"weightedAverageSharesGrowth"`)
-   Weighted Average Shares Diluted Growth (`"weightedAverageSharesDilutedGrowth"`)
-   Dividends per Share Growth (`"dividendsperShareGrowth"`)
-   Operating Cash Flow Growth (`"operatingCashFlowGrowth"`)
-   Free Cash Flow Growth (`"freeCashFlowGrowth"`)
-   10y Revenue Growth Per Share (`"tenYRevenueGrowthPerShare"`)
-   5y Revenue Growth Per Share (`"fiveYRevenueGrowthPerShare"`)
-   3y Revenue Growth Per Share (`"threeYRevenueGrowthPerShare"`)
-   10y Operating CF Growth Per Share (`"tenYOperatingCFGrowthPerShare"`)
-   5y Operating CF Growth Per Share (`"fiveYOperatingCFGrowthPerShare"`)
-   3y Operating CF Growth Per Share (`"threeYOperatingCFGrowthPerShare"`)
-   10y Net Income Growth Per Share (`"tenYNetIncomeGrowthPerShare"`)
-   5y Net Income Growth Per Share (`"fiveYNetIncomeGrowthPerShare"`)
-   3y Net Income Growth Per Share (`"threeYNetIncomeGrowthPerShare"`)
-   10y Shareholders Equity Growth Per Share (`"tenYShareholdersEquityGrowthPerShare"`)
-   5y Shareholders Equity Growth Per Share (`"fiveYShareholdersEquityGrowthPerShare"`)
-   3y Shareholders Equity Growth Per Share (`"threeYShareholdersEquityGrowthPerShare"`)
-   10y Dividend per Share Growth Per Share (`"tenYDividendperShareGrowthPerShare"`)
-   5y Dividend per Share Growth Per Share (`"fiveYDividendperShareGrowthPerShare"`)
-   3y Dividend per Share Growth Per Share (`"threeYDividendperShareGrowthPerShare"`)
-   Receivables Growth (`"receivablesGrowth"`)
-   Inventory Growth (`"inventoryGrowth"`)
-   Asset Growth (`"assetGrowth"`)
-   Book Value per Share Growth (`"bookValueperShareGrowth"`)
-   Debt Growth (`"debtGrowth"`)
-   R&D Expense Growth (`"rdexpenseGrowth"`)
-   SG&A Expenses Growth" (`"sgaexpensesGrowth"`)

## [Examples](#/functions/growth?id=examples)

### [Example 1 - Single metric (EPS Growth)](#/functions/growth?id=example-1-single-metric-eps-growth)

```
=SF("AAPL", "growth", "epsgrowth", "2022")

0.08465608466 (8.47%)
```

### [Example 2 - Multiple annual metrics (EPS Growth & Revenue Growth)](#/functions/growth?id=example-2-multiple-annual-metrics-eps-growth-amp-revenue-growth)

```
=SF("AAPL", "growth", "epsgrowth&revenueGrowth", "2022")
```

![Growth Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/growth_2.png "Growth Example 2")

### [Example 3 - Multiple years and all metrics](#/functions/growth?id=example-3-multiple-years-and-all-metrics)

```
=SF("AAPL", "growth", "all", "2012-2022")
```

![Growth Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/growth_3.png "Growth Example 3")

### [Example 4 - Quarterly growth data for Q4 2022](#/functions/growth?id=example-4-quarterly-growth-data-for-q4-2022)

```
=SF("AAPL", "growthQ4", "all", "2022")
```

![Growth Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/growth_4.png "Growth Example 4")

### [Example 5 - Several growth metrics with no header rows and no line item labels](#/functions/growth?id=example-5-several-growth-metrics-with-no-header-rows-and-no-line-item-labels)

```
=SF("AAPL", "growth", "dividendsperShareGrowth&netIncomeGrowth&ebitgrowth", "2022", "NH&NLI")
```

![Growth Example 5](https://cdn.sheetsfinance.com/public-site/img/docs/growth_5.png "Growth Example 5")

### [Example 6 - Multiple years and reversed year ordering](#/functions/growth?id=example-6-multiple-years-and-reversed-year-ordering)

```
=SF("AAPL", "growth", "all", "2010-2020", "-")
```

![Growth Example 6](https://cdn.sheetsfinance.com/public-site/img/docs/growth_6.png "Growth Example 6")

## Embedded Content