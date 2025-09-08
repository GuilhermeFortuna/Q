from __future__ import annotations

from typing import Any, Mapping, Optional, Dict, List, Tuple
import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics, QGuiApplication, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
)

import pyqtgraph as pg
import pandas as pd
import numpy as np
from src.visualizer.models import BacktestResultModel, IndicatorConfig


def _as_dict(results: Any) -> Mapping[str, Any]:
    """
    Normalize incoming results to a dict.
    Supports:
      - dict-like objects
      - objects exposing get_result() -> dict
      - objects exposing .result or .results that are dict-like
    """
    if results is None:
        return {}

    if isinstance(results, Mapping):
        return results

    # Try common TradeRegistry-like APIs
    if hasattr(results, "get_result"):
        try:
            maybe = results.get_result()
            if isinstance(maybe, Mapping):
                return maybe
        except Exception:
            pass

    for attr in ("result", "results"):
        if hasattr(results, attr):
            maybe = getattr(results, attr)
            if isinstance(maybe, Mapping):
                return maybe

    # Fallback: best-effort dict() of __dict__ (filtered)
    if hasattr(results, "__dict__"):
        return {k: v for k, v in vars(results).items() if not k.startswith("_")}

    return {}


class KPICard(QFrame):
    """A card widget for displaying a single KPI with label and value."""

    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Label
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("color: #888; font-size: 11px; font-weight: normal;")
        layout.addWidget(label_widget)

        # Value
        value_widget = QLabel(value)
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setStyleSheet("color: #fff; font-size: 14px; font-weight: bold;")
        layout.addWidget(value_widget)

        self.setStyleSheet(
            """
            KPICard {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 6px;
            }
            KPICard:hover {
                border-color: #666;
            }
        """
        )


