# PyQuant Backtester

A Python framework for defining, backtesting, and analyzing trading strategies on historical market data.

## Overview

This package provides a comprehensive set of tools to simulate trading strategies against historical price data. It is designed to be flexible and extensible, allowing users to define their own custom strategies, handle various data sources, and analyze the performance of their backtests in detail.

## Installation

This package is configured with `pyproject.toml` and can be installed using:

```bash
uv add backtester
```
### Dependencies

- `metatrader5>=5.0.5200` - MT5 connectivity
- `numpy>=1.26.4` - Numerical computations
- `tqdm>=4.67.1` - Progress bars

## Core Components

The framework is built around five main modules:

### 1. Data (`data.py`)

This module handles market data ingestion and processing:

- **`MarketData`**: Abstract base class for all market data types with MT5 connection functionality
- **`CandleData`**: Manages OHLCV (Open, High, Low, Close, Volume) candle data
  - Imports from MT5 using `import_from_mt5()` 
  - Imports from CSV using `import_from_csv()`
  - Formats MT5 data with `format_candle_data_from_mt5()`
- **`TickData`**: Handles tick-level data for granular backtests
  - Supports batch imports for large datasets
  - Configurable batch size with `DEFAULT_BATCH_IMPORT_STEP_DAYS`

### 2. Strategy (`strategy.py`)

Defines the trading strategy interface:

- **`TradingStrategy`**: Abstract base class requiring implementation of:
  - `compute_indicators(data)` - Calculate technical indicators
  - `entry_strategy(i, data)` - Define entry conditions
  - `exit_strategy(i, data, trade_info)` - Define exit conditions

Implementations of this interface (like moving average crossover or RSI-based strategies) should be housed in a separate `strategies` package.

### 3. Engine (`engine.py`)

The backtesting execution engine:
- **`BacktestParameters`**: Configuration dataclass with:
  - `point_value` - Value per point movement
  - `cost_per_trade` - Transaction costs
  - `permit_swingtrade` - Allow swing trades
  - Time limits: `entry_time_limit`, `exit_time_limit`
  - `max_trade_day` - Maximum trade duration
  - `bypass_first_exit_check` - Skip initial exit check
- **`Engine`**: Core backtesting engine
  - Supports candle and tick data types
  - Progress tracking with `display_progress` option
  - Integrates with bridge module for result sharing
- **`EngineData`** classes: Handle data compartmentalization for processing

### 4. Trades (`trades.py`)

Trade management and performance analysis:

- **`TradeOrder`**: Represents individual trade orders with:
  - Type: 'buy', 'sell', 'close', 'invert'
  - Price, datetime, amount, slippage, comments
  - New: optional `info: dict | None` — used by composite strategies to attach contextual info (e.g., labeled signal decisions per entry/exit check)
- **`TradeRegistry`**: Comprehensive trade tracking and analysis
  - Real-time position management
  - Performance metrics: profit factor, accuracy, drawdown
  - Monthly result computation with tax calculations
  - Brazilian tax rates: 15% swing trade, 20% day trade
  - New DataFrame columns `entry_info` and `exit_info` — persist the `TradeOrder.info` payloads for the orders that opened/closed/inverted a position

### 5. Utils (`utils.py`)

Utility functions and constants:

- **`TIMEFRAMES`**: MT5 timeframe mappings with delta calculations
- **`MARKET_DATA_LAYOUT`**: Plotly chart layout configuration
- **`TimeframeInfo`**: Named tuple for timeframe metadata

## Architecture

The backtesting process follows this workflow:

1. **Data Loading**: `CandleData` or `TickData` loads historical market data
2. **Strategy Definition**: Custom or built-in strategies inherit from `TradingStrategy`
3. **Engine Configuration**: `Engine` combines data, strategy, and parameters
4. **Execution**: `run_backtest()` iterates through data, executing strategy logic
5. **Analysis**: `TradeRegistry` provides comprehensive performance metrics

## API Surface

### Key Classes
- `CandleData(symbol, timeframe, data=None)`
- `TickData(symbol, data=None)`
- `TradingStrategy()` - Abstract base class
- `MaCrossover(tick_value, short_ma_func, short_ma_period, long_ma_func, long_ma_period, delta_tick_factor, always_active)`
- `BacktestParameters(point_value, cost_per_trade, **kwargs)`
- `Engine(parameters, strategy, data)`
- `TradeOrder(type, price, datetime, comment="", amount=None, slippage=None)`
- `TradeRegistry(point_value, cost_per_trade)`

### Key Methods
- `engine.run_backtest(display_progress=False)` - Execute backtest
- `registry.get_result()` - Get performance metrics
- `CandleData.import_from_csv(path)` - Load CSV data
- `CandleData.import_from_mt5(symbol, timeframe, date_from, date_to)` - Load MT5 data

## Configuration

The `BacktestParameters` class accepts the following configuration:

- **Required**: `point_value` (float), `cost_per_trade` (float)
- **Optional**: `permit_swingtrade` (bool), time limits, trade duration limits

## Data I/O

### CSV Format
Expected columns: `datetime`, `open`, `high`, `low`, `close`, `volume`
- Date format: `%d/%m/%Y %H:%M`
- Decimal separator: `,` (comma)
- Encoding: UTF-8 or Latin-1

