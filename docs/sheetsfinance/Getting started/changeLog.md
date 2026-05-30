# [Change Log](https://www.sheetsfinance.com/docs\#/changeLog?id=change-log)

* * *

## [v4.1.0 google sheets v1.1.6 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v410-google-sheets-v116-excel)

`Released: 9 April 2026`

- NEW RELEASE Options package.
- NEW `SF_OPTIONS_PRO()` function for professional options analytics.
- Full OPRA chains with greeks, bid/ask, volume, open interest, and direct contract lookups.
- 20+ years of historical options data including historical chains and contract/strike time-series.
- New implied volatility analytics including IV periods, IV Rank, IV Rank batch, and historical time-series workflows.
- New full volatility surface and surface forecast datasets.
- New options-derived earnings analytics including implied move, straddle %, and earnings effect.
- `SF_BROKERAGE()` added to Function Generator.
- `SF_OPTIONS_PRO()` added to Function Generator.

## [v4.0.6 google sheets v1.0.5 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v406-google-sheets-v105-excel)

`Released: 3 April 2026`

- Schwab brokerage connections now refresh at real-time rates rather than 24 hours.
- Schwab brokerage connections extended orders window from 2 to 30 days.

## [v4.0.5 google sheets v1.0.4 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v405-google-sheets-v104-excel)

`Released: 16 March 2026`

- Reduction in latency on real-time exchange quotes.
- Fix `symbol` display for brokerage transactions where the item is an option rather than an equity.
- Fix to technicals caching for ADX indicator to improve update speeds.
- Rename tier "Solo" to "Pro".

## [v4.0.4 google sheets v1.0.3 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v404-google-sheets-v103-excel)

`Released: 19 February 2026`

- Fix for `exchange` display for brokerage options positions.
- Fix for `calYear` option for quarterly statements to correctly sort by calendar year rather than company financial year.
- Fix intra-day times-series caching bug to improve update speeds.

## [v4.0.3 google sheets v1.0.2 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v403-google-sheets-v102-excel)

`Released: 9 February 2026`

- Added new dividend adjusted time-series period `"dailyAdj"` to `SF_TIMESERIES()` function. Includes entire OHLC data adjusted for dividends.
- Removed `adjClose` from regular daily time-series.

## [v4.0.2 google sheets v1.0.1 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v402-google-sheets-v101-excel)

`Released: 1 February 2026`

- Fixed filter counter for screener, repeated filters with different conditions only counted once, e.g. `"marketCap>1000000&marketCap<5000000"` now counts as 1 filter not 2.
- Added `"decimal"` option to `"change"` data type to return change as a decimal rather than percentage.
- Fixed bug impacting daily time-series update speeds.
- Upped TTM Ratios batching limit to 500 for business plans.

## [v1.0.0 excel](https://www.sheetsfinance.com/docs\#/changeLog?id=v100-excel)

`Released: 18 January 2026`

- SheetsFinance released on the Microsoft Marketplace for Microsoft Excel 🎉
- The following differences exist currently between the Google Sheets and Microsoft Excel versions of SheetsFinance:
  - No Template Library in Excel version (coming soon)
  - No Options data in Excel version (coming soon)
  - Excel provides an option to display all errors as text in-cell for clarity
  - Excel caching and performance are sigificantly more powerful due to the nature of the platform

## [v4.0.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v401-google-sheets)

`Released: 11 January 2026`

- Empower and Chase added as supported brokers for SheetsFinance Brokerage.
- Fidelity refresh delay reduced to 2 hours.
- Tastytrade added support for crypto assets.
- General bug fixing and improvements to brokerage connections.
- Bug impacting `volume` metric display for screener fixed.

## [v4.0.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v400-google-sheets)

`Released: 14 November 2025`

