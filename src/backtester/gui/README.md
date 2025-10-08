# Backtester GUI

A comprehensive graphical user interface for the Backtester package, providing an intuitive way to build, configure, and execute trading strategies.

## 📚 Documentation

- **[User Guide](docs/backtester_gui/USER_GUIDE.md)** - Complete user manual with tutorials and examples
- **[Developer Guide](docs/backtester_gui/DEVELOPER_GUIDE.md)** - Architecture details and extension guide
- **[API Reference](docs/backtester_gui/API_REFERENCE.md)** - Quick reference for classes and methods

## Features

### 🎯 Strategy Builder
- **Visual Signal Composition**: Drag-and-drop interface for building trading strategies
- **Signal Library**: Comprehensive library of technical indicators and signals
- **Parameter Configuration**: Easy-to-use forms for configuring signal parameters
- **Strategy Templates**: Pre-built strategy templates for quick start
- **Real-time Validation**: Instant feedback on strategy configuration

### 📊 Data Configuration
- **Multiple Data Sources**: Support for CSV, Parquet, and MetaTrader 5
- **Data Validation**: Automatic data quality checks and validation
- **Data Preview**: Real-time preview of loaded market data
- **Statistics**: Comprehensive data statistics and analysis

### ⚙️ Backtest Configuration
- **Trading Costs**: Configure point values, commissions, and costs
- **Risk Management**: Set position limits, drawdown controls, and time limits
- **Execution Settings**: Configure slippage, order types, and execution options
- **Advanced Options**: Data processing, performance, and debug settings

### 📈 Execution & Monitoring
- **Real-time Progress**: Live progress tracking during backtest execution
- **Live Metrics**: Real-time P&L, trade count, win rate, and drawdown
- **Execution Logs**: Detailed logging of backtest execution
- **Results Visualization**: Automatic integration with the visualizer package

## Architecture

The GUI is built using PySide6 (Qt6) and follows a clean architecture pattern:

```
src/backtester/gui/
├── main_window.py          # Main application window
├── models/                 # Data models
│   ├── strategy_model.py   # Strategy data management
│   └── backtest_model.py   # Backtest configuration
├── controllers/            # Business logic controllers
│   ├── strategy_controller.py  # Strategy building logic
│   └── execution_controller.py # Backtest execution
├── widgets/                # UI components
│   ├── strategy_builder.py     # Strategy composition interface
│   ├── data_config.py          # Data loading and configuration
│   ├── backtest_config.py      # Parameter configuration
│   ├── execution_monitor.py    # Real-time monitoring
│   └── signal_library.py       # Available signals panel
└── dialogs/                # Dialog windows
    ├── strategy_save.py        # Save strategy dialog
    ├── data_import.py          # Data import dialog
    └── parameter_edit.py       # Parameter editing dialog
```

## Usage

### Quick Start

### Method 1: Using the Example Script
```bash
python examples/backtester_gui_example.py
```

### Method 2: Direct Python Import
```python
from src.backtester.gui.main_window import BacktesterMainWindow
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = BacktesterMainWindow()
window.show()
sys.exit(app.exec())
```

### 5-Minute Tutorial
1. **Load Data**: Switch to Data Configuration tab → Add CSV/Parquet file
2. **Build Strategy**: Go to Strategy Builder → Drag RSI signal to canvas
3. **Configure**: Set parameters (period=14) and role (Entry)
4. **Set Parameters**: Switch to Backtest Configuration → Set trading costs
5. **Run Backtest**: Go to Execution & Monitoring → Click "Run Backtest"

For detailed tutorials, see the [User Guide](docs/backtester_gui/USER_GUIDE.md).

## Workflow

### 1. Strategy Building
1. Open the **Strategy Builder** tab
2. Select signals from the **Signal Library**
3. Configure signal parameters
4. Arrange signals in the **Strategy Canvas**
5. Validate the strategy configuration

### 2. Data Configuration
1. Switch to the **Data Configuration** tab
2. Add data sources (CSV, Parquet, or MT5)
3. Configure symbol, timeframe, and date range
4. Load and validate the data
5. Preview data quality and statistics

### 3. Backtest Setup
1. Go to the **Backtest Configuration** tab
2. Set trading costs and parameters
3. Configure risk management settings
4. Set execution options
5. Validate the configuration

### 4. Execution & Monitoring
1. Switch to the **Execution & Monitoring** tab
2. Click **Run Backtest** to start execution
3. Monitor real-time progress and metrics
4. View execution logs
5. Analyze results in the **Results** tab

