"""
GUI Widgets Package

This package contains the main UI widgets for the Backtester GUI,
providing the visual interface for all backtesting workflows.

Widgets:
- StrategyBuilderWidget: Visual signal composition interface
- DataConfigWidget: Market data loading and configuration
- BacktestConfigWidget: Backtest parameter configuration
- ExecutionMonitorWidget: Real-time execution monitoring
- SignalLibraryWidget: Available signals panel
"""

from .strategy_builder import StrategyBuilderWidget
from .data_config import DataConfigWidget
from .backtest_config import BacktestConfigWidget
from .execution_monitor import ExecutionMonitorWidget
from .signal_library import SignalLibraryWidget

__all__ = [
    'StrategyBuilderWidget',
    'DataConfigWidget',
    'BacktestConfigWidget',
    'ExecutionMonitorWidget',
    'SignalLibraryWidget',
]


