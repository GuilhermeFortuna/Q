"""
Strategy Builder Widget for Backtester GUI

This module contains the main interface for composing trading strategies,
including signal management, parameter editing, and real-time validation.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QSplitter,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QMessageBox,
    QScrollArea,
    QFrame,
    QMenu,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont, QColor, QPalette

from ..models.strategy_model import StrategyModel, SignalRole, SignalConfig
from ..controllers.strategy_controller import StrategyController
from ..dialogs.parameter_edit import ParameterEditDialog
from .signal_library import SignalLibraryWidget


class SignalTableWidget(QTableWidget):
    """
    Custom table widget for displaying and managing strategy signals.

    This widget provides a comprehensive interface for viewing, editing, and
    managing all signals within a trading strategy. It displays signals in a
    tabular format with columns for enabled status, signal name, role, parameters,
    and action buttons.

    The table supports:
    - Real-time editing of signal parameters
    - Enable/disable toggling for individual signals
    - Signal role management (entry, exit, filter)
    - Inline parameter editing with validation
    - Context menus for advanced operations

    Attributes:
        signal_edited (Signal): Emitted when a signal is edited (signal_id)
        signal_removed (Signal): Emitted when a signal is removed (signal_id)
        signal_toggled (Signal): Emitted when signal enabled state changes (signal_id, enabled)

    Example:
        ```python
        table = SignalTableWidget()
        table.signal_edited.connect(self.on_signal_edited)
        table.add_signal_row(signal_config)
        ```
    """

    signal_edited = Signal(str)  # signal_id
    signal_removed = Signal(str)  # signal_id
    signal_toggled = Signal(str, bool)  # signal_id, enabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the table UI."""
        # Set columns
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(
            ["Enabled", "Signal Name", "Role", "Parameters", "Actions"]
        )

        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(False)

        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Enabled
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Signal Name
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Role
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Parameters
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Actions

        self.setColumnWidth(0, 70)  # Enabled
        self.setColumnWidth(2, 80)  # Role
        self.setColumnWidth(4, 130)  # Actions

        # Connect signals
        self.cellChanged.connect(self._on_cell_changed)
        self.cellClicked.connect(self._on_cell_clicked)

    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the table."""
        from ..theme import theme

        self.setStyleSheet(
            theme.get_table_stylesheet()
            + """
            QCheckBox {
                color: #BBBBBB;
            }
            """
        )

    def add_signal_row(self, signal_config: SignalConfig):
        """Add a signal row to the table."""
        row = self.rowCount()
        self.insertRow(row)

        # Enabled checkbox (centered in cell)
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(signal_config.enabled)
        enabled_checkbox.stateChanged.connect(
            lambda state, signal_id=signal_config.signal_id: self.signal_toggled.emit(
                signal_id, state == Qt.Checked
            )
        )

        # Create a container widget to center the checkbox
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.addWidget(enabled_checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)

        self.setCellWidget(row, 0, checkbox_container)

        # Signal name
        signal_name_item = QTableWidgetItem(signal_config.signal_type)
        signal_name_item.setData(Qt.UserRole, signal_config.signal_id)
        self.setItem(row, 1, signal_name_item)

        # Role
        role_item = QTableWidgetItem(signal_config.role.value.title())
        self.setItem(row, 2, role_item)

        # Parameters summary
        param_summary = self._create_parameter_summary(signal_config.parameters)
        param_item = QTableWidgetItem(param_summary)
        param_item.setToolTip(self._create_parameter_tooltip(signal_config.parameters))
        self.setItem(row, 3, param_item)

        # Actions
        actions_widget = self._create_actions_widget(signal_config.signal_id)
        self.setCellWidget(row, 4, actions_widget)

    def _create_parameter_summary(self, parameters: Dict[str, Any]) -> str:
        """Create a summary string of parameters."""
        if not parameters:
            return "No parameters"

        param_parts = []
        for param_name, param in parameters.items():
            if param.value is not None:
                param_parts.append(f"{param_name}={param.value}")

        if param_parts:
            summary = ", ".join(param_parts[:3])  # Show first 3 parameters
            if len(param_parts) > 3:
                summary += f" (+{len(param_parts) - 3} more)"
            return summary
        else:
            return "Default parameters"

    def _create_parameter_tooltip(self, parameters: Dict[str, Any]) -> str:
        """Create a detailed tooltip for parameters."""
        if not parameters:
            return "No parameters"

        tooltip_parts = []
        for param_name, param in parameters.items():
            param_type = param.parameter_type
            required = " (required)" if param.required else " (optional)"
            value = f" = {param.value}" if param.value is not None else ""
            tooltip_parts.append(f"{param_name}: {param_type}{required}{value}")

        return "\n".join(tooltip_parts)

    def _create_actions_widget(self, signal_id: str) -> QWidget:
        """Create the actions widget for a signal row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Edit button with theme green
        from ..theme import theme

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(50, 26)
        edit_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BACKGROUND_MAIN};
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_HOVER};
            }}
        """
        )
        edit_btn.clicked.connect(lambda: self.signal_edited.emit(signal_id))
        layout.addWidget(edit_btn)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedSize(60, 26)
        remove_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {theme.ERROR};
                color: {theme.BACKGROUND_MAIN};
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ff6666;
            }}
        """
        )
        remove_btn.clicked.connect(lambda: self.signal_removed.emit(signal_id))
        layout.addWidget(remove_btn)

        return widget

    def _on_cell_changed(self, row: int, column: int):
        """Handle cell changes."""
        # This could be used for inline editing if needed
        pass

    def _on_cell_clicked(self, row: int, column: int):
        """Handle cell clicks."""
        # This could be used for additional interactions
        pass

    def update_signal_row(self, signal_config: SignalConfig):
        """Update an existing signal row."""
        for row in range(self.rowCount()):
            signal_name_item = self.item(row, 1)
            if (
                signal_name_item
                and signal_name_item.data(Qt.UserRole) == signal_config.signal_id
            ):
                # Update enabled checkbox
                enabled_checkbox = self.cellWidget(row, 0)
                if enabled_checkbox:
                    enabled_checkbox.setChecked(signal_config.enabled)

                # Update parameters summary
                param_summary = self._create_parameter_summary(signal_config.parameters)
                param_item = self.item(row, 3)
                if param_item:
                    param_item.setText(param_summary)
                    param_item.setToolTip(
                        self._create_parameter_tooltip(signal_config.parameters)
                    )
                break

    def remove_signal_row(self, signal_id: str):
        """Remove a signal row from the table."""
        for row in range(self.rowCount()):
            signal_name_item = self.item(row, 1)
            if signal_name_item and signal_name_item.data(Qt.UserRole) == signal_id:
                self.removeRow(row)
                break

    def clear_signals(self):
        """Clear all signal rows."""
        self.setRowCount(0)


