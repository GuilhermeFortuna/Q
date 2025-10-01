# q · Quantitative Trading Research Toolkit ⚡

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/badge/packaging-uv-green.svg)](https://docs.astral.sh/uv/)

A modern, high-performance Python framework for quantitative trading research. `q` provides a complete toolkit to define, backtest, analyze, and optimize trading strategies with a focus on fast iteration and clear, actionable insights.

## 🌟 Why q?

- **Modular by Design**: Easily plug in custom data sources, strategies, execution models, and visualizations.
- **Fast Iteration Loop**: Go from idea to analysis in minutes: Load → Backtest → Visualize → Optimize.
- **Clear Abstractions**: Built with clean, intuitive interfaces for strategies, data models, and the backtesting engine.
- **GUI-First Analysis**: Move beyond raw metrics with interactive charts that provide deeper insights into strategy performance.

## ✨ Core Features

- `🧠` **Event-Driven Backtester**: A powerful engine for simulating strategies on both OHLCV and tick-by-tick data.
- `📈` **Interactive Visualizer**: Built with `PySide6` and `pyqtgraph` to create interactive charts, trade lists, and performance summaries.
- `🎯` **Parameter Optimization**: Integrated with `Optuna` for efficient hyperparameter search to find the best settings for your strategies.
- `🧩` **Composable Strategies**: A sophisticated architecture for building complex strategies by combining smaller, reusable signal components.
- `💾` **Flexible Data Handling**: Natively supports importing data from MetaTrader 5 or loading from local files (CSV, Parquet) into `pandas` DataFrames.

---
<!-- Optional: Add a screenshot of the application -->
<!-- ![Screenshot of q Visualizer](docs/images/backtest_summary.png) -->

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.10`
- **OS**: Windows is recommended for MetaTrader 5 integration. Linux and macOS are fully supported for other data workflows (e.g., CSV, Parquet).
- **Optional**: MetaTrader 5 terminal for live data integration.

**Key Dependencies**:
- `pandas`, `numpy`
- `PySide6`, `pyqtgraph` for visualization
- `Optuna` for optimization
- `pandas-ta` (vendored) for technical indicators

### 📦 Installation

We recommend using `uv` for package management.

1.  **Install uv** (if you don't have it):
    Follow the instructions at [docs.astral.sh/uv/](https://docs.astral.sh/uv/).

2.  **Sync Dependencies**:
    From the project root, run:
    ```sh
    uv sync
    ```

Alternatively, you can use `pip` and a virtual environment:

```sh
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

pip install -e .
```



## 📂 Project Structure

The repository is organized as a `uv` workspace with the core logic contained in the `src/` directory.

```
src/
  backtester/    # Core backtesting engine, data abstractions, trades and results
  bridge/        # Data management and inter-component communication
  visualizer/    # Interactive plotting windows and summary UIs
  optimizer/     # Optuna-based optimization components
  strategies/    # Strategies and composable signal architecture
    signals/       # Modular signals (RSI, ADX/DMI, Supertrend, Donchian, MACD, Keltner, ATR, VWAP, etc.)
    composite.py   # CompositeStrategy to aggregate multiple signals
    combiners.py   # Gated/thresholded/weighted combiners for signal decisions
    archetypes.py  # Prebuilt factories: Momentum Rider, Range Fader, Volatility Breakout
vendors/
  pandas_ta/     # Vendored pandas-ta for technical indicators
scripts/
  backtest/      # Example backtest scripts
    composites/    # Example composite backtests (momentum_rider_test.py, range_fader_test.py, volatility_breakout_test.py)
  analysis/      # Analysis/plotting scripts
  optimization/  # Optimization utilities and examples
  playground/    # Development and testing scripts
docs/            # Notes and implementation docs for visualizer
pyproject.toml   # Project metadata and dependencies
uv.lock          # uv lockfile
```


## ⚡ Quickstart

The `scripts/` directory contains ready-to-run examples.

### Example 1: Basic Backtest & Visualization
This script imports 5-minute data for `DOL$` from MT5, runs a moving average crossover strategy, and launches the interactive summary window.

**Run:**
```textmate
python scripts\backtest\dol_test.py
```

> **Note**: If you don't use MetaTrader 5, you can adapt the script to load your own `pandas` DataFrame.

### Example 2: Run a Composite Strategy
This example assembles multiple signals (e.g., momentum, mean-reversion) into a composite strategy and runs a backtest. It demonstrates how the framework can analyze the contribution of each signal to a trade decision.

**Run:**
```textmate
python scripts\backtest\composites\momentum_rider_test.py
```


### Example 3: Plot Candlesticks with Indicators
This script shows how to use the `visualizer` API to plot a candlestick chart and overlay technical indicators like an EMA.

**Run:**
```textmate
python scripts\analysis\plot_candlestick_with_indicators.py
```


## 💻 Programmatic Usage

You can easily integrate `q`'s components into your own scripts.

### Running a Backtest

Here's how to programmatically configure and run a backtest with a `MaCrossover` strategy and visualize the results.

```python
from src.data.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.strategies.swingtrade import MaCrossover
from src.visualizer import show_backtest_summary

# 1. Prepare Data
# Loads from MT5 by default.
candles = CandleData(symbol="DOL$", timeframe="5min")
# To use your own data:
# candles.data = your_pandas_dataframe

# 2. Configure Backtest
params = BacktestParameters(point_value=10.0, cost_per_trade=2.50)
strategy = MaCrossover(
    tick_value=0.5,
    short_ma_period=9,
    long_ma_period=12,
)
engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))

# 3. Run Simulation
trade_registry = engine.run_backtest(display_progress=True)

# 4. Show Interactive Summary
if trade_registry.get_result() is not None:
    show_backtest_summary(trade_registry, ohlc_df=candles.data)
```


### Plotting a Chart

Create a candlestick chart with a custom indicator.

```python
import pandas as pd
import pandas_ta as pta
from src.visualizer.windows import show_chart, IndicatorConfig

# Create a sample OHLC DataFrame
ohlc = pd.DataFrame({
    "open": [1.0, 1.5, 1.2, 1.8], "high": [1.6, 1.7, 1.9, 2.1],
    "low": [0.9, 1.1, 1.0, 1.5], "close": [1.4, 1.3, 1.8, 2.0],
    "volume": [100, 150, 120, 200],
})

# Compute an indicator
ohlc['ema9'] = pta.ema(ohlc['close'], length=9)

# Define the indicator for the chart
indicators = [
    IndicatorConfig(type='line', y=ohlc['ema9'], name='EMA(9)', color='blue'),
]

# Display the chart
show_chart(ohlc_data=ohlc, indicators=indicators, show_volume=True)
```


## 🗺️ Roadmap

We have an exciting future planned for `q`:

- `🏛️` **Multi-Asset Portfolio Backtesting**: Simulate strategies across a universe of assets.
- `🚶` **Walk-Forward Optimization**: Add tools for robust, out-of-sample validation.
- `⚖️` **Advanced Risk & Position Sizing**: Implement sophisticated capital management modules.
- `📊` **Expanded GUI**: New views for factor attribution, market regime analysis, and in-depth trade reviews.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please feel free to open an issue or submit a pull request.

## 📜 License
```
This project is licensed under the MIT License. See the `LICENSE` file for more information.
```
