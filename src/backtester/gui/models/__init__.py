"""
GUI Models Package

This package contains the data models for the Backtester GUI, providing
a clean separation between the UI components and the underlying data logic.

Models:
- StrategyModel: Manages strategy composition and signal configuration
- BacktestModel: Handles backtest configuration and data management
"""

from .strategy_model import StrategyModel
from .backtest_model import BacktestModel

__all__ = [
    'StrategyModel',
    'BacktestModel',
]


