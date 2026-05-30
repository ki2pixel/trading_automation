# SheetsFinance Docs | Brokerage Holdings

# [Brokerage Holdings](#/functions/brokerage-holdings?id=brokerage-holdings)

> **🚨 Important:** If you haven't yet connected your brokerage accounts via SheetsFinance then you won't have access to this function, please refer to the [Brokerage](#/use/brokerage) docs page to get started.

Access your real-time brokerage account holdings data directly in Google Sheets using the `SF_BROKERAGE()` function. This function allows you to pull in your account holdings/portfolio data from your connected brokerage accounts.

```
=SF_BROKERAGE(acccount, "holdings", metrics, "", "", "", options)
```

-   `account` is the nickname of the brokerage account connection you want to pull data from. You can find the nickname of your connected brokerage accounts from the Brokerage Sidebar in Google Sheets (`Extensions > SheetsFinance > Brokerage`). You can set custom nicknames for your brokerage accounts, see the [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts) for more information.
-   `type` is the type of data you want to pull in, in this case `"holdings"`.
-   `metrics` selects what data you want to pull in. You can leave this blank or set it to `"all"` to output ALL available holdings metrics. You can also chain together multiple metrics using the `&` operator, for example `"symbol&name&price&marketValue"`. See the full list of available metrics below.
-   `options` adjusts the formatting of the output. There is currently one available option:
    -   `"NH"` - No header row.

> **🧐 Why are there empty quotes in this function?** The `SF_BROKERAGE()` function is used for a variety of types. The `"transaction"` type has the optional additional arguments `startDate`, `endDate` and `txnType`. In this case of this type, `"holdings"` these arguments aren't needed and can be left blank ("")

> **🔥 Hot Tip:** `holdings` is the default return of the `SF_BROKERAGE()` function, therefore a shorthand way of returning _all_ holdings for an account is `=SF_BROKERAGE(<account_nickname>)`, for example `=SF_BROKERAGE("vanguard")`.

## [Metrics](#/functions/brokerage-holdings?id=metrics)

The metrics available for the `"holdings"` type are as follows:

-   `"all"` - All available holdings data.
-   `"symbol"` - The symbol of the holding.
-   `"name"` - The name of the holding.
-   `"exchange"` - The exchange the holding is listed on.
-   `"exchangeName"` - The name of the exchange the holding is listed on.
-   `"exchangeTimezone"` - The timezone of the exchange the holding is listed on.
-   `"exchangeOpen"` - The opening time of the exchange the holding is listed on.
-   `"exchangeClose"` - The closing time of the exchange the holding is listed on.
-   `"type"` - The type of holding.
-   `"price"` - The current price of the holding.
-   `"marketValue"` - The market value of the holding.
-   `"totalPL"` - The total profit/loss of the holding.
-   `"totalPLPercent"` - The total profit/loss percentage of the holding.
-   `"units"` - The number of units of the holding.
-   `"averagePurchasePrice"` - The average purchase price of the holding.
-   `"currency"` - The currency of the holding.

## [Examples](#/functions/brokerage-holdings?id=examples)

> **🤓 Reminder for the below examples:** `"alpaca"` is the nickname of our example brokerage account, you will need to replace this with the nickname of your own brokerage account.

### [Example 1: Pulling in all holdings data for an account (your portfolio)](#/functions/brokerage-holdings?id=example-1-pulling-in-all-holdings-data-for-an-account-your-portfolio)

```
=SF_BROKERAGE("alpaca")
```

![Brokerage Holdings Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-holdings_1.png)

### [Example 2: Pulling in specific metrics from your account holdings](#/functions/brokerage-holdings?id=example-2-pulling-in-specific-metrics-from-your-account-holdings)

```
=SF_BROKERAGE("alpaca", "holdings", "symbol&name&price&marketValue")
```

![Brokerage Holdings Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-holdings_2.png)

### [Example 3: Pulling in holdings data with no header row](#/functions/brokerage-holdings?id=example-3-pulling-in-holdings-data-with-no-header-row)

```
=SF_BROKERAGE("alpaca", "holdings", "symbol&name&price&marketValue", "", "", "", "NH")
```

![Brokerage Holdings Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-holdings_3.png)

## Embedded Content