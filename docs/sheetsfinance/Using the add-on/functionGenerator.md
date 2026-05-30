# SheetsFinance Docs | Function Generator

# [Function Generator](#/use/functionGenerator?id=function-generator)

The **Function Generator** is what makes SheetsFinance so easy to use! It automatically builds and generates all our functions for you. Not only that, but you can use it to search through the vast amount of financial data available on SheetsFinance. The **Function Generator** opens as a sidebar in Google Sheets and is accessed via the 'Extensions' menu (_**Extensions > SheetsFinance > Function Generator**_). Once you've chosen all the parameters click **Generate** and the function will be automatically inserted into your Sheet for you 🚀

![](https://cdn.sheetsfinance.com/public-site/img/docs/functionGenerator.png)

> **HOT TIP:** The Function Generator will display the function you are building in real-time. You can use this to learn about how SheetsFinance functions are designed.

## [Where do I find the Function Generator?](#/use/functionGenerator?id=where-do-i-find-the-function-generator)

Both the Function Generator and the Symbol Search can be opened via the 'Extensions' dropdown menu in Google Sheets (Extensions > SheetsFinance > Function Generator), see the below image:  
![](https://cdn.sheetsfinance.com/public-site/img/docs/menu_fg_2.png)

## [How to use the Function Generator?](#/use/functionGenerator?id=how-to-use-the-function-generator)

1.  Open the Function Generator from the 'Extensions' dropdown menu.
2.  Enter either the stock you want to search (e.g. `"AAPL"`), the cell containing the stock code (e.g. `A1`) or a range of cells if it's a batch function (e.g. `A1:A21`).

![Enter Stock Code](https://cdn.sheetsfinance.com/public-site/img/docs/fg_enter_stock_code.png "Enter Stock Code")

or

![Enter Stock Cell](https://cdn.sheetsfinance.com/public-site/img/docs/fg_enter_cell.png "Enter Stock Cell")

3.  Select the base function type. These represent all the [Available Functions](#/functions/availableFunctions), for example, Real-time/historical data (`=SF()`) or Dividends (`=SF_DIVIDEND()`).

![Select Base Function](https://cdn.sheetsfinance.com/public-site/img/docs/fg_select_base_function.png "Select Base Function")

4.  Complete the rest of the input options depending on the data you are after. In this example we are after the real-time price change of `"AAPL"` as a percentage.

![](https://cdn.sheetsfinance.com/public-site/img/docs/fg_completed.png)

5.  Click **Generate** and the function will populate whichever cell you are actively highlighting in Google Sheets. You can optionally specify which cell you'd like to insert the function into by writing it in the `Insert` input box.

## Embedded Content