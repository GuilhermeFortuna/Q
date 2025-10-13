# Backtester GUI Developer Guide

A comprehensive guide for developers who want to extend, customize, or contribute to the Backtester GUI.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding Custom Signals](#adding-custom-signals)
3. [Creating Custom Widgets](#creating-custom-widgets)
4. [Extending Data Sources](#extending-data-sources)
5. [Theme Customization](#theme-customization)
6. [Testing Guidelines](#testing-guidelines)
7. [Integration Points](#integration-points)
8. [Performance Optimization](#performance-optimization)

## Architecture Overview

The Backtester GUI follows a clean MVC (Model-View-Controller) architecture with Qt's signal/slot mechanism for communication.

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Window (View)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Strategy  │  │     Data    │  │  Backtest   │        │
│  │   Builder   │  │   Config    │  │   Config    │        │
│  │  (Widget)   │  │  (Widget)   │  │  (Widget)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                Controllers (Business Logic)                │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Strategy      │  │   Execution     │                  │
│  │   Controller    │  │   Controller    │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                    Models (Data Layer)                     │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Strategy      │  │   Backtest      │                  │
│  │     Model       │  │     Model       │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### Models (`src/backtester/gui/models/`)
- **StrategyModel**: Manages strategy configuration, signals, and parameters
- **BacktestModel**: Handles backtest configuration, data sources, and execution settings

#### Controllers (`src/backtester/gui/controllers/`)
- **StrategyController**: Business logic for strategy building and validation
- **ExecutionController**: Manages backtest execution and progress monitoring

#### Views (`src/backtester/gui/widgets/`)
- **StrategyBuilderWidget**: Visual strategy composition interface
- **DataConfigWidget**: Data loading and configuration interface
- **BacktestConfigWidget**: Parameter configuration interface
- **ExecutionMonitorWidget**: Real-time execution monitoring

#### Dialogs (`src/backtester/gui/dialogs/`)
- **ParameterEditDialog**: Signal parameter editing
- **DataImportDialog**: Data source import wizard
- **StrategySaveDialog**: Strategy persistence

### Signal/Slot Communication

The GUI uses Qt's signal/slot mechanism for loose coupling:

```python
# Example: Strategy signal configuration
class StrategyBuilderWidget(QWidget):
    signal_added = Signal(str)  # signal_id
    signal_removed = Signal(str)  # signal_id
    signal_updated = Signal(str, dict)  # signal_id, config
    
    def add_signal(self, signal_type: str):
        # Emit signal when signal is added
        self.signal_added.emit(signal_id)
```

### Threading Model

- **Main Thread**: UI updates and user interactions
- **Execution Thread**: Backtest execution (prevents UI freezing)
- **Worker Threads**: Data loading and heavy computations

## Adding Custom Signals

### Step 1: Create Signal Class

Create a new signal class that inherits from the base signal interface:

```python
# src/strategies/signals/my_custom_signal.py
from typing import Dict, Any, Optional
import pandas as pd
from ..base import BaseSignal

class MyCustomSignal(BaseSignal):
    """Custom signal implementation example."""
    
    def __init__(self, 
                 parameter1: float = 14.0,
                 parameter2: str = "sma",
                 **kwargs):
        super().__init__(**kwargs)
        self.parameter1 = parameter1
        self.parameter2 = parameter2
        
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """Compute the signal values."""
        # Your signal calculation logic here
        result = data['close'].rolling(window=int(self.parameter1)).mean()
        return result
        
    def get_parameters(self) -> Dict[str, Any]:
        """Return signal parameters for GUI configuration."""
        return {
            'parameter1': {
                'type': 'float',
                'default': 14.0,
                'min': 1.0,
                'max': 100.0,
                'description': 'Period for calculation'
            },
            'parameter2': {
                'type': 'choice',
                'choices': ['sma', 'ema', 'wma'],
                'default': 'sma',
                'description': 'Moving average type'
            }
        }
```

### Step 2: Register Signal in GUI

Add your signal to the signal library:

```python
# src/backtester/gui/widgets/signal_library.py
from src.strategies.signals.my_custom_signal import MyCustomSignal

class SignalLibraryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_signal_catalog()
    
    def _setup_signal_catalog(self):
        """Setup the signal catalog with available signals."""
        self.signals = {
            'My Custom Signal': {
                'class': MyCustomSignal,
                'category': 'Custom',
                'description': 'Custom signal implementation',
                'icon': 'custom_signal_icon.png'
            },
            # ... other signals
        }
```

### Step 3: Add GUI Configuration

Create a parameter editor for your signal:

```python
# src/backtester/gui/dialogs/parameter_edit.py
class ParameterEditDialog(QDialog):
    def _create_parameter_widgets(self, signal_config: dict):
        """Create parameter input widgets based on signal configuration."""
        for param_name, param_config in signal_config.items():
            if param_config['type'] == 'float':
                widget = QDoubleSpinBox()
                widget.setRange(param_config['min'], param_config['max'])
                widget.setValue(param_config['default'])
            elif param_config['type'] == 'choice':
                widget = QComboBox()
                widget.addItems(param_config['choices'])
                widget.setCurrentText(param_config['default'])
            # ... other parameter types
```

### Step 4: Integration Testing

Test your signal integration:

```python
# tests/strategies/signals/test_my_custom_signal.py
import pytest
import pandas as pd
from src.strategies.signals.my_custom_signal import MyCustomSignal

def test_my_custom_signal():
    """Test custom signal functionality."""
    # Create test data
    data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    })
    
    # Create signal instance
    signal = MyCustomSignal(parameter1=5.0, parameter2='sma')
    
    # Compute signal
    result = signal.compute(data)
    
    # Verify results
    assert len(result) == len(data)
    assert not result.isna().all()
```

## Creating Custom Widgets

### Widget Base Class

All custom widgets should inherit from the base widget class:

```python
# src/backtester/gui/widgets/base_widget.py
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

class BaseWidget(QWidget):
    """Base class for all GUI widgets."""
    
    # Common signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)
    status_updated = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()
        self._connect_signals()
    
    def _setup_ui(self):
        """Override to setup widget UI."""
        pass
    
    def _apply_styling(self):
        """Override to apply custom styling."""
        pass
    
    def _connect_signals(self):
        """Override to connect internal signals."""
        pass
```

### Custom Widget Example

```python
# src/backtester/gui/widgets/my_custom_widget.py
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton
from .base_widget import BaseWidget

class MyCustomWidget(BaseWidget):
    """Example custom widget for demonstration."""
    
    # Custom signals
    custom_action_triggered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
    
    def _setup_ui(self):
        """Setup the custom widget UI."""
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel("My Custom Widget")
        layout.addWidget(self.title_label)
        
        # Action button
        self.action_button = QPushButton("Perform Action")
        self.action_button.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_button)
    
    def _apply_styling(self):
        """Apply custom styling."""
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
    
    def _connect_signals(self):
        """Connect internal signals."""
        pass
    
    def _on_action_clicked(self):
        """Handle action button click."""
        self.custom_action_triggered.emit("action_performed")
        self.status_updated.emit("Action completed")
    
    def set_data(self, data: Dict[str, Any]):
        """Set widget data."""
        self.data = data
        self.data_changed.emit(data)
    
    def get_data(self) -> Dict[str, Any]:
        """Get widget data."""
        return self.data
```

### Widget Integration

To integrate your custom widget into the main application:

```python
# src/backtester/gui/main_window.py
from .widgets.my_custom_widget import MyCustomWidget

class BacktesterMainWindow(QMainWindow):
    def _create_tabs(self):
        """Create the main tab widgets."""
        # ... existing tabs
        
        # Add custom widget tab
        self.custom_widget = MyCustomWidget()
        self.tab_widget.addTab(self.custom_widget, "My Custom Tab")
        
        # Connect custom signals
        self.custom_widget.custom_action_triggered.connect(self._on_custom_action)
    
    def _on_custom_action(self, action: str):
        """Handle custom widget actions."""
        print(f"Custom action triggered: {action}")
```

## Extending Data Sources

### Data Source Interface

Create a new data source by implementing the data source interface:

```python
# src/backtester/gui/models/data_source_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class DataSourceInterface(ABC):
    """Interface for data source implementations."""
    
    @abstractmethod
    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data from the source."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate data source configuration."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """Get supported data formats."""
        pass
```

### Custom Data Source Implementation

```python
# src/backtester/gui/models/custom_data_source.py
from typing import Dict, Any, Optional
import pandas as pd
import requests
from .data_source_interface import DataSourceInterface

class CustomAPIDataSource(DataSourceInterface):
    """Custom data source for API-based data loading."""
    
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.api_key = None
    
    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data from custom API."""
        symbol = config.get('symbol')
        timeframe = config.get('timeframe')
        start_date = config.get('start_date')
        end_date = config.get('end_date')
        
        # Make API request
        url = f"{self.base_url}/data"
        params = {
            'symbol': symbol,
            'timeframe': timeframe,
            'start': start_date,
            'end': end_date,
            'api_key': self.api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Convert to DataFrame
        data = response.json()
        df = pd.DataFrame(data)
        
        # Format data
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        return df
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate API configuration."""
        required_fields = ['symbol', 'timeframe', 'start_date', 'end_date']
        return all(field in config for field in required_fields)
    
    def get_supported_formats(self) -> list:
        """Get supported data formats."""
        return ['OHLCV', 'TICK']
```

### Data Source Registration

Register your data source in the data configuration widget:

```python
# src/backtester/gui/widgets/data_config.py
from .models.custom_data_source import CustomAPIDataSource

class DataConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_sources = {
            'CSV File': CSVDataSource(),
            'Parquet File': ParquetDataSource(),
            'MetaTrader 5': MT5DataSource(),
            'Custom API': CustomAPIDataSource(),  # Add your custom source
        }
```

## Theme Customization

### Theme System

The GUI uses a centralized theme system for consistent styling:

```python
# src/backtester/gui/theme.py
class Theme:
    """Centralized theme management."""
    
    # Color palette
    COLORS = {
        'background': '#1e1e1e',
        'surface': '#2d2d30',
        'primary': '#0078d4',
        'secondary': '#106ebe',
        'success': '#107c10',
        'warning': '#ff8c00',
        'error': '#d13438',
        'text': '#ffffff',
        'text_secondary': '#cccccc',
        'border': '#3e3e42',
    }
    
    # Typography
    FONTS = {
        'heading': 'Segoe UI, 14px, bold',
        'body': 'Segoe UI, 12px, normal',
        'caption': 'Segoe UI, 10px, normal',
    }
    
    # Spacing
    SPACING = {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
    }
```

### Custom Theme Implementation

```python
# src/backtester/gui/theme/custom_theme.py
from .theme import Theme

class CustomTheme(Theme):
    """Custom theme implementation."""
    
    COLORS = {
        **Theme.COLORS,
        'background': '#0a0a0a',  # Darker background
        'primary': '#00ff88',     # Green primary color
        'accent': '#ff6b35',      # Orange accent
    }
    
    def get_button_style(self, variant: str = 'primary') -> str:
        """Get button style for specific variant."""
        base_style = """
            QPushButton {
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
        """
        
        if variant == 'primary':
            return base_style + f"""
                background-color: {self.COLORS['primary']};
                color: {self.COLORS['background']};
            """
        elif variant == 'secondary':
            return base_style + f"""
                background-color: {self.COLORS['surface']};
                color: {self.COLORS['text']};
                border: 1px solid {self.COLORS['border']};
            """
        
        return base_style
```

### Applying Custom Themes

```python
# src/backtester/gui/main_window.py
from .theme.custom_theme import CustomTheme

class BacktesterMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = CustomTheme()  # Use custom theme
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply theme styling to the application."""
        self.setStyleSheet(self.theme.get_application_style())
```

## Testing Guidelines

### Unit Testing

Test individual components in isolation:

```python
# tests/backtester/gui/test_strategy_builder.py
import pytest
from PySide6.QtWidgets import QApplication
from src.backtester.gui.widgets.strategy_builder import StrategyBuilderWidget

@pytest.fixture
def app():
    """Create QApplication for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def strategy_builder(app):
    """Create StrategyBuilderWidget for testing."""
    return StrategyBuilderWidget()

def test_signal_addition(strategy_builder):
    """Test adding signals to strategy builder."""
    initial_count = strategy_builder.get_signal_count()
    
    strategy_builder.add_signal('RSI')
    
    assert strategy_builder.get_signal_count() == initial_count + 1

def test_signal_removal(strategy_builder):
    """Test removing signals from strategy builder."""
    strategy_builder.add_signal('RSI')
    signal_id = strategy_builder.get_signal_ids()[0]
    
    strategy_builder.remove_signal(signal_id)
    
    assert strategy_builder.get_signal_count() == 0
```

### Integration Testing

Test component interactions:

```python
# tests/backtester/gui/test_integration.py
import pytest
from PySide6.QtWidgets import QApplication
from src.backtester.gui.main_window import BacktesterMainWindow

@pytest.fixture
def main_window():
    """Create main window for integration testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    window = BacktesterMainWindow()
    return window

def test_strategy_data_integration(main_window):
    """Test integration between strategy builder and data config."""
    # Add data source
    main_window.data_config.add_data_source('CSV', {'path': 'test_data.csv'})
    
    # Build strategy
    main_window.strategy_builder.add_signal('RSI')
    
    # Verify integration
    assert main_window.strategy_builder.can_run_backtest()
    assert main_window.data_config.has_valid_data()
```

### UI Testing

Test user interactions:

```python
# tests/backtester/gui/test_ui_interactions.py
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from src.backtester.gui.widgets.strategy_builder import StrategyBuilderWidget

def test_button_clicks():
    """Test button click interactions."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    widget = StrategyBuilderWidget()
    
    # Test add signal button
    add_button = widget.findChild(QPushButton, "add_signal_button")
    QTest.mouseClick(add_button, Qt.LeftButton)
    
    # Verify signal was added
    assert widget.get_signal_count() > 0
```

## Integration Points

### Backtester Engine Integration

The GUI integrates with the core backtester engine:

```python
# src/backtester/gui/controllers/execution_controller.py
from ...engine import Engine, BacktestParameters
from ...strategy import TradingStrategy

class ExecutionController:
    def run_backtest(self, strategy: TradingStrategy, 
                    data: Dict[str, Any], 
                    config: BacktestParameters):
        """Execute backtest using the core engine."""
        engine = Engine(
            parameters=config,
            strategy=strategy,
            data=data
        )
        
        results = engine.run_backtest(display_progress=False)
        return results
```

### Data Module Integration

Integration with the data management system:

```python
# src/backtester/gui/widgets/data_config.py
from src.data import CandleData, TickData

class DataConfigWidget:
    def load_csv_data(self, path: str, symbol: str, timeframe: str):
        """Load CSV data using the data module."""
        candle_data = CandleData(symbol=symbol, timeframe=timeframe)
        candle_data.data = CandleData.import_from_csv(path)
        return candle_data
```

### Visualizer Integration

Results are automatically opened in the visualizer:

```python
# src/backtester/gui/controllers/execution_controller.py
from src.visualizer import open_results

class ExecutionController:
    def on_backtest_completed(self, results):
        """Handle backtest completion."""
        # Store results in bridge
        self.bridge.store_results(results)
        
        # Open in visualizer
        open_results(results)
```

## Performance Optimization

### Memory Management

- **Data Loading**: Load only necessary data ranges
- **Caching**: Cache calculated indicators
- **Cleanup**: Properly dispose of large objects

### UI Responsiveness

- **Threading**: Use worker threads for heavy operations
- **Progress Updates**: Provide real-time progress feedback
- **Async Operations**: Use async/await for I/O operations

### Calculation Optimization

- **Vectorization**: Use pandas/numpy vectorized operations
- **Lazy Loading**: Load data on demand
- **Batch Processing**: Process data in batches for large datasets

---

*For user-focused documentation, see the [User Guide](USER_GUIDE.md). For API details, see the [API Reference](API_REFERENCE.md).*




















