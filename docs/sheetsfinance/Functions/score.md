# SheetsFinance Docs | Financial Score

# [Financial Score - Altmans Z-Score and Piotroski F-Score](#/functions/score?id=financial-score-altmans-z-score-and-piotroski-f-score)

The `score` data type returns two financial scores for a stock: the Altman's Z-Score and the Piotroski F-Score in conjunction with the underlying metrics used to calculate these scores. These scores are used to evaluate the financial health and performance of a company. The Altman's Z-Score is a measure of a company's likelihood of bankruptcy, while the Piotroski F-Score is a measure of a company's financial strength and profitability.

```
=SF(symbol, "score", metric, "", options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `metric` selects what metrics to display (see options below), display all metrics by leaving blank or using `"all"`. Chain together as many metrics as you'd like using `&`, e.g., `"date&zScore&fScore"`.
-   `options` adjusts the formatting of the output. Available options include: `"NH"` for no header rows and `"NLI"` for no line items. You can chain together as many options as you'd like using `&`, e.g., `"NH&NLI"`.

The `score` `metric` options are:

-   All (`"all"`)
-   Revenue (`"revenue"`)
-   Total Liabilities (`"totalLiabilities"`)
-   Market Capitalization (`"marketCap"`)
-   EBIT (`"ebit"`)
-   Retained Earnings (`"retainedEarnings"`)
-   Total Assets (`"totalAssets"`)
-   Working Capital (`"workingCapital"`)
-   Piotroski F-Score (`"piotroskiScore"`)
-   Altman's Z-Score (`"altmanZScore"`)

> **Important:** The Altman's Z-Score and Piotroski F-Score are calculated based on the financial data of the company and are used as indicators of financial health and performance.

## [Examples](#/functions/score?id=examples)

#### [Example 1 - Display all financial scores and metrics](#/functions/score?id=example-1-display-all-financial-scores-and-metrics)

```
=SF("AAPL", "score")
```

![Financial Score Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/score_1.png "Financial Score Example 1")

#### [Example 2 - Display selected metrics and scores](#/functions/score?id=example-2-display-selected-metrics-and-scores)

```
=SF("AAPL", "score", "piotroskiScore&altmanZScore")
```

![Financial Score Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/score_2.png "Financial Score Example 2")

#### [Example 3 - Display single metric](#/functions/score?id=example-3-display-single-metric)

```
=SF("AAPL", "score", "altmanZScore")
```

![Financial Score Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/score_3.png "Financial Score Example 3")

## Embedded Content