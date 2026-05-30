# SheetsFinance Docs | Historical Market Cap

# [Historical Market Capitalisation](#/functions/historicalMarketCap?id=historical-market-capitalisation)

The historical market capitalisation for a company can be access in 2 ways. You can either retrieve a single date in history which is done through using the `"historicals"` data type or you can return an entire time-series between 2 dates by using the `SF_TECHNICAL()` function. Both are shown below:

## [Historical Market Cap - Single Date](#/functions/historicalMarketCap?id=historical-market-cap-single-date)

```
=SF("AAPL", "historical", "marketCap", "2001-07-24")

6834000000
```

## [Historical Market Cap - Time-series](#/functions/historicalMarketCap?id=historical-market-cap-time-series)

```
=SF_TECHNICAL("AAPL", "marketCap&all", "", "2015-07-24", "2022-11-29")

[multi-cell array]
```

> **NOTE:** All the same functionality of `SF_TECHNICAL()` is available such as formatting the output with options or only displaying certain metrics. The only available metrics for `marketCap` are `marketCap` and `date`. Read more on [SF\_TECHNICAL()](#/functions/technicals).

![Historical Market Cap Example](https://cdn.sheetsfinance.com/public-site/img/docs/historicalMarketCap.png "Historical Market Cap Example")

## Embedded Content