### MT5 Integration
- Direct connection to MetaTrader 5 terminal
- Automatic data formatting and cleanup
- Connection retry logic with configurable attempts

## Usage Example

```python
from src.backtester.data import CandleData
from src.strategies.swingtrade.ma_crossover import MaCrossover
from src.backtester.engine import Engine, BacktestParameters

# Load data
candles = CandleData(symbol='MSFT', timeframe='60min')
candles.data = CandleData.import_from_csv('path/to/data.csv')

# Configure strategy
strategy = MaCrossover(
    tick_value=0.01,
    short_ma_func='ema',
    short_ma_period=9,
    long_ma_func='sma',
    long_ma_period=21,
    delta_tick_factor=2.0,
    always_active=True
)

# Set up engine
params = BacktestParameters(point_value=450.00, cost_per_trade=2.50)
engine = Engine(parameters=params, strategy=strategy, data={'candle': candles})

# Run backtest
results = engine.run_backtest(display_progress=True)
performance = results.get_result()
```

### Reading decision labels from trades

```python
from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.strategies.archetypes import create_momentum_rider_strategy

# Minimal setup
candles = CandleData(symbol="WDO", timeframe="15min")
# candles.data = <your OHLCV DataFrame>
params = BacktestParameters(point_value=10.0, cost_per_trade=1.0)
strategy = create_momentum_rider_strategy()
engine = Engine(parameters=params, strategy=strategy, data={"candle": candles})
results = engine.run_backtest(display_progress=False)

# After the backtest
trades = results.trades  # TradeRegistry DataFrame
for i, row in trades.iterrows():
    entry_meta = row.get("entry_info") if hasattr(row, "get") else row["entry_info"]
    decisions = (entry_meta or {}).get("decisions", []) if isinstance(entry_meta, dict) else []
    print(f"Trade #{i+1} type={row['type']}:")
    for d in decisions:
        print(f"  - {d.get('label')}: {d.get('side')} (strength={float(d.get('strength', 0.0)):.2f})")
```

See `scripts\backtest\composites\` for examples that print this analysis.

## CLI Examples

Sample scripts are available in `scripts/backtest/`:
- `ccm_test.py` - CCM futures backtest example
- `dol_test.py` - DOL futures backtest example

## Testing

The package includes comprehensive validation:
- Type checking for all parameters
- Data format validation
- Connection error handling
- Performance metric calculations

## Integration

Results are automatically stored in the bridge module's `data_manager` for integration with visualization components and other system modules.

## Performance Metrics

The `TradeRegistry` calculates:
- **P&L**: Net/gross balance, total profit/loss, costs, taxes
- **Performance**: Profit factor, accuracy, mean profit/loss ratios
- **Risk**: Maximum drawdown (absolute and relative)
- **Trade Statistics**: Total/positive/negative trade counts
- **Time Analysis**: Duration, monthly results, average monthly performance

## Automated Strategy Evaluation (Gate + Score)

Use `backtester.evaluation` to encode what “acceptable” means and to rank strategies consistently.

- Acceptance gate: fast hard rules to reject weak/fragile runs (e.g., min trades, max drawdown, min PF).
- Composite score: normalized 0..1 score combining profit factor, drawdown, Sharpe, CAGR, trade count, etc.
- Labeling: A/B/C for accepted runs, REJECT for failed gates.

Example:

```python
from src.backtester import (
    Engine, BacktestParameters, CandleData,
    AcceptanceCriteria, StrategyEvaluator, metrics_from_trade_registry,
)

# 1) Prepare data and engine
data = CandleData(symbol="TEST", timeframe="15min")
# data.data = <OHLCV DataFrame with datetime index>
params = BacktestParameters(point_value=10.0, cost_per_trade=1.0)
engine = Engine(parameters=params, strategy=my_strategy, data={"candle": data})
reg = engine.run_backtest(display_progress=False)

# 2) Evaluate
criteria = AcceptanceCriteria(
    min_trades=200, min_profit_factor=1.3, max_drawdown=0.20, min_sharpe=1.0
)
evaluator = StrategyEvaluator(criteria)
metrics = metrics_from_trade_registry(reg)
result = evaluator.evaluate(metrics)
print(result.label, result.score, result.reasons)
```

Out-of-sample stability (optional): run the strategy on IS/OOS splits and penalize instability via `oos_stability` in metrics. A helper is available:

```python
from src.backtester.evaluation import oos_stability_from_two_runs
m_is = metrics_from_trade_registry(reg_is)
m_oos = metrics_from_trade_registry(reg_oos)
stability = oos_stability_from_two_runs(reg_is, reg_oos, evaluator)
# Inject and re-evaluate
m_is["oos_stability"] = stability
result = evaluator.evaluate(m_is)
```

Integration with Optuna: optimize to maximize `result.score` and prune trials that fail the gate (see optimizer README for a sketch).

## Roadmap

- [ ] Multiprocessing support for distributed backtesting
- [ ] Additional technical indicators
- [ ] Portfolio-level backtesting
- [ ] Risk management modules
- [ ] Advanced order types
- [ ] Real-time strategy execution
