# SheetsFinance Docs | Brokerage

# [Brokerage](#/use/brokerage?id=brokerage)

SheetsFinance Brokerage allows you to securely connect all your brokerage accounts to Google Sheets and Excel. The connection enables you to pull in your real-time holdings, recent orders, transaction history, account balances and options positions directly into your spreadsheet. Please check our list of [supported brokers](#/use/brokerage?id=supported-brokers) to see if your brokerage account is available.

This docs page will guide you through enabling brokerage and connecting your accounts. Once connected you will be able to use the function `=SF_BROKERAGE()` in your brokerage-enabled spreadsheets. For all the details on how to use the `SF_BROKERAGE()` function to generate your real-time data, please refer to the [Brokerage Function](#/functions/brokerage) page.

On this page:

-   [Supported Brokers](#/use/brokerage?id=supported-brokers)
-   [Connecting Your Brokerage Account](#/use/brokerage?id=connecting-your-brokerage-account) (a step-by-step guide)
-   [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts)
-   [Disconnecting a Brokerage Account](#/use/brokerage?id=disconnecting-a-brokerage-account)
-   [Privacy and Security](#/use/brokerage?id=privacy-and-security)

## [Supported Brokers](#/use/brokerage?id=supported-brokers)

SheetsFinance has a growing list of supported brokers. Below you can see a list of which brokers are currently supported and for each broker detail on:

-   The asset classes supported for holdings and recent orders data.
-   The maximum data delay from your brokerage account to Google Sheets and Excel.

> **⏳ 24hr Delays:** Some brokers may have a 24hr delay on their data. This means that the data is updated once per day from the brokerage account to Google Sheets and Excel. This is due to the brokerage provider's data policy and is not controlled by SheetsFinance.

> **⚠️ Available Soon:** Some brokers are currently in the process of being integrated. If you would like to be notified when they are available, please contact us.

Logo

Name

Holdings Asset Classes

Recent Order Asset Classes

Transaction Types

Transaction History

Min Delay

![Alpaca](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/alpaca-logo-square.webp)

Alpaca

ADR Crypto ETF Option Stock

ADR Crypto ETF Option Stock

Buy/Sell Dividend Deposit/Withdraw Fee Option Events

All

20s

![Binance](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/binance-logo-square.webp)

Binance

Crypto

Not Available

Dividend Deposit/Withdraw Buy/Sell

All

90s

![Bux](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/bux-square-logo.webp)

Bux

ADR ETF Stock

Not Available

Not Available

30s

![Chase](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/chase-logo.webp)

Chase

ETF Mutual Fund Stock

ETF Mutual Fund Stock

Buy/Sell Deposit/Withdraw Reinvestment

Last 2 years

2hrs

![Coinbase](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/coinbase-logo-square.webp)

Coinbase

Crypto

Not Available

Buy/Sell Deposit/Withdraw

All

90s

![CommSec](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/commsec-logo-square.webp)

CommSec

ADR ETF Stock

Not Available

Not Available

30s

![Degiro](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/degiro_logo.jpeg)

Degiro

ADR ETF Stock

ADR ETF Stock

Buy/Sell Dividend Deposit/Withdraw Fee

All

60s

![E*Trade](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/etrade-logo-square.webp)

E\*Trade

ADR ETF Option Stock

ADR ETF Option Stock

Buy/Sell Deposit/Withdraw Dividend Fee

Last 2 years

30s

![Empower](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/empower-logo.webp)

Empower

Mutual Fund

Not Available

Not Available

2hrs

![Fidelity](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/fidelity_logo.webp)

Fidelity

ADR ETF Fixed Income Mutual Fund Option Stock

ADR ETF Fixed Income Mutual Fund Option Stock

Buy/Sell Deposit/Withdraw Dividend Reinvestment Option Events

Last 2 years

2hrs

![Interactive Brokers](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/ibrk-logo.webp)

Interactive Brokers

ADR ETF Fixed Income Mutual Fund Option Stock

ADR ETF Fixed Income Mutual Fund Stock

Not Available

24hrs

![Kraken](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/kraken-logo.webp)

Kraken

Crypto

Not Available

Buy/Sell Deposit/Withdraw Fee

All

90s

![Public](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/public-logo-square.webp)

Public

Crypto ETF Fixed Income Mutual Fund Option Stock

Not Available

Buy/Sell Dividend Deposit/Withdraw Fee Interest Adjustment Transfer

All

30s

![Questrade](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/questrade-logo-square.webp)

Questrade

ETF Stock

ETF Stock

Buy/Sell Dividend Deposit/Withdraw Fee

All

24hrs

![Robinhood](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/robinhood-logo-square.webp)

Robinhood

ADR Crypto ETF Option Stock

ADR Crypto ETF Option Stock

Buy/Sell Dividend Deposit/Withdraw Option Events

All

30s

![Schwab](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/schwab-logo-square.webp)

Schwab

ADR ETF Mutual Fund Option Stock

ADR ETF Mutual Fund Option Stock

Buy/Sell Dividend

Last 2 years

Real-time

![Stake Australia](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/stake-logo-square.webp)

Stake Australia

ADR ETF Stock

ADR ETF Stock

Buy/Sell Dividend Deposit/Withdraw

All

30s

![tastytrade](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/tasty.avif)

tastytrade

stock option ETF Crypto

stock option ETF Crypto

Buy/Sell Deposit/Withdraw Dividend

All

30s

![TradeStation](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/tradestation-logo-square.webp)

TradeStation

ADR ETF Option Stock

ADR ETF Stock

Not Available

30s

![Tradier](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/tradier-logo-square.webp)

Tradier

ADR ETF Option Stock

ADR ETF Stock

Buy/Sell Dividend Deposit/Withdraw

All

5mins

![Trading212](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/trading212-logo-square.webp)

Trading212

ETF Stock

ETF Stock

Buy/Sell Deposit/Withdraw Dividend Fee

All

5mins

![Unocoin ](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/unocoin_logo.webp)

Unocoin

Crypto

Crypto

Buy/Sell Deposit/Withdraw Fee

All

30s

![Upstox](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/upstox_logo.webp)

Upstox

ETF Stock

Not Available

Not Available

60s

![Vanguard US](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/vanguard-square-logo.webp)

Vanguard US

ADR ETF Mutual Fund Stock

ETF Stock

Buy/Sell Dividend Deposit/Withdraw

All

24hrs

![Wealthsimple](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/wealthsimple-trade-logo-square.webp)

Wealthsimple

ADR Crypto ETF Fixed Income Mutual Fund Stock

ADR Crypto ETF Fixed Income Option Stock

Buy/Sell Dividend Deposit/Withdraw Option Events

Since April 2023

30s

![Webull Canada ](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/webull-logo.webp)

Webull Canada

ETF Stock

ETF Stock

Not Available

24hrs

![Webull US](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/webull-logo-us-square.webp)

Webull US

ADR ETF Option Stock

ADR ETF Stock

Buy/Sell Dividend Deposit/Withdraw

All

24hrs

![Wells Fargo](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/Wells_Fargo_Logo.webp)

Wells Fargo

Stock

Not Available

Not Available

2hrs

![Zerodha](https://cdn.sheetsfinance.com/public-site/img/docs/brokers/zerodha-logo-square.webp)

Zerodha

ADR ETF Stock

Not Available

Buy/Sell

All

30s

## [Connecting Your Brokerage Account](#/use/brokerage?id=connecting-your-brokerage-account)

To connect your brokerage account, follow these steps:

1.  Purchase your SheetsFinance brokerage subscription.
2.  Connect your brokerage account(s) to SheetsFinance.
3.  Open Google Sheets or Excel and connect to SheetsFinance.
4.  Enable brokerage in your spreadsheet (only required for Google Sheets).
5.  Start using the `SF_BROKERAGE()` function to pull in your real-time data.

### [1\. Purchase Your SheetsFinance Brokerage Subscription](#/use/brokerage?id=_1-purchase-your-sheetsfinance-brokerage-subscription)

Brokerage is a separate subscription to our SheetsFinance Data subscription. You can purchase a brokerage subscription with or without a SheetsFinance Data subscription. Monthly and Annual brokerage subscription options are available on our [Pricing](https://sheetsfinance.com/pricing?group=brokerage) page.

### [2\. Connect Your Brokerage Account(s) to SheetsFinance](#/use/brokerage?id=_2-connect-your-brokerage-accounts-to-sheetsfinance)

Once you have purchased your brokerage subscription, you will need to connect your brokerage account(s) to SheetsFinance. To do this, follow these steps:

1.  Head to your [Account Dashboard](https://sheetsfinance.com/account) on the SheetsFinance website.
2.  Navigate to the [Brokerage](https://sheetsfinance.com/account?tab=brokerage) tab.
3.  Click on the 'Connect' button in the "Create New Connection" section.
4.  Follow the secure on-boarding flow by selecting the institution you want to connect and entering your login credentials. You may be navitgated to the institution's website to complete the connection.
5.  Once connected, you will see your brokerage account(s) listed in the "Connected Brokerage Accounts" section.

### [3\. Open Google Sheets or Excel and Connect to SheetsFinance](#/use/brokerage?id=_3-open-google-sheets-or-excel-and-connect-to-sheetsfinance)

#### [Already have a SheetsFinance Data Subscription?](#/use/brokerage?id=already-have-a-sheetsfinance-data-subscription)

If you already have an active SheetsFinance Data subscription just ensure that your Google Sheets or Excel environment has the latest account data.

**Google Sheets**

You can do this in Google Sheets by opening your Account Modal by clicking `Account` from the dropdown menu in Google Sheets (`Extensions > SheetsFinance > Account`). You should see your new Brokerage subscription displayed. If you still don't see your new brokerage plan, try running `Sync`, also available from the dropdown menu in Google Sheets (`Extensions > SheetsFinance > Tools > Sync`).

**Microsoft Excel**

In Excel, open your Account Modal by clicking the **Account** button in the ribbon menu and then **Manage Account**. This will open a pop-up modal where you can enter your unique excel Connection ID found in your account dashboard on our website. Entering this Connection ID will sync your account data.

If you still don't see your new brokerage plan in Excel, try instead navigating to the account section of the sidebar. Open the sidebar by clicking the main SheetsFinance button in the ribbon menu, then open the dropdown menu by clicking the three parallel lines top left. Click **Account** and then click the small refresh icon at the top right of the account card.

#### [First time connecting to SheetsFinance?](#/use/brokerage?id=first-time-connecting-to-sheetsfinance)

If you've either purchased the stand-alone brokerage subscription or added brokerage to a new data subscription, you will need to connect to SheetsFinance. To do this you can either:

**Google Sheets**

1.  **Open Google Sheets with the same account email you used to sign-up for SheetsFinance:** Your account will auto-recognise your connection.
2.  **Open Google Sheets with any account:** Install SheetsFinance and then connect to your SheetsFinance account by clicking `Account` from the dropdown menu in Google Sheets (`Extensions > SheetsFinance > Account`). From there you can click 'Change Connection' where you can enter your SheetsFinance `Connection ID` provided on your [Account Dashboard](https://sheetsfinance.com/account).

> 🤨 **Confused about the difference between your SheetsFinance and Google accounts?** More details on the differences can be found under [Account and Pricing](#/use/account-and-pricing) in our docs.

**Microsoft Excel**

1.  Open Excel and install SheetsFinance from the Office Add-ins store.
2.  Click the **Account** button in the ribbon menu and then **Manage Account**.
3.  This will open a pop-up modal where you can enter your unique excel Connection ID found in your account dashboard on our website.
4.  Entering this Connection ID will connect your Excel environment to your SheetsFinance account.

### [4\. Enable Brokerage in Your Spreadsheet (Google Sheets Only)](#/use/brokerage?id=_4-enable-brokerage-in-your-spreadsheet-google-sheets-only)

Due to the sensitive nature of brokerage data and the ability for users to share their spreadsheets on Google Sheets with others, brokerage data is not enabled by default. Brokerage data must be enabled in each spreadsheet you wish to use it in and can be disabled at any time. This can only be done by the owner of the spreadsheet. To enable brokerage in your spreadsheet, follow these steps:

1.  Open the spreadsheet you want to enable brokerage in.
2.  Open the Brokerage Sidebar by clicking `Brokerage` from the dropdown menu in Google Sheets (`Extensions > SheetsFinance > Brokerage`).
3.  Tick the `Enable Brokerage for this document` checkbox.

### [5\. Start Using the `SF_BROKERAGE()` Function](#/use/brokerage?id=_5-start-using-the-sf_brokerage-function)

Now that you have successfully connected your brokerage account(s) to SheetsFinance and enabled brokerage in your spreadsheet, you can start using the `SF_BROKERAGE()` function to pull in your real-time data. For all the details on how to use the `SF_BROKERAGE()` function to generate your real-time data, please refer to the [Brokerage Function](#/functions/brokerage) page.

**Important:** To reference the correct brokerage account you must use the nickname you set for your brokerage account(s). You can find this nickname in the Brokerage Sidebar in italics under the brokerage account's institution name. You can also set a custom nickname for your brokerage account(s) in Google Sheets and Excel. For more information on setting nicknames for your brokerage accounts, please refer to the [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts) section below.

## [Setting Nicknames for Your Brokerage Accounts](#/use/brokerage?id=setting-nicknames-for-your-brokerage-accounts)

SheetsFinance uses settable nicknames to identify your brokerage accounts. These nicknames are used in the `SF_BROKERAGE()` function to pull in your real-time data. By default, SheetsFinance will use the institution name of your brokerage account as the nickname. If you would like to set a custom nickname for your brokerage account(s) you can do so within Google Sheets or Excel by following these steps:

1.  Open the Brokerage Sidebar by clicking `Brokerage` from the dropdown menu in Google Sheets (`Extensions > SheetsFinance > Brokerage`). Or in Excel, open the sidebar by clicking the main SheetsFinance button in the ribbon menu, then open the dropdown menu by clicking the three parallel lines top left. Click **Brokerage**.
2.  Click on the small pencil icon on the top right of the brokerage account card you would like to set a nickname for.
3.  Enter your desired nickname and click `Save`.
4.  You can now use this nickname in the `SF_BROKERAGE()` function to pull in your real-time data.

## [Disconnecting a Brokerage Account](#/use/brokerage?id=disconnecting-a-brokerage-account)

Removing your SheetsFinance brokerage subscription will automatically disconnect all your brokerage accounts.

If you would like to disconnect a single brokerage account whilst maintaining your SheetsFinance Brokerage subscription, you can do so by following these steps:

1.  Head to your [Account Dashboard](https://sheetsfinance.com/account) on the SheetsFinance website.
2.  Navigate to the [Brokerage](https://sheetsfinance.com/account?tab=brokerage) tab.
3.  Click on the small `X` icon on the right of the brokerage account card you would like to disconnect.
4.  Confirm the disconnection by clicking `Remove` when prompted.

## [Privacy and Security](#/use/brokerage?id=privacy-and-security)

We take the security and privacy of your data very seriously.There are two classes of data associated with your brokerage subscription:

1.  **Brokerage Data**: This is the data that is pulled in from your brokerage account(s) into Google Sheets and/or Excel.
2.  **Brokerage Credentials**: Randomised tokens that are used to authenticate your brokerage account(s) with SheetsFinance.

SheetsFinance does the following to ensure the security of your data:

1.  **User data belongs to the user**: Your brokerage data is your own, we do not touch it without your explicit permission. Only you have access to your brokerage data.
2.  **No Long-term Brokerage Data Storage**: We do not store any of your brokerage data in databases on our servers. The only storage medium is temporary caching in-memory whilst actively using the data in Google Sheets and/or Excel, this is to ensure best performance.
3.  **Encrypted Brokerage Credentials**: Your brokerage credentials are encrypted, stored securely and regularly rotated. Your brokerage credentials are only valid for the server-to-server connection between SheetsFinance and brokerage providers and are useless outside of this context.
4.  **Complete Disconnection**: If you remove a brokerage connection or your entire brokerage subscription, all brokerage credentials become invalid for future use. Entirely new credentials are generated if you reconnect your brokerage account(s).
5.  **Read-Only Access**: SheetsFinance has read-only access to your brokerage data. We do not have the ability to execute trades or make any changes to your brokerage account(s).

For further information please refer to the security documents of our brokerage connection provider [SnapTrade](https://snaptrade.com/security).

## Embedded Content