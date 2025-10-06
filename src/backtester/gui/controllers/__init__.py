"""
GUI Controllers Package

This package contains the controller classes for the Backtester GUI,
handling the business logic and coordination between models and views.

Controllers:
- StrategyController: Manages strategy building and validation logic
- ExecutionController: Handles backtest execution and monitoring
"""

from .strategy_controller import StrategyController
from .execution_controller import ExecutionController

__all__ = [
    'StrategyController',
    'ExecutionController',
]


