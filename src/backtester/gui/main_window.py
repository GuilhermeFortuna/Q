"""
Main Window for Backtester GUI

This module contains the main application window that provides a tabbed interface
for all backtesting workflows including strategy building, data configuration,
backtest setup, and execution monitoring.
"""

import os
import sys

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QMessageBox,
    QApplication,
    QDialog,
)
from PySide6.QtCore import Qt, QTimer

from src.helper import PROJECT_ROOT
from .controllers.execution_controller import ExecutionController
from .controllers.strategy_controller import StrategyController
from .models.backtest_model import BacktestModel
from .models.strategy_model import StrategyModel
from .widgets.backtest_config import BacktestConfigWidget
from .widgets.data_config import DataConfigWidget
from .widgets.execution_monitor import ExecutionMonitorWidget
from .widgets.strategy_builder import StrategyBuilderWidget


class BacktesterMainWindow(QMainWindow):
    """
    Main application window for the Backtester GUI.

    This is the central component of the Backtester GUI application, providing
    a comprehensive tabbed interface for all backtesting workflows. The window
    follows a Model-View-Controller (MVC) architecture with Qt's signal/slot
    mechanism for loose coupling between components.

    The main window consists of four primary tabs:
    - Strategy Builder: Visual composition of trading strategies
    - Data Configuration: Loading and validation of market data
    - Backtest Configuration: Parameter setup for backtest execution
    - Execution & Monitoring: Real-time backtest execution and results

    Attributes:
        strategy_model (StrategyModel): Manages strategy configuration and state
        backtest_model (BacktestModel): Handles data sources and backtest config
        strategy_controller (StrategyController): Business logic for strategy operations
        execution_controller (ExecutionController): Manages backtest execution
        tab_widget (QTabWidget): Main tabbed interface container
        strategy_builder (StrategyBuilderWidget): Strategy composition interface
        data_config (DataConfigWidget): Data loading and configuration interface
        backtest_config (BacktestConfigWidget): Parameter configuration interface
        execution_monitor (ExecutionMonitorWidget): Real-time execution monitoring

    Signals:
        tab_changed(int): Emitted when active tab changes
        application_closing(): Emitted before application closes

    Example:
        ```python
        from PySide6.QtWidgets import QApplication
        from src.backtester.gui.main_window import BacktesterMainWindow
        import sys

        app = QApplication(sys.argv)
        window = BacktesterMainWindow()
        window.show()
        sys.exit(app.exec())
        ```
    """

    def __init__(self, parent=None):
        """
        Initialize the BacktesterMainWindow.

        Sets up the main application window with all necessary components including
        models, controllers, UI widgets, and signal connections. The window is
        configured with a professional dark theme and proper sizing constraints.

        Args:
            parent (Optional[QWidget]): Parent widget for this window. Defaults to None.

        Note:
            The initialization process follows this sequence:
            1. Set window properties (title, size)
            2. Initialize models and controllers
            3. Setup UI components and layout
            4. Connect signals between components
            5. Apply styling and theme
            6. Set initial status
        """
        super().__init__(parent)
        self.setWindowTitle("Backtester - Quantitative Trading Research Toolkit")
        self.setMinimumSize(1200, 800)

        # Initialize models and controllers
        self.backtest_model = BacktestModel()
        self.strategy_model = StrategyModel(self.backtest_model)
        self.strategy_controller = StrategyController(self.strategy_model)
        self.execution_controller = ExecutionController(self.backtest_model)

        # Setup UI components
        self._setup_ui()
        self._setup_connections()
        self._apply_styling()

        # Initialize status
        self._update_status("Ready")

    def _setup_ui(self):
        """
        Initialize the main user interface components.

        Creates the central widget with tabbed interface, menu bar, toolbar,
        and status bar. This method sets up the basic structure of the main
        window before individual tabs are created.

        The UI structure:
        - Central widget with vertical layout
        - Tab widget containing all main interfaces
        - Menu bar with File, Edit, View, and Help menus
        - Toolbar with quick access buttons
        - Status bar with progress indicator and connection status
        """
        # Create central widget with tabbed interface
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create individual tabs
        self._create_tabs()

        # Setup menu bar, toolbar, and status bar
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()

    def _create_tabs(self):
        """
        Create the main tab widgets.

        Initializes all four primary tabs of the application:
        1. Strategy Builder - Visual strategy composition interface
        2. Data Configuration - Market data loading and validation
        3. Backtest Configuration - Parameter setup and configuration
        4. Execution & Monitoring - Real-time backtest execution and results

        Each tab widget is connected to its respective model and controller
        to maintain proper MVC separation and data flow.
        """
        # Strategy Builder Tab
        self.strategy_builder = StrategyBuilderWidget(
            self.strategy_model, self.strategy_controller
        )
        self.tab_widget.addTab(self.strategy_builder, "Strategy Builder")

        # Data Configuration Tab
        self.data_config = DataConfigWidget(self.backtest_model)
        self.tab_widget.addTab(self.data_config, "Data Configuration")

        # Backtest Configuration Tab
        self.backtest_config = BacktestConfigWidget(self.backtest_model)
        self.tab_widget.addTab(self.backtest_config, "Backtest Configuration")

        # Execution & Monitoring Tab
        self.execution_monitor = ExecutionMonitorWidget(
            self.backtest_model, self.strategy_model, self.execution_controller
        )
        self.tab_widget.addTab(self.execution_monitor, "Execution & Monitoring")

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        # New Strategy
        new_action = QAction("&New Strategy", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("Create a new trading strategy")
        new_action.triggered.connect(self._new_strategy)
        file_menu.addAction(new_action)

        # Open Strategy
        open_action = QAction("&Open Strategy", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open an existing strategy file")
        open_action.triggered.connect(self._open_strategy)
        file_menu.addAction(open_action)

        # Save Strategy
        save_action = QAction("&Save Strategy", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("Save current strategy")
        save_action.triggered.connect(self._save_strategy)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Export Results
        export_action = QAction("&Export Results", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export backtest results")
        export_action.triggered.connect(self._export_results)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        # Undo
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.setStatusTip("Undo last action")
        self.undo_action.triggered.connect(self._undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)

        # Redo
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.setStatusTip("Redo last action")
        self.redo_action.triggered.connect(self._redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        # Show Strategy Builder
        show_builder_action = QAction("&Strategy Builder", self)
        show_builder_action.setStatusTip("Switch to Strategy Builder tab")
        show_builder_action.triggered.connect(
            lambda: self.tab_widget.setCurrentIndex(0)
        )
        view_menu.addAction(show_builder_action)

        # Show Data Config
        show_data_action = QAction("&Data Configuration", self)
        show_data_action.setStatusTip("Switch to Data Configuration tab")
        show_data_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(show_data_action)

        # Show Backtest Config
        show_backtest_action = QAction("&Backtest Configuration", self)
        show_backtest_action.setStatusTip("Switch to Backtest Configuration tab")
        show_backtest_action.triggered.connect(
            lambda: self.tab_widget.setCurrentIndex(2)
        )
        view_menu.addAction(show_backtest_action)

        # Show Execution Monitor
        show_execution_action = QAction("&Execution Monitor", self)
        show_execution_action.setStatusTip("Switch to Execution Monitor tab")
        show_execution_action.triggered.connect(
            lambda: self.tab_widget.setCurrentIndex(3)
        )
        view_menu.addAction(show_execution_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        # About
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Backtester")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create the application toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)

        # Quick access buttons
        new_action = QAction("New", self)
        new_action.setStatusTip("Create new strategy")
        new_action.triggered.connect(self._new_strategy)
        toolbar.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setStatusTip("Open strategy")
        open_action.triggered.connect(self._open_strategy)
        toolbar.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setStatusTip("Save strategy")
        save_action.triggered.connect(self._save_strategy)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Run backtest button
        self.run_backtest_action = QAction("Run Backtest", self)
        self.run_backtest_action.setShortcut("Ctrl+R")
        self.run_backtest_action.setStatusTip(
            "Execute backtest with current configuration"
        )
        self.run_backtest_action.triggered.connect(self._run_backtest)
        self.run_backtest_action.setEnabled(False)
        toolbar.addAction(self.run_backtest_action)

        # Stop backtest button
        self.stop_backtest_action = QAction("Stop Backtest", self)
        self.stop_backtest_action.setShortcut("Ctrl+Shift+R")
        self.stop_backtest_action.setStatusTip("Stop running backtest")
        self.stop_backtest_action.triggered.connect(self._stop_backtest)
        self.stop_backtest_action.setEnabled(False)
        toolbar.addAction(self.stop_backtest_action)

        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh current view")
        refresh_action.triggered.connect(self._refresh_current_view)
        toolbar.addAction(refresh_action)

    def _create_status_bar(self):
        """Create the application status bar."""
        self.status_bar = self.statusBar()

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Memory usage indicator
        self.memory_label = QLabel("Memory: --")
        self.memory_label.setToolTip("Current memory usage")
        self.status_bar.addPermanentWidget(self.memory_label)

        # Last action timestamp
        self.last_action_label = QLabel("")
        self.last_action_label.setToolTip("Last action performed")
        self.status_bar.addPermanentWidget(self.last_action_label)

        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setToolTip("Data source connection status")
        self.status_bar.addPermanentWidget(self.connection_label)

        # Start memory monitoring timer
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self._update_memory_usage)
        self.memory_timer.start(5000)  # Update every 5 seconds

    def _setup_connections(self):
        """Setup signal connections between components."""
        # Connect tab changes to update status
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Connect model changes to UI updates
        self.strategy_model.strategy_changed.connect(self._on_strategy_changed)
        self.backtest_model.data_loaded.connect(self._on_data_loaded)
        self.backtest_model.config_changed.connect(self._on_config_changed)

        # Connect execution controller signals
        self.execution_controller.backtest_started.connect(self._on_backtest_started)
        self.execution_controller.backtest_finished.connect(self._on_backtest_finished)
        self.execution_controller.backtest_error.connect(self._on_backtest_error)
        self.execution_controller.progress_updated.connect(self._on_progress_updated)

        # Connect undo/redo signals
        self.strategy_model.undo_available_changed.connect(self._on_undo_available_changed)
        self.strategy_model.redo_available_changed.connect(self._on_redo_available_changed)

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Setup additional keyboard shortcuts."""
        # Tab switching shortcuts
        tab_shortcuts = [
            ("Ctrl+1", lambda: self.tab_widget.setCurrentIndex(0)),
            ("Ctrl+2", lambda: self.tab_widget.setCurrentIndex(1)),
            ("Ctrl+3", lambda: self.tab_widget.setCurrentIndex(2)),
            ("Ctrl+4", lambda: self.tab_widget.setCurrentIndex(3)),
        ]
        
        for shortcut, callback in tab_shortcuts:
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            # Close any open dialogs or cancel current operation
            self._handle_escape_key()
        else:
            super().keyPressEvent(event)

    def _handle_escape_key(self):
        """Handle escape key press."""
        # Close any open dialogs
        for child in self.findChildren(QDialog):
            if child.isVisible():
                child.reject()
                return
        
        # Cancel current operation if any
        if self.execution_controller.is_running():
            self._stop_backtest()

    def _undo(self):
        """Undo the last operation."""
        if self.strategy_model.undo():
            self._update_status("Undo: " + (self.strategy_model.get_undo_description() or "Unknown"))
        else:
            self._update_status("Nothing to undo")

    def _redo(self):
        """Redo the last undone operation."""
        if self.strategy_model.redo():
            self._update_status("Redo: " + (self.strategy_model.get_redo_description() or "Unknown"))
        else:
            self._update_status("Nothing to redo")

    def _on_undo_available_changed(self, available: bool):
        """Handle undo availability change."""
        self.undo_action.setEnabled(available)
        if available:
            description = self.strategy_model.get_undo_description()
            self.undo_action.setStatusTip(f"Undo: {description}")
        else:
            self.undo_action.setStatusTip("Undo last action")

    def _on_redo_available_changed(self, available: bool):
        """Handle redo availability change."""
        self.redo_action.setEnabled(available)
        if available:
            description = self.strategy_model.get_redo_description()
            self.redo_action.setStatusTip(f"Redo: {description}")
        else:
            self.redo_action.setStatusTip("Redo last action")

    def _apply_styling(self):
        """Apply JetBrains-inspired dark theme styling to the application."""
        from .theme import theme

        self.setStyleSheet(theme.get_main_window_stylesheet())

    def _update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.setText(message)
        self._update_last_action(message)

    def _update_last_action(self, action: str):
        """Update the last action timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_action_label.setText(f"Last: {timestamp}")
        self.last_action_label.setToolTip(f"Last action: {action} at {timestamp}")

    def _update_memory_usage(self):
        """Update memory usage display."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
        except ImportError:
            self.memory_label.setText("Memory: --")
        except Exception:
            self.memory_label.setText("Memory: Error")

    def _refresh_current_view(self):
        """Refresh the current view."""
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # Strategy Builder
            self.strategy_builder._refresh_strategy()
            self._update_status("Strategy builder refreshed")
        elif current_tab == 1:  # Data Configuration
            self.data_config._refresh_statistics()
            self._update_status("Data configuration refreshed")
        elif current_tab == 2:  # Backtest Configuration
            self.backtest_config._load_config()
            self._update_status("Backtest configuration refreshed")
        elif current_tab == 3:  # Execution Monitor
            self.execution_monitor._refresh_display()
            self._update_status("Execution monitor refreshed")

    def _update_window_title(self):
        """Update the window title to show current file."""
        base_title = "Backtester - Quantitative Trading Research Toolkit"
        file_path = self.strategy_model.get_strategy_file_path()

        if file_path:
            import os

            filename = os.path.basename(file_path)
            self.setWindowTitle(f"{base_title} - {filename}")
        else:
            self.setWindowTitle(base_title)

    def _on_tab_changed(self, index: int):
        """Handle tab change events."""
        tab_names = [
            "Strategy Builder",
            "Data Configuration",
            "Backtest Configuration",
            "Execution & Monitoring",
        ]
        if 0 <= index < len(tab_names):
            self._update_status(f"Switched to {tab_names[index]}")

    def _on_strategy_changed(self):
        """Handle strategy model changes."""
        self._update_status("Strategy updated")
        # Use QTimer.singleShot to avoid recursion
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._update_run_button_state)

    def _on_data_loaded(self):
        """Handle data loading completion."""
        self._update_status("Data loaded successfully")
        self._update_run_button_state()

    def _on_config_changed(self):
        """Handle backtest configuration changes."""
        self._update_status("Configuration updated")
        self._update_run_button_state()

    def _on_backtest_started(self):
        """Handle backtest start."""
        self._update_status("Running backtest...")
        self.run_backtest_action.setEnabled(False)
        self.stop_backtest_action.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    def _on_backtest_finished(self, results, ohlc_data_with_indicators):
        """Handle backtest completion."""
        self._update_status("Backtest completed")
        self.run_backtest_action.setEnabled(True)
        self.stop_backtest_action.setEnabled(False)
        self.progress_bar.setVisible(False)

        # Show results in visualizer
        self._show_results(results)

    def _on_backtest_error(self, error_message: str):
        """Handle backtest errors."""
        self._update_status(f"Backtest error: {error_message}")
        self.run_backtest_action.setEnabled(True)
        self.stop_backtest_action.setEnabled(False)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "Backtest Error", error_message)

    def _on_progress_updated(self, progress: int):
        """Handle progress updates."""
        self.progress_bar.setValue(progress)

    def _update_run_button_state(self):
        """Update the state of the run backtest button."""
        can_run = (
            self.strategy_model.has_strategy()
            and self.backtest_model.has_data()
            and self.backtest_model.has_config()
        )
        self.run_backtest_action.setEnabled(can_run)

    def _new_strategy(self):
        """Create a new strategy."""
        # Check for unsaved changes
        if self.strategy_model.has_strategy():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have an unsaved strategy. Do you want to save it before creating a new one?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self._save_strategy()
                if not self.strategy_model.get_strategy_file_path():
                    return  # Save was cancelled
            elif reply == QMessageBox.Cancel:
                return  # User cancelled
            # If Discard, continue with creating new strategy

        self.strategy_model.clear_strategy()
        self.tab_widget.setCurrentIndex(0)  # Switch to Strategy Builder
        self._update_status("New strategy created")
        self._update_window_title()

    def _get_create_strategies_directory(self) -> str:
        # Set default directory for strategies
        strategies_dir = os.path.join(
            PROJECT_ROOT, "src", "backtester", "gui", "saved_strategies"
        )
        if not os.path.exists(strategies_dir):
            try:
                os.makedirs(strategies_dir, exist_ok=True)
                self._update_status(
                    f"Created default strategies directory: {strategies_dir}"
                )
            except:
                strategies_dir = os.getcwd()  # Fallback to current directory

        return strategies_dir

    def _open_strategy(self):
        """Open an existing strategy file."""
        # Check for unsaved changes
        if self.strategy_model.has_strategy():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have an unsaved strategy. Do you want to save it before opening a new one?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self._save_strategy()
                if not self.strategy_model.get_strategy_file_path():
                    return  # Save was cancelled
            elif reply == QMessageBox.Cancel:
                return  # User cancelled
            # If Discard, continue with opening

        # Get file path from dialog
        from PySide6.QtWidgets import QFileDialog

        strategies_dir = self._get_create_strategies_directory()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Strategy", strategies_dir, "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        # Load the strategy
        if self.strategy_model.import_strategy(file_path):
            # Update window title
            self._update_window_title()
            self._update_status(f"Strategy loaded from {file_path}")
            # Switch to Strategy Builder tab
            self.tab_widget.setCurrentIndex(0)
        else:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load strategy from:\n{file_path}\n\nPlease check the file format and try again.",
            )

    def _save_strategy(self):
        """Save the current strategy."""
        if not self.strategy_model.has_strategy():
            QMessageBox.warning(
                self, "No Strategy", "Please create a strategy before saving."
            )
            return

        # Get file path from dialog
        from PySide6.QtWidgets import QFileDialog
        import os
        import re

        # Set default directory for strategies
        strategies_dir = self._get_create_strategies_directory()

        # Get current strategy name for default filename
        strategy_config = self.strategy_model.get_strategy_config()
        default_name = strategy_config.name if strategy_config else "New Strategy"
        # Clean filename (remove invalid characters)
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', default_name)
        default_path = os.path.join(strategies_dir, f"{clean_name}.json")

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Strategy", default_path, "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        # Ensure .json extension
        if not file_path.endswith('.json'):
            file_path += '.json'

        # Save the strategy
        if self.strategy_model.export_strategy(file_path):
            # Update window title
            self._update_window_title()
            self._update_status(f"Strategy saved to {file_path}")
            QMessageBox.information(
                self, "Save Strategy", f"Strategy saved successfully to:\n{file_path}"
            )
        else:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save strategy to:\n{file_path}"
            )

    def _export_results(self):
        """Export backtest results."""
        # TODO: Implement export functionality
        QMessageBox.information(
            self, "Export Results", "Export results functionality to be implemented"
        )

    def _run_backtest(self):
        """
        Run the backtest with current configuration.

        Validates that all required components are available (strategy, data,
        configuration) and starts the backtest execution. The execution runs
        in a separate thread to prevent UI blocking.

        The method performs the following validations:
        - Strategy must be created and valid
        - Market data must be loaded and validated
        - Backtest parameters must be configured

        Raises:
            QMessageBox: Warning dialogs for missing components
            Exception: Any errors during backtest initialization

        Note:
            The actual backtest execution is handled by the ExecutionController
            in a separate thread to maintain UI responsiveness.
        """
        try:
            # Get strategy from model
            strategy = self.strategy_model.get_strategy()
            if not strategy:
                QMessageBox.warning(
                    self, "No Strategy", "Please create a strategy first"
                )
                return

            # Get data and config from model
            data = self.backtest_model.get_data()
            config = self.backtest_model.get_config()

            if not data:
                QMessageBox.warning(self, "No Data", "Please load market data first")
                return

            if not config:
                QMessageBox.warning(
                    self,
                    "No Configuration",
                    "Please configure backtest parameters first",
                )
                return

            # Start backtest
            self.execution_controller.run_backtest(strategy, data, config)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start backtest: {str(e)}")

    def _stop_backtest(self):
        """Stop the running backtest."""
        self.execution_controller.stop_backtest()

    def _show_results(self, results):
        """Show backtest results in the visualizer."""
        try:
            from ...visualizer import show_backtest_summary

            # Get OHLC data for visualization
            ohlc_data = self.backtest_model.get_ohlc_data()

            # Show results window
            show_backtest_summary(
                results=results,
                ohlc_df=ohlc_data,
                title="Backtest Results",
                block=False,
            )

        except Exception as e:
            QMessageBox.warning(
                self, "Visualization Error", f"Could not show results: {str(e)}"
            )

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Backtester",
            "Backtester GUI v1.0\n\n"
            "A comprehensive graphical interface for quantitative trading research.\n\n"
            "Features:\n"
            "• Visual strategy building\n"
            "• Market data management\n"
            "• Real-time backtesting\n"
            "• Advanced analytics\n\n"
            "Built with PySide6 and PyQtGraph",
        )

    def closeEvent(self, event):
        """Handle application close event."""
        # Check for running backtest
        if self.execution_controller.is_running():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A backtest is currently running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.execution_controller.stop_backtest()
            else:
                event.ignore()
                return

        # Check for unsaved strategy
        if self.strategy_model.has_strategy():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have an unsaved strategy. Do you want to save it before exiting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self._save_strategy()
                if not self.strategy_model.get_strategy_file_path():
                    event.ignore()  # Save was cancelled
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
            # If Discard, continue with exit

        event.accept()


def main():
    """Main entry point for the Backtester GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Backtester")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Quantitative Trading Research")

    window = BacktesterMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
