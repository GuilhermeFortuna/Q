# q · Quantitative Trading Research Toolkit ⚡

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/badge/packaging-uv-green.svg)](https://docs.astral.sh/uv/)
[![GUI Ready](https://img.shields.io/badge/GUI-Ready-purple.svg)](https://github.com)
[![Backtesting](https://img.shields.io/badge/Backtesting-Advanced-orange.svg)](https://github.com)

> **The complete toolkit for quantitative trading research** — from strategy development to optimization, with both intuitive GUI and powerful programmatic interfaces.

<!-- ![Project Banner](docs/images/banner.png) *Placeholder: Hero banner showcasing the GUI interface and key features* -->

## 📋 Table of Contents

- [Why q?](#-why-q)
- [✨ Features](#-features)
- [🖼️ Screenshots & Demo](#️-screenshots--demo)
- [🚀 Installation](#-installation)
- [⚡ Quick Start](#-quick-start)
  - [GUI Quick Start (5 minutes)](#gui-quick-start-5-minutes)
  - [Programmatic Quick Start (5 minutes)](#programmatic-quick-start-5-minutes)
- [💻 Usage Examples](#-usage-examples)
  - [Simple Examples](#simple-examples)
  - [Advanced Examples](#advanced-examples)
- [🏗️ Core Components](#️-core-components)
- [📚 Documentation](#-documentation)
- [🎯 Use Cases](#-use-cases)
- [📂 Project Structure](#-project-structure)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

---

## 🌟 Why q?

**q** is designed for traders and researchers who demand both speed and sophistication. Whether you're building your first strategy or optimizing a complex multi-signal system, q provides the perfect balance of power and usability.

### For Traders & Researchers
- **🎯 Fast Iteration**: Go from idea to analysis in minutes, not hours
- **🧠 Smart Strategy Building**: Visual drag-and-drop interface + powerful programmatic API
- **📊 Deep Insights**: Interactive charts and comprehensive performance analysis
- **🔬 Research-Ready**: Built-in optimization, evaluation, and statistical analysis tools

### For Developers
- **🧩 Modular Architecture**: Clean, extensible design with clear separation of concerns
- **⚡ High Performance**: Optimized for large datasets and complex calculations
- **🔧 Developer-Friendly**: Comprehensive documentation, type hints, and testing
- **🌐 Integration-Ready**: Works with MetaTrader 5, CSV, Parquet, and custom data sources

---

## ✨ Features

### 🎨 **Interactive GUI Application**
- **Visual Strategy Builder**: Drag-and-drop interface for building complex trading strategies
- **Signal Library**: 17+ pre-built technical indicators (RSI, MACD, Supertrend, Donchian, etc.)
- **Real-time Monitoring**: Live progress tracking and metrics during backtest execution
- **Results Visualization**: Automatic integration with interactive charts and trade analysis

<!-- ![GUI Interface](docs/images/gui-interface.png) *Placeholder: Screenshot of the main GUI interface showing strategy builder* -->

### 🧠 **Advanced Strategy Architecture**
- **Composable Signals**: Build complex strategies by combining smaller, reusable components
- **Smart Combiners**: Gated, thresholded, and weighted voting systems for signal decisions
- **Strategy Archetypes**: Pre-built factories for Momentum Rider, Range Fader, and Volatility Breakout
- **Signal Evaluation**: Built-in framework for testing signal effectiveness and contribution

### ⚡ **High-Performance Backtesting Engine**
- **Event-Driven Architecture**: Simulate strategies on both OHLCV and tick-by-tick data
- **Flexible Data Sources**: Native support for MetaTrader 5, CSV, and Parquet files
- **Comprehensive Metrics**: Profit factor, Sharpe ratio, drawdown analysis, and more
- **Brazilian Tax Integration**: Automatic calculation of day trade and swing trade taxes

### 📈 **Interactive Visualization Suite**
- **Candlestick Charts**: High-performance OHLC visualization with technical indicators
- **Trade Analysis**: Interactive trade filtering, outcome analysis, and performance review
- **Backtest Summaries**: Formatted KPI tables and comprehensive result displays
- **Custom Indicators**: Easy overlay of moving averages, RSI, MACD, and custom signals

### 🔬 **Optimization & Research Tools**
- **Optuna Integration**: Advanced hyperparameter optimization with pruning
- **Strategy Evaluation**: Acceptance criteria and composite scoring systems
- **Walk-Forward Analysis**: Out-of-sample validation and stability testing
- **Performance Attribution**: Detailed analysis of signal contributions to trades

---

## 🖼️ Screenshots & Demo

<!-- ![Strategy Builder](docs/images/strategy-builder.png) *Placeholder: Screenshot of the visual strategy builder interface* -->

<!-- ![Backtest Results](docs/images/backtest-results.png) *Placeholder: Screenshot showing interactive charts with trade markers and performance metrics* -->

<!-- ![Signal Library](docs/images/signal-library.png) *Placeholder: Screenshot of the signal library panel with available indicators* -->

<!-- ![Optimization Dashboard](docs/images/optimization-dashboard.png) *Placeholder: Screenshot of Optuna optimization results and parameter space exploration* -->

*Screenshots coming soon! Check out the [GUI User Guide](docs/backtester_gui/USER_GUIDE.md) for detailed interface walkthroughs.*

---

## 🚀 Installation

### Prerequisites
- **Python**: `3.10`
- **OS**: Windows (recommended for MT5), macOS, or Linux
- **Optional**: MetaTrader 5 terminal for live data integration

### Quick Installation

**Recommended: Using uv**
```bash
# Install uv (if you don't have it)
# Follow instructions at https://docs.astral.sh/uv/

# Clone and install
git clone https://github.com/your-username/q.git
cd q
uv sync
```

**Alternative: Using pip**
```bash
git clone https://github.com/your-username/q.git
cd q
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .
```

### Verify Installation
```bash
python -c "from src.backtester.gui.main_window import BacktesterMainWindow; print('✅ GUI ready!')"
python -c "from src.strategies.archetypes import create_momentum_rider_strategy; print('✅ Strategies ready!')"
```

---

## ⚡ Quick Start

Choose your preferred approach — both take just 5 minutes!

### GUI Quick Start (5 minutes)

1. **Launch the GUI**
   ```bash
   python examples/backtester_gui_example.py
   ```

2. **Load Sample Data**
   - Switch to "Data Configuration" tab
   - Add a CSV file or connect to MetaTrader 5
   - Preview your data

3. **Build Your Strategy**
   - Go to "Strategy Builder" tab
   - Drag RSI signal from the library to the canvas
   - Set parameters (period=14) and role (Entry)
   - Add a Moving Average signal for confirmation

4. **Configure & Run**
   - Switch to "Backtest Configuration"
   - Set trading costs and parameters
   - Go to "Execution & Monitoring"
   - Click "Run Backtest" and watch the magic happen!

5. **Analyze Results**
   - View interactive charts with trade markers
   - Explore performance metrics and trade details
   - Export results or save your strategy

### Programmatic Quick Start (5 minutes)

**Simple Moving Average Crossover**
```python
from src.data.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.strategies.swingtrade import MaCrossover
from src.visualizer import show_backtest_summary

# 1. Load data
candles = CandleData(symbol="DOL$", timeframe="5min")
# For your own data: candles.data = your_pandas_dataframe

# 2. Configure strategy
strategy = MaCrossover(
    tick_value=0.5,
    short_ma_period=9,
    long_ma_period=21,
)

# 3. Run backtest
params = BacktestParameters(point_value=10.0, cost_per_trade=2.50)
engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
results = engine.run_backtest(display_progress=True)

# 4. Visualize results
if results.get_result() is not None:
    show_backtest_summary(results, ohlc_df=candles.data)
```

**Composite Strategy with Multiple Signals**
```python
from src.strategies.archetypes import create_momentum_rider_strategy
from src.backtester.evaluation import AcceptanceCriteria, StrategyEvaluator

# Create a sophisticated multi-signal strategy
strategy = create_momentum_rider_strategy()

# Run backtest
engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
results = engine.run_backtest(display_progress=True)

# Evaluate strategy performance
criteria = AcceptanceCriteria(
    min_trades=50, 
    min_profit_factor=1.3, 
    max_drawdown=0.15
)
evaluator = StrategyEvaluator(criteria)
metrics = evaluator.evaluate(results)
print(f"Strategy Grade: {metrics.label} (Score: {metrics.score:.2f})")
```

---

## 💻 Usage Examples

### Simple Examples

**Basic Chart Visualization**
```python
import pandas as pd
import pandas_ta as pta
from src.visualizer.windows import show_chart, IndicatorConfig

# Create sample data
ohlc = pd.DataFrame({
    "open": [1.0, 1.5, 1.2, 1.8], 
    "high": [1.6, 1.7, 1.9, 2.1],
    "low": [0.9, 1.1, 1.0, 1.5], 
    "close": [1.4, 1.3, 1.8, 2.0],
    "volume": [100, 150, 120, 200],
})

# Add technical indicator
ohlc['ema9'] = pta.ema(ohlc['close'], length=9)

# Visualize
indicators = [
    IndicatorConfig(type='line', y=ohlc['ema9'], name='EMA(9)', color='blue'),
]
show_chart(ohlc_data=ohlc, indicators=indicators, show_volume=True)
```

**Single Signal Strategy**
```python
from src.strategies.signals import RsiSignal
from src.strategies.composite import CompositeStrategy

# Create RSI mean reversion strategy
rsi_signal = RsiSignal(length=14, oversold=30, overbought=70)
strategy = CompositeStrategy(signals=[rsi_signal], always_active=True)

# Run and analyze
engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
results = engine.run_backtest(display_progress=True)
```

### Advanced Examples

**Multi-Signal Strategy with Combiners**
```python
from src.strategies.composite import CompositeStrategy
from src.strategies.combiners import GatedCombiner
from src.strategies.signals import (
    AdxDmiSignal, SupertrendFlipSignal, DonchianBreakoutSignal
)

# Build sophisticated strategy
signals = [
    AdxDmiSignal(length=14, adx_thresh=25.0),      # Trend filter
    SupertrendFlipSignal(atr_length=10, atr_mult=3.0),  # Volatility filter
    DonchianBreakoutSignal(breakout_len=20, pullback_len=5),  # Entry signal
]

# Use gated combiner: filters must pass, then entry signal triggers
combiner = GatedCombiner(
    filter_indices=[0, 1], 
    entry_indices=[2], 
    require_all_filters=False
)

strategy = CompositeStrategy(signals=signals, combiner=combiner)
```

**Parameter Optimization with Optuna**
```python
import optuna
from src.optimizer.engine import OptimizationEngine

def objective(trial):
    # Suggest parameters
    rsi_period = trial.suggest_int('rsi_period', 10, 30)
    rsi_oversold = trial.suggest_int('rsi_oversold', 20, 40)
    
    # Create strategy with suggested parameters
    strategy = create_optimized_strategy(rsi_period, rsi_oversold)
    
    # Run backtest
    engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
    results = engine.run_backtest(display_progress=False)
    
    # Return optimization metric
    return results.get_result()['profit_factor']

# Run optimization
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
print(f"Best parameters: {study.best_params}")
```

**Custom Signal Implementation**
```python
from src.strategies.signals.base import TradingSignal

class CustomVolatilitySignal(TradingSignal):
    def __init__(self, period=20, threshold=2.0):
        super().__init__()
        self.period = period
        self.threshold = threshold
    
    def compute(self, data):
        # Calculate rolling volatility
        returns = data['close'].pct_change()
        volatility = returns.rolling(self.period).std()
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        signals[volatility > self.threshold] = 1  # High volatility = long
        signals[volatility < -self.threshold] = -1  # Low volatility = short
        
        return signals
```

---

## 🏗️ Core Components

### 🎨 **Backtester GUI** (`src/backtester/gui/`)
Complete graphical interface for strategy development and analysis:
- **Strategy Builder**: Visual drag-and-drop strategy composition
- **Signal Library**: 17+ technical indicators with parameter configuration
- **Data Configuration**: Multi-source data loading and validation
- **Execution Monitor**: Real-time backtest progress and metrics
- **Results Analysis**: Interactive charts and performance summaries

### 🧠 **Strategy Framework** (`src/strategies/`)
Sophisticated signal composition architecture:
- **Signal Library**: RSI, MACD, Supertrend, Donchian, Keltner, ATR, VWAP, Heikin Ashi, and more
- **Combiners**: Gated, thresholded, and weighted voting systems
- **Archetypes**: Pre-built strategy factories for common patterns
- **Composite Strategy**: Flexible framework for combining multiple signals

### ⚡ **Backtesting Engine** (`src/backtester/`)
High-performance simulation engine:
- **Event-Driven Architecture**: Realistic trade simulation
- **Multi-Data Support**: OHLCV candles and tick-by-tick data
- **Risk Management**: Position sizing, drawdown controls, time limits
- **Performance Metrics**: Comprehensive P&L and risk analysis
- **Tax Integration**: Brazilian day trade and swing trade calculations

### 📈 **Visualization Suite** (`src/visualizer/`)
Interactive charts and analysis tools:
- **Candlestick Charts**: High-performance OHLC visualization
- **Trade Analysis**: Interactive filtering and outcome analysis
- **Technical Indicators**: Easy overlay of moving averages and oscillators
- **Backtest Summaries**: Formatted KPI tables and result displays

### 🔬 **Optimization Engine** (`src/optimizer/`)
Advanced parameter optimization:
- **Optuna Integration**: State-of-the-art hyperparameter optimization
- **Strategy Evaluation**: Acceptance criteria and composite scoring
- **Walk-Forward Analysis**: Out-of-sample validation
- **Performance Attribution**: Signal contribution analysis

### 📊 **Data Management** (`src/data/`)
Flexible data handling and storage:
- **Multi-Source Support**: MetaTrader 5, CSV, Parquet
- **Data Validation**: Automatic quality checks and formatting
- **Performance Optimization**: Efficient storage and retrieval
- **Format Conversion**: Seamless data transformation

---

## 📚 Documentation

### 📖 **User Guides**
- **[GUI User Guide](docs/backtester_gui/USER_GUIDE.md)** - Complete GUI walkthrough and tutorials
- **[Developer Guide](docs/backtester_gui/DEVELOPER_GUIDE.md)** - Architecture and extension guide
- **[API Reference](docs/backtester_gui/API_REFERENCE.md)** - Quick reference for classes and methods

### 🔧 **Component Documentation**
- **[Backtester](src/backtester/README.md)** - Core backtesting engine and data handling
- **[Strategies](src/strategies/README.md)** - Signal library and composition framework
- **[Visualizer](src/visualizer/README.md)** - Charting and visualization tools
- **[Optimizer](src/optimizer/README.md)** - Parameter optimization and evaluation

### 🎯 **Examples & Tutorials**
- **[Basic Examples](examples/)** - Simple backtest and visualization examples
- **[Composite Strategies](scripts/backtest/composites/)** - Advanced multi-signal examples
- **[Optimization Examples](scripts/optimization/)** - Parameter optimization workflows

---

## 🎯 Use Cases

### 📈 **Day Trading Strategy Development**
- Build and test intraday strategies with tick-level precision
- Optimize entry/exit timing with multiple confirmation signals
- Analyze performance across different market conditions
- Real-time strategy monitoring and adjustment

### 🎯 **Swing Trading System Optimization**
- Develop multi-timeframe strategies with trend and momentum filters
- Optimize parameters for different market regimes
- Walk-forward analysis for robust out-of-sample validation
- Portfolio-level risk management and position sizing

### 🔬 **Quantitative Research**
- Test new technical indicators and signal combinations
- Analyze signal effectiveness and contribution to performance
- Monte Carlo simulation and stress testing
- Factor analysis and market regime classification

### 🏢 **Institutional Applications**
- Multi-strategy portfolio backtesting
- Risk management and compliance monitoring
- Performance attribution and reporting
- Integration with existing trading infrastructure

---

## 📂 Project Structure

```
q/
├── src/                          # Core framework
│   ├── backtester/              # Backtesting engine & GUI
│   │   ├── gui/                 # Interactive GUI application
│   │   │   ├── main_window.py   # Main application window
│   │   │   ├── widgets/         # UI components
│   │   │   ├── controllers/     # Business logic
│   │   │   └── models/          # Data models
│   │   ├── engine.py            # Core backtesting engine
│   │   ├── strategy.py          # Strategy interface
│   │   ├── trades.py            # Trade management
│   │   └── evaluation.py        # Strategy evaluation framework
│   ├── strategies/              # Strategy & signal framework
│   │   ├── signals/             # 17+ technical indicators
│   │   ├── composite.py         # Strategy composition
│   │   ├── combiners.py         # Signal combination logic
│   │   └── archetypes.py        # Pre-built strategy factories
│   ├── visualizer/              # Interactive visualization
│   │   ├── windows/             # GUI windows
│   │   ├── plots/               # Chart components
│   │   └── models.py            # Data models
│   ├── optimizer/               # Parameter optimization
│   │   ├── engine.py            # Optuna integration
│   │   └── database.py          # Results storage
│   └── data/                    # Data management
│       ├── candle_data.py       # OHLCV data handling
│       ├── tick_data.py         # Tick-level data
│       └── store.py             # Data storage
├── examples/                    # Ready-to-run examples
│   ├── backtester_gui_example.py
│   └── strategies/              # Strategy configurations
├── scripts/                     # Analysis & optimization scripts
│   ├── backtest/               # Backtest examples
│   ├── analysis/               # Data analysis tools
│   └── optimization/           # Optimization workflows
├── docs/                       # Comprehensive documentation
│   ├── backtester_gui/         # GUI documentation
│   └── core_idea.md            # Framework concepts
└── tests/                      # Comprehensive test suite
    ├── backtester/             # Engine tests
    ├── strategies/             # Strategy tests
    └── visualizer/             # Visualization tests
```

---

## 🗺️ Roadmap

### 🚀 **Near Term (Q1 2024)**
- **Enhanced GUI**: Advanced charting features and custom indicator support
- **Real-time Data**: Live market data integration and streaming
- **Performance Optimization**: GPU acceleration for large datasets
- **Export Features**: PNG/SVG chart export and strategy sharing

### 🏛️ **Medium Term (Q2-Q3 2024)**
- **Multi-Asset Portfolio**: Cross-asset strategy backtesting and optimization
- **Walk-Forward Analysis**: Advanced time series cross-validation tools
- **Risk Management**: Sophisticated position sizing and risk controls
- **Cloud Integration**: Cloud-based data storage and computation

### 🌟 **Long Term (Q4 2024+)**
- **Real-time Trading**: Live strategy execution and monitoring
- **Machine Learning**: ML-based signal generation and optimization
- **API Platform**: REST API for remote strategy execution
- **Plugin Ecosystem**: Third-party indicator and strategy marketplace

---

## 🤝 Contributing

We welcome contributions from both traders and developers! Here's how you can help:

### 🐛 **Bug Reports**
- Use GitHub Issues with detailed reproduction steps
- Include system information and error logs
- Test with the latest version before reporting

### 💡 **Feature Requests**
- Describe the use case and expected behavior
- Consider if it fits the project's scope and architecture
- Provide examples or mockups when possible

### 🔧 **Code Contributions**
- Fork the repository and create a feature branch
- Follow the existing code style and conventions
- Add tests for new functionality
- Update documentation as needed

### 📚 **Documentation**
- Improve existing guides and tutorials
- Add examples for new features
- Translate documentation to other languages

### 🧪 **Testing**
- Test on different operating systems and Python versions
- Verify GUI functionality across platforms
- Report performance issues with large datasets

**Getting Started:**
1. Check out the [Developer Guide](docs/backtester_gui/DEVELOPER_GUIDE.md)
2. Look at existing issues and pull requests
3. Join our discussions for questions and ideas
4. Start with small improvements and work your way up

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **pandas-ta** - Comprehensive technical analysis library
- **PyQtGraph** - High-performance plotting framework
- **Optuna** - Advanced hyperparameter optimization
- **MetaTrader 5** - Professional trading platform integration
- **The Python Community** - For the amazing ecosystem of tools and libraries

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

[Report Bug](https://github.com/your-username/q/issues) · [Request Feature](https://github.com/your-username/q/issues) · [Join Discussion](https://github.com/your-username/q/discussions)

</div>