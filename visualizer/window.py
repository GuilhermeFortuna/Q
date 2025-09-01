import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow
from visualizer.plots import CandlestickItem
from visualizer.plots import LinePlotItem
import pandas as pd

class PlotWindow(QMainWindow):
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
        #self.df = pd.DataFrame(self.data)

        # Create a plot item
        self.plot = self.graphWidget.addPlot(row=0, col=0)


    def _load_data_from_file(self, file_path):
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

    def create_candlestick_plot(self, ohlc: pd.DataFrame) -> None:
        if 'time' not in ohlc.columns:
            ohlc['time'] = ohlc.index.copy()
        candlestick = CandlestickItem(ohlc)
        self.plot.addItem(candlestick)

    def create_line_plot(self, x, y, name, color, width):
        line = LinePlotItem(x, y, name=name, color=color, width=width)
        self.plot.addItem(line)


if __name__ == '__main__':pass
