from src.visualizer.windows.plot_data import PlotWindow

import pandas as pd
import numpy as np
import pyqtgraph as pg
from pyqtgraph import QtCore
from typing import Optional, Callable, Literal
import datetime as dt
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QDateTimeEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QGraphicsPathItem,
)
from PySide6.QtCore import QDateTime as PQtDateTime, Qt as PQt
from PySide6.QtGui import QPainterPath, QPen, QColor

from src.visualizer.models import IndicatorConfig

DEFAULT_TRADE_MARKER_SIZE = 20


class PlotTradesWindow(PlotWindow):
    """
    Provides functionality to display and manage a plotting window for trades.

    The PlotTradesWindow class is designed for visualizing trade data within a customized
    plotting environment. The window supports displaying trades with specific attributes,
    enabling control over timeline filters, mapping trade timestamps, and integrating with
    candlestick charts' axes. Users can manage trade data dynamically by adding, clearing,
    or modifying trades. It maintains compatibility with datetime and numeric axes for enhanced
    usability and allows state-based control of trade rendering based on outcomes such as
    profit, loss, or flat trades.

    :ivar marker_size: Defines the size of markers used in the trade visualization.
    :type marker_size: int
    :ivar trades: Holds the trades DataFrame for visualizing transaction data.
    :type trades: Optional[pandas.DataFrame]
    """

    def __init__(
        self,
        trades: Optional[pd.DataFrame] = None,
        *,
        marker_size: int = DEFAULT_TRADE_MARKER_SIZE,
    ):
        super().__init__()
        self.setWindowTitle("Trades")
        self.marker_size = marker_size

        # Add a reference to the main plot for backward compatibility
        self.plot = self.price_plot

        # Data
        self._ohlc_data: Optional[pd.DataFrame] = None
        self.trades: Optional[pd.DataFrame] = None

        # Plot items
        self._candlestick_item: Optional[pg.GraphicsObject] = None
        self._layers: list[pg.GraphicsObject] = []

        # Rendering options
        self._filter_candles = True
        self._show_entries = True
        self._show_exits = True
        self._show_links = True
        self._outcome_filter = "All"

        # Time filter state
        self._filter_start: Optional[pd.Timestamp] = None
        self._filter_end: Optional[pd.Timestamp] = None
        self._filtered_trades: Optional[pd.DataFrame] = None

        # Colors/symbols
        self._colors = {
            "buy": (40, 220, 130),
            "sell": (255, 90, 90),
        }  # Distinct Red/Green Tones
        self._entry_symbols = {"buy": "t", "sell": "t1"}
        self._exit_symbol = "o"
        # Outcome colors for future link/annotation usage
        self._outcome_colors = {
            "win": (0, 200, 0),
            "loss": (220, 50, 50),
            "flat": (160, 160, 160),
        }

        # Mapping: datetime -> x
        self._time_mapper: Optional[Callable[[pd.Series], pd.Series]] = None
        # Default to datetime mode (POSIX timestamps)
        self.use_datetime_axis()

        # Initialize time filter UI
        self._init_time_filter_ui()

        if trades is not None:
            self.set_trades(trades)

    def add_candlestick_plot(
        self, ohlc: pd.DataFrame, show_volume: bool = False
    ) -> None:
        """
        Sets up the time axis and stores the OHLC data for deferred rendering
        in the _render method. It does not draw the candlestick item itself.
        """
        # Call the new setup method from the parent to configure the time axis
        # and get back the ohlc data with the correct integer 'time' column.
        df_with_numeric_time = self.setup_time_axis(ohlc)
        self._ohlc_data = df_with_numeric_time
        # Note: We do NOT add the candlestick item here.
        # That is handled by the self._render() method, which allows us
        # to control the layering and visibility of all plot items.
        if show_volume:
            self.add_volume_subplot()

    # Integration helpers
    def use_datetime_axis(self) -> None:
        """Use POSIX timestamps as x (when your candlestick axis is datetime)."""
        self._time_mapper = lambda ts: pd.to_datetime(ts).view("int64") / 1e9
        # Recompute mapped x fields if trades are already loaded
        trades = getattr(self, "trades", None)
        if trades is not None and not trades.empty:
            self._precompute_trade_fields()

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
        # Recompute mapped x fields if trades are already loaded
        trades = getattr(self, "trades", None)
        if trades is not None and not trades.empty:
            self._precompute_trade_fields()

    # Public API
    def set_trades(self, trades: pd.DataFrame) -> None:
        self._validate_columns(trades)
        self.trades = trades.copy()
        self.trades["start"] = pd.to_datetime(self.trades["start"])
        self.trades["end"] = pd.to_datetime(self.trades["end"])
        self._precompute_trade_fields()
        self._refresh_filter_controls_bounds()
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
        self._precompute_trade_fields()
        self._refresh_filter_controls_bounds()
        self._render()

    def clear_trades(self) -> None:
        for it in self._layers:
            try:
                self.plot.removeItem(it)
            except Exception:
                pass
        self._layers.clear()

    def _precompute_trade_fields(self) -> None:
        """
        Precompute per-trade fields used by rendering and future enhancements:
        - _side: normalized 'buy'/'sell'
        - _y_entry, _y_exit: entry and exit prices per side
        - _x_start, _x_end: mapped x positions using current time mapper
        - _is_win, _is_lose, _is_flat, _outcome: outcome classification based on profit/delta
        """
        if self.trades is None or self.trades.empty:
            return

        df = self.trades

        # Normalize side and ensure numeric price columns
        side = df["type"].astype(str).str.lower().str.strip()
        df["_side"] = side

        buyprice = pd.to_numeric(df["buyprice"], errors="coerce")
        sellprice = pd.to_numeric(df["sellprice"], errors="coerce")

        # Entry/exit price by side
        df["_y_entry"] = buyprice.where(side == "buy", sellprice)
        df["_y_exit"] = sellprice.where(side == "buy", buyprice)

        # Mapped x (depends on current mapper)
        df["_x_start"] = self._map_time(df["start"])
        df["_x_end"] = self._map_time(df["end"])

        # Outcome metric: prefer 'profit' (from trades.csv), then 'delta', else price diff
        if "profit" in df.columns:
            profit_series = pd.to_numeric(df["profit"], errors="coerce")
        else:
            profit_series = pd.Series(pd.NA, index=df.index, dtype="float64")

        if "delta" in df.columns:
            delta_series = pd.to_numeric(df["delta"], errors="coerce")
        else:
            delta_series = pd.Series(pd.NA, index=df.index, dtype="float64")

        price_diff = (
            sellprice - buyprice
        )  # fallback if neither profit nor delta is available

        outcome_metric = profit_series
        if outcome_metric.isna().any():
            outcome_metric = outcome_metric.fillna(delta_series)
        if outcome_metric.isna().any():
            outcome_metric = outcome_metric.fillna(price_diff)

        df["_is_win"] = outcome_metric > 0
        df["_is_lose"] = outcome_metric < 0
        df["_is_flat"] = ~(df["_is_win"] | df["_is_lose"])
        df["_outcome"] = pd.Series("flat", index=df.index)
        df.loc[df["_is_win"], "_outcome"] = "win"
        df.loc[df["_is_lose"], "_outcome"] = "loss"

    # ---- Time filter UI and API ----

    def _init_time_filter_ui(self) -> None:
        """Create docked time filter controls with quick ranges."""
        self._filter_dock = QDockWidget("Time Filter", self)
        self._filter_dock.setObjectName("TimeFilterDock")
        w = QWidget(self._filter_dock)
        vbox = QVBoxLayout(w)

        # Quick ranges
        rng_row = QHBoxLayout()
        rng_label = QLabel("Quick range:")
        self._cmb_quick_range = QComboBox()
        self._cmb_quick_range.addItems(
            [
                "All",
                "Today",
                "Last 1D",
                "Last 7D",
                "Last 30D",
                "Month-to-date",
                "Custom",
            ]
        )
        rng_row.addWidget(rng_label)
        rng_row.addWidget(self._cmb_quick_range)
        vbox.addLayout(rng_row)

        # Start/End editors
        dt_row1 = QHBoxLayout()
        lbl_start = QLabel("Start:")
        self._dt_start = QDateTimeEdit()
        self._dt_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._dt_start.setCalendarPopup(True)
        dt_row1.addWidget(lbl_start)
        dt_row1.addWidget(self._dt_start)
        vbox.addLayout(dt_row1)

        dt_row2 = QHBoxLayout()
        lbl_end = QLabel("End:")
        self._dt_end = QDateTimeEdit()
        self._dt_end.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._dt_end.setCalendarPopup(True)
        dt_row2.addWidget(lbl_end)
        dt_row2.addWidget(self._dt_end)
        vbox.addLayout(dt_row2)

        # Buttons
        btn_row = QHBoxLayout()
        self._btn_apply = QPushButton("Apply")
        self._btn_reset = QPushButton("Reset")
        btn_row.addWidget(self._btn_apply)
        btn_row.addWidget(self._btn_reset)
        vbox.addLayout(btn_row)

        vbox.addSpacing(10)
        # Add a separator or label for view options
        view_options_label = QLabel("View Options")
        vbox.addWidget(view_options_label)

        # Checkbox for filtering candles
        self._chk_filter_candles = QCheckBox("Filter candlesticks")
        self._chk_filter_candles.setChecked(self._filter_candles)
        self._chk_filter_candles.stateChanged.connect(self._on_filter_candles_changed)
        vbox.addWidget(self._chk_filter_candles)

        # Trade visibility toggles
        toggles_row = QHBoxLayout()
        self._chk_show_entries = QCheckBox("Entries")
        self._chk_show_entries.setChecked(self._show_entries)
        self._chk_show_entries.stateChanged.connect(self._on_show_entries_changed)
        toggles_row.addWidget(self._chk_show_entries)

        self._chk_show_exits = QCheckBox("Exits")
        self._chk_show_exits.setChecked(self._show_exits)
        self._chk_show_exits.stateChanged.connect(self._on_show_exits_changed)
        toggles_row.addWidget(self._chk_show_exits)

        self._chk_show_links = QCheckBox("Links")
        self._chk_show_links.setChecked(self._show_links)
        self._chk_show_links.stateChanged.connect(self._on_show_links_changed)
        toggles_row.addWidget(self._chk_show_links)
        vbox.addLayout(toggles_row)

        # Outcome filter
        outcome_row = QHBoxLayout()
        outcome_label = QLabel("Outcome:")
        self._cmb_outcome_filter = QComboBox()
        self._cmb_outcome_filter.addItems(["All", "Win", "Loss", "Flat"])
        self._cmb_outcome_filter.currentTextChanged.connect(
            self._on_outcome_filter_changed
        )
        outcome_row.addWidget(outcome_label)
        outcome_row.addWidget(self._cmb_outcome_filter)
        vbox.addLayout(outcome_row)

        w.setLayout(vbox)
        self._filter_dock.setWidget(w)
        self.addDockWidget(PQt.RightDockWidgetArea, self._filter_dock)

        # Connections
        self._cmb_quick_range.currentTextChanged.connect(self._on_quick_range_changed)
        self._btn_apply.clicked.connect(self._apply_filter_and_render)
        self._btn_reset.clicked.connect(self.clear_time_filter)

        # Initial state
        self._set_filter_controls_enabled(False)

    def _on_filter_candles_changed(self, state: int) -> None:
        self._filter_candles = bool(state)
        self._render()

    def _on_show_entries_changed(self, state: int) -> None:
        self._show_entries = bool(state)
        self._render()

    def _on_show_exits_changed(self, state: int) -> None:
        self._show_exits = bool(state)
        self._render()

    def _on_show_links_changed(self, state: int) -> None:
        self._show_links = bool(state)
        self._render()

    def _on_outcome_filter_changed(self, text: str) -> None:
        self._outcome_filter = text
        self._render()

    def _set_filter_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self._cmb_quick_range,
            self._dt_start,
            self._dt_end,
            self._btn_apply,
            self._btn_reset,
            self._chk_filter_candles,
            self._chk_show_entries,
            self._chk_show_exits,
            self._chk_show_links,
            self._cmb_outcome_filter,
        ):
            widget.setEnabled(enabled)

    def _refresh_filter_controls_bounds(self) -> None:
        """Set min/max bounds of editors based on trades and initialize values if needed."""
        if self.trades is None or self.trades.empty:
            self._set_filter_controls_enabled(False)
            return

        self._set_filter_controls_enabled(True)

        min_start = pd.to_datetime(self.trades["start"]).min()
        max_end = pd.to_datetime(self.trades["end"]).max()

        def to_qdt(ts: pd.Timestamp) -> PQtDateTime:
            secs = int(pd.Timestamp(ts).timestamp())
            return PQtDateTime.fromSecsSinceEpoch(secs)

        qmin = to_qdt(min_start)
        qmax = to_qdt(max_end)

        self._dt_start.setMinimumDateTime(qmin)
        self._dt_start.setMaximumDateTime(qmax)
        self._dt_end.setMinimumDateTime(qmin)
        self._dt_end.setMaximumDateTime(qmax)

        # Initialize editors if unset
        if self._filter_start is None:
            self._dt_start.setDateTime(qmin)
        else:
            # clamp to bounds
            fs = max(min_start, self._filter_start)
            fs = min(max_end, fs)
            self._dt_start.setDateTime(to_qdt(fs))

        if self._filter_end is None:
            self._dt_end.setDateTime(qmax)
        else:
            fe = max(min_start, self._filter_end)
            fe = min(max_end, fe)
            self._dt_end.setDateTime(to_qdt(fe))

        # Default quick range to 'All' if no filter
        if self._filter_start is None and self._filter_end is None:
            self._cmb_quick_range.setCurrentText("All")

    def _on_quick_range_changed(self, text: str) -> None:
        if self.trades is None or self.trades.empty:
            return
        min_start = pd.to_datetime(self.trades["start"]).min()
        max_end = pd.to_datetime(self.trades["end"]).max()

        now = pd.Timestamp.now()
        # Base end defaults to dataset max for last-X ranges
        end = max_end
        start = None

        if text == "All":
            self.clear_time_filter()
            # Also set editors to bounds for clarity
            self._refresh_filter_controls_bounds()
            return
        elif text == "Today":
            # Today by calendar day in local time
            start = now.normalize()
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        elif text == "Last 1D":
            start = end - pd.Timedelta(days=1)
        elif text == "Last 7D":
            start = end - pd.Timedelta(days=7)
        elif text == "Last 30D":
            start = end - pd.Timedelta(days=30)
        elif text == "Month-to-date":
            month_start = pd.Timestamp(year=end.year, month=end.month, day=1)
            start = month_start
        elif text == "Custom":
            # Do not auto-apply; user will adjust and hit Apply
            return
        else:
            return

        # Clamp to dataset bounds
        if start is not None:
            start = max(min_start, start)
        if end is not None:
            end = min(max_end, end)

        self.set_time_filter(start, end)

    def _apply_filter_and_render(self) -> None:
        # Read from editors and apply
        if self.trades is None or self.trades.empty:
            return
        fs = pd.to_datetime(self._dt_start.dateTime().toSecsSinceEpoch(), unit="s")
        fe = pd.to_datetime(self._dt_end.dateTime().toSecsSinceEpoch(), unit="s")
        self.set_time_filter(fs, fe)

    def set_time_filter(
        self, start: Optional[pd.Timestamp], end: Optional[pd.Timestamp]
    ) -> None:
        """Set current time filter and re-render."""
        # Normalize order
        if start is not None and end is not None and start > end:
            start, end = end, start

        self._filter_start = None if start is None else pd.to_datetime(start)
        self._filter_end = None if end is None else pd.to_datetime(end)

        # Sync editors
        def to_qdt(ts: pd.Timestamp) -> PQtDateTime:
            secs = int(pd.Timestamp(ts).timestamp())
            return PQtDateTime.fromSecsSinceEpoch(secs)

        if self.trades is not None and not self.trades.empty:
            self._refresh_filter_controls_bounds()
            if self._filter_start is not None:
                self._dt_start.setDateTime(to_qdt(self._filter_start))
            if self._filter_end is not None:
                self._dt_end.setDateTime(to_qdt(self._filter_end))

        self._render()

    def clear_time_filter(self) -> None:
        """Clear the current time filter and re-render full data."""
        self._filter_start = None
        self._filter_end = None
        if hasattr(self, "_cmb_quick_range"):
            self._cmb_quick_range.setCurrentText("All")
        if self.trades is not None and not self.trades.empty:
            self._refresh_filter_controls_bounds()
        self._render()

    def get_time_filter(self) -> tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """Return the current (start, end) filter."""
        return self._filter_start, self._filter_end

    def _apply_time_filter(self) -> pd.DataFrame:
        """Return filtered trades according to current time filter (overlap semantics)."""
        if self.trades is None or self.trades.empty:
            return pd.DataFrame(columns=[])

        df = self.trades
        if self._filter_start is not None or self._filter_end is not None:
            start = (
                self._filter_start
                if self._filter_start is not None
                else pd.to_datetime(df["start"]).min()
            )
            end = (
                self._filter_end
                if self._filter_end is not None
                else pd.to_datetime(df["end"]).max()
            )

            mask = (df["start"] <= end) & (df["end"] >= start)
            df = df.loc[mask]

        # Apply outcome filter
        if self._outcome_filter != "All":
            df = df.loc[df["_outcome"] == self._outcome_filter.lower()]

        return df

    def _update_plot_view_range(self, df_filtered: pd.DataFrame) -> None:
        """Adjust the x-range of the plot to match the current filter selection or filtered data span."""
        if df_filtered is None or df_filtered.empty:
            return

        # Prefer explicit filter bounds when set
        if self._filter_start is not None:
            x0 = float(self._map_time(pd.Series([self._filter_start])).iloc[0])
        else:
            x0 = float(df_filtered["_x_start"].min())

        if self._filter_end is not None:
            x1 = float(self._map_time(pd.Series([self._filter_end])).iloc[0])
        else:
            x1 = float(df_filtered["_x_end"].max())

        if x0 == x1:
            # Avoid zero-width range
            pad = 1.0
            x0 -= pad
            x1 += pad

        try:
            self.plot.setXRange(x0, x1, padding=0.02)
        except Exception:
            pass

    # Internal
    def _render(self) -> None:
        self.clear_trades()
        if self._candlestick_item:
            self.plot.removeItem(self._candlestick_item)
            self._candlestick_item = None

        # Render candlesticks
        ohlc_to_render = self._ohlc_data
        if ohlc_to_render is not None and not ohlc_to_render.empty:
            start, end = self.get_time_filter()
            if self._filter_candles and start and end:
                if isinstance(ohlc_to_render.index, pd.DatetimeIndex):
                    # Slice data, ensuring we don't fail on missing dates
                    ohlc_to_render = ohlc_to_render.loc[
                        ohlc_to_render.index.to_series().between(start, end)
                    ]

            if not ohlc_to_render.empty:
                CandlestickItem = self.PLOT_TYPE_MAP["candlestick"]
                self._candlestick_item = CandlestickItem(ohlc_to_render)
                self.plot.addItem(self._candlestick_item)

        if self.trades is None or self.trades.empty:
            self._update_plot_view_range(
                pd.DataFrame()
            )  # Pass empty to maybe reset zoom
            return

        df = self._apply_time_filter()
        if df is None or df.empty:
            self._update_plot_view_range(df)
            return

        buy_mask = df["type"].str.lower() == "buy"
        sell_mask = df["type"].str.lower() == "sell"

        # Entries (batched: single item, per-spot symbols/colors)
        if self._show_entries:
            x_ent = df["_x_start"].astype(float).to_numpy()
            y_ent = df["_y_entry"].astype(float).to_numpy()
            side_ent = df["_side"].astype(str).to_numpy()
            if x_ent.size > 0:
                # Symbols: triangle up for buy ('t'), triangle down for sell ('t1')
                symbols_ent = np.where(side_ent == "buy", "t", "t1")
                # Colors by side
                condition = (side_ent == "buy")[:, np.newaxis]
                colors_ent = np.where(
                    condition, self._colors["buy"], self._colors["sell"]
                )
                # Use a white pen for a visible outline
                outline_pen = pg.mkPen((240, 240, 240), width=1)
                pens_ent = [outline_pen] * len(x_ent)
                brushes_ent = [pg.mkBrush(*c, 200) for c in colors_ent]
                self._add_scatter_batch(
                    x_ent,
                    y_ent,
                    symbols=symbols_ent,
                    brushes=brushes_ent,
                    pens=pens_ent,
                    name="Entries",
                )

        # Exits (batched: single item, ring markers via transparent brush)
        if self._show_exits:
            x_ex = df["_x_end"].astype(float).to_numpy()
            y_ex = df["_y_exit"].astype(float).to_numpy()
            side_ex = df["_side"].astype(str).to_numpy()
            if x_ex.size > 0:
                symbols_ex = np.array(["o"] * len(x_ex))
                # Colors by side
                condition = (side_ex == "buy")[:, np.newaxis]
                colors_ex = np.where(
                    condition, self._colors["buy"], self._colors["sell"]
                )
                pens_ex = [pg.mkPen(tuple(c), width=1.8) for c in colors_ex]
                transparent = pg.mkBrush(0, 0, 0, 0)
                brushes_ex = [transparent] * len(x_ex)
                self._add_scatter_batch(
                    x_ex,
                    y_ex,
                    symbols=symbols_ex,
                    brushes=brushes_ex,
                    pens=pens_ex,
                    name="Exits",
                )

        # Dashed link lines: entry -> exit, colored by outcome (win/loss/flat)
        if self._show_links:
            self._add_trade_link_batches(df)

        # Adjust view to current filter selection
        self._update_plot_view_range(df)

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

    def _add_scatter_batch(
        self,
        x,
        y,
        *,
        symbols=None,
        brushes=None,
        pens=None,
        name: str = "",
        size: Optional[int] = None,
    ) -> None:
        """
        Add a single ScatterPlotItem with per-spot customization.
        - x, y: sequences
        - symbols: sequence of per-spot symbols (or single symbol)
        - brushes: sequence of pg.Brush or color tuples per spot
        - pens: sequence of pg.Pen or color tuples per spot
        - name: legend name
        - size: marker size (if None uses self.marker_size)
        """
        if x is None:
            return
        x_list = list(x)
        if len(x_list) == 0:
            return
        y_list = list(y)
        if size is None:
            size = self.marker_size
        item = pg.ScatterPlotItem()
        kwargs = {
            "x": x_list,
            "y": y_list,
            "size": size,
            "name": name,
        }
        if symbols is not None:
            kwargs["symbol"] = list(symbols)
        if brushes is not None:
            kwargs["brush"] = list(brushes)
        if pens is not None:
            kwargs["pen"] = list(pens)
        item.setData(**kwargs)
        self.plot.addItem(item)
        self._layers.append(item)

    def _add_trade_link_batches(self, df: pd.DataFrame) -> None:
        """
        Draw dashed link lines from entry to exit using a single QGraphicsPathItem per outcome.
        This reduces item count and allows cosmetic dashed pens for clarity at all zoom levels.
        """
        if df is None or df.empty:
            return

        for outcome in ("win", "loss", "flat"):
            mask = df["_outcome"] == outcome
            if not mask.any():
                continue

            x_start = df.loc[mask, "_x_start"].astype(float).to_numpy()
            x_end = df.loc[mask, "_x_end"].astype(float).to_numpy()
            y_entry = df.loc[mask, "_y_entry"].astype(float).to_numpy()
            y_exit = df.loc[mask, "_y_exit"].astype(float).to_numpy()

            if x_start.size == 0:
                continue

            path = QPainterPath()
            # Build many small segments via moveTo/lineTo
            path.moveTo(float(x_start[0]), float(y_entry[0]))
            path.lineTo(float(x_end[0]), float(y_exit[0]))
            for i in range(1, len(x_start)):
                path.moveTo(float(x_start[i]), float(y_entry[i]))
                path.lineTo(float(x_end[i]), float(y_exit[i]))

            item = QGraphicsPathItem(path)
            r, g, b = self._outcome_colors.get(outcome, (160, 160, 160))
            pen = QPen(QColor(r, g, b, 200))
            pen.setCosmetic(True)
            pen.setWidthF(1.8)
            pen.setStyle(QtCore.Qt.DashLine)
            item.setPen(pen)
            item.setZValue(-1)  # behind markers
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
    indicators: Optional[list[IndicatorConfig]] = None,
    time_mode: Literal["auto", "datetime", "bars"] = "auto",
    time_col: str = "time",
    marker_size: int = DEFAULT_TRADE_MARKER_SIZE,
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
    # This now calls the overridden method in PlotTradesWindow
    window.add_candlestick_plot(ohlc_data)

    # Choose alignment mode first, so the time mapper is ready
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

    # Set trades, which triggers the primary render of candles and trade markers
    window.set_trades(trades_df)

    # Now, with the primary plot established, add the indicators
    if indicators:
        for config in indicators:
            if config.type == "line":
                window.add_line_plot(
                    x=ohlc_data.index,
                    y=config.y,
                    name=config.name,
                    color=config.color,
                    width=config.width,
                )

    return window


def show_candlestick_with_trades(
    ohlc_data: pd.DataFrame,
    trades_df: pd.DataFrame,
    *,
    title: str = "Candlestick + Trades",
    indicators: Optional[list[IndicatorConfig]] = None,
    time_mode: Literal["auto", "datetime", "bars"] = "auto",
    time_col: str = "time",
    marker_size: int = DEFAULT_TRADE_MARKER_SIZE,
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
        indicators=indicators,
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
