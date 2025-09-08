import pyqtgraph as pg
from PySide6.QtWidgets import QApplication
from src.visualizer.plots import CandlestickItem
from src.visualizer.plots import LinePlotItem
import pandas as pd

from src.visualizer.windows.base import BaseWindow


class DateAxis(pg.AxisItem):
    """
    A custom axis item that displays dates from a series of timestamps.
    This axis will display formatted date strings instead of numerical indices,
    effectively removing gaps from weekends and non-trading hours.
    """

    def __init__(self, timestamps, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timestamps = timestamps

    def tickStrings(self, values, scale, spacing):
        """
        Convert numerical tick values (indices) to date strings.
        """
        strings = []
        for v in values:
            index = int(round(v))
            if 0 <= index < len(self._timestamps):
                # Format the timestamp to a readable date string
                strings.append(
                    pd.to_datetime(self._timestamps[index]).strftime('%Y-%m-%d %H:%M')
                )
            else:
                # Return an empty string for indices outside the data range
                strings.append('')
        return strings


class PlotWindow(BaseWindow):
    """
    A class representing a window for plotting market data.

    This class is designed to display and manage various types of financial
    charts, such as candlestick and line plots, using the plotting functionality
    provided by pyqtgraph. The `PlotWindow` allows users to visualize market data
    in a graphical format, facilitating analysis and interpretation.

    The window is configured with a date-time axis and automatically handles
    conversion of time-based data for plotting.

    :ivar PLOT_TYPE_MAP: A mapping of plot type names to their corresponding
        plot item classes. Used for determining the appropriate plot type
        dynamically.
    :type PLOT_TYPE_MAP: dict
    :ivar graphWidget: An instance of `pyqtgraph.GraphicsLayoutWidget` used as
        the central widget for the plotting window.
    :type graphWidget: pyqtgraph.GraphicsLayoutWidget
    :ivar data: Stores the market data used for plotting. Typically provided
        as a list or loaded from an external source.
    :type data: list
    :ivar plot: The plotting object within the `graphWidget` where different
        types of charts and data visualizations are added.
    :type plot: pyqtgraph.PlotItem
    """

    PLOT_TYPE_MAP = {
        'candlestick': CandlestickItem,
        'line': LinePlotItem,
    }

    def __init__(self, title: str = "Market Data", initial_candles: int = 100):
        super(PlotWindow, self).__init__()
        self.graphWidget = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.graphWidget)
        self.setWindowTitle(title)

        # This will store the original datetime values for axis labeling
        self._time_values = None
        # Store ohlc data for dynamic y-range adjustments
        self._ohlc_data = None
        self._initial_candles = initial_candles

        # Create a plot item
        self.plot = self.graphWidget.addPlot(row=0, col=0)
        self.plot.addLegend()
        self.plot.showGrid(x=True, y=True, alpha=0.3)

        # Disable auto-ranging and connect range change handler for dynamic Y zoom
        vb = self.plot.getViewBox()
        vb.disableAutoRange()
        self.plot.sigXRangeChanged.connect(self._on_x_range_changed)

    def _on_x_range_changed(self):
        """
        Dynamically adjusts the Y-axis range to fit the visible candles.
        This provides an auto-zoom effect on the Y-axis as the user pans or zooms.
        """
        if self._ohlc_data is None or self._ohlc_data.empty:
            return

        # Get the visible range of indices from the plot's view box
        view_box = self.plot.getViewBox()
        x_range = view_box.viewRange()[0]
        start_index = max(0, int(x_range[0]))
        end_index = min(len(self._ohlc_data), int(x_range[1]) + 1)

        if start_index >= end_index:
            return

        # Slice the data to the visible range and find min/max prices
        visible_data = self._ohlc_data.iloc[start_index:end_index]
        if visible_data.empty:
            return

        min_low = visible_data['low'].min()
        max_high = visible_data['high'].max()

        # Add some padding to the y-range for better visibility
        y_padding = (max_high - min_low) * 0.1
        view_box.setYRange(min_low - y_padding, max_high + y_padding, padding=0)

    def add_candlestick_plot(self, ohlc: pd.DataFrame) -> None:
        """
        Adds a candlestick plot to the window.
        This method sets up a custom x-axis to display datetimes without gaps.
        :param ohlc: DataFrame with open, high, low, close columns and a datetime index.
        """
        df = ohlc.copy()
        self._ohlc_data = df.reset_index(drop=True)  # Store for y-range adjustments

        if 'time' not in df.columns:
            time_data = df.index.to_series()
        else:
            time_data = df['time']

        # Store the original timestamps and set up the custom axis
        self._time_values = pd.to_datetime(time_data).reset_index(drop=True)
        date_axis = DateAxis(timestamps=self._time_values.values, orientation='bottom')
        self.plot.setAxisItems({'bottom': date_axis})

        # Use integer indices for the x-axis to remove gaps
        df['time'] = self._time_values.index.to_list()

        candlestick = CandlestickItem(df)
        self.plot.addItem(candlestick)

        # Set the initial visible range to the last N candles
        num_candles = len(df)
        initial_view_start = max(0, num_candles - self._initial_candles)
        self.plot.setXRange(initial_view_start, num_candles)

    def add_line_plot(self, x, y, name, color, width) -> None:
        """
        Adds a line plot. Aligns datetime x-axis data to the candlestick's axis.
        :param x: A list or array of x-axis data (can be datetime objects).
        :param y: A list or array of y-axis data.
        :param name: Name of the line for the legend.
        :param color: Color of the line.
        :param width: Width of the line.
        """
        x_series = pd.Series(x)
        if pd.api.types.is_datetime64_any_dtype(x_series.dtype):
            if self._time_values is None:
                raise ValueError(
                    "A candlestick plot must be added first to establish a time axis."
                )
            # Map datetime values to integer indices using the stored time values
            x_numeric = self._time_values.searchsorted(pd.to_datetime(x_series))
        else:
            x_numeric = x_series

        line = LinePlotItem(x_numeric.tolist(), y, name=name, color=color, width=width)
        self.plot.addItem(line)

    def add_histogram_plot(self, data) -> None:
        pass


if __name__ == '__main__':
    import sys
    from datetime import datetime
    from src.backtester import CandleData

    # Data parameters
    DATA_PATH = r'F:\New_Backup_03_2025\PyQuant\data\ccm_60min_atualizado.csv'
    TIMEFRAME = '60min'
    DATE_FROM = datetime(2020, 1, 1)
    DATE_TO = datetime.today()

    candles = CandleData(symbol='CCM', timeframe=TIMEFRAME)
    candle_data = candles.import_from_csv(DATA_PATH)
    candle_data = candle_data.loc[
        (candle_data.index >= DATE_FROM) & (candle_data.index <= DATE_TO)
    ].copy()

    q_app = QApplication(sys.argv)
    plot_window = PlotWindow(title="CCM Market Data Analysis", initial_candles=150)

    # Add candlestick plot first to define the time axis
    plot_window.add_candlestick_plot(candle_data)

    # Example of adding a line plot for the 'close' price
    plot_window.add_line_plot(
        x=candle_data.index,
        y=candle_data['close'],
        name='Close Price',
        color='yellow',
        width=2,
    )
    plot_window.show()
    sys.exit(q_app.exec())
