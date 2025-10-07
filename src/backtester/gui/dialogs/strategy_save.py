"""
Strategy Save Dialog for Backtester GUI

This module contains the dialog for saving strategy configurations.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QFormLayout
from PySide6.QtCore import Qt

class StrategySaveDialog(QDialog):
    """Dialog for saving strategy configurations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Strategy")
        self.setModal(True)
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Strategy name
        self.name_edit = QLineEdit()
        form_layout.addRow("Strategy Name:", self.name_edit)
        
        # Description
        self.description_edit = QLineEdit()
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_strategy_name(self):
        """Get the strategy name."""
        return self.name_edit.text()
    
    def get_strategy_description(self):
        """Get the strategy description."""
        return self.description_edit.text()
    
    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the dialog."""
        from ..theme import theme
        self.setStyleSheet(
            theme.get_dialog_stylesheet() +
            theme.get_form_stylesheet() +
            theme.get_button_stylesheet("primary")
        )


