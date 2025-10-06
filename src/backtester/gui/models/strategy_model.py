"""
Strategy Model for Backtester GUI

This module contains the data model for managing trading strategies,
including signal composition, parameter configuration, and validation.
"""

from typing import Dict, List, Optional, Any, Union
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass, field
from enum import Enum

from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeOrder


class SignalType(Enum):
    """Enumeration of available signal types."""
    RSI = "rsi"
    MACD = "macd"
    MOVING_AVERAGE = "moving_average"
    BOLLINGER_BANDS = "bollinger_bands"
    STOCHASTIC = "stochastic"
    CUSTOM = "custom"


class SignalRole(Enum):
    """Enumeration of signal roles in strategy composition."""
    ENTRY = "entry"
    EXIT = "exit"
    FILTER = "filter"
    CONFIRMATION = "confirmation"


@dataclass
class SignalParameter:
    """Data class for signal parameters."""
    name: str
    value: Any
    parameter_type: str  # 'int', 'float', 'str', 'bool', 'list'
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    options: Optional[List[str]] = None
    description: str = ""
    required: bool = True


@dataclass
class SignalConfig:
    """Data class for signal configuration."""
    signal_id: str
    signal_type: SignalType
    role: SignalRole
    parameters: Dict[str, SignalParameter] = field(default_factory=dict)
    enabled: bool = True
    weight: float = 1.0
    description: str = ""


@dataclass
class StrategyConfig:
    """Data class for complete strategy configuration."""
    strategy_id: str
    name: str
    description: str
    signals: List[SignalConfig] = field(default_factory=list)
    combiners: List[str] = field(default_factory=list)  # Signal combination logic
    created_at: str = ""
    modified_at: str = ""


