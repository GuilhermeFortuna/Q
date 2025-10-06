"""
Strategy Controller for Backtester GUI

This module contains the controller for managing strategy building logic,
including signal composition, validation, and compilation.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox

from ..models.strategy_model import StrategyModel, SignalType, SignalRole, StrategyConfig
from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeOrder


class StrategyCompilationThread(QThread):
    """Thread for compiling strategies to avoid blocking the UI."""
    
    compilation_finished = Signal(object)  # compiled strategy
    compilation_error = Signal(str)  # error message
    
    def __init__(self, strategy_config: StrategyConfig):
        super().__init__()
        self.strategy_config = strategy_config
    
    def run(self):
        """Compile the strategy configuration into a TradingStrategy object."""
        try:
            # TODO: Implement strategy compilation logic
            # This would convert the StrategyConfig into a TradingStrategy instance
            # For now, we'll create a placeholder
            
            compiled_strategy = self._compile_strategy(self.strategy_config)
            self.compilation_finished.emit(compiled_strategy)
            
        except Exception as e:
            self.compilation_error.emit(str(e))
    
    def _compile_strategy(self, config: StrategyConfig) -> TradingStrategy:
        """Compile a strategy configuration into a TradingStrategy object."""
        # This is a placeholder implementation
        # In a real implementation, this would:
        # 1. Create signal objects based on the configuration
        # 2. Set up entry and exit logic
        # 3. Configure signal combination rules
        # 4. Return a complete TradingStrategy instance
        
        class CompiledStrategy(TradingStrategy):
            def __init__(self, strategy_config: StrategyConfig):
                super().__init__()
                self.config = strategy_config
                self._setup_signals()
            
            def _setup_signals(self):
                """Setup signals based on configuration."""
                # TODO: Implement signal setup logic
                pass
            
            def compute_indicators(self, data: dict) -> None:
                """Compute technical indicators for all signals."""
                # TODO: Implement indicator computation
                pass
            
            def entry_strategy(self, i: int, data: dict) -> Optional[TradeOrder]:
                """Determine entry signals."""
                # TODO: Implement entry logic
                return None
            
            def exit_strategy(self, i: int, data: dict, trade_info) -> Optional[TradeOrder]:
                """Determine exit signals."""
                # TODO: Implement exit logic
                return None
        
        return CompiledStrategy(config)


class StrategyController(QObject):
    """
    Controller for managing strategy building and compilation.
    
    This controller handles:
    - Strategy validation and compilation
    - Signal parameter management
    - Integration with the backtester engine
    - Error handling and user feedback
    """
    
    # Signals
    strategy_compiled = Signal(object)  # compiled strategy
    compilation_error = Signal(str)  # error message
    validation_changed = Signal(bool)  # is_valid
    
    def __init__(self, strategy_model: StrategyModel, parent=None):
        super().__init__(parent)
        self.strategy_model = strategy_model
        self._compilation_thread: Optional[StrategyCompilationThread] = None
        
        # Connect model signals
        self.strategy_model.strategy_changed.connect(self._on_strategy_changed)
        self.strategy_model.validation_changed.connect(self._on_validation_changed)
    
    def _on_strategy_changed(self):
        """Handle strategy model changes."""
        # Validate the strategy when it changes
        # Use QTimer.singleShot to avoid recursion
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.validate_strategy)
    
    def _on_validation_changed(self, is_valid: bool):
        """Handle validation state changes."""
        self.validation_changed.emit(is_valid)
    
    def validate_strategy(self) -> bool:
        """Validate the current strategy configuration."""
        return self.strategy_model.validate_strategy()
    
    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self.strategy_model.get_validation_errors()
    
    def compile_strategy(self) -> bool:
        """Compile the current strategy configuration."""
        if not self.strategy_model.has_strategy():
            self.compilation_error.emit("No strategy to compile")
            return False
        
        # Validate before compilation
        if not self.validate_strategy():
            errors = self.get_validation_errors()
            self.compilation_error.emit(f"Strategy validation failed: {'; '.join(errors)}")
            return False
        
        # Start compilation in a separate thread
        strategy_config = self.strategy_model.get_strategy_config()
        if strategy_config:
            self._compilation_thread = StrategyCompilationThread(strategy_config)
            self._compilation_thread.compilation_finished.connect(self._on_compilation_finished)
            self._compilation_thread.compilation_error.connect(self._on_compilation_error)
            self._compilation_thread.start()
            return True
        
        return False
    
    def _on_compilation_finished(self, compiled_strategy: TradingStrategy):
        """Handle successful strategy compilation."""
        self.strategy_compiled.emit(compiled_strategy)
        self._compilation_thread = None
    
    def _on_compilation_error(self, error_message: str):
        """Handle strategy compilation errors."""
        self.compilation_error.emit(error_message)
        self._compilation_thread = None
    
    def is_compiling(self) -> bool:
        """Check if strategy compilation is in progress."""
        return self._compilation_thread is not None and self._compilation_thread.isRunning()
    
    def cancel_compilation(self):
        """Cancel ongoing strategy compilation."""
        if self._compilation_thread and self._compilation_thread.isRunning():
            self._compilation_thread.terminate()
            self._compilation_thread.wait()
            self._compilation_thread = None
    
    def get_available_signal_types(self) -> List[SignalType]:
        """Get list of available signal types."""
        return list(self.strategy_model.get_available_signals().keys())
    
    def get_signal_parameters(self, signal_type: SignalType) -> Dict[str, Any]:
        """Get parameters for a specific signal type."""
        signals = self.strategy_model.get_available_signals()
        return signals.get(signal_type, {}).get("parameters", {})
    
    def create_signal(self, signal_type: SignalType, role: SignalRole, **kwargs) -> Optional[str]:
        """Create a new signal in the current strategy."""
        try:
            return self.strategy_model.add_signal(signal_type, role, **kwargs)
        except Exception as e:
            self.compilation_error.emit(f"Failed to create signal: {str(e)}")
            return None
    
    def update_signal_parameter(self, signal_id: str, parameter_name: str, value: Any) -> bool:
        """Update a signal parameter."""
        try:
            return self.strategy_model.update_signal_parameter(signal_id, parameter_name, value)
        except Exception as e:
            self.compilation_error.emit(f"Failed to update parameter: {str(e)}")
            return False
    
    def remove_signal(self, signal_id: str) -> bool:
        """Remove a signal from the current strategy."""
        try:
            return self.strategy_model.remove_signal(signal_id)
        except Exception as e:
            self.compilation_error.emit(f"Failed to remove signal: {str(e)}")
            return False
    
    def get_strategy_signals(self) -> List[Dict[str, Any]]:
        """Get all signals in the current strategy."""
        strategy_config = self.strategy_model.get_strategy_config()
        if not strategy_config:
            return []
        
        signals = []
        for signal in strategy_config.signals:
            signal_data = {
                "signal_id": signal.signal_id,
                "signal_type": signal.signal_type,
                "role": signal.role,
                "enabled": signal.enabled,
                "weight": signal.weight,
                "description": signal.description,
                "parameters": {
                    name: {
                        "value": param.value,
                        "type": param.parameter_type,
                        "min_value": param.min_value,
                        "max_value": param.max_value,
                        "options": param.options,
                        "description": param.description,
                        "required": param.required
                    }
                    for name, param in signal.parameters.items()
                }
            }
            signals.append(signal_data)
        
        return signals
    
    def export_strategy(self, file_path: str) -> bool:
        """Export the current strategy to a file."""
        try:
            return self.strategy_model.export_strategy(file_path)
        except Exception as e:
            self.compilation_error.emit(f"Failed to export strategy: {str(e)}")
            return False
    
    def import_strategy(self, file_path: str) -> bool:
        """Import a strategy from a file."""
        try:
            return self.strategy_model.import_strategy(file_path)
        except Exception as e:
            self.compilation_error.emit(f"Failed to import strategy: {str(e)}")
            return False
    
    def create_strategy_template(self, template_type: str) -> bool:
        """Create a strategy from a predefined template."""
        try:
            if template_type == "ma_crossover":
                return self._create_ma_crossover_template()
            elif template_type == "rsi_mean_reversion":
                return self._create_rsi_mean_reversion_template()
            elif template_type == "macd_trend":
                return self._create_macd_trend_template()
            else:
                self.compilation_error.emit(f"Unknown template type: {template_type}")
                return False
        except Exception as e:
            self.compilation_error.emit(f"Failed to create template: {str(e)}")
            return False
    
    def _create_ma_crossover_template(self) -> bool:
        """Create a moving average crossover strategy template."""
        # Create new strategy
        self.strategy_model.create_strategy("MA Crossover", "Simple moving average crossover strategy")
        
        # Add fast MA signal
        self.strategy_model.add_signal(
            SignalType.MOVING_AVERAGE,
            SignalRole.ENTRY,
            period=10,
            ma_type="SMA"
        )
        
        # Add slow MA signal
        self.strategy_model.add_signal(
            SignalType.MOVING_AVERAGE,
            SignalRole.ENTRY,
            period=20,
            ma_type="SMA"
        )
        
        return True
    
    def _create_rsi_mean_reversion_template(self) -> bool:
        """Create an RSI mean reversion strategy template."""
        # Create new strategy
        self.strategy_model.create_strategy("RSI Mean Reversion", "RSI-based mean reversion strategy")
        
        # Add RSI signal
        self.strategy_model.add_signal(
            SignalType.RSI,
            SignalRole.ENTRY,
            period=14,
            overbought=70,
            oversold=30
        )
        
        return True
    
    def _create_macd_trend_template(self) -> bool:
        """Create a MACD trend following strategy template."""
        # Create new strategy
        self.strategy_model.create_strategy("MACD Trend", "MACD-based trend following strategy")
        
        # Add MACD signal
        self.strategy_model.add_signal(
            SignalType.MACD,
            SignalRole.ENTRY,
            fast_period=12,
            slow_period=26,
            signal_period=9
        )
        
        return True
