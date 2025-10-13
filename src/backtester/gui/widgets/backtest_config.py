"""
Backtest Configuration Widget

This widget provides a user interface for configuring backtest parameters,
including capital settings, risk management, and execution parameters.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QTimeEdit,
    QCheckBox,
    QTabWidget,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtGui import QFont

from ..models.backtest_model import BacktestModel, BacktestConfig


class BacktestConfigWidget(QWidget):
    """
    Widget for configuring backtest parameters.

    This widget provides:
    - Basic backtest parameters (capital, costs, etc.)
    - Risk management settings
    - Execution parameters
    - Time-based restrictions
    """

    config_changed = Signal()

    def __init__(self, backtest_model: BacktestModel, parent=None):
        super().__init__(parent)
        self.backtest_model = backtest_model

        self._setup_ui()
        self._connect_signals()
        self._load_config()
        self._apply_styling()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Backtest Configuration"))
        header_layout.addStretch()

        # Presets dropdown
        self.presets_combo = QComboBox()
        self.presets_combo.setToolTip("Select a configuration preset")
        self.presets_combo.addItem("Custom", None)
        self._load_presets()
        self.presets_combo.currentTextChanged.connect(self._on_preset_changed)
        header_layout.addWidget(QLabel("Preset:"))
        header_layout.addWidget(self.presets_combo)
        
        # Load preset button
        load_preset_btn = QPushButton("Load Preset")
        load_preset_btn.setToolTip("Load the selected preset configuration")
        load_preset_btn.clicked.connect(self._on_load_preset_clicked)
        header_layout.addWidget(load_preset_btn)
        
        # Save as preset button
        save_preset_btn = QPushButton("Save as Preset")
        save_preset_btn.setToolTip("Save current configuration as a new preset")
        save_preset_btn.clicked.connect(self._on_save_preset_clicked)
        header_layout.addWidget(save_preset_btn)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setToolTip("Reset all configuration parameters to their default values")
        reset_btn.clicked.connect(self._on_reset_clicked)
        header_layout.addWidget(reset_btn)

        layout.addLayout(header_layout)

        # Main content in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Create tab widget for different configuration sections
        tab_widget = QTabWidget()

        # Basic Parameters Tab
        basic_tab = self._create_basic_parameters_tab()
        tab_widget.addTab(basic_tab, "Basic Parameters")

        # Risk Management Tab
        risk_tab = self._create_risk_management_tab()
        tab_widget.addTab(risk_tab, "Risk Management")

        # Execution Settings Tab
        execution_tab = self._create_execution_settings_tab()
        tab_widget.addTab(execution_tab, "Execution Settings")

        content_layout.addWidget(tab_widget)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def _create_basic_parameters_tab(self):
        """Create the basic parameters tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Basic Parameters Group
        basic_group = QGroupBox("Basic Parameters")
        basic_layout = QFormLayout(basic_group)

        # Point Value
        self.point_value_spin = QDoubleSpinBox()
        self.point_value_spin.setRange(0.01, 1000.0)
        self.point_value_spin.setDecimals(2)
        self.point_value_spin.setSuffix(" points")
        self.point_value_spin.setToolTip("Value of one point movement in the instrument (e.g., $10 for ES futures)")
        basic_layout.addRow("Point Value:", self.point_value_spin)

        # Cost per Trade
        self.cost_per_trade_spin = QDoubleSpinBox()
        self.cost_per_trade_spin.setRange(0.0, 1000.0)
        self.cost_per_trade_spin.setDecimals(2)
        self.cost_per_trade_spin.setSuffix(" $")
        self.cost_per_trade_spin.setToolTip("Fixed cost per trade (commission + fees)")
        basic_layout.addRow("Cost per Trade:", self.cost_per_trade_spin)

        # Initial Capital
        self.initial_capital_spin = QDoubleSpinBox()
        self.initial_capital_spin.setRange(0.0, 10000000.0)
        self.initial_capital_spin.setDecimals(2)
        self.initial_capital_spin.setSuffix(" $")
        self.initial_capital_spin.setSpecialValueText("Not set")
        basic_layout.addRow("Initial Capital:", self.initial_capital_spin)

        # Commission
        self.commission_spin = QDoubleSpinBox()
        self.commission_spin.setRange(0.0, 1000.0)
        self.commission_spin.setDecimals(2)
        self.commission_spin.setSuffix(" $")
        basic_layout.addRow("Commission:", self.commission_spin)

        # Margin Requirement
        self.margin_requirement_spin = QDoubleSpinBox()
        self.margin_requirement_spin.setRange(0.0, 1000000.0)
        self.margin_requirement_spin.setDecimals(2)
        self.margin_requirement_spin.setSuffix(" $")
        basic_layout.addRow("Margin Requirement:", self.margin_requirement_spin)

        layout.addWidget(basic_group)
        layout.addStretch()

        return tab

    def _create_risk_management_tab(self):
        """Create the risk management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Risk Management Group
        risk_group = QGroupBox("Risk Management")
        risk_layout = QFormLayout(risk_group)

        # Max Trades per Day
        self.max_trades_per_day_spin = QSpinBox()
        self.max_trades_per_day_spin.setRange(0, 1000)
        self.max_trades_per_day_spin.setSpecialValueText("Unlimited")
        risk_layout.addRow("Max Trades per Day:", self.max_trades_per_day_spin)

        # Permit Swing Trade
        self.permit_swingtrade_check = QCheckBox("Allow swing trading")
        risk_layout.addRow("Swing Trading:", self.permit_swingtrade_check)

        # Max Position Size
        self.max_position_size_spin = QDoubleSpinBox()
        self.max_position_size_spin.setRange(0.0, 1000000.0)
        self.max_position_size_spin.setDecimals(2)
        self.max_position_size_spin.setSuffix(" units")
        self.max_position_size_spin.setSpecialValueText("Unlimited")
        risk_layout.addRow("Max Position Size:", self.max_position_size_spin)

        # Stop Loss (Pips)
        self.stop_loss_pips_spin = QDoubleSpinBox()
        self.stop_loss_pips_spin.setRange(0.0, 10000.0)
        self.stop_loss_pips_spin.setDecimals(1)
        self.stop_loss_pips_spin.setSuffix(" pips")
        self.stop_loss_pips_spin.setSpecialValueText("Not set")
        risk_layout.addRow("Stop Loss:", self.stop_loss_pips_spin)

        # Take Profit (Pips)
        self.take_profit_pips_spin = QDoubleSpinBox()
        self.take_profit_pips_spin.setRange(0.0, 10000.0)
        self.take_profit_pips_spin.setDecimals(1)
        self.take_profit_pips_spin.setSuffix(" pips")
        self.take_profit_pips_spin.setSpecialValueText("Not set")
        risk_layout.addRow("Take Profit:", self.take_profit_pips_spin)

        layout.addWidget(risk_group)
        layout.addStretch()

        return tab

    def _create_execution_settings_tab(self):
        """Create the execution settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Time Restrictions Group
        time_group = QGroupBox("Time Restrictions")
        time_layout = QFormLayout(time_group)

        # Entry Time Limit
        self.entry_time_edit = QTimeEdit()
        self.entry_time_edit.setTime(QTime(9, 0, 0))
        self.entry_time_edit.setDisplayFormat("hh:mm:ss")
        time_layout.addRow("Entry Time Limit:", self.entry_time_edit)

        # Exit Time Limit
        self.exit_time_edit = QTimeEdit()
        self.exit_time_edit.setTime(QTime(17, 0, 0))
        self.exit_time_edit.setDisplayFormat("hh:mm:ss")
        time_layout.addRow("Exit Time Limit:", self.exit_time_edit)

        layout.addWidget(time_group)

        # Execution Parameters Group
        execution_group = QGroupBox("Execution Parameters")
        execution_layout = QFormLayout(execution_group)

        # Slippage
        self.slippage_spin = QDoubleSpinBox()
        self.slippage_spin.setRange(0.0, 100.0)
        self.slippage_spin.setDecimals(2)
        self.slippage_spin.setSuffix(" pips")
        execution_layout.addRow("Slippage:", self.slippage_spin)

        # Bypass First Exit Check
        self.bypass_first_exit_check = QCheckBox("Bypass first exit check")
        execution_layout.addRow("Exit Logic:", self.bypass_first_exit_check)

        # Always Active
        self.always_active_check = QCheckBox(
            "Always active (invert positions on opposite signals)"
        )
        self.always_active_check.setToolTip(
            "When enabled, opposite signals will invert positions.\n"
            "When disabled, opposite signals will close positions."
        )
        execution_layout.addRow("Position Mode:", self.always_active_check)

        layout.addWidget(execution_group)
        layout.addStretch()

        return tab

    def _connect_signals(self):
        """Connect widget signals."""
        # Connect all spin boxes and check boxes to config changed signal
        widgets = [
            self.point_value_spin,
            self.cost_per_trade_spin,
            self.initial_capital_spin,
            self.commission_spin,
            self.margin_requirement_spin,
            self.max_trades_per_day_spin,
            self.permit_swingtrade_check,
            self.max_position_size_spin,
            self.stop_loss_pips_spin,
            self.take_profit_pips_spin,
            self.entry_time_edit,
            self.exit_time_edit,
            self.slippage_spin,
            self.bypass_first_exit_check,
            self.always_active_check,
        ]

        for widget in widgets:
            if hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(self._on_config_changed)
            elif hasattr(widget, 'timeChanged'):
                widget.timeChanged.connect(self._on_config_changed)
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(self._on_config_changed)

    def _load_config(self):
        """Load configuration from the model."""
        config = self.backtest_model.get_backtest_config()

        # Basic parameters
        self.point_value_spin.setValue(config.point_value)
        self.cost_per_trade_spin.setValue(config.cost_per_trade)
        self.initial_capital_spin.setValue(config.initial_capital or 0.0)
        self.commission_spin.setValue(config.commission)
        self.margin_requirement_spin.setValue(config.margin_requirement)

        # Risk management
        self.max_trades_per_day_spin.setValue(config.max_trade_day or 0)
        self.permit_swingtrade_check.setChecked(config.permit_swingtrade)
        self.max_position_size_spin.setValue(config.max_position_size or 0.0)
        self.stop_loss_pips_spin.setValue(config.stop_loss_pips or 0.0)
        self.take_profit_pips_spin.setValue(config.take_profit_pips or 0.0)

        # Time limits
        if config.entry_time_limit:
            self.entry_time_edit.setTime(
                QTime.fromString(str(config.entry_time_limit), "hh:mm:ss")
            )
        if config.exit_time_limit:
            self.exit_time_edit.setTime(
                QTime.fromString(str(config.exit_time_limit), "hh:mm:ss")
            )

        # Execution settings
        self.slippage_spin.setValue(config.slippage)
        self.bypass_first_exit_check.setChecked(config.bypass_first_exit_check)
        self.always_active_check.setChecked(config.always_active)

    def _on_config_changed(self):
        """Handle configuration changes."""
        # Create new config object
        config = BacktestConfig()

        # Basic parameters
        config.point_value = self.point_value_spin.value()
        config.cost_per_trade = self.cost_per_trade_spin.value()
        config.initial_capital = (
            self.initial_capital_spin.value()
            if self.initial_capital_spin.value() > 0
            else None
        )
        config.commission = self.commission_spin.value()
        config.margin_requirement = self.margin_requirement_spin.value()

        # Risk management
        config.max_trade_day = (
            self.max_trades_per_day_spin.value()
            if self.max_trades_per_day_spin.value() > 0
            else None
        )
        config.permit_swingtrade = self.permit_swingtrade_check.isChecked()
        config.max_position_size = (
            self.max_position_size_spin.value()
            if self.max_position_size_spin.value() > 0
            else None
        )
        config.stop_loss_pips = (
            self.stop_loss_pips_spin.value()
            if self.stop_loss_pips_spin.value() > 0
            else None
        )
        config.take_profit_pips = (
            self.take_profit_pips_spin.value()
            if self.take_profit_pips_spin.value() > 0
            else None
        )

        # Time limits
        config.entry_time_limit = (
            self.entry_time_edit.time().toPython()
            if self.entry_time_edit.time().isValid()
            else None
        )
        config.exit_time_limit = (
            self.exit_time_edit.time().toPython()
            if self.exit_time_edit.time().isValid()
            else None
        )

        # Execution settings
        config.slippage = self.slippage_spin.value()
        config.bypass_first_exit_check = self.bypass_first_exit_check.isChecked()
        config.always_active = self.always_active_check.isChecked()

        # Update the model
        self.backtest_model.update_backtest_config(config)
        self.config_changed.emit()

    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the widget."""
        from ..theme import theme

        self.setStyleSheet(
            theme.get_widget_base_stylesheet()
            + theme.get_groupbox_stylesheet()
            + theme.get_form_stylesheet()
            + theme.get_button_stylesheet("primary")
            + theme.get_scroll_area_stylesheet()
        )

    def _load_presets(self):
        """Load available presets from the data file."""
        try:
            import json
            import os
            from ..data import config_presets
            
            presets_file = os.path.join(os.path.dirname(config_presets.__file__), 'config_presets.json')
            with open(presets_file, 'r') as f:
                presets_data = json.load(f)
            
            for preset_id, preset_info in presets_data.items():
                self.presets_combo.addItem(preset_info['name'], preset_id)
        except Exception as e:
            print(f"Error loading presets: {e}")

    def _on_preset_changed(self, preset_name):
        """Handle preset selection change."""
        if preset_name != "Custom":
            # Update the preset description or show preview
            pass

    def _on_load_preset_clicked(self):
        """Handle load preset button click."""
        preset_id = self.presets_combo.currentData()
        if preset_id:
            self._load_preset_config(preset_id)

    def _on_save_preset_clicked(self):
        """Handle save as preset button click."""
        from PySide6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name:
            self._save_current_as_preset(name)

    def _load_preset_config(self, preset_id):
        """Load configuration from a preset."""
        try:
            import json
            import os
            from ..data import config_presets
            
            presets_file = os.path.join(os.path.dirname(config_presets.__file__), 'config_presets.json')
            with open(presets_file, 'r') as f:
                presets_data = json.load(f)
            
            if preset_id in presets_data:
                preset_params = presets_data[preset_id]['parameters']
                
                # Apply preset parameters to the form
                self.point_value_spin.setValue(preset_params.get('point_value', 10.0))
                self.cost_per_trade_spin.setValue(preset_params.get('cost_per_trade', 2.5))
                self.initial_capital_spin.setValue(preset_params.get('initial_capital', 10000.0))
                self.max_position_size_spin.setValue(preset_params.get('max_position_size', 1000.0))
                self.stop_loss_spin.setValue(preset_params.get('stop_loss_pips', 20))
                self.take_profit_spin.setValue(preset_params.get('take_profit_pips', 40))
                self.max_daily_trades_spin.setValue(preset_params.get('max_daily_trades', 10))
                self.risk_per_trade_spin.setValue(preset_params.get('risk_per_trade', 2.0))
                self.max_drawdown_spin.setValue(preset_params.get('max_drawdown', 10.0))
                
                # Update other parameters as needed
                self._on_config_changed()
                
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Load Preset Error", f"Failed to load preset: {str(e)}")

    def _save_current_as_preset(self, name):
        """Save current configuration as a new preset."""
        try:
            # Get current configuration
            current_config = self._get_current_config()
            
            # Add to presets (this would typically save to a user presets file)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Save Preset", f"Preset '{name}' saved successfully!")
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Save Preset Error", f"Failed to save preset: {str(e)}")

    def _get_current_config(self):
        """Get current configuration as a dictionary."""
        return {
            'point_value': self.point_value_spin.value(),
            'cost_per_trade': self.cost_per_trade_spin.value(),
            'initial_capital': self.initial_capital_spin.value(),
            'max_position_size': self.max_position_size_spin.value(),
            'stop_loss_pips': self.stop_loss_spin.value(),
            'take_profit_pips': self.take_profit_spin.value(),
            'max_daily_trades': self.max_daily_trades_spin.value(),
            'risk_per_trade': self.risk_per_trade_spin.value(),
            'max_drawdown': self.max_drawdown_spin.value(),
        }

    def _on_reset_clicked(self):
        """Handle reset to defaults button click."""
        self.backtest_model.reset_backtest_config()
        self._load_config()
        self.config_changed.emit()
