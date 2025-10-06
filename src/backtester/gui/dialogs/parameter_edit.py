"""
Parameter Edit Dialog for Backtester GUI

This module contains the dialog for editing signal parameters.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
from PySide6.QtCore import Qt

class ParameterEditDialog(QDialog):
    """Dialog for editing signal parameters."""
    
    def __init__(self, signal_name, parameters, parent=None):
        super().__init__(parent)
        self.signal_name = signal_name
        self.parameters = parameters
        self.parameter_widgets = {}
        self.setWindowTitle(f"Edit {signal_name} Parameters")
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Edit parameters for {self.signal_name}")
        title_label.setStyleSheet("font-weight: bold; color: #fff;")
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Create parameter widgets
        for param_name, param_info in self.parameters.items():
            widget = self._create_parameter_widget(param_info)
            self.parameter_widgets[param_name] = widget
            form_layout.addRow(f"{param_name}:", widget)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _create_parameter_widget(self, param_info):
        """Create a widget for editing a parameter."""
        param_type = param_info.get('type', 'str')
        value = param_info.get('value', '')
        
        if param_type == 'int':
            widget = QSpinBox()
            widget.setRange(param_info.get('min', 0), param_info.get('max', 999999))
            widget.setValue(int(value) if value else 0)
        elif param_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(param_info.get('min', 0.0), param_info.get('max', 999999.0))
            widget.setValue(float(value) if value else 0.0)
            widget.setDecimals(2)
        elif param_type == 'bool':
            widget = QCheckBox()
            widget.setChecked(bool(value) if value else False)
        elif param_type == 'choice':
            widget = QComboBox()
            widget.addItems(param_info.get('choices', []))
            widget.setCurrentText(str(value) if value else '')
        else:
            widget = QLineEdit()
            widget.setText(str(value) if value else '')
        
        return widget
    
    def get_parameter_values(self):
        """Get the current parameter values."""
        values = {}
        for param_name, widget in self.parameter_widgets.items():
            if isinstance(widget, QSpinBox):
                values[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[param_name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[param_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[param_name] = widget.currentText()
            else:
                values[param_name] = widget.text()
        return values


