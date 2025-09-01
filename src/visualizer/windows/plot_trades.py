from src.visualizer.windows.plot_data import PlotWindow

import pandas as pd
import pyqtgraph as pg
from typing import Optional, Callable, Literal
from PySide6.QtWidgets import QApplication


class PlotTradesWindow(PlotWindow):
    def __init__(self, trades: Optional[pd.DataFrame] = None, *, marker_size: int = 10):
        super().__init__()
        self.setWindowTitle("Trades")
        self.marker_size = marker_size
        self._layers: list[pg.ScatterPlotItem] = []

        # Colors/symbols
        self._colors = {"buy": (0, 200, 0), "sell": (220, 50, 50)}
        self._entry_symbols = {"buy": "t", "sell": "t1"}
        self._exit_symbol = "o"

        # Mapping: datetime -> x
        self._time_mapper: Optional[Callable[[pd.Series], pd.Series]] = None
        # Default to datetime mode (POSIX timestamps)
        self.use_datetime_axis()

        self.trades: Optional[pd.DataFrame] = None
        if trades is not None:
            self.set_trades(trades)

    # Integration helpers
    def use_datetime_axis(self) -> None:
        """Use POSIX timestamps as x (when your candlestick axis is datetime)."""
        self._time_mapper = lambda ts: pd.to_datetime(ts).view("int64") / 1e9

    def bind_to_bars(self, ohlc: pd.DataFrame, time_col: str = "time") -> None:
        """
        Bind trades to the same x used by your candlestick item when it uses numeric bar x.
        - If ohlc[time_col] is numeric: map trade datetimes to nearest bar x.
        - If ohlc[time_col] looks like datetime: we fallback to datetime axis mapping.
        """
        if time_col not in ohlc.columns:
            # Fall back to datetime axis using index if no time column
            self.use_datetime_axis()
            return

        col = ohlc[time_col]
        # If column looks like datetimes, prefer datetime axis
        if pd.api.types.is_datetime64_any_dtype(col):
            self.use_datetime_axis()
            return

        # Numeric x, but need datetimes per bar to match trades by timestamp
        # Prefer index for bar datetimes; if not datetime index, try to parse 'start'/'end' later
        bar_times = ohlc.index
        if not isinstance(bar_times, pd.DatetimeIndex):
            # No datetime index available; still allow numeric x mapping by nearest integer bar
            x_vals = col.astype(float).to_numpy()

            def map_numeric(ts: pd.Series) -> pd.Series:
                # Without timestamps for bars, best effort: round to nearest integer
                # Expect caller to pre-map trade times externally if needed.
                return pd.Series(
                    pd.to_numeric(ts.index, errors="coerce"), index=ts.index
                )

            self._time_mapper = map_numeric
            return

        # Build nearest-bar mapping with known bar datetimes + numeric x
        x_vals = col.astype(float).to_numpy()
        #        bar_times = pd.to_datetime(bar_times).view("int64").to_numpy()  # ns
        bar_times = pd.to_datetime(bar_times).view("int64")
        # Ensure monotonic for searchsorted
        # If not monotonic, we sort both arrays together
        if not (pd.Index(bar_times).is_monotonic_increasing):
            order = bar_times.argsort()
            bar_times = bar_times[order]
            x_vals = x_vals[order]

        def map_to_nearest_bar(ts: pd.Series) -> pd.Series:
            ts_ns = pd.to_datetime(ts).view("int64").to_numpy()
            idxs = pd.Index(bar_times).searchsorted(ts_ns, side="left")
            idxs = idxs.clip(0, len(x_vals) - 1)
            # Pick nearest between idxs and idxs-1
            left = (idxs - 1).clip(0, len(x_vals) - 1)
            choose_left = (idxs == len(x_vals)) | (
                (ts_ns - bar_times[left]) <= (bar_times[idxs] - ts_ns).clip(min=0)
            )
            nearest = left.copy()
            nearest[~choose_left] = idxs[~choose_left]
            return pd.Series(x_vals[nearest], index=ts.index)

        self._time_mapper = map_to_nearest_bar

    # Public API
    def set_trades(self, trades: pd.DataFrame) -> None:
        self._validate_columns(trades)
        self.trades = trades.copy()
        self.trades["start"] = pd.to_datetime(self.trades["start"])
        self.trades["end"] = pd.to_datetime(self.trades["end"])
        self._render()

    def add_trades(self, trades: pd.DataFrame) -> None:
        self._validate_columns(trades)
        trades = trades.copy()
        trades["start"] = pd.to_datetime(trades["start"])
        trades["end"] = pd.to_datetime(trades["end"])
        if self.trades is None:
            self.trades = trades
        else:
            self.trades = pd.concat([self.trades, trades], axis=0, ignore_index=True)
        self._render()

    def clear_trades(self) -> None:
        for it in self._layers:
            try:
                self.plot.removeItem(it)
            except Exception:
                pass
        self._layers.clear()

    # Internal
    def _render(self) -> None:
        self.clear_trades()
        if self.trades is None or self.trades.empty:
            return

        df = self.trades

        buy_mask = df["type"].str.lower() == "buy"
        sell_mask = df["type"].str.lower() == "sell"

        # Entries
        x_buy_entry = self._map_time(df.loc[buy_mask, "start"])
        y_buy_entry = df.loc[buy_mask, "buyprice"].astype(float)
        x_sell_entry = self._map_time(df.loc[sell_mask, "start"])
        y_sell_entry = df.loc[sell_mask, "sellprice"].astype(float)

        # Exits
        x_buy_exit = self._map_time(df.loc[buy_mask, "end"])
        y_buy_exit = df.loc[buy_mask, "sellprice"].astype(float)
        x_sell_exit = self._map_time(df.loc[sell_mask, "end"])
        y_sell_exit = df.loc[sell_mask, "buyprice"].astype(float)

        if len(x_buy_entry) > 0:
            self._add_scatter(
                x_buy_entry,
                y_buy_entry,
                color=self._colors["buy"],
                symbol=self._entry_symbols["buy"],
                name="Buy Entry",
            )
        if len(x_sell_entry) > 0:
            self._add_scatter(
                x_sell_entry,
                y_sell_entry,
                color=self._colors["sell"],
                symbol=self._entry_symbols["sell"],
                name="Sell Entry",
            )
        if len(x_buy_exit) > 0:
            self._add_scatter(
                x_buy_exit,
                y_buy_exit,
                color=self._colors["buy"],
                symbol=self._exit_symbol,
                name="Buy Exit",
            )
        if len(x_sell_exit) > 0:
            self._add_scatter(
                x_sell_exit,
                y_sell_exit,
                color=self._colors["sell"],
                symbol=self._exit_symbol,
                name="Sell Exit",
            )

    def _map_time(self, ts: pd.Series) -> pd.Series:
        return (
            self._time_mapper(ts)
            if self._time_mapper is not None
            else pd.to_datetime(ts).view("int64") / 1e9
        )

    def _add_scatter(self, x, y, *, color, symbol: str, name: str) -> None:
        brush = pg.mkBrush(*color, 170)
        pen = pg.mkPen(color, width=1.5)
        item = pg.ScatterPlotItem(
            x=list(x),
            y=list(y),
            size=self.marker_size,
            brush=brush,
            pen=pen,
            symbol=symbol,
            name=name,
        )
        self.plot.addItem(item)
        self._layers.append(item)

    def _validate_columns(self, df: pd.DataFrame) -> None:
        required = {"start", "end", "amount", "type", "buyprice", "sellprice"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(
                f"Trades DataFrame is missing required columns: {sorted(missing)}"
            )


# --- Orchestration helpers colocated with PlotTradesWindow ---


def create_candlestick_with_trades(
    ohlc_data: pd.DataFrame,
    trades_df: pd.DataFrame,
    *,
    time_mode: Literal["auto", "datetime", "bars"] = "auto",
    time_col: str = "time",
    marker_size: int = 10,
) -> PlotTradesWindow:
    """
    Create a PlotTradesWindow, add candlesticks, align, and render trade markers.

    Args:
        ohlc_data: OHLC DataFrame. If it lacks a 'time' column, one will be created from the index by the window.
        trades_df: Trades DataFrame with columns like trades.csv (start, end, type, buyprice, sellprice, ...).
        time_mode: 'datetime' to use POSIX timestamps, 'bars' to bind to numeric bar x-axis,
                   or 'auto' to infer from ohlc_data[time_col] dtype.
        time_col: Name of the column used by the candlestick for x-axis when time_mode='bars'.
        marker_size: Marker size for ScatterPlotItems.

    Returns:
        A configured PlotTradesWindow with both candles and trade markers.
    """
    window = PlotTradesWindow(marker_size=marker_size)
    window.add_candlestick_plot(ohlc_data)

    # Choose alignment mode
    if time_mode == "datetime":
        window.use_datetime_axis()
    elif time_mode == "bars":
        window.bind_to_bars(ohlc_data, time_col=time_col)
    else:
        # auto
        if time_col in ohlc_data.columns and pd.api.types.is_numeric_dtype(
            ohlc_data[time_col]
        ):
            window.bind_to_bars(ohlc_data, time_col=time_col)
        else:
            window.use_datetime_axis()

    window.set_trades(trades_df)
    return window


def show_candlestick_with_trades(
    ohlc_data: pd.DataFrame,
    trades_df: pd.DataFrame,
    *,
    title: str = "Candlestick + Trades",
    time_mode: Literal["auto", "datetime", "bars"] = "auto",
    time_col: str = "time",
    marker_size: int = 10,
    block: Optional[bool] = None,
) -> PlotTradesWindow:
    """
    Create and display a PlotTradesWindow with candlesticks and trade markers.

    Args:
        ohlc_data: OHLC DataFrame.
        trades_df: Trades DataFrame (columns as in trades.csv).
        title: Window title.
        time_mode: Axis alignment mode. See create_candlestick_with_trades.
        time_col: Column name used for 'bars' mode.
        marker_size: Scatter marker size.
        block: Whether to block execution running the event loop. If None, defaults to True if a QApplication is created here.

    Returns:
        The PlotTradesWindow instance.
    """
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication([])
        created_app = True

    window = create_candlestick_with_trades(
        ohlc_data=ohlc_data,
        trades_df=trades_df,
        time_mode=time_mode,
        time_col=time_col,
        marker_size=marker_size,
    )
    window.setWindowTitle(title)
    window.show()

    # Decide whether to block
    if block is None:
        block = created_app  # if we created the app here, default to blocking

    if block:
        app.exec()

    return window
