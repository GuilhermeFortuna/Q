"""
Strategy Model for Backtester GUI

This module contains the data model for managing trading strategies,
including signal composition, parameter configuration, and validation.
"""

import inspect
from typing import Dict, List, Optional, Any, Union
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass, field
from enum import Enum

from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeOrder
from src.strategies import TradingSignal


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
        # Cache of discovered signal classes for instantiation (must be before _initialize_signal_library)
        self._signal_classes: Dict[str, type] = {}
        self._available_signals: Dict[SignalType, Dict[str, Any]] = (
            self._initialize_signal_library()
        )
        self._validation_errors: List[str] = []

    def _initialize_signal_library(self) -> Dict[SignalType, Dict[str, Any]]:
        """
        Dynamically discover and initialize the library of available signals.

        This method scans the src/strategies/signals package, finds all TradingSignal
        subclasses, and extracts their metadata (name, description, parameters) from
        their class definition and __init__ signature.
        """
        import importlib
        import pkgutil
        from pathlib import Path

        signal_library = {}

        try:
            # Import the signals package
            import src.strategies.signals as signals_package
            from src.strategies.signals.base import TradingSignal

            # Get the package path
            package_path = Path(signals_package.__file__).parent

            # Iterate through all modules in the signals package
            for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
                if module_name == 'base' or module_name.startswith('_'):
                    continue

                try:
                    # Import the module
                    module = importlib.import_module(
                        f'src.strategies.signals.{module_name}'
                    )

                    # Find all TradingSignal subclasses in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            obj is not TradingSignal
                            and issubclass(obj, TradingSignal)
                            and obj.__module__ == module.__name__
                        ):

                            # Extract signal metadata
                            signal_info = self._extract_signal_metadata(obj)
                            if signal_info:
                                # Use class name as the key
                                signal_library[name] = signal_info
                                # Cache the class for later instantiation
                                self._signal_classes[name] = obj

                except Exception as e:
                    print(f"Error loading signal module {module_name}: {e}")
                    continue

            print(
                f"Discovered {len(signal_library)} signals: {list(signal_library.keys())}"
            )

        except Exception as e:
            print(f"Error initializing signal library: {e}")
            import traceback

            traceback.print_exc()

        return signal_library

    def _extract_signal_metadata(self, signal_class: type) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a signal class including name, description, and parameters.

        Parameters are extracted from the __init__ method signature using inspect.
        """
        from typing import get_type_hints

        try:
            # Get class name and docstring
            class_name = signal_class.__name__
            docstring = inspect.getdoc(signal_class) or "No description available"

            # Extract first line as name, rest as description
            doc_lines = docstring.split('\n', 1)
            name = doc_lines[0].strip()
            description = doc_lines[1].strip() if len(doc_lines) > 1 else name

            # Get __init__ signature
            sig = inspect.signature(signal_class.__init__)

            # Extract parameters
            parameters = {}
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'args', 'kwargs'):
                    continue

                # Get parameter metadata
                param_info = self._extract_parameter_metadata(param_name, param, sig)
                if param_info:
                    parameters[param_name] = param_info

            return {
                'name': name,
                'description': description,
                'class_name': class_name,
                'parameters': parameters,
            }

        except Exception as e:
            print(f"Error extracting metadata from {signal_class.__name__}: {e}")
            return None

    def _extract_parameter_metadata(
        self, param_name: str, param: inspect.Parameter, signature: inspect.Signature
    ) -> Optional[SignalParameter]:
        """Extract metadata for a single parameter from its signature."""
        import inspect

        # Get default value
        default_value = (
            param.default if param.default != inspect.Parameter.empty else None
        )

        # Infer parameter type from annotation or default value
        param_type = 'str'  # default
        if param.annotation != inspect.Parameter.empty:
            annotation = param.annotation
            # Handle Optional types
            if hasattr(annotation, '__origin__'):
                if annotation.__origin__ is Union:
                    # Get the first non-None type
                    args = [a for a in annotation.__args__ if a is not type(None)]
                    if args:
                        annotation = args[0]

            if annotation == int or annotation == 'int':
                param_type = 'int'
            elif annotation == float or annotation == 'float':
                param_type = 'float'
            elif annotation == bool or annotation == 'bool':
                param_type = 'bool'
            elif annotation == str or annotation == 'str':
                param_type = 'str'
        elif default_value is not None:
            # Infer from default value
            if isinstance(default_value, int):
                param_type = 'int'
            elif isinstance(default_value, float):
                param_type = 'float'
            elif isinstance(default_value, bool):
                param_type = 'bool'
            elif isinstance(default_value, str):
                param_type = 'str'

        # Set reasonable min/max values based on parameter name and type
        min_value = None
        max_value = None
        if param_type in ('int', 'float'):
            if 'period' in param_name.lower() or 'length' in param_name.lower():
                min_value = 1
                max_value = 500
            elif 'band' in param_name.lower() or 'threshold' in param_name.lower():
                min_value = 0
                max_value = 100
            elif 'std' in param_name.lower() or 'deviation' in param_name.lower():
                min_value = 0.1
                max_value = 10.0
            else:
                min_value = 0
                max_value = 1000

        # Check if parameter is required (no default value)
        required = param.default == inspect.Parameter.empty

        return SignalParameter(
            name=param_name,
            value=default_value,
            parameter_type=param_type,
            min_value=min_value,
            max_value=max_value,
            description=f"{param_name} parameter",
            required=required,
        )

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
            modified_at=datetime.now().isoformat(),
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

        # Check if strategy has any signals configured
        if (
            not self._current_strategy.signals
            or len(self._current_strategy.signals) == 0
        ):
            print("No signals configured in strategy")
            return None

        # Compile strategy from configuration
        try:
            from src.strategies.composite import CompositeStrategy

            # Convert SignalConfig objects to actual TradingSignal instances
            signal_instances = []
            for signal_config in self._current_strategy.signals:
                if not signal_config.enabled:
                    continue

                signal_instance = self._create_signal_instance(signal_config)
                if signal_instance:
                    signal_instances.append(signal_instance)

            if not signal_instances:
                print("No enabled signals to compile")
                return None

            # Create CompositeStrategy with compiled signals
            strategy = CompositeStrategy(
                signals=signal_instances, always_active=True  # Default to always active
            )

            return strategy

        except Exception as e:
            print(f"Error compiling strategy: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _create_signal_instance(
        self, signal_config: SignalConfig
    ) -> Optional[TradingSignal]:
        """
        Create a TradingSignal instance from a SignalConfig.

        This method dynamically instantiates the signal class using the cached
        signal classes and passes the configured parameters.
        """
        try:
            # Get the signal class name from the config
            # signal_type can be either a string (class name) or SignalType enum
            if isinstance(signal_config.signal_type, str):
                class_name = signal_config.signal_type
            else:
                # For backward compatibility with SignalType enum
                class_name = signal_config.signal_type.value

            # Get the signal class
            signal_class = self._signal_classes.get(class_name)
            if not signal_class:
                print(f"Signal class not found: {class_name}")
                return None

            # Build kwargs from parameters
            kwargs = {}
            for param_name, param in signal_config.parameters.items():
                if param.value is not None:
                    kwargs[param_name] = param.value

            # Instantiate the signal
            return signal_class(**kwargs)

        except Exception as e:
            print(f"Error creating signal instance: {e}")
            import traceback


            traceback.print_exc()
            return None

    def add_signal(self, signal_class_name: str, role: SignalRole, **kwargs) -> str:
        """
        Add a signal to the current strategy.

        Args:
            signal_class_name: The name of the signal class (e.g., 'RsiMeanReversionSignal')
            role: The role of the signal (ENTRY, EXIT, FILTER, CONFIRMATION)
            **kwargs: Optional parameter overrides

        Returns:
            The signal_id of the newly added signal
        """
        if not self._current_strategy:
            raise ValueError("No strategy loaded")

        import uuid

        signal_id = str(uuid.uuid4())

        # Get signal template
        signal_template = self._available_signals.get(signal_class_name)
        if not signal_template:
            raise ValueError(f"Unknown signal class: {signal_class_name}")

        # Create signal configuration
        signal_config = SignalConfig(
            signal_type=signal_class_name,  # Store class name as string
            signal_type=signal_class_name,  # class name string
            role=role,
            parameters=signal_template["parameters"].copy(),
            description=signal_template["description"],
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

    def update_signal_parameter(
        self, signal_id: str, parameter_name: str, value: Any
    ) -> bool:
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
        """Get the library of available signals keyed by class name."""
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
        entry_signals = [
            s for s in self._current_strategy.signals if s.role == SignalRole.ENTRY
        ]
        if not entry_signals:
            self._validation_errors.append(
                "Strategy must have at least one entry signal"
            )

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
                elif param.parameter_type == "float" and not isinstance(
                    param.value, (int, float)
                ):
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be a number"
                    )
                elif param.parameter_type == "str" and not isinstance(param.value, str):
                    self._validation_errors.append(
                        f"Signal {signal.signal_id}: Parameter '{param_name}' must be a string"
                    )
                elif param.parameter_type == "bool" and not isinstance(
                    param.value, bool
                ):
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
                        "signal_type": signal.signal_type.value,
                            if isinstance(signal.signal_type, str)
                            else getattr(
                                signal.signal_type, "value", str(signal.signal_type)
                            )
                        ),
                        "role": signal.role.value,
                        "parameters": {
                            name: {
                                "value": param.value,
                                "parameter_type": param.parameter_type,
                                "min_value": param.min_value,
                                "max_value": param.max_value,
                                "options": param.options,
                                "description": param.description,
                                "required": param.required,
                            }
                            for name, param in signal.parameters.items()
                        },
                        "enabled": signal.enabled,
                        "weight": signal.weight,
                        "description": signal.description,
                    }
                    for signal in self._current_strategy.signals
                ],
                "combiners": self._current_strategy.combiners,
                "created_at": self._current_strategy.created_at,
                "modified_at": self._current_strategy.modified_at,
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
                st = signal_data["signal_type"]
                if isinstance(st, str):
                    signal_type=SignalType(signal_data["signal_type"]),
                else:
                    class_name = getattr(st, "value", str(st))
                signal_config = SignalConfig(
                    signal_id=signal_data["signal_id"],
                    signal_type=class_name,
                    role=SignalRole(signal_data["role"]),
                    enabled=signal_data.get("enabled", True),
                    weight=signal_data.get("weight", 1.0),
                    description=signal_data.get("description", ""),
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
                        required=param_data.get("required", True),
                    )

                # Add imported signals at the beginning to maintain order
                self._current_strategy.signals.insert(0, signal_config)

            self.strategy_changed.emit()
            return True

        except Exception as e:
            print(f"Error importing strategy: {e}")
            return False
