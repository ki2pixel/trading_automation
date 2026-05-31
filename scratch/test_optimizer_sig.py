import inspect
from backtest_engine.bayesian_optimizer import run_bayesian_optimization
sig = inspect.signature(run_bayesian_optimization)
for name, param in sig.parameters.items():
    print(f"{name}: {param.default}")
