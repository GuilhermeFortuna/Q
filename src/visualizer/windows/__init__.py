import sys
import pandas as pd
from PySide6.QtWidgets import QApplication

from src.visualizer.models import IndicatorConfig
from .plot_data import PlotWindow

__all__ = ["show_chart"]


def show_chart(
    ohlc_data: pd.DataFrame,
    indicators: list[IndicatorConfig] = None,
    title: str = "Market Data",
    initial_candles: int = 100,
    block: bool = True,
):
    """
    A comprehensive plotting function to display OHLC data with various technical indicators.

    This function simplifies the process of creating a complex financial chart. It
    handles the setup of the plotting window, rendering of the primary candlestick
    chart, and overlaying or adding subplots for a list of provided indicators.

    :param ohlc_data: A pandas DataFrame containing the OHLC data with a
        datetime index and columns for 'open', 'high', 'low', and 'close'.
    :param indicators: A list of `IndicatorConfig` objects, where each object
        defines an indicator to be plotted.
    :param title: The title of the plot window.
    :param initial_candles: The number of initial candles to display.
    :param block: If True, the application event loop is started, and the
        function will block until the window is closed. If False, the window
        is shown, and the function returns the window instance.

    :return: The `PlotWindow` instance if `block` is False.

    Example Usage:
    -------------
    >>> from src.visualizer.models import IndicatorConfig
    >>> sma = ohlc_data['close'].rolling(20).mean()
    >>> volume = ohlc_data['volume']
    >>> indicators = [
    ...     IndicatorConfig(type='line', y=sma, name='SMA(20)', color='blue'),
    ...     IndicatorConfig(type='histogram', y=volume, name='Volume', color='gray')
    ... ]
    >>> show_chart(ohlc_data, indicators=indicators, title="Stock Analysis")
    """
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = PlotWindow(title=title, initial_candles=initial_candles)
    window.add_candlestick_plot(ohlc_data)

    if indicators:
        for indicator in indicators:
            x_data = indicator.x if indicator.x is not None else ohlc_data.index

            try:
                if indicator.type == 'line':
                    window.add_line_plot(
                        x=x_data,
                        y=indicator.y,
                        name=indicator.name,
                        color=indicator.color,
                        width=indicator.width,
                    )
                elif indicator.type == 'scatter':
                    window.add_scatter_plot(
                        x=x_data,
                        y=indicator.y,
                        name=indicator.name,
                        color=indicator.color,
                        size=indicator.size,
                        symbol=indicator.symbol,
                    )
                elif indicator.type == 'histogram':
                    window.add_histogram_plot(
                        x=x_data,
                        y=indicator.y,
                        name=indicator.name,
                        color=indicator.color,
                    )
                else:
                    print(f"Warning: Unknown plot type '{indicator.type}'. Skipping.")
            except Exception as e:
                print(
                    f"An unexpected error occurred while plotting indicator "
                    f"'{indicator.name}': {e}"
                )

    window.show()

    if block:
        app.exec()

    return window
