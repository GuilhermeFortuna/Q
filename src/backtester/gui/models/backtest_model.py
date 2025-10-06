"""
Backtest Model for Backtester GUI

This module contains the data models for managing backtest configuration,
data sources, and execution parameters.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass
from datetime import datetime, time, date

if TYPE_CHECKING:
    from src.backtester.engine import BacktestParameters


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""

    source_type: str  # "csv", "parquet", "mt5", "database"
    symbol: str
    timeframe: str
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    file_path: Optional[str] = None
    connection_string: Optional[str] = None
    table_name: Optional[str] = None


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""

    # Basic parameters
    point_value: float = 1.0
    cost_per_trade: float = 0.0
    initial_capital: Optional[float] = None

    # Risk management
    max_trade_day: Optional[int] = None
    permit_swingtrade: bool = False

    # Time limits
    entry_time_limit: Optional[time] = None
    exit_time_limit: Optional[time] = None

    # Execution settings
    slippage: float = 0.0
    bypass_first_exit_check: bool = False

    # Additional parameters
    commission: float = 0.0
    margin_requirement: float = 0.0
    max_position_size: Optional[float] = None
    stop_loss_pips: Optional[float] = None
    take_profit_pips: Optional[float] = None


class BacktestModel(QObject):
    """
    Data model for managing backtest configuration and data sources.

    This model handles:
    - Data source configuration and management
    - Backtest parameter configuration
    - Integration with the backtester engine
    - Data validation and preparation
    """

    # Signals
    data_sources_changed = Signal()
    backtest_config_changed = Signal()
    validation_changed = Signal(bool)  # is_valid
    data_loaded = Signal()  # data loaded signal
    data_loading_error = Signal(str)  # error message
    data_loading_progress = Signal(int)  # progress percentage
    config_changed = Signal()  # general config changed signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_sources: Dict[str, DataSourceConfig] = {}
        self._backtest_config = BacktestConfig()
        self._validation_errors: List[str] = []
        # Loaded data storage (source_id -> data object)
        self._loaded_data: Dict[str, Any] = {}

    def add_data_source(self, source_id: str, config: DataSourceConfig) -> bool:
        """Add a new data source configuration."""
        try:
            self._data_sources[source_id] = config
            self.data_sources_changed.emit()
            return True
        except Exception as e:
            print(f"Error adding data source: {e}")
            return False

    def remove_data_source(self, source_id: str) -> bool:
        """Remove a data source configuration."""
        if source_id in self._data_sources:
            del self._data_sources[source_id]
            self.data_sources_changed.emit()
            return True
        return False

    def get_data_source(self, source_id: str) -> Optional[DataSourceConfig]:
        """Get a data source configuration by ID."""
        return self._data_sources.get(source_id)

    def get_data_sources(self) -> Dict[str, DataSourceConfig]:
        """Get all data source configurations."""
        return self._data_sources.copy()

    def update_data_source(self, source_id: str, config: DataSourceConfig) -> bool:
        """Update an existing data source configuration."""
        if source_id in self._data_sources:
            self._data_sources[source_id] = config
            self.data_sources_changed.emit()
            return True
        return False

    def get_backtest_config(self) -> BacktestConfig:
        """Get the current backtest configuration."""
        return self._backtest_config

    def get_config(self) -> 'BacktestParameters':
        """Get the current backtest configuration as BacktestParameters."""
        from src.backtester.engine import BacktestParameters

        return BacktestParameters(
            point_value=self._backtest_config.point_value,
            cost_per_trade=self._backtest_config.cost_per_trade,
            permit_swingtrade=self._backtest_config.permit_swingtrade,
            entry_time_limit=self._backtest_config.entry_time_limit,
            exit_time_limit=self._backtest_config.exit_time_limit,
            max_trade_day=self._backtest_config.max_trade_day,
            bypass_first_exit_check=self._backtest_config.bypass_first_exit_check,
        )

    def update_backtest_config(self, config: BacktestConfig) -> None:
        """Update the backtest configuration."""
        self._backtest_config = config
        self.backtest_config_changed.emit()

    def validate_configuration(self) -> bool:
        """Validate the current configuration."""
        self._validation_errors.clear()

        # Validate data sources
        if not self._data_sources:
            self._validation_errors.append("At least one data source is required")

        for source_id, config in self._data_sources.items():
            self._validate_data_source(source_id, config)

        # Validate backtest config
        self._validate_backtest_config()

        is_valid = len(self._validation_errors) == 0
        self.validation_changed.emit(is_valid)
        return is_valid

    def _validate_data_source(self, source_id: str, config: DataSourceConfig):
        """Validate a data source configuration."""
        if not config.symbol:
            self._validation_errors.append(
                f"Data source {source_id}: Symbol is required"
            )

        if not config.timeframe:
            self._validation_errors.append(
                f"Data source {source_id}: Timeframe is required"
            )

        if config.source_type in ["csv", "parquet"] and not config.file_path:
            self._validation_errors.append(
                f"Data source {source_id}: File path is required for file-based sources"
            )

        if config.source_type == "database" and not config.connection_string:
            self._validation_errors.append(
                f"Data source {source_id}: Connection string is required for database sources"
            )

    def _validate_backtest_config(self):
        """Validate the backtest configuration."""
        if self._backtest_config.point_value <= 0:
            self._validation_errors.append("Point value must be greater than 0")

        if self._backtest_config.cost_per_trade < 0:
            self._validation_errors.append("Cost per trade cannot be negative")

        if (
            self._backtest_config.initial_capital is not None
            and self._backtest_config.initial_capital <= 0
        ):
            self._validation_errors.append("Initial capital must be greater than 0")

        if (
            self._backtest_config.max_trade_day is not None
            and self._backtest_config.max_trade_day <= 0
        ):
            self._validation_errors.append("Max trades per day must be greater than 0")

    def get_validation_errors(self) -> List[str]:
        """Get the current validation errors."""
        return self._validation_errors.copy()

    def get_data(self) -> Dict[str, Any]:
        """Get loaded data for all data sources in the format expected by the Engine."""
        # Transform data from source_id -> data_obj to data_type -> data_obj
        engine_data = {}
        
        for source_id, data_obj in self._loaded_data.items():
            # Determine data type based on the data object type
            if hasattr(data_obj, '__class__'):
                class_name = data_obj.__class__.__name__
                if 'Candle' in class_name:
                    engine_data['candle'] = data_obj
                elif 'Tick' in class_name:
                    engine_data['tick'] = data_obj
                else:
                    # Try to infer from the data object's attributes
                    if hasattr(data_obj, 'timeframe'):
                        engine_data['candle'] = data_obj
                    else:
                        engine_data['tick'] = data_obj
        
        return engine_data

    def has_data(self) -> bool:
        """Check if any data has been loaded."""
        # Return True if any data has been loaded into the model.
        return len(self._loaded_data) > 0

    def has_config(self) -> bool:
        """Check if the model has enough configuration to run a backtest.

        Returns True when there is at least one data source and basic backtest parameters
        are set (e.g., positive point value).
        """
        # Must have at least one data source
        if not self._data_sources:
            return False
        # Basic validation of backtest parameters
        if (
            self._backtest_config.point_value is None
            or self._backtest_config.point_value <= 0
        ):
            return False
        return True

    def get_ohlc_data(self) -> Optional[Any]:
        """Get OHLC data for visualization."""
        # Return the first loaded data source for visualization
        if self._loaded_data:
            return next(iter(self._loaded_data.values()), None)
        return None

    def store_loaded_data(self, source_id: str, data: Any) -> None:
        """Store loaded data object for a given data source and emit data_loaded."""
        try:
            self._loaded_data[source_id] = data
            # Notify listeners that data is available
            self.data_loaded.emit()
        except Exception as e:
            print(f"Error storing loaded data for {source_id}: {e}")

    def clear_loaded_data(self):
        """Clear previously loaded data."""
        self._loaded_data.clear()
        # Emit data_sources_changed to indicate a change in available data
        self.data_sources_changed.emit()

    def clear_data_sources(self):
        """Clear all data sources."""
        self._data_sources.clear()
        self.data_sources_changed.emit()

    def reset_backtest_config(self):
        """Reset backtest configuration to defaults."""
        self._backtest_config = BacktestConfig()
        self.backtest_config_changed.emit()

    def export_configuration(self, file_path: str) -> bool:
        """Export the current configuration to a file."""
        try:
            import json

            config_data = {
                "data_sources": {
                    source_id: {
                        "source_type": config.source_type,
                        "symbol": config.symbol,
                        "timeframe": config.timeframe,
                        "date_from": (
                            config.date_from.isoformat() if config.date_from else None
                        ),
                        "date_to": (
                            config.date_to.isoformat() if config.date_to else None
                        ),
                        "file_path": config.file_path,
                        "connection_string": config.connection_string,
                        "table_name": config.table_name,
                    }
                    for source_id, config in self._data_sources.items()
                },
                "backtest_config": {
                    "point_value": self._backtest_config.point_value,
                    "cost_per_trade": self._backtest_config.cost_per_trade,
                    "initial_capital": self._backtest_config.initial_capital,
                    "max_trade_day": self._backtest_config.max_trade_day,
                    "permit_swingtrade": self._backtest_config.permit_swingtrade,
                    "entry_time_limit": (
                        self._backtest_config.entry_time_limit.isoformat()
                        if self._backtest_config.entry_time_limit
                        else None
                    ),
                    "exit_time_limit": (
                        self._backtest_config.exit_time_limit.isoformat()
                        if self._backtest_config.exit_time_limit
                        else None
                    ),
                    "slippage": self._backtest_config.slippage,
                    "bypass_first_exit_check": self._backtest_config.bypass_first_exit_check,
                    "commission": self._backtest_config.commission,
                    "margin_requirement": self._backtest_config.margin_requirement,
                    "max_position_size": self._backtest_config.max_position_size,
                    "stop_loss_pips": self._backtest_config.stop_loss_pips,
                    "take_profit_pips": self._backtest_config.take_profit_pips,
                },
            }

            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def import_configuration(self, file_path: str) -> bool:
        """Import configuration from a file."""
        try:
            import json

            with open(file_path, 'r') as f:
                config_data = json.load(f)

            # Import data sources
            self._data_sources.clear()
            for source_id, source_data in config_data.get("data_sources", {}).items():
                config = DataSourceConfig(
                    source_type=source_data["source_type"],
                    symbol=source_data["symbol"],
                    timeframe=source_data["timeframe"],
                    date_from=(
                        datetime.fromisoformat(source_data["date_from"]).date()
                        if source_data.get("date_from")
                        else None
                    ),
                    date_to=(
                        datetime.fromisoformat(source_data["date_to"]).date()
                        if source_data.get("date_to")
                        else None
                    ),
                    file_path=source_data.get("file_path"),
                    connection_string=source_data.get("connection_string"),
                    table_name=source_data.get("table_name"),
                )
                self._data_sources[source_id] = config

            # Import backtest config
            backtest_data = config_data.get("backtest_config", {})
            self._backtest_config = BacktestConfig(
                point_value=backtest_data.get("point_value", 1.0),
                cost_per_trade=backtest_data.get("cost_per_trade", 0.0),
                initial_capital=backtest_data.get("initial_capital"),
                max_trade_day=backtest_data.get("max_trade_day"),
                permit_swingtrade=backtest_data.get("permit_swingtrade", False),
                entry_time_limit=(
                    time.fromisoformat(backtest_data["entry_time_limit"])
                    if backtest_data.get("entry_time_limit")
                    else None
                ),
                exit_time_limit=(
                    time.fromisoformat(backtest_data["exit_time_limit"])
                    if backtest_data.get("exit_time_limit")
                    else None
                ),
                slippage=backtest_data.get("slippage", 0.0),
                bypass_first_exit_check=backtest_data.get(
                    "bypass_first_exit_check", False
                ),
                commission=backtest_data.get("commission", 0.0),
                margin_requirement=backtest_data.get("margin_requirement", 0.0),
                max_position_size=backtest_data.get("max_position_size"),
                stop_loss_pips=backtest_data.get("stop_loss_pips"),
                take_profit_pips=backtest_data.get("take_profit_pips"),
            )

            self.data_sources_changed.emit()
            self.backtest_config_changed.emit()
            return True

        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False
