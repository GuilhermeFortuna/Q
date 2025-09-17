# 📊 Q — Python Toolkit for Quantitative Trading

A Python toolkit for quantitative trading research, featuring:

- ⚡ **Backtester** — Event-driven engine for running strategies on OHLCV candles  
- 📈 **Visualizer** — Interactive PySide6 + pyqtgraph windows for charts, trades, and summaries  
- 🔍 **Optimizer** — Hyperparameter search using Optuna  
- 📝 **Scripts** — Ready-to-run examples for data analysis and backtests  

Organized as a **uv workspace** with subpackages under `src/`.

---

## 📜 Table of Contents
<details>
<summary>Click to expand</summary>

- [⚙️ Requirements](#️-requirements)
- [📦 Installation](#-installation)
- [📂 Project Structure](#-project-structure)
- [🚀 Quickstart](#-quickstart)
  - [Example 1 — Backtest DOL$ (5m) with visualization](#example-1--backtest-dol-5m-with-visualization)
  - [Example 2 — Backtest CCM with visualization](#example-2--backtest-ccm-with-visualization)
  - [Example 3 — Plot candlestick with indicators](#example-3--plot-candlestick-with-indicators)
  - [Example 4 — Run composite strategy (Momentum Rider)](#example-4--run-composite-strategy-momentum-rider)
- [🐍 Programmatic Usage](#-programmatic-usage)
  - [Backtest with summary](#backtest-with-summary)
  - [Candlestick + EMA](#candlestick--ema)
  - [Composite Strategy](#composite-strategy)
- [📑 Data Notes](#-data-notes)
- [🛠️ Development](#️-development)

</details>

---

## ⚙️ Requirements

- **Python**: `3.10`  
- **OS**: Windows (recommended for MetaTrader5 data import). Linux/macOS may work if not using MetaTrader5.  
- **Optional**: MetaTrader 5 terminal (for `metatrader5` data import).  

**Key dependencies** (see `pyproject.toml`):  
- pandas, numpy, tqdm, pandas-ta (vendored)  
- PySide6, pyqtgraph  
- Flask (dashboards/services)  
- Optuna (optimization)  
- MetaTrader5 (data acquisition)  

---

## 📦 Installation

This project uses `uv` workspaces (`uv.lock`, `pyproject.toml`). You can install with **uv (recommended)** or **pip**.

### Using uv
```bash
# Install uv if needed → https://docs.astral.sh/uv/
uv sync
```

### Using pip (editable)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

🔑 Notes:
- Python 3.10 required (`requires-python ==3.10.*`).  
- For MetaTrader5: ensure the terminal is installed, logged in, and accessible to the `metatrader5` package.  

---

## 📂 Project Structure

```plaintext
src/
  backtester/    # Core engine, data abstractions, trades, results
  bridge/        # Data management and inter-component communication
  visualizer/    # Interactive plotting windows and UIs
  optimizer/     # Optuna-based optimization components
  strategies/
    signals/       # Modular signals (RSI, ADX/DMI, Supertrend, Donchian, etc.)
    composite.py   # CompositeStrategy for aggregating signals
    combiners.py   # Gated/thresholded/weighted combiners
    archetypes.py  # Prebuilt factories (Momentum Rider, Range Fader, Volatility Breakout)
vendors/
  pandas_ta/     # Vendored pandas-ta
scripts/
  backtest/      # Example backtests
    composites/    # Composite backtests (momentum_rider_test.py, etc.)
  analysis/      # Analysis & plotting scripts
  optimization/  # Optimization utilities
  playground/    # Sandbox & dev scripts
docs/            # Notes & visualizer docs
pyproject.toml   # Project metadata & dependencies
uv.lock          # uv lockfile
```

---

## 🚀 Quickstart

Try these scripts after installation.

### Example 1 — Backtest DOL$ (5m) with visualization
```bash
python scripts\backtest\dol_test.py
```
- Imports OHLCV from MetaTrader5 (last 90 days).  
- Runs an MA crossover strategy.  
- Launches an interactive summary window.  

### Example 2 — Backtest CCM with visualization
```bash
python scripts\backtest\ccm_test.py
```

### Example 3 — Plot candlestick with indicators
```bash
python scripts\analysis\plot_candlestick_with_indicators.py
```

### Example 4 — Run composite strategy (Momentum Rider)
```bash
python scripts\backtest\composites\momentum_rider_test.py
```

---

## 🐍 Programmatic Usage

### Backtest with summary
```python
from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.strategies.swingtrade import MaCrossover
from src.visualizer import show_backtest_summary

candles = CandleData(symbol="DOL$", timeframe="5min")
params = BacktestParameters(point_value=10.0, cost_per_trade=2.50)
strategy = MaCrossover(short_ma_func="ema", short_ma_period=9,
                       long_ma_func="sma", long_ma_period=12,
                       tick_value=0.5, delta_tick_factor=1,
                       always_active=True)

engine = Engine(parameters=params, strategy=strategy, data={"candle": candles})
registry = engine.run_backtest(display_progress=True)
result = registry.get_result()
if result is not None:
    show_backtest_summary(registry, ohlc_df=candles.data.copy())
```

### Candlestick + EMA
```python
import pandas as pd, pandas_ta as pta
from src.visualizer.windows import show_chart, IndicatorConfig

ohlc = pd.DataFrame({...})  # Your OHLCV data
ohlc['ema9'] = pta.ema(ohlc['close'], length=9)

show_chart(ohlc_data=ohlc,
           indicators=[IndicatorConfig(type='line', y=ohlc['ema9'], name='EMA(9)', color='blue')],
           show_volume=True, initial_candles=100)
```

### Composite Strategy
```python
from src.backtester.engine import BacktestParameters, Engine
from src.backtester.data import CandleData
from src.strategies.archetypes import create_momentum_rider_strategy

candles = CandleData(symbol="WDO", timeframe="15min")
params = BacktestParameters(point_value=10.0, cost_per_trade=1.0)
strategy = create_momentum_rider_strategy()

engine = Engine(parameters=params, strategy=strategy, data={"candle": candles})
registry = engine.run_backtest(display_progress=True)
print(registry.trades[["type", "entry_info", "exit_info"]].head())
```

---

## 📑 Data Notes
- **MetaTrader5**: Example scripts assume symbols like `DOL$`, `CCM$`. Adapt as needed.  
- **Custom Data**: Use CSV/Parquet with `open, high, low, close, volume` + datetime index → assign to `CandleData.data`.  

---

## 🛠️ Development

- Style: `black` (line length 88, see `pyproject.toml`).  
- Workspace: `uv` manages `src/backtester`, `src/visualizer`, `src/optimizer`.  
- Vendored: pandas-ta included under `vendors/pandas_ta`.  

### Workflow with uv
```bash
uv sync
uv run python scripts\backtest\dol_test.py
```

### Or with venv
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python scripts\backtest\dol_test.py
```

---

✅ This README now has a collapsible table of contents for easy navigation.
