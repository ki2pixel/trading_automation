# [Documentation](https://www.sheetsfinance.com/docs\#/?id=documentation)

Welcome to SheetsFinance! Our add-on connects your Google Sheet or Excel Workbook to tens of thousands of global companies, ETFS, cryptocurrencies, FOREX, mutual funds and much more, allowing you to access crucial real-time and historical financial data. Getting started with our add-on is **super** simple. This page will help you get installed and started, then continue browsing this documentation to learn about all the add-ons great features.

> **"futher setup needed"** -
> If you've landed on this page because your installation of SheetsFinance said you required "further setup" don't panic, there's no further setup needed, you've just been sent here so you can read through our documentation and learn how to get the most out of our extension😁

> **TIPS**:
>
> - There's a handy search bar in the top left corner that can help you navigate our docs straight to the information you're after.
> - We are always available via live chat (see the speech bubble in the bottom right of your screen) or via email at [support@sheetsfinance.com](mailto:support@sheetsfinance.com).

* * *

# [Installation](https://www.sheetsfinance.com/docs\#/?id=installation)

## [Google Sheets](https://www.sheetsfinance.com/docs\#/?id=google-sheets)

### [Option 1 - From Google Sheets](https://www.sheetsfinance.com/docs\#/?id=option-1-from-google-sheets)

