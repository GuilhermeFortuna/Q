import pyqtgraph as pg

class LinePlotItem(pg.PlotDataItem):
    def __init__(self, x, y, name: str, color: str = 'yellow', width: int = 2):
        """
        A wrapper for pyqtgraph.PlotDataItem to be used for line plots.
        :param x: A list or array of x-axis data.
        :param y: A list or array of y-axis data.
        :param kwargs: Additional keyword arguments to pass to PlotDataItem.
        """
        pen = pg.mkPen(color=color, width=width)
        super().__init__(x, y, pen=pen, name=name)
