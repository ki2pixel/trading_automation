# [Templates](https://www.sheetsfinance.com/docs\#/templates?id=templates)

🚨 You can now access our entire library of templates on our brand new [Templates Page](https://www.sheetsfinance.com/templates). This docs page will stay here for legacy reasons but we recommend you check out the new page for a much larger selection of SheetsFinance and community-built spreadsheet templates.

We've built a series of custom Google Sheets templates to get you started with SheetsFinance. To use them all you need to do is install our add-on and then **click the link below** which will take you to a read-only Google Sheet. Once there click `File` \> `Make a copy` to create your own version and off you go!

> [Pre-built Templates v2.1](https://docs.google.com/spreadsheets/d/1PqqfgUCJJsKpBBTHGptAlD6P03su1qJhCQK-1gDzfDs)

The templates are ready to go immediately but should be used as a guide to show you what's possible with SheetsFinance. Once you get confident using our formulas and the Function Generator get creative and edit/extend them to suit your needs! Remember, if you have any troubles using the templates or you've designed something new and want to share it with us please reach out via our [contact page](https://www.sheetsfinance.com/support/contact) or on our website's live chat.

For older versions of our templates please see our [list of versions](https://www.sheetsfinance.com/docs#/templates?id=list-of-versions)

> **IMPORTANT DISCLAIMER:** These templates are provided 'as is', solely for informational purposes and in no way constitue financial advice. This is particularly relavent for the scoring methodology used in Template 1 - Growth Analysis which is entirely informational and in no way confirms the future stock price or success of a company. This scoring system only rates the company's _historical_ performance and should not be used as a basis for any investing decisions.

* * *

### [Template 1a - Growth Analysis](https://www.sheetsfinance.com/docs\#/templates?id=template-1a-growth-analysis)

The growth analysis template is a 10 year snapshot of a company's performance with particular focus on 4 key growth rates: book value per share (BVPS), earnings per share (EPS), sales per share (SPS) and operating cash flow per share (OCFPS). This template is in a dashboard format and **only requires changing the company ticker code in cell `A1`** for the whole sheet to reload with information about the new company. This template can be used for developing a fundamental analysis of a company's historical performance taken directly from their reported financials. The template includes:

- Real-time information
- Visual graphing of growth rates over the last 10 years
- Simplified scoring on growth metrics as a way of judging/evaluating the company's historical performance
- Detailed financials on key metrics

> **IMPORTANT:** This analysis is only relevant for companies. Inputting cryptocurrencies, FOREX ratios or ETFs into the `A1` cell will result in errors.

![Growth Analysis](https://cdn.sheetsfinance.com/public-site/img/docs/templates_growth_analysis.png)

### [Template 1b - MOS Valuation](https://www.sheetsfinance.com/docs\#/templates?id=template-1b-mos-valuation)

> **IMPORTANT:**
>
> - This template will automatically calculate once opened based on whichever company you have entered into `A1` of the growth analysis template (1a).
> - Do not edit any coloured cells, only white cells should be used to adjust the valuation.
> - This valuation methodology is built for profitable companies that have been publicly listed on an exchange for at least 10 years. **Do not attempt to use this to value non-profitable companies or speculative penny stocks**.

The Margin of Safety (MOS) valuation template builds off the growth analysis template (1a) and conducts an automatic valuation of the company you're currently viewing. The valuation utilises the growth rates calculated in the growth analysis and forecasts the estimated growth in a company's value over a specified number of years. Based on the estimated future value of the company, the valuation calculates the buy price required to generate the selected yearly return (MAAR %). The MOS valuation applies a user specified margin of safety to the calculated buy price.

**Using the MOS valuation sheet**

1. Select a company to value by entering it into cell `A1` of the Growth Analysis (1a).
2. Change to the MOS Valuation (1b) sheet.
3. Select the `Safety Margin`. This is the additional safety margin you'd like to apply to the valuation's result. It is recommended to use 50% for this.
4. Select the `MAAR`. This is the yearly return you want to earn from this investment. It is recommended to use 10-15% for this.
5. Select the `Historical Growth`. This chooses which growth rates from the Growth Analysis (1a) to use for the MOS valuation.
6. Select the `Forecast Length`. This specifies how many years forward you'd like to estimate the future value of the company.
7. Decide whether you'd like to adjust the calculated `Future P/E` or `Growth Rate` by entering your own figures into the `Future P/E Adj.` and the `Growth Rate Adj.` To use the automatically calculated values select `OFF`.
8. At the top left of the sheet you will now see the `Buy Price` calculated. The `Fair Value` is the buy price without the safety margin applied.

The valuation is conducted automatically but we've laied out the numbers down the left-hand side of the sheet. If you're interested in understanding the methodology please continue reading below the following image.

![MOS Valuation Template](https://cdn.sheetsfinance.com/public-site/img/docs/valuation_template.png)

**How the automatic valuation method works:**

1. Calculate the average growth rate of the company over the last X years (X defined by ‘Historical Growth’). These numbers come from the Growth Analysis sheet (1a).
2. Apply this average growth rate (compounding) to the current EPS of the company over Y years (Y defined by ‘Forecast Length’) to estimate the future earnings of the company.
3. Estimate the P/E of the company Y years from now, assuming you choose to sell in a bull/greedy market (as you should) you should choose the highest of your P/E estimates.
4. Calculate the estimated stock price at this future date (Y years from now) by multiplying the future P/E by the future EPS.
5. Decide the annual returns you’d like to generate from your investment (MAAR), e.g. 15% returns year-on-year.
6. Reverse compound the estimate stock price Y years from now by your MAAR to get a current day fair purchase value for the company. This is the price you are willing to pay today to earn your MAAR % on the investment for Y years.
7. Apply a margin of safety % to this final price, e.g. I want to purchase the stock at 50% below the fair value estimate.
8. You now have your buy price.

* * *

### [Template 2 - Watchlist](https://www.sheetsfinance.com/docs\#/templates?id=template-2-watchlist)

The watchlist template is a simple real-time watchlist for any of our stocks, ETFs, cryptocurrencies or FOREX ratios. You can use this template to easily track any investment option in real-time. Conditional formatting helps signify if the stock is up or down for the day or whether the daily volume has exceeded the average volume. This template is very simple and readily extendible so have an explore of what other data you'd like to display and add it on!

> **SUGGESTION:** You can use Refresh Real-time (Add-ons > SheetsFinance > Refresh > Refresh Real-time) to force reload your watchlist to get the most up-to-date information.

![Watchlist](https://cdn.sheetsfinance.com/public-site/img/docs/templates_watchlist.png)

* * *

### [Template 3 - Investing Portfolio](https://www.sheetsfinance.com/docs\#/templates?id=template-3-investing-portfolio)

The portfolio template is a designed for keeping tabs on your active investment portfolio. This template only relies on you entering your investment purchases or sales in the `Order List` section and the **rest is managed for you**. The template will automatically keep track of your total invested units and let you know whether you are overall at a profit or loss. The pie charts give you a simplified overview of your portfolio breakdown by item, sector and exchange. The `Details` section gives you a snapshot of the company or coin's key metrics such as EPS (ttm), P/E ratio, market cap and so on... The `All time position` section keeps track of all your historical investments, even once fully sold out of a position, so that you can keep track of your overall performance. If you want to use this template as is then **do not edit the greyed out cells**, these will update automatically when you enter your order infofrmation in the `Order List`.

> **IMPORTANT:** Once the sum of units of a particular stock or coin fall to 0 in the Order List (i.e. you have sold all your remaining units) the stock or coin will be automatically removed from your portfolio. Therefore, **any profit or loss associated with this stock or coin will no longer be reported in your total profit/loss figure**.

![Portfolio](https://cdn.sheetsfinance.com/public-site/img/docs/templates_portfolio2.png)

* * *

## [List of Versions](https://www.sheetsfinance.com/docs\#/templates?id=list-of-versions)

- [Pre-built Templates v2.1](https://docs.google.com/spreadsheets/d/1PqqfgUCJJsKpBBTHGptAlD6P03su1qJhCQK-1gDzfDs) (September 2023)
- [Pre-built Templates v2](https://docs.google.com/spreadsheets/d/11OQOdwz2pX5eGnZTye7wmGONNkKEeLIeIg7mt7eAMEU/) (June 2021)
- [Pre-built Templates v1](https://docs.google.com/spreadsheets/d/1Dd7ioYVGxTvxGVWAuN9UXXkXoJGs-SQZHIXGncPEPCw) (November 2021)