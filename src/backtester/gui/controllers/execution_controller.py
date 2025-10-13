"""
Execution Controller for Backtester GUI

This module contains the controller for managing backtest execution,
including progress monitoring, error handling, and results management.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox

from ..models.backtest_model import BacktestModel
from ...engine import Engine, BacktestParameters
from ...strategy import TradingStrategy
from ...trades import TradeRegistry


class BacktestExecutionThread(QThread):
    """Thread for executing backtests to avoid blocking the UI."""

    backtest_finished = Signal(object, object)  # TradeRegistry results, OHLC data with indicators
    backtest_error = Signal(str)  # error message
    progress_updated = Signal(int)  # progress percentage
    status_updated = Signal(str)  # status message

    def __init__(
        self,
        strategy: TradingStrategy,
        data: Dict[str, Any],
        config: BacktestParameters,
    ):
        super().__init__()
        self.strategy = strategy
        self.data = data
        self.config = config
        self._should_stop = False

    def run(self):
        """Execute the backtest in a separate thread."""
        try:
            self.status_updated.emit("Initializing backtest...")
            self.progress_updated.emit(0)

            # Validate data before creating engine
            if not self.data:
                raise ValueError("No data provided to backtest execution thread")

            print(f"[BacktestExecutionThread] Data keys: {list(self.data.keys())}")

            # Check if we have the required data type
            if 'candle' not in self.data and 'tick' not in self.data:
                raise ValueError(
                    f"Invalid data format. Expected 'candle' or 'tick' key, "
                    f"but got: {list(self.data.keys())}"
                )

            # Create engine
            engine = Engine(
                parameters=self.config, strategy=self.strategy, data=self.data
            )

            if self._should_stop:
                return

            self.status_updated.emit("Running backtest...")
            self.progress_updated.emit(10)

            # Run backtest with progress monitoring
            # Note: The current Engine doesn't support progress callbacks
            # This would need to be enhanced to support real-time progress updates
            results = engine.run_backtest(display_progress=False)

            if self._should_stop:
                return

            # Capture OHLC data with computed indicators from the engine
            ohlc_data_with_indicators = None
            if 'candle' in engine.data and hasattr(engine.data['candle'], 'data'):
                ohlc_data_with_indicators = engine.data['candle'].data.copy()
                print(f"[BacktestExecutionThread] Captured OHLC data with {len(ohlc_data_with_indicators.columns)} columns")
                print(f"[BacktestExecutionThread] Columns: {list(ohlc_data_with_indicators.columns)}")

            self.progress_updated.emit(100)
            self.status_updated.emit("Backtest completed")
            self.backtest_finished.emit(results, ohlc_data_with_indicators)

        except Exception as e:
            import traceback

            error_msg = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(f"[BacktestExecutionThread] Error: {error_msg}")
            self.backtest_error.emit(str(e))

    def stop(self):
        """Request the backtest to stop."""
        self._should_stop = True


class ExecutionController(QObject):
    """
    Controller for managing backtest execution and monitoring.

    This controller is responsible for orchestrating backtest execution in the
    Backtester GUI. It manages the execution lifecycle from initialization
    through completion, handling threading, progress monitoring, error management,
    and results processing.

    The controller follows the MVC pattern by acting as the intermediary between
    the UI components (views) and the backtesting engine (model). It ensures
    that backtest execution runs in separate threads to maintain UI responsiveness
    while providing real-time feedback to the user.

    Key Responsibilities:
    - Thread Management: Executes backtests in separate QThread instances
    - Progress Monitoring: Tracks and reports execution progress
    - Error Handling: Manages exceptions and provides user feedback
    - Results Processing: Handles backtest results and visualization
    - State Management: Tracks execution state and prevents conflicts
    - Integration: Connects with the backtesting engine and data models

    Threading Model:
    - Main Thread: UI updates and user interactions
    - Execution Thread: Backtest execution (BacktestExecutionThread)
    - Signal/Slot: Communication between threads using Qt signals

    Attributes:
        backtest_model (BacktestModel): Manages backtest configuration and data
        execution_thread (Optional[BacktestExecutionThread]): Current execution thread
        is_running (bool): Whether a backtest is currently executing
        current_results (Optional[TradeRegistry]): Results from last execution

    Signals:
        backtest_started(): Emitted when backtest execution begins
        backtest_finished(object): Emitted when backtest completes (TradeRegistry results)
        backtest_error(str): Emitted when backtest encounters an error (error_message)
        progress_updated(int): Emitted with progress updates (percentage)
        status_updated(str): Emitted with status message updates (message)

    Example:
        ```python
        from src.backtester.gui.controllers.execution_controller import ExecutionController
        from src.backtester.gui.models.backtest_model import BacktestModel

        model = BacktestModel()
        controller = ExecutionController(model)
        controller.backtest_finished.connect(self.on_backtest_completed)
        controller.run_backtest(strategy, data, config)
        ```
    """

    # Signals
    backtest_started = Signal()
    backtest_finished = Signal(object, object)  # TradeRegistry results, OHLC data with indicators
    backtest_error = Signal(str)  # error message
    progress_updated = Signal(int)  # progress percentage
    status_updated = Signal(str)  # status message

    def __init__(self, backtest_model: BacktestModel, parent=None):
        super().__init__(parent)
        self.backtest_model = backtest_model
        self._execution_thread: Optional[BacktestExecutionThread] = None
        self._current_results: Optional[TradeRegistry] = None
        self._current_ohlc_data: Optional[Any] = None  # Store OHLC data with computed indicators
        self._is_running = False

        # Progress monitoring timer
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.setInterval(100)  # Update every 100ms

    def run_backtest(
        self,
        strategy: TradingStrategy,
        data: Dict[str, Any],
        config: BacktestParameters,
    ) -> bool:
        """Start a backtest execution."""
        if self._is_running:
            self.backtest_error.emit("A backtest is already running")
            return False

        try:
            # Validate inputs
            if not strategy:
                self.backtest_error.emit("No strategy provided")
                return False

            if not data:
                self.backtest_error.emit("No data provided")
                return False

            if not config:
                self.backtest_error.emit("No configuration provided")
                return False

            # Start execution thread
            self._execution_thread = BacktestExecutionThread(strategy, data, config)
            self._execution_thread.backtest_finished.connect(self._on_backtest_finished)
            self._execution_thread.backtest_error.connect(self._on_backtest_error)
            self._execution_thread.progress_updated.connect(self._on_progress_updated)
            self._execution_thread.status_updated.connect(self._on_status_updated)

            self._is_running = True
            self._execution_thread.start()
            self._progress_timer.start()

            self.backtest_started.emit()
            return True

        except Exception as e:
            self.backtest_error.emit(f"Failed to start backtest: {str(e)}")
            return False

    def stop_backtest(self):
        """Stop the currently running backtest."""
        if self._execution_thread and self._execution_thread.isRunning():
            self._execution_thread.stop()
            self._execution_thread.wait(5000)  # Wait up to 5 seconds

            if self._execution_thread.isRunning():
                self._execution_thread.terminate()
                self._execution_thread.wait()

            self._execution_thread = None
            self._is_running = False
            self._progress_timer.stop()
            self.status_updated.emit("Backtest stopped")

    def is_running(self) -> bool:
        """Check if a backtest is currently running."""
        return self._is_running

    def get_current_results(self) -> Optional[TradeRegistry]:
        """Get the results from the last completed backtest."""
        return self._current_results

    def get_current_ohlc_data(self) -> Optional[Any]:
        """Get the OHLC data with computed indicators from the last completed backtest."""
        return self._current_ohlc_data

    def _on_backtest_finished(self, results: TradeRegistry, ohlc_data_with_indicators: Optional[Any]):
        """Handle backtest completion."""
        self._current_results = results
        self._current_ohlc_data = ohlc_data_with_indicators
        self._is_running = False
        self._progress_timer.stop()

        if self._execution_thread:
            self._execution_thread = None

        self.backtest_finished.emit(results, ohlc_data_with_indicators)

    def _on_backtest_error(self, error_message: str):
        """Handle backtest errors."""
        self._is_running = False
        self._progress_timer.stop()

        if self._execution_thread:
            self._execution_thread = None

        self.backtest_error.emit(error_message)

    def _on_progress_updated(self, progress: int):
        """Handle progress updates."""
        self.progress_updated.emit(progress)

    def _on_status_updated(self, status: str):
        """Handle status updates."""
        self.status_updated.emit(status)

    def _update_progress(self):
        """Update progress during backtest execution."""
        # This is a placeholder for more sophisticated progress monitoring
        # In a real implementation, this would query the execution thread
        # for current progress information
        pass

    def get_backtest_summary(self) -> Optional[Dict[str, Any]]:
        """Get a summary of the last backtest results."""
        if not self._current_results:
            return None

        try:
            # Get results from TradeRegistry
            results = self._current_results.get_result(return_result=True)
            return results
        except Exception as e:
            print(f"Error getting backtest summary: {e}")
            return None

    def export_results(self, file_path: str, format: str = "csv") -> bool:
        """Export backtest results to a file."""
        if not self._current_results:
            return False

        try:
            if format.lower() == "csv":
                self._current_results.trades.to_csv(file_path, index=False)
            elif format.lower() == "json":
                import json

                results = self.get_backtest_summary()
                if results:
                    with open(file_path, 'w') as f:
                        json.dump(results, f, indent=2, default=str)
            else:
                return False

            return True
        except Exception as e:
            print(f"Error exporting results: {e}")
            return False

    def get_trade_statistics(self) -> Optional[Dict[str, Any]]:
        """Get detailed trade statistics."""
        if not self._current_results:
            return None

        try:
            registry = self._current_results
            return {
                "total_trades": len(registry.trades),
                "positive_trades": registry.num_positive_trades,
                "negative_trades": registry.num_negative_trades,
                "win_rate": registry.accuracy,
                "profit_factor": registry.profit_factor,
                "net_balance": registry.net_balance,
                "mean_profit": registry.mean_profit,
                "mean_loss": registry.mean_loss,
                "max_drawdown": registry._compute_maximum_drawdown(),
                "total_profit": registry.positive_trades_sum,
                "total_loss": registry.negative_trades_sum,
            }
        except Exception as e:
            print(f"Error getting trade statistics: {e}")
            return None

    def get_equity_curve(self) -> Optional[List[float]]:
        """Get the equity curve data."""
        if not self._current_results:
            return None

        try:
            registry = self._current_results
            if not registry.trades.empty and 'balance' in registry.trades.columns:
                return registry.trades['balance'].tolist()
        except Exception as e:
            print(f"Error getting equity curve: {e}")

        return None

    def get_drawdown_curve(self) -> Optional[List[float]]:
        """Get the drawdown curve data."""
        if not self._current_results:
            return None

        try:
            registry = self._current_results
            if not registry.trades.empty and 'balance' in registry.trades.columns:
                balance = registry.trades['balance']
                max_balance = balance.cummax()
                drawdown = max_balance - balance
                return drawdown.tolist()
        except Exception as e:
            print(f"Error getting drawdown curve: {e}")

        return None

    def clear_results(self):
        """Clear the current backtest results."""
        self._current_results = None
