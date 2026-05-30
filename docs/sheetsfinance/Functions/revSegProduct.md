# SheetsFinance Docs | Revenue Segmentation by Product

# [Revenue Segmentation by Product](#/functions/revSegProduct?id=revenue-segmentation-by-product)

> **🇺🇸 Important:** Revenue segmentation data is only available for US markets

The `revSegProduct` data type returns revenue segmentation data by product category for a stock. This allows investors to analyze how a company's revenue is distributed across its various product lines. The data is sourced from SEC filings and reflects company-reported segmentations.

```
=SF(symbol, type, metrics, year, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` determines which quarterly or annual revenue segmentation data to display. Options include:
    -   Annual Revenue Segmentation (`"revSegProduct"`)
    -   Quarterly Revenue Segmentation for all Quarters (`"revSegProductQ"`)
    -   Quarterly Revenue Segmentation for Quarter X (`"revSegProductQX"`) where `X` can be `1`,`2`,`3` or `4`
-   `metrics` selects what metrics/product segements to display (see options below), display all metrics by leaving blank or using `"all"`. Note that each company will have different metrics based on their revenue segmentation. Chain together as many metrics as you'd like using `&`, e.g. for AAPL, `"period&date&iPhone&Mac"`.
-   `year` is the year or range of years for which you want to retrieve the data. You can enter a single year (e.g., `2020`) or a range of years (e.g., `2019-2021`).
-   `options` adjusts the formatting of the output. There are currently four (4) available options. (1) `"NH"` for no header rows, (2) `"NLI"` for no line item labels, (3) `"-"` to reverse the year ordering and (4) `"calYear"` which adjusts the search to calendar years instead of fiscal years. These options can be chained together with the `&` operator, for example `"NH&NLI&-"`.

The revenue segmentation by product `metric` options are:

-   Period (`"period"`)
-   Date (`"date"`)
-   Fiscal Year (`"fiscalYear"`)
-   Product-specific segments (varies by company)

> **Note:** The specific product segments vary by company. For example, Apple (`AAPL`) reports revenue under segments such as:
> 
> -   iPhone
> -   iPad
> -   Wearables, Home and Accessories
> -   Services
> -   Mac

## [Examples](#/functions/revSegProduct?id=examples)

#### [Example 1 - Display the most recent year of revenue segmentation data](#/functions/revSegProduct?id=example-1-display-the-most-recent-year-of-revenue-segmentation-data)

```
=SF("AAPL", "revSegProduct")
```

![Revenue Segmentation Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/revSegProduct_1.png "Revenue Segmentation Example 1")

#### [Example 2 - Display revenue segmentation for a specific year](#/functions/revSegProduct?id=example-2-display-revenue-segmentation-for-a-specific-year)

```
=SF("AAPL", "revSegProduct", "all", "2022")
```

![Revenue Segmentation Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/revSegProduct_2.png "Revenue Segmentation Example 2")

#### [Example 3 - Display several selected metrics for all quarters for a range of years](#/functions/revSegProduct?id=example-3-display-several-selected-metrics-for-all-quarters-for-a-range-of-years)

```
=SF("AAPL", "revSegProductQ", "period&date&iPhone&Mac&iPad", "2023-2024")
```

![Revenue Segmentation Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/revSegProduct_3.png "Revenue Segmentation Example 3")

#### [Example 4 - Display several selected metrics for a specific quarter of a specific year](#/functions/revSegProduct?id=example-4-display-several-selected-metrics-for-a-specific-quarter-of-a-specific-year)

```
=SF("AAPL", "revSegProductQ1", "period&date&iPhone&Mac&iPad", "2024")
```

![Revenue Segmentation Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/revSegProduct_4.png "Revenue Segmentation Example 4")

#### [Example 5 - Display several selected metrics for a specific quarter for a range of years](#/functions/revSegProduct?id=example-5-display-several-selected-metrics-for-a-specific-quarter-for-a-range-of-years)

```
=SF("AAPL", "revSegProductQ2", "period&date&iPhone&Mac&iPad", "2020-2024")
```

![Revenue Segmentation Example 5](https://cdn.sheetsfinance.com/public-site/img/docs/revSegProduct_5.png "Revenue Segmentation Example 5")

## Embedded Content