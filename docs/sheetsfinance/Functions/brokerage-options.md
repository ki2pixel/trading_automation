# SheetsFinance Docs | Brokerage Options Positions

# [Brokerage Options Positions](#/functions/brokerage-options?id=brokerage-options-positions)

> **🚨 Important:** If you haven't yet connected your brokerage accounts via SheetsFinance then you won't have access to this function, please refer to the [Brokerage](#/use/brokerage) docs page to get started.

Access your brokerage account options positions data directly in Google Sheets using the `SF_BROKERAGE()` function. This function allows you to pull in your options positions data from your connected brokerage accounts.

```
=SF_BROKERAGE(acccount, "optionsPositions", metrics, "", "", "", options)
```

-   `account` is the nickname of the brokerage account connection you want to pull data from. You can find the nickname of your connected brokerage accounts from the Brokerage Sidebar in Google Sheets (`Extensions > SheetsFinance > Brokerage`). You can set custom nicknames for your brokerage accounts, see the [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts) for more information.
-   `type` is the type of data you want to pull in, in this case `"optionsPositions"`.
-   `metrics` selects what data you want to pull in. You can leave this blank or set it to `"all"` to output ALL available holdings metrics. You can also chain together multiple metrics using the `&` operator, for example `"symbol&name&price&marketValue"`. See the full list of available metrics below.
-   `options` adjusts the formatting of the output. There is currently one available option:
    -   `"NH"` - No header row.

> **🧐 Why are there empty quotes in this function?** The `SF_BROKERAGE()` function is used for a variety of types. The `"transaction"` type has the optional additional arguments `startDate`, `endDate` and `txnType`. In this case of this type, `"optionsPositions"` these arguments aren't needed and can be left blank ("")

## [Metrics](#/functions/brokerage-options?id=metrics)

The metrics available for the `"optionsPositions"` type are as follows:

-   `"all"` - All available options positions data.
-   `"contractSymbol"` - The contract symbol of the options position.
-   `"symbol"` - The symbol of the options position.
-   `"name"` - The name of the options position.
-   `"optionType"` - The option type of the options position.
-   `"strikePrice"` - The strike price of the options position.
-   `"expirationDate"` - The expiration date of the options position.
-   `"optionDescription"` - The option description of the options position.
-   `"currency"` - The currency of the options position.
-   `"exchange"` - The exchange the options position is listed on.
-   `"price"` - The price of the options position.
-   `"units"` - The units of the options position.
-   `"averagePurchasePrice"` - The average purchase price of the options position.

## [Examples](#/functions/brokerage-options?id=examples)

> **🤓 Reminder for the below examples:** `"alpaca"` is the nickname of our example brokerage account, you will need to replace this with the nickname of your own brokerage account.

### [Example 1: Pulling in all options positions data for an account](#/functions/brokerage-options?id=example-1-pulling-in-all-options-positions-data-for-an-account)

```
=SF_BROKERAGE("alpaca", "optionsPositions")
```

### [Example 2: Pulling in specific metrics from your account options positions](#/functions/brokerage-options?id=example-2-pulling-in-specific-metrics-from-your-account-options-positions)

```
=SF_BROKERAGE("alpaca", "optionsPositions", "symbol&name&optionType&strikePrice&expirationDate")
```

#### [Example 3: Pulling in all options positions data for an account with no header row](#/functions/brokerage-options?id=example-3-pulling-in-all-options-positions-data-for-an-account-with-no-header-row)

```
=SF_BROKERAGE("alpaca", "optionsPositions", "all", "", "", "", "NH")
```

## Embedded Content