# SheetsFinance Docs | Dividend Data

# [Dividends](#/functions/dividends?id=dividends)

Historical company dividends can be generated via `SF_DIVIDEND()`. This function will return multiple rows and columns of data depending on the date range supplied and the metrics requested. The function layout is as follows:

```
=SF_DIVIDEND(symbol, startDate, endDate, metric, options)
```

-   `symbol` is the ticker symbol of the financial asset (e.g., `"AAPL"`). You can use our [Symbol Search](#/use/symbolSearch) to find the correct ticker symbol.
-   `startDate` is the start date for the dividend history, written in iso format YYY-MM-DD, e.g. `"2000-04-03"`
-   `endDate` is the end date for the dividend history, written in iso format YYY-MM-DD, e.g. `"2019-12-24"`
-   `metric` selects what metrics to display. Leave blank or enter `"all"` to display all available metrics. You can also select a single metric or multiple metrics by chaining them together with the `&` operator, e.g. `"date&dividend&paymentDate"`.
-   `options` adjusts the formatting of the output. `"-"` for descending order and `"NH"` for no header on the output. These can be combined by chaining with the `&` opertator like so `"-&NH"`.

The dividend `metric` options are:

-   All (`"all"`)
-   Date (`"date"`)
-   Dividend (`"dividend"`)
-   Adjusted Dividend (`"adjDividend"`)
-   Record Date (`"recordDate"`)
-   Payment Date (`"paymentDate"`)
-   Declaration Date (`"declarationDate"`)
-   Yield (`"yield"`)
-   Frequency (`"frequency"`)

> **NOTE:**
> 
> -   Leaving `metric` blank will default to displaying all metrics, the same as inputting `"all"`.
> -   You can chain together metrics to display a subset using the `&` character, such as `"date&dividend"`.

---

#### [Example 1 - All metrics no formatting](#/functions/dividends?id=example-1-all-metrics-no-formatting)

```
=SF_DIVIDEND("AAPL", "2015-10-12", "2022-03-10", "all")
```

![Dividends - Example 1](https://cdn.sheetsfinance.com/public-site/img/docs/dividend1.png "Dividends - Example 1")

---

#### [Example 2 - Single metric no formatting](#/functions/dividends?id=example-2-single-metric-no-formatting)

```
=SF_DIVIDEND("AAPL", "2015-10-12", "2022-03-10", "dividend")
```

![Dividends - Example 2](https://cdn.sheetsfinance.com/public-site/img/docs/dividend2.png "Dividends - Example 2")

---

#### [Example 3 - Multiple metrics no formatting](#/functions/dividends?id=example-3-multiple-metrics-no-formatting)

```
=SF_DIVIDEND("AAPL", "2015-10-12", "2022-03-10", "date&dividend&paymentDate")
```

![Dividends - Example 3](https://cdn.sheetsfinance.com/public-site/img/docs/dividend3.png "Dividends - Example 3")

---

#### [Example 4 - Multiple metrics no header](#/functions/dividends?id=example-4-multiple-metrics-no-header)

```
=SF_DIVIDEND("AAPL", "2015-10-12", "2022-03-10", "date&dividend&adjDividend", "NH")
```

![Dividends - Example 4](https://cdn.sheetsfinance.com/public-site/img/docs/dividend4.png "Dividends - Example 4")

---

#### [Example 5 - Multiple metrics, no header, descending order](#/functions/dividends?id=example-5-multiple-metrics-no-header-descending-order)

```
=SF_DIVIDEND("AAPL", "2015-10-12", "2022-03-10", "date&dividend&adjDividend", "-NH")
```

![Dividends - Example 5](https://cdn.sheetsfinance.com/public-site/img/docs/dividend5.png "Dividends - Example 5")

## Embedded Content