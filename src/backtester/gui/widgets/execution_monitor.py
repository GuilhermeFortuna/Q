"""
Execution Monitor Widget for Backtester GUI

This module contains the interface for monitoring backtest execution,
including real-time progress tracking, live metrics, and results display.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QTabWidget,
    QGridLayout,
    QFrame,
    QScrollArea,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPalette

from ..models.backtest_model import BacktestModel
from ..models.strategy_model import StrategyModel
from ..controllers.execution_controller import ExecutionController


class MetricsCardWidget(QFrame):
    """Widget for displaying a single metric card."""

    def __init__(self, title: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the metrics card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "color: #888; font-size: 11px; font-weight: normal;"
        )
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
            "color: #fff; font-size: 14px; font-weight: bold;"
        )
        layout.addWidget(self.value_label)

    def _apply_styling(self):
        """Apply styling to the metrics card."""
        self.setStyleSheet(
            """
            MetricsCardWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 6px;
            }
            MetricsCardWidget:hover {
                border-color: #666;
            }
        """
        )
        self.setFixedSize(120, 80)

    def set_value(self, value: str):
        """Update the metric value."""
        self.value = value
        self.value_label.setText(value)


class LiveMetricsWidget(QWidget):
    """Widget for displaying live backtest metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.metrics_cards = {}
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the live metrics UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Live Metrics")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        layout.addWidget(title_label)

        # Metrics grid
        self.metrics_layout = QGridLayout()
        layout.addLayout(self.metrics_layout)

        # Initialize metrics cards
        self._create_metrics_cards()

        layout.addStretch()

    def _create_metrics_cards(self):
        """Create the metrics cards."""
        metrics = [
            ("Current P&L", "0.00"),
            ("Total Trades", "0"),
            ("Win Rate", "0%"),
            ("Max DD", "0.00"),
            ("Current DD", "0.00"),
            ("Profit Factor", "0.00"),
        ]

        for i, (title, value) in enumerate(metrics):
            card = MetricsCardWidget(title, value)
            self.metrics_cards[title] = card
            row = i // 3
            col = i % 3
            self.metrics_layout.addWidget(card, row, col)

    def _apply_styling(self):
        """Apply styling to the widget."""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                color: #fff;
            }
        """
        )

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update the metrics display."""
        for title, value in metrics.items():
            if title in self.metrics_cards:
                formatted_value = self._format_value(value)
                self.metrics_cards[title].set_value(formatted_value)

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "—"

        if isinstance(value, (int, float)):
            if isinstance(value, float):
                return f"{value:.2f}"
            else:
                return str(value)

        return str(value)


class ProgressWidget(QWidget):
    """Widget for displaying backtest progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the progress UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Progress")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        layout.addWidget(title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # ETA label
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.eta_label)

    def _apply_styling(self):
        """Apply styling to the widget."""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                color: #fff;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background-color: #3c3c3c;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 2px;
            }
        """
        )

    def set_progress(self, progress: int):
        """Set the progress percentage."""
        self.progress_bar.setValue(progress)

    def set_status(self, status: str):
        """Set the status message."""
        self.status_label.setText(status)

    def set_eta(self, eta: str):
        """Set the ETA message."""
        self.eta_label.setText(eta)


class LogWidget(QWidget):
    """Widget for displaying backtest logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the log UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Execution Log")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        layout.addWidget(title_label)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # Clear button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)

    def _apply_styling(self):
        """Apply styling to the widget."""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                color: #fff;
            }
            QTextEdit {
                background-color: #2b2b2b;
                color: #fff;
                border: 1px solid #555;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0088ff;
            }
        """
        )

    def add_log_message(self, message: str):
        """Add a log message."""
        self.log_text.append(f"[{self._get_timestamp()}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")


