"""
Data Import Dialog for Backtester GUI

This module contains the dialog for importing data from various sources.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QFormLayout, QComboBox, QFileDialog
from PySide6.QtCore import Qt

class DataImportDialog(QDialog):
    """Dialog for importing data from various sources."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Data")
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Source type
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["CSV", "Parquet", "MT5"])
        form_layout.addRow("Source Type:", self.source_type_combo)
        
        # File path
        self.file_path_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._browse_file)
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_btn)
        form_layout.addRow("File Path:", file_layout)
        
        # Symbol
        self.symbol_edit = QLineEdit()
        form_layout.addRow("Symbol:", self.symbol_edit)
        
        # Timeframe
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1min", "5min", "15min", "30min", "60min", "1day"])
        form_layout.addRow("Timeframe:", self.timeframe_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _browse_file(self):
        """Browse for file selection."""
        file_types = "CSV Files (*.csv);;Parquet Files (*.parquet);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", file_types)
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def get_source_type(self):
        """Get the source type."""
        return self.source_type_combo.currentText().lower()
    
    def get_file_path(self):
        """Get the file path."""
        return self.file_path_edit.text()
    
    def get_symbol(self):
        """Get the symbol."""
        return self.symbol_edit.text()
    
    def get_timeframe(self):
        """Get the timeframe."""
        return self.timeframe_combo.currentText()


