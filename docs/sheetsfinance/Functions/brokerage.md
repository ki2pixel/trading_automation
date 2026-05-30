# SheetsFinance Docs | The Brokerage Function

# [The Brokerage Function](#/functions/brokerage?id=the-brokerage-function)

> **🚨 Important:** If you haven't yet connected your brokerage accounts via SheetsFinance then you won't have access to this function, please refer to the [Brokerage](#/use/brokerage) docs page to get started.

The `SF_BROKERAGE()` function is used to pull in real-time data from your connected brokerage accounts. This function is only available to users who have connected their brokerage accounts via SheetsFinance. The function is used to pull in data from your brokerage accounts such as account holdings, balances, options positions, orders, historical transactions, and more.

```
=SF_BROKERAGE(acccount, type, metrics, startDate, endDate, txnType, options)
```

-   `account` is the nickname of the brokerage account connection you want to pull data from. You can find the nickname of your connected brokerage accounts from the Brokerage Sidebar in Google Sheets (`Extensions > SheetsFinance > Brokerage`). You can set custom nicknames for your brokerage accounts, see the [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts) for more information.
-   `type` is the type of data you want to pull in. The available types are:
    -   `"holdings"` - Account holdings/portfolio. Detailed examples under [Brokerage Holdings](#/functions/brokerage-holdings).
    -   `"orders"` - Recent orders. Detailed examples under [Brokerage Recent Orders](#/functions/brokerage-orders).
    -   `"balances"` - Account balances. Detailed examples under [Brokerage Account Balances](#/functions/brokerage-balances).
    -   `"transactions"` - Historical transactions. Detailed examples under [Brokerage Transactions](#/functions/brokerage-transactions).
    -   `"optionsPositions"` - Options positions. Detailed examples under [Brokerage Options Positions](#/functions/brokerage-options).
-   `metrics` selects what data you want to pull in. The available metrics depend on the `type` selected. See the [Metrics](#/functions/brokerage?id=metrics) section below for more information.
-   `startDate` \[OPTIONAL\] is the start date for the data you want to pull in. This is only required for the `"transactions"` type. The date should be in the format `YYYY-MM-DD`.
-   `endDate` \[OPTIONAL\] is the end date for the data you want to pull in. This is only required for the `"transactions"` type. The date should be in the format `YYYY-MM-DD`.
-   `txnType` \[OPTIONAL\] is the type of transactions you want to pull in. This is only required for the `"transactions"` type. The available transaction types are:
    -   `"BUY"` – Asset bought.
    -   `"SELL"` – Asset sold.
    -   `"DIVIDEND"` – Dividend payout.
    -   `"CONTRIBUTION"` – Cash contribution.
    -   `"WITHDRAWAL"` – Cash withdrawal.
    -   `"REI"` – Dividend reinvestment.
    -   `"INTEREST"` – Interest deposited into the account.
    -   `"FEE"` – Fee withdrawn from the account.
    -   `"OPTIONEXPIRATION"` – Option expiration event.
    -   `"OPTIONASSIGNMENT"` – Option assignment event.
    -   `"OPTIONEXERCISE"` – Option exercise event.
    -   `"TRANSFER"` – Transfer of assets from one account to another.
-   `options` adjusts the formatting of the output. There is currently one available option:
    -   `"NH"` - No header row.

## [Metrics](#/functions/brokerage?id=metrics)

The metrics available for each `type` are as follows:

### [Holdings](#/functions/brokerage?id=holdings)

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

### [Orders](#/functions/brokerage?id=orders)

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

### [Balances](#/functions/brokerage?id=balances)

-   `"all"` - All available balance data.
-   `"currency"` - The currency of the balance.
-   `"currencyName"` - The name of the currency.
-   `"cash"` - The cash balance.
-   `"buyingPower"` - The buying power.

### [Transactions](#/functions/brokerage?id=transactions)

-   `"all"` - All available transaction data.
-   `"symbol"` - The symbol of the transaction.
-   `"name"` - The name of the transaction.
-   `"currency"` - The currency of the transaction.
-   `"exchange"` - The exchange the transaction is listed on.
-   `"type"` - The type of transaction.
-   `"amount"` - The amount of the transaction.
-   `"price"` - The price of the transaction.
-   `"units"` - The units of the transaction.
-   `"fee"` - The fee of the transaction.
-   `"fxRate"` - The FX rate of the transaction.
-   `"description"` - The description of the transaction.
-   `"settlementDate"` - The settlement date of the transaction.
-   `"tradeDate"` - The trade date of the transaction.
-   `"institution"` - The institution of the transaction.

### [Options Positions](#/functions/brokerage?id=options-positions)

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

## Embedded Content