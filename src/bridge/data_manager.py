"""
DataManager is a simple utility to share data between the backtester and the visualizer.

It provides methods to store (hold) the results of a backtest and to retrieve them later.
This minimal implementation keeps results in-memory. For more advanced scenarios, this
could be extended to support multiple result slots, persistence, or pub/sub updates.
"""

from __future__ import annotations
from typing import Any, Optional

from src.backtester.trades import TradeRegistry


class DataManager:
    """Manage shared data (e.g., backtest results) between components.

    Usage:
        dm = DataManager()
        dm.set_backtest_results(results)
        results = dm.get_backtest_results()

    A module-level singleton instance `data_manager` is also provided for convenience.
    """

    def __init__(self) -> None:
        self._backtest_results: TradeRegistry | None = None

    def set_backtest_results(self, results: TradeRegistry) -> None:
        """Store or update backtest results.

        Args:
            results: Arbitrary object representing backtest results (e.g., TradeRegistry, dict, DataFrame).
        """
        self._backtest_results = results

    def get_backtest_results(self) -> TradeRegistry | None:
        """Retrieve the stored backtest results.

        Returns:
            The previously stored backtest results object, or None if none were stored yet.
        """
        return self._backtest_results


# Optional shared instance for easy access across modules
data_manager = DataManager()

__all__ = ["DataManager", "data_manager"]
