import pandas as pd
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication

from src.visualizer.plots import CandlestickItem
from src.visualizer.plots import LinePlotItem
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
        self.resize(1600, 800)

        # This will store the original datetime values for axis labeling
        self._time_values = None
        # Store ohlc data for dynamic y-range adjustments
        self._ohlc_data = None
        self._initial_candles = initial_candles
        self._indicator_plots = []

        # Create a plot item for price
        self.price_plot = self.graphWidget.addPlot(row=0, col=0)
        self.price_plot.addLegend()
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)

        # Disable auto-ranging and connect range change handler for dynamic Y zoom
        vb = self.price_plot.getViewBox()
        vb.disableAutoRange()
        self.price_plot.sigXRangeChanged.connect(self._on_x_range_changed)

    def _on_x_range_changed(self):
        """
        Dynamically adjusts the Y-axis range to fit the visible candles.
        This provides an auto-zoom effect on the Y-axis as the user pans or zooms.
        """
        if self._ohlc_data is None or self._ohlc_data.empty:
            return

        # Get the visible range of indices from the plot's view box
        view_box = self.price_plot.getViewBox()
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

    def add_candlestick_plot(
        self, ohlc: pd.DataFrame, show_volume: bool = False
    ) -> None:
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
        self.price_plot.setAxisItems({'bottom': date_axis})

        # Use integer indices for the x-axis to remove gaps
        df['time'] = self._time_values.index.to_list()

        candlestick = CandlestickItem(df)
        self.price_plot.addItem(candlestick)

        # Set the initial visible range to the last N candles
        num_candles = len(df)
        initial_view_start = max(0, num_candles - self._initial_candles)
        self.price_plot.setXRange(initial_view_start, num_candles)

        # Optionally, add volume subplot
        if show_volume:
            self.add_volume_subplot()

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
        self.price_plot.addItem(line)

    def add_scatter_plot(self, x, y, name, color, size, symbol):
        """
        Adds a scatter plot to the main price chart. Useful for plotting markers
        like tops and bottoms.
        :param x: A list or array of x-axis data (can be datetime objects).
        :param y: A list or array of y-axis data.
        :param name: Name of the scatter plot for the legend.
        :param color: Color of the markers.
        :param size: Size of the markers.
        :param symbol: Shape of the markers (e.g., 'o', 's', 't', 'd', '+').
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

        scatter = pg.ScatterPlotItem(
            x=x_numeric.tolist(),
            y=y.tolist(),
            name=name,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(color),
            size=size,
            symbol=symbol,
        )
        self.price_plot.addItem(scatter)

    def add_volume_subplot(self):
        """
        Adds a volume subplot with bars colored based on the candle's direction.
        Green for positive (close >= open) and red for negative (close < open).
        Requires 'open', 'close', and 'volume' columns in the OHLC data.
        """
        if self._ohlc_data is None or not all(
            c in self._ohlc_data for c in ['open', 'close', 'volume']
        ):
            print(
                "Warning: OHLC data with 'open', 'close', and 'volume' is required for the volume subplot."
            )
            return
        if self._time_values is None:
            print("Warning: Time values not set. Add a candlestick plot first.")
            return

        # Determine colors based on candle direction
        brushes = [
            (
                pg.mkBrush(color='#00FF00')
                if row.close >= row.open
                else pg.mkBrush(color='#FF0000')
            )
            for row in self._ohlc_data.itertuples()
        ]

        self.add_histogram_plot(
            x=self._time_values,
            y=self._ohlc_data['volume'],
            name="Volume",
            brushes=brushes,
        )

    def add_histogram_plot(self, x, y, name, color=None, brushes=None) -> None:
        """
        Adds a histogram-style plot (bar graph) in a new subplot below the main chart.
        Useful for indicators like volume or MACD.
        :param x: A list or array of x-axis data (can be datetime objects).
        :param y: A list or array of y-axis data.
        :param name: Name for the subplot's title.
        :param color: Color of the histogram bars (if brushes are not provided).
        :param brushes: A list of brushes for coloring each bar individually.
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

        # Create a new plot for the indicator
        self.graphWidget.nextRow()
        indicator_plot = self.graphWidget.addPlot(col=0)
        indicator_plot.setXLink(self.price_plot)  # Link X axes
        indicator_plot.setMaximumHeight(200)  # Give it a reasonable max height
        indicator_plot.showGrid(x=True, y=True, alpha=0.3)
        indicator_plot.setTitle(name)

        # Disable autorange on the new plot. Otherwise, adding the bar item will
        # cause it to zoom out to fit all data, and since the X-axis is linked,
        # it will force the main plot to zoom out as well.
        indicator_vb = indicator_plot.getViewBox()
        indicator_vb.disableAutoRange()

        # Create BarGraphItem
        bar_args = {
            'x': x_numeric.tolist(),
            'height': y.tolist(),
            'width': 0.6,
        }
        if brushes:
            bar_args['brushes'] = brushes
        elif color:
            bar_args['brush'] = pg.mkBrush(color)
        else:
            # Default color if neither is provided
            bar_args['brush'] = pg.mkBrush('gray')

        bar_item = pg.BarGraphItem(**bar_args)

        indicator_plot.addItem(bar_item)
        self._indicator_plots.append(indicator_plot)

        # Set a manual Y-range for the histogram since auto-range is disabled.
        if y is not None and not y.empty:
            max_y = y.max()
            indicator_vb.setYRange(0, max_y * 1.1)


if __name__ == '__main__':
    import sys
    from datetime import datetime, timedelta
    from src.backtester import CandleData
    import pandas_ta as pta

    # Data parameters
    symbol = 'DOL$'
    timeframe = '5min'
    date_to = datetime.today()
    date_from = date_to - timedelta(days=15)

    candles = CandleData(symbol='DOL', timeframe=timeframe)
    candle_data = CandleData.import_from_mt5(
        mt5_symbol=symbol, timeframe=timeframe, date_from=date_from, date_to=date_to
    )
    candle_data['volume'] = candle_data['real_volume'].copy()

    # --- Example indicator data ---
    # Simple Moving Average
    candle_data['ma'] = pta.ema(candle_data['close'], length=9)
    # Example scatter data (e.g., local maxima)
    hilo_period = 9
    hilo = pta.hilo(
        candle_data['high'],
        candle_data['low'],
        candle_data['close'],
        hilo_period,
        hilo_period,
    ).iloc[:, 0]
    candle_data['hilo'] = hilo.copy()

    q_app = QApplication(sys.argv)
    plot_window = PlotWindow(title="CCM Market Data Analysis", initial_candles=150)

    # Add candlestick plot first to define the time axis
    plot_window.add_candlestick_plot(candle_data)

    # Example of adding a line plot for a moving average
    plot_window.add_line_plot(
        x=candle_data.index,
        y=candle_data['ma'],
        name='MA',
        color='cyan',
        width=2,
    )

    # Example of adding a scatter plot for local maxima
    plot_window.add_scatter_plot(
        x=candle_data['hilo'].index,
        y=candle_data['hilo'],
        name='HiLo',
        color='magenta',
        size=10,
        symbol='d',  # Diamond symbol
    )

    # Example of adding a volume histogram in a subplot
    plot_window.add_histogram_subplot(
        x=candle_data.index,
        y=candle_data['volume'],
        name='Volume',
        color='gray',
    )

    plot_window.show()
    sys.exit(q_app.exec())