## Signal Library

The GUI includes a comprehensive library of technical indicators:

### Momentum Indicators
- **RSI** (Relative Strength Index)
- **Stochastic Oscillator**

### Trend Indicators
- **MACD** (Moving Average Convergence Divergence)
- **Moving Averages** (SMA, EMA, WMA, DEMA, TEMA)

### Volatility Indicators
- **Bollinger Bands**

### Custom Signals
- Support for custom signal implementations
- Extensible signal library architecture

## Integration

The GUI seamlessly integrates with the existing Backtester package:

- **Engine Integration**: Uses the existing `Engine` class for backtesting
- **Data Integration**: Leverages `CandleData` and `TickData` classes
- **Results Integration**: Automatically opens results in the visualizer
- **Strategy Integration**: Works with existing `TradingStrategy` implementations

## Styling

The GUI features a professional dark theme optimized for trading applications:

- **Dark Color Scheme**: Easy on the eyes for long trading sessions
- **High Contrast**: Clear visibility of important information
- **Consistent Design**: Unified look and feel across all components
- **Responsive Layout**: Adapts to different window sizes

## Error Handling

Comprehensive error handling throughout the application:

- **Validation**: Real-time validation of all inputs
- **Error Messages**: Clear, actionable error messages
- **Recovery**: Graceful handling of errors with recovery options
- **Logging**: Detailed logging for debugging and support

## Performance

Optimized for performance with large datasets:

- **Threading**: Backtest execution in separate threads
- **Progress Updates**: Real-time progress monitoring
- **Memory Management**: Efficient handling of large datasets
- **Caching**: Intelligent caching of calculated indicators

## Future Enhancements

Planned features for future releases:

- **Strategy Optimization**: Built-in parameter optimization
- **Walk-forward Analysis**: Time series cross-validation
- **Monte Carlo Simulation**: Risk analysis and stress testing
- **Portfolio Management**: Multi-strategy portfolio backtesting
- **Cloud Integration**: Cloud-based data and execution
- **API Integration**: REST API for remote execution
- **Plugin System**: Extensible plugin architecture

## Dependencies

- **PySide6**: Qt6 bindings for Python
- **PyQtGraph**: High-performance plotting
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **MetaTrader5**: MT5 integration (optional)

## Troubleshooting

### Common Issues

#### GUI Won't Start
- **Check PySide6**: `pip install PySide6`
- **Verify Python**: Requires Python 3.8+
- **Check Dependencies**: Ensure all packages are installed

#### Data Loading Errors
- **File Format**: Ensure CSV has correct column names (datetime, open, high, low, close, volume)
- **Date Format**: Use supported formats (%d/%m/%Y %H:%M or ISO)
- **File Encoding**: Try UTF-8 or Latin-1 encoding
- **Data Validation**: Check for missing or invalid values

#### Strategy Validation Errors
- **Signal Parameters**: Ensure all required parameters are set
- **Signal Roles**: Each strategy needs at least one entry signal
- **Parameter Ranges**: Check that parameter values are within valid ranges
- **Strategy Logic**: Avoid circular dependencies between signals

#### Backtest Execution Errors
- **Data Availability**: Ensure data covers the specified period
- **Strategy Logic**: Test with simple data first
- **Memory Usage**: Large datasets may require more RAM
- **Execution Logs**: Check detailed error messages in the log

### Performance Issues

#### Slow Data Loading
- **Use Parquet**: Faster than CSV for large datasets
- **Reduce Date Range**: Load only necessary data
- **Check Disk Speed**: Use SSD for better performance

#### Slow Backtest Execution
- **Reduce Data Frequency**: Use higher timeframes when possible
- **Simplify Strategy**: Remove unnecessary calculations
- **Check Indicators**: Some indicators are computationally expensive

### Getting Help

1. **Check Logs**: Review execution logs for error details
2. **Validate Configuration**: Ensure all settings are correct
3. **Test with Simple Data**: Use basic examples first
4. **Check Documentation**: Refer to [User Guide](docs/backtester_gui/USER_GUIDE.md) and [API Reference](docs/backtester_gui/API_REFERENCE.md)
5. **Report Issues**: Include error messages and configuration details

## Contributing

Contributions are welcome! Please see the main project README for contribution guidelines.

## License

This project is licensed under the same terms as the main Backtester package.


