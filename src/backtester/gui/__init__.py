"""
Backtester GUI Package

This package provides a comprehensive graphical user interface for the Backtester system,
enabling users to build, configure, and execute trading strategies through an intuitive
visual interface.

Main Components:
- BacktesterMainWindow: Main application window with tabbed interface
- Strategy Builder: Visual signal composition interface
- Data Configuration: Market data loading and validation
- Backtest Configuration: Parameter setup and validation
- Execution Monitor: Real-time backtest monitoring and results
"""

from .main_window import BacktesterMainWindow
from .widgets.strategy_builder import StrategyBuilderWidget
from .widgets.data_config import DataConfigWidget
from .widgets.backtest_config import BacktestConfigWidget
from .widgets.execution_monitor import ExecutionMonitorWidget

__all__ = [
    'BacktesterMainWindow',
    'StrategyBuilderWidget',
    'DataConfigWidget', 
    'BacktestConfigWidget',
    'ExecutionMonitorWidget',
]


