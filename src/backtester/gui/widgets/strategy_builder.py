"""
Strategy Builder Widget

This widget provides a visual interface for composing trading strategies,
including signal configuration, parameter editing, and strategy validation.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QTextEdit,
    QSplitter,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ..models.strategy_model import StrategyModel, SignalType, SignalRole, SignalConfig
from ..controllers.strategy_controller import StrategyController


class SignalParameterWidget(QWidget):
    """Widget for editing a single signal parameter."""

    parameter_changed = Signal(str, str, object)  # signal_id, param_name, value

    def __init__(self, signal_id: str, param_name: str, param_config, parent=None):
        super().__init__(parent)
        self.signal_id = signal_id
        self.param_name = param_name
        self.param_config = param_config

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Parameter name
        name_label = QLabel(f"{self.param_name}:")
        name_label.setMinimumWidth(120)
        layout.addWidget(name_label)

        # Parameter value widget based on type
        if self.param_config.parameter_type == "int":
            self.value_widget = QSpinBox()
            self.value_widget.setRange(
                self.param_config.min_value or -999999,
                self.param_config.max_value or 999999,
            )
            self.value_widget.setValue(self.param_config.value or 0)
        elif self.param_config.parameter_type == "float":
            self.value_widget = QDoubleSpinBox()
            self.value_widget.setRange(
                self.param_config.min_value or -999999.0,
                self.param_config.max_value or 999999.0,
            )
            self.value_widget.setValue(self.param_config.value or 0.0)
            self.value_widget.setDecimals(2)
        elif self.param_config.parameter_type == "str":
            if self.param_config.options:
                self.value_widget = QComboBox()
                self.value_widget.addItems(self.param_config.options)
                self.value_widget.setCurrentText(str(self.param_config.value or ""))
            else:
                self.value_widget = QLineEdit()
                self.value_widget.setText(str(self.param_config.value or ""))
        elif self.param_config.parameter_type == "bool":
            self.value_widget = QCheckBox()
            self.value_widget.setChecked(bool(self.param_config.value))
        else:
            self.value_widget = QLineEdit()
            self.value_widget.setText(str(self.param_config.value or ""))

        layout.addWidget(self.value_widget)

        # Description
        if self.param_config.description:
            desc_label = QLabel(self.param_config.description)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            layout.addWidget(desc_label)

    def _connect_signals(self):
        if hasattr(self.value_widget, 'valueChanged'):
            self.value_widget.valueChanged.connect(self._on_value_changed)
        elif hasattr(self.value_widget, 'textChanged'):
            self.value_widget.textChanged.connect(self._on_value_changed)
        elif hasattr(self.value_widget, 'currentTextChanged'):
            self.value_widget.currentTextChanged.connect(self._on_value_changed)
        elif hasattr(self.value_widget, 'toggled'):
            self.value_widget.toggled.connect(self._on_value_changed)

    def _on_value_changed(self):
        if hasattr(self.value_widget, 'value'):
            value = self.value_widget.value()
        elif hasattr(self.value_widget, 'text'):
            value = self.value_widget.text()
        elif hasattr(self.value_widget, 'currentText'):
            value = self.value_widget.currentText()
        elif hasattr(self.value_widget, 'isChecked'):
            value = self.value_widget.isChecked()
        else:
            value = str(self.value_widget.text())

        self.parameter_changed.emit(self.signal_id, self.param_name, value)


class SignalConfigWidget(QGroupBox):
    """Widget for configuring a single signal."""

    signal_updated = Signal(str)  # signal_id
    signal_removed = Signal(str)  # signal_id

    def __init__(self, signal_config: SignalConfig, parent=None):
        super().__init__(parent)
        self.signal_config = signal_config
        self.parameter_widgets = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setTitle(
            f"{self.signal_config.signal_type.value.upper()} - {self.signal_config.role.value}"
        )
            f"{self.signal_config.signal_type.upper()} - {self.signal_config.role.value}"
        )

        # Set minimum height for better visibility
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)

        # Signal info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"ID: {self.signal_config.signal_id[:8]}..."))
        info_layout.addStretch()

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setStyleSheet("QPushButton { color: red; }")
        remove_btn.clicked.connect(self._on_remove_clicked)
        info_layout.addWidget(remove_btn)

        layout.addLayout(info_layout)

        # Parameters
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        for param_name, param_config in self.signal_config.parameters.items():
            param_widget = SignalParameterWidget(
                self.signal_config.signal_id, param_name, param_config
            )
            param_widget.parameter_changed.connect(self._on_parameter_changed)
            self.parameter_widgets[param_name] = param_widget
            params_layout.addRow(param_widget)

        layout.addWidget(params_group)

        # Description
        if self.signal_config.description:
            desc_label = QLabel(self.signal_config.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(desc_label)

    def _connect_signals(self):
        pass

    def _on_parameter_changed(self, signal_id: str, param_name: str, value):
        self.signal_updated.emit(signal_id)

    def _on_remove_clicked(self):
        self.signal_removed.emit(self.signal_config.signal_id)


class StrategyBuilderWidget(QWidget):
    """
    Main widget for building trading strategies.

    This widget provides:
    - Visual signal composition interface
    - Parameter editing for each signal
    - Strategy validation and preview
    - Integration with the strategy model
    """

    strategy_changed = Signal()

    def __init__(
        self,
        strategy_model: StrategyModel,
        strategy_controller: StrategyController,
        parent=None,
    ):
        super().__init__(parent)
        self.strategy_model = strategy_model
        self.strategy_controller = strategy_controller
        self.signal_widgets = {}

        self._setup_ui()
        self._connect_signals()
        self._update_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Modern header with better styling
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )
        header_layout = QHBoxLayout(header_frame)

        # Title with icon
        title_label = QLabel("Strategy Builder")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px;
            }
        """
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Action buttons with modern styling
        button_style = """
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #6a6a6a;
                border-radius: 6px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #7a7a7a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """

        # Load strategy button
        load_strategy_btn = QPushButton("📁 Load Strategy")
        load_strategy_btn.setStyleSheet(button_style)
        load_strategy_btn.clicked.connect(self._on_load_strategy)
        header_layout.addWidget(load_strategy_btn)

        # Save strategy button
        save_strategy_btn = QPushButton("💾 Save Strategy")
        save_strategy_btn.setStyleSheet(button_style)
        save_strategy_btn.clicked.connect(self._on_save_strategy)
        header_layout.addWidget(save_strategy_btn)

        layout.addWidget(header_frame)

        # Main content area with modern card-based layout
        main_content = QWidget()
        main_layout = QHBoxLayout(main_content)
        main_layout.setSpacing(15)

        # Left panel - Signal library with modern styling
        left_panel = QFrame()
        left_panel.setStyleSheet(
            """
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)

        # Available signals header
        signals_header = QLabel("📊 Available Signals")
        signals_header.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px 0px;
                border-bottom: 2px solid #404040;
                margin-bottom: 10px;
            }
        """
        )
        left_layout.addWidget(signals_header)

        # Signals list with modern styling
        self.signals_list = QListWidget()
        self.signals_list.setStyleSheet(
            """
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 5px;
                color: #ffffff;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
        """
        )
        self._populate_signals_list()
        left_layout.addWidget(self.signals_list)

        # Add signal button with modern styling
        add_signal_btn = QPushButton("➕ Add Selected Signal")
        add_signal_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                padding: 12px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """
        )
        add_signal_btn.clicked.connect(self._on_add_signal)
        left_layout.addWidget(add_signal_btn)

        main_layout.addWidget(left_panel, 1)

        # Right panel - Strategy workspace (give it more space)
        right_panel = QFrame()
        right_panel.setStyleSheet(
            """
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # Strategy workspace header
        workspace_header = QLabel("🎯 Strategy Workspace")
        workspace_header.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px 0px;
                border-bottom: 2px solid #404040;
                margin-bottom: 10px;
            }
        """
        )
        right_layout.addWidget(workspace_header)

        # Strategy info section (auto-created when needed)
        self.strategy_info = QFrame()
        self.strategy_info.setStyleSheet(
            """
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """
        )
        info_layout = QVBoxLayout(self.strategy_info)

        # Strategy name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Strategy Name:"))
        self.strategy_name_edit = QLineEdit()
        self.strategy_name_edit.setPlaceholderText("Enter strategy name...")
        self.strategy_name_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """
        )
        name_layout.addWidget(self.strategy_name_edit)
        info_layout.addLayout(name_layout)

        # Strategy description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.strategy_desc_edit = QTextEdit()
        self.strategy_desc_edit.setPlaceholderText("Enter strategy description...")
        self.strategy_desc_edit.setMaximumHeight(60)
        self.strategy_desc_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #0078d4;
            }
        """
        )
        desc_layout.addWidget(self.strategy_desc_edit)
        info_layout.addLayout(desc_layout)

        right_layout.addWidget(self.strategy_info)

        # Current signals section
        signals_section = QLabel("📈 Strategy Signals")
        signals_section.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px 0px;
                margin-top: 10px;
            }
        """
        )
        right_layout.addWidget(signals_section)

        # Signals container with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(300)  # Set minimum height for better visibility
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 6px;
            }
        """
        )

        self.signals_container = QWidget()
        self.signals_container_layout = QVBoxLayout(self.signals_container)
        self.signals_container_layout.setContentsMargins(10, 10, 10, 10)
        self.signals_container_layout.setSpacing(10)  # Add spacing between signals
        scroll_area.setWidget(self.signals_container)

        right_layout.addWidget(scroll_area)

        # Validation status
        self.validation_label = QLabel("Ready to build your strategy")
        self.validation_label.setStyleSheet(
            """
            QLabel {
                color: #888888;
                font-style: italic;
                padding: 5px;
                background-color: #1e1e1e;
                border-radius: 4px;
                margin-top: 10px;
            }
        """
        )
        right_layout.addWidget(self.validation_label)

        main_layout.addWidget(right_panel, 2)

        layout.addWidget(main_content)

    def _populate_signals_list(self):
        """Populate the list of available signals."""
        self.signals_list.clear()

        available_signals = self.strategy_model.get_available_signals()
        for signal_type, signal_info in available_signals.items():
            item = QListWidgetItem(signal_info["name"])
            item.setData(Qt.UserRole, signal_type)
            item.setToolTip(signal_info["description"])
            self.signals_list.addItem(item)

    def _connect_signals(self):
        """Connect widget signals."""
        self.strategy_model.strategy_changed.connect(self._on_strategy_changed)
        self.strategy_model.signal_added.connect(self._on_signal_added)
        self.strategy_model.signal_removed.connect(self._on_signal_removed)
        self.strategy_model.signal_updated.connect(self._on_signal_updated)
        self.strategy_model.validation_changed.connect(self._on_validation_changed)

        self.strategy_name_edit.textChanged.connect(self._on_strategy_info_changed)
        self.strategy_desc_edit.textChanged.connect(self._on_strategy_info_changed)

    def _update_ui(self):
        """Update the UI based on current strategy state."""
        # Temporarily disconnect text change signals to prevent recursion
        self.strategy_name_edit.textChanged.disconnect()
        self.strategy_desc_edit.textChanged.disconnect()

        if self.strategy_model.has_strategy():
            config = self.strategy_model.get_strategy_config()
            self.strategy_name_edit.setText(config.name)
            self.strategy_desc_edit.setText(config.description)
            self._update_signals_display()
        else:
            self.strategy_name_edit.clear()
            self.strategy_desc_edit.clear()
            self._clear_signals_display()

        # Reconnect the signals
        self.strategy_name_edit.textChanged.connect(self._on_strategy_info_changed)
        self.strategy_desc_edit.textChanged.connect(self._on_strategy_info_changed)

    def _update_signals_display(self):
        """Update the display of current signals."""
        self._clear_signals_display()

        if not self.strategy_model.has_strategy():
            self._add_placeholder()
            return

        config = self.strategy_model.get_strategy_config()

        if not config.signals:
            self._add_placeholder()
        else:
            for signal in config.signals:
                self._add_signal_widget(signal)

    def _clear_signals_display(self):
        """Clear the signals display."""
        for widget in self.signal_widgets.values():
            widget.deleteLater()
        self.signal_widgets.clear()

        # Clear all items from layout
        while self.signals_container_layout.count():
            child = self.signals_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _add_placeholder(self):
        """Add placeholder message when no signals are present."""
        placeholder = QLabel(
            "🚀 Start building your strategy!\n\nSelect a signal from the left panel and click 'Add Selected Signal' to begin."
        )
        placeholder.setStyleSheet(
            """
            color: #888888; 
            font-style: italic; 
            padding: 30px; 
            font-size: 14px;
            background-color: #1a1a1a;
            border: 2px dashed #404040;
            border-radius: 8px;
        """
        )
        placeholder.setAlignment(Qt.AlignCenter)
        self.signals_container_layout.addWidget(placeholder)

    def _add_signal_widget(self, signal_config: SignalConfig):
        """Add a signal widget to the display."""
        signal_widget = SignalConfigWidget(signal_config)
        signal_widget.signal_updated.connect(self._on_signal_widget_updated)
        signal_widget.signal_removed.connect(self._on_signal_widget_removed)

        self.signal_widgets[signal_config.signal_id] = signal_widget
        self.signals_container_layout.addWidget(signal_widget)

    def _on_new_strategy(self):
        """Handle new strategy button click."""
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "New Strategy", "Strategy name:")
        if ok and name:
            description, ok = QInputDialog.getText(
                self, "New Strategy", "Strategy description (optional):"
            )
            if ok:
                self.strategy_model.create_strategy(name, description or "")

    def _on_load_strategy(self):
        """Handle load strategy button click."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Strategy", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.strategy_model.import_strategy(file_path)

    def _on_save_strategy(self):
        """Handle save strategy button click."""
        if not self.strategy_model.has_strategy():
            return

        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Strategy", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.strategy_model.export_strategy(file_path)

    def _on_add_signal(self):
        """Handle add signal button click."""
        current_item = self.signals_list.currentItem()

            QMessageBox.information(
                self,
                "No Signal Selected",
                "Please select a signal from the list first.",
            )
            from PySide6.QtWidgets import QMessageBox

        signal_type = current_item.data(Qt.UserRole)
            return

        signal_type = current_item.data(Qt.UserRole)  # class name string
            strategy_name = (
                self.strategy_name_edit.text().strip()
                or f"Strategy {signal_type.value.title()}"
            )
            strategy_desc = (
                self.strategy_desc_edit.toPlainText().strip()
                or f"Strategy using {signal_type.value.title()}"
            )
        signal_info = available_signals.get(signal_type, {})
        display_name = signal_info.get("name", signal_type)

        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QComboBox,
            QVBoxLayout,
            QLabel,
        )
        if not self.strategy_model.has_strategy():
            strategy_name = (
                self.strategy_name_edit.text().strip()
                or f"Strategy {display_name.title()}"
        dialog.setStyleSheet(
            """
            strategy_desc = (
                self.strategy_desc_edit.toPlainText().strip()
                or f"Strategy using {display_name.title()}"
            )
            self.strategy_model.create_strategy(strategy_name, strategy_desc)

        # Show role selection dialog with modern styling
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QComboBox,
            QVBoxLayout,
            QLabel,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Signal")
        dialog.setModal(True)
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                padding: 5px;
            }
            QComboBox {
        """
        )
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
        header_label = QLabel(f"➕ Add {signal_type.value.upper()} Signal")
        header_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ffffff;"
        )
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 10px;
            }
        """
        buttons.setStyleSheet(
            """

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel(f"➕ Add {display_name.upper()} Signal")
        header_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ffffff;"
        )
        layout.addWidget(header_label)

        # Role selection
        role_label = QLabel("Select signal role:")
        layout.addWidget(role_label)
        """
        )
        role_combo = QComboBox()
        role_combo.addItems([role.value.title() for role in SignalRole])
        layout.addWidget(role_combo)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet(
            """
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #6a6a6a;
                border-radius: 6px;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            role = SignalRole(role_combo.currentText().lower())
            self.strategy_model.add_signal(signal_type, role)

    def _on_strategy_changed(self):
        """Handle strategy changed signal."""
        # Use QTimer.singleShot to avoid recursion
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._update_ui)
        self.strategy_changed.emit()

    def _on_signal_added(self, signal_id: str):
        """Handle signal added signal."""
        self._update_signals_display()

    def _on_signal_removed(self, signal_id: str):
        """Handle signal removed signal."""
        if signal_id in self.signal_widgets:
            self.signal_widgets[signal_id].deleteLater()
            del self.signal_widgets[signal_id]

    def _on_signal_updated(self, signal_id: str):
        """Handle signal updated signal."""
        # Update the specific signal widget if it exists
        if signal_id in self.signal_widgets:
            # Refresh the widget
            pass

    def _on_validation_changed(self, is_valid: bool):
        """Handle validation changed signal."""
        if is_valid:
            self.validation_label.setText("Strategy is valid")
            self.validation_label.setStyleSheet("color: green;")
        else:
            errors = self.strategy_model.get_validation_errors()
            self.validation_label.setText(f"Validation errors: {'; '.join(errors)}")
            self.validation_label.setStyleSheet("color: red;")

    def _on_strategy_info_changed(self):
        """Handle strategy information changes."""
        if self.strategy_model.has_strategy():
            config = self.strategy_model.get_strategy_config()
            config.name = self.strategy_name_edit.text()
            config.description = self.strategy_desc_edit.toPlainText()
            # Don't emit strategy_changed here as it will be emitted by the model

    def _on_signal_widget_updated(self, signal_id: str):
        """Handle signal widget parameter updates."""
        # Update the model with the new parameter values
        signal_widget = self.signal_widgets.get(signal_id)
        if signal_widget:
            for param_name, param_widget in signal_widget.parameter_widgets.items():
                if hasattr(param_widget.value_widget, 'value'):
                    value = param_widget.value_widget.value()
                elif hasattr(param_widget.value_widget, 'text'):
                    value = param_widget.value_widget.text()
                elif hasattr(param_widget.value_widget, 'currentText'):
                    value = param_widget.value_widget.currentText()
                elif hasattr(param_widget.value_widget, 'isChecked'):
                    value = param_widget.value_widget.isChecked()
                else:
                    value = str(param_widget.value_widget.text())

                self.strategy_model.update_signal_parameter(
                    signal_id, param_name, value
                )

    def _on_signal_widget_removed(self, signal_id: str):
        """Handle signal widget removal."""
        self.strategy_model.remove_signal(signal_id)
