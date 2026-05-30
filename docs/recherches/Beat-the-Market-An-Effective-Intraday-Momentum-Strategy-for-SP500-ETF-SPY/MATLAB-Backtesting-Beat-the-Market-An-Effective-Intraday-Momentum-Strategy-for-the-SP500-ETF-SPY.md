MATLAB: Backtesting "Beat the Market: An Effective Intraday Momentum Strategy for the S&P500 ETF (SPY)"
=======================================================================================================

In the world of finance, MATLAB is a powerful tool used by quantitative researchers to run statistical inferences and backtest systematic trading strategies. In this blog post, we share the MATLAB code that has been used to study the profitability of the strategy presented in our paper "[Beat the Market: An Effective Intraday Momentum Strategy for the S&P500 ETF (SPY](https://bit.ly/BeatTheMarketSPY)[)](https://bit.ly/BeatTheMarketSPY)".

![](https://concretumgroup.com/wp-content/uploads/2024/05/image-16.png)

***To enhance the readability and make the code more intuitive for novice quant researchers, we intentionally avoided more complex coding procedures that may result in improved computational efficiency***.

**Step-by-Step Guide Through the Backtesting Process**
------------------------------------------------------

Below, we give an overview of the main building blocks behind the backtesting procedure.

[**Step 1: Download Data**](https://concretumgroup.com/backtesting-riding-intraday-trends-in-us-markets-using-matlab/#Step-1) -- Learn how to get FREE access to daily, intraday, and dividend data from [Polygon.io](https://bit.ly/3QONhk4).

[**Step 2: Add Key Variables**](https://concretumgroup.com/backtesting-riding-intraday-trends-in-us-markets-using-matlab/#Step-2) -- We explain how to calculate key indicators presented in the paper, such as VWAP, Move (from Open), Sigma_Open, SPY Rolling Volatility, and many others. These indicators are required to run the backtest of the strategy.

**[Step 3: Backtest](https://concretumgroup.com/backtesting-riding-intraday-trends-in-us-markets-using-matlab/#Step-3)** -- Dive into the actual backtesting process; create the main time series needed to conduct statistical inferences and performance evaluation.

**[Step 4: Study Results](https://concretumgroup.com/backtesting-riding-intraday-trends-in-us-markets-using-matlab/#Step-4)** -- We show how to plot the equity line of the trading strategy in conjunction with the passive Buy & Hold portfolio. Learn how to use historical returns time series to evaluate the profitability and risk behind the intraday momentum strategy.

![](https://concretumgroup.com/wp-content/uploads/2024/05/steps.png)

#### Tools Needed

-   **[MATLAB](https://bit.ly/3wLGFMk)**: MATLAB is a high-level programming language and environment developed by MathWorks. It is widely used for numerical computing, data analysis, algorithm development, and visualization. You can try MATLAB for FREE for 20 hours by visiting the official MathWorks website. Alternatively, a MATLAB Home license costs $149 for personal use.

**How to Read This Post**
-------------------------

For each step, we will provide the full code first, then explain it step by step. If a step depends on a utility function (a function we wrote that is not built-in MATLAB), we will provide its code after the step code directly before the explanation.

**Step 1: Download Data**
-------------------------

### **Overview**

In this step, we utilize Polygon's API to fetch intraday, daily, and dividend data for the SPY ETF. Even though Polygon provides many financial time series for each ticker, for the sake of our backtest, we only need historical data for OHLC (open, high, low, close), Volume, Time, and Dividends.

### **Step 1 Code:**

Click to see the MATLAB code for Step 1

MATLAB

```
spy_intra_data  = fetchPolygonData('SPY', '2022-05-09', '2024-04-22','minute');
spy_daily_data  = fetchPolygonData('SPY', '2022-05-09', '2024-04-22', 'day');
dividends       = fetchPolygonDividends('SPY');
```

### **Needed functions for Step 1**:

-   fetchPolygonData
-   fetchPolygonDividends

Click to see the MATLAB code for fetchPolygonData

MATLAB

```
function stock_data = fetchPolygonData(stocksTicker, fromDate, toDate, period)
    % Fetch stock data from Polygon.io API

    % Validate date range
    dateFrom = datetime(fromDate, 'InputFormat', 'yyyy-MM-dd');
    dateTo = datetime(toDate, 'InputFormat', 'yyyy-MM-dd');
    if dateTo - dateFrom > years(2)
        error('Date range exceeds the maximum of 2 years allowed for data access.');
    end

    % Define API key and parameters
    apiKey = 'API_KEY';
    multiplier = '1';
    timespan = period;  % 'minute' or 'day', depending on the period parameter
    adjusted = 'false';
    sort = 'asc';
    limit = '50000';

    % Construct the initial URL for the Polygon API request
    baseUrl = 'https://api.polygon.io/v2/aggs/ticker/';
    url = sprintf('%s%s/range/%s/%s/%s/%s?adjusted=%s&sort=%s&limit=%s&apiKey=%s', ...
        baseUrl, stocksTicker, multiplier, timespan, fromDate, toDate, adjusted, sort, limit, apiKey);

    % Use webread to fetch data from the API
    options = weboptions('ContentType', 'json', 'Timeout', 12);

    % Initialize result structure
    stock_data = struct('volume', [], 'ohlc', [], 'caldt', []);

    % Paginate through data using cursors
    while true
        fprintf('Fetching data from: %s\n', url);
        data = webread(url, options);

        % Process the current page of stock data
        stockData = data.results;
        datetimeValues = arrayfun(@(x) datetime(x / 1000, 'ConvertFrom', 'posixtime', 'TimeZone', 'America/New_York'), [stockData.t]);

        if strcmp(period, 'minute')
            % Market hours filter (applied only if 'minute' resolution)
            marketStart = timeofday(datetime('09:30', 'Format', 'HH:mm'));
            marketEnd = timeofday(datetime('15:59', 'Format', 'HH:mm'));
            marketHoursFilter = timeofday(datetimeValues) >= marketStart & timeofday(datetimeValues) <= marketEnd;

            filteredVolumes = [stockData(marketHoursFilter).v]';
            filteredOHLC = [[stockData(marketHoursFilter).o]' [stockData(marketHoursFilter).h]' [stockData(marketHoursFilter).l]' [stockData(marketHoursFilter).c]'];

            stock_data.volume = [stock_data.volume; filteredVolumes];
            stock_data.ohlc = [stock_data.ohlc; filteredOHLC];
            stock_data.caldt = [stock_data.caldt; datenum(datetimeValues(marketHoursFilter))'];

        else
            volumes = [stockData.v]';
            ohlc = [[stockData.o]' [stockData.h]' [stockData.l]' [stockData.c]'];

            stock_data.volume = [stock_data.volume; volumes];
            stock_data.ohlc = [stock_data.ohlc; ohlc];
            stock_data.caldt = [stock_data.caldt; datenum(datetimeValues)'];
        end

        % Check if there is a next page
        if isfield(data, 'next_url') && ~isempty(data.next_url)
            url = [data.next_url '&apiKey=' apiKey];
        else
            break;  % Exit loop if no more pages
        end
    end
end
```

Click to see the MATLAB code for fetchPolygonDividends

MATLAB

```
function dividends = fetchPolygonDividends(stocksTicker)
    % Fetches dividend data from Polygon.io for a specified stock ticker.

    % Define API key and limit inside the function
    apiKey = 'API_KEY';
    limit = '1000'; % Limit for the number of records

    % Construct the initial URL for the Polygon API request
    url = sprintf('https://api.polygon.io/v3/reference/dividends?ticker=%s&limit=%s&apiKey=%s', stocksTicker, limit, apiKey);

    % Initialize the output struct 'dividends'
    dividends = struct('caldt', [], 'dividend', []);

    % Use webread to fetch data from the API with options
    options = weboptions('ContentType', 'json', 'Timeout', 12);

    % Paginate through data using next_url
    while true
        fprintf('Fetching data from: %s\n', url);
        data = webread(url, options);

        % Check if there are results and append to dividends struct
        if isfield(data, 'results')
            results = data.results;
            for i = 1:numel(results)
                caldt = datenum(results{i}.ex_dividend_date, 'yyyy-mm-dd');
                dividend = results{i}.cash_amount;
                dividends.caldt = [dividends.caldt; caldt];
                dividends.dividend = [dividends.dividend; dividend];
            end
        end

        if isfield(data, 'next_url') && ~isempty(data.next_url)
            url = [data.next_url '&apiKey=' apiKey];
        else
            break;
        end
    end
end
```

### **Explanation**:

To initiate the backtest, we require high-quality intraday trading data. Here, we use Polygon's API, a reliable source for financial data that offers free access within certain limits---specifically, up to 2 years of data and 5 requests per minute. This example demonstrates how to fetch this data using custom MATLAB functions that adjust the timestamp from UTC to NY Market time (from 9:30 AM to 3:59 PM) and filter for market hours only.

After running the codes, which will take approximately 2.5 minutes, the variables will contain the following data:

-   `**spy_intra_data**`: Includes intraday volume and OHLC (open, high, low, close).
-   `**spy_daily_data**`: Contains daily volume and OHLC.
-   `**dividends**`: Stores dividend dates and amounts.

Note that it will take 2.5 minutes because the function is written so that it does not exceed 5 requests per minute; with a paid option, the downloading will be almost instantaneous.

You must obtain a **free** API Key by registering with Polygon. Consider securely managing your API key, such as using a virtual environment variable for sensitive information.

You must obtain a free API Key by registering with Polygon. Consider securely managing your API key, such as using a virtual environment variable for sensitive information. When you get your API Key, remember to update line 12 in **fetchPolygonData** and line 5 in **fetchPolygonDividends** with the actual value of the API Key, making sure it's a string, like "EXAMPLE_API_KEY" not EXAMPLE_API_KEY.

### **Efficiency Tip:**

While initially fetching the data may take approximately 2.5 minutes due to API rate limits, you do not need to repeat this process every time you want to analyze the data or test your trading strategy. To save time, you can store the fetched data locally after the first download.

-   **Save the Data**: After running the data fetching scripts and obtaining `**spy_intra_data**`, `**spy_daily_data**`, and `**dividends**`, save these variables into a MATLAB file. This way, you only need to fetch the data once, and can easily reload it for future analyses or tests.

Click to see the MATLAB code

MATLAB

```
save('database.mat', 'spy_intra_data', 'spy_daily_data', 'dividends');
```

-   **Load the Data**: The next time you need the data, instead of re-fetching it from the API, you can simply load it from the saved file. This is much faster and conserves API usage.

Click to see the MATLAB code for fetchPolygonDividends

MATLAB

```
load('database.mat');
```

#### **1.1 Deeper look into the variables**

All of the previous variables are stored in a structure, and each row is associated with the other rows by having the same index, as illustrated in the image:

![](https://concretumgroup.com/wp-content/uploads/2024/05/deeper_look_ohlc.png)

Now that we have downloaded data and created the basic database, we can proceed to calculate all the technical indicators.

**Step 2: Add Key Variables**
-----------------------------

### **Overview**

In this step, we'll dive into the calculations of various technical indicators that are crucial for running the backtest in Step 3. These metrics include VWAP, Move (from Open), Sigma_Open, SPY Rolling Volatility, and many others. Each step is broken down for clarity.

### **Step 2 Code:**

Click to see the MATLAB code for Step 2

MATLAB

```
% Convert caldt to integer days to represent unique trading days
spy_intra_data.day = fix(spy_intra_data.caldt);
% Calculate and round time of day from caldt to four decimal places
spy_intra_data.tod = round(mod(spy_intra_data.caldt, 1), 4);

% Extract unique days from the data
all_days = unique(spy_intra_data.day);

% Initialize new intraday variables to NaN for holding calculated values
spy_intra_data.move_open = NaN(size(spy_intra_data.caldt));
spy_intra_data.vwap      = NaN(size(spy_intra_data.caldt));
spy_intra_data.spy_dvol  = NaN(size(spy_intra_data.caldt));

% Initialize array for storing daily returns of SPY
spy_return = NaN(length(all_days), 1);

% Loop through each trading day starting from the second day
for d = 2:length(all_days)
    % Indices for current day data
    idx = find(spy_intra_data.day == all_days(d));
    % Indices for previous day data
    idx_y = find(spy_intra_data.day == all_days(d-1));

    % Extract OHLC data for the current day
    ohlc = spy_intra_data.ohlc(idx, :);
    % Extract volume data for the current day
    volume = spy_intra_data.volume(idx, :);

    % Compute the VWAP using high, low, close and volume
    spy_intra_data.vwap(idx) = v_wap(ohlc, volume);

    % Calculate absolute percentage change from the open price at 9:30 AM
    open = spy_intra_data.ohlc(idx(1), 1);
    spy_intra_data.move_open(idx) = abs(ohlc(:, 4)./open - 1);

    % Calculate daily return for SPY using closing prices of current and previous days
    spy_return(d, 1) = spy_intra_data.ohlc(idx(end), 4) / spy_intra_data.ohlc(idx_y(end), 4) - 1;

    % Calculate rolling 14-day volatility of SPY returns if we have enough data
    if d > 15
        spy_intra_data.spy_dvol(idx) = std(spy_return(d-15:d-1));
    end
end

% Calculate the minutes from market open at 9:30 AM
spy_intra_data.min_from_open = round((spy_intra_data.tod - 9.5 / 24) * 60 * 24, 0) + 1;

% Vector of all minutes from market open from 1 to 390
all_minutes = 1:390;

% Initialize sigma_open with NaNs for calculating rolling mean
spy_intra_data.sigma_open = NaN(size(spy_intra_data.caldt));

% Calculate rolling mean of movement from open, grouped by each minute
for m = 1:length(all_minutes)
    idx_ = find(spy_intra_data.min_from_open == all_minutes(m));
    spy_intra_data.sigma_open(idx_) = lag_TS(Rolling_Mean(spy_intra_data.move_open(idx_), 14, 'omitnan'), 1);
end

% Convert dividend dates to integer days for matching
dividends.day = fix(dividends.caldt);

% Initialize dividend data vector with zeros
spy_intra_data.dividends = zeros(size(spy_intra_data.caldt));

% Assign dividend values to corresponding trading days
for i = 1:length(dividends.caldt)
    idx = find(spy_intra_data.day == dividends.day(i), 1);
    if ~isempty(idx)
        spy_intra_data.dividends(idx) = dividends.dividend(i);
    end
end
```

### **Needed functions for Step 2:**

-   v_wap
-   Rolling_Mean
-   lag_TS

Click to see the MATLAB code for v_wap

MATLAB

```
function y = v_wap(ohlc, volume)
    % Calculate the Volume Weighted Average Price (VWAP) for given price data
    % Inputs:
    %   ohlc: An Nx4 matrix where columns represent open, high, low, and close prices
    %   volume: An Nx1 vector of trading volumes for each corresponding row in ohlc
    % Output:
    %   y: An Nx1 vector of VWAP values

    hlc = mean(ohlc(:,2:end), 2); % Calculate the mean of high, low, and close prices
    vol_x_hlc = volume .* hlc;    % Product of volume and average price
    y = cumsum(vol_x_hlc) ./ cumsum(volume); % Cumulative sum to calculate VWAP
end
```

Click to see the MATLAB code for Rolling_Mean

MATLAB

```
function y = Rolling_Mean(price, window, nanflag)
    % Compute the rolling mean of a time-series over a specified window
    % Inputs:
    %   price: An Nx1 vector of price data
    %   window: Scalar defining the number of observations used for the moving average
    %   nanflag: String, either 'omitnan' or 'includenan', specifying how to treat NaNs
    % Output:
    %   y: An Nx1 vector of the rolling mean values

    y = movmean(price, [window-1 0], 1, nanflag); % Calculate moving average
    y(1:window-1) = NaN; % Assign NaN to the first 'window-1' elements
end
```

Click to see the MATLAB code for lag_TS

MATLAB

```
function y = lag_TS(data, n)
    % Lag a data matrix by 'n' periods
    % Inputs:
    %   data: An NxM matrix of data
    %   n: Scalar defining the number of periods by which to lag the data
    % Output:
    %   y: An NxM matrix of lagged data

    [T, N] = size(data); % Get the dimensions of the input data matrix
    y = NaN(T, N); % Initialize the output matrix with NaNs

    if n > 0
        y((n+1):T, :) = data(1:(T-n), :); % Lag data forward by 'n' periods
    end
end
```

### **Explanation:**

#### **2.1 Preparing Data Variables**

-   **Date and Time Variables:**
    -   `**spy_intra_data.day**`: This represents the trading day by fixing the date component of **spy_intra_data.caldt**, effectively removing the time of day portion.
    -   `**spy_intra_data.tod**`: This captures the time of day by extracting the decimal part of `**spy_intra_data.caldt**` and rounding to four decimal places, representing the time in fractional days.

Click to see the MATLAB code for Data Variables

MATLAB

```
% Convert caldt to integer days to represent unique trading days
spy_intra_data.day = fix(spy_intra_data.caldt);
% Calculate and round time of day from caldt to four decimal places
spy_intra_data.tod = round(mod(spy_intra_data.caldt, 1), 4);
```

-   **Unique Days:**
    -   `**all_days**`: A vector containing all unique days derived from `**spy_intra_data.day**`, which helps in processing data day by day.

Click to see the MATLAB code for Unique Days

MATLAB

```
% Extract unique days from the data
all_days = unique(spy_intra_data.day);
```

#### **2.2 Initializing Variables for Metrics**

Variables like `**spy_intra_data.move_open**`, `**spy_intra_data.vwap**`, and `**spy_intra_data.spy_dvol**` are initialized with `NaN` values for each timestamp in `**spy_intra_data.caldt**`, setting up placeholders for the calculated metrics.

Click to see the MATLAB code

MATLAB

```
% Initialize new intraday variables to NaN for holding calculated values
spy_intra_data.move_open = NaN(size(spy_intra_data.caldt));
spy_intra_data.vwap = NaN(size(spy_intra_data.caldt));
spy_intra_data.spy_dvol = NaN(size(spy_intra_data.caldt));

% Initialize array for storing daily returns of SPY
spy_return = NaN(length(all_days), 1);
```

#### **2.3 Calculating Daily Metrics**

We loop through each trading day starting from the second day (as the first day lacks a previous day's data for some calculations):

-   **Indexes for Current and Previous Days:**
    -   `**idx**`: Indexes for the current day's data in `**spy_intra_data.day**`.
    -   `**idx_y**`: Indexes for the previous day's data in `**spy_intra_data.day**`.

-   **Daily VWAP Calculation:**
    -   Using the `**v_wap**` function, we calculate the Volume Weighted Average Price (VWAP) for each day using high, low, close, and volume data.

\[ \text{VWAP}_t = \frac{\sum_{i=1}^t P_{\text{HLC},i} \times \text{Volume}_i}{\sum_{i=1}^t \text{Volume}_i} \] \[ \text{Where } P_{\text{HLC},i} \text{ is defined as:} \] \[ P_{\text{HLC},i} = \frac{\text{High}_i + \text{Low}_i + \text{Close}_i}{3} \]

-   **Move from the Open**:
    -   Calculate the absolute percentage move between the market Open price (at 9:30) and the Close of each 1-minute bar.

-   **Daily SPY Returns:**
    -   Compute the daily return of SPY by comparing the Close of day t with the Close of day t-1

-   **Rolling Volatility:**
    -   Calculate a 14-day rolling standard deviation of daily returns to measure market volatility. This only starts from the 16th day because the previous 15 days are needed to compute the first value.

Click to see the MATLAB code for Rolling Volatility

MATLAB

```
    % Calculate daily return for SPY using closing prices of current and previous days
    spy_return(d, 1) = spy_intra_data.ohlc(idx(end), 4) / spy_intra_data.ohlc(idx_y(end), 4) - 1;

    % Calculate rolling 14-day volatility of SPY returns if we have enough data
    if d > 15
        spy_intra_data.spy_dvol(idx) = std(spy_return(d-15:d-1));
    end
```

To understand better the calculations of **spy_return** and **`spy_intra_data.spy_dvol`**, look at the next figure:

![](https://concretumgroup.com/wp-content/uploads/2024/05/SPY_Return_Vol.png)

#### **2.5 Adjusting Time Variables**

-   **Minutes from Market Open:**
    -   Create a variable where for each intraday data, we know how many minutes have occurred since the open of the market. This variable is needed to limit trading only to specific minutes of the day.
    -   In this case, 9:30 will be the first "1" min from open, and 15:59 will be 390, since there are 390 minutes of trading within a day.

Click to see the MATLAB code for Minutes from Market Open

MATLAB

```
% Calculate the minutes from market open at 9:30 AM
spy_intra_data.min_from_open = round((spy_intra_data.tod - 9.5 / 24) * 60 * 24, 0) + 1;
```

![](https://concretumgroup.com/wp-content/uploads/2024/05/image-14.png)

#### **2.6 Calculating Intraday Rolling Metrics**

-   **Rolling Mean Sigma:**
    -   For each minute from market open, compute a rolling mean of the absolute move from open, and apply a one-day lag. This captures the average move from Open to minute MM over the previous 14 days.

Click to see the MATLAB code for Minutes from Rolling Mean Sigma

MATLAB

```
% Vector of all minutes from market open from 1 to 390
all_minutes = 1:390;

% Initialize sigma_open with NaNs for calculating rolling mean
spy_intra_data.sigma_open = NaN(size(spy_intra_data.caldt));

% Calculate rolling mean of movement from open, grouped by each minute
for m = 1:length(all_minutes)
    idx_ = find(spy_intra_data.min_from_open == all_minutes(m));
    spy_intra_data.sigma_open(idx_) = lag_TS(Rolling_Mean(spy_intra_data.move_open(idx_), 14, 'omitnan'), 1);
end
```

To understand it visually, see the following figure:

![](https://concretumgroup.com/wp-content/uploads/2024/05/SIGMA_OPEN3.png)

#### **2.7 Handling Dividend Data**

-   **Integration**: Some overnight gaps are not due to real demand/supply imbalance but are caused by dividend payments. We need to keep track of these dividends to properly compute the Noise Area in the backtest.

Click to see the MATLAB code for Dividends

MATLAB

```
% Convert dividend dates to integer days for matching
dividends.day = fix(dividends.caldt);

% Initialize dividend data vector with zeros
spy_intra_data.dividends = zeros(size(spy_intra_data.caldt));

% Assign dividend values to corresponding trading days
for i = 1:length(dividends.caldt)
    idx = find(spy_intra_data.day == dividends.day(i), 1);
    if ~isempty(idx)
        spy_intra_data.dividends(idx) = dividends.dividend(i);
    end
end
```

Now that we have included in our database all the technical variables, we are ready to run the backtest.

**Step 3: Backtest**
--------------------

### **Overview**

In this part, we conduct the actual backtest. This section involves defining the trading environment, including assets under management (AUM), commission costs, maximum leverage, volatility multiplier, and many others. To improve the readability of the code, we used a for loop where each iteration represents a historical trading day.

### **Step 3 Code:**

Click to see the MATLAB code for Step 3

MATLAB

```
AUM_0              = 100000; % starting AUM

commission         = 0.0035; % commission per share
min_comm_per_order = 0.35; % minimum commission per order

% VOLATILITY BAND DEFINITION
band_mult       = 1; % the Volatility Multiplier as described in paper

% REBALANCING FREQUENCY
trade_freq   = 30;

% SIZING METHOD
sizing_type  = "vol_target"; % Full Notional, Volatility Target
target_vol   = 0.02; % when all tranches are activated! This is very unlikely!
max_leverage = 4;

% Clear previous strategy logs
clear strat trade_log

% Initalize a structure where the strategy daily info are saved
strat.caldt         = all_days;
strat.ret           = NaN(length(all_days),1);
strat.AUM           = AUM_0*ones(length(all_days),1);
strat.ret_spy       = NaN(length(all_days),1);

% Calculate daily returns for SPY using the adjusted closing prices

spy_daily_data.ret = [NaN; diff(spy_daily_data.ohlc(:, 4)) ./ spy_daily_data.ohlc(1:end-1, 4)];

for d = 2:length(all_days) % start from day 2 as we need data from AUM(d-1)=AUM(1)
    % indexes for previous day intraday data
    idx_y      = find(spy_intra_data.day == all_days(d-1));

    % indexes for today intraday data
    idx        = find(spy_intra_data.day == all_days(d));

    % intraday data for today
    ohlc          = spy_intra_data.ohlc(idx,:);
    vwap          = spy_intra_data.vwap(idx,:);
    min_from_open = spy_intra_data.min_from_open(idx,1);
    spx_vol       = spy_intra_data.spy_dvol(idx(1));
    open          = ohlc(1,1);
    dividend      = spy_intra_data.dividends(idx(1));

    % adjust for the dividend (a overnight gap down due to a dividend paid is not a demand/supply imbalance)
    y_close    = spy_intra_data.ohlc(idx_y(end),4) - dividend;

    if isnan(spy_intra_data.sigma_open(idx(1))); continue; end; % no data for spy_intra_data.sigma_open on the first 14 days (length of rolling window for this sigma_open formula)

    UB = max(open,y_close)*(1+band_mult*spy_intra_data.sigma_open(idx));
    LB = min(open,y_close)*(1-band_mult*spy_intra_data.sigma_open(idx));

    % at the end of each minute check if price > max ( VWAP , UB ) for
    % long, or price < min ( VWAP , LB ) for short
    signal = zeros(length(ohlc),1);
    signal(ohlc(:,4)>UB & ohlc(:,4)>vwap) = 1;
    signal(ohlc(:,4)<LB & ohlc(:,4)<vwap) = -1;

    % HOW MANY SHARES TO TRADE
    if strcmp(sizing_type,"vol_target") % as final version in paper
        shares = round(strat.AUM(d-1)/open*min(target_vol/spx_vol,max_leverage),0);
    elseif strcmp(sizing_type,"full_notional") % as initial version in paper
        shares = round(strat.AUM(d-1)/open,0);
    end

    % We don't trade every minute, but every "trade_freq" ( in paper is
    % 30minutes)
    idx_trade  = find(mod(min_from_open,trade_freq)==0);

    % COMPUTE THE
    % 1. Only at hh:00 and hh:30 check the signal and report it in the exposure vector
    % 2. Replace the NaN on all other minutes with the most recent exposure
    % computed at hh:00 and hh:30
    % 3. Lag by 1 period the exposure as the signal compute at the end of
    % minute t is used for trading t+1
    % 4. Replace NaN with 0
    change_1m = [NaN; diff(ohlc(:,4))];

    exposure                  = NaN(length(signal),1);
    exposure(idx_trade,1)     = signal(idx_trade,1);
    exposure = fillmissing(exposure, 'previous');
    exposure                  = lag_TS(exposure,1);
    exposure(isnan(exposure)) = 0;

    trades_count          = sum(abs(diff([exposure; 0])),'omitmissing');

    % PnL calculation
    gross_pnl          = sum(exposure.*change_1m,'omitmissing')*shares;
    commission_paid    = trades_count*max(min_comm_per_order,commission*shares);
    net_pnl            = gross_pnl - commission_paid;

    % Update strategy performance
    strat.ret(d)       = net_pnl/strat.AUM(d-1);
    strat.AUM(d)       = strat.AUM(d-1)+net_pnl;

    % Save SPY's daily return
    idx_spx    = find(spy_daily_data.caldt == all_days(d));
    if ~isempty(idx_spx)
        strat.ret_spy(d) = spy_daily_data.ret(idx_spx);
    end

end
```

### **Explanation:**

#### **3.1 Initial Setup and Parameters**

-   `**AUM_0**` Initial assets under management set at $100,000.
-   **`commission`** and **`min_comm_per_order`:** Define the trading costs per share and the minimum commission per transaction.

Click to see the MATLAB code

MATLAB

```
AUM_0 = 100000; % Starting AUM
commission = 0.0035; % Commission per share
min_comm_per_order = 0.35; % Minimum commission per order
```

#### **3.2 Trading Configuration**

-   **band_mult**: Multiplier that adjusts the width of the volatility bands used for trade triggers.
-   **trade_freq**: Frequency of portfolio rebalancing, set to every 30 minutes.
-   **sizing_type**: Strategy for determining trade size, options include volatility targeting (`**vol_target**`) and using the full notional value (`**full_notional**`).

Click to see the MATLAB code

MATLAB

```
band_mult = 1; % Volatility band multiplier
trade_freq = 30; % Rebalancing frequency in minutes
sizing_type = "vol_target"; % Sizing method: 'vol_target'
```

#### **3.3 Strategy Data Structures**

-   **strat**: A structure to store daily strategy performance metrics, including calendar dates, daily returns, AUM, and SPY benchmark returns.

Click to see the MATLAB code

MATLAB

```
strat.caldt = all_days;
strat.ret = NaN(length(all_days), 1);
strat.AUM = AUM_0 * ones(length(all_days), 1);
strat.ret_spy = NaN(length(all_days), 1);
```

#### **3.4 Trading Logic**

-   Implement trading logic to execute based on volatility bands and VWAP signals.
-   Adjust previous day's closing price for dividends, compute trading signals, and manage trades execution.
-   As the trading frequency is a parameter, we compute the signal for each minute of the day.

Click to see the MATLAB code

MATLAB

```
for d = 2:length(all_days)
    idx = find(spy_intra_data.day == all_days(d));
    idx_y = find(spy_intra_data.day == all_days(d-1));
    ohlc = spy_intra_data.ohlc(idx,:);
    vwap = spy_intra_data.vwap(idx,:);
    dividend = spy_intra_data.dividends(idx(1));
    y_close = spy_intra_data.ohlc(idx_y(end), 4) - dividend;
    UB = max(ohlc(1,1), y_close) * (1 + band_mult * spy_intra_data.sigma_open(idx));
    LB = min(ohlc(1,1), y_close) * (1 - band_mult * spy_intra_data.sigma_open(idx));
    signal = zeros(length(ohlc), 1);
    signal(ohlc(:,4) > UB & ohlc(:,4) > vwap) = 1;  % Long signal
    signal(ohlc(:,4) < LB & ohlc(:,4) < vwap) = -1; % Short signal

    % Shares, Rebalancing Minutes, Exposure Next Section %
```

#### **3.5 Share Sizing Decision**

-   **Volatility Targeting (`vol_target`)**:
    -   First, we compute the leverage required to achieve our desired level of volatility, ensuring it does not exceed the maximum leverage provided by the broker.
    -   To determine the number of shares to be traded, we multiply the AUM by the resulting leverage and then divide by the opening price. Finally, we round the result to the nearest integer.
-   **Full Notional (`full_notional`)**:
    -   Calculate shares by rounding down the AUM divided by the opening price.

Click to see the MATLAB code

MATLAB

```
    if strcmp(sizing_type,"vol_target")         % as final version in paper
        shares = round(strat.AUM(d-1)/open*min(target_vol/spx_vol,max_leverage),0);
    elseif strcmp(sizing_type,"full_notional") % as initial version in paper
        shares = round(strat.AUM(d-1)/open,0);
    end
```

#### **3.6 Rebalancing Minutes**

-   Identify the minutes (or rows) when the strategy can check the signal.
-   Use these identified minutes to evaluate the trading signal.

Click to see the MATLAB code

MATLAB

```
idx_trade  = find(mod(min_from_open,trade_freq)==0);
```

#### **3.7 Exposure**

-   Initialize an empty vector to track the portfolio exposure for each minute of the day.
-   On rebalancing minutes, check the trading signal and update the exposure vector accordingly.
-   Maintain the same exposure in the subsequent minutes until a new rebalancing minute is reached.
-   Lag the exposure by one period so that the signal computed at the end of minute t affects the PnL of the strategy for minute t+1.
-   Replace all NaN values in the exposure vector with 0.
-   Count the number of transactions per day based on changes in the exposure.
-   This section ensures that the strategy rebalances the portfolio at specified intervals, correctly computes the exposure, and tracks the number of transactions per day, maintaining consistency and accuracy in the backtesting process.

Click to see the MATLAB code

MATLAB

```
exposure                  = NaN(length(signal),1);
exposure(idx_trade,1)     = signal(idx_trade,1);
exposure                  = fillmissing(exposure, 'previous');
exposure                  = lag_TS(exposure,1);
exposure(isnan(exposure)) = 0;

trades_count              = sum(abs(diff([exposure; 0])),'omitmissing');
```

#### **3.8 Profit and Loss Calculation**

-   Calculate and update the profit and loss for the strategy, taking into account trade execution and commissions.
-   Update the Asset Under Management (AUM) at the end of the day.

Click to see the MATLAB code

MATLAB

```
change_1m = [NaN; diff(ohlc(:,4))];
gross_pnl = sum(signal .* change_1m, 'omitmissing') * shares;
commission_paid = trades_count * max(min_comm_per_order, commission * shares);
net_pnl = gross_pnl - commission_paid;
strat.ret(d) = net_pnl / strat.AUM(d-1);
strat.AUM(d) = strat.AUM(d-1) + net_pnl;
```

#### **3.9 Benchmarking**

-   Save the daily returns of a passive SPY buy-and-hold strategy for comparison.

Click to see the MATLAB code

MATLAB

```
if ~isempty(idx_spx)
    strat.ret_spy(d) = spy_daily_data.ret(idx_spx);
end
```

And that's it, our backtest is done! Now we can study the historical performance of the strategy.

**Step 4: Study Results**
-------------------------

### **Overview**

In this section, we learn how to plot the equity lines for the active intraday momentum strategy and for the passive portfolio invested in the SPY. Moreover, we compute the main performance statistics used by investors to evaluate the efficacy of a trading strategy.

### **Step 4 Code:**

Click to see the MATLAB code

MATLAB

```
strat.AUM_SPX = AUM_0 * cumprod(1 + strat.ret_spy, 'omitnan'); % Calculating the adjusted AUM for SPX

fig = figure();
plot(strat.caldt, strat.AUM, 'LineWidth', 2,'Color','k'), hold on
plot(strat.caldt, strat.AUM_SPX, 'LineWidth', 1, 'Color','r'), hold off
grid on; set(gca, 'GridLineStyle', ':');
datetick('x', 'mmm yy', 'keepticks'); % Keep the ticks and format them
xtickangle(90); % Rotate x-tick labels
ytickformat('$%,.0f'); % Format y-tick labels as currency
ax = gca; ax.YAxis.Exponent = 0; % Avoid scientific notation in y-axis
set(gca, 'FontSize', 8); % Adjust font size for readability
legend('Momentum', 'SPY', 'Location', 'northwest'); % Adjust legend
title('Intraday Momentum Strategy', 'FontWeight', 'bold', 'FontSize', 12);
subtitle(['Commission = $' num2str(commission) '/share'], 'FontSize', 9);

stats.totret = round((prod(1+strat.ret,'omitmissing')-1)*100,0);
stats.irr    = round((prod(1+strat.ret,'omitmissing')^(252/length(all_days))-1)*100,1);
stats.vol    = round(std(strat.ret,'omitmissing')*sqrt(252)*100,1);
stats.sr     = round(mean(strat.ret,'omitmissing')/std(strat.ret,'omitmissing')*sqrt(252),2);
stats.hr     = round(sum(strat.ret>0)/sum(abs(strat.ret)>0)*100,0);
stats.mdd    = round(maxdrawdown(strat.AUM)*100,0);
regr         = fitlm(strat.ret_spy,strat.ret);
coef         = regr.Coefficients.Estimate;
stats.alpha  = round(coef(1)*100*252,2);
stats.beta   = round(coef(2),2);
```

#### **4.1 AUM Calculation for Active and Passive S&P 500 Exposure**

-   **AUM Calculation**: In these lines, we compute the adjusted AUM for the active and passive investment in the SPY by multiplying the initial AUM by the cumulative product of (1 + daily returns). This accounts for compounding effects over the trading period.

Click to see the MATLAB code

MATLAB

```
strat.AUM_SPX = AUM_0 * cumprod(1 + strat.ret_spy, 'omitnan');
```

#### **4.2 Visualization of Strategy Performance**

-   **Plotting Procedure**: The MATLAB script generates a plot that overlays the growth of the strategy's AUM against that of the SPY AUM. The visualization uses different colors and line widths to distinguish between the two, with additional graphical elements to enhance readability and interpretation.

Click to see the MATLAB code

MATLAB

```
% AUM for a Passive S&P500 exposure
strat.AUM_SPX = AUM_0 * cumprod(1 + strat.ret_spy, 'omitnan'); % Calculating the adjusted AUM for SPX

fig = figure();
plot(strat.caldt, strat.AUM, 'LineWidth', 2,'Color','k'), hold on
plot(strat.caldt, strat.AUM_SPX, 'LineWidth', 1, 'Color','r'), hold off
grid on; set(gca, 'GridLineStyle', ':');
datetick('x', 'mmm yy', 'keepticks'); % Keep the ticks and format them
xtickangle(90); % Rotate x-tick labels
ytickformat('$%,.0f'); % Format y-tick labels as currency
ax = gca; ax.YAxis.Exponent = 0; % Avoid scientific notation in y-axis
set(gca, 'FontSize', 8); % Adjust font size for readability
legend('Momentum', 'SPY', 'Location', 'northwest'); % Adjust legend
title('Intraday Momentum Strategy', 'FontWeight', 'bold', 'FontSize', 12);
subtitle(['Commission = $' num2str(commission) '/share'], 'FontSize', 9);
```

-   ****Comparison Insights**:** The plot provides immediate visual insights into the relative performance and volatility of the intraday momentum strategy versus a passive investment strategy in the SPY, highlighting the impact of strategic trades and commission costs.

![](https://concretumgroup.com/wp-content/uploads/2024/05/Results-2.png)

#### **4.3 Performance Statistics:**

The final step evaluates the overall performance of the intraday momentum strategy through key financial metrics. These statistics provide a comprehensive view of the strategy's returns, risk, and comparison to the benchmark, helping investors understand its effectiveness and suitability for their investment goals.

#### **Key Performance Metrics**

-   **Total Return**: Measures the total percentage return over the entire period.
-   **Annualized Return (IRR)**: Geometric average return per year.
-   **Volatility**: Represents the standard deviation of the strategy's returns, annualized to show expected fluctuation over a year.
-   **Sharpe Ratio**: Calculates the risk-adjusted return, quantifying how much return is achieved per unit of risk.
-   **Hit Ratio**: Percentage of positive returns over the total trading days, indicating the consistency of positive outcomes. The denominator does not include days when the strategy was not activated.
-   **Maximum Drawdown (MDD)**: The largest drop from peak to trough in AUM.
-   **Alpha**: Measures the strategy's return in excess of the market's return, adjusted for risk (beta).
-   **Beta**: Quantifies the sensitivity of an asset's returns to the movements of the overall market

Click to see the MATLAB code

MATLAB

```
stats.totret = round((prod(1+strat.ret,'omitmissing')-1)*100,0);
stats.irr    = round((prod(1+strat.ret,'omitmissing')^(252/length(all_days))-1)*100,1);
stats.vol    = round(std(strat.ret,'omitmissing')*sqrt(252)*100,1);
stats.sr     = round(mean(strat.ret,'omitmissing')/std(strat.ret,'omitmissing')*sqrt(252),2);
stats.hr     = round(sum(strat.ret>0)/sum(abs(strat.ret)>0)*100,0);
stats.mdd    = round(maxdrawdown(strat.AUM)*100,0);
regr         = fitlm(strat.ret_spy,strat.ret);
coef         = regr.Coefficients.Estimate;
stats.alpha  = round(coef(1)*100*252,2);
stats.beta   = round(coef(2),2);
```

![](https://concretumgroup.com/wp-content/uploads/2024/05/image.png)

**Full Code and Final Words**
-----------------------------

You can download the full code from here and run it directly cell by cell in your MATLAB!\
Remember to run cell 0 (at the bottom) to load needed functions!

[Backtesting_BeatTheMarket](https://concretumgroup.com/wp-content/uploads/2024/05/Backtesting_BeatTheMarket.mlx)