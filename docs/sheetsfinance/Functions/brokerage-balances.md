# SheetsFinance Docs | Brokerage Balances

# [Brokerage Account Balances](#/functions/brokerage-balances?id=brokerage-account-balances)

> **🚨 Important:** If you haven't yet connected your brokerage accounts via SheetsFinance then you won't have access to this function, please refer to the [Brokerage](#/use/brokerage) docs page to get started.

Access your real-time brokerage account balances data directly in Google Sheets using the `SF_BROKERAGE()` function. This function allows you to pull in your account balances data from your connected brokerage accounts.

```
=SF_BROKERAGE(acccount, "balances", metrics, "", "", "", options)
```

-   `account` is the nickname of the brokerage account connection you want to pull data from. You can find the nickname of your connected brokerage accounts from the Brokerage Sidebar in Google Sheets (`Extensions > SheetsFinance > Brokerage`). You can set custom nicknames for your brokerage accounts, see the [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts) for more information.
-   `type` is the type of data you want to pull in, in this case `"balances"`.
-   `metrics` selects what data you want to pull in. You can leave this blank or set it to `"all"` to output ALL available orders metrics. You can also chain together multiple metrics using the `&` operator, for example `"currency&cash"`. See the full list of available metrics below.
-   `options` adjusts the formatting of the output. There is currently one available option:
    -   `"NH"` - No header row.

> **🧐 Why are there empty quotes in this function?** The `SF_BROKERAGE()` function is used for a variety of types. The `"transaction"` type has the optional additional arguments `startDate`, `endDate` and `txnType`. In this case of this type, `"orders"` these arguments aren't needed and can be left blank ("")

## [Metrics](#/functions/brokerage-balances?id=metrics)

The metrics available for the `"balances"` type are as follows:

-   `"all"` - All available balance data.
-   `"currency"` - The currency of the balance.
-   `"currencyName"` - The name of the currency.
-   `"cash"` - The cash balance.
-   `"buyingPower"` - The buying power.

## [Examples](#/functions/brokerage-balances?id=examples)

### [Example 1: Pulling in all balances data for an account](#/functions/brokerage-balances?id=example-1-pulling-in-all-balances-data-for-an-account)

> **🤓 Reminder for the below examples:** `"alpaca"` is the nickname of our example brokerage account, you will need to replace this with the nickname of your own brokerage account.

```
=SF_BROKERAGE("alpaca", "balances")
```

![Brokerage Balances Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-balances_1.png)

### [Example 2: Pulling in specific metrics from your account balances](#/functions/brokerage-balances?id=example-2-pulling-in-specific-metrics-from-your-account-balances)

```
=SF_BROKERAGE("alpaca", "balances", "currency&cash")
```

![Brokerage Balances Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-balances_2.png)

### [Example 3: Pulling in all balances data for an account with no header row](#/functions/brokerage-balances?id=example-3-pulling-in-all-balances-data-for-an-account-with-no-header-row)

```
=SF_BROKERAGE("alpaca", "balances", "all", "", "", "", "NH")
```

![Brokerage Balances Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-balances_3.png)

## Embedded Content