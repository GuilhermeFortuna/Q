"""
Results Panel Widget for Backtester GUI

This module contains a comprehensive results panel for displaying backtest results
with multiple tabs for different views: summary, equity curve, trades, and statistics.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QGroupBox,
    QGridLayout,
    QScrollArea,
    QFrame,
    QSplitter,
    QTextEdit,
    QProgressBar,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
import json
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

from ..theme import theme


class MetricsCardWidget(QFrame):
    """Widget for displaying individual performance metrics in a card format."""
    
    def __init__(self, title: str, value: str = "", description: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.description = description
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(self.value_label)
        
        # Description
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setStyleSheet("font-size: 10px; color: #666;")
            self.desc_label.setWordWrap(True)
            layout.addWidget(self.desc_label)
    
    def _apply_styling(self):
        """Apply card styling."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.BACKGROUND_SECONDARY};
                border: 1px solid {theme.BORDER_DEFAULT};
                border-radius: 5px;
            }}
        """)
    
    def set_value(self, value: str, color: str = "#fff"):
        """Update the value and color."""
        self.value_label.setText(value)
        self.value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")


class EquityCurveWidget(QWidget):
    """Widget for displaying interactive equity curve chart."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(12, 6), facecolor=theme.BACKGROUND_PRIMARY)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the equity curve UI."""
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
    
    def _apply_styling(self):
        """Apply chart styling."""
        self.ax.set_facecolor(theme.BACKGROUND_PRIMARY)
        self.ax.tick_params(colors=theme.TEXT_PRIMARY)
        self.ax.spines['bottom'].set_color(theme.BORDER_DEFAULT)
        self.ax.spines['top'].set_color(theme.BORDER_DEFAULT)
        self.ax.spines['right'].set_color(theme.BORDER_DEFAULT)
        self.ax.spines['left'].set_color(theme.BORDER_DEFAULT)
        self.ax.xaxis.label.set_color(theme.TEXT_PRIMARY)
        self.ax.yaxis.label.set_color(theme.TEXT_PRIMARY)
    
    def plot_equity_curve(self, equity_data: List[float], dates: List[datetime] = None):
        """Plot the equity curve."""
        self.ax.clear()
        
        if dates:
            self.ax.plot(dates, equity_data, color=theme.ACCENT_PRIMARY, linewidth=2)
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
        else:
            self.ax.plot(equity_data, color=theme.ACCENT_PRIMARY, linewidth=2)
        
        self.ax.set_title('Equity Curve', color=theme.TEXT_PRIMARY, fontsize=14)
        self.ax.set_xlabel('Time', color=theme.TEXT_PRIMARY)
        self.ax.set_ylabel('Equity', color=theme.TEXT_PRIMARY)
        self.ax.grid(True, alpha=0.3, color=theme.BORDER_DEFAULT)
        
        self.figure.tight_layout()
        self.canvas.draw()


class TradesTableWidget(QTableWidget):
    """Widget for displaying trades in a table format."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the trades table UI."""
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "Date", "Symbol", "Side", "Quantity", "Price", "P&L", "Duration", "Status"
        ])
        
        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Symbol
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Side
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Quantity
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # P&L
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Status
    
    def _apply_styling(self):
        """Apply table styling."""
        self.setStyleSheet(theme.get_table_stylesheet())
    
    def load_trades(self, trades: List[Dict[str, Any]]):
        """Load trades data into the table."""
        self.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            # Date
            date_item = QTableWidgetItem(trade.get('date', ''))
            self.setItem(row, 0, date_item)
            
            # Symbol
            symbol_item = QTableWidgetItem(trade.get('symbol', ''))
            self.setItem(row, 1, symbol_item)
            
            # Side
            side_item = QTableWidgetItem(trade.get('side', ''))
            side_item.setForeground(QColor(theme.ACCENT_SUCCESS if trade.get('side') == 'BUY' else theme.ACCENT_DANGER))
            self.setItem(row, 2, side_item)
            
            # Quantity
            quantity_item = QTableWidgetItem(str(trade.get('quantity', 0)))
            self.setItem(row, 3, quantity_item)
            
            # Price
            price_item = QTableWidgetItem(f"{trade.get('price', 0):.2f}")
            self.setItem(row, 4, price_item)
            
            # P&L
            pnl = trade.get('pnl', 0)
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")
            pnl_color = theme.ACCENT_SUCCESS if pnl >= 0 else theme.ACCENT_DANGER
            pnl_item.setForeground(QColor(pnl_color))
            self.setItem(row, 5, pnl_item)
            
            # Duration
            duration_item = QTableWidgetItem(trade.get('duration', ''))
            self.setItem(row, 6, duration_item)
            
            # Status
            status_item = QTableWidgetItem(trade.get('status', ''))
            self.setItem(row, 7, status_item)


