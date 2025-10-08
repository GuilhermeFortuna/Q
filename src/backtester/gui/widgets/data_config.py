"""
Data Configuration Widget for Backtester GUI

This module contains the interface for loading and configuring market data,
including data source selection, validation, and preview functionality.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QDateEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QCheckBox,
    QSplitter,
    QHeaderView,
    QAbstractItemView,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont
import pandas as pd

from ..models.backtest_model import BacktestModel, DataSourceConfig
from src.data import CandleData, TickData


class DataSourceWidget(QWidget):
    """
    Widget for configuring a single data source.

    This widget provides a comprehensive interface for configuring individual
    data sources including file paths, connection parameters, date ranges,
    and data validation settings. It supports multiple data source types
    including CSV files, Parquet files, MetaTrader 5, and database connections.

    The widget displays:
    - Data source identification and type selection
    - Configuration parameters specific to the source type
    - Date range selection for historical data
    - Data validation and quality indicators
    - Load/remove actions for the data source

    Attributes:
        source_id (str): Unique identifier for this data source
        config (DataSourceConfig): Configuration object for this source
        source_updated (Signal): Emitted when source configuration changes (source_id)
        load_requested (Signal): Emitted when user requests data loading (source_id)
        source_removed (Signal): Emitted when source is removed (source_id)

    Example:
        ```python
        from src.backtester.gui.widgets.data_config import DataSourceWidget
        from src.backtester.gui.models.backtest_model import DataSourceConfig

        config = DataSourceConfig(
            source_id="EURUSD_1H",
            source_type="CSV",
            symbol="EURUSD",
            timeframe="1H"
        )
        widget = DataSourceWidget("EURUSD_1H", config)
        widget.load_requested.connect(self.on_load_data)
        ```
    """

    source_updated = Signal(str)  # source_id
    load_requested = Signal(str)  # source_id - emitted when user clicks Load Data
    source_removed = Signal(str)  # source_id

    def __init__(self, source_id: str, config: DataSourceConfig, parent=None):
        super().__init__(parent)
        self.source_id = source_id
        self.config = config
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the data source configuration UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()

        self.title_label = QLabel(f"Data Source: {self.source_id}")
        self.title_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #fff;"
        )
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """
        )
        self.remove_btn.clicked.connect(self._remove_source)
        header_layout.addWidget(self.remove_btn)

        layout.addLayout(header_layout)

        # Configuration form
        form_layout = QFormLayout()

        # Source type
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["CSV", "Parquet", "MT5", "Database"])
        self.source_type_combo.setCurrentText(self.config.source_type.upper())
        self.source_type_combo.currentTextChanged.connect(self._on_source_type_changed)
        form_layout.addRow("Source Type:", self.source_type_combo)

        # Symbol
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setText(self.config.symbol)
        self.symbol_edit.textChanged.connect(self._on_config_changed)
        form_layout.addRow("Symbol:", self.symbol_edit)

        # Timeframe
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(
            ["1min", "5min", "15min", "30min", "60min", "1day"]
        )
        self.timeframe_combo.setCurrentText(self.config.timeframe)
        self.timeframe_combo.currentTextChanged.connect(self._on_config_changed)
        form_layout.addRow("Timeframe:", self.timeframe_combo)

        # Date range
        date_layout = QHBoxLayout()

        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDate(self.config.date_from or QDate.currentDate())
        self.date_from_edit.dateChanged.connect(self._on_config_changed)
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.date_from_edit)

        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDate(self.config.date_to or QDate.currentDate())
        self.date_to_edit.dateChanged.connect(self._on_config_changed)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.date_to_edit)

        form_layout.addRow("Date Range:", date_layout)

        # File path (for CSV/Parquet)
        self.file_path_widget = QWidget()
        self.file_path_layout = QHBoxLayout()
        self.file_path_widget.setLayout(self.file_path_layout)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setText(self.config.file_path or "")
        self.file_path_edit.textChanged.connect(self._on_config_changed)
        self.file_path_layout.addWidget(self.file_path_edit)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._browse_file)
        self.file_path_layout.addWidget(self.browse_btn)

        form_layout.addRow("File Path:", self.file_path_widget)

        # Load button
        self.load_btn = QPushButton("Load Data")
        self.load_btn.clicked.connect(self._load_data)
        form_layout.addRow("", self.load_btn)

        layout.addLayout(form_layout)

        # Status
        self.status_label = QLabel("Not loaded")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # Update visibility based on source type
        self._update_ui_visibility()

    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the widget."""
        from ..theme import theme
        self.setStyleSheet(
            theme.get_widget_base_stylesheet() +
            theme.get_groupbox_stylesheet() +
            theme.get_form_stylesheet() +
            theme.get_button_stylesheet("primary")
        )

    def _on_source_type_changed(self, source_type: str):
        """Handle source type changes."""
        self.config.source_type = source_type.lower()
        self._update_ui_visibility()
        self._on_config_changed()

    def _update_ui_visibility(self):
        """Update UI visibility based on source type."""
        is_file_source = self.config.source_type in ["csv", "parquet"]
        self.file_path_widget.setVisible(is_file_source)

    def _on_config_changed(self):
        """Handle configuration changes."""
        # Update config object
        self.config.symbol = self.symbol_edit.text()
        self.config.timeframe = self.timeframe_combo.currentText()
        self.config.date_from = self.date_from_edit.date().toPython()
        self.config.date_to = self.date_to_edit.date().toPython()
        self.config.file_path = self.file_path_edit.text()

        self.source_updated.emit(self.source_id)

    def _browse_file(self):
        """Browse for file selection."""
        file_types = "CSV Files (*.csv);;Parquet Files (*.parquet);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", file_types
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def _load_data(self):
        """Load data from the configured source."""
        self.status_label.setText("Loading...")
        self.status_label.setStyleSheet("color: #ffaa00;")
        self.load_btn.setEnabled(False)

        # Emit dedicated load signal so parent can perform the actual loading
        self.load_requested.emit(self.source_id)

    def _remove_source(self):
        """Remove this data source."""
        self.source_removed.emit(self.source_id)

    def set_loaded_status(self, loaded: bool, message: str = ""):
        """Set the loaded status."""
        if loaded:
            self.status_label.setText("Loaded successfully")
            self.status_label.setStyleSheet("color: #00ff88;")
        else:
            self.status_label.setText(f"Load failed: {message}")
            self.status_label.setStyleSheet("color: #ff4444;")

        self.load_btn.setEnabled(True)

    def get_config(self) -> DataSourceConfig:
        """Get the current configuration."""
        return self.config


class DataPreviewWidget(QWidget):
    """Widget for previewing loaded data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the data preview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Data Preview")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        layout.addWidget(title_label)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        # Statistics
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)

    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the widget."""
        from ..theme import theme
        self.setStyleSheet(
            theme.get_widget_base_stylesheet() +
            theme.get_table_stylesheet() +
            theme.get_form_stylesheet()
        )

    def set_data(self, data, source_id: str):
        """Set the data to preview."""
        if data is None:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.stats_text.clear()
            return

        try:
            # Handle wrapped data objects (CandleData/TickData)
            if hasattr(data, 'df') and data.df is not None:
                df = data.df
            elif hasattr(data, 'data') and data.data is not None:
                df = data.data
            else:
                df = data

            # Set table data
            self.table.setRowCount(min(len(df), 100))  # Limit to 100 rows
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels([str(col) for col in df.columns])

            # Fill table
            for i in range(min(len(df), 100)):
                for j, col in enumerate(df.columns):
                    value = df.iloc[i, j]
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)

            # Resize columns
            self.table.resizeColumnsToContents()

            # Set statistics
            stats = self._get_data_statistics(df, source_id)
            self.stats_text.setPlainText(stats)

        except Exception as e:
            self.stats_text.setPlainText(f"Error displaying data: {str(e)}")

    def _get_data_statistics(self, df, source_id: str) -> str:
        """Get data statistics text."""
        stats = [
            f"Data Source: {source_id}",
            f"Rows: {len(df)}",
            f"Columns: {len(df.columns)}",
            (
                f"Date Range: {df.index.min()} to {df.index.max()}"
                if hasattr(df.index, 'min')
                else "No date range"
            ),
            f"Missing Values: {df.isnull().sum().sum()}",
            "",
            "Column Information:",
        ]

        for col in df.columns:
            stats.append(f"  {col}: {df[col].dtype} ({df[col].isnull().sum()} missing)")

        return "\n".join(stats)


class DataConfigWidget(QWidget):
    """
    Main widget for data configuration and loading.

    This is the central component for managing market data in the Backtester GUI.
    It provides a comprehensive interface for loading, validating, and configuring
    market data from various sources including CSV files, Parquet files, and
    MetaTrader 5 connections.

    The widget consists of several key sections:
    1. Data Source Management: Add, configure, and remove data sources
    2. Data Loading Interface: Load data from configured sources
    3. Data Validation: Real-time validation and quality checking
    4. Data Preview: Tabular and statistical preview of loaded data
    5. Data Statistics: Comprehensive data quality metrics

    Supported Data Sources:
    - CSV Files: Standard OHLCV format with datetime index
    - Parquet Files: Optimized columnar storage for large datasets
    - MetaTrader 5: Direct connection to MT5 terminal
    - Database: Custom database connections (extensible)

    Key Features:
    - Multi-source data management
    - Real-time data validation
    - Data quality indicators and statistics
    - Preview functionality with data tables
    - Automatic data format detection
    - Error handling and user feedback

    Attributes:
        backtest_model (BacktestModel): Manages data sources and loaded data
        data_sources (Dict[str, DataSourceWidget]): Dictionary of data source widgets
        data_table (QTableWidget): Table for data preview
        statistics_text (QTextEdit): Displays data statistics
        validation_text (QTextEdit): Shows validation messages

    Signals:
        data_loaded(str, bool): Emitted when data loading completes (source_id, success)
        data_validated(str, bool, str): Emitted with validation results (source_id, is_valid, message)
        data_source_added(str): Emitted when data source is added (source_id)
        data_source_removed(str): Emitted when data source is removed (source_id)

    Example:
        ```python
        from src.backtester.gui.widgets.data_config import DataConfigWidget
        from src.backtester.gui.models.backtest_model import BacktestModel

        model = BacktestModel()
        widget = DataConfigWidget(model)
        widget.data_loaded.connect(self.on_data_loaded)
        widget.add_data_source("CSV", {"path": "data.csv", "symbol": "EURUSD"})
        ```
    """

    def __init__(self, backtest_model: BacktestModel, parent=None):
        super().__init__(parent)
        self.backtest_model = backtest_model
        self.data_source_widgets = {}

        self._setup_ui()
        self._setup_connections()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the data configuration UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Data Sources tab
        self.sources_tab = self._create_sources_tab()
        self.tab_widget.addTab(self.sources_tab, "Data Sources")

        # Data Preview tab
        self.preview_tab = self._create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "Data Preview")

        # Statistics tab
        self.stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")

    def _create_sources_tab(self) -> QWidget:
        """Create the data sources configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Data Sources")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Add source button
        self.add_source_btn = QPushButton("Add Data Source")
        self.add_source_btn.clicked.connect(self._add_data_source)
        header_layout.addWidget(self.add_source_btn)

        layout.addLayout(header_layout)

        # Sources container
        self.sources_scroll = QScrollArea()
        self.sources_scroll.setWidgetResizable(True)
        self.sources_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sources_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.sources_container = QWidget()
        self.sources_layout = QVBoxLayout(self.sources_container)
        self.sources_layout.setAlignment(Qt.AlignTop)

        self.sources_scroll.setWidget(self.sources_container)
        layout.addWidget(self.sources_scroll)

        # Instructions
        instructions = QLabel(
            "Configure your data sources below. You can load data from CSV files, "
            "Parquet files, or MetaTrader 5. Click 'Add Data Source' to get started."
        )
        instructions.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        return widget

    def _create_preview_tab(self) -> QWidget:
        """Create the data preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Source selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Select Source:"))

        self.preview_source_combo = QComboBox()
        self.preview_source_combo.currentTextChanged.connect(self._update_preview)
        source_layout.addWidget(self.preview_source_combo)

        source_layout.addStretch()
        layout.addLayout(source_layout)

        # Preview widget
        self.preview_widget = DataPreviewWidget()
        layout.addWidget(self.preview_widget)

        return widget

    def _create_stats_tab(self) -> QWidget:
        """Create the statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Statistics display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)

        # Refresh button
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self._refresh_statistics)
        layout.addWidget(refresh_btn)

        return widget

    def _setup_connections(self):
        """Setup signal connections."""
        # Model connections
        self.backtest_model.data_loaded.connect(self._on_data_loaded)
        self.backtest_model.data_loading_error.connect(self._on_data_loading_error)
        self.backtest_model.data_loading_progress.connect(
            self._on_data_loading_progress
        )

    def _apply_styling(self):
        """Apply JetBrains-inspired styling to the widget."""
        from ..theme import theme
        self.setStyleSheet(
            theme.get_widget_base_stylesheet() +
            theme.get_main_window_stylesheet() +
            theme.get_scroll_area_stylesheet() +
            theme.get_button_stylesheet("primary") +
            theme.get_form_stylesheet()
        )

    def _add_data_source(self):
        """Add a new data source."""
        import uuid

        source_id = f"source_{str(uuid.uuid4())[:8]}"

        config = DataSourceConfig(source_type="csv", symbol="EURUSD", timeframe="60min")

        # Add to model
        self.backtest_model.add_data_source(source_id, config)

        # Create widget
        widget = DataSourceWidget(source_id, config)
        widget.source_updated.connect(self._on_source_updated)
        widget.load_requested.connect(self._on_load_requested)
        widget.source_removed.connect(self._on_source_removed)

        self.data_source_widgets[source_id] = widget
        self.sources_layout.addWidget(widget)

        # Update preview combo
        self.preview_source_combo.addItem(source_id, source_id)

    def _on_source_updated(self, source_id: str):
        """Handle source configuration updates."""
        if source_id in self.data_source_widgets:
            widget = self.data_source_widgets[source_id]
            config = widget.get_config()
            self.backtest_model.add_data_source(source_id, config)

    def _on_source_removed(self, source_id: str):
        """Handle source removal."""
        if source_id in self.data_source_widgets:
            widget = self.data_source_widgets[source_id]
            widget.deleteLater()
            del self.data_source_widgets[source_id]

            # Remove from model
            self.backtest_model.remove_data_source(source_id)

            # Update preview combo
            index = self.preview_source_combo.findData(source_id)
            if index >= 0:
                self.preview_source_combo.removeItem(index)

    def _on_load_requested(self, source_id: str):
        """Handle a request from a DataSourceWidget to load its configured data.

        Loads CSV or Parquet files and stores the resulting DataFrame in the
        BacktestModel via `store_loaded_data`. Updates the widget status and
        emits `data_loading_error` on failure.
        """
        if source_id not in self.data_source_widgets:
            return

        widget = self.data_source_widgets[source_id]
        config = widget.get_config()

        try:
            if config.source_type.lower() in ["csv"]:
                # First, peek at the CSV to detect if it has Portuguese columns
                # This helps us decide whether to use the specialized import_from_csv method
                df_peek = None
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        df_peek = pd.read_csv(config.file_path, encoding=enc, nrows=1)
                        break
                    except Exception:
                        continue

                if df_peek is None:
                    raise ValueError("Failed to read CSV with common encodings")

                # Check if CSV has Portuguese column names
                portuguese_columns = [
                    'abertura',
                    'máxima',
                    'maxima',
                    'mínima',
                    'minima',
                    'fechamento',
                    'data',
                    'volume quantidade',
                ]
                has_portuguese = any(
                    col.lower() in portuguese_columns for col in df_peek.columns
                )

                if has_portuguese:
                    # Use CandleData.import_from_csv() which handles Portuguese format
                    print(
                        f"Detected Portuguese columns, using CandleData.import_from_csv()"
                    )
                    data_obj = CandleData(
                        symbol=config.symbol, timeframe=config.timeframe
                    )
                    data_obj.import_from_csv(config.file_path)

                    # import_from_csv sets self.df internally, doesn't return it
                    if data_obj.df is None or data_obj.df.empty:
                        raise ValueError(
                            "CandleData.import_from_csv() failed to load data"
                        )

                    print(
                        f"Successfully loaded Portuguese CSV with columns: {list(data_obj.df.columns)}"
                    )
                else:
                    # Standard CSV loading for English/other formats
                    print(f"Loading standard CSV file")
                    df = None
                    for enc in ("utf-8", "latin-1", "cp1252"):
                        try:
                            df = pd.read_csv(config.file_path, encoding=enc)
                            break
                        except Exception:
                            continue
                    if df is None:
                        raise ValueError("Failed to read CSV with common encodings")

                    # Create CandleData or TickData based on column detection
                    ohlc_columns = ['open', 'high', 'low', 'close']
                    df_columns_lower = [col.lower() for col in df.columns]
                    has_ohlc = any(col in ohlc_columns for col in df_columns_lower)

                    if has_ohlc:
                        data_obj = CandleData(
                            symbol=config.symbol, timeframe=config.timeframe
                        )
                        data_obj.df = df
                        print(f"Created CandleData object for {source_id}")
                    else:
                        data_obj = TickData(symbol=config.symbol)
                        data_obj.df = df
                        print(f"Created TickData object for {source_id}")

            elif config.source_type.lower() in ["parquet"]:
                df = pd.read_parquet(config.file_path)

                # Basic sanity check
                if df is None or df.empty:
                    raise ValueError("Loaded data is empty")

                # Create CandleData or TickData based on column detection
                ohlc_columns = ['open', 'high', 'low', 'close']
                df_columns_lower = [col.lower() for col in df.columns]
                has_ohlc = any(col in ohlc_columns for col in df_columns_lower)

                if has_ohlc:
                    data_obj = CandleData(
                        symbol=config.symbol, timeframe=config.timeframe
                    )
                    data_obj.df = df
                else:
                    data_obj = TickData(symbol=config.symbol)
                    data_obj.df = df

            elif config.source_type.lower() == "mt5":
                # MT5 import - delegate to CandleData if available
                # Convert date objects to datetime objects for MT5
                from datetime import datetime, time
                date_from = datetime.combine(config.date_from, time.min) if config.date_from else None
                date_to = datetime.combine(config.date_to, time.max) if config.date_to else None
                
                candle_data = CandleData(config.symbol, config.timeframe)
                df = candle_data.import_from_mt5(
                    mt5_symbol=config.symbol,
                    timeframe=config.timeframe,
                    date_from=date_from,
                    date_to=date_to,
                )
                if df is None or df.empty:
                    raise ValueError("MT5 import returned empty data")
                data_obj = candle_data
            else:
                raise ValueError(f"Unsupported source type: {config.source_type}")

            # Store wrapped data object in model and update UI
            self.backtest_model.store_loaded_data(source_id, data_obj)
            widget.set_loaded_status(True)

            # Ensure preview combo contains the source
            if self.preview_source_combo.findData(source_id) == -1:
                self.preview_source_combo.addItem(source_id, source_id)

        except Exception as e:
            err_msg = str(e)
            widget.set_loaded_status(False, err_msg)
            # Emit model-level error for other listeners
            self.backtest_model.data_loading_error.emit(err_msg)

    def _on_data_loaded(self):
        """Handle data loading completion."""
        # Update all source widgets
        for widget in self.data_source_widgets.values():
            widget.set_loaded_status(True)

        # Update preview
        self._update_preview()

        # Update statistics
        self._refresh_statistics()

    def _on_data_loading_error(self, error_message: str):
        """Handle data loading errors."""
        # Update all source widgets
        for widget in self.data_source_widgets.values():
            widget.set_loaded_status(False, error_message)

    def _on_data_loading_progress(self, progress: int):
        """Handle data loading progress updates."""
        # TODO: Implement progress updates
        pass

    def _update_preview(self):
        """Update the data preview."""
        current_source = self.preview_source_combo.currentData()
        if current_source:
            # Get data directly from the loaded data (by source_id)
            data = self.backtest_model._loaded_data.get(current_source)
            self.preview_widget.set_data(data, current_source)

    def _refresh_statistics(self):
        """Refresh the statistics display."""
        stats_text = []

        # Get the raw loaded data (by source_id) for display purposes
        loaded_data = self.backtest_model._loaded_data
        if not loaded_data:
            stats_text.append("No data loaded")
        else:
            stats_text.append("Data Sources Summary:")
            stats_text.append("=" * 50)

            for source_id, data in loaded_data.items():
                # Determine data type for display
                data_type = "unknown"
                if hasattr(data, '__class__'):
                    class_name = data.__class__.__name__
                    if 'Candle' in class_name:
                        data_type = "candle"
                    elif 'Tick' in class_name:
                        data_type = "tick"
                    elif hasattr(data, 'columns'):
                        # Check if it has OHLC columns (candle data) - support multiple languages
                        ohlc_columns = [
                            # English
                            'open',
                            'high',
                            'low',
                            'close',
                            # Portuguese
                            'abertura',
                            'maxima',
                            'minima',
                            'fechamento',
                            # Spanish
                            'apertura',
                            'maximo',
                            'minimo',
                            'cierre',
                            # French
                            'ouverture',
                            'haut',
                            'bas',
                            'fermeture',
                        ]
                        df_columns_lower = [col.lower() for col in data.columns]
                        has_ohlc = any(col in ohlc_columns for col in df_columns_lower)
                        data_type = "candle" if has_ohlc else "tick"

                stats_text.append(f"\nSource: {source_id}")
                stats_text.append("-" * 30)
                stats_text.append(f"Data Type: {data_type}")

                if hasattr(data, 'symbol'):
                    stats_text.append(f"Symbol: {data.symbol}")
                if hasattr(data, 'timeframe'):
                    stats_text.append(f"Timeframe: {data.timeframe}")

                # Handle wrapped data objects (CandleData/TickData)
                if hasattr(data, 'df') and data.df is not None:
                    df = data.df
                elif hasattr(data, 'data') and data.data is not None:
                    df = data.data
                else:
                    df = data

                if hasattr(df, 'columns'):
                    stats_text.append(f"Rows: {len(df)}")
                    stats_text.append(f"Columns: {list(df.columns)}")

                    if hasattr(df.index, 'min'):
                        stats_text.append(
                            f"Date Range: {df.index.min()} to {df.index.max()}"
                        )

                    stats_text.append(f"Missing Values: {df.isnull().sum().sum()}")

        self.stats_text.setPlainText("\n".join(stats_text))