class KPIGroupWidget(QGroupBox):
    """A group of KPI cards with a title."""

    def __init__(self, title: str, kpis: List[Tuple[str, str]], parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #fff;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        layout = QGridLayout(self)
        layout.setSpacing(8)

        # Add KPI cards in a grid (2 columns max)
        for i, (label, value) in enumerate(kpis):
            row = i // 2
            col = i % 2
            card = KPICard(label, value)
            layout.addWidget(card, row, col)


class MiniChartWidget(QWidget):
    """A small chart widget for equity curve or drawdown."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', '')
        self.plot_widget.setLabel('bottom', '')

        # Style the plot
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='#888', width=1))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#888', width=1))
        self.plot_widget.getAxis('left').setTextPen(pg.mkPen(color='#ccc'))
        self.plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color='#ccc'))

        layout.addWidget(self.plot_widget)

        # Set minimum height
        self.setMinimumHeight(200)

    def plot_series(self, data, color='#00ff88', fill=False):
        """Plot a data series."""
        if data is None or data.empty:
            return

        try:
            x = range(len(data))
            y = data.values

            # Remove NaN and infinite values
            valid_mask = ~(pd.isna(y) | np.isinf(y))
            if not valid_mask.any():
                return

            x_clean = [x[i] for i in range(len(x)) if valid_mask[i]]
            y_clean = y[valid_mask]

            if fill and 'drawdown' in self.title.lower():
                # Fill area for drawdown
                self.plot_widget.plot(
                    x_clean,
                    y_clean,
                    pen=pg.mkPen(color=color, width=2),
                    fillLevel=0,
                    brush=pg.mkBrush(color=color + '40'),
                )
            else:
                # Regular line plot
                self.plot_widget.plot(
                    x_clean, y_clean, pen=pg.mkPen(color=color, width=2)
                )

        except Exception as e:
            print(f"Error plotting {self.title}: {e}")


class MonthlyResultsWidget(QWidget):
    """Widget to display monthly results in a table."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Monthly Results")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: #2b2b2b;
                color: #fff;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #fff;
                border: 1px solid #555;
                font-weight: bold;
                padding: 4px;
            }
        """
        )

        layout.addWidget(self.table)

        # Set minimum height
        self.setMinimumHeight(150)

    def set_data(self, monthly_df):
        """Set the monthly results data."""
        if monthly_df is None or monthly_df.empty:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        try:
            # Set up table
            self.table.setRowCount(len(monthly_df))
            self.table.setColumnCount(len(monthly_df.columns))
            self.table.setHorizontalHeaderLabels(monthly_df.columns)

            # Fill data
            for i, row in monthly_df.iterrows():
                for j, value in enumerate(row):
                    # Format values
                    if isinstance(value, float):
                        if (
                            'balance' in monthly_df.columns[j]
                            or 'result' in monthly_df.columns[j]
                        ):
                            formatted_value = f"{value:,.2f}"
                        else:
                            formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = str(value)

                    item = QTableWidgetItem(formatted_value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)

            # Adjust column widths
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error setting monthly data: {e}")


class BacktestSummaryWindow(QMainWindow):
    """Enhanced backtest summary window with KPIs, charts, and actions."""

    def __init__(
        self, results: Any, ohlc_df=None, parent=None, title: str = "Backtest Summary"
    ):
        super().__init__(parent)
        self.setWindowTitle(title)

        # Add a placeholder for the trades chart window reference
        self._trades_chart_window: Optional[QMainWindow] = None

        # Create the data model
        if isinstance(results, BacktestResultModel):
            self.model = results
        else:
            self.model = BacktestResultModel(registry=results, ohlc_df=ohlc_df)

        self._setup_ui()
        self._populate_data()

        # Style
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
                color: #fff;
            }
        """
        )

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel: KPIs
        kpi_widget = self._create_kpi_panel()
        splitter.addWidget(kpi_widget)

        # Right panel: Charts and monthly results
        charts_widget = self._create_charts_panel()
        splitter.addWidget(charts_widget)

        # Set splitter proportions
        splitter.setStretchFactor(0, 2)  # KPIs take 2/3 of space
        splitter.setStretchFactor(1, 1)  # Charts take 1/3 of space

        # Toolbar
        self._create_toolbar()

    def _create_toolbar(self):
        """Create the toolbar with action buttons."""
        toolbar = self.addToolBar("Actions")
        toolbar.setStyleSheet(
            """
            QToolBar {
                background-color: #2b2b2b;
                border: none;
                spacing: 5px;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0088ff;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """
        )

        # Open trades chart button
        open_trades_btn = QPushButton("Open Trades Chart")
        open_trades_btn.clicked.connect(self._open_trades_chart)
        open_trades_btn.setEnabled(
            self.model.ohlc_df is not None and self.model.trades_df is not None
        )
        if not open_trades_btn.isEnabled():
            open_trades_btn.setToolTip("Requires both OHLC and trade data")
        toolbar.addWidget(open_trades_btn)

        toolbar.addSeparator()

        # Export button
        export_btn = QPushButton("Export Summary")
        export_btn.clicked.connect(self._export_summary)
        toolbar.addWidget(export_btn)

    def _create_kpi_panel(self) -> QWidget:
        """Create the KPI panel with grouped metrics."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        kpi_container = QWidget()
        kpi_layout = QVBoxLayout(kpi_container)
        kpi_layout.setSpacing(15)

        # Define KPI groups
        kpi_groups = self._get_kpi_groups()

        # Create group widgets
        for group_title, kpis in kpi_groups:
            if kpis:  # Only create group if it has KPIs
                group_widget = KPIGroupWidget(group_title, kpis)
                kpi_layout.addWidget(group_widget)

        kpi_layout.addStretch()
        scroll_area.setWidget(kpi_container)

        return scroll_area

    def _create_charts_panel(self) -> QWidget:
        """Create the charts panel with equity curve, drawdown, and monthly results."""
        charts_container = QWidget()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(10)

        # Equity curve chart
        self.equity_chart = MiniChartWidget("Equity Curve")
        charts_layout.addWidget(self.equity_chart)

        # Drawdown chart
        self.drawdown_chart = MiniChartWidget("Drawdown")
        charts_layout.addWidget(self.drawdown_chart)

        # Monthly results table
        self.monthly_widget = MonthlyResultsWidget()
        charts_layout.addWidget(self.monthly_widget)

        return charts_container

    def _get_kpi_groups(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """Get organized KPI groups with formatted values."""
        result = self.model.result

        groups = [
            (
                "P&L",
                [
                    (
                        "Net Balance",
                        self.model.format_value(
                            "net_balance (BRL)", result.get("net_balance (BRL)")
                        ),
                    ),
                    (
                        "Gross Balance",
                        self.model.format_value(
                            "gross_balance (BRL)", result.get("gross_balance (BRL)")
                        ),
                    ),
                    (
                        "Total Profit",
                        self.model.format_value(
                            "total_profit (BRL)", result.get("total_profit (BRL)")
                        ),
                    ),
                    (
                        "Total Loss",
                        self.model.format_value(
                            "total_loss (BRL)", result.get("total_loss (BRL)")
                        ),
                    ),
                    (
                        "Total Tax",
                        self.model.format_value(
                            "total_tax (BRL)", result.get("total_tax (BRL)")
                        ),
                    ),
                    (
                        "Total Cost",
                        self.model.format_value(
                            "total_cost (BRL)", result.get("total_cost (BRL)")
                        ),
                    ),
                ],
            ),
            (
                "Performance",
                [
                    (
                        "Profit Factor",
                        self.model.format_value(
                            "profit_factor", result.get("profit_factor")
                        ),
                    ),
                    (
                        "Accuracy",
                        self.model.format_value(
                            "accuracy (%)", result.get("accuracy (%)")
                        ),
                    ),
                    (
                        "Mean Profit",
                        self.model.format_value(
                            "mean_profit (BRL)", result.get("mean_profit (BRL)")
                        ),
                    ),
                    (
                        "Mean Loss",
                        self.model.format_value(
                            "mean_loss (BRL)", result.get("mean_loss (BRL)")
                        ),
                    ),
                    (
                        "Mean Ratio",
                        self.model.format_value("mean_ratio", result.get("mean_ratio")),
                    ),
                    (
                        "Std Deviation",
                        self.model.format_value(
                            "standard_deviation", result.get("standard_deviation")
                        ),
                    ),
                ],
            ),
            (
                "Trades",
                [
                    (
                        "Total Trades",
                        self.model.format_value(
                            "total_trades", result.get("total_trades")
                        ),
                    ),
                    (
                        "Positive Trades",
                        self.model.format_value(
                            "positive_trades", result.get("positive_trades")
                        ),
                    ),
                    (
                        "Negative Trades",
                        self.model.format_value(
                            "negative_trades", result.get("negative_trades")
                        ),
                    ),
                ],
            ),
            (
                "Risk",
                [
                    (
                        "Max Drawdown",
                        self.model.format_value(
                            "maximum_drawdown (BRL)",
                            result.get("maximum_drawdown (BRL)"),
                        ),
                    ),
                    (
                        "Drawdown %",
                        self.model.format_value(
                            "drawdown_relative (%)", result.get("drawdown_relative (%)")
                        ),
                    ),
                    (
                        "Final Drawdown %",
                        self.model.format_value(
                            "drawdown_final (%)", result.get("drawdown_final (%)")
                        ),
                    ),
                ],
            ),
            (
                "Period",
                [
                    (
                        "Start Date",
                        self.model.format_value("start_date", result.get("start_date")),
                    ),
                    (
                        "End Date",
                        self.model.format_value("end_date", result.get("end_date")),
                    ),
                    (
                        "Duration",
                        self.model.format_value("duration", result.get("duration")),
                    ),
                    (
                        "Avg Monthly",
                        self.model.format_value(
                            "average_monthly_result (BRL)",
                            result.get("average_monthly_result (BRL)"),
                        ),
                    ),
                ],
            ),
        ]

        # Filter out groups with all None/empty values
        filtered_groups = []
        for group_title, kpis in groups:
            valid_kpis = [
                (label, value)
                for label, value in kpis
                if value != "—" and value is not None
            ]
            if valid_kpis:
                filtered_groups.append((group_title, valid_kpis))

        return filtered_groups

    def _populate_data(self):
        """Populate the charts with data."""
        # Equity curve
        balance = self.model.balance
        if balance is not None:
            self.equity_chart.plot_series(balance, color='#00ff88')

        # Drawdown
        drawdown = self.model.drawdown
        if drawdown is not None:
            self.drawdown_chart.plot_series(drawdown, color='#ff4444', fill=True)

        # Monthly results
        monthly_df = self.model.monthly_df
        self.monthly_widget.set_data(monthly_df)

    def _open_trades_chart(self):
        """Open the trades chart window."""
        try:
            from src.visualizer.windows.plot_trades import show_candlestick_with_trades

            # Auto-detect indicator columns from the ohlc_df
            indicators = []
            if self.model.ohlc_df is not None:
                standard_cols = {"open", "high", "low", "close", "volume", "time"}
                indicator_cols = [
                    col
                    for col in self.model.ohlc_df.columns
                    if col.lower() not in standard_cols
                ]

                # Define a cycle of colors for the indicators
                plot_colors = ["#00FFFF", "#FF00FF", "#FFFF00", "#FFA500", "#DA70D6"]

                for i, col_name in enumerate(indicator_cols):
                    indicators.append(
                        IndicatorConfig(
                            type="line",
                            y=self.model.ohlc_df[col_name],
                            name=col_name.upper(),
                            color=plot_colors[i % len(plot_colors)],
                        )
                    )

            # Store the new window in an instance attribute to keep it alive
            self._trades_chart_window = show_candlestick_with_trades(
                ohlc_data=self.model.ohlc_df,
                trades_df=self.model.trades_df,
                indicators=indicators,
                title="Trades Chart",
                block=False,
            )
        except Exception as e:
            print(f"Error opening trades chart: {e}")

    def _export_summary(self):
        """Export the summary data."""
        # TODO: Implement export functionality
        print("Export functionality to be implemented")


def show_backtest_summary(
    results: Any,
    ohlc_df: Optional[Any] = None,
    title: str = "Backtest Summary",
    block: Optional[bool] = None,
    size: Optional[tuple[int, int]] = None,
) -> BacktestSummaryWindow:
    """
    Show the enhanced backtest summary window.

    Args:
        results: Backtest results (registry instance or dict)
        ohlc_df: Optional OHLC DataFrame for trades chart
        title: Window title
        block: Whether to block execution (start event loop)
        size: Optional window size (width, height)

    Returns:
        BacktestSummaryWindow instance
    """
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication([])
        created_app = True

    window = BacktestSummaryWindow(results, ohlc_df=ohlc_df, title=title)

    if size is not None:
        window.resize(size[0], size[1])
    else:
        # Set a good default size
        window.resize(1200, 800)

    window.show()

    if block is None:
        block = created_app

    if block:
        app.exec()

    return window


# Legacy dialog for backward compatibility
def _format_value(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, (int, float)):
        return f"{v}"
    return f"{v}"


def _format_results_text(results_dict: Mapping[str, Any]) -> str:
    """Returns a text block similar to console output."""
    preferred_order = [
        "net_balance (BRL)",
        "gross_balance (BRL)",
        "total_tax (BRL)",
        "total_cost (BRL)",
        "total_profit (BRL)",
        "total_loss (BRL)",
        "profit_factor",
        "accuracy (%)",
        "mean_profit (BRL)",
        "mean_loss (BRL)",
        "mean_ratio",
        "standard_deviation",
        "total_trades",
        "positive_trades",
        "negative_trades",
        "maximum_drawdown (BRL)",
        "drawdown_relative (%)",
        "drawdown_final (%)",
        "start_date",
        "end_date",
        "duration",
        "average_monthly_result (BRL)",
    ]

    keys_available = {str(k): k for k in results_dict.keys()}

    lines = ["--- Results ---"]
    for label in preferred_order:
        if label in keys_available:
            orig_key = keys_available[label]
            val = results_dict.get(orig_key)
            lines.append(f"{label:40s} { _format_value(val) }")

    extra_keys = [k for k in results_dict.keys() if str(k) not in preferred_order]
    if extra_keys:
        lines.append("")
        for k in sorted(extra_keys, key=lambda x: str(x)):
            lines.append(f"{k}: { _format_value(results_dict[k]) }")

    return "\n".join(lines)


class BacktestSummaryDialog(QDialog):
    """Legacy dialog - kept for backward compatibility."""

    def __init__(
        self,
        results: Any,
        parent=None,
        title: str = "Backtest Summary",
        initial_size: tuple[int, int] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        data_dict = _as_dict(results)
        text = _format_results_text(data_dict)

        layout = QVBoxLayout(self)

        header = QLabel("Summary of backtest results")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(header)

        self.text_area = QPlainTextEdit(self)
        self.text_area.setReadOnly(True)

        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setStyleHint(QFont.Monospace)
        self.text_area.setFont(font)

        self.text_area.setPlainText(text)
        layout.addWidget(self.text_area)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        if initial_size is not None:
            self.resize(initial_size[0], initial_size[1])
        else:
            self._resize_to_fit_text(text)

    def _resize_to_fit_text(self, text: str) -> None:
        fm = QFontMetrics(self.text_area.font())
        lines = text.splitlines() or [""]
        max_cols = max(len(line) for line in lines)
        line_count = len(lines)

        char_w = fm.horizontalAdvance("M")
        line_h = fm.lineSpacing()

        frame = self.text_area.frameWidth()
        cushion = 16
        scrollbar_allowance = 20

        content_w = (max_cols * char_w) + (frame * 2) + cushion + scrollbar_allowance
        content_h = (line_count * line_h) + (frame * 2) + cushion + scrollbar_allowance

        screen = (
            self.windowHandle().screen()
            if self.windowHandle()
            else QGuiApplication.primaryScreen()
        )
        if screen:
            avail = screen.availableGeometry()
            max_w = int(avail.width() * 0.7)
            max_h = int(avail.height() * 0.7)
            content_w = min(content_w, max_w)
            content_h = min(content_h, max_h)

        self.text_area.setMinimumSize(int(content_w), int(content_h))
        self.adjustSize()
