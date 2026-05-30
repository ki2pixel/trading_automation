# SheetsFinance Docs | Brokerage Orders

# [Brokerage Recent Orders](#/functions/brokerage-orders?id=brokerage-recent-orders)

> **🚨 Important:** If you haven't yet connected your brokerage accounts via SheetsFinance then you won't have access to this function, please refer to the [Brokerage](#/use/brokerage) docs page to get started.

Access your real-time brokerage account recent orders data directly in Google Sheets using the `SF_BROKERAGE()` function. This function allows you to pull in your recent orders data from your connected brokerage accounts.

```
=SF_BROKERAGE(acccount, "orders", metrics, "", "", "", options)
```

-   `account` is the nickname of the brokerage account connection you want to pull data from. You can find the nickname of your connected brokerage accounts from the Brokerage Sidebar in Google Sheets (`Extensions > SheetsFinance > Brokerage`). You can set custom nicknames for your brokerage accounts, see the [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts) for more information.
-   `type` is the type of data you want to pull in, in this case `"orders"`.
-   `metrics` selects what data you want to pull in. You can leave this blank or set it to `"all"` to output ALL available orders metrics. You can also chain together multiple metrics using the `&` operator, for example `"symbol&name&type&action&executionPrice"`. See the full list of available metrics below.
-   `options` adjusts the formatting of the output. There is currently one available option:
    -   `"NH"` - No header row.

> **🧐 Why are there empty quotes in this function?** The `SF_BROKERAGE()` function is used for a variety of types. The `"transaction"` type has the optional additional arguments `startDate`, `endDate` and `txnType`. In this case of this type, `"orders"` these arguments aren't needed and can be left blank ("")

## [Metrics](#/functions/brokerage-orders?id=metrics)

The metrics available for the `"orders"` type are as follows:

-   `"all"` - All available order data.
-   `"symbol"` - The symbol of the order.
-   `"name"` - The name of the order.
-   `"currency"` - The currency of the order.
-   `"exchange"` - The exchange the order is listed on.
-   `"type"` - The type of order.
-   `"optionSymbol"` - The option symbol of the order.
-   `"action"` - The action of the order.
-   `"totalQuantity"` - The total quantity of the order.
-   `"openQuantity"` - The open quantity of the order.
-   `"canceledQuantity"` - The canceled quantity of the order.
-   `"filledQuantity"` - The filled quantity of the order.
-   `"executionPrice"` - The execution price of the order.
-   `"limitPrice"` - The limit price of the order.
-   `"stopPrice"` - The stop price of the order.
-   `"orderType"` - The type of order.
-   `"timeInForce"` - The time in force of the order.
-   `"timePlaced"` - The time the order was placed.
-   `"timeUpdated"` - The time the order was updated.
-   `"timeExecuted"` - The time the order was executed.
-   `"expiryDate"` - The expiry date of the order.

## [Examples](#/functions/brokerage-orders?id=examples)

> **🤓 Reminder for the below examples:** `"alpaca"` is the nickname of our example brokerage account, you will need to replace this with the nickname of your own brokerage account.

### [Example 1: Pulling in all recent orders data for an account](#/functions/brokerage-orders?id=example-1-pulling-in-all-recent-orders-data-for-an-account)

```
=SF_BROKERAGE("alpaca", "orders")
```

![Brokerage Orders Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-orders_1.png)

### [Example 2: Pulling in specific metrics from your account recent orders](#/functions/brokerage-orders?id=example-2-pulling-in-specific-metrics-from-your-account-recent-orders)

```
=SF_BROKERAGE("alpaca", "orders", "symbol&name&type&action&executionPrice")
```

![Brokerage Orders Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-orders_2.png)

### [Example 3: Pulling in recent orders with no header row](#/functions/brokerage-orders?id=example-3-pulling-in-recent-orders-with-no-header-row)

```
=SF_BROKERAGE("alpaca", "orders", "symbol&name&type&action&executionPrice", "", "", "", "NH")
```

![Brokerage Orders Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/brokerage-orders_3.png)

## Embedded Content