class ValidationPanel(QFrame):
    """Panel for displaying validation errors and warnings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the validation panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Validation")
        title_label.setStyleSheet("font-weight: bold; color: #fff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Status indicator
        from ..theme import theme

        self.status_label = QLabel("✓ Valid")
        self.status_label.setStyleSheet(
            f"color: {theme.ACCENT_PRIMARY}; font-weight: bold;"
        )
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Validation messages
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        self.messages_text.setMaximumHeight(100)
        self.messages_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #2b2b2b;
                color: #fff;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
        """
        )
        layout.addWidget(self.messages_text)

    def _apply_styling(self):
        """Apply styling to the validation panel."""
        self.setStyleSheet(
            """
            ValidationPanel {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """
        )

    def update_validation(self, is_valid: bool, errors: List[str]):
        """Update the validation display."""
        from ..theme import theme

        if is_valid:
            self.status_label.setText("✓ Valid")
            self.status_label.setStyleSheet(
                f"color: {theme.ACCENT_PRIMARY}; font-weight: bold;"
            )
            self.messages_text.clear()
        else:
            self.status_label.setText("✗ Invalid")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")

            # Display errors
            error_html = "<br>".join([f"• {error}" for error in errors])
            self.messages_text.setHtml(
                f"<span style='color: #f44336;'>{error_html}</span>"
            )


class StrategyBuilderWidget(QWidget):
    """
    Main widget for building and configuring trading strategies.

    This is the central component for strategy composition in the Backtester GUI.
    It provides a comprehensive interface for creating, editing, and validating
    trading strategies through a visual drag-and-drop approach.

    The widget consists of three main sections:
    1. Signal Library (left panel): Browse and select available trading signals
    2. Strategy Canvas (center): Visual composition area for arranging signals
    3. Parameter Panel (right): Edit signal parameters and configuration

    Key Features:
    - Drag-and-drop signal composition
    - Real-time parameter validation
    - Visual signal role management (entry, exit, filter)
    - Strategy validation and compilation
    - Signal library with search and filtering
    - Context menus for advanced operations

    Attributes:
        strategy_model (StrategyModel): Manages strategy data and state
        strategy_controller (StrategyController): Handles strategy business logic
        signal_library (SignalLibraryWidget): Panel for signal selection
        signal_table (SignalTableWidget): Table for signal management
        validation_text (QTextEdit): Displays validation messages

    Signals:
        strategy_changed(): Emitted when strategy configuration changes
        signal_added(str): Emitted when signal is added (signal_id)
        signal_removed(str): Emitted when signal is removed (signal_id)
        validation_result(bool, str): Emitted with validation results (is_valid, message)

    Example:
        ```python
        from src.backtester.gui.widgets.strategy_builder import StrategyBuilderWidget
        from src.backtester.gui.models.strategy_model import StrategyModel
        from src.backtester.gui.controllers.strategy_controller import StrategyController

        model = StrategyModel()
        controller = StrategyController(model)
        builder = StrategyBuilderWidget(model, controller)
        builder.strategy_changed.connect(self.on_strategy_changed)
        ```
    """

    # Signals
    strategy_changed = Signal()
    signal_added = Signal(str, object)  # signal_class_name, role
    signal_edited = Signal(str)  # signal_id
    signal_removed = Signal(str)  # signal_id

    def __init__(
        self,
        strategy_model: StrategyModel,
        strategy_controller: StrategyController,
        parent=None,
    ):
        super().__init__(parent)
        self.strategy_model = strategy_model
        self.strategy_controller = strategy_controller

        self._setup_ui()
        self._apply_styling()
        self._connect_signals()
        self._refresh_strategy()

    def _setup_ui(self):
        """Setup the strategy builder UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Strategy Builder")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Action buttons
        self.new_strategy_btn = QPushButton("New Strategy")
        self.new_strategy_btn.clicked.connect(self._on_new_strategy)
        header_layout.addWidget(self.new_strategy_btn)

        self.compile_btn = QPushButton("Compile Strategy")
        self.compile_btn.setEnabled(False)
        self.compile_btn.clicked.connect(self._on_compile_strategy)
        header_layout.addWidget(self.compile_btn)

        layout.addLayout(header_layout)

        # Main content splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Signal Library
        self.signal_library = SignalLibraryWidget(self.strategy_model)
        main_splitter.addWidget(self.signal_library)

        # Right panel - Strategy Canvas
        strategy_panel = QWidget()
        strategy_layout = QVBoxLayout(strategy_panel)
        strategy_layout.setContentsMargins(0, 0, 0, 0)

        # Strategy info
        info_group = QGroupBox("Strategy Information")
        info_layout = QVBoxLayout(info_group)

        # Strategy name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.strategy_name_label = QLabel("No strategy loaded")
        self.strategy_name_label.setStyleSheet("font-weight: bold; color: #fff;")
        name_layout.addWidget(self.strategy_name_label)
        name_layout.addStretch()
        info_layout.addLayout(name_layout)

        # Strategy description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.strategy_desc_label = QLabel("No description")
        self.strategy_desc_label.setStyleSheet("color: #ccc;")
        desc_layout.addWidget(self.strategy_desc_label)
        desc_layout.addStretch()
        info_layout.addLayout(desc_layout)

        strategy_layout.addWidget(info_group)

        # Configured signals
        signals_group = QGroupBox("Configured Signals")
        signals_layout = QVBoxLayout(signals_group)

        # Signal table
        self.signal_table = SignalTableWidget()
        signals_layout.addWidget(self.signal_table)

        # Signal table actions
        table_actions_layout = QHBoxLayout()

        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.setEnabled(False)
        self.move_up_btn.setMinimumHeight(28)
        self.move_up_btn.clicked.connect(self._on_move_signal_up)
        table_actions_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.setEnabled(False)
        self.move_down_btn.setMinimumHeight(28)
        self.move_down_btn.clicked.connect(self._on_move_signal_down)
        table_actions_layout.addWidget(self.move_down_btn)

        table_actions_layout.addStretch()

        self.clear_signals_btn = QPushButton("Clear All")
        self.clear_signals_btn.setEnabled(False)
        self.clear_signals_btn.setMinimumSize(100, 32)
        self.clear_signals_btn.clicked.connect(self._on_clear_signals)
        from ..theme import theme

        self.clear_signals_btn.setStyleSheet(theme.get_button_stylesheet("secondary"))
        table_actions_layout.addWidget(self.clear_signals_btn)

        signals_layout.addLayout(table_actions_layout)
        strategy_layout.addWidget(signals_group)

        # Validation panel
        self.validation_panel = ValidationPanel()
        strategy_layout.addWidget(self.validation_panel)

        main_splitter.addWidget(strategy_panel)

        # Set splitter proportions (30% library, 70% strategy)
        # Use stretch factors to ensure proper proportional sizing
        main_splitter.setStretchFactor(0, 5)  # Left panel: 30%
        main_splitter.setStretchFactor(1, 5)  # Right panel: 70%

        # Set initial sizes as a fallback (based on minimum window width of 1200px)
        main_splitter.setSizes([600, 600])

        layout.addWidget(main_splitter)

    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the widget."""
        from ..theme import theme

        self.setStyleSheet(
            theme.get_widget_base_stylesheet()
            + theme.get_groupbox_stylesheet()
            + theme.get_button_stylesheet("primary")
        )

    def _connect_signals(self):
        """Connect widget signals."""
        # Signal library signals
        self.signal_library.add_signal_requested.connect(self._on_add_signal_requested)

        # Signal table signals
        self.signal_table.signal_edited.connect(self._on_edit_signal)
        self.signal_table.signal_removed.connect(self._on_remove_signal)
        self.signal_table.signal_toggled.connect(self._on_toggle_signal)

        # Model signals
        self.strategy_model.strategy_changed.connect(self._on_strategy_changed)
        self.strategy_model.signal_added.connect(self._on_signal_added)
        self.strategy_model.signal_removed.connect(self._on_signal_removed)
        self.strategy_model.validation_changed.connect(
            self._on_model_validation_changed
        )

        # Controller signals
        self.strategy_controller.validation_changed.connect(
            self._on_controller_validation_changed
        )

    def _refresh_strategy(self):
        """Refresh the strategy display from the model."""
        strategy_config = self.strategy_model.get_strategy_config()

        if strategy_config:
            self.strategy_name_label.setText(strategy_config.name)
            self.strategy_desc_label.setText(
                strategy_config.description or "No description"
            )
            self.compile_btn.setEnabled(True)
            self.clear_signals_btn.setEnabled(True)
        else:
            self.strategy_name_label.setText("No strategy loaded")
            self.strategy_desc_label.setText("No description")
            self.compile_btn.setEnabled(False)
            self.clear_signals_btn.setEnabled(False)

        # Refresh signal table
        self._refresh_signal_table()

        # Validation will be updated by the model's validation_changed signal

    def _refresh_signal_table(self):
        """Refresh the signal table from the model."""
        self.signal_table.clear_signals()

        strategy_config = self.strategy_model.get_strategy_config()
        if strategy_config and strategy_config.signals:
            for signal_config in strategy_config.signals:
                self.signal_table.add_signal_row(signal_config)

        # Update move buttons
        self._update_move_buttons()

    def _update_move_buttons(self):
        """Update the state of move up/down buttons."""
        has_signals = self.signal_table.rowCount() > 0
        has_selection = self.signal_table.currentRow() >= 0

        self.move_up_btn.setEnabled(
            has_signals and has_selection and self.signal_table.currentRow() > 0
        )
        self.move_down_btn.setEnabled(
            has_signals
            and has_selection
            and self.signal_table.currentRow() < self.signal_table.rowCount() - 1
        )

    def _update_validation(self):
        """Update the validation display."""
        is_valid = self.strategy_controller.validate_strategy()
        errors = self.strategy_controller.get_validation_errors()
        self.validation_panel.update_validation(is_valid, errors)

    def _on_new_strategy(self):
        """Handle new strategy button click."""
        reply = QMessageBox.question(
            self,
            "New Strategy",
            "Create a new strategy? This will clear the current strategy.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.strategy_model.create_strategy(
                "New Strategy", "A new trading strategy"
            )

    def _on_compile_strategy(self):
        """Handle compile strategy button click."""
        if self.strategy_controller.compile_strategy():
            QMessageBox.information(
                self, "Compilation", "Strategy compiled successfully!"
            )
        else:
            errors = self.strategy_controller.get_validation_errors()
            error_text = "\n".join(errors) if errors else "Unknown compilation error"
            QMessageBox.warning(
                self,
                "Compilation Error",
                f"Strategy compilation failed:\n\n{error_text}",
            )

    def _on_add_signal_requested(self, signal_class_name: str, role: SignalRole):
        """Handle add signal request from signal library."""
        try:
            signal_id = self.strategy_model.add_signal(signal_class_name, role)
            self.strategy_changed.emit()
        except Exception as e:
            QMessageBox.warning(
                self, "Add Signal Error", f"Failed to add signal: {str(e)}"
            )

    def _on_edit_signal(self, signal_id: str):
        """Handle edit signal request."""
        signal_config = self.strategy_model.get_signal(signal_id)
        if not signal_config:
            return

        # Create parameter edit dialog
        dialog = ParameterEditDialog(
            signal_name=signal_config.signal_type,
            parameters=signal_config.parameters,
            parent=self,
        )

        if dialog.exec() == dialog.Accepted:
            # Get updated parameters from dialog
            updated_params = dialog.get_parameters()

            # Update parameters in model
            for param_name, param_value in updated_params.items():
                self.strategy_model.update_signal_parameter(
                    signal_id, param_name, param_value
                )

    def _on_remove_signal(self, signal_id: str):
        """Handle remove signal request."""
        signal_config = self.strategy_model.get_signal(signal_id)
        if not signal_config:
            return

        reply = QMessageBox.question(
            self,
            "Remove Signal",
            f"Remove signal '{signal_config.signal_type}' from the strategy?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.strategy_model.remove_signal(signal_id)

    def _on_toggle_signal(self, signal_id: str, enabled: bool):
        """Handle signal enable/disable toggle."""
        signal_config = self.strategy_model.get_signal(signal_id)
        if signal_config:
            signal_config.enabled = enabled
            self.strategy_model.strategy_changed.emit()

    def _on_clear_signals(self):
        """Handle clear all signals button click."""
        reply = QMessageBox.question(
            self,
            "Clear Signals",
            "Remove all signals from the strategy?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            strategy_config = self.strategy_model.get_strategy_config()
            if strategy_config:
                # Remove all signals
                signal_ids = [signal.signal_id for signal in strategy_config.signals]
                for signal_id in signal_ids:
                    self.strategy_model.remove_signal(signal_id)

    def _on_move_signal_up(self):
        """Handle move signal up button click."""
        current_row = self.signal_table.currentRow()
        if current_row > 0:
            # Get signal IDs
            strategy_config = self.strategy_model.get_strategy_config()
            if strategy_config and len(strategy_config.signals) > current_row:
                # Swap signals in the model
                signals = strategy_config.signals
                signals[current_row], signals[current_row - 1] = (
                    signals[current_row - 1],
                    signals[current_row],
                )
                self.strategy_model.strategy_changed.emit()
                self.signal_table.selectRow(current_row - 1)

    def _on_move_signal_down(self):
        """Handle move signal down button click."""
        current_row = self.signal_table.currentRow()
        if current_row < self.signal_table.rowCount() - 1:
            # Get signal IDs
            strategy_config = self.strategy_model.get_strategy_config()
            if strategy_config and len(strategy_config.signals) > current_row + 1:
                # Swap signals in the model
                signals = strategy_config.signals
                signals[current_row], signals[current_row + 1] = (
                    signals[current_row + 1],
                    signals[current_row],
                )
                self.strategy_model.strategy_changed.emit()
                self.signal_table.selectRow(current_row + 1)

    def _on_strategy_changed(self):
        """Handle strategy model changes."""
        self._refresh_strategy()
        self.strategy_changed.emit()

    def _on_signal_added(self, signal_id: str):
        """Handle signal added to strategy."""
        self._refresh_signal_table()

    def _on_signal_removed(self, signal_id: str):
        """Handle signal removed from strategy."""
        self._refresh_signal_table()

    def _on_model_validation_changed(self, is_valid: bool):
        """Handle model validation state changes."""
        # Update validation display directly from model
        errors = self.strategy_model.get_validation_errors()
        self.validation_panel.update_validation(is_valid, errors)

    def _on_controller_validation_changed(self, is_valid: bool):
        """Handle controller validation state changes."""
        # Update validation display directly from controller
        errors = self.strategy_controller.get_validation_errors()
        self.validation_panel.update_validation(is_valid, errors)
