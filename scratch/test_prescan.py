import pandas as pd
from backtest_engine.strategies.pmax_explorer import vectorbt_prescan
from backtest_engine.configuration import ParameterSpec

df = pd.DataFrame({"close": [1, 2, 3], "high": [2, 3, 4], "low": [0, 1, 2]})

specs = [
    ParameterSpec(name="multiplier", kind="choice", values=[3.0]),
    ParameterSpec(name="length", kind="choice", values=[10]),
]

res = vectorbt_prescan(df, specs, {"periods": 14}, None, None, None, 15, "/tmp")
print("Prescan returned:", len(res), "specs")
