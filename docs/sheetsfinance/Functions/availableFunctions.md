# SheetsFinance Docs | Available Functions

# [Using our functions](#/functions/availableFunctions?id=using-our-functions)

SheetsFinance has access to hundreds of thousands of data points but we've kept things nice and simple for you. There are 11 core functions used by our add-on to access the entire range of financial information from realtime stock prices to minute-by-minute timeseries.

## [SF()](#/functions/availableFunctions?id=sf)

Most of our real-time and historical data can be accessed using our `SF()` function. This function's layout is as follows:

```
=SF(symbol, type, subtype/metric, year, options)
```

-   `symbol` is the symbol of the financial asset (e.g. `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol. This can sometimes be a range of cells, see [Real-time Batch](#/functions/realtimeBatch) or [Company Info Batch](#/functions/companyinfoBatch).
-   `type` is the data type category, here is a list of some of the options available:
    -   `"realTime"`
    -   `"companyInfo"`
    -   `"historical"`
    -   `"ratios"`
    -   `"peers"`
    -   `"growth"`
    -   `"change"`
    -   `"estimates"`
    -   `"priceTargets"`
    -   `"analysts"`
    -   `"ratings"`
    -   `"instHolders"`
    -   `"etfInfo"`
    -   `"etfHoldings"`
    -   `"etfSectors"`
    -   `"historicalFinancialsIncome"`
    -   `"historicalFinancialsBalance"`
    -   `"historicalFinancialsCash"`
-   `subtype/metric` is the data type subcategory. For the full list of options see that data type's documentation.
-   `year` is generally the year in YYYY form (e.g. `"2010"`) used for the `"historicalFinancialX"`, `"growth"`, `"historical"` or `"ratios"` data types, it can be left off when using `"realTime"` or `"companyInfo"` and is optional for `analysts` and `ratings`. This can also be a range of years (e.g. `"2010-2020"`) or `"ttm"` when using `"historicalFinancialX"`, see [Multiple Years](#/functions/historicalFinancials?id=multiple-years). This field is treated as the last X months for the `"priceTargets"` data type.
-   `options` adjusts the formatting of the output data. Available options vary per data type, please see that data type's documentation.

See more on it's usage in [Realtime](#/functions/realtime), [Company Info](#/functions/companyInfo), [Key Ratios](#/functions/ratios),[Peers](#/functions/peers), [Company Growth](#/functions/growth), [Price Targets](#/functions/priceTargets), [Analyst Estimates](#/functions/estimates), [Analyst Ratings](#/functions/analysts), [Analyst Ratings Totals](#/functions/analysts), [Historical Financials](#/functions/historicalFinancials), [ETF Info](#/functions/etfInfo), [ETF Holdings](#/functions/etfHoldings), [ETF Sectors](#/functions/etfSectors) and [Institutional Holders](#/functions/instHolders).

### [Quick realtime price](#/functions/availableFunctions?id=quick-realtime-price)

If no `type`, `subtype` or `year` is given then the function will default to return the realtime current price. This can simplify the process of quickly returning a stock or coin price. For example:

**Stock realtime price:**

```
=SF("AAPL")
```

**Crypto realtime price:**

```
=SF("BTCUSD")
```

**FOREX realtime rate:**

```
=SF("USDGBP")
```

---

## [SF\_TIMESERIES()](#/functions/availableFunctions?id=sf_timeseries)

Historical stock or coin price and volume data can be generated via `SF_TIMESERIES()`. This function will return multiple rows of data depending on the timeseries range or period specified. This functions layout is as follows:

```
=SF_TIMESERIES(symbol, startDate, endDate, period, metric, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `startDate` is the starting date of the timeseries, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`
-   `endDate` is the ending date of the timeseries, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `period` specifies the period for an intraday timeseries (e.g. 5 minute intervals, `"5min"`). This parameter will override `startDate` and `endDate` if used and can be left out for a daily timeseries.
-   `metric` selects what metric to display. Choose from `"open"`, `"high"`, `"low"`, `"close"`, `"volume"`, `"change"` and `"changePercent"`
-   `options` adjusts the formatting of the output. `"-"` for descending order and `"NH"` for no header on the output. These can be combined like so `"-&NH"`.

See more on it's usage in [Timeseries](#/functions/timeseries)

---

## [SF\_DIVIDEND()](#/functions/availableFunctions?id=sf_dividend)

Historical company dividends can be generated via `SF_DIVIDEND()`. This function will return multiple rows and columns of data depending on the date range supplied and the metrics requested. The function layout is as follows:

```
=SF_DIVIDEND(symbol, startDate, endDate, metric, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `startDate` is the start date for the dividend history, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`
-   `endDate` is the end date for the dividend history, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `metric` selects what metrics to display. Leave blank or use `"all"` to display all metrics. Chain together metrics with `&` symbol to display more than one (e.g. `"date&dividend"`). Metrics include `"date"`, `"dividend"`, `"adjDividend"`, `"recordDate"`, `"paymentDate"` and `"declarationDate"`.
-   `options` adjusts the formatting of the output. `"-"` for descending order and `"NH"` for no header on the output. These can be combined like so `"-&NH"`.

See more on it's usage in [Dividends](#/functions/dividends)

---

## [SF\_OPTIONS()](#/functions/availableFunctions?id=sf_options)

The option chain for a stock can be generated with `SF_OPTIONS()`. This function will return multiple rows and columns depending on the number of options contracts for a particular expiration date and the metrics selected to be displayed. The function layout is as follows:

```
=SF_OPTIONS(symbol, type, metric, expirationDate, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`) or of the options contract (e.g., `"AAPL240920C00160000"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `metric` selects what metrics to display. Leave blank or use "all" to display all metrics. Chain together metrics with `&` symbol to display more than one (e.g. `"contractSymbol&strike"`). Metrics include: `'"contractSymbol"`, `"strike"`, `"currency"`, `"lastPrice"`, `"change"`, `"percentChange"`, `"volume"`, `"openInterest"`, `"bid"`, `"ask"`, `"contractSize"`, \`\`"expiration"`,` "lastTradeDate"`,` "impliedVolatility"`,` "intheMoney"\`.
-   `expirationDate` sets the expiration date of the options in iso format YYY-MM-DD, e.g. `"2023-10-23"`, this will default to the next date _after_ the expiration entered if not exact.
-   `options` adjusts the formatting of the output. `"-"` for descending order and `"NH"` for no header on the output. These can be combined like so `"-&NH"`.

See more on its usage in [Options Chains & Contracts](#/functions/options)

---

## [SF\_OPTIONS\_PRO()](#/functions/availableFunctions?id=sf_options_pro)

Professional options analytics can be generated with `SF_OPTIONS_PRO()`. This function gives you access to full OPRA chains with greeks, historical chain snapshots, IV term structure, surface data, earnings analytics and IV rank data. The function layout is as follows:

```
=SF_OPTIONS_PRO(symbol, dataType, expirationDate, strike, tradeDate, endDate, metrics, options)
```

-   `symbol` is the ticker symbol of the underlying asset (for example `"AAPL"`), a fully specified OCC contract symbol (for example `"AAPL251219C00165000"`), or a range of symbols for batched `"ivRank"` requests.
-   `dataType` selects the options analytics dataset. Available options are `"calls"`, `"puts"`, `"calls&puts"`, `"expirationDates"`, `"ivPeriods"`, `"surface"`, `"surfaceForecast"`, `"earnings"` and `"ivRank"`. Entering `"strikes"` aliases to `"calls&puts"`.
-   `expirationDate` sets the target expiration date in `YYYY-MM-DD` format or as an Excel date serial for the expiry-aware datasets.
-   `strike` is used for contract-level lookups when you are not using a full OCC contract symbol. Leave it blank for full chain outputs and for the non-contract data types.
-   `tradeDate` requests historical data when supplied. For `"expirationDates"`, it returns the expiration dates that were available on that historical date.
-   `endDate` is used for historical `"calls"`, `"puts"`, `"ivPeriods"` and `"ivRank"` requests.
-   `metrics` selects what metrics to display. Leave blank or use `"all"` to display all available metrics, or chain together fields with `&`.
-   `options` allows additional request or output options to be chained together with `&`.

See more on its usage in the [Options overview](#/functions/options-pro), [Chains & Contracts](#/functions/options-pro-chains-contracts), [Historical Chains](#/functions/options-pro-historical-chains), [Contract & Strike Time-series](#/functions/options-pro-contract-strike-time-series), [Expiration Dates](#/functions/options-pro-expiration-dates), [IV Periods](#/functions/options-pro-iv-periods), [IV Periods Time-series](#/functions/options-pro-iv-periods-time-series), [Surface](#/functions/options-pro-surface), [Surface Forecast](#/functions/options-pro-surface-forecast), [Earnings](#/functions/options-pro-earnings), [IV Rank](#/functions/options-pro-iv-rank), [IV Rank Time-series](#/functions/options-pro-iv-rank-time-series) and [IV Rank Batch](#/functions/options-pro-iv-rank-batch).

---

## [SF\_CALENDAR()](#/functions/availableFunctions?id=sf_calendar)

Use the `SF_CALENDAR()` function to access a number of different financial calendars such as earnings, dividends, splits and macroeconomics. This function is also used for other date-based financial data, such as US Treasury Rates. This function will return multiple rows and columns depending on the date range supplied and the metrics requested. The function layout is as follows:

```
=SF_CALENDAR(searchTerms, type, startDate, endDate, metrics, options)
```

-   `searchTerms` is a series of terms to filter the calendar results by. Multiple terms can be chained together with the `&` symbol. Leaving this blank applies no filtering to the calendar.
-   `type` is the type of calendar to generate. Available options are `"earnings"`, `"dividends"`, `"splits"`, `"economic"` and `"treasury"`.
-   `startDate` is the start date for the calendar, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`. The maximum range between `startDate` and `endDate` for one function call is 90 days. If the range is larger than this it will be truncated to 90 days.
-   `endDate` is the end date for the calendar, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `metric` selects what metrics to display. Leave blank or use `"all"` to display all metrics. Chain together metrics with `&` symbol to display more than one (e.g. `"date&dividend"`). Metrics are specific to the calendar type, see the calendar type's documentation for more information.
-   `options` adjusts the formatting of the output. `"-"` for descending order and `"NH"` for no header on the output. These can be combined like so `"-&NH"`.

See more on it's usage in [Calendar](#/functions/calendar) and [US Treasury Rates](#/functions/treasury)

---

## [SF\_SPARK()](#/functions/availableFunctions?id=sf_spark)

A Google Sheets sparkline of historical stock or coin price can be generated with the help of `SF_SPARK()`. This function is to be **used in conjunction with** Google Sheet's built in sparklines function (`SPARKLINE()`). This functions layout is as follows:

```
=SF_SPARK(symbol, lastXdays, type)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `lastXdays` is a integer value to specify the number of days to display the price sparkline over (e.g. `"365"` will display the price performance of the last year)
-   `type` is either `"price"` (or left empty) to return a price sparkline or `"volume"` for a volume bar chart sparkline.

**Important:** This function should be nested in Google Sheet's sparkline function like so: `SPARKLINE(SF_SPARK())`. See more on it's usage in [Sparklines](#/functions/sparklines)

---

## [SF\_TECHNICAL()](#/functions/availableFunctions?id=sf_technical)

Technical analysis is achieved using the `SF_TECHNICAL()` function. The function allows for the generation of a specified technical analysis layered over the historical price data of a stock, crypto or ETF. You are able to define a period and apply the analysis over ranges within that period, for instance a 20 day SMA with daily data or a 20 min SMA with minute-by-minute intra-day data.

```
=SF_TECHNICAL(symbol, type, period, startDate, endDate, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `type` is the analysis type chained together (using the `&` operator) with the additional display items you want to include in your output. The available analysis types are available below. Remember to include the subperiod, for example `sma20` would be a Simple Moving Average (SMA) applied over 20 periods. Some examples are `"sma20&all"`, `"ema50&date&close"` and `"williams100&date&high&low"`.
-   `period` defines the base period, for example `"daily"`, `"1min"` or `"30min"`. All period options are outlined below.
-   `startDate` is the starting date of the time series, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`
-   `endDate` is the ending date of the time series, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `options` adjusts the formatting of the output. There are currently only one available option, you can set this field to `"NH"` for no header row. Of course, this option does not apply for single cell outputs.

See more on it's usage in [Technicals](#/functions/technicals)

## [SF\_NEWS()](#/functions/availableFunctions?id=sf_news)

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

See more on it's usage in [News](#/functions/news)

---

## [SF\_SCREEN()](#/functions/availableFunctions?id=sf_screen)

If you're looking to screen our entire database of financial assets by a variety of metrics, then `SF_SCREEN()` is what you're after. Unlike all other SheetsFinance functions, `SF_SCREEN()` is not centered around a specific stock symbol/code but rather a query string that is used to filter our database. Composing the correct query string can be a bit complex, so be sure to use our super handy, in-built stock screener tool. In addition to the query string, you can then specify the metrics you want to display in the output and apply further filtering such as ordering, limiting and more. The function layout is as follows:

```
=SF_SCREEN(query_string, metrics, options)
```

-   `query_string` is the query string you want to use to filter our database. E.g. `"marketcap>1000000000&exchange=NYSE,NASDAQ&sector=Technology"`.
-   `metrics` Use this parameter to select which items you'd like to see in the output. If left blank or as `"all"` then all metrics/columns are returned. You can chain together multiple metrics using the `&` symbol. E.g. `"symbol&sector&industry&exchange&marketCap&price"`.
-   `options` adjusts the formatting of the output. There are a number of available options, such as removal of the header rows (`"NH"`), or ordering of the output (`"ob=beta"`). See the full list of options below on the functions page, [Stock Screener](#/functions/screener).

See more on it's usage in [Stock Screener](#/functions/screener)

---

## [SF\_MAP()](#/functions/availableFunctions?id=sf_map)

The `SF_MAP()` function can be used to map/convert other global identifying codes (e.g. CUSIP numbers) to stock ticker symbols. This can be handy when integrating SheetsFinance with other data sources that rely on alternative ways of identifying a financial product.

```
=SF_MAP(code, type)
```

-   `code` is the code/identifier you want to map to a stock ticker symbol.
-   `type` is the type of code you are mapping, e.g. CUSIP or CIK numbers. Defaults to converting CUSIP codes if this parameter is omitted.

See more on it's usage in [ISIN, CUSIP & CIK Mapper](#/functions/map)

## Embedded Content