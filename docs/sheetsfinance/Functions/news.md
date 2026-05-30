# SheetsFinance Docs | News Feeds

# [News Feed - Stocks (US Only), Crypto and FOREX/Commodities](#/functions/news?id=news-feed-stocks-us-only-crypto-and-forexcommodities)

The `SF_NEWS()` function hooks your spreadsheet into the latest news feeds for stocks, crypto, and FOREX/commodities. The function allows you to pull the latest news articles for a given symbol or collection of symbols (see [News Feed Batch](#/functions/newsBatch)). Additionally you can filter the feed by a combination of providers and instantly access the URL links to each article.

```
=SF_NEWS(symbol(s), type, limit, metrics, site, startDate, endDate, options)
```

-   `symbol(s)` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol. You can also use a range of cells e.g. `A1:A10` to pull news for multiple symbols, see [News Feed Batch](#/functions/newsBatch).
-   `type` selects the type of news feed to pull. The options are `"stocks"`, `"crypto"` or `"forexAndCommodities"`. Defaults to `"stocks"`.
-   `limit` sets the number of news articles to pull. Defaults to `10`. Limits are plan dependent check our [pricing page](https://sheetsfinance.com/pricing) for more information.
-   `metrics` selects what metrics to display (see options below), display all metrics by leaving blank or using `"all"`. Chain together as many metrics as you'd like using `&`, e.g., `"publishedDate&url"`.
-   `site` **OPTIONAL** filters the news feed by specific source sites (e.g. `"barrons.com"`), you can chain together multiple sites using `&`, e.g., `"barrons.com&cnbc.com"`.
-   `startDate` **OPTIONAL** sets the starting date of the news feed, written in iso format YYY-MM-DD, e.g. `"2022-01-01"`. Only applicable for `"stocks"` type.
-   `endDate` **OPTIONAL** sets the ending date of the news feed, written in iso format YYY-MM-DD, e.g. `"2022-01-10"`. Only applicable for `"stocks"` type.
-   `options` **OPTIONAL** adjusts the formatting of the output. Available options are `"NH"` for no header row and `"-"` for descending order. You can chain together multiple options using `&`, e.g., `"NH&-"`.

> **IMPORTANT:**
> 
> -   Data is sourced prior to filtering, so the number of articles returned may be less than the limit set if the filter criteria are too restrictive. Additionally, when accessing multiple symbols the limit is applied to the total number of articles returned, not per symbol, therefore if certain symbols do not have any recent articles in the returned feed then they will not be displayed.
> -   Stocks/equity data is currently only available for US stocks.

## [Metrics](#/functions/news?id=metrics)

The `news` metrics options are:

-   All (`"all"`)
-   Published Date (`"publishedDate"`)
-   Publisher (`"publisher"`)
-   Site (`"site"`)
-   Title (`"title"`)
-   Text (`"text"`)
-   URL (`"url"`)

## [Examples](#/functions/news?id=examples)

### [Example 1 - Display latest 10 articles for AAPL](#/functions/news?id=example-1-display-latest-10-articles-for-aapl)

```
=SF_NEWS("AAPL")
```

![News Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/news1.png "News Example 1")

### [Example 2 - Display latest 10 articles for BTC](#/functions/news?id=example-2-display-latest-10-articles-for-btc)

```
=SF_NEWS("BTCUSD", "crypto")
```

![News Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/news2.png "News Example 2")

### [Example 3 - Display latest 20 articles for AAPL with selected metrics](#/functions/news?id=example-3-display-latest-20-articles-for-aapl-with-selected-metrics)

```
=SF_NEWS("AAPL", "stocks", 20, "publishedDate&site&title&url")
```

![News Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/news3.png "News Example 3")

### [Example 4 - Display latest 10 articles, then filter by sites](#/functions/news?id=example-4-display-latest-10-articles-then-filter-by-sites)

```
=SF_NEWS("AAPL", "stocks", 20, "all", "barrons.com&seekingalpha.com&reuters.com&marketwatch.com")
```

![News Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/news4.png "News Example 4")

### [Example 5 - Display latest 10 articles for AAPL between specific dates (only available for stocks)](#/functions/news?id=example-5-display-latest-10-articles-for-aapl-between-specific-dates-only-available-for-stocks)

```

=SF_NEWS("AAPL", "stocks", 10, "all", "", "2022-01-01", "2022-01-10")
```

![News Example 5](https://cdn.sheetsfinance.com/public-site/img/docs/news5.png "News Example 5")

## Embedded Content