import pyqtgraph as pg
from PySide6.QtWidgets import QApplication
from src.visualizer.plots import CandlestickItem
from src.visualizer.plots import LinePlotItem
import pandas as pd

from src.visualizer.windows.base import BaseWindow


class PlotWindow(BaseWindow):
    """
    A class representing a window for plotting market data.

    This class is designed to display and manage various types of financial
    charts, such as candlestick and line plots, using the plotting functionality
    provided by pyqtgraph. The `PlotWindow` allows users to visualize market data
    in a graphical format, facilitating analysis and interpretation.

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

    def __init__(self, data: list = None):
        super(PlotWindow, self).__init__()
        self.graphWidget = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.graphWidget)
        self.setWindowTitle("Market Data")

        self.data = data
        # self.df = pd.DataFrame(self.data)

        # Create a plot item
        self.plot = self.graphWidget.addPlot(row=0, col=0)

    def _load_data_from_file(self, file_path):  # TODO: Maybe remove this private method
        """Loads and prepares data from a CSV file."""
        try:
            self.data = pd.read_csv(file_path)
            if isinstance(self.data, pd.DataFrame) and not self.data.empty:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def add_candlestick_plot(self, ohlc: pd.DataFrame) -> None:
        if 'time' not in ohlc.columns:
            ohlc['time'] = ohlc.index.copy()
        candlestick = CandlestickItem(ohlc)
        self.plot.addItem(candlestick)

    def add_line_plot(self, x, y, name, color, width) -> None:
        line = LinePlotItem(x, y, name=name, color=color, width=width)
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
    candle_data.insert(0, 'time', list(range(len(candle_data))))

    q_app = QApplication(sys.argv)
    plot_window = PlotWindow()
    plot_window.add_candlestick_plot(candle_data)
    # plot_window.create_line_plot(x=x, y=y, name='Close', color='yellow', width=2)
    plot_window.show()
    sys.exit(q_app.exec())
