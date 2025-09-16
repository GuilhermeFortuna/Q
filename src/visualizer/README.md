
# Market Data Visualizer

A Python package for visualizing financial market data through interactive candlestick charts and trade analysis windows. Built with PySide6 and PyQtGraph for high-performance, desktop-based GUI applications.

## Overview

The visualizer package provides a comprehensive toolkit for displaying financial market data, including OHLC candlestick charts, line plots, and detailed trade visualization with filtering capabilities. It integrates seamlessly with pandas DataFrames and offers both programmatic API and interactive GUI components.

## Architecture

The package is organized into three main modules:

### 1. Plots (`plots/`)

Core plotting components that render different types of financial visualizations:

- **`CandlestickItem`**: Custom PyQtGraph GraphicsObject for rendering OHLC candlestick charts with optimized performance using pre-computed QPicture objects
- **`LinePlotItem`**: Wrapper around PyQtGraph PlotDataItem for customizable line plots with configurable colors and styling

### 2. Windows (`windows/`)

GUI window classes providing complete interactive interfaces:

- **`BaseWindow`**: Base QMainWindow class for consistent window behavior
- **`PlotWindow`**: Main plotting window supporting candlestick and line plots with dynamic data loading
- **`PlotTradesWindow`**: Advanced trade visualization window with:
  - Interactive time filtering (quick ranges, custom dates)
  - Trade marker rendering (entries/exits with configurable symbols)
  - Outcome-based filtering (win/loss/flat trades)
  - Candlestick integration with time axis alignment
  - Dockable control panels for filtering options
- **`BacktestSummaryDialog`**: Modal dialog for displaying backtest results with formatted KPI tables

### 3. Main API (`__init__.py`)

High-level convenience functions for quick visualization:

- **Application Management**: Automatic QApplication creation and event loop handling
- **Quick Plotting Functions**: `show_candlestick()`, `show_line_plot()` for immediate visualization
- **Plot Creation Utilities**: `create_candlestick_plot()`, `create_line_plot()` for programmatic use

## Installation

The visualizer package is part of a workspace project. Install with dependencies:
```bash
# Install the workspace including visualizer
uv sync

# Or install specific dependencies
uv add pyqtgraph==0.13.7 pyside6==6.7.2
```
## Dependencies

- **PySide6 (6.7.2)**: Qt6 bindings for GUI framework
- **PyQtGraph (0.13.7)**: High-performance plotting library
- **pandas**: DataFrame support for data handling
- **numpy**: Numerical operations

## Usage

### Quick Start - Basic Candlestick Chart
```python
import pandas as pd
from src.visualizer import show_candlestick

# Load OHLC data
ohlc_data = pd.read_csv('market_data.csv')  # with open, high, low, close columns
show_candlestick(ohlc_data, title="Market Analysis", block=True)
```
### Trade Visualization with Filtering
```python
from src.visualizer.windows.plot_trades import show_candlestick_with_trades

# Display candlesticks with trade markers
window = show_candlestick_with_trades(
    ohlc_data=ohlc_df,
    trades_df=trades_df,  # DataFrame with start, end, type, buyprice, sellprice columns
    title="Backtest Results",
    time_mode="bars",     # or "datetime" for timestamp alignment
    marker_size=12,
    block=True
)
```
### Backtest Summary Display

```python
from src.visualizer.windows.backtest_summary import show_backtest_summary

# Show formatted backtest results
show_backtest_summary(
    results=backtest_result_dict,
    title="Strategy Performance",
    block=True
)
```


### Programmatic API

```python
from src.visualizer import create_plot_window, create_candlestick_plot

# Create and customize window programmatically
window = create_plot_window("Custom Analysis")
window = create_candlestick_plot(ohlc_data, window)
window.add_line_plot(x_data, y_data, name="Signal", color="yellow", width=2)
window.show()
```


## Configuration

### Time Axis Modes

The package supports flexible time axis handling:

- **`datetime` mode**: Uses POSIX timestamps for continuous time axis
- **`bars` mode**: Maps trades to discrete bar indices for perfect alignment with candlestick data
- **`auto` mode**: Automatically detects the appropriate mode based on data types

### Trade Data Format

Expected DataFrame columns for trade visualization:

| Column | Type | Description |
|--------|------|-------------|
| `start` | datetime | Trade entry timestamp |
| `end` | datetime | Trade exit timestamp |
| `type` | str | Trade direction ("buy" or "sell") |
| `buyprice` | float | Buy execution price |
| `sellprice` | float | Sell execution price |
| `amount` | float | Trade size/volume |
| `profit` | float (optional) | Trade P&L |

## API Reference

### Core Functions

- `show_candlestick(ohlc_data, title, block)` - Display candlestick chart
- `show_line_plot(x, y, name, color, width, title, block)` - Display line plot
- `create_plot_window(title)` - Create empty plot window
- `create_candlestick_plot(ohlc_data, window)` - Add candlestick to window

### Advanced Windows

- `show_candlestick_with_trades(ohlc_data, trades_df, **opts)` - Complete trade analysis window
- `show_backtest_summary(results, **opts)` - Formatted results display

## Data I/O

### Input Formats

- **OHLC DataFrames**: Must contain `open`, `high`, `low`, `close` columns
- **Time Column**: Optional `time` column; uses DataFrame index if missing
- **Trade DataFrames**: See trade data format table above

### Time Handling

The package automatically handles various datetime formats and provides robust conversion between pandas timestamps and plot coordinates. Time zones are preserved when possible.

## Testing

The package includes validation for:

- Data format compliance (required columns, data types)
- Time axis alignment between candlesticks and trades
- GUI responsiveness with large datasets
- Cross-platform Qt application lifecycle management

## Roadmap

### Planned Features

- **Technical Indicators**: Built-in overlay support for moving averages, RSI, MACD
- **Multi-timeframe Views**: Synchronized charts across different timeframes
- **Export Capabilities**: PNG/SVG chart export and CSV data export
- **Performance Enhancements**: GPU acceleration for large datasets
- **Strategy Replay**: Frame-by-frame strategy execution visualization
- **Portfolio View**: Multi-symbol dashboard with correlation analysis

### Integration Goals

- Seamless integration with backtester package for strategy development
- Real-time data streaming support for live market analysis
- Plugin architecture for custom indicators and chart types

## Examples

See example usage in `scripts/backtest/dol_test.py` or `scripts/backtest/ccm_test.py` for complete examples integrating the visualizer with backtest results from the backtester package.

## License

Part of the PyQuant trading framework workspace.
```
This is the complete content that accurately reflects your current visualizer package implementation. You can copy and paste this entire content to replace your existing README.md file.
```
