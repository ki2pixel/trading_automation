# SheetsFinance Docs | Company Info Batch

# [Company Info Batch](#/functions/companyinfoBatch?id=company-info-batch)

Are you after a lot of data fast? Our new company info batch feature allows you to apply the `companyInfo` data type to a large range of codes at the same time! This returns the data significantly faster than individual functions and only counts as 1 external request for Google's API quota. Company Info Batch functions excatly the same as Real-time Batch, just use the [SF()](#/functions/availableFunctions?id=sf) function as you normally would but instead of applying it to a single cell use it on a vertical range like so:

```
=SF(A1:A100, "companyInfo", "sector")

[multi-cell array of market caps]
```

All `comapnyInfo` subtypes such as `name`, `exchange`, `sector`, `lastDiv`, `beta` etc... work with the batch functionality like so:

```
=SF(A1:A100, "companyInfo", "exchange")

[multi-cell array of year highs]
```

You can even chain together metrics to return 1000s of data points at once:

```
=SF(A1:A100, "companyInfo", "name&exchange&sector&lastDiv")
```

> **IMPORTANT:**
> 
> -   Allows a maximum of 2000 symbols per function, e.g. `=SF(A1:A2000)`.
> -   Does not identify individual errors and so if data is not available for a particular code in your range it will just return a blank cell.
> -   Returns data in **exactly the same order** as the code range, therefore use it directly adjacent to the requested codes, see video example below.

---

## [Examples](#/functions/companyinfoBatch?id=examples)

#### [Example 1 - Single metric (market capitalisation)](#/functions/companyinfoBatch?id=example-1-single-metric-market-capitalisation)

```
=SF(A2:A11, "companyInfo", "marketCap")
```

![Company Info Batch Example](https://cdn.sheetsfinance.com/public-site/img/docs/companyInfo_batch_gif2.gif "Company Info Batch Example")

---

### [Example 2 - Mutliple metrics](#/functions/companyinfoBatch?id=example-2-mutliple-metrics)

```
=SF(A2:A20, "companyInfo", "name&exchange&sector&lastDiv")
```

![Company Info Batch multiple metrics](https://cdn.sheetsfinance.com/public-site/img/docs/companyInfo_batch_2.png "Company Info Batch multiple metrics")

#### [Example 2 - Single Metric (sector)](#/functions/companyinfoBatch?id=example-2-single-metric-sector)

```
=SF(A2:A11, "companyInfo", "sector")
```

![Company Info Batch Sectors](https://cdn.sheetsfinance.com/public-site/img/docs/companyInfo_batch_sector.png "Company Info Batch Sectors")

## Embedded Content