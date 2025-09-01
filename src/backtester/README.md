# PyQuant Backtester

A Python framework for defining, backtesting, and analyzing trading strategies on historical market data.

## Overview

This package provides a comprehensive set of tools to simulate trading strategies against historical price data. It is designed to be flexible and extensible, allowing users to define their own custom strategies, handle various data sources, and analyze the performance of their backtests in detail.

## Core Components

The framework is built around four main components:

### 1. Data (`data.py`)

This module is responsible for handling market data.

*   **`MarketData`**: A base class for handling market data, with functionality for connecting to MetaTrader 5.
*   **`CandleData`**: Manages OHLCV (Open, High, Low, Close, Volume) candle data. It supports importing data from MT5 or CSV files.
*   **`TickData`**: Manages tick-level data for more granular backtests, including tools for importing large datasets in batches from MT5.

### 2. Strategy (`strategy.py`)

This is where the logic of a trading strategy is defined.

*   **`TradingStrategy`**: An abstract base class that all custom strategies must inherit from. It defines the required methods for a strategy: `compute_indicators`, `entry_strategy`, and `exit_strategy`.
*   **`MaCrossover`**: An example implementation of a simple moving average crossover strategy, demonstrating how to build a custom strategy.

### 3. Engine (`engine.py`)

The engine drives the backtest, iterating through historical data and executing the strategy.

*   **`BacktestParameters`**: A data class to configure the simulation, including settings like cost per trade, slippage, and time limits.
*   **`Engine`**: The core of the backtester. It takes the market data, a strategy instance, and backtest parameters, then runs the simulation day by day, calling the strategy's entry and exit logic.

### 4. Trades (`trades.py`)

This component handles the creation and analysis of trade orders.

*   **`TradeOrder`**: Represents a single trade (buy or sell) with details like price, time, and amount.
*   **`TradeRegistry`**: Manages the lifecycle of all trades within a backtest. It registers new orders, tracks open positions, and calculates a comprehensive set of performance metrics, such as:
    *   Net Balance & Profit Factor
    *   Trade Accuracy
    *   Mean Profit/Loss
    *   Maximum Drawdown

## How It Works

The backtesting process follows these steps:

1.  **Load Data**: An instance of `CandleData` or `TickData` is created to load the historical market data for the desired symbol and timeframe.
2.  **Define Strategy**: A custom strategy class is created by inheriting from `TradingStrategy`. The core logic for entering and exiting trades is implemented in the `entry_strategy` and `exit_strategy` methods.
3.  **Configure Engine**: The `Engine` is instantiated with the loaded data, an instance of the custom strategy, and a `BacktestParameters` object.
4.  **Run Backtest**: The `engine.run_backtest()` method is called. The engine iterates through the data, feeding it to the strategy. The strategy, in turn, returns `TradeOrder` objects when its conditions are met.
5.  **Analyze Results**: When the backtest is complete, the `run_backtest` method returns the `TradeRegistry` instance, which contains the full history of trades and a rich set of performance analytics accessible via the `get_result()` method.

## Basic Usage Example

Here is a simplified example of how to set up and run a backtest using the `MaCrossover` strategy.

```python
from src.backtester import CandleData
from src.backtester import MaCrossover
from src.backtester import Engine, BacktestParameters


# 1. Load Data
# Assumes you have a 'MSFT_M5.csv' file with candle data.
msft_data = CandleData( symbol='MSFT', timeframe='M5' )
msft_data.import_from_csv(
    'path/to/your/data/MSFT_M5.csv',
    datetime_col='datetime',
    open_col='open',
    high_col='high',
    low_col='low',
    close_col='close',
    volume_col='volume'
)

# 2. Define Strategy
# Use the built-in moving average crossover strategy
strategy = MaCrossover(
    short_ma_period=20,
    long_ma_period=50
)

# 3. Configure Engine
# Use default parameters for this example
params = BacktestParameters()

# 4. Initialize and Run Engine
engine = Engine(
    strategy=strategy,
    data={'candle': msft_data},
    parameters=params
)

results = engine.run_backtest( display_progress=True )

# 5. Get and print the results
trade_summary = results.get_result()
print( trade_summary )

```