class ExecutionMonitorWidget(QWidget):
    """
    Main widget for execution monitoring.

    This widget provides:
    - Real-time progress tracking
    - Live metrics display
    - Execution log
    - Results summary
    """

    def __init__(
        self,
        backtest_model: BacktestModel,
        strategy_model: StrategyModel,
        execution_controller: ExecutionController,
        parent=None,
    ):
        super().__init__(parent)
        self.backtest_model = backtest_model
        self.strategy_model = strategy_model
        self.execution_controller = execution_controller

        self._setup_ui()
        self._setup_connections()
        self._apply_styling()

        # Update timer for live metrics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_live_metrics)
        self.update_timer.setInterval(1000)  # Update every second

    def _setup_ui(self):
        """Setup the execution monitor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Execution tab
        self.execution_tab = self._create_execution_tab()
        self.tab_widget.addTab(self.execution_tab, "Execution")

        # Results tab
        self.results_tab = self._create_results_tab()
        self.tab_widget.addTab(self.results_tab, "Results")

        # Plot Trades tab
        self.plot_trades_tab = self._create_plot_trades_tab()
        self.tab_widget.addTab(self.plot_trades_tab, "Plot Trades")

        # Control buttons
        self._create_control_buttons(layout)

    def _create_execution_tab(self) -> QWidget:
        """Create the execution monitoring tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left panel: Progress and metrics
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Progress widget
        self.progress_widget = ProgressWidget()
        left_layout.addWidget(self.progress_widget)

        # Live metrics widget
        self.live_metrics_widget = LiveMetricsWidget()
        left_layout.addWidget(self.live_metrics_widget)

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # Right panel: Logs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Log widget
        self.log_widget = LogWidget()
        right_layout.addWidget(self.log_widget)

        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Left panel
        splitter.setStretchFactor(1, 1)  # Right panel

        return widget

    def _create_results_tab(self) -> QWidget:
        """Create the results display tab with integrated visualizer."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create a placeholder widget that will be replaced with visualizer content
        self.results_placeholder = QLabel("No results available")
        self.results_placeholder.setAlignment(Qt.AlignCenter)
        self.results_placeholder.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.results_placeholder)

        # Store reference for the visualizer widget
        self.results_visualizer_widget = None

        return widget

    def _create_plot_trades_tab(self) -> QWidget:
        """Create the plot trades tab with integrated PlotTradesWindow."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create a placeholder widget that will be replaced with plot trades content
        self.plot_trades_placeholder = QLabel("No trades data available")
        self.plot_trades_placeholder.setAlignment(Qt.AlignCenter)
        self.plot_trades_placeholder.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.plot_trades_placeholder)

        # Store reference for the plot trades widget
        self.plot_trades_widget = None

        return widget

    def _create_control_buttons(self, layout: QVBoxLayout):
        """Create the control buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Run backtest button
        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.clicked.connect(self._run_backtest)
        self.run_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00aa00;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00cc00;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """
        )
        button_layout.addWidget(self.run_btn)

        # Stop backtest button
        self.stop_btn = QPushButton("Stop Backtest")
        self.stop_btn.clicked.connect(self._stop_backtest)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #aa0000;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """
        )
        button_layout.addWidget(self.stop_btn)

        # Clear results button
        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.clicked.connect(self._clear_results)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

    def _setup_connections(self):
        """Setup signal connections."""
        # Controller connections
        self.execution_controller.backtest_started.connect(self._on_backtest_started)
        self.execution_controller.backtest_finished.connect(self._on_backtest_finished)
        self.execution_controller.backtest_error.connect(self._on_backtest_error)
        self.execution_controller.progress_updated.connect(self._on_progress_updated)
        self.execution_controller.status_updated.connect(self._on_status_updated)

    def _apply_styling(self):
        """Apply styling to the widget."""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                color: #fff;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0066cc;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
        """
        )

    def _run_backtest(self):
        """Run the backtest."""
        try:
            # Get strategy from model
            strategy = self.strategy_model.get_strategy()
            if not strategy:
                self.log_widget.add_log_message("ERROR: No strategy available")
                return

            # Get data and config
            data = self.backtest_model.get_data()
            config = self.backtest_model.get_config()

            if not data:
                self.log_widget.add_log_message("ERROR: No data loaded")
                return

            if not config:
                self.log_widget.add_log_message("ERROR: No configuration available")
                return

            # Start backtest
            self.log_widget.add_log_message("Starting backtest...")
            self.execution_controller.run_backtest(strategy, data, config)

        except Exception as e:
            self.log_widget.add_log_message(
                f"ERROR: Failed to start backtest: {str(e)}"
            )

    def _stop_backtest(self):
        """Stop the running backtest."""
        self.log_widget.add_log_message("Stopping backtest...")
        self.execution_controller.stop_backtest()

    def _clear_results(self):
        """Clear the results display."""
        # Clear results display
        if self.results_visualizer_widget is not None:
            self.results_visualizer_widget.setParent(None)
            self.results_visualizer_widget = None
        
        if self.results_placeholder is None:
            self.results_placeholder = QLabel("No results available")
            self.results_placeholder.setAlignment(Qt.AlignCenter)
            self.results_placeholder.setStyleSheet("color: #888; font-size: 14px;")
            self.results_tab.layout().addWidget(self.results_placeholder)
        else:
            self.results_placeholder.setText("No results available")
        
        # Clear plot trades display
        if self.plot_trades_widget is not None:
            self.plot_trades_widget.setParent(None)
            self.plot_trades_widget = None
        
        if self.plot_trades_placeholder is None:
            self.plot_trades_placeholder = QLabel("No trades data available")
            self.plot_trades_placeholder.setAlignment(Qt.AlignCenter)
            self.plot_trades_placeholder.setStyleSheet("color: #888; font-size: 14px;")
            self.plot_trades_tab.layout().addWidget(self.plot_trades_placeholder)
        else:
            self.plot_trades_placeholder.setText("No trades data available")
        self.execution_controller.clear_results()
        self.log_widget.add_log_message("Results cleared")

    def _on_backtest_started(self):
        """Handle backtest start."""
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_widget.set_progress(0)
        self.progress_widget.set_status("Running backtest...")
        self.update_timer.start()
        self.log_widget.add_log_message("Backtest started")

    def _on_backtest_finished(self, results):
        """Handle backtest completion."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_widget.set_progress(100)
        self.progress_widget.set_status("Backtest completed")
        self.update_timer.stop()
        self.log_widget.add_log_message("Backtest completed successfully")

        # Update results display
        self._update_results_display(results)

    def _on_backtest_error(self, error_message: str):
        """Handle backtest errors."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_widget.set_status("Backtest failed")
        self.update_timer.stop()
        self.log_widget.add_log_message(f"ERROR: {error_message}")

    def _on_progress_updated(self, progress: int):
        """Handle progress updates."""
        self.progress_widget.set_progress(progress)

    def _on_status_updated(self, status: str):
        """Handle status updates."""
        self.progress_widget.set_status(status)
        self.log_widget.add_log_message(status)

    def _update_live_metrics(self):
        """Update live metrics during backtest execution."""
        if self.execution_controller.is_running():
            # Get current results for live metrics
            results = self.execution_controller.get_current_results()
            if results:
                metrics = self._extract_live_metrics(results)
                self.live_metrics_widget.update_metrics(metrics)

    def _extract_live_metrics(self, results) -> Dict[str, Any]:
        """Extract live metrics from results."""
        try:
            return {
                "Current P&L": f"{results.net_balance:.2f}",
                "Total Trades": str(len(results.trades)),
                "Win Rate": f"{results.accuracy:.1f}%",
                "Max DD": f"{results._compute_maximum_drawdown().get('maximum_drawdown', 0):.2f}",
                "Current DD": "0.00",  # TODO: Calculate current drawdown
                "Profit Factor": f"{results.profit_factor:.2f}",
            }
        except Exception as e:
            return {
                "Current P&L": "—",
                "Total Trades": "—",
                "Win Rate": "—",
                "Max DD": "—",
                "Current DD": "—",
                "Profit Factor": "—",
            }

    def _update_results_display(self, results):
        """Update the results display with integrated visualizer."""
        try:
            # Import the visualizer components
            from src.visualizer.windows.backtest_summary import BacktestSummaryWindow
            from src.visualizer.models import BacktestResultModel
            
            # Get OHLC data if available
            ohlc_data = None
            if hasattr(self.backtest_model, 'get_ohlc_data'):
                ohlc_data = self.backtest_model.get_ohlc_data()
            
            # Create the visualizer model
            model = BacktestResultModel(
                registry=results, 
                result=results.result if hasattr(results, 'result') else results,
                ohlc_df=ohlc_data
            )
            
            # Remove the placeholder
            if self.results_placeholder is not None:
                self.results_placeholder.setParent(None)
                self.results_placeholder = None
            
            # Create the visualizer widget (without the main window wrapper)
            visualizer_widget = self._create_visualizer_widget(model)
            
            # Add it to the results tab layout
            results_layout = self.results_tab.layout()
            results_layout.addWidget(visualizer_widget)
            
            # Store reference
            self.results_visualizer_widget = visualizer_widget

            # Also update the Plot Trades tab
            self._update_plot_trades_display(results, ohlc_data)

        except Exception as e:
            # Fallback to simple text display
            if self.results_placeholder is not None:
                self.results_placeholder.setText(f"Error displaying results: {str(e)}")
                self.results_placeholder.setStyleSheet("color: #ff4444;")
            else:
                # Create a new placeholder if needed
                self.results_placeholder = QLabel(f"Error displaying results: {str(e)}")
                self.results_placeholder.setAlignment(Qt.AlignCenter)
                self.results_placeholder.setStyleSheet("color: #ff4444; font-size: 14px;")
                self.results_tab.layout().addWidget(self.results_placeholder)

    def _create_visualizer_widget(self, model):
        """Create a visualizer widget from the BacktestResultModel."""
        from src.visualizer.windows.backtest_summary import (
            KPIGroupWidget, MiniChartWidget, MonthlyResultsWidget
        )
        from PySide6.QtWidgets import QScrollArea, QSplitter
        
        # Create a container widget
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(10)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel: KPIs
        kpi_widget = self._create_kpi_panel(model)
        splitter.addWidget(kpi_widget)
        
        # Right panel: Charts and monthly results
        charts_widget = self._create_charts_panel(model)
        splitter.addWidget(charts_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 2)  # KPIs take 2/3 of space
        splitter.setStretchFactor(1, 1)  # Charts take 1/3 of space
        
        return container
    
    def _create_kpi_panel(self, model):
        """Create the KPI panel with grouped metrics."""
        from PySide6.QtWidgets import QScrollArea
        from src.visualizer.windows.backtest_summary import KPIGroupWidget
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        kpi_container = QWidget()
        kpi_layout = QVBoxLayout(kpi_container)
        kpi_layout.setSpacing(15)
        
        # Define KPI groups
        kpi_groups = self._get_kpi_groups(model)
        
        # Create group widgets
        for group_title, kpis in kpi_groups:
            if kpis:  # Only create group if it has KPIs
                group_widget = KPIGroupWidget(group_title, kpis)
                kpi_layout.addWidget(group_widget)
        
        kpi_layout.addStretch()
        scroll_area.setWidget(kpi_container)
        
        return scroll_area
    
    def _create_charts_panel(self, model):
        """Create the charts panel with equity curve, drawdown, and monthly results."""
        from src.visualizer.windows.backtest_summary import MiniChartWidget, MonthlyResultsWidget
        
        charts_container = QWidget()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(10)
        
        # Equity curve chart
        equity_chart = MiniChartWidget("Equity Curve")
        balance = model.balance
        if balance is not None:
            equity_chart.plot_series(balance, color='#00ff88')
        charts_layout.addWidget(equity_chart)
        
        # Drawdown chart
        drawdown_chart = MiniChartWidget("Drawdown")
        drawdown = model.drawdown
        if drawdown is not None:
            drawdown_chart.plot_series(drawdown, color='#ff4444', fill=True)
        charts_layout.addWidget(drawdown_chart)
        
        # Monthly results table
        monthly_widget = MonthlyResultsWidget()
        monthly_df = model.monthly_df
        monthly_widget.set_data(monthly_df)
        charts_layout.addWidget(monthly_widget)
        
        return charts_container
    
    def _get_kpi_groups(self, model):
        """Get organized KPI groups with formatted values."""
        result = model.result
        
        groups = [
            (
                "P&L",
                [
                    (
                        "Net Balance",
                        model.format_value(
                            "net_balance (BRL)", result.get("net_balance (BRL)")
                        ),
                    ),
                    (
                        "Gross Balance",
                        model.format_value(
                            "gross_balance (BRL)", result.get("gross_balance (BRL)")
                        ),
                    ),
                    (
                        "Total Profit",
                        model.format_value(
                            "total_profit (BRL)", result.get("total_profit (BRL)")
                        ),
                    ),
                    (
                        "Total Loss",
                        model.format_value(
                            "total_loss (BRL)", result.get("total_loss (BRL)")
                        ),
                    ),
                    (
                        "Total Tax",
                        model.format_value(
                            "total_tax (BRL)", result.get("total_tax (BRL)")
                        ),
                    ),
                    (
                        "Total Cost",
                        model.format_value(
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
                        model.format_value(
                            "profit_factor", result.get("profit_factor")
                        ),
                    ),
                    (
                        "Accuracy",
                        model.format_value(
                            "accuracy (%)", result.get("accuracy (%)")
                        ),
                    ),
                    (
                        "Mean Profit",
                        model.format_value(
                            "mean_profit (BRL)", result.get("mean_profit (BRL)")
                        ),
                    ),
                    (
                        "Mean Loss",
                        model.format_value(
                            "mean_loss (BRL)", result.get("mean_loss (BRL)")
                        ),
                    ),
                    (
                        "Mean Ratio",
                        model.format_value("mean_ratio", result.get("mean_ratio")),
                    ),
                    (
                        "Std Deviation",
                        model.format_value(
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
                        model.format_value(
                            "total_trades", result.get("total_trades")
                        ),
                    ),
                    (
                        "Positive Trades",
                        model.format_value(
                            "positive_trades", result.get("positive_trades")
                        ),
                    ),
                    (
                        "Negative Trades",
                        model.format_value(
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
                        model.format_value(
                            "maximum_drawdown (BRL)",
                            result.get("maximum_drawdown (BRL)"),
                        ),
                    ),
                    (
                        "Drawdown %",
                        model.format_value(
                            "drawdown_relative (%)", result.get("drawdown_relative (%)")
                        ),
                    ),
                    (
                        "Final Drawdown %",
                        model.format_value(
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
                        model.format_value("start_date", result.get("start_date")),
                    ),
                    (
                        "End Date",
                        model.format_value("end_date", result.get("end_date")),
                    ),
                    (
                        "Duration",
                        model.format_value("duration", result.get("duration")),
                    ),
                    (
                        "Avg Monthly",
                        model.format_value(
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

    def _update_plot_trades_display(self, results, ohlc_data):
        """Update the plot trades display with PlotTradesWindow."""
        try:
            # Import the visualizer components
            from src.visualizer.windows.plot_trades import PlotTradesWindow
            from src.visualizer.models import BacktestResultModel
            
            # Create the visualizer model to get trades data
            model = BacktestResultModel(
                registry=results, 
                result=results.result if hasattr(results, 'result') else results,
                ohlc_df=ohlc_data
            )
            
            # Get trades data
            trades_df = model.trades_df
            if trades_df is None or trades_df.empty:
                if self.plot_trades_placeholder is not None:
                    self.plot_trades_placeholder.setText("No trades data available")
                return
            
            # Remove the placeholder
            if self.plot_trades_placeholder is not None:
                self.plot_trades_placeholder.setParent(None)
                self.plot_trades_placeholder = None
            
            # Create the plot trades widget
            plot_trades_widget = self._create_plot_trades_widget(model, ohlc_data)
            
            # Add it to the plot trades tab layout
            plot_trades_layout = self.plot_trades_tab.layout()
            plot_trades_layout.addWidget(plot_trades_widget)
            
            # Store reference
            self.plot_trades_widget = plot_trades_widget

        except Exception as e:
            # Fallback to simple text display
            if self.plot_trades_placeholder is not None:
                self.plot_trades_placeholder.setText(f"Error displaying trades: {str(e)}")
                self.plot_trades_placeholder.setStyleSheet("color: #ff4444;")
            else:
                # Create a new placeholder if needed
                self.plot_trades_placeholder = QLabel(f"Error displaying trades: {str(e)}")
                self.plot_trades_placeholder.setAlignment(Qt.AlignCenter)
                self.plot_trades_placeholder.setStyleSheet("color: #ff4444; font-size: 14px;")
                self.plot_trades_tab.layout().addWidget(self.plot_trades_placeholder)

    def _create_plot_trades_widget(self, model, ohlc_data):
        """Create a plot trades widget from the BacktestResultModel."""
        from src.visualizer.windows.plot_trades import PlotTradesWindow
        from src.visualizer.models import IndicatorConfig
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
        from PySide6.QtCore import Qt
        
        # Create a container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Get trades data
        trades_df = model.trades_df
        if trades_df is None or trades_df.empty:
            no_trades_label = QLabel("No trades data available")
            no_trades_label.setAlignment(Qt.AlignCenter)
            no_trades_label.setStyleSheet("color: #888; font-size: 14px;")
            layout.addWidget(no_trades_label)
            return container
        
        # Create a button to open the trades chart in a separate window
        open_chart_btn = QPushButton("Open Trades Chart")
        open_chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0088ff;
            }
        """)
        
        # Auto-detect indicator columns from the ohlc_df
        indicators = []
        if ohlc_data is not None and not ohlc_data.empty:
            standard_cols = {"open", "high", "low", "close", "volume", "time"}
            indicator_cols = [
                col
                for col in ohlc_data.columns
                if col.lower() not in standard_cols
            ]

            # Define a cycle of colors for the indicators
            plot_colors = ["#00FFFF", "#FF00FF", "#FFFF00", "#FFA500", "#DA70D6"]

            for i, col_name in enumerate(indicator_cols):
                indicators.append(
                    IndicatorConfig(
                        type="line",
                        y=ohlc_data[col_name],
                        name=col_name.upper(),
                        color=plot_colors[i % len(plot_colors)],
                    )
                )
        
        def open_trades_chart():
            try:
                from src.visualizer.windows.plot_trades import show_candlestick_with_trades
                
                window = show_candlestick_with_trades(
                    ohlc_data=ohlc_data if ohlc_data is not None and not ohlc_data.empty else None,
                    trades_df=trades_df,
                    indicators=indicators,
                    title="Trades Chart",
                    block=False,
                )
                return window
            except Exception as e:
                print(f"Error opening trades chart: {e}")
                return None
        
        # Connect the button
        open_chart_btn.clicked.connect(open_trades_chart)
        
        # Add button to layout
        layout.addWidget(open_chart_btn)
        
        # Add some info text
        info_label = QLabel(f"Found {len(trades_df)} trades. Click the button above to open detailed trade visualization with candlestick charts and indicators.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #ccc; font-size: 11px; padding: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Add a simple trades summary table
        try:
            from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
            
            # Create a simple trades summary table
            trades_table = QTableWidget()
            trades_table.setRowCount(min(10, len(trades_df)))  # Show max 10 trades
            trades_table.setColumnCount(6)
            trades_table.setHorizontalHeaderLabels(["Type", "Entry Time", "Exit Time", "Entry Price", "Exit Price", "P&L"])
            
            # Style the table
            trades_table.setStyleSheet("""
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
            """)
            
            # Fill the table with trade data
            for i, (idx, trade) in enumerate(trades_df.head(10).iterrows()):
                trades_table.setItem(i, 0, QTableWidgetItem(str(trade.get('type', 'N/A'))))
                trades_table.setItem(i, 1, QTableWidgetItem(str(trade.get('start', 'N/A'))))
                trades_table.setItem(i, 2, QTableWidgetItem(str(trade.get('end', 'N/A'))))
                trades_table.setItem(i, 3, QTableWidgetItem(f"{trade.get('buyprice', 0):.4f}"))
                trades_table.setItem(i, 4, QTableWidgetItem(f"{trade.get('sellprice', 0):.4f}"))
                
                # Calculate P&L
                pnl = trade.get('profit', 0)
                if pnl == 0:
                    pnl = trade.get('sellprice', 0) - trade.get('buyprice', 0)
                
                pnl_item = QTableWidgetItem(f"{pnl:.2f}")
                if pnl > 0:
                    pnl_item.setStyleSheet("color: #00ff00;")
                elif pnl < 0:
                    pnl_item.setStyleSheet("color: #ff0000;")
                trades_table.setItem(i, 5, pnl_item)
            
            # Adjust column widths
            trades_table.horizontalHeader().setStretchLastSection(True)
            trades_table.resizeColumnsToContents()
            
            layout.addWidget(trades_table)
            
        except Exception as e:
            print(f"Error creating trades table: {e}")
        
        return container
