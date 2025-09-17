# Strategies

Strategy implementations and a composable signal architecture used with the backtester.

## Overview

- CompositeStrategy: Aggregates multiple TradingSignal components into a single strategy decision.
- Signals: Reusable building blocks (e.g., MaCrossoverSignal, BollingerBandSignal) that produce directional decisions with strengths.
- Swingtrade: Backward-compatible MaCrossover strategy that internally uses the signals architecture.

Packages:
- signals/: signal primitives and helpers
- swingtrade/: concrete swing trading strategies (e.g., MaCrossover)
- daytrade/: placeholder for day trading strategies

## Installation

Part of the workspace:

```
uv sync
```

## Quick examples

1) Classic MA crossover (backward-compatible class)
```python
from src.backtester.engine import Engine, BacktestParameters
from src.backtester.data import CandleData
from src.strategies.swingtrade.ma_crossover import MaCrossover

# Prepare data
candles = CandleData(symbol="DOL$", timeframe="M5")
# candles.data = CandleData.import_from_mt5(...)
# or: candles.data = CandleData.import_from_csv("path.csv")

# Build strategy and engine
strategy = MaCrossover(
    tick_value=0.5,
    short_ma_func="ema",
    long_ma_func="sma",
    short_ma_period=9,
    long_ma_period=21,
    delta_tick_factor=2.0,
    always_active=True,
)
params = BacktestParameters(point_value=450.0, cost_per_trade=2.5)
engine = Engine(parameters=params, strategy=strategy, data={"candle": candles})
results = engine.run_backtest(display_progress=True)
print(results.get_result())
```

2) Composing signals with CompositeStrategy
```python
from src.strategies.composite import CompositeStrategy
from src.strategies.signals import MaCrossoverSignal, BollingerBandSignal

signals = [
    MaCrossoverSignal(tick_value=0.5, short_ma_period=9, long_ma_period=21),
    BollingerBandSignal(length=20, std=2.0),
]
strategy = CompositeStrategy(signals=signals, always_active=True)
```

## Notes

- The MaCrossover class preserves the original public API but is implemented using signals internally.
- See scripts/backtest/ for runnable end-to-end examples.
