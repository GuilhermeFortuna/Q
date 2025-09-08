from src.visualizer.windows.plot_data import PlotWindow
from src.visualizer.plots import CandlestickItem, LinePlotItem
from src.visualizer.windows.backtest_summary import show_backtest_summary
from src.visualizer.models import BacktestResultModel
import pandas as pd

__all__ = [
    'PlotWindow',
    'create_candlestick_plot',
    'create_line_plot',
    'create_plot_window',
    'show_candlestick',
    'show_line_plot',
    'show_backtest_summary',
    'BacktestResultModel',
]


def _ensure_qapplication():
    """
    Ensure QApplication exists. Create one if it doesn't exist.

    Returns:
        QApplication instance
    """
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _should_exec_app():
    """
    Determine if we should call app.exec() based on the environment.

    Returns:
        bool: True if we should exec, False otherwise
    """
    import sys
    import threading

    # Don't exec if we're not in the main thread
    if threading.current_thread() != threading.main_thread():
        return False

    # Check if we're in an interactive environment
    try:
        # Check for IPython/Jupyter
        if hasattr(__builtins__, '__IPYTHON__'):
            return False

        # Check for interactive Python shell
        if hasattr(sys, 'ps1'):
            return False

        # Check if stdin is connected to a terminal (interactive mode)
        if sys.stdin.isatty():
            return False

    except:
        pass

    # Check if QApplication is already running an event loop
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QCoreApplication

        app = QApplication.instance()
        if app is not None:
            # Try to check if event loop is already running
            if QCoreApplication.instance() and hasattr(app, '_running_exec'):
                return False
    except:
        pass

    return True


# Utility functions for quick plotting


def create_plot_window(title: str = "Market Data") -> PlotWindow:
    """
    Create a new plot window with default settings.

    Args:
        title: Window title

    Returns:
        PlotWindow instance ready for plotting
    """
    _ensure_qapplication()  # Ensure QApplication exists
    window = PlotWindow()
    window.setWindowTitle(title)
    return window


def create_candlestick_plot(
    ohlc_data: pd.DataFrame, show_volume: bool = False, window: PlotWindow = None
) -> PlotWindow:
    """
    Create a candlestick plot from OHLC data.

    Args:
        ohlc_data: DataFrame with open, high, low, close columns
        window: Optional existing PlotWindow instance. If None, creates a new one.

    Returns:
        PlotWindow instance with the candlestick plot
    """
    if window is None:
        _ensure_qapplication()  # Ensure QApplication exists
        window = create_plot_window("Candlestick Chart")

    window.add_candlestick_plot(ohlc=ohlc_data, show_volume=show_volume)
    return window


def create_line_plot(
    x,
    y,
    name: str = "Line",
    color: str = 'yellow',
    width: int = 2,
    window: PlotWindow = None,
) -> PlotWindow:
    """
    Create a line plot from x, y data.

    Args:
        x: X-axis data
        y: Y-axis data
        name: Name of the line plot
        color: Line color
        width: Line width
        window: Optional existing PlotWindow instance. If None, creates a new one.

    Returns:
        PlotWindow instance with the line plot
    """
    if window is None:
        _ensure_qapplication()  # Ensure QApplication exists
        window = create_plot_window(f"Line Chart - {name}")

    window.add_line_plot(x, y, name, color, width)
    return window


def show_candlestick(
    ohlc_data: pd.DataFrame, title: str = "Candlestick Chart", block: bool = None
) -> PlotWindow:
    """
    Quickly display a candlestick chart in a new window.

    Args:
        ohlc_data: DataFrame with open, high, low, close columns
        title: Window title
        block: Whether to block execution (start event loop). If None, auto-detect.

    Returns:
        PlotWindow instance
    """
    try:
        app = _ensure_qapplication()

        window = create_candlestick_plot(ohlc_data)
        window.setWindowTitle(title)
        window.show()

        # Auto-detect if we should block unless explicitly specified
        if block is None:
            block = _should_exec_app()

        if block:
            app._running_exec = True
            app.exec()

        return window

    except Exception as e:
        print(f"Error displaying candlestick chart: {e}")
        import traceback

        traceback.print_exc()  # This will help debug the issue
        return None


def show_line_plot(
    x,
    y,
    name: str = "Line",
    color: str = 'yellow',
    width: int = 2,
    title: str = None,
    block: bool = None,
) -> PlotWindow:
    """
    Quickly display a line plot in a new window.

    Args:
        x: X-axis data
        y: Y-axis data
        name: Name of the line plot
        color: Line color
        width: Line width
        title: Window title
        block: Whether to block execution (start event loop). If None, auto-detect.

    Returns:
        PlotWindow instance
    """
    try:
        if title is None:
            title = f"Line Chart - {name}"

        app = _ensure_qapplication()

        window = create_line_plot(x, y, name, color, width)
        window.setWindowTitle(title)
        window.show()

        # Auto-detect if we should block unless explicitly specified
        if block is None:
            block = _should_exec_app()

        if block:
            app._running_exec = True
            app.exec()

        return window

    except Exception as e:
        print(f"Error displaying line plot: {e}")
        import traceback

        traceback.print_exc()  # This will help debug the issue
        return None
