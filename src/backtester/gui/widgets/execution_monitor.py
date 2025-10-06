"""
Execution Monitor Widget for Backtester GUI

This module contains the interface for monitoring backtest execution,
including real-time progress tracking, live metrics, and results display.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QProgressBar, QTextEdit, QTableWidget, QTableWidgetItem, QSplitter,
    QTabWidget, QGridLayout, QFrame, QScrollArea, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPalette

from ..models.backtest_model import BacktestModel
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
        self.title_label.setStyleSheet("color: #888; font-size: 11px; font-weight: normal;")
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #fff; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.value_label)
    
    def _apply_styling(self):
        """Apply styling to the metrics card."""
        self.setStyleSheet("""
            MetricsCardWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 6px;
            }
            MetricsCardWidget:hover {
                border-color: #666;
            }
        """)
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
            ("Profit Factor", "0.00")
        ]
        
        for i, (title, value) in enumerate(metrics):
            card = MetricsCardWidget(title, value)
            self.metrics_cards[title] = card
            row = i // 3
            col = i % 3
            self.metrics_layout.addWidget(card, row, col)
    
    def _apply_styling(self):
        """Apply styling to the widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #fff;
            }
        """)
    
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
        self.setStyleSheet("""
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
        """)
    
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
        self.setStyleSheet("""
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
        """)
    
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
    Main widget for monitoring backtest execution.
    
    This widget provides:
    - Real-time progress tracking
    - Live metrics display
    - Execution logs
    - Results visualization
    """
    
    def __init__(self, backtest_model: BacktestModel, execution_controller: ExecutionController, parent=None):
        super().__init__(parent)
        self.backtest_model = backtest_model
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
        """Create the results display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Results will be populated when backtest completes
        self.results_label = QLabel("No results available")
        self.results_label.setAlignment(Qt.AlignCenter)
        self.results_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.results_label)
        
        return widget
    
    def _create_control_buttons(self, layout: QVBoxLayout):
        """Create the control buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Run backtest button
        self.run_btn = QPushButton("Run Backtest")
        self.run_btn.clicked.connect(self._run_backtest)
        self.run_btn.setStyleSheet("""
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
        """)
        button_layout.addWidget(self.run_btn)
        
        # Stop backtest button
        self.stop_btn = QPushButton("Stop Backtest")
        self.stop_btn.clicked.connect(self._stop_backtest)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
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
        """)
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
        self.setStyleSheet("""
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
        """)
    
    def _run_backtest(self):
        """Run the backtest."""
        try:
            # Get strategy from model
            strategy = self.backtest_model.get_strategy()
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
            self.log_widget.add_log_message(f"ERROR: Failed to start backtest: {str(e)}")
    
    def _stop_backtest(self):
        """Stop the running backtest."""
        self.log_widget.add_log_message("Stopping backtest...")
        self.execution_controller.stop_backtest()
    
    def _clear_results(self):
        """Clear the results display."""
        self.results_label.setText("No results available")
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
                "Profit Factor": f"{results.profit_factor:.2f}"
            }
        except Exception as e:
            return {
                "Current P&L": "—",
                "Total Trades": "—",
                "Win Rate": "—",
                "Max DD": "—",
                "Current DD": "—",
                "Profit Factor": "—"
            }
    
    def _update_results_display(self, results):
        """Update the results display."""
        try:
            # Get summary statistics
            summary = self.execution_controller.get_backtest_summary()
            if summary:
                results_text = "Backtest Results Summary\n"
                results_text += "=" * 50 + "\n\n"
                
                for key, value in summary.items():
                    if isinstance(value, (int, float)):
                        if "BRL" in key:
                            results_text += f"{key}: R$ {value:,.2f}\n"
                        else:
                            results_text += f"{key}: {value:.2f}\n"
                    else:
                        results_text += f"{key}: {value}\n"
                
                self.results_label.setText(results_text)
                self.results_label.setStyleSheet("color: #fff; font-size: 11px; font-family: 'Consolas', 'Courier New', monospace;")
            else:
                self.results_label.setText("Results available but summary not generated")
                
        except Exception as e:
            self.results_label.setText(f"Error displaying results: {str(e)}")
            self.results_label.setStyleSheet("color: #ff4444;")
