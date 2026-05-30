# SheetsFinance Docs | Realtime Batch

# [Real-time Batch](#/functions/realtimeBatch?id=real-time-batch)

Are you after a lot of data fast? Our new realtime batch feature allows you to apply the `realTime` data type to a range of codes at the same time! This returns the data significantly faster than individual functions and only counts as 1 external request for Google's API quota. The functionality is simple, just use the [SF()](#/functions/availableFunctions?id=sf) function as you normally would but instead of applying it to a single cell use it on a vertical range like so:

```
=SF(A1:A100)

[multi-cell array of real-time prices]
```

All `realTime` subtypes such as `volume`, `dayHigh`, `dayLow` etc... work with the batch functionality like so:

```
=SF(A1:A100, "realTime", "volume")

[multi-cell array of real-time volumes]
```

You can even chain together metrics to return 1000s of data points at once:

```
=SF(A1:A100, "realTime", "price&volume&dayHigh&dayLow&previousClose&changesPercentage")
```

> **IMPORTANT:**
> 
> -   Allows a maximum of 2000 symbols per function, e.g. `=SF(A1:A2000)`.
> -   Does not identify individual errors and so if data is not available for a particular code in your range it will just return a blank cell.
> -   Returns data in **exactly the same order** as the code range, therefore use it directly adjacent to the requested codes, see video example below.

---

## [Examples](#/functions/realtimeBatch?id=examples)

#### [Example 1 - Batch real-time price](#/functions/realtimeBatch?id=example-1-batch-real-time-price)

```
=SF(A2:A10)
```

![Realtime Batch Example](https://cdn.sheetsfinance.com/public-site/img/docs/eo_realtime_batch.gif "Real-time batch Example")

---

#### [Example 2 - Batch real-time multiple metrics](#/functions/realtimeBatch?id=example-2-batch-real-time-multiple-metrics)

Use just 1 function to call multiple metrics on 100s of stocks at once!

```
=SF(A2:A24, "realTime", "price&volume&dayHigh&dayLow&previousClose&changesPercentage")
```

![Realtime Batch - Multiple metrics ](https://cdn.sheetsfinance.com/public-site/img/docs/realTime_batch_3.png "Realtime Batch - Multiple metrics")

#### [Example 3 - Batch real-time single metric (volume)](#/functions/realtimeBatch?id=example-3-batch-real-time-single-metric-volume)

```
=SF(A2:A32, "realTime", "volume")
```

![Realtime Batch Volume](https://cdn.sheetsfinance.com/public-site/img/docs/realtime_batch_volume.png "Realtime Batch Volume")

## Embedded Content