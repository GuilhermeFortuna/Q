# Backtester GUI API Reference

Quick reference for the Backtester GUI classes, methods, and signals.

## Table of Contents

1. [Main Window](#main-window)
2. [Widgets](#widgets)
3. [Controllers](#controllers)
4. [Models](#models)
5. [Dialogs](#dialogs)
6. [Signals & Slots](#signals--slots)
7. [Data Structures](#data-structures)

## Main Window

### BacktesterMainWindow

Main application window providing tabbed interface for all backtesting workflows.

```python
from src.backtester.gui.main_window import BacktesterMainWindow
```

#### Constructor
```python
BacktesterMainWindow(parent: Optional[QWidget] = None)
```

#### Key Methods
- `show()` - Display the main window
- `close()` - Close the application
- `get_current_tab()` - Get currently active tab index
- `set_current_tab(index: int)` - Switch to specified tab

#### Signals
- `tab_changed(int)` - Emitted when active tab changes
- `application_closing()` - Emitted before application closes

## Widgets

### StrategyBuilderWidget

Visual interface for composing trading strategies.

```python
from src.backtester.gui.widgets.strategy_builder import StrategyBuilderWidget
```

#### Constructor
```python
StrategyBuilderWidget(strategy_model: StrategyModel, 
                     strategy_controller: StrategyController, 
                     parent: Optional[QWidget] = None)
```

#### Key Methods
- `add_signal(signal_type: str) -> str` - Add signal to strategy, returns signal_id
- `remove_signal(signal_id: str)` - Remove signal from strategy
- `update_signal_parameters(signal_id: str, params: dict)` - Update signal parameters
- `validate_strategy() -> bool` - Validate current strategy configuration
- `get_strategy_config() -> dict` - Get complete strategy configuration
- `load_strategy(config: dict)` - Load strategy from configuration
- `save_strategy() -> dict` - Save current strategy configuration

#### Signals
- `signal_added(str)` - signal_id
- `signal_removed(str)` - signal_id
- `signal_updated(str, dict)` - signal_id, parameters
- `strategy_validated(bool, str)` - is_valid, error_message
- `strategy_saved(dict)` - strategy_config

### DataConfigWidget

Interface for loading and configuring market data.

```python
from src.backtester.gui.widgets.data_config import DataConfigWidget
```

#### Constructor
```python
DataConfigWidget(backtest_model: BacktestModel, parent: Optional[QWidget] = None)
```

#### Key Methods
- `add_data_source(source_type: str, config: dict) -> str` - Add data source, returns source_id
- `remove_data_source(source_id: str)` - Remove data source
- `load_data(source_id: str) -> bool` - Load data from source
- `validate_data(source_id: str) -> bool` - Validate loaded data
- `get_data_summary(source_id: str) -> dict` - Get data statistics
- `export_data(source_id: str, path: str)` - Export data to file

#### Signals
- `data_source_added(str)` - source_id
- `data_source_removed(str)` - source_id
- `data_loaded(str, bool)` - source_id, success
- `data_validated(str, bool, str)` - source_id, is_valid, error_message

### BacktestConfigWidget

Configuration interface for backtest parameters.

```python
from src.backtester.gui.widgets.backtest_config import BacktestConfigWidget
```

#### Constructor
```python
BacktestConfigWidget(backtest_model: BacktestModel, parent: Optional[QWidget] = None)
```

#### Key Methods
- `set_trading_costs(point_value: float, cost_per_trade: float)` - Set trading costs
- `set_risk_parameters(max_trades: int, max_drawdown: float)` - Set risk parameters
- `set_execution_settings(slippage: float, order_type: str)` - Set execution settings
- `validate_configuration() -> bool` - Validate current configuration
- `get_configuration() -> BacktestParameters` - Get backtest parameters
- `load_configuration(config: BacktestParameters)` - Load configuration

#### Signals
- `configuration_changed(dict)` - configuration
- `validation_result(bool, str)` - is_valid, error_message

### ExecutionMonitorWidget

Real-time monitoring interface for backtest execution.

```python
from src.backtester.gui.widgets.execution_monitor import ExecutionMonitorWidget
```

#### Constructor
```python
ExecutionMonitorWidget(execution_controller: ExecutionController, 
                      parent: Optional[QWidget] = None)
```

#### Key Methods
- `start_backtest(strategy: TradingStrategy, data: dict, config: BacktestParameters)` - Start backtest
- `stop_backtest()` - Stop running backtest
- `get_progress() -> int` - Get current progress percentage
- `get_metrics() -> dict` - Get current performance metrics
- `clear_results()` - Clear previous results
- `export_results(path: str)` - Export results to file

#### Signals
- `backtest_started()` - Emitted when backtest starts
- `backtest_finished(object)` - TradeRegistry results
- `backtest_error(str)` - error_message
- `progress_updated(int)` - progress_percentage
- `metrics_updated(dict)` - current_metrics

### SignalLibraryWidget

Panel displaying available trading signals.

```python
from src.backtester.gui.widgets.signal_library import SignalLibraryWidget
```

#### Constructor
```python
SignalLibraryWidget(parent: Optional[QWidget] = None)
```

#### Key Methods
- `get_available_signals() -> dict` - Get all available signals
- `get_signal_info(signal_type: str) -> dict` - Get signal information
- `filter_signals(category: str)` - Filter signals by category
- `search_signals(query: str)` - Search signals by name/description

#### Signals
- `signal_selected(str)` - signal_type
- `signal_double_clicked(str)` - signal_type

## Controllers

### StrategyController

Business logic controller for strategy management.

```python
from src.backtester.gui.controllers.strategy_controller import StrategyController
```

#### Constructor
```python
StrategyController(strategy_model: StrategyModel)
```

#### Key Methods
- `create_strategy(name: str) -> str` - Create new strategy, returns strategy_id
- `add_signal_to_strategy(strategy_id: str, signal_type: str) -> str` - Add signal, returns signal_id
- `remove_signal_from_strategy(strategy_id: str, signal_id: str)` - Remove signal
- `update_signal_parameters(strategy_id: str, signal_id: str, params: dict)` - Update parameters
- `validate_strategy(strategy_id: str) -> tuple[bool, str]` - Validate strategy
- `save_strategy(strategy_id: str, name: str)` - Save strategy
- `load_strategy(strategy_id: str) -> dict` - Load strategy configuration

### ExecutionController

Controller for backtest execution and monitoring.

```python
from src.backtester.gui.controllers.execution_controller import ExecutionController
```

#### Constructor
```python
ExecutionController(backtest_model: BacktestModel)
```

#### Key Methods
- `run_backtest(strategy: TradingStrategy, data: dict, config: BacktestParameters) -> TradeRegistry` - Execute backtest
- `stop_backtest()` - Stop running backtest
- `get_execution_status() -> str` - Get current execution status
- `get_progress() -> int` - Get execution progress
- `get_metrics() -> dict` - Get current performance metrics

#### Signals
- `execution_started()` - Emitted when execution starts
- `execution_finished(object)` - TradeRegistry results
- `execution_error(str)` - error_message
- `progress_updated(int)` - progress_percentage

## Models

### StrategyModel

Data model for strategy configuration and management.

```python
from src.backtester.gui.models.strategy_model import StrategyModel
```

#### Constructor
```python
StrategyModel()
```

#### Key Methods
- `add_strategy(strategy_id: str, config: dict)` - Add strategy configuration
- `remove_strategy(strategy_id: str)` - Remove strategy
- `get_strategy(strategy_id: str) -> dict` - Get strategy configuration
- `update_strategy(strategy_id: str, config: dict)` - Update strategy
- `list_strategies() -> list` - Get list of strategy IDs
- `validate_strategy(strategy_id: str) -> tuple[bool, str]` - Validate strategy

#### Properties
- `strategies: Dict[str, dict]` - Dictionary of strategy configurations
- `current_strategy: Optional[str]` - Currently selected strategy ID

### BacktestModel

Data model for backtest configuration and data sources.

```python
from src.backtester.gui.models.backtest_model import BacktestModel
```

#### Constructor
```python
BacktestModel()
```

#### Key Methods
- `add_data_source(source_id: str, config: DataSourceConfig)` - Add data source
- `remove_data_source(source_id: str)` - Remove data source
- `get_data_source(source_id: str) -> DataSourceConfig` - Get data source config
- `load_data(source_id: str) -> bool` - Load data from source
- `get_loaded_data(source_id: str) -> Optional[DataFrame]` - Get loaded data
- `set_backtest_parameters(params: BacktestParameters)` - Set backtest parameters
- `get_backtest_parameters() -> BacktestParameters` - Get backtest parameters

#### Properties
- `data_sources: Dict[str, DataSourceConfig]` - Dictionary of data source configurations
- `loaded_data: Dict[str, DataFrame]` - Dictionary of loaded data
- `backtest_parameters: Optional[BacktestParameters]` - Current backtest parameters

## Dialogs

### ParameterEditDialog

Dialog for editing signal parameters.

```python
from src.backtester.gui.dialogs.parameter_edit import ParameterEditDialog
```

#### Constructor
```python
ParameterEditDialog(signal_type: str, 
                   current_params: dict, 
                   parent: Optional[QWidget] = None)
```

#### Key Methods
- `get_parameters() -> dict` - Get edited parameters
- `set_parameters(params: dict)` - Set initial parameters
- `validate_parameters() -> bool` - Validate current parameters
- `reset_to_defaults()` - Reset parameters to defaults

#### Signals
- `parameters_changed(dict)` - new_parameters
- `parameters_accepted(dict)` - accepted_parameters
- `parameters_cancelled()` - Emitted when dialog is cancelled

### DataImportDialog

Wizard dialog for importing data sources.

```python
from src.backtester.gui.dialogs.data_import import DataImportDialog
```

#### Constructor
```python
DataImportDialog(parent: Optional[QWidget] = None)
```

#### Key Methods
- `get_import_config() -> dict` - Get import configuration
- `set_import_config(config: dict)` - Set import configuration
- `validate_import() -> bool` - Validate import configuration
- `preview_data() -> DataFrame` - Preview imported data

#### Signals
- `import_requested(dict)` - import_config
- `import_cancelled()` - Emitted when import is cancelled

### StrategySaveDialog

Dialog for saving strategy configurations.

```python
from src.backtester.gui.dialogs.strategy_save import StrategySaveDialog
```

#### Constructor
```python
StrategySaveDialog(strategy_config: dict, parent: Optional[QWidget] = None)
```

#### Key Methods
- `get_save_config() -> dict` - Get save configuration
- `set_strategy_name(name: str)` - Set strategy name
- `set_description(description: str)` - Set strategy description
- `validate_save() -> bool` - Validate save configuration

#### Signals
- `strategy_saved(dict)` - save_config
- `save_cancelled()` - Emitted when save is cancelled

## Signals & Slots

### Common Signal Patterns

#### Data Change Signals
```python
data_changed = Signal(dict)  # data
data_loaded = Signal(str, bool)  # source_id, success
data_validated = Signal(str, bool, str)  # source_id, is_valid, error_message
```

#### Configuration Signals
```python
configuration_changed = Signal(dict)  # configuration
parameters_updated = Signal(str, dict)  # signal_id, parameters
settings_changed = Signal(dict)  # settings
```

#### Execution Signals
```python
execution_started = Signal()
execution_finished = Signal(object)  # results
execution_error = Signal(str)  # error_message
progress_updated = Signal(int)  # progress_percentage
```

#### UI Interaction Signals
```python
button_clicked = Signal(str)  # button_name
item_selected = Signal(str)  # item_id
item_double_clicked = Signal(str)  # item_id
tab_changed = Signal(int)  # tab_index
```

### Signal Connection Examples

```python
# Connect widget signals
widget.data_changed.connect(self.on_data_changed)
widget.button_clicked.connect(self.on_button_clicked)

# Connect controller signals
controller.execution_finished.connect(self.on_execution_finished)
controller.progress_updated.connect(self.update_progress_bar)

# Connect model signals
model.strategy_updated.connect(self.refresh_strategy_display)
model.validation_result.connect(self.show_validation_message)
```

## Data Structures

### SignalConfig

Configuration for a trading signal.

```python
@dataclass
class SignalConfig:
    signal_id: str
    signal_type: str
    role: SignalRole  # ENTRY, EXIT, FILTER
    parameters: Dict[str, Any]
    enabled: bool = True
    position: Tuple[int, int] = (0, 0)  # x, y coordinates
```

### DataSourceConfig

Configuration for a data source.

```python
@dataclass
class DataSourceConfig:
    source_id: str
    source_type: str  # CSV, PARQUET, MT5, API
    symbol: str
    timeframe: str
    date_range: Tuple[datetime, datetime]
    parameters: Dict[str, Any]
    loaded: bool = False
    data_quality: Optional[Dict[str, Any]] = None
```

### BacktestParameters

Backtest execution parameters.

```python
@dataclass
class BacktestParameters:
    point_value: float
    cost_per_trade: float
    permit_swingtrade: bool = True
    entry_time_limit: Optional[datetime] = None
    exit_time_limit: Optional[datetime] = None
    max_trade_day: Optional[int] = None
    bypass_first_exit_check: bool = False
    slippage: float = 0.0
    order_type: str = "market"
```

### SignalRole (Enum)

Role of a signal in the strategy.

```python
class SignalRole(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    FILTER = "filter"
```

### ExecutionStatus (Enum)

Status of backtest execution.

```python
class ExecutionStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
```

---

*For user tutorials, see the [User Guide](USER_GUIDE.md). For development details, see the [Developer Guide](DEVELOPER_GUIDE.md).*




