1. Open a new [Google Sheet](https://sheets.google.com/)

2. Navigate to the **Extensions** menu and select **Add-ons** from the dropdown, then **Get add-ons** (this will open Google Workspace Marketplace within a pop-up modal)


![Install from Sheets](https://cdn.sheetsfinance.com/public-site/img/docs/install_1.png)

3. Search for **SheetsFinance**
4. Select the **SheetsFinance** add-on and click **Install**

![Install from Sheets](https://cdn.sheetsfinance.com/public-site/img/docs/install_3.png)

5. Refresh your Google Sheet to ensure it's all working correctly

### [Option 2 - From Google Workspace Marketplace](https://www.sheetsfinance.com/docs\#/?id=option-2-from-google-workspace-marketplace)

1. Go to the Google Workspace Marketplace and install our add-on. Here is a direct link:

> [SheetsFinance](http://workspace.google.com/marketplace/app/appname/454765795033)

2. When installing via the Google Workspace Marketplace it is recommended that you open one of the add-on's menu items after install to ensure it has install correctly.

### [Okay it's installed but where is it?](https://www.sheetsfinance.com/docs\#/?id=okay-it39s-installed-but-where-is-it)

Once you've installed the add-on it will be available under the **Extensions** menu as show below:

![Add-on menu](https://cdn.sheetsfinance.com/public-site/img/docs/menu_1.png)

> **Note:** Your 15 day free trial will begin on install and you'll have full access to our data service.

## [Microsoft Excel](https://www.sheetsfinance.com/docs\#/?id=microsoft-excel)

1. Open a new Excel Workbook and click **Add-ins** from the Home ribbon menu.

![Install from Excel](https://cdn.sheetsfinance.com/public-site/img/docs/excel_demo_1.png)

2. Either directly search for **SheetsFinance** or click **More Add-ins** which will open the Office Add-ins store in a pop-up modal. You can then search for **SheetsFinance** there. Then click **Add** to install.

![Install from Excel](https://cdn.sheetsfinance.com/public-site/img/docs/excel_demo_2.png)

3. Once installed successfully you'll see SheetsFinance buttons appear in your Home ribbon and a success message.

![Install from Excel](https://cdn.sheetsfinance.com/public-site/img/docs/excel_demo_3.png)

4. Connect your account by opening the sidebar (1) and entering your Excel Connection ID (2). You can find your Connection ID in your [SheetsFinance Account Dashboard](https://sheetsfinance.com/account). Click **Connect** to login.

![Excel Connection](https://cdn.sheetsfinance.com/public-site/img/docs/excel_demo_4.png)

5. You're all set! You can now start using SheetsFinance in Excel.

![Excel Connection](https://cdn.sheetsfinance.com/public-site/img/docs/excel_demo_5.png)

* * *

# [Quick start](https://www.sheetsfinance.com/docs\#/?id=quick-start)

Using SheetsFinance is as simple as entering the correct formula into a Google Sheets or Excel cell. You can either use our functions directly or use our super handy [Function Generator](https://www.sheetsfinance.com/docs#/use/functionGenerator) to build the functions for you. Examples for both are shown below.

> **🔥 Hot Tip:** If you're just getting started with the SheetsFinance add-on use the in-built Function Generator to make your life much easier. As you get to know our functions you can start directly entering them.

## [Direct Function](https://www.sheetsfinance.com/docs\#/?id=direct-function)

> **Important:** Some regions use semi colons (`;`) instead of commas (`,`) as function separators, if you are getting function errors this may be your problem!

1. Open up a new Google Sheet or Excel Workbook
2. Click on a cell
3. Enter the following:

```excel
=SF("AAPL","realTime","price")
```

Once loaded you should see Apple Inc.'s (AAPL) current price.

Even more simply you can do the following:

```excel
=SF("AAPL")
```

This will also result in Apple Inc.'s (AAPL) current price as the default return of the [SF()](https://www.sheetsfinance.com/docs#/functions/availableFunctions?id=sf) function is the real-time current price of the stock, ETF, cryptocurrency or FOREX rate.

Use our [Symbol Search](https://www.sheetsfinance.com/docs#/use/symbolSearch) to find the correct stock, ETF, FOREX or crypto code.

See [Available Functions](https://www.sheetsfinance.com/docs#/functions/availableFunctions) for details on all available functions.

See [Performance Tips](https://www.sheetsfinance.com/docs#/use/performance-optimisation) for tips on optimising your use of SheetsFinance functions.

## [Function Generator](https://www.sheetsfinance.com/docs\#/?id=function-generator)

1. Enter `AAPL` in cell `A1`.

![Quick start](https://cdn.sheetsfinance.com/public-site/img/docs/quickstart_1.png)

2. Open our [Function Generator](https://www.sheetsfinance.com/docs#/use/functionGenerator) from the add-on drop down in Google Sheets or in Excel, click the main SheetsFinance logo in the ribbon menu.

![Function Generator](https://cdn.sheetsfinance.com/public-site/img/docs/menu_fg_2.png)

3. Fill out the fields in the Function Generator like so:
   - Insert into Cell - `B1` ( **Note:** Leave this blank is totally fine! The formula will instead be inserted into the currently selected cell in Google Sheets or Excel)\]
   - Ticker Cell - `A1`
   - Select `Real-time/Historical`
   - Type - `Real-time`
   - Subtype - `Price`

![Quick start](https://cdn.sheetsfinance.com/public-site/img/docs/quickstart_2.png)

4. Click **Generate**

Once loaded you should see Apple Inc.'s (AAPL) current price in cell `B1`.

![Quick start](https://cdn.sheetsfinance.com/public-site/img/docs/quickstart_3.png)

5. Now type `V` into cell `A2`
6. Drag down the function that was generated in `B1` to cover `B2`

![Quick start](https://cdn.sheetsfinance.com/public-site/img/docs/quickstart_4.png)

Once loaded you should see Visa Inc.'s (V) current price in cell `B2`

![Quick start](https://cdn.sheetsfinance.com/public-site/img/docs/quickstart_5.png)

See [Function Generator](https://www.sheetsfinance.com/docs#/use/functionGenerator) for detailed use.

* * *

# [Limits](https://www.sheetsfinance.com/docs\#/?id=limits)

> **PRO TIPS**
>
> - The best way to manage both rate limits and quotas is to take advantage of our [Realtime Batch](https://www.sheetsfinance.com/docs#/functions/realtimeBatch), [Company Info Batch](https://www.sheetsfinance.com/docs#/functions/companyinfoBatch) and other batch functions. This can significantly reduce your external data usage.
> - Consider purchasing a Google Workspace Account if you intend to use SheetsFinance in Google Sheets for more than 20,000 data calls a day. This will increase your daily Google quota by 5x to 100,000 data calls a day. Note there are some restrictions to when your increased quota is applied, please read [Google's Documentation](https://developers.google.com/apps-script/guides/services/quotas).

## [Quotas](https://www.sheetsfinance.com/docs\#/?id=quotas)

> The following information about quotas only apply to Google Sheets users

We don't have any data quotas! That's right, you have unlimited calls to our external data service through our various functions. **BUT** Google has a hard quota on external requests at 20,000/day. It is important to note that Google's daily quota is for **all Google Sheets activity on your Google account**. Therefore if you use other add-ons in different sheets to access external data this will count toward your overall external data quota.

If you do find that you're regularly hitting Google's limit you could purchase a [Google Workspace Account](https://workspace.google.com/intl/en_au/) which will increase your daily limit to **100,000/day** (5x increase). This is a good move if you intend to use SheetsFinance to pull large quantities of data daily! It is important to note that to receive the increased quota for your Workspace account you must:

1. Have cumulatively paid at least USD $100 (or equivalent) on the registered Workspace domain, and;
2. Have at least 60 days elapse since reaching the above payment threshold.

You can read more on Google quotas [here](https://developers.google.com/apps-script/guides/services/quotas).

## [Rate Limits](https://www.sheetsfinance.com/docs\#/?id=rate-limits)

Our external data service, like most, is rate limited to protect it from abuse. This means that if you attempt to run 100s of simultaneous functions you may find you hit a rate limit error. We have done our best to efficiently cache non-realtime data and throttle out-going requests but from time-to-time you may over-do it. Don't panic. Just wait a few seconds and re-generate the formula.

**Note:** If you're still seeing the error be sure you've entirely deleted the formula and then re-entered it. If you continue to have problems please [contact us](https://sheetsfinance.com/support/contact).

As always, please access our data in a smart and respectable way. Any abuse of our external data service will result in subscription suspension and potential termination.