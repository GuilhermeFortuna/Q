# Optimizer

Optuna-based optimization utilities for trading strategies.

This package provides a simple Optimizer class that runs studies over a parameter space for a given TradingStrategy, using the backtester Engine to evaluate performance.

## Installation

Part of the workspace:

```
uv sync
```

## Concept

- You pass:
  - strategy_class: a class deriving from backtester.TradingStrategy
  - config: defines parameter space, number of trials, target metric and direction
  - backtest_settings: settings forwarded to the backtester Engine
- The Optimizer runs an Optuna study, instantiating the strategy with suggested parameters and evaluating a chosen metric.

## API

- class Optimizer(strategy_class, config, backtest_settings)
  - run() -> optuna.study.Study: executes the optimization study

Parameter space format (example):

```python
config = {
    "parameters": {
        "short_ma_period": {"type": "int", "min": 5, "max": 30, "step": 1},
        "long_ma_period": {"type": "int", "min": 10, "max": 100, "step": 1},
        "delta_tick_factor": {"type": "float", "min": 0.5, "max": 3.0, "step": 0.1},
        "short_ma_func": {"type": "categorical", "choices": ["ema", "sma", "jma"]},
    },
    "n_trials": 50,
    "metric": "total_profit",     # key in the registry summary to optimize
    "direction": "maximize",       # or "minimize"
}
```

## Usage sketch

```python
from src.optimizer.engine import Optimizer
from src.strategies.swingtrade.ma_crossover import MaCrossover

backtest_settings = {
    # Engine kwargs as used in your backtester.Engine
}

opt = Optimizer(
    strategy_class=MaCrossover,
    config=config,
    backtest_settings=backtest_settings,
)
study = opt.run()
print("Best params:", study.best_trial.params)
```

Notes:
- The exact Engine API and registry summary keys may differ based on your backtester implementation. Adjust backtest_settings and metric accordingly.
