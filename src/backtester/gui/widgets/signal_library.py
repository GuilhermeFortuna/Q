"""
Signal Library Widget for Backtester GUI

This module contains the interface for browsing and selecting available trading signals,
including search, filtering, and parameter preview functionality.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QComboBox,
    QSplitter,
    QScrollArea,
    QFrame,
    QFormLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from ..models.strategy_model import StrategyModel, SignalRole, SignalParameter


class SignalItemWidget(QFrame):
    """Custom widget for displaying signal information in the list."""
    
    signal_selected = Signal(str)  # signal_class_name
    add_to_strategy_requested = Signal(str, object)  # signal_class_name, role
    
    def __init__(self, signal_class_name: str, signal_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.signal_class_name = signal_class_name
        self.signal_info = signal_info
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the signal item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header with signal name and add button
        header_layout = QHBoxLayout()
        
        # Signal name
        self.name_label = QLabel(self.signal_info.get('name', self.signal_class_name))
        self.name_label.setStyleSheet("font-weight: bold; color: #fff; font-size: 12px;")
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        # Add to strategy button
        self.add_btn = QPushButton("Add")
        self.add_btn.setFixedSize(60, 24)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0088ff;
            }
        """)
        self.add_btn.clicked.connect(self._on_add_clicked)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Description
        description = self.signal_info.get('description', 'No description available')
        self.desc_label = QLabel(description)
        self.desc_label.setStyleSheet("color: #ccc; font-size: 10px;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(40)
        layout.addWidget(self.desc_label)
        
        # Parameters summary
        params = self.signal_info.get('parameters', {})
        if params:
            param_names = list(params.keys())[:3]  # Show first 3 parameters
            param_text = ", ".join(param_names)
            if len(params) > 3:
                param_text += f" (+{len(params) - 3} more)"
            
            self.params_label = QLabel(f"Parameters: {param_text}")
            self.params_label.setStyleSheet("color: #888; font-size: 9px;")
            layout.addWidget(self.params_label)
    
    def _apply_styling(self):
        """Apply styling to the signal item."""
        self.setStyleSheet("""
            SignalItemWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                margin: 2px;
            }
            SignalItemWidget:hover {
                border-color: #666;
                background-color: #333;
            }
        """)
        self.setFixedHeight(100)
    
    def _on_add_clicked(self):
        """Handle add button click."""
        # For now, default to ENTRY role - this could be enhanced with a role selection dialog
        self.add_to_strategy_requested.emit(self.signal_class_name, SignalRole.ENTRY)
    
    def mousePressEvent(self, event):
        """Handle mouse press to select signal."""
        if event.button() == Qt.LeftButton:
            self.signal_selected.emit(self.signal_class_name)
        super().mousePressEvent(event)


class SignalLibraryWidget(QWidget):
    """
    Widget for browsing and selecting available trading signals.
    
    This widget provides:
    - Signal browser with search and filtering
    - Signal details display
    - Add to strategy functionality
    """
    
    # Signals
    signal_selected = Signal(str)  # signal_class_name
    add_signal_requested = Signal(str, object)  # signal_class_name, role
    
    def __init__(self, strategy_model: StrategyModel, parent=None):
        super().__init__(parent)
        self.strategy_model = strategy_model
        self.signal_items = {}  # signal_class_name -> SignalItemWidget
        self._setup_ui()
        self._apply_styling()
        self._populate_signals()
    
    def _setup_ui(self):
        """Setup the signal library UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Signal Library")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(60, 24)
        refresh_btn.clicked.connect(self._populate_signals)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Search and filter section
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout(search_group)
        
        # Search box
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search signals...")
        self.search_edit.textChanged.connect(self._filter_signals)
        search_layout.addWidget(self.search_edit)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Momentum", "Trend", "Volatility", "Volume", "Custom"])
        self.category_combo.currentTextChanged.connect(self._filter_signals)
        filter_layout.addWidget(self.category_combo)
        
        search_layout.addLayout(filter_layout)
        layout.addWidget(search_group)
        
        # Splitter for signal list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Signal list panel
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Signal count label
        self.count_label = QLabel("0 signals")
        self.count_label.setStyleSheet("color: #888; font-size: 10px;")
        list_layout.addWidget(self.count_label)
        
        # Signal list
        self.signal_list = QListWidget()
        self.signal_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 3px;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: #0066cc;
            }
        """)
        list_layout.addWidget(self.signal_list)
        
        splitter.addWidget(list_panel)
        
        # Signal details panel
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Details header
        details_header = QLabel("Signal Details")
        details_header.setStyleSheet("font-weight: bold; color: #fff;")
        details_layout.addWidget(details_header)
        
        # Details content
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #fff;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        details_layout.addWidget(self.details_text)
        
        # Add to strategy section
        add_group = QGroupBox("Add to Strategy")
        add_layout = QVBoxLayout(add_group)
        
        # Role selection
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Role:"))
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Entry", "Exit", "Filter", "Confirmation"])
        role_layout.addWidget(self.role_combo)
        
        add_layout.addLayout(role_layout)
        
        # Add button
        self.add_btn = QPushButton("Add to Strategy")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._on_add_to_strategy)
        add_layout.addWidget(self.add_btn)
        
        details_layout.addWidget(add_group)
        details_layout.addStretch()
        
        splitter.addWidget(details_panel)
        
        # Set splitter proportions (70% list, 30% details)
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
        # Connect signals
        self.signal_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _apply_styling(self):
        """Apply styling to the widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #fff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QComboBox {
                background-color: #2b2b2b;
                color: #fff;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
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
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
    
    def _populate_signals(self):
        """Populate the signal list with available signals."""
        # Clear existing items
        self.signal_list.clear()
        self.signal_items.clear()
        
        # Get available signals from model
        available_signals = self.strategy_model.get_available_signals()
        
        if not available_signals:
            # Show message if no signals available
            item = QListWidgetItem("No signals available")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.signal_list.addItem(item)
            self.count_label.setText("0 signals")
            return
        
        # Create signal items
        for signal_class_name, signal_info in available_signals.items():
            signal_item = SignalItemWidget(signal_class_name, signal_info)
            
            # Connect signals
            signal_item.signal_selected.connect(self._on_signal_selected)
            signal_item.add_to_strategy_requested.connect(self._on_add_signal_requested)
            
            # Create list item
            list_item = QListWidgetItem()
            list_item.setSizeHint(signal_item.sizeHint())
            self.signal_list.addItem(list_item)
            self.signal_list.setItemWidget(list_item, signal_item)
            
            # Store reference
            self.signal_items[signal_class_name] = signal_item
        
        # Update count
        self.count_label.setText(f"{len(available_signals)} signals")
        
        # Apply current filter
        self._filter_signals()
    
    def _filter_signals(self):
        """Filter signals based on search text and category."""
        search_text = self.search_edit.text().lower()
        category = self.category_combo.currentText()
        
        visible_count = 0
        
        for i in range(self.signal_list.count()):
            item = self.signal_list.item(i)
            if not item:
                continue
                
            signal_widget = self.signal_list.itemWidget(item)
            if not signal_widget:
                continue
            
            signal_class_name = signal_widget.signal_class_name
            signal_info = signal_widget.signal_info
            
            # Check search text
            matches_search = (
                search_text in signal_class_name.lower() or
                search_text in signal_info.get('name', '').lower() or
                search_text in signal_info.get('description', '').lower()
            )
            
            # Check category (simplified categorization)
            matches_category = True
            if category != "All":
                signal_name = signal_info.get('name', '').lower()
                if category == "Momentum":
                    matches_category = any(x in signal_name for x in ['rsi', 'stochastic', 'momentum'])
                elif category == "Trend":
                    matches_category = any(x in signal_name for x in ['ma', 'macd', 'trend', 'crossover'])
                elif category == "Volatility":
                    matches_category = any(x in signal_name for x in ['bollinger', 'atr', 'volatility', 'bands'])
                elif category == "Volume":
                    matches_category = any(x in signal_name for x in ['volume', 'vwap'])
                elif category == "Custom":
                    matches_category = signal_class_name.startswith('Custom')
            
            # Show/hide item
            if matches_search and matches_category:
                item.setHidden(False)
                visible_count += 1
            else:
                item.setHidden(True)
        
        # Update count
        self.count_label.setText(f"{visible_count} signals")
    
    def _on_signal_selected(self, signal_class_name: str):
        """Handle signal selection."""
        self.signal_selected.emit(signal_class_name)
        self._update_details(signal_class_name)
        self.add_btn.setEnabled(True)
    
    def _on_add_signal_requested(self, signal_class_name: str, role: SignalRole):
        """Handle add signal request from signal item."""
        self.add_signal_requested.emit(signal_class_name, role)
    
    def _on_add_to_strategy(self):
        """Handle add to strategy button click."""
        current_item = self.signal_list.currentItem()
        if not current_item:
            return
        
        signal_widget = self.signal_list.itemWidget(current_item)
        if not signal_widget:
            return
        
        signal_class_name = signal_widget.signal_class_name
        role_text = self.role_combo.currentText()
        
        # Convert role text to enum
        role_map = {
            "Entry": SignalRole.ENTRY,
            "Exit": SignalRole.EXIT,
            "Filter": SignalRole.FILTER,
            "Confirmation": SignalRole.CONFIRMATION
        }
        role = role_map.get(role_text, SignalRole.ENTRY)
        
        self.add_signal_requested.emit(signal_class_name, role)
    
    def _on_selection_changed(self):
        """Handle list selection change."""
        current_item = self.signal_list.currentItem()
        if not current_item:
            self.add_btn.setEnabled(False)
            self.details_text.clear()
            return
        
        signal_widget = self.signal_list.itemWidget(current_item)
        if signal_widget:
            self._update_details(signal_widget.signal_class_name)
            self.add_btn.setEnabled(True)
    
    def _update_details(self, signal_class_name: str):
        """Update the details panel with signal information."""
        available_signals = self.strategy_model.get_available_signals()
        signal_info = available_signals.get(signal_class_name)
        
        if not signal_info:
            self.details_text.clear()
            return
        
        # Build details text
        details = []
        details.append(f"<b>Signal:</b> {signal_info.get('name', signal_class_name)}")
        details.append(f"<b>Class:</b> {signal_class_name}")
        details.append("")
        details.append(f"<b>Description:</b>")
        details.append(signal_info.get('description', 'No description available'))
        details.append("")
        
        # Parameters
        parameters = signal_info.get('parameters', {})
        if parameters:
            details.append("<b>Parameters:</b>")
            for param_name, param in parameters.items():
                param_type = param.parameter_type
                required = " (required)" if param.required else " (optional)"
                default = f" = {param.value}" if param.value is not None else ""
                details.append(f"• {param_name}: {param_type}{required}{default}")
                if param.description:
                    details.append(f"  <i>{param.description}</i>")
        else:
            details.append("<b>Parameters:</b> None")
        
        self.details_text.setHtml("<br>".join(details))
    
    def refresh_signals(self):
        """Refresh the signal list from the model."""
        self._populate_signals()
    
    def select_signal(self, signal_class_name: str):
        """Select a specific signal in the list."""
        for i in range(self.signal_list.count()):
            item = self.signal_list.item(i)
            if item and not item.isHidden():
                signal_widget = self.signal_list.itemWidget(item)
                if signal_widget and signal_widget.signal_class_name == signal_class_name:
                    self.signal_list.setCurrentItem(item)
                    break
