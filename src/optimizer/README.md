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
    backtest_config=backtest_settings,
)
study = opt.run()
print( "Best params:", study.best_trial.params )
```

## Using the evaluator (gate + score) in Optuna

You can optimize an objective, not just a raw metric, by wiring the backtester evaluator.

```python
import optuna
from src.backtester import (
    Engine, BacktestParameters, CandleData,
    AcceptanceCriteria, StrategyEvaluator, metrics_from_trade_registry,
)

criteria = AcceptanceCriteria(
    min_trades=200,
    min_profit_factor=1.3,
    max_drawdown=0.20,
    min_sharpe=1.0,
)
evaluator = StrategyEvaluator(criteria)


def objective(trial: optuna.trial.Trial) -> float:
    # Suggest params and build your strategy
    params = {
        'short_ma': trial.suggest_int('short_ma', 5, 50),
        'long_ma': trial.suggest_int('long_ma', 20, 200),
    }
    strategy = MyStrategy(**params)

    # Prepare engine (simplified sketch)
    candles = CandleData(symbol='TEST', timeframe='15min')
    candles.data = load_df()
    bt_params = BacktestParameters(point_value=10.0, cost_per_trade=1.0)
    engine = Engine(parameters=bt_params, strategy=strategy, data={'candle': candles})

    # Run backtest
    registry = engine.run_backtest(display_progress=False)

    # Evaluate
    m = metrics_from_trade_registry(registry)
    result = evaluator.evaluate(m)

    # Prune failed gates early to speed up the search
    if not result.passed:
        raise optuna.exceptions.TrialPruned(','.join(result.reasons))

    # Maximize composite score in [0,1]
    return result.score

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=200)
print('Best trial score:', study.best_trial.value)
print('Best params:', study.best_trial.params)
```

This approach scores and classifies each trial consistently, prunes weak candidates, and focuses the search on robust, risk-adjusted performance.

Notes:
- The exact Engine API and registry summary keys may differ based on your backtester implementation. Adjust backtest_settings and metric accordingly.