class StrategyModel(QObject):
    """
    Data model for managing trading strategies in the GUI.
    
    This model handles:
    - Signal composition and configuration
    - Parameter validation and management
    - Strategy serialization and deserialization
    - Integration with the backtester engine
    """
    
    # Signals
    strategy_changed = Signal()
    signal_added = Signal(str)  # signal_id
    signal_removed = Signal(str)  # signal_id
    signal_updated = Signal(str)  # signal_id
    validation_changed = Signal(bool)  # is_valid
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_strategy: Optional[StrategyConfig] = None
        self._available_signals: Dict[SignalType, Dict[str, Any]] = self._initialize_signal_library()
        self._validation_errors: List[str] = []
        
    def _initialize_signal_library(self) -> Dict[SignalType, Dict[str, Any]]:
        """Initialize the library of available signals with their parameters."""
        return {
            SignalType.RSI: {
                "name": "Relative Strength Index",
                "description": "Momentum oscillator that measures the speed and magnitude of price changes",
                "parameters": {
                    "period": SignalParameter(
                        name="period",
                        value=14,
                        parameter_type="int",
                        min_value=1,
                        max_value=100,
                        description="Number of periods for RSI calculation"
                    ),
                    "overbought": SignalParameter(
                        name="overbought",
                        value=70,
                        parameter_type="float",
                        min_value=50,
                        max_value=100,
                        description="Overbought threshold"
                    ),
                    "oversold": SignalParameter(
                        name="oversold",
                        value=30,
                        parameter_type="float",
                        min_value=0,
                        max_value=50,
                        description="Oversold threshold"
                    )
                }
            },
            SignalType.MACD: {
                "name": "Moving Average Convergence Divergence",
                "description": "Trend-following momentum indicator",
                "parameters": {
                    "fast_period": SignalParameter(
                        name="fast_period",
                        value=12,
                        parameter_type="int",
                        min_value=1,
                        max_value=50,
                        description="Fast EMA period"
                    ),
                    "slow_period": SignalParameter(
                        name="slow_period",
                        value=26,
                        parameter_type="int",
                        min_value=1,
                        max_value=100,
                        description="Slow EMA period"
                    ),
                    "signal_period": SignalParameter(
                        name="signal_period",
                        value=9,
                        parameter_type="int",
                        min_value=1,
                        max_value=50,
                        description="Signal line EMA period"
                    )
                }
            },
            SignalType.MOVING_AVERAGE: {
                "name": "Moving Average",
                "description": "Simple or exponential moving average",
                "parameters": {
                    "period": SignalParameter(
                        name="period",
                        value=20,
                        parameter_type="int",
                        min_value=1,
                        max_value=200,
                        description="Moving average period"
                    ),
                    "ma_type": SignalParameter(
                        name="ma_type",
                        value="SMA",
                        parameter_type="str",
                        options=["SMA", "EMA", "WMA", "DEMA", "TEMA"],
                        description="Type of moving average"
                    )
                }
            },
            SignalType.BOLLINGER_BANDS: {
                "name": "Bollinger Bands",
                "description": "Volatility indicator with upper and lower bands",
                "parameters": {
                    "period": SignalParameter(
                        name="period",
                        value=20,
                        parameter_type="int",
                        min_value=1,
                        max_value=100,
                        description="Moving average period"
                    ),
                    "std_dev": SignalParameter(
                        name="std_dev",
                        value=2.0,
                        parameter_type="float",
                        min_value=0.1,
                        max_value=5.0,
                        description="Standard deviation multiplier"
                    )
                }
            },
            SignalType.STOCHASTIC: {
                "name": "Stochastic Oscillator",
                "description": "Momentum indicator comparing closing price to price range",
                "parameters": {
                    "k_period": SignalParameter(
                        name="k_period",
                        value=14,
                        parameter_type="int",
                        min_value=1,
                        max_value=50,
                        description="%K period"
                    ),
                    "d_period": SignalParameter(
                        name="d_period",
                        value=3,
                        parameter_type="int",
                        min_value=1,
                        max_value=20,
                        description="%D period"
                    ),
                    "overbought": SignalParameter(
                        name="overbought",
                        value=80,
                        parameter_type="float",
                        min_value=50,
                        max_value=100,
                        description="Overbought threshold"
                    ),
                    "oversold": SignalParameter(
                        name="oversold",
                        value=20,
                        parameter_type="float",
                        min_value=0,
                        max_value=50,
                        description="Oversold threshold"
                    )
                }
            }
        }
    
    def create_strategy(self, name: str, description: str = "") -> str:
        """Create a new strategy."""
        import uuid
        from datetime import datetime
        
        strategy_id = str(uuid.uuid4())
        self._current_strategy = StrategyConfig(
            strategy_id=strategy_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
        
        self.strategy_changed.emit()
        return strategy_id
    
    def clear_strategy(self):
        """Clear the current strategy."""
        self._current_strategy = None
        self._validation_errors.clear()
        self.strategy_changed.emit()
        self.validation_changed.emit(True)
    
    def has_strategy(self) -> bool:
        """Check if a strategy is currently loaded."""
        return self._current_strategy is not None
    
    def get_strategy_config(self) -> Optional[StrategyConfig]:
        """Get the current strategy configuration."""
        return self._current_strategy
    
    def get_strategy(self) -> Optional[TradingStrategy]:
        """Get the compiled strategy object for backtesting."""
        if not self._current_strategy:
            return None
            
        # TODO: Implement strategy compilation from configuration
        # This would convert the StrategyConfig into a TradingStrategy instance
        # For now, return a placeholder strategy to allow testing
        from src.strategies.composite import CompositeStrategy
        from src.strategies.signals import MaCrossoverSignal
        
        # Create a simple strategy for testing
        try:
            # This is a placeholder - in a real implementation, you would
            # convert the StrategyConfig into actual signal objects
            strategy = CompositeStrategy()
            return strategy
        except Exception as e:
            print(f"Error creating strategy: {e}")
            return None
    
    def add_signal(self, signal_type: SignalType, role: SignalRole, **kwargs) -> str:
        """Add a signal to the current strategy."""
        if not self._current_strategy:
            raise ValueError("No strategy loaded")
            
        import uuid
        signal_id = str(uuid.uuid4())
        
        # Get signal template
        signal_template = self._available_signals.get(signal_type)
        if not signal_template:
            raise ValueError(f"Unknown signal type: {signal_type}")
        
        # Create signal configuration
        signal_config = SignalConfig(
            signal_id=signal_id,
            signal_type=signal_type,
            role=role,
            parameters=signal_template["parameters"].copy(),
            description=signal_template["description"]
        )
        
        # Update parameters with provided values
        for param_name, param_value in kwargs.items():
            if param_name in signal_config.parameters:
                signal_config.parameters[param_name].value = param_value
        
        # Add new signals at the beginning of the list so they appear first
        self._current_strategy.signals.insert(0, signal_config)
        self._update_modified_time()
        self.signal_added.emit(signal_id)
        self.strategy_changed.emit()
        
        return signal_id
    
    def remove_signal(self, signal_id: str) -> bool:
        """Remove a signal from the current strategy."""
        if not self._current_strategy:
            return False
            
        for i, signal in enumerate(self._current_strategy.signals):
            if signal.signal_id == signal_id:
                del self._current_strategy.signals[i]
                self._update_modified_time()
                self.signal_removed.emit(signal_id)
                self.strategy_changed.emit()
                return True
                
        return False
    
    def update_signal_parameter(self, signal_id: str, parameter_name: str, value: Any) -> bool:
        """Update a signal parameter value."""
        if not self._current_strategy:
            return False
            
        for signal in self._current_strategy.signals:
            if signal.signal_id == signal_id:
                if parameter_name in signal.parameters:
                    signal.parameters[parameter_name].value = value
                    self._update_modified_time()
                    self.signal_updated.emit(signal_id)
                    self.strategy_changed.emit()
                    return True
                    
        return False
    
    def get_signal(self, signal_id: str) -> Optional[SignalConfig]:
        """Get a signal configuration by ID."""
        if not self._current_strategy:
            return None
            
        for signal in self._current_strategy.signals:
            if signal.signal_id == signal_id:
                return signal
                
        return None
    
    def get_available_signals(self) -> Dict[SignalType, Dict[str, Any]]:
        """Get the library of available signals."""
        return self._available_signals
    
    def validate_strategy(self) -> bool:
        """Validate the current strategy configuration."""
        self._validation_errors.clear()
        
        if not self._current_strategy:
            self._validation_errors.append("No strategy loaded")
            self.validation_changed.emit(False)
            return False
        
        # Check if strategy has signals
        if not self._current_strategy.signals:
            self._validation_errors.append("Strategy must have at least one signal")
        
        # Check if strategy has entry signals
        entry_signals = [s for s in self._current_strategy.signals if s.role == SignalRole.ENTRY]
        if not entry_signals:
            self._validation_errors.append("Strategy must have at least one entry signal")
        
        # Validate individual signals
        for signal in self._current_strategy.signals:
            self._validate_signal(signal)
        
        is_valid = len(self._validation_errors) == 0
        self.validation_changed.emit(is_valid)
        return is_valid
    
    def _validate_signal(self, signal: SignalConfig):
        """Validate a single signal configuration."""
        for param_name, param in signal.parameters.items():
            if param.required and param.value is None:
                self._validation_errors.append(
                    f"Signal {signal.signal_id}: Required parameter '{param_name}' is missing"
                )
                continue
                
            # Type validation
            if param.value is not None:
                if param.parameter_type == "int" and not isinstance(param.value, int):
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be an integer"
                    )
                elif param.parameter_type == "float" and not isinstance(param.value, (int, float)):
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be a number"
                    )
                elif param.parameter_type == "str" and not isinstance(param.value, str):
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be a string"
                    )
                elif param.parameter_type == "bool" and not isinstance(param.value, bool):
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be a boolean"
                    )
            
            # Range validation
            if param.value is not None and param.parameter_type in ["int", "float"]:
                if param.min_value is not None and param.value < param.min_value:
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be >= {param.min_value}"
                    )
                if param.max_value is not None and param.value > param.max_value:
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be <= {param.max_value}"
                    )
            
            # Options validation
            if param.options and param.value not in param.options:
                self._validation_errors.append(
                    f"Signal {signal.signal_id}: Parameter '{param_name}' must be one of {param.options}"
                )
    
    def get_validation_errors(self) -> List[str]:
        """Get the current validation errors."""
        return self._validation_errors.copy()
    
    def _update_modified_time(self):
        """Update the modified timestamp of the current strategy."""
        if self._current_strategy:
            from datetime import datetime
            self._current_strategy.modified_at = datetime.now().isoformat()
    
    def export_strategy(self, file_path: str) -> bool:
        """Export the current strategy to a file."""
        if not self._current_strategy:
            return False
            
        try:
            import json
            from datetime import datetime
            
            # Convert to serializable format
            strategy_data = {
                "strategy_id": self._current_strategy.strategy_id,
                "name": self._current_strategy.name,
                "description": self._current_strategy.description,
                "signals": [
                    {
                        "signal_id": signal.signal_id,
                        "signal_type": signal.signal_type.value,
                        "role": signal.role.value,
                        "parameters": {
                            name: {
                                "value": param.value,
                                "parameter_type": param.parameter_type,
                                "min_value": param.min_value,
                                "max_value": param.max_value,
                                "options": param.options,
                                "description": param.description,
                                "required": param.required
                            }
                            for name, param in signal.parameters.items()
                        },
                        "enabled": signal.enabled,
                        "weight": signal.weight,
                        "description": signal.description
                    }
                    for signal in self._current_strategy.signals
                ],
                "combiners": self._current_strategy.combiners,
                "created_at": self._current_strategy.created_at,
                "modified_at": self._current_strategy.modified_at
            }
            
            with open(file_path, 'w') as f:
                json.dump(strategy_data, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error exporting strategy: {e}")
            return False
    
    def import_strategy(self, file_path: str) -> bool:
        """Import a strategy from a file."""
        try:
            import json
            
            with open(file_path, 'r') as f:
                strategy_data = json.load(f)
            
            # Create strategy configuration
            self._current_strategy = StrategyConfig(
                strategy_id=strategy_data["strategy_id"],
                name=strategy_data["name"],
                description=strategy_data["description"],
                combiners=strategy_data.get("combiners", []),
                created_at=strategy_data.get("created_at", ""),
                modified_at=strategy_data.get("modified_at", "")
            )
            
            # Load signals
            for signal_data in strategy_data.get("signals", []):
                signal_config = SignalConfig(
                    signal_id=signal_data["signal_id"],
                    signal_type=SignalType(signal_data["signal_type"]),
                    role=SignalRole(signal_data["role"]),
                    enabled=signal_data.get("enabled", True),
                    weight=signal_data.get("weight", 1.0),
                    description=signal_data.get("description", "")
                )
                
                # Load parameters
                for param_name, param_data in signal_data.get("parameters", {}).items():
                    signal_config.parameters[param_name] = SignalParameter(
                        name=param_name,
                        value=param_data["value"],
                        parameter_type=param_data["parameter_type"],
                        min_value=param_data.get("min_value"),
                        max_value=param_data.get("max_value"),
                        options=param_data.get("options"),
                        description=param_data.get("description", ""),
                        required=param_data.get("required", True)
                    )
                
                # Add imported signals at the beginning to maintain order
                self._current_strategy.signals.insert(0, signal_config)
            
            self.strategy_changed.emit()
            return True
            
        except Exception as e:
            print(f"Error importing strategy: {e}")
            return False
