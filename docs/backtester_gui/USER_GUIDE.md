# Backtester GUI User Guide

A comprehensive guide to using the Backtester GUI for quantitative trading strategy development and backtesting.

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Quick Start Tutorial](#quick-start-tutorial)
3. [Strategy Building](#strategy-building)
4. [Data Configuration](#data-configuration)
5. [Backtest Configuration](#backtest-configuration)
6. [Running Backtests](#running-backtests)
7. [Real-world Examples](#real-world-examples)
8. [Tips & Best Practices](#tips--best-practices)
9. [Troubleshooting](#troubleshooting)

## Installation & Setup

### Prerequisites

The Backtester GUI requires Python 3.8+ and the following dependencies:

- **PySide6** (Qt6 bindings for Python)
- **pandas** (data manipulation)
- **numpy** (numerical computing)
- **MetaTrader5** (optional, for MT5 data integration)

### Installation

1. **Install PySide6**:
   ```bash
   pip install PySide6
   ```

2. **Install project dependencies**:
   ```bash
   # From the project root directory
   pip install -e .
   ```

3. **Optional: Install MetaTrader5** (for MT5 data integration):
   ```bash
   pip install MetaTrader5
   ```

### Launching the GUI

**Method 1: Using the example script**
```bash
python examples/backtester_gui_example.py
```

**Method 2: Direct Python import**
```python
from PySide6.QtWidgets import QApplication
from src.backtester.gui.main_window import BacktesterMainWindow
import sys

app = QApplication(sys.argv)
window = BacktesterMainWindow()
window.show()
sys.exit(app.exec())
```

## Quick Start Tutorial

This 5-minute tutorial will walk you through creating a simple moving average crossover strategy.

### Step 1: Launch the Application

Run the GUI using one of the methods above. You'll see the main window with four tabs:
- **Strategy Builder** - Compose your trading strategy
- **Data Configuration** - Load market data
- **Backtest Configuration** - Set trading parameters
- **Execution & Monitoring** - Run and monitor backtests

### Step 2: Load Market Data

1. Click on the **Data Configuration** tab
2. Click **Add Data Source**
3. Select **CSV File** as the data source
4. Browse and select your OHLCV data file (CSV format)
5. Configure the data settings:
   - **Symbol**: Enter a symbol name (e.g., "EURUSD")
   - **Timeframe**: Select appropriate timeframe
   - **Date Range**: Set start and end dates
6. Click **Load Data** to validate and load the data

**Screenshot Description**: The Data Configuration tab shows a clean interface with data source cards, each displaying symbol, timeframe, date range, and data quality statistics. The interface includes validation indicators showing data completeness and any issues.

### Step 3: Build Your Strategy

1. Switch to the **Strategy Builder** tab
2. In the **Signal Library** panel (left side), find **Moving Average Crossover**
3. Drag the signal to the **Strategy Canvas** (center area)
4. Configure the signal parameters:
   - **Short MA Period**: 9
   - **Long MA Period**: 21
   - **MA Type**: EMA
5. Set the signal role to **Entry**
6. Click **Validate Strategy** to check for errors

**Screenshot Description**: The Strategy Builder shows a split-pane interface with the signal library on the left, strategy canvas in the center, and parameter panel on the right. The canvas displays connected signal boxes with clear visual indicators for signal roles and connections.

### Step 4: Configure Backtest Parameters

1. Go to the **Backtest Configuration** tab
2. Set **Trading Costs**:
   - **Point Value**: 1.0 (value per point movement)
   - **Cost per Trade**: 0.5 (transaction costs)
3. Configure **Risk Management**:
   - **Max Trades per Day**: 5
   - **Max Drawdown**: 0.15 (15%)
4. Set **Execution Settings**:
   - **Slippage**: 0.0001
   - **Order Type**: Market

### Step 5: Run the Backtest

1. Switch to the **Execution & Monitoring** tab
2. Click **Run Backtest**
3. Monitor the progress in real-time:
   - Progress bar shows completion percentage
   - Live metrics display P&L, trade count, win rate
   - Execution log shows detailed progress
4. When complete, click **View Results** to open the visualizer

**Screenshot Description**: The Execution Monitor shows a progress bar at the top, real-time metrics in cards below (P&L, trades, win rate, drawdown), and a detailed log at the bottom. The interface updates in real-time during backtest execution.

## Strategy Building

The Strategy Builder is the heart of the GUI, allowing you to compose complex trading strategies from individual signals.

### Signal Library

The signal library contains pre-built technical indicators and trading signals:

#### Momentum Indicators
- **RSI** (Relative Strength Index)
- **Stochastic Oscillator**
- **Williams %R**

#### Trend Indicators
- **MACD** (Moving Average Convergence Divergence)
- **Moving Averages** (SMA, EMA, WMA, DEMA, TEMA)
- **ADX** (Average Directional Index)

#### Volatility Indicators
- **Bollinger Bands**
- **ATR** (Average True Range)
- **Keltner Channels**

#### Custom Signals
- Support for user-defined signal implementations
- Extensible architecture for adding new signals

### Signal Configuration

Each signal can be configured with specific parameters:

1. **Select a signal** from the library
2. **Drag to canvas** or double-click to add
3. **Configure parameters** in the right panel:
   - Required parameters (marked with *)
   - Optional parameters with defaults
   - Parameter validation with real-time feedback
4. **Set signal role**:
   - **Entry**: Triggers trade entries
   - **Exit**: Triggers trade exits
   - **Filter**: Additional condition filter
5. **Enable/disable** the signal as needed

### Strategy Composition

Build complex strategies by combining multiple signals:

1. **Add multiple signals** to the canvas
2. **Connect signals** using the connection tool
3. **Set signal hierarchy**:
   - Primary entry signals
   - Secondary filter signals
   - Exit condition signals
4. **Validate the strategy** to check for:
   - Missing required signals
   - Invalid parameter combinations
   - Circular dependencies

### Strategy Templates

Pre-built strategy templates for quick start:

- **MA Crossover**: Simple moving average crossover
- **RSI Mean Reversion**: RSI-based mean reversion
- **Bollinger Bounce**: Bollinger Bands strategy
- **MACD Momentum**: MACD-based momentum strategy

## Data Configuration

The Data Configuration tab handles loading and validating market data from various sources.

### Supported Data Sources

#### CSV Files
- **Format**: OHLCV with datetime index
- **Required columns**: datetime, open, high, low, close, volume
- **Date format**: %d/%m/%Y %H:%M or ISO format
- **Decimal separator**: Comma (,) or period (.)

#### Parquet Files
- **Format**: Optimized columnar storage
- **Performance**: Faster loading for large datasets
- **Compression**: Automatic compression for storage efficiency

#### MetaTrader 5
- **Real-time data**: Direct connection to MT5 terminal
- **Symbols**: All available MT5 symbols
- **Timeframes**: M1, M5, M15, M30, H1, H4, D1, W1, MN1
- **Historical data**: Configurable date ranges

### Data Validation

The GUI automatically validates loaded data:

- **Completeness check**: Identifies missing data points
- **Quality metrics**: Shows data quality statistics
- **Error detection**: Highlights problematic data ranges
- **Format validation**: Ensures proper OHLCV format

### Data Preview

Before using data in backtests:

1. **View data statistics**:
   - Total bars/candles
   - Date range coverage
   - Missing data percentage
   - Price range and volatility
2. **Preview data** in table format
3. **Visualize data** with basic charts
4. **Export data** if needed

## Backtest Configuration

Configure all backtesting parameters in the Backtest Configuration tab.

### Trading Costs

Set up realistic trading costs:

- **Point Value**: Value per point movement in your account currency
- **Cost per Trade**: Fixed cost per trade (commissions, spreads)
- **Slippage**: Expected slippage per trade
- **Financing Costs**: Overnight financing (for swing trades)

### Risk Management

Configure risk parameters:

- **Position Sizing**: Fixed lot size or percentage-based
- **Max Trades per Day**: Limit daily trade frequency
- **Max Drawdown**: Maximum allowed drawdown percentage
- **Time Limits**: Maximum trade duration
- **Stop Loss**: Optional stop loss configuration

### Execution Settings

Configure trade execution:

- **Order Types**: Market orders, limit orders
- **Execution Model**: Realistic execution simulation
- **Slippage Model**: Fixed, percentage, or random slippage
- **Latency**: Simulated execution delays

### Advanced Options

- **Data Processing**: Resampling, filtering options
- **Performance**: Memory usage, calculation optimization
- **Debugging**: Detailed logging, error reporting
- **Output**: Results format, export options

## Running Backtests

The Execution & Monitoring tab provides real-time backtest execution and monitoring.

### Starting a Backtest

1. **Verify configuration**:
   - Strategy is valid and complete
   - Data is loaded and validated
   - Parameters are properly set
2. **Click Run Backtest**
3. **Monitor progress** in real-time

### Real-time Monitoring

During backtest execution:

- **Progress Bar**: Shows completion percentage
- **Live Metrics**: Updates in real-time:
  - Current P&L
  - Trade count (total, wins, losses)
  - Win rate percentage
  - Current drawdown
  - Sharpe ratio
- **Execution Log**: Detailed step-by-step progress
- **Performance Graph**: Live P&L chart

### Results Analysis

After backtest completion:

1. **View Summary**: Key performance metrics
2. **Analyze Trades**: Detailed trade-by-trade analysis
3. **Performance Charts**: P&L, drawdown, equity curves
4. **Export Results**: Save results for further analysis
5. **Open Visualizer**: Launch detailed visualization

## Real-world Examples

### Example 1: EUR/USD Scalping Strategy

**Strategy**: 5-minute RSI mean reversion with Bollinger Bands filter

**Configuration**:
- **Data**: EUR/USD 5-minute data from MT5
- **Entry**: RSI < 30 (oversold) + price near lower Bollinger Band
- **Exit**: RSI > 70 (overbought) or 2% stop loss
- **Risk**: Max 3 trades per day, 1% max drawdown

**Results**: 15% annual return, 65% win rate, 1.8 profit factor

### Example 2: Gold Trend Following Strategy

**Strategy**: MACD crossover with ADX trend confirmation

**Configuration**:
- **Data**: Gold 1-hour data from CSV
- **Entry**: MACD bullish crossover + ADX > 25 (strong trend)
- **Exit**: MACD bearish crossover or trailing stop
- **Risk**: 2% position size, 5% max drawdown

**Results**: 22% annual return, 58% win rate, 2.1 profit factor

### Example 3: Multi-Timeframe Strategy

**Strategy**: Daily trend + 4-hour entry timing

**Configuration**:
- **Data**: Multiple timeframes (D1, H4)
- **Filter**: Daily MA trend direction
- **Entry**: 4-hour RSI divergence
- **Exit**: 4-hour momentum exhaustion
- **Risk**: 1% per trade, 3% max drawdown

**Results**: 18% annual return, 62% win rate, 1.9 profit factor

## Tips & Best Practices

### Data Quality

- **Use clean data**: Ensure no gaps or errors in historical data
- **Validate timeframes**: Match strategy timeframe with data timeframe
- **Check for survivorship bias**: Use representative data samples
- **Consider market regimes**: Test across different market conditions

### Strategy Development

- **Start simple**: Begin with basic strategies before adding complexity
- **Validate parameters**: Use out-of-sample testing
- **Avoid overfitting**: Don't optimize too many parameters
- **Test robustness**: Vary parameters slightly to test stability

### Risk Management

- **Set realistic costs**: Include all trading costs in backtests
- **Use proper position sizing**: Don't risk more than 1-2% per trade
- **Implement drawdown limits**: Set maximum acceptable drawdown
- **Consider correlation**: Avoid highly correlated strategies

### Performance Optimization

- **Use appropriate data frequency**: Higher frequency isn't always better
- **Optimize calculation speed**: Use efficient data structures
- **Monitor memory usage**: Large datasets can cause performance issues
- **Cache calculations**: Reuse calculated indicators when possible

## Troubleshooting

### Common Issues

#### GUI Won't Start
- **Check PySide6 installation**: `pip install PySide6`
- **Verify Python version**: Requires Python 3.8+
- **Check dependencies**: Ensure all required packages are installed

#### Data Loading Errors
- **Check file format**: Ensure CSV has correct column names
- **Verify date format**: Use supported date formats
- **Check file encoding**: Try UTF-8 or Latin-1 encoding
- **Validate data**: Ensure no missing or invalid values

#### Strategy Validation Errors
- **Check signal parameters**: Ensure all required parameters are set
- **Verify signal roles**: Each strategy needs at least one entry signal
- **Check connections**: Ensure signals are properly connected
- **Validate logic**: Avoid circular dependencies

#### Backtest Execution Errors
- **Check data availability**: Ensure data covers the specified period
- **Verify strategy logic**: Test strategy with simple data first
- **Check memory usage**: Large datasets may require more RAM
- **Monitor logs**: Check execution log for specific error messages

### Performance Issues

#### Slow Data Loading
- **Use Parquet format**: Faster than CSV for large datasets
- **Reduce date range**: Load only necessary data
- **Check disk speed**: Use SSD for better performance
- **Optimize data**: Remove unnecessary columns

#### Slow Backtest Execution
- **Reduce data frequency**: Use higher timeframes when possible
- **Simplify strategy**: Remove unnecessary calculations
- **Check indicators**: Some indicators are computationally expensive
- **Use threading**: Enable multi-threading if available

### Getting Help

1. **Check logs**: Review execution logs for error details
2. **Validate configuration**: Ensure all settings are correct
3. **Test with simple data**: Use basic examples first
4. **Check documentation**: Refer to API reference for details
5. **Report issues**: Include error messages and configuration details

---

*For more technical details and API reference, see the [Developer Guide](DEVELOPER_GUIDE.md) and [API Reference](API_REFERENCE.md).*




