class ResultsPanelWidget(QWidget):
    """
    Comprehensive results panel for displaying backtest results.
    
    This widget provides a tabbed interface for viewing different aspects
    of backtest results including summary metrics, equity curve, trade details,
    and statistical analysis.
    """
    
    # Signals
    export_requested = Signal(str)  # export_format
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_data = None
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the results panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Backtest Results")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Export button
        self.export_btn = QPushButton("Export Results")
        self.export_btn.setToolTip("Export results to various formats")
        self.export_btn.clicked.connect(self._show_export_menu)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_summary_tab()
        self._create_equity_tab()
        self._create_trades_tab()
        self._create_statistics_tab()
    
    def _create_summary_tab(self):
        """Create the summary tab with key metrics."""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        # Metrics grid
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Create metric cards
        self.metrics_cards = {
            'total_return': MetricsCardWidget("Total Return", "$0.00", "Total profit/loss"),
            'sharpe_ratio': MetricsCardWidget("Sharpe Ratio", "0.00", "Risk-adjusted return"),
            'max_drawdown': MetricsCardWidget("Max Drawdown", "0.00%", "Largest peak-to-trough decline"),
            'win_rate': MetricsCardWidget("Win Rate", "0.00%", "Percentage of profitable trades"),
            'profit_factor': MetricsCardWidget("Profit Factor", "0.00", "Gross profit / Gross loss"),
            'total_trades': MetricsCardWidget("Total Trades", "0", "Number of trades executed"),
            'avg_trade': MetricsCardWidget("Avg Trade", "$0.00", "Average profit per trade"),
            'avg_duration': MetricsCardWidget("Avg Duration", "0h", "Average trade duration")
        }
        
        # Add cards to grid
        row, col = 0, 0
        for card in self.metrics_cards.values():
            metrics_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        layout.addWidget(metrics_group)
        layout.addStretch()
        
        self.tab_widget.addTab(summary_widget, "Summary")
    
    def _create_equity_tab(self):
        """Create the equity curve tab."""
        equity_widget = QWidget()
        layout = QVBoxLayout(equity_widget)
        
        # Equity curve widget
        self.equity_curve = EquityCurveWidget()
        layout.addWidget(self.equity_curve)
        
        self.tab_widget.addTab(equity_widget, "Equity Curve")
    
    def _create_trades_tab(self):
        """Create the trades tab."""
        trades_widget = QWidget()
        layout = QVBoxLayout(trades_widget)
        
        # Trades table
        self.trades_table = TradesTableWidget()
        layout.addWidget(self.trades_table)
        
        self.tab_widget.addTab(trades_widget, "Trades")
    
    def _create_statistics_tab(self):
        """Create the statistics tab."""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # Statistics text area
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.BACKGROUND_SECONDARY};
                color: {theme.TEXT_PRIMARY};
                border: 1px solid {theme.BORDER_DEFAULT};
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
        """)
        layout.addWidget(self.stats_text)
        
        self.tab_widget.addTab(stats_widget, "Statistics")
    
    def _apply_styling(self):
        """Apply styling to the results panel."""
        self.setStyleSheet(theme.get_widget_base_stylesheet())
    
    def load_results(self, results_data: Dict[str, Any]):
        """Load backtest results data."""
        self.results_data = results_data
        
        # Update summary metrics
        self._update_summary_metrics(results_data)
        
        # Update equity curve
        if 'equity_curve' in results_data:
            self.equity_curve.plot_equity_curve(results_data['equity_curve'])
        
        # Update trades table
        if 'trades' in results_data:
            self.trades_table.load_trades(results_data['trades'])
        
        # Update statistics
        self._update_statistics(results_data)
    
    def _update_summary_metrics(self, results_data: Dict[str, Any]):
        """Update the summary metrics cards."""
        metrics = results_data.get('metrics', {})
        
        # Total Return
        total_return = metrics.get('total_return', 0)
        self.metrics_cards['total_return'].set_value(
            f"${total_return:.2f}",
            theme.ACCENT_SUCCESS if total_return >= 0 else theme.ACCENT_DANGER
        )
        
        # Sharpe Ratio
        sharpe = metrics.get('sharpe_ratio', 0)
        self.metrics_cards['sharpe_ratio'].set_value(f"{sharpe:.2f}")
        
        # Max Drawdown
        max_dd = metrics.get('max_drawdown', 0)
        self.metrics_cards['max_drawdown'].set_value(f"{max_dd:.2f}%", theme.ACCENT_DANGER)
        
        # Win Rate
        win_rate = metrics.get('win_rate', 0)
        self.metrics_cards['win_rate'].set_value(f"{win_rate:.1f}%")
        
        # Profit Factor
        profit_factor = metrics.get('profit_factor', 0)
        self.metrics_cards['profit_factor'].set_value(f"{profit_factor:.2f}")
        
        # Total Trades
        total_trades = metrics.get('total_trades', 0)
        self.metrics_cards['total_trades'].set_value(str(total_trades))
        
        # Average Trade
        avg_trade = metrics.get('avg_trade', 0)
        self.metrics_cards['avg_trade'].set_value(
            f"${avg_trade:.2f}",
            theme.ACCENT_SUCCESS if avg_trade >= 0 else theme.ACCENT_DANGER
        )
        
        # Average Duration
        avg_duration = metrics.get('avg_duration', 0)
        self.metrics_cards['avg_duration'].set_value(f"{avg_duration:.1f}h")
    
    def _update_statistics(self, results_data: Dict[str, Any]):
        """Update the statistics text."""
        stats_text = "Detailed Statistics\n" + "=" * 50 + "\n\n"
        
        metrics = results_data.get('metrics', {})
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                stats_text += f"{key.replace('_', ' ').title()}: {value:.4f}\n"
            else:
                stats_text += f"{key.replace('_', ' ').title()}: {value}\n"
        
        self.stats_text.setPlainText(stats_text)
    
    def _show_export_menu(self):
        """Show export options menu."""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # PDF export
        pdf_action = menu.addAction("Export to PDF")
        pdf_action.triggered.connect(lambda: self._export_results("pdf"))
        
        # Excel export
        excel_action = menu.addAction("Export to Excel")
        excel_action.triggered.connect(lambda: self._export_results("excel"))
        
        # CSV export
        csv_action = menu.addAction("Export to CSV")
        csv_action.triggered.connect(lambda: self._export_results("csv"))
        
        # JSON export
        json_action = menu.addAction("Export to JSON")
        json_action.triggered.connect(lambda: self._export_results("json"))
        
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))
    
    def _export_results(self, format_type: str):
        """Export results in the specified format."""
        if not self.results_data:
            QMessageBox.warning(self, "Export Error", "No results data to export")
            return
        
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Results as {format_type.upper()}",
            f"backtest_results.{format_type}",
            f"{format_type.upper()} Files (*.{format_type})"
        )
        
        if file_path:
            try:
                if format_type == "json":
                    self._export_json(file_path)
                elif format_type == "csv":
                    self._export_csv(file_path)
                elif format_type == "excel":
                    self._export_excel(file_path)
                elif format_type == "pdf":
                    self._export_pdf(file_path)
                
                QMessageBox.information(self, "Export Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results: {str(e)}")
    
    def _export_json(self, file_path: str):
        """Export results to JSON format."""
        with open(file_path, 'w') as f:
            json.dump(self.results_data, f, indent=2, default=str)
    
    def _export_csv(self, file_path: str):
        """Export trades to CSV format."""
        if 'trades' in self.results_data:
            trades = self.results_data['trades']
            if trades:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                    writer.writeheader()
                    writer.writerows(trades)
    
    def _export_excel(self, file_path: str):
        """Export results to Excel format."""
        # This would require openpyxl or xlsxwriter
        # For now, just export as JSON
        self._export_json(file_path.replace('.xlsx', '.json'))
    
    def _export_pdf(self, file_path: str):
        """Export results to PDF format."""
        # This would require reportlab or similar
        # For now, just export as JSON
        self._export_json(file_path.replace('.pdf', '.json'))
