import pandas as pd
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QPointF
from PySide6.QtGui import QTextItem
import numpy as np

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
                # Get the timestamp and check if it's valid
                timestamp = self._timestamps[index]
                if pd.isna(timestamp) or pd.isnull(timestamp):
                    # Handle NaT/NaN values
                    strings.append('')
                else:
                    # Format the timestamp to a readable date string
                    try:
                        strings.append(
                            pd.to_datetime(timestamp).strftime('%Y-%m-%d %H:%M')
                        )
                    except (ValueError, TypeError):
                        # Fallback for any other datetime formatting issues
                        strings.append('')
            else:
                # Return an empty string for indices outside the data range
                strings.append('')
        return strings


class ChartTooltipController:
    """Controller for handling hover tooltips on chart elements."""

    def __init__(self, plot_window):
        self.plot_window = plot_window
        self.price_plot = plot_window.price_plot
        self.view_box = self.price_plot.getViewBox()

        # Tooltip configuration
        self.enabled = True
        self.delay_ms = 100
        self.pick_radius = 10

        # Tooltip display
        self.tooltip_item = pg.TextItem(anchor=(0, 1))
        self.tooltip_item.setVisible(False)
        self.price_plot.addItem(self.tooltip_item)

        # Hover state
        self._current_hover = None
        self._tooltip_timer = QTimer()
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._show_tooltip)
        self._last_mouse_pos = None

        # Connect mouse events
        self.price_plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _on_mouse_moved(self, pos):
        """Handle mouse movement over the plot."""
        if not self.enabled:
            self._hide_tooltip()
            return

        # Convert to view coordinates
        view_pos = self.view_box.mapSceneToView(pos)
        self._last_mouse_pos = pos

        # Find nearest data point
        hover_info = self._find_nearest_point(view_pos)

        if hover_info != self._current_hover:
            self._current_hover = hover_info
            self._tooltip_timer.stop()

            if hover_info:
                self._tooltip_timer.start(self.delay_ms)
            else:
                self._hide_tooltip()

    def _find_nearest_point(self, view_pos):
        """Find the nearest data point within pick radius."""
        x_pos = view_pos.x()
        y_pos = view_pos.y()

        # Convert pick radius from pixels to data units
        pixel_size = self.view_box.viewPixelSize()
        if pixel_size is None:
            return None

        # Handle both QPointF and tuple returns from viewPixelSize()
        try:
            if hasattr(pixel_size, 'x'):
                # QPointF object
                x_radius = pixel_size.x() * self.pick_radius
                y_radius = pixel_size.y() * self.pick_radius
            else:
                # Tuple (x, y)
                x_radius = pixel_size[0] * self.pick_radius
                y_radius = pixel_size[1] * self.pick_radius
        except (AttributeError, IndexError, TypeError):
            # Fallback to reasonable defaults if pixel size detection fails
            x_radius = self.pick_radius
            y_radius = self.pick_radius

        closest_info = None
        closest_distance = float('inf')

        # Check candlestick data
        if (
            hasattr(self.plot_window, '_ohlc_data')
            and self.plot_window._ohlc_data is not None
        ):
            ohlc_info = self._check_candlestick_hover(x_pos, y_pos, x_radius, y_radius)
            if ohlc_info and ohlc_info['distance'] < closest_distance:
                closest_info = ohlc_info
                closest_distance = ohlc_info['distance']

        # Check line plots
        for item_info in getattr(self.plot_window, '_line_items', []):
            line_info = self._check_line_hover(
                item_info, x_pos, y_pos, x_radius, y_radius
            )
            if line_info and line_info['distance'] < closest_distance:
                closest_info = line_info
                closest_distance = line_info['distance']

        # Check scatter plots
        for item_info in getattr(self.plot_window, '_scatter_items', []):
            scatter_info = self._check_scatter_hover(
                item_info, x_pos, y_pos, x_radius, y_radius
            )
            if scatter_info and scatter_info['distance'] < closest_distance:
                closest_info = scatter_info
                closest_distance = scatter_info['distance']

        # Check histogram plots
        for plot in getattr(self.plot_window, '_indicator_plots', []):
            # Map mouse position to the indicator plot's coordinate system
            plot_view_box = plot.getViewBox()
            plot_view_pos = plot_view_box.mapSceneToView(self._last_mouse_pos)

            hist_info = self._check_histogram_hover(
                plot, plot_view_pos.x(), plot_view_pos.y(), x_radius, y_radius
            )
            if hist_info and hist_info['distance'] < closest_distance:
                closest_info = hist_info
                closest_distance = hist_info['distance']

        return closest_info

    def _check_candlestick_hover(self, x_pos, y_pos, x_radius, y_radius):
        """Check if hovering over candlestick data."""
        ohlc = self.plot_window._ohlc_data

        # Find nearest x index
        x_index = max(0, min(len(ohlc) - 1, int(round(x_pos))))

        if abs(x_pos - x_index) > x_radius:
            return None

        candle = ohlc.iloc[x_index]

        # Check if y position is within candle range
        if y_pos < candle['low'] - y_radius or y_pos > candle['high'] + y_radius:
            return None

        # Calculate distance to nearest relevant price
        if candle['low'] <= y_pos <= candle['high']:
            y_distance = 0  # Inside the candle
        else:
            y_distance = min(abs(y_pos - candle['low']), abs(y_pos - candle['high']))

        x_distance = abs(x_pos - x_index)
        distance = (x_distance / x_radius) ** 2 + (y_distance / y_radius) ** 2

        # Get timestamp if available
        x_value = self._get_x_display_value(x_index)

        return {
            'type': 'candlestick',
            'name': self._get_symbol_name(),
            'x_index': x_index,
            'x_value': x_value,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle.get('volume'),
            'distance': distance,
        }

    def _check_line_hover(self, item_info, x_pos, y_pos, x_radius, y_radius):
        """Check if hovering over line plot data."""
        x_data = item_info['x_data']
        y_data = item_info['y_data']
        name = item_info['name']

        if len(x_data) == 0 or len(y_data) == 0:
            return None

        # Find nearest x point
        x_array = np.array(x_data)
        y_array = np.array(y_data)

        # Remove NaN values
        valid_mask = ~(np.isnan(y_array) | np.isinf(y_array))
        if not np.any(valid_mask):
            return None

        x_valid = x_array[valid_mask]
        y_valid = y_array[valid_mask]

        x_distances = np.abs(x_valid - x_pos)
        nearest_x_idx = np.argmin(x_distances)

        if x_distances[nearest_x_idx] > x_radius:
            return None

        nearest_x = x_valid[nearest_x_idx]
        nearest_y = y_valid[nearest_x_idx]

        y_distance = abs(y_pos - nearest_y)
        if y_distance > y_radius:
            return None

        distance = (x_distances[nearest_x_idx] / x_radius) ** 2 + (
            y_distance / y_radius
        ) ** 2

        # Map back to original index for x_value display
        original_idx = int(round(nearest_x))
        x_value = self._get_x_display_value(original_idx)

        return {
            'type': 'line',
            'name': name,
            'x_index': original_idx,
            'x_value': x_value,
            'y_value': nearest_y,
            'distance': distance,
        }

    def _check_histogram_hover(self, indicator_plot, x_pos, y_pos, x_radius, y_radius):
        """Check if hovering over histogram bars."""
        # Get all bar items from the indicator plot
        for item in indicator_plot.items:
            if isinstance(item, pg.BarGraphItem):
                return self._check_bar_item_hover(
                    item, indicator_plot, x_pos, y_pos, x_radius, y_radius
                )
        return None

    def _check_bar_item_hover(
        self, bar_item, indicator_plot, x_pos, y_pos, x_radius, y_radius
    ):
        """Check hover on individual bar graph item."""
        try:
            # Get bar data
            bar_data = getattr(bar_item, 'opts', {})
            x_data = bar_data.get('x', [])
            height_data = bar_data.get('height', [])
            width = bar_data.get('width', 0.6)

            if not x_data or not height_data:
                return None

            # Find nearest bar
            x_array = np.array(x_data)
            height_array = np.array(height_data)

            x_distances = np.abs(x_array - x_pos)
            nearest_idx = np.argmin(x_distances)

            nearest_x = x_array[nearest_idx]
            nearest_height = height_array[nearest_idx]

            # Check if within bar bounds
            if abs(x_pos - nearest_x) > width / 2 + x_radius:
                return None

            if y_pos < -y_radius or y_pos > nearest_height + y_radius:
                return None

            distance = (abs(x_pos - nearest_x) / (width / 2 + x_radius)) ** 2
            if y_pos > nearest_height:
                distance += ((y_pos - nearest_height) / y_radius) ** 2
            elif y_pos < 0:
                distance += (abs(y_pos) / y_radius) ** 2

            # Get plot title as name
            name = getattr(indicator_plot, '_title', 'Histogram')
            if hasattr(indicator_plot, 'titleLabel') and indicator_plot.titleLabel:
                name = indicator_plot.titleLabel.text

            x_value = self._get_x_display_value(int(round(nearest_x)))

            return {
                'type': 'histogram',
                'name': name,
                'x_index': int(round(nearest_x)),
                'x_value': x_value,
                'y_value': nearest_height,
                'distance': distance,
            }

        except Exception:
            return None

    def _get_x_display_value(self, x_index):
        """Get display-friendly x value (timestamp or index)."""
        if (
            hasattr(self.plot_window, '_time_values')
            and self.plot_window._time_values is not None
        ):
            if 0 <= x_index < len(self.plot_window._time_values):
                timestamp = self.plot_window._time_values.iloc[x_index]
                return pd.to_datetime(timestamp).strftime('%Y-%m-%d %H:%M')
        return str(x_index)

    def _get_symbol_name(self):
        """Get symbol name from window title or default."""
        title = self.plot_window.windowTitle()
        # Extract symbol from title like "EURUSD 5min"
        parts = title.split()
        if parts:
            return parts[0]
        return "Symbol"

    def _show_tooltip(self):
        """Show tooltip for current hover info."""
        if not self._current_hover or not self._last_mouse_pos:
            return

        html = self._build_tooltip_html(self._current_hover)
        self.tooltip_item.setHtml(html)
        self.tooltip_item.setVisible(True)

        # Position tooltip near cursor
        view_pos = self.view_box.mapSceneToView(self._last_mouse_pos)

        # Offset tooltip to avoid cursor overlap
        try:
            pixel_size = self.view_box.viewPixelSize()
            dx = pixel_size.x() * 16
            dy = -pixel_size.y() * 12
        except Exception:
            dx, dy = 0, 0

        self.tooltip_item.setPos(view_pos.x() + dx, view_pos.y() + dy)

    def _build_tooltip_html(self, hover_info):
        """Build HTML for tooltip display."""
        info_type = hover_info['type']
        name = hover_info['name']
        x_value = hover_info['x_value']

        if info_type == 'candlestick':
            volume_text = ""
            if hover_info['volume'] is not None:
                volume_text = f"<div>Volume: {hover_info['volume']:,.0f}</div>"

            html = f"""
            <div style='background-color:#20222A; color:#eaeaf1; padding:8px 10px; border:1px solid #3A3D47; border-radius:6px;'>
                <div style='font-weight:bold;margin-bottom:4px;'>{name}</div>
                <div style='color:#a7a7b3;margin-bottom:4px;'>{x_value}</div>
                <div>O: {hover_info['open']:.4f}</div>
                <div>H: {hover_info['high']:.4f}</div>
                <div>L: {hover_info['low']:.4f}</div>
                <div>C: {hover_info['close']:.4f}</div>
                {volume_text}
            </div>
            """
        elif info_type == 'line':
            html = f"""
            <div style='background-color:#20222A; color:#eaeaf1; padding:8px 10px; border:1px solid #3A3D47; border-radius:6px;'>
                <div style='font-weight:bold;margin-bottom:4px;'>{name}</div>
                <div style='color:#a7a7b3;margin-bottom:4px;'>{x_value}</div>
                <div>Value: {hover_info['y_value']:.4f}</div>
            </div>
            """
        elif info_type == 'scatter':
            html = f"""
            <div style='background-color:#20222A; color:#eaeaf1; padding:8px 10px; border:1px solid #3A3D47; border-radius:6px;'>
                <div style='font-weight:bold;margin-bottom:4px;'>{name}</div>
                <div style='color:#a7a7b3;margin-bottom:4px;'>{x_value}</div>
                <div>Value: {hover_info['y_value']:.4f}</div>
            </div>
            """
        elif info_type == 'histogram':
            html = f"""
            <div style='background-color:#20222A; color:#eaeaf1; padding:8px 10px; border:1px solid #3A3D47; border-radius:6px;'>
                <div style='font-weight:bold;margin-bottom:4px;'>{name}</div>
                <div style='color:#a7a7b3;margin-bottom:4px;'>{x_value}</div>
                <div>Value: {hover_info['y_value']:,.2f}</div>
            </div>
            """
        else:
            html = f"""
            <div style='background-color:#20222A; color:#eaeaf1; padding:8px 10px; border:1px solid #3A3D47; border-radius:6px;'>
                <div style='font-weight:bold;'>{name}</div>
                <div>{x_value}</div>
            </div>
            """

        return html

    def _hide_tooltip(self):
        """Hide the tooltip."""
        self.tooltip_item.setVisible(False)

    def set_enabled(self, enabled):
        """Enable or disable tooltip functionality."""
        self.enabled = enabled
        if not enabled:
            self._hide_tooltip()

    def _check_scatter_hover(self, item_info, x_pos, y_pos, x_radius, y_radius):
        """Check if hovering over scatter plot data."""
        x_data = item_info['x_data']
        y_data = item_info['y_data']
        name = item_info['name']

        if len(x_data) == 0 or len(y_data) == 0:
            return None

        # Find nearest scatter point
        x_array = np.array(x_data)
        y_array = np.array(y_data)

        # Remove NaN values
        valid_mask = ~(np.isnan(y_array) | np.isinf(y_array))
        if not np.any(valid_mask):
            return None

        x_valid = x_array[valid_mask]
        y_valid = y_array[valid_mask]

        # Calculate distances to all valid points
        x_distances = np.abs(x_valid - x_pos)
        y_distances = np.abs(y_valid - y_pos)

        # Find points within the pick radius (using circular distance)
        within_radius_mask = (x_distances <= x_radius) & (y_distances <= y_radius)

        if not np.any(within_radius_mask):
            return None

        # Among points within radius, find the closest one
        valid_indices = np.where(within_radius_mask)[0]
        distances = np.sqrt(
            (x_distances[valid_indices] / x_radius) ** 2
            + (y_distances[valid_indices] / y_radius) ** 2
        )

        closest_idx = valid_indices[np.argmin(distances)]
        nearest_x = x_valid[closest_idx]
        nearest_y = y_valid[closest_idx]
        distance = distances[np.argmin(distances)]

        # Map back to original index for x_value display
        original_idx = int(round(nearest_x))
        x_value = self._get_x_display_value(original_idx)

        return {
            'type': 'scatter',
            'name': name,
            'x_index': original_idx,
            'x_value': x_value,
            'y_value': nearest_y,
            'distance': distance,
        }


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
        # Store line items for tooltip functionality
        self._line_items = []
        # Store scatter items for tooltip functionality
        self._scatter_items = []

        # Create a plot item for price
        self.price_plot = self.graphWidget.addPlot(row=0, col=0)
        self.price_plot.addLegend()
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)

        # Disable auto-ranging and connect range change handler for dynamic Y zoom
        vb = self.price_plot.getViewBox()
        vb.disableAutoRange()
        self.price_plot.sigXRangeChanged.connect(self._on_x_range_changed)

        # Initialize tooltip controller
        self._tooltip_controller = None

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

    def setup_time_axis(self, ohlc: pd.DataFrame) -> pd.DataFrame:
        """
        Sets up the custom time axis based on the OHLC data.
        Returns a DataFrame with the numeric 'time' column for plotting.
        """
        df = ohlc.copy()
        # If a numeric 'time' column is provided, use the index for datetime values.
        # Otherwise, assume the index is the primary source for datetimes.
        if 'time' in df.columns and pd.api.types.is_numeric_dtype(df['time']):
            time_data = df.index.to_series()
            # The df already has the correct integer indices in the 'time' column.
        else:
            time_data = df.index.to_series()
            # Create integer indices for the x-axis to remove gaps
            df['time'] = list(range(len(df)))

        # Store the original timestamps and set up the custom axis
        # Ensure time_data is properly converted to datetime
        if isinstance(time_data.index, pd.DatetimeIndex):
            # If the index is already datetime, use it directly
            self._time_values = time_data.values
        else:
            # Convert to datetime, handling various input formats
            try:
                self._time_values = pd.to_datetime(time_data).values
            except Exception as e:
                print(f"Warning: Could not convert time_data to datetime: {e}")
                # Fallback: create a dummy datetime range
                self._time_values = pd.date_range(
                    start='2021-01-01', 
                    periods=len(df), 
                    freq='1H'
                ).values
        
        # Validate timestamps and remove any NaT values
        if len(self._time_values) > 0:
            # Check for NaT values and replace them with valid timestamps
            valid_mask = ~pd.isna(self._time_values)
            if not valid_mask.all():
                print(f"Warning: Found {len(self._time_values) - valid_mask.sum()} NaT values in timestamps")
                # Create a valid datetime range for the entire dataset
                if valid_mask.any():
                    # Use the first valid timestamp as reference
                    first_valid_idx = valid_mask.argmax()
                    first_valid_time = self._time_values[first_valid_idx]
                    # Create a continuous datetime range
                    self._time_values = pd.date_range(
                        start=first_valid_time,
                        periods=len(df),
                        freq='1H'
                    ).values
                else:
                    # All timestamps are invalid, create a dummy range
                    self._time_values = pd.date_range(
                        start='2021-01-01',
                        periods=len(df),
                        freq='1H'
                    ).values
        
        date_axis = DateAxis(timestamps=self._time_values, orientation='bottom')
        self.price_plot.setAxisItems({'bottom': date_axis})
        return df

    def add_candlestick_plot(
        self, ohlc: pd.DataFrame, show_volume: bool = False
    ) -> None:
        """
        Adds a candlestick plot to the window.
        This method sets up a custom x-axis to display datetimes without gaps.
        :param ohlc: DataFrame with open, high, low, close columns and a datetime index.
        """
        df_with_numeric_time = self.setup_time_axis(ohlc)
        self._ohlc_data = df_with_numeric_time.reset_index(
            drop=True
        )  # Store for y-range adjustments

        candlestick = CandlestickItem(df_with_numeric_time)
        self.price_plot.addItem(candlestick)

        # Set the initial visible range to the last N candles
        num_candles = len(df_with_numeric_time)
        initial_view_start = max(0, num_candles - self._initial_candles)
        self.price_plot.setXRange(initial_view_start, num_candles)

        # Initialize tooltip controller after candlestick is added
        if self._tooltip_controller is None:
            self._tooltip_controller = ChartTooltipController(self)

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

        # Store line data for tooltip functionality
        self._line_items.append(
            {
                'item': line,
                'x_data': x_numeric.tolist(),
                'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                'name': name,
            }
        )

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
        self._scatter_items.append(
            {
                'item': scatter,
                'x_data': x_numeric.tolist(),
                'y_data': y.tolist() if hasattr(y, 'tolist') else list(y),
                'name': name,
                'size': size,
            }
        )

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