- NEW statement functions `income`, `balancesheet` and `cashflow` with new line items and significantly improved consolidation and standardisation. Deprecated statement functions to remain active for backward compatibility, see [Historical Financial Statements (Deprecated)](https://www.sheetsfinance.com/docs#/functions/historicalFinancials) for old documentation.
- NEW `ipos` added as Financial Calendar type for upcoming and historical IPOs.
- NEW option `calYear` for statements, growth, ratios, revenue segmentation and others allowing search by calendar year rather than company financial year.
- NEW option `pad` for statements, growth, ratios, revenue segmentation and others to left and/ore right pad output data with blank columns for missing periods to maintain consistent output between companies.
- NEW option `includeWeekends` for `historical` function to include weekend dates when pulling data for crypto and forex/commodities.
- Metrics added to stock screener: `ipoDate`, `avgVolume` and `price`. All included as basic filters and allowing sorting.
- Metrics added to `dividends` Financial Calendar: `frequency` and `yield`.
- Metric added to `prePostMarket`: `volume`.
- Metric added to `insiders`: `directOrIndirect`.
- Metrics added to `peers`: `name`, `price` and `marketCap`.
- Metric added to `SF_NEWS()`: `publisher`.
- Statement functions now support a range of years for TTM data to output TTM data per quarter side-by-side for multiple years. E.g., `SF("AAPL", "incomeTTM", "all", "2019-2022")` will return TTM income statements for each quarter from 2019 to 2022.
- Statement functions support sorting by `YYYY-MM` for quarterly data when using `calYear` option. E.g. `SF("AAPL", "incomeQ", "all", "2022-09", "calYear")` will return the quarterly statement released in September 2022.
- `estimates` now defaults to next/upcoming year when year parameter is omitted.
- `priceTargets` functions now accepts `YYYY`, `YYYY-MM` and `YYYY-MM-DD` formats for date parameter not just `lastXMonths`.
- `insiderStats` name changes for clarity. Old naming conventions backward compatible. `cik` added.
- Significant improvements to caching, performance and speed across all functions.

**Breaking:**

- No longer supporting inter-day periods for Technical Analysis time-series (`1week`, `1month`, `1year`).
- Removal of metrics `releaseTime` and `fiscalYearEnd` from `earnings` function.

## [v3.9.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v391-google-sheets)

`Released: 15 July 2025`

- Added new fields to `companyInfo` function
- Improvements to batch processing for `companyInfo`, `historical` and `ratios` (ttm) functions.

## [v3.9.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v390-google-sheets)

`Released: 2 July 2025`

- 98 new filters and metrics added to the `SF_SCREEN()` function as well as largescale overhaul of screener functionality. See [Screener](https://www.sheetsfinance.com/docs#/functions/screener) for more details.
- Updated Stock Screener user interface in Google Sheets sidebar.
- Bug fix for longer period sparklines.

## [v3.8.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v380-google-sheets)

`Released: 20 June 2025`

- `ratios` function overhaul, new metrics, improved naming consistency. See [Key Ratios Update](https://www.sheetsfinance.com/docs#/help/ratios-migration) for more details.
- NEW RELEASE of batching for `ttm` ratios. Limited to 10 symbols for non-commercial plans. [Contact us](https://sheetsfinance.com/support/contact) to express interest in larger batches.
- `adjClose` added to batch EOD data for split-adjusted closing prices.
- Background fixes to caching and performance.
- `yield` and `frequency` added to `SF_DIVIDEND()` function for dividend yield and frequency of dividends.

# [v3.7.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v371-google-sheets)

`Released: 29 May 2025`

- Exchange filter added to in-app Symbol Search.
- Bug fixing for brokerage feature, improved reconnection, authentication and error handling.
- Metrics for `SF_OPTIONS()` now respect order of chaining.
- Bug fixing for moving between Symbol Search and Function Generator in-app.
- Allow chaining for transaction type in `SF_BROKERAGE()` function.
- Refresh options now case insensitive, e.g., `=sf("AAPL")` and `=sf_timeseries("AAPL")` correctly targeted by refresh.

## [v3.7.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v370-google-sheets)

`Released: 30 April 2025`

- NEW RELEASE SheetsFinance Brokerage.
- NEW `SF_BROKERAGE()` function now available from the SheetsFinance Extension.
- Bug fix for `priceTargets` function.

## [v3.6.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v362-google-sheets)

`Released: 26 April 2025`

- Historical batch bug fixed. Batching of historical EOD data back online.

## [v3.6.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v361-google-sheets)

`Released: 22 April 2025`

- Changed delimiter for `industryPE` from `","` to `"|"` for better compatibility with industry naming.
- Fixed bug impact `ADX` calculations for `SF_TECHNICAL()` function.
- Bug fix for `SF_SCREEN()` function for better outputting of multiple listed industries.

## [v3.6.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v360-google-sheets)

`Released: 14 March 2025`

- NEW `revSegProduct` function for annual and quarterly revenue segmentation by product for US stocks.
- NEW `revSegGeo` function for annual and quarterly revenue segmentation by geography for US stocks.

## [v3.5.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v350-google-sheets)

`Released: 12 February 2025`

- NEW `historical` function now allows batching for historical EOD data.
- `historical` function now allows for metric chaining.
- Fixed formatting bug for `industryPE` and `sectorPE` data types, `"NLI"` and `"NH"` now work as expected.

## [v3.4.3 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v343-google-sheets)

`Released: 16 December 2024`

- Fixed RSI bug impacting calculations for `SF_TECHNICAL()` function.
- Added new line items to `ratios` function.
- Added `reportedCurrency` to balance sheet and cash flow statements.

## [v3.4.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v342-google-sheets)

`Released: 12 November 2024`

- Timezone and daylight savings bug fixes for options data.
- Improved caching and optimisations for options data.
- Fixed auth bug for `priceTargets`.
- Automatic handling for non-trading days for `SF_TECHNICAL()` function.

## [v3.4.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v341-google-sheets)

`Released: 8 October 2024`

- Automatic handling of bi-annual reporting companies for historical financials and TTM data.
- Template Library added to sidebar in Google Sheets.

## [v3.4.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v340-google-sheets)

`Released: 20 September 2024`

- NEW`SF_NEWS()` function for news feeds of stocks, crypto and forex/commodities. Includes batch functionality.
- NEW `shares` function added to `SF_TIMESERIES()` for historical outstanding shares and float data.
- NEW `score` function for financial scoring (Altman Z-Score and Piotroski F-Score).
- Added `divYield` to `companyInfo` function, can also be batched.
- Improved caching for historical PE data.
- New symbols added.

## [v3.3.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v332-google-sheets)

`Released: 27 August 2024`

- **WEBSITE** \- New [Template library](https://sheetsfinance.com/templates) to search and download pre-built templates.
- **WEBSITE** \- New [Blog](https://sheetsfinance.com/blog) covering SheetsFinance updates, tutorials and more.
- New external links to international (non-US) filings for `historicalFinancials` functions.
- Increase of max batch call limit to 5000 symbols.
- Timezone bug fix for `SF_TECHNICAL()` function. Better handling of half-hour timezones.
- Improved caching.
- Correct date formatting for `priceTargets`

## [v3.3.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v331-google-sheets)

`Released: 3 July 2024`

- Fix to historical financials ratio line items for TTM data.
- Add `".US"` search term for US stocks in `SF_CALENDAR()` function.
- Added `researchAndDevelopmentToRevenue` to ttm ratios data.
- Fix technicals metric chaining bug.

## [v3.3.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v330-google-sheets)

`Released: 27 June 2024`

- NEW `SF_CALENDAR()` function for `"economic"`, `"earnings"`, `"dividends"` and `"splits"` calendars.
- NEW US Treasury Rates using `SF_CALENDAR()` function.
- NEW `"insiders"` data type for insider trading roaster data.
- NEW `"insidersStats"` data type for summarised insider trading statistics.
- NEW `"sectorPE"` data type for historical average sector PE ratios.
- NEW `"industryPE"` data type for historical average industry PE ratios.
- Bug fixing.

## [v3.2.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v320-google-sheets)

`Released: 6 June 2024`

- New auth, account management system and website released.
- "Code Guide" renamed "Symbol Search".
- Caching, speed and performance improvements to extension.
- Bug fixing.

## [v3.1.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v311-google-sheets)

`Released: 12 April 2024`

- NEW `"isin"` option for `SF_MAP()` code mapper from ISIN to SheetsFinance ticker symbol.
- Bug fixing.

## [v3.1.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v310-google-sheets)

`Released: 04 April 2024`

- NEW `"esg"` data type for ESG scores, US markets only.
- NEW `"owners"` data type for owners earnings calculations.
- `"ratings"` function now allows for metric chaining and multi-year output.
- Historical market cap maximum output range increased to 5 years.
- Major speed optimisations and caching improvements.
- Completed migration of metrics from `companyInfo` to `realTime` data type.
- NEW utility **Clear Cache** now available from drop-down menu.

## [v3.0.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v302-google-sheets)

`Released: 20 March 2024`

- Fixed timezone-related bug impacting `SF_OPTIONS()` where next proceeding expiration date data was displayed rather than requested day.
- `SF_TECHNICAL()` data extended to 20+ years of history for daily, weekly and yearly data.
- Fixed bug with `SF_TECHNICAL()` function impacting technicals calculations when period is larger than date range.

## [v3.0.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v301-google-sheets)

`Released: 6 March 2024`

- NEW `"mid"` metric added to `SF_OPTIONS()`.
- Updated `roic` ratio calculation.
- Speed improvements/optimisations.
- Bug fixing.

## [v3.0.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v300-google-sheets)

`Released: 28 February 2024`

- INCREASED batch calls to `2000` symbols for all batch functions.
- NEW `estimatesQ` for historical and forecast quarterly estimates.
- NEW `"-"` option to reverse year order for multi-year historical financials, ratios, growth and estimates.
- `prePostMarket` function operates in batch format.
- Metric chaining for `historicalFinancials` functions, select as many metrics as you'd like to display.
- NEW inter-day time-series periods `"1week"`, `"1month"`, `"1year"`.
- NEW `"sum"` option for historical financials TTM reports (e.g., `"historicalFinancialsIncomeTTM"`) to sum all quarters and return TTM value for any historical date.
- NEW `"dividendPerShare"` (TTM only) and `"debtToMarketCap"` metrics for key ratios.
- Bug fixes, timezone related issues, dividend display and others.
- Addition of new assets and cryptocurrencies.

## [v2.9.5 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v295-google-sheets)

`Released: 16 February 2024`

- Refresh Real-time now also includes `SF_OPTIONS()` function.

## [v2.9.4 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v294-google-sheets)

`Released: 26 December 2023`

- Bug fix, default intra-day time-series. `SF_TIMESERIES()` allows for blank/null dates for intra-day data.

## [v2.9.3 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v293-google-sheets)

`Released: 21 December 2023`

- CHANGE to `etfHoldings` function to output decimal percentage (i.e., 0.02 = 2%), rather than whole percentage (i.e., 2 = 2%) for `weightPercentage` metric.

## [v2.9.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v292-google-sheets)

`Released: 06 December 2023`

- NEW `earnings` function for accessing quarterly EPS, EPS estimate, revenue and revenue estimate data.
- NEW `etfCountries` function for accessing ETF country exposure data.
- CHANGE to `etfSectors` function to output decimal percentage (i.e., 0.02 = 2%), rather than whole percentage (i.e., 2 = 2%).\`
- Bug fix for historical market capitalisation data.
- Addition of new assets.

## [v2.9.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v291-google-sheets)

`Released: 08 November 2023`

- New periods, `"1week"`, `"1month"` and `"1year"` added to `SF_TECHNICAL` function.
- `SF_OPTIONS` can now be ordered and limited using `ob=XXX` and `limit=XXX` option parameters.

## [v2.9.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v290-google-sheets)

`Released: 26 October 2023`

- NEW `prePostMarket` function for accessing pre and post market data for US equities.
- Increased batch calls to 500 codes for all batch functions.
- NEW intra-day time-series now covers 20+ years of history.
- Bug fixes and optimisations.

## [v2.8.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v280-google-sheets)

`Released: 02 October 2023`

- `growth` function now includes quarterly data, multi-year dumps and metric chaining.
- Metrics now display in order of chaining for `growth` and `ratios` functions.
- `growth` and `ratios` functions are now sorted by company financial year (same as historical financials) and new line item `Calendar Year` added to output.

## [v2.7.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v271-google-sheets)

`Released: 20 September 2023`

- Allow horizontal batch output for `companyInfo` and `realTime` functions.
- Added missing ratios `"dividendPayoutRatio"` and `"payoutRatio"` to `ratios` function.
- Left-padded columns of multi-year `ratios` output for pre IPO years to maintain consistent output between companies.
- Fixed bug with searching index options via direct contract.

## [v2.7.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v270-google-sheets)

`Released: 13 September 2023`

- `ratios` function now includes quarterly data, multi-year dumps and metric chaining.
- Bug fixing for technicals filtering and index display in batch functions.
- Addition of new assets.

## [v2.6.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v261-google-sheets)

`Released: 4 August 2023`

- Ordering of output for chaining command follows the order of the metrics in the command e.g., `"price&previousClose&change"` will output in that order.

## [v2.6.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v260-google-sheets)

`Released: 2 August 2023`

- Chaining of `realTime` and `companyInfo` metrics, e.g. `"price&previousClose&change"`.
- Chaining of `realTime` and `companyInfo` for batch functions.
- Moved metrics from `companyInfo` to `realTime` function.
- Fixed timezone bug with `earnignsAnnouncement` metric.
- Allowed for multiple listing of the same symbol in a batch call.

## [v2.5.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v250-google-sheets)

`Released: 17 July 2023`

- NEW Stock Screener using `SF_SCREEN()`.
- NEW Stock Screener Generator.
- Added new cryptocurrencies.
- Bug fixes and improved caching for ETF data.

## [v2.4.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v242-google-sheets)

`Released: 12 July 2023`

- Added `"instHolders"` data type.
- Added Refresh Errors feature.
- Added new cryptocurrencies.

## [v2.4.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v241-google-sheets)

`Released: 27 June 2023`

- Added `"max"` as option to `change` data type.
- Increased batch pulls from 200 to 300 codes for all batch functions.
- Optimisations to caching.

## [v2.4.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v240-google-sheets)

`Released: 9 June 2023`

- New `"etfInfo"` data type.
- New `"etfSectors"` data type.
- Added `"earningsAnnouncement"` to `companyInfo`.

## [v2.3.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v230-google-sheets)

`Released: 24 May 2023`

- New Function Generator, now including all SheetsFinance functions, new searchable and filterable format.
- New Code Guide.
- Added `"CIK"` and `"cusip"` to `companyInfo`.
- Added `"goodwillAndIntangibleAssets"`, `"deferredRevenueNonCurrent"`, `"capitalLeaseObligations"`, `"preferredStock"` and `"minorityInterest"` to Balance Sheets.

## [v2.2.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v220-google-sheets)

`Released: 10 May 2023`

- Added `"etfHoldings"` data type.
- Fixed `"analysts"` data type with addition of metric filtering and options.
- Adjusted dates output of all date-based functions so that date formatting is recognised by Google Sheets.

## [v2.1.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v211-google-sheets)

`Released: 06 April 2023`

- Addition of `finalLink` metric for financial statements for direct SEC link to 10-K/Q (US only).
- Speed increase, optimised loading time.
- Bug fixes.

## [v2.1.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v210-google-sheets)

`Released: 26 March 2023`

- `ttm` now available for historical cash flow statements.
- Multiple year statement dumps for quarterly reports
- Multiple year quarterly comparisons
- Direct options contract searching
- Addition of new stocks

## [v2.0.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v201-google-sheets)

`Released: 10 February 2023`

- Addition of 5,000 new global stocks and mutual funds.
- ASX stocks now available in batch requests.
- Speed increases and data delivery optimisation.
- Updated function generator.

## [v2.0.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v200-google-sheets)

`Released: 29 November 2022`

- New functions `SF_TECHNICAL()`, `SF_MAP()`.
- New data type `"change"`.
- Historical market cap data now available from `"historical"` or `SF_TECHNICAL()` for a time series.
- Addition of new stocks.
- Overhaul and optimisation of user authentication.
- Other bugs and fixes.

## [v1.8.3 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v183-google-sheets)

`Released: 01 August 2022`

- Added `"priceTargets"` data type.
- Added batch capability for `"companyInfo"`.
- Narrowed permissions scope for improved security and privacy.
- Fixed options bug for multi-year `historicalFinancials`.
- Addition of new stocks.

## [v1.8.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v182-google-sheets)

`Released: 16 June 2022`

- Added `"estimates"` data type.
- Fixed refresh bugs and optimised refresh process. Refresh All and Refresh Real-time fully functioning.
- Fixed inifinite load registration bug.

## [v1.8.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v181-google-sheets)

`Released: 9 June 2022`

- Patch for `"ttm"` bug, issue now resolved.
- Formatting improvements to Function Generator.
- Addition of new stocks and crypto.

## [v1.8.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v180-google-sheets)

`Released: 17 March 2022`

- New historical dividend data with new custom function `SF_DIVIDEND()`.
- New options data with new custom function `SF_OPTIONS()`.
- Updated `SF_TIMESERIES()` to allow for metric chaining.
- Improved data formatting for historical financials to remove headers and line items with `"NH"` and `"NLI"`.
- New `peers` data type, also included in in-app function generator.

## [v1.7.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v171-google-sheets)

`Released: 15 February 2022`

- Bug fixing for historical financial ttm.
- Optimised loading speeds for account auth.
- Bug fix for weekend crypto prices.
- Addition of new stocks.

## [v1.7.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v170-google-sheets)

`Released: 03 February 2022`

- Major server upgrades, improvements to loading times, rate limiting and external request optimisation.
- Function generator uses separator based on Sheet locale (`;` or `,`).
- Added `"reportedCurrency"`, `"period"` and `"calendarYear"` to historical financials options.

## [v1.6.5 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v165-google-sheets)

`Released: 28 January 2022`

- New stocks added
- `"ttm"` now available for all historical financials
- Account system upgrade
- `"isin"` added as an option to `companyInfo` data type
- Fixed refresh bug
- Added new crypto
- Improved code guide

## [v1.6.4 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v164-google-sheets)

`Released: 11 November 2021`

- New alt coins added
- New historical financials TTM functionality added
- Speed and performance improvements
- Bug fix ASX timeseries

## [v1.6.3 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v163-google-sheets)

`Released: 06 October 2021`

- "insert into" no longer required for Function Generator, defaults to highlighted cell
- Bug with `changesPercentage` fixed

## [v1.6.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v162-google-sheets)

`Released: 23 September 2021`

- `ttm` added as an option to the `ratios` subtype
- Fixed bug with ASX sparklines
- Fixed bug with `companyInfo` datatype for cryptos

## [v1.6.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v161-google-sheets)

`Released: 13 September 2021`

- Entering a range of years for historical financials, e.g., "2019-2021"
- Additional exchanges added
- ASX added to code guide

## [v1.5.3 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v153-google-sheets)

`Released: 30 August 2021`

- 30+ years of quarterly reports now accesible through historical financials
- Improved validation and error handling

## [v1.5.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v152-google-sheets)

`Released: 28 August 2021`

- Added 1000+ new cryptocurrencies with real-time and historical data
- New cryptocurrencies added to code guide
- Added ASX (Australian Stock Exchange) coverage, real-time and historical

## [v1.5.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v151-google-sheets)

`Released: 14 August 2021`

- New `SF_TIMESERIES()` parameters `metric` and `options`. `metric` to select a specific time series metric to display. `options` to format the output.

## [v1.5.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v150-google-sheets)

`Released: 04 August 2021`

- Single cell return for ratings totals
- New `historical` data type for getting daily data from any specific date from last 30+ years

## [v1.4.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v142-google-sheets)

`Released: 12 July 2021`

- Batch real-time data requests

## [v1.4.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v141-google-sheets)

`Released: 11 July 2021`

- Bug patch for user management
- Addition of `roic` to `ratios` data type
- Bug patch for ^ symbol not working on index codes
- Removed case contraint on ticker codes

## [v1.4.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v140-google-sheets)

`Released: 07 July 2021`

- Analyst ratings totals data
- Analyst ratings detailed data
- Improved client-side validation
- Bug patching and improved error handling
- Added refresh functionality in add-on menu (Refresh Real-time and Refresh All)

## [v1.3.2 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v132-google-sheets)

`Released: 16 June 2021`

- Additional company info `"beta"`,`"lastDiv"`,`"currency"`,`"industry"`,`"website"`,`"sector"`,`"country"`,`"fullTimeEmployees"`,`"ipoDate"`,`"ce"`
- Refresh Real-time added to menu to reload realtime info in active sheet
- Company growth information added
- patched dropdown bug

## [v1.3.1 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v131-google-sheets)

`Released: 13 June 2021`

- `SF_SPARK` now has `"volume"` or `"price"` options, added to function generator
- Improved error handling on external data requests
- Further optimised data cacheing

## [v1.3.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v130-google-sheets)

`Released: 10 June 2021`

#### [Changes](https://www.sheetsfinance.com/docs\#/changeLog?id=changes)

- Default return for SF() now realtime price
- Improved error handling
- Code Guide simple click enter stock codes into sheet
- Optimised code guide load time
- Improved error handling for timeseries and sparkline

#### [Breaking changes](https://www.sheetsfinance.com/docs\#/changeLog?id=breaking-changes)

- None

## [v1.2.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v120-google-sheets)

`Released: 10 June 2021`

#### [Changes](https://www.sheetsfinance.com/docs\#/changeLog?id=changes-1)

- SF\_STOCKS\_CRYPT() deprecated and migrated to SF()
- FOREX added
- Improved security
- Bug patch on custom function access

#### [Breaking changes](https://www.sheetsfinance.com/docs\#/changeLog?id=breaking-changes-1)

- SF\_STOCKS\_CRYPT() deprecated replaced by SF(), still functional, autocomplete removed

## [v1.1.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v110-google-sheets)

`Released: 08 June 2021`

- Fix account bug
- Fix verification bug

## [v1.1.0 google sheets](https://www.sheetsfinance.com/docs\#/changeLog?id=v110-google-sheets-1)

`Released: 06 June 2021`

#### [Changes](https://www.sheetsfinance.com/docs\#/changeLog?id=changes-2)

- `all` option for Historical Financials to display entire financial statement
- Installation bug fix
- `My Account` access bug fix
- Formatting adjustment to time series display

#### [Breaking changes](https://www.sheetsfinance.com/docs\#/changeLog?id=breaking-changes-2)

- None