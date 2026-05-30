Backtesting 2 Years of FREE Data Using Python: Enhancing SPY Momentum Strategies with Polygon, from 'Beat the Market'
=====================================================================================================================

Python is a versatile tool employed by quantitative researchers to perform statistical analyses and backtest systematic trading strategies. In this blog post, we will share the Python code that replicates the results of the MATLAB code used to generate the findings in our paper titled '[Beat the Market: An Effective Intraday Momentum Strategy for the S&P500 ETF (SPY)](https://bit.ly/BeatTheMarketSPY)'. This code allows for backtesting to evaluate the profitability of the described strategy.

![](https://concretumgroup.com/wp-content/uploads/2024/05/image-16.png)

***In this blog post, we are translating [MATLAB code](https://concretumgroup.com/backtesting-riding-intraday-trends-in-us-markets-using-matlab/) into Python, maintaining the exact same logic as originally presented. Our aim is to make the code more accessible and intuitive, especially for novice quantitative researchers. To enhance readability, we have intentionally avoided more complex coding procedures that could potentially increase computational efficiency but might also obscure understanding.***

**Step-by-Step Guide Through the Backtesting Process**
------------------------------------------------------

Below, we give an overview of the main building blocks behind the backtesting procedure.

[**Step 1: Download Data**](https://concretumgroup.com/python-backtesting-beat-the-market-an-effective-intraday-momentum-strategy-for-the-sp500-etf-spy/#Step-1) -- Learn how to get FREE access to daily, intraday, and dividend data from [Polygon.io](https://bit.ly/3QONhk4).

[**Step 2: Add Key Variables**](https://concretumgroup.com/python-backtesting-beat-the-market-an-effective-intraday-momentum-strategy-for-the-sp500-etf-spy/#Step-2) -- We explain how to calculate key indicators presented in the paper, such as VWAP, Move (from Open), Sigma_Open, SPY Rolling Volatility, and many others. These indicators are required to run the backtest of the strategy.

**[Step 3: Backtesting](https://concretumgroup.com/python-backtesting-beat-the-market-an-effective-intraday-momentum-strategy-for-the-sp500-etf-spy/#Step-3)** -- Dive into the actual backtesting process; create the main time series needed to conduct statistical inferences and performance evaluation.

**[Step 4: Study Results](https://concretumgroup.com/python-backtesting-beat-the-market-an-effective-intraday-momentum-strategy-for-the-sp500-etf-spy/#Step-4)** -- We show how to plot the equity line of the trading strategy in conjunction with the passive Buy & Hold portfolio. Learn how to use historical returns time series to evaluate the profitability and risk behind the intraday momentum strategy.

![Backtesting steps](https://concretumgroup.com/wp-content/uploads/2024/05/image-17.png)

#### Tools Needed

-   **[Python](https://www.python.org/)**: Python is a versatile programming language widely used for data analysis and visualization. It's free and open-source.
    -   [**Pandas**](https://pandas.pydata.org/): Pandas is a Python library for data manipulation and analysis, ideal for working with numerical tables and time series.
    -   **[Matplotlib](https://matplotlib.org/)**: Matplotlib is a Python library for creating a wide variety of static, animated, and interactive visualizations.
    -   **[Statsmodels](https://www.statsmodels.org/stable/index.html)**: Statsmodels provides tools for statistical modeling in Python, offering numerous methods for regression and time series analysis.

**How to Read This Post**
-------------------------

For each step, we will provide the full code first, then explain it step by step. If a step depends on a utility function (a function we wrote that is not built-in Python), we will provide its code after the step code directly before the explanation.

### **Needed Imports for All Steps**:

Click to see the Python code for needed imports

Python

```
import requests
import time
import pandas as pd
from   datetime import datetime
import numpy as np
import pytz
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from   matplotlib.ticker import FuncFormatter
import statsmodels.api as sm
```

If you have missing libraries, just run this:

Click to see the command prompts

PowerShell

```
pip install requests
pip install pandas
pip install numpy
pip install pytz
pip install matplotlib
pip install statsmodels
```

**Step 1: Download Data**
-------------------------

### **Overview**

In this step, we utilize Polygon's API to fetch intraday, daily, and dividend data for the SPY ETF. Even though Polygon provides many financial time series for each ticker, for the sake of our backtest, we only need historical data for OHLC (open, high, low, close), Volume, Time, and Dividends.

### **Step 1 Code:**

Click to see the Python code for Step 1

Python

```
ticker = 'SPY'
from_date = '2022-05-09'
until_date = '2024-04-22'

spy_intra_data = fetch_polygon_data(ticker, from_date, until_date, 'minute')
spy_daily_data = fetch_polygon_data(ticker, from_date, until_date, 'day')
dividends      = fetch_polygon_dividends(ticker)
```

### **Needed functions for Step 1**:

-   **fetch_polygon_data**
-   **fetch_polygon_dividends**

Click to see the Python code for fetch_polygon_data & fetch_polygon_dividends

Python

```
# Define the API key and base URL
API_KEY  = 'API_KEY'
BASE_URL = 'https://api.polygon.io'

# Define the rate limit enforcement based on the API tier, Free or Paid.
ENFORCE_RATE_LIMIT = True

def fetch_polygon_data(ticker, start_date, end_date, period, enforce_rate_limit=ENFORCE_RATE_LIMIT):
    """Fetch stock data from Polygon.io based on the given period (minute or day).
       enforce_rate_limit: Set to True to enforce rate limits (suitable for free tiers), False for paid tiers with minimal or no rate limits.
    """
    multiplier = '1'
    timespan = period
    limit = '50000'  # Maximum entries per request
    eastern = pytz.timezone('America/New_York')  # Eastern Time Zone

    url = f'{BASE_URL}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date}/{end_date}?adjusted=false&sort=asc&limit={limit}&apiKey={API_KEY}'

    data_list = []
    request_count = 0
    first_request_time = None

    while True:
        if enforce_rate_limit and request_count == 5:
            elapsed_time = time.time() - first_request_time
            if elapsed_time < 60:
                wait_time = 60 - elapsed_time
                print(f"API rate limit reached. Waiting {wait_time:.2f} seconds before next request.")
                time.sleep(wait_time)
            request_count = 0
            first_request_time = time.time()  # Reset the timer after the wait

        if first_request_time is None and enforce_rate_limit:
            first_request_time = time.time()

        response = requests.get(url)
        if response.status_code != 200:
            error_message = response.json().get('error', 'No specific error message provided')
            print(f"Error fetching data: {error_message}")
            break

        data = response.json()
        request_count += 1

        results_count = len(data.get('results', []))
        print(f"Fetched {results_count} entries from API.")

        if 'results' in data:
            for entry in data['results']:
                utc_time = datetime.fromtimestamp(entry['t'] / 1000, pytz.utc)
                eastern_time = utc_time.astimezone(eastern)

                data_entry = {
                    'volume': entry['v'],
                    'open': entry['o'],
                    'high': entry['h'],
                    'low': entry['l'],
                    'close': entry['c'],
                    'caldt': eastern_time.replace(tzinfo=None)
                }

                if period == 'minute':
                    if eastern_time.time() >= datetime.strptime('09:30', '%H:%M').time() and eastern_time.time() <= datetime.strptime('15:59', '%H:%M').time():
                        data_list.append(data_entry)
                else:
                    data_list.append(data_entry)

        if 'next_url' in data and data['next_url']:
            url = data['next_url'] + '&apiKey=' + API_KEY
        else:
            break

    df = pd.DataFrame(data_list)
    print("Data fetching complete.")
    return df

def fetch_polygon_dividends(ticker):
    """ Fetches dividend data from Polygon.io for a specified stock ticker. """
    url = f'{BASE_URL}/v3/reference/dividends?ticker={ticker}&limit=1000&apiKey={API_KEY}'

    dividends_list = []
    while True:
        response = requests.get(url)
        data = response.json()
        if 'results' in data:
            for entry in data['results']:
                dividends_list.append({
                    'caldt': datetime.strptime(entry['ex_dividend_date'], '%Y-%m-%d'),
                    'dividend': entry['cash_amount']
                })

        if 'next_url' in data and data['next_url']:
            url = data['next_url'] + '&apiKey=' + API_KEY
        else:
            break

    return pd.DataFrame(dividends_list)
```

### **Explanation:**

To initiate the backtest, we require high-quality intraday trading data. Here, we use Polygon's API, a reliable source for financial data that offers free access within certain limits---specifically, up to 2 years of data and 5 requests per minute. This example demonstrates how to fetch this data using custom Python functions that adjust the timestamp from UTC to NY Market time (from 9:30 AM to 3:59 PM) and filter for market hours only.

After running the codes, the data frames will have the following:

-   **spy_intra_data**: Includes intraday volume and OHLC (open, high, low, close).
-   **spy_daily_data**: Contains daily volume and OHLC.
-   **dividends**: Stores dividend dates and amounts.

You must obtain a **free** API Key by registering with Polygon. Consider securely managing your API key, such as using a virtual environment variable for sensitive information.

When you get your API Key, remember to update **line 2** in the code snippet of functions with the actual value of the API Key, making sure it's a string, like "EXAMPLE_API_KEY" not EXAMPLE_API_KEY.

### **Need faster data fetching?**

If you have a paid option, set **ENFORCE_RATE_LIMIT** to **False** **(line 6)** in the code snippet. This will remove the restriction of 5 requests per minute.

Please note that the code is not optimized for large datasets. As stated in the introduction, the focus was on clarity for novice quants rather than optimization.

**Step 2: Add Key Variables**
-----------------------------

### **Overview**

In this step, we'll dive into the calculations of various technical indicators that are crucial for running the backtest in Step 3. These metrics include VWAP, Move (from Open), Sigma_Open, SPY Rolling Volatility, and many others. Each step is broken down for clarity.

### **Step 2 Code:**

Click to see the Python Code for Step 2

Python

```
# Load the intraday data into a DataFrame and set the datetime column as the index.
df = pd.DataFrame(spy_intra_data)
df['day'] = pd.to_datetime(df['caldt']).dt.date  # Extract the date part from the datetime for daily analysis.
df.set_index('caldt', inplace=True)  # Setting the datetime as the index for easier time series manipulation.

# Group the DataFrame by the 'day' column to facilitate operations that need daily aggregation.
daily_groups = df.groupby('day')

# Extract unique days from the dataset to iterate through each day for processing.
all_days = df['day'].unique()

# Initialize new columns to store calculated metrics, starting with NaN for absence of initial values.
df['move_open'] = np.nan  # To record the absolute daily change from the open price
df['vwap'] = np.nan       # To calculate the Volume Weighted Average Price.
df['spy_dvol'] = np.nan   # To record SPY's daily volatility.

# Create a series to hold computed daily returns for SPY, initialized with NaN.
spy_ret = pd.Series(index=all_days, dtype=float)

# Iterate through each day to calculate metrics.
for d in range(1, len(all_days)):
    current_day = all_days[d]
    prev_day = all_days[d - 1]

    # Access the data for the current and previous days using their groups.
    current_day_data = daily_groups.get_group(current_day)
    prev_day_data = daily_groups.get_group(prev_day)

    # Calculate the average of high, low, and close prices.
    hlc = (current_day_data['high'] + current_day_data['low'] + current_day_data['close']) / 3

    # Compute volume-weighted metrics for VWAP calculation.
    vol_x_hlc = current_day_data['volume'] * hlc
    cum_vol_x_hlc = vol_x_hlc.cumsum()  # Cumulative sum for VWAP calculation.
    cum_volume = current_day_data['volume'].cumsum()

    # Assign the calculated VWAP to the corresponding index in the DataFrame.
    df.loc[current_day_data.index, 'vwap'] = cum_vol_x_hlc / cum_volume

    # Calculate the absolute percentage change from the day's opening price.
    open_price = current_day_data['open'].iloc[0]
    df.loc[current_day_data.index, 'move_open'] = (current_day_data['close'] / open_price - 1).abs()

    # Compute the daily return for SPY using the closing prices from the current and previous day.
    spy_ret.loc[current_day] = current_day_data['close'].iloc[-1] / prev_day_data['close'].iloc[-1] - 1

    # Calculate the 15-day rolling volatility, starting calculation after accumulating 15 days of data.
    if d > 14:
        df.loc[current_day_data.index, 'spy_dvol'] = spy_ret.iloc[d - 15:d - 1].std(skipna=False)

# Calculate the minutes from market open and determine the minute of the day for each timestamp.
df['min_from_open'] = ((df.index - df.index.normalize()) / pd.Timedelta(minutes=1)) - (9 * 60 + 30) + 1
df['minute_of_day'] = df['min_from_open'].round().astype(int)

# Group data by 'minute_of_day' for minute-level calculations.
minute_groups = df.groupby('minute_of_day')

# Calculate rolling mean and delayed sigma for each minute of the trading day.
df['move_open_rolling_mean'] = minute_groups['move_open'].transform(lambda x: x.rolling(window=14, min_periods=13).mean())
df['sigma_open'] = minute_groups['move_open_rolling_mean'].transform(lambda x: x.shift(1))

# Convert dividend dates to datetime and merge dividend data based on trading days.
dividends['day'] = pd.to_datetime(dividends['caldt']).dt.date
df = df.merge(dividends[['day', 'dividend']], on='day', how='left')
df['dividend'] = df['dividend'].fillna(0)  # Fill missing dividend data with 0.
```

### **Explanation:**

#### **2.1 Preparing Data Variables**

-   **Date and Time Variables:**
    -   **df['day']**: This represents the trading day by converting the **caldt** datetime column into just the date component, effectively separating the date from time.

Click to see the Python Code

Python

```
df['day'] = pd.to_datetime(df['caldt']).dt.date
```

-   ****Index Setting**:**
    -   **df.set_index('caldt'):** This sets the **`caldt`** column as the DataFrame's index, facilitating efficient time-series operations and enabling easier slicing and access based on time.

Click to see the Python Code

Python

```
df.set_index('caldt', inplace=True)
```

#### **2.2 Grouping and Data Aggregation**

-   **Daily Grouping for Efficient Access:**
    -   **Group Data by Day:** This organizes the data into groups based on each unique trading day, facilitating easier daily aggregations and calculations.

Click to see the Python Code

Python

```
daily_groups = df.groupby('day')
```

-   **Unique Days Extraction:**
    -   **Extract Unique Trading Days:** Retrieves all unique days from the data, providing a basis for day-by-day iterations in subsequent calculations.

Click to see the Python Code

Python

```
all_days = df['day'].unique()
```

#### **2.3 Initializing Variables for Metrics**

-   **Metric Placeholders Initialization:**
    -   **NaN Initialization**: Columns such as `**move_open**`, `**vwap**`, and **`spy_dvol`** are initialized with NaN values, setting up placeholders for calculated trading metrics.

Click to see the Python Code

Python

```
df['move_open'] = np.nan  # To record the absolute daily change from the open price
df['vwap'] = np.nan       # To calculate the Volume Weighted Average Price.
df['spy_dvol'] = np.nan   # To record SPY's daily volatility.
```

-   ****Daily Returns and Volatility Preparation**:**
    -   **spy_ret Series**: Sets up a Pandas Series to capture computed daily returns for SPY, initialized with NaN to accommodate future numerical operations.

Click to see the Python Code

Python

```
spy_ret = pd.Series(index=all_days, dtype=float)
```

#### **2.4 Computation of Daily Metrics**

-   ****Daily Metrics Calculation Loop**:** This loop calculates various metrics for each day by iterating through all unique trading days
    -   **VWAP Calculation**: Computes the Volume Weighted Average Price using cumulative sums of volume times the average of high, low, and close prices.
    -   **Open Price Movement**: Calculates the absolute percentage change from the day's opening price to the close.
    -   **Daily Returns**: Computes the daily return for SPY using the close prices of the current and previous days.
    -   **Rolling Volatility**: Calculates a 15-day rolling volatility of SPY returns, starting calculations after at least 14 days of data are available.

Click to see the Python Code

Python

```
# Iterate through each day to calculate metrics.
for d in range(1, len(all_days)):
    current_day = all_days[d]
    prev_day = all_days[d - 1]

    # Access the data for the current and previous days using their groups.
    current_day_data = daily_groups.get_group(current_day)
    prev_day_data = daily_groups.get_group(prev_day)

    # Calculate the average of high, low, and close prices.
    hlc = (current_day_data['high'] + current_day_data['low'] + current_day_data['close']) / 3

    # Compute volume-weighted metrics for VWAP calculation.
    vol_x_hlc = current_day_data['volume'] * hlc
    cum_vol_x_hlc = vol_x_hlc.cumsum()  # Cumulative sum for VWAP calculation.
    cum_volume = current_day_data['volume'].cumsum()

    # Assign the calculated VWAP to the corresponding index in the DataFrame.
    df.loc[current_day_data.index, 'vwap'] = cum_vol_x_hlc / cum_volume

    # Calculate the absolute percentage change from the day's opening price.
    open_price = current_day_data['open'].iloc[0]
    df.loc[current_day_data.index, 'move_open'] = (current_day_data['close'] / open_price - 1).abs()

    # Compute the daily return for SPY using the closing prices from the current and previous day.
    spy_ret.loc[current_day] = current_day_data['close'].iloc[-1] / prev_day_data['close'].iloc[-1] - 1

    # Calculate the 15-day rolling volatility, starting calculation after accumulating 15 days of data.
    if d > 14:
        df.loc[current_day_data.index, 'spy_dvol'] = spy_ret.iloc[d - 15:d - 1].std(skipna=False)
```

#### **2.5 Minute-level Calculations:**

-   **Minute from Market Open**:
    -   Calculates the minutes from market open for each timestamp, helping in analyzing intraday trends and movements.
-   **Rolling Mean and Delayed Sigma Calculations**:
    -   Calculates rolling means and a shifted sigma (standard deviation) for opening movements, to explore more nuanced intraday dynamics.

Click to see the Python Code

Python

```
df['min_from_open'] = ((df.index - df.index.normalize()) / pd.Timedelta(minutes=1)) - (9 * 60 + 30) + 1
df['minute_of_day'] = df['min_from_open'].round().astype(int)

minute_groups = df.groupby('minute_of_day')
df['move_open_rolling_mean'] = minute_groups['move_open'].transform(lambda x: x.rolling(window=14, min_periods=13).mean())
df['sigma_open'] = minute_groups['move_open_rolling_mean'].transform(lambda x: x.shift(1))

```

#### **2.6 Handling Dividends**

-   **Dividend Data Integration**:
    -   Converts dividend dates to datetime and merges this data based on trading days, accounting for dividends in the analysis which is crucial for accurate return calculations.

Click to see the Python Code

Python

```
dividends['day'] = pd.to_datetime(dividends['caldt']).dt.date
df = df.merge(dividends[['day', 'dividend']], on='day', how='left')
df['dividend'] = df['dividend'].fillna(0)
```

Now that we have our needed Indicators, lets start backtesting!

**Step 3: Backtesting**
-----------------------

### **Overview**

In this part, we conduct the actual backtest. This section involves defining the trading environment, including assets under management (AUM), commission costs, maximum leverage, volatility multiplier, and many others. To improve the readability of the code, we used a for loop where each iteration represents a historical trading day.

### **Step 3 Code:**

Click to see the Python Code for Step 3

Python

```
import math

# Constants and settings
AUM_0 = 100000.0
commission = 0.0035
min_comm_per_order = 0.35
band_mult = 1
band_simplified = 0
trade_freq = 30
sizing_type = "vol_target"
target_vol = 0.02
max_leverage = 4

# Group data by day for faster access
daily_groups = df.groupby('day')

# Initialize strategy DataFrame using unique days
strat = pd.DataFrame(index=all_days)
strat['ret'] = np.nan
strat['AUM'] = AUM_0
strat['ret_spy'] = np.nan

# Calculate daily returns for SPY using the closing prices
df_daily = pd.DataFrame(spy_daily_data)
df_daily['caldt'] = pd.to_datetime(df_daily['caldt']).dt.date
df_daily.set_index('caldt', inplace=True)  # Set the datetime column as the DataFrame index for easy time series manipulation.

df_daily['ret'] = df_daily['close'].diff() / df_daily['close'].shift()

# Loop through all days, starting from the second day
for d in range(1, len(all_days)):
    current_day = all_days[d]
    prev_day = all_days[d-1]

    if prev_day in daily_groups.groups and current_day in daily_groups.groups:
        prev_day_data = daily_groups.get_group(prev_day)
        current_day_data = daily_groups.get_group(current_day)

        if 'sigma_open' in current_day_data.columns and current_day_data['sigma_open'].isna().all():
            continue

        prev_close_adjusted = prev_day_data['close'].iloc[-1] - df.loc[current_day_data.index, 'dividend'].iloc[-1]

        open_price = current_day_data['open'].iloc[0]
        current_close_prices = current_day_data['close']
        spx_vol = current_day_data['spy_dvol'].iloc[0]
        vwap = current_day_data['vwap']

        sigma_open = current_day_data['sigma_open']
        UB = max(open_price, prev_close_adjusted) * (1 + band_mult * sigma_open)
        LB = min(open_price, prev_close_adjusted) * (1 - band_mult * sigma_open)

        # Determine trading signals
        signals = np.zeros_like(current_close_prices)
        signals[(current_close_prices > UB) & (current_close_prices > vwap)] = 1
        signals[(current_close_prices < LB) & (current_close_prices < vwap)] = -1

        # Position sizing
        previous_aum = strat.loc[prev_day, 'AUM']

        if sizing_type == "vol_target":
            if math.isnan(spx_vol):
                shares = round(previous_aum / open_price * max_leverage)
            else:
                shares = round(previous_aum / open_price * min(target_vol / spx_vol, max_leverage))

        elif sizing_type == "full_notional":
            shares = round(previous_aum / open_price)

        # Apply trading signals at trade frequencies
        trade_indices = np.where(current_day_data["min_from_open"] % trade_freq == 0)[0]
        exposure = np.full(len(current_day_data), np.nan)  # Start with NaNs
        exposure[trade_indices] = signals[trade_indices]  # Apply signals at trade times

        # Custom forward-fill that stops at zeros
        last_valid = np.nan  # Initialize last valid value as NaN
        filled_values = []  # List to hold the forward-filled values
        for value in exposure:
            if not np.isnan(value):  # If current value is not NaN, update last valid value
                last_valid = value
            if last_valid == 0:  # Reset if last valid value is zero
                last_valid = np.nan
            filled_values.append(last_valid)

        exposure = pd.Series(filled_values, index=current_day_data.index).shift(1).fillna(0).values  # Apply shift and fill NaNs

        # Calculate trades count based on changes in exposure
        trades_count = np.sum(np.abs(np.diff(np.append(exposure, 0))))

        # Calculate PnL
        change_1m = current_close_prices.diff()
        gross_pnl = np.sum(exposure * change_1m) * shares
        commission_paid = trades_count * max(min_comm_per_order, commission * shares)
        net_pnl = gross_pnl - commission_paid

        # Update the daily return and new AUM
        strat.loc[current_day, 'AUM'] = previous_aum + net_pnl
        strat.loc[current_day, 'ret'] = net_pnl / previous_aum

        # Save the passive Buy&Hold daily return for SPY
        strat.loc[current_day, 'ret_spy'] = df_daily.loc[df_daily.index == current_day, 'ret'].values[0]
```

### **Explanation:**

#### **3.1 Initial Setup and Parameters**

-   Set the initial parameters required for the backtest:

Click to see the Python Code

Python

```
AUM_0 = 100000.0  # Initial amount of money to manage
commission = 0.0035  # Commission rate per trade
min_comm_per_order = 0.35  # Minimum commission per trade
band_mult = 1  # Multiplier for the trading band
trade_freq = 30  # Frequency of trades in minutes
sizing_type = "vol_target"  # Strategy for sizing positions based on volatility
target_vol = 0.02  # Target volatility for the position sizing
max_leverage = 4  # Maximum leverage allowed
```

#### **3.2 Data Preparation**:

-   Prepare the data and initialize the strategy Data Frame:

Click to see the Python Code

Python

```
# Group data by day for faster access
daily_groups = df.groupby('day')

# Initialize strategy DataFrame using unique days
strat = pd.DataFrame(index=all_days)
strat['ret'] = np.nan
strat['AUM'] = AUM_0
strat['ret_spy'] = np.nan
```

#### **3.3 Calculate Daily Returns for SPY**

-   Calculate and set the daily returns for SPY based on the close prices, this will be used for benchmarking (**BUY&HOLD)** :

Click to see the Python Code

Python

```
df_daily = pd.DataFrame(spy_daily_data)
df_daily['caldt'] = pd.to_datetime(df_daily['caldt']).dt.date
df_daily.set_index('caldt', inplace=True)
df_daily['ret'] = df_daily['close'].diff() / df_daily['close'].shift()
```

#### **3.4 Trading Logic**

-   Loop through each trading day and access the necessary data:

Click to see the Python Code

Python

```
for d in range(1, len(all_days)):
    current_day = all_days[d]
    prev_day = all_days[d-1]

    if prev_day in daily_groups.groups and current_day in daily_groups.groups:
        prev_day_data = daily_groups.get_group(prev_day)
        current_day_data = daily_groups.get_group(current_day)

        if 'sigma_open' in current_day_data.columns and current_day_data['sigma_open'].isna().all():
            continue  # Skip if no valid sigma data
```

#### **3.5 Position Sizing and Trading Signals**

-   Determine the position size and calculate trading signals:

Click to see the Python Code

Python

```
        previous_aum = strat.loc[prev_day, 'AUM']

        if sizing_type == "vol_target":
            spx_vol = current_day_data['spy_dvol'].iloc[0]
            if math.isnan(spx_vol):
                shares = round(previous_aum / open_price * max_leverage)
            else:
                shares = round(previous_aum / open_price * min(target_vol / spx_vol, max_leverage))
        elif sizing_type == "full_notional":
            shares = round(previous_aum / open_price)
```

-   Calculate upper and lower bounds and signals:

Click to see the Python Code

Python

```
        UB = max(open_price, prev_close_adjusted) * (1 + band_mult * sigma_open)
        LB = min(open_price, prev_close_adjusted) * (1 - band_mult * sigma_open)
        signals = np.zeros_like(current_close_prices)
        signals[(current_close_prices > UB) & (current_close_prices > vwap)] = 1
        signals[(current_close_prices < LB) & (current_close_prices < vwap)] = -1
```

#### **3.6 Trade Execution**

-   Apply trading signals and manage exposure using a custom forward-fill method:

Click to see the Python Code

Python

```
        # Apply trading signals at trade frequencies
        trade_indices = np.where(current_day_data["min_from_open"] % trade_freq == 0)[0]
        exposure = np.full(len(current_day_data), np.nan)
        exposure[trade_indices] = signals[trade_indices]

        # Custom forward-fill logic
        filled_values = []
        last_valid = np.nan
        for value in exposure:
            if not np.isnan(value):
                last_valid = value
            if last_valid == 0:
                last_valid = np.nan
            filled_values.append(last_valid)
        exposure = pd.Series(filled_values, index=current_day_data.index).shift(1).fillna(0).values
```

#### **3.7 Profit and Loss Calculation**

-   Calculate profit and loss, and update the daily returns and AUM:

Click to see the Python Code

Python

```
        gross_pnl = np.sum(exposure * current_close_prices.diff()) * shares
        commission_paid = trades_count * max(min_comm_per_order, commission * shares)
        net_pnl = gross_pnl - commission_paid
        strat.loc[current_day, 'AUM'] = previous_aum + net_pnl
        strat.loc[current_day, 'ret'] = net_pnl / previous_aum
```

#### **3.8 Record Passive Buy&Hold Returns**

-   Record the passive Buy&Hold returns for comparison:

Click to see the Python Code

Python

```
        strat.loc[current_day, 'ret_spy'] = df_daily.loc[df_daily.index == current_day, 'ret'].values[0]
```

And that's it, our backtesting is done! lets see the results in the next step.

**Step 4: Study Results**
-------------------------

### **Overview**

In this step, we analyze the results of the trading strategy by visualizing the growth of Assets Under Management (AUM) over time for both the strategy and a passive investment in the S&P 500. Additionally, we compute various performance metrics to assess the strategy's effectiveness.

### **Step 4 Code:**

Click to see the Python Code

Python

```
# Calculate cumulative products for AUM calculations
strat['AUM_SPX'] = AUM_0 * (1 + strat['ret_spy']).cumprod(skipna=True)

# Create a figure and a set of subplots
fig, ax = plt.subplots()

# Plotting the AUM of the strategy and the passive S&P 500 exposure
ax.plot(strat.index, strat['AUM'], label='Momentum', linewidth=2, color='k')
ax.plot(strat.index, strat['AUM_SPX'], label='S&P 500', linewidth=1, color='r')

# Formatting the plot
ax.grid(True, linestyle=':')
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
plt.xticks(rotation=90)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax.set_ylabel('AUM ($)')
plt.legend(loc='upper left')
plt.title('Intraday Momentum Strategy', fontsize=12, fontweight='bold')
plt.suptitle(f'Commission = ${commission}/share', fontsize=9, verticalalignment='top')

# Show the plot
plt.show()

# Calculate additional stats and display them
stats = {
    'Total Return (%)': round((np.prod(1 + strat['ret'].dropna()) - 1) * 100, 0),
    'Annualized Return (%)': round((np.prod(1 + strat['ret']) ** (252 / len(strat['ret'])) - 1) * 100, 1),
    'Annualized Volatility (%)': round(strat['ret'].dropna().std() * np.sqrt(252) * 100, 1),
    'Sharpe Ratio': round(strat['ret'].dropna().mean() / strat['ret'].dropna().std() * np.sqrt(252), 2),
    'Hit Ratio (%)': round((strat['ret'] > 0).sum() / (strat['ret'].abs() > 0).sum() * 100, 0),
    'Maximum Drawdown (%)': round(strat['AUM'].div(strat['AUM'].cummax()).sub(1).min() * -100, 0)
}

Y = strat['ret'].dropna()
X = sm.add_constant(strat['ret_spy'].dropna())
model = sm.OLS(Y, X).fit()
stats['Alpha (%)'] = round(model.params.const * 100 * 252, 2)
stats['Beta'] = round(model.params['ret_spy'], 2)

print(stats)

```

#### **4.1 AUM Calculation for Active and Passive S&P 500 Exposure**

-   Compute the cumulative product of the returns, which represents the growth of the initial investment (AUM) over time.

Click to see the Python Code

Python

```
# Calculate the cumulative AUM for the strategy and S&P 500
strat['AUM_SPX'] = AUM_0 * (1 + strat['ret_spy']).cumprod(skipna=True)
```

#### **4.2 Plotting AUM**

-   Use **`matplotlib`** to create a plot that shows how the AUM

![Backtesting Beat_The_Market using Python results](https://concretumgroup.com/wp-content/uploads/2024/05/image-18.png)

Click to see the Python Code

Python

```
# Set up the plot
fig, ax = plt.subplots()

# Plot the AUM for both the strategy and the passive S&P 500
ax.plot(strat.index, strat['AUM'], label='Momentum', linewidth=2, color='k')
ax.plot(strat.index, strat['AUM_SPX'], label='S&P 500', linewidth=1, color='r')

# Grid and date formatting
ax.grid(True, linestyle=':')
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
plt.xticks(rotation=90)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax.set_ylabel('AUM ($)')
plt.legend(loc='upper left')
plt.title('Intraday Momentum Strategy', fontsize=12, fontweight='bold')
plt.suptitle(f'Commission = ${commission}/share', fontsize=9, verticalalignment='top')
plt.show()

```

#### **4.3 Calculate Additional Statistics**

-   Compute various statistics to evaluate the performance of the trading strategy in comparison to a passive investment. These include total return, annualized return, volatility, Sharpe ratio, hit rate, maximum drawdown, and regression analysis for alpha and beta.

Click to see the Python Code

Python

```
# Calculating key performance metrics for the strategy
stats = {
    'Total Return (%)': round((np.prod(1 + strat['ret'].dropna()) - 1) * 100, 0),
    'Annualized Return (%)': round((np.prod(1 + strat['ret'].dropna()) ** (252 / len(strat['ret'].dropna())) - 1) * 100, 1),
    'Annualized Volatility (%)': round(strat['ret'].dropna().std() * np.sqrt(252) * 100, 1),
    'Sharpe Ratio': round(strat['ret'].dropna().mean() / strat['ret'].dropna().std() * np.sqrt(252), 2),
    'Hit Ratio (%)': round((strat['ret'] > 0).sum() / (strat['ret'].abs() > 0).sum() * 100, 0),
    'Maximum Drawdown (%)': round(strat['AUM'].div(strat['AUM'].cummax()).sub(1).min() * -100, 0)
}
```

#### **4.4 Regression Analysis for Alpha and Beta**

-   Regression analysis to determine the strategy's alpha (performance relative to a benchmark) and beta (quantifies the sensitivity of an asset's returns to the movements of the overall market).

Click to see the Python Code

Python

```
# Prepare data for regression
Y = strat['ret'].dropna()
X = sm.add_constant(strat['ret_spy'].dropna())

# Conduct linear regression
model = sm.OLS(Y, X).fit()

# Extract alpha and beta from the regression results
stats['Alpha (%)'] = round(model.params.const * 100 * 252, 2)
stats['Beta'] = round(model.params['ret_spy'], 2)

```

#### **Results**

-   **Total Return** (%): 79.0,
-   **Annualized Return** (%): 35.8,
-   **Annualized Volatility** (%): 13.0,
-   **Sharpe Ratio**: 2.42,
-   **Hit Rate** (%): 50.0,
-   **Maximum Drawdown** (%): 6.0,
-   **Alpha** (%): 30.66,
-   **Beta**: 0.07

**Full Code and Final Words**
-----------------------------

**You can try the code online for free using Google Colab!**

![](https://concretumgroup.com/wp-content/uploads/2024/05/image-19.png)

**Click on the Following Link:**

##### **[Google Colab : Beat the Market: An Effective Intraday Momentum Strategy for the S&P500 ETF (SPY)](https://colab.research.google.com/drive/1sYvAU_c9gLpc7hXtbrn2TBFIAVg9KulQ?usp=sharing)**