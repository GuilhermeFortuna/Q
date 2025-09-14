# q

A Python toolkit for quantitative trading research, featuring:

- Backtester: event-driven engine for running strategies on OHLCV candles
- Visualizer: interactive PySide6 + pyqtgraph windows for charts, trades and summaries
- Optimizer: hyperparameter search using Optuna
- Scripts: ready-to-run examples for data analysis and backtests

This repository is organized as a uv workspace with subpackages under `src/`.

## Requirements

- Python 3.10
- Windows is recommended (MetaTrader5 data import convenience), but Linux/macOS may work for parts that do not rely on MetaTrader5
- Optional: MetaTrader 5 (for `metatrader5` data import)

Key Python dependencies (see `pyproject.toml`):
- pandas, numpy, pandas-ta (vendored), tqdm
- PySide6, pyqtgraph
- Flask (for potential dashboards/services)
- Optuna (optimization)
- MetaTrader5 (data acquisition)

## Installation

The project uses `uv` workspaces (see `uv.lock` and `pyproject.toml`). You can use either uv or pip.

Using uv (recommended):

1) Install uv if you don’t have it yet: https://docs.astral.sh/uv/
2) From the project root:

```
uv sync
```

Using pip (editable):

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Notes:
- Python 3.10 is required (see `requires-python ==3.10.*` in pyproject).
- If you intend to import data from MetaTrader5, ensure the MetaTrader 5 terminal is installed and logged in, and the `metatrader5` Python package can connect.

## Project Structure

```
src/
  backtester/    # Core backtesting engine, data abstractions, trades and results
  visualizer/    # Interactive plotting windows and summary UIs
  optimizer/     # Optuna-based optimization components
  strategies/    # Example strategies (daytrade/swingtrade)
vendors/
  pandas_ta/     # Vendored pandas-ta for technical indicators
scripts/
  backtest/      # Example backtest scripts
  analysis/      # Analysis/plotting scripts
  optimization/  # (If present) optimization utilities
docs/            # Notes and implementation docs for visualizer
pyproject.toml   # Project metadata and dependencies
uv.lock          # uv lockfile
```

## Quickstart

Below are working examples you can run after installing dependencies. These scripts demonstrate importing data, running a simple moving average crossover strategy, and visualizing results.

### Example 1: Backtest DOL$ (5m) with visualization

File: `scripts\backtest\dol_test.py`

What it does:
- Imports OHLCV data from MetaTrader5 for `DOL$` 5-minute bars (last 90 days by default)
- Runs a MA crossover strategy
- Launches an interactive backtest summary window (PySide6 + pyqtgraph)

Run:

```
python scripts\backtest\dol_test.py
```

If you don’t have MetaTrader5 data available, adapt the script to load your own DataFrame (columns: open, high, low, close, volume; index as datetime) into `CandleData`.

### Example 2: Backtest CCM with visualization

File: `scripts\backtest\ccm_test.py`

This example configures a different instrument (CCM) and parameters, then displays the backtest summary:

```
python scripts\backtest\ccm_test.py
```

### Example 3: Plot candlestick with indicators

File: `scripts\analysis\plot_candlestick_with_indicators.py`

Demonstrates computing an EMA(9) with pandas-ta and plotting it on a candlestick chart via the Visualizer API.

Run:

```
python scripts\analysis\plot_candlestick_with_indicators.py
```

## Programmatic Usage

Example: Run MA crossover backtest and show summary in one script:

```python
from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.strategies.swingtrade import MaCrossover
from src.visualizer import show_backtest_summary

# Prepare data (replace with your own loader if not using MT5)
candles = CandleData(symbol="DOL$", timeframe="5min")
# candles.data = <your DataFrame with columns open, high, low, close, volume and datetime index>

# Configure and run backtest
params = BacktestParameters(point_value=10.0, cost_per_trade=2.50)
strategy = MaCrossover(
    tick_value=0.5,
    short_ma_func="ema",
    short_ma_period=9,
    long_ma_func="sma",
    long_ma_period=12,
    delta_tick_factor=1,
    always_active=True,
)
engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
trade_registry = engine.run_backtest(display_progress=True)
result = trade_registry.get_result()

# Show interactive summary
if result is not None:
    ohlc_df = candles.data.copy()
    if 'time' not in ohlc_df.columns:
        ohlc_df.insert(0, 'time', list(range(len(ohlc_df))))
    show_backtest_summary(trade_registry, ohlc_df=ohlc_df)
```

Example: Plot a candlestick chart with an EMA indicator:

```python
import pandas as pd
import pandas_ta as pta
from src.visualizer.windows import show_chart, IndicatorConfig

# Minimal OHLC sample DataFrame; replace with your own OHLCV data
ohlc = pd.DataFrame(
    {
        "open": [1.0, 1.5, 1.2, 1.8],
        "high": [1.6, 1.7, 1.9, 2.1],
        "low": [0.9, 1.1, 1.0, 1.5],
        "close": [1.4, 1.3, 1.8, 2.0],
        "volume": [100, 150, 120, 200],
    }
)

# Compute indicator and plot
ohlc['ema9'] = pta.ema(ohlc['close'], length=9)
indicators = [
    IndicatorConfig(type='line', y=ohlc['ema9'], name='EMA(9)', color='blue'),
]
show_chart(ohlc_data=ohlc, indicators=indicators, show_volume=True, initial_candles=100)
```

## Data Notes

- MetaTrader5: The example scripts assume access to MT5 symbols like `DOL$`/`CCM$`. Replace with your broker/symbol names as needed. Ensure terminal is installed and logged in.
- Custom data: If you have CSV/Parquet data, construct a DataFrame (columns: open, high, low, close, volume) with a datetime index and assign it to `CandleData.data`.

## Development

- Code style: `black` (configured in `pyproject.toml` with line length 88)
- Workspace: `uv` manages `src/backtester`, `src/visualizer`, and `src/optimizer` as members
- Vendored packages: pandas-ta is included under `vendors/pandas_ta`

Recommended workflow with uv:

```
uv sync
uv run python scripts\backtest\dol_test.py
```

Or with a virtual environment:

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python scripts\backtest\dol_test.py
```
