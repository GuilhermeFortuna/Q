# Strategies

Strategy implementations and a composable signal architecture used with the backtester.

## Overview

- CompositeStrategy: Aggregates multiple `TradingSignal` components into a single decision.
- Signals package: Ready-to-use building blocks (RSI mean reversion, ADX/DMI, Supertrend, Donchian breakout, MACD momentum, Keltner squeeze, ATR trailing stop, VWAP deviation, Heikin Ashi trend, MTF MA alignment, Choppiness filter, Volume spike/exhaustion, plus helpers).
- Combiners: Classes to combine multiple signal decisions (gated, thresholded, weighted voting) for different decision policies.
- Archetypes: Prebuilt composite strategy factories (Momentum Rider, Range Fader, Volatility Breakout) to speed up experimentation.

## Packages and modules

- signals/            # `TradingSignal` implementations and common helpers
- composite.py        # `CompositeStrategy` and default `weighted_vote` combiner
- combiners.py        # `GatedCombiner`, `ThresholdedWeightedVote`, `WeightedSignalCombiner`
- archetypes.py       # `create_momentum_rider_strategy()`, `create_range_fader_strategy()`, `create_volatility_breakout_strategy()`
- swingtrade/         # Backward-compatible MaCrossover wrapper

## Installation

Part of the workspace:

```
uv sync
```

## Examples

1) Compose signals manually with a combiner

```python
from src.backtester.engine import BacktestParameters, Engine
from src.data.data import CandleData
from src.strategies.composite import CompositeStrategy
from src.strategies.combiners import GatedCombiner
from src.strategies.signals import (
    AdxDmiSignal, SupertrendFlipSignal, DonchianBreakoutSignal,
)


signals = [
    AdxDmiSignal( length=14, adx_thresh=25.0 ),  # filter
    SupertrendFlipSignal( atr_length=10, atr_mult=3.0 ),  # filter
    DonchianBreakoutSignal( breakout_len=20, pullback_len=5 ),  # entry
]
combiner = GatedCombiner( filter_indices=[0, 1], entry_indices=[2], require_all_filters=False )
strategy = CompositeStrategy( signals=signals, combiner=combiner, always_active=True )

candles = CandleData( symbol="WDO", timeframe="15min" )
params = BacktestParameters( point_value=10.0, cost_per_trade=1.0 )
engine = Engine( parameters=params, strategy=strategy, data={"candle": candles} )
registry = engine.run_backtest( display_progress=True )
```

2) Use an archetype factory
```python
from src.strategies.archetypes import create_range_fader_strategy
strategy = create_range_fader_strategy()
```

3) Access labeled decisions from trades

```python
from src.backtester.engine import BacktestParameters, Engine
from src.data.data import CandleData
from src.strategies.archetypes import create_momentum_rider_strategy


# Minimal setup to obtain a TradeRegistry
candles = CandleData( symbol="WDO", timeframe="15min" )
# candles.data = <your OHLCV DataFrame>
params = BacktestParameters( point_value=10.0, cost_per_trade=1.0 )
strategy = create_momentum_rider_strategy()
engine = Engine( parameters=params, strategy=strategy, data={"candle": candles} )
registry = engine.run_backtest( display_progress=False )

# Each trade row includes labeled decisions at entry/exit
trades = registry.trades
print( trades[["type", "entry_info", "exit_info"]].head() )
# Each *_info contains {'decisions': [{'label': 'SignalClass', 'side': 'long|short|None', 'strength': 0..1}, ...]}
```

## Runnable examples

See `scripts\backtest\composites\` for ready-to-run examples:
- momentum_rider_test.py
- range_fader_test.py
- volatility_breakout_test.py

## Notes

- The `MaCrossover` example remains available and now leverages the signals architecture under the hood when applicable.
