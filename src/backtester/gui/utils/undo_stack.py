"""
Undo/Redo System for Strategy Builder

This module implements a command pattern-based undo/redo system for tracking
and reverting strategy modifications in the GUI.
"""

from typing import Any, Callable, Optional, List
from PySide6.QtCore import QObject, Signal
from enum import Enum


class CommandType(Enum):
    """Types of commands that can be undone/redone."""
    ADD_SIGNAL = "add_signal"
    REMOVE_SIGNAL = "remove_signal"
    EDIT_SIGNAL = "edit_signal"
    MOVE_SIGNAL = "move_signal"
    UPDATE_PARAMETER = "update_parameter"
    TOGGLE_SIGNAL = "toggle_signal"
    CLEAR_SIGNALS = "clear_signals"


class Command(QObject):
    """
    Base class for all undoable commands.
    
    Each command encapsulates a single operation that can be undone and redone.
    Commands store the necessary state to reverse their effects.
    """
    
    def __init__(self, command_type: CommandType, description: str):
        super().__init__()
        self.command_type = command_type
        self.description = description
        self.timestamp = None
    
    def execute(self) -> bool:
        """
        Execute the command.
        
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def undo(self) -> bool:
        """
        Undo the command.
        
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement undo()")
    
    def redo(self) -> bool:
        """
        Redo the command (same as execute).
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.execute()


class AddSignalCommand(Command):
    """Command for adding a signal to the strategy."""
    
    def __init__(self, strategy_model, signal_class_name: str, role, signal_id: str = None):
        super().__init__(CommandType.ADD_SIGNAL, f"Add signal: {signal_class_name}")
        self.strategy_model = strategy_model
        self.signal_class_name = signal_class_name
        self.role = role
        self.signal_id = signal_id
    
    def execute(self) -> bool:
        """Add the signal."""
        try:
            if not self.signal_id:
                self.signal_id = self.strategy_model.add_signal(self.signal_class_name, self.role)
            else:
                # Re-add with existing ID
                self.strategy_model.add_signal_with_id(self.signal_class_name, self.role, self.signal_id)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Remove the signal."""
        try:
            if self.signal_id:
                self.strategy_model.remove_signal(self.signal_id)
            return True
        except Exception:
            return False


class RemoveSignalCommand(Command):
    """Command for removing a signal from the strategy."""
    
    def __init__(self, strategy_model, signal_id: str, signal_config: Any):
        super().__init__(CommandType.REMOVE_SIGNAL, f"Remove signal: {signal_config.signal_type}")
        self.strategy_model = strategy_model
        self.signal_id = signal_id
        self.signal_config = signal_config
    
    def execute(self) -> bool:
        """Remove the signal."""
        try:
            self.strategy_model.remove_signal(self.signal_id)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Re-add the signal."""
        try:
            self.strategy_model.add_signal_with_config(self.signal_config)
            return True
        except Exception:
            return False


class EditSignalCommand(Command):
    """Command for editing signal parameters."""
    
    def __init__(self, strategy_model, signal_id: str, old_params: dict, new_params: dict):
        super().__init__(CommandType.EDIT_SIGNAL, f"Edit signal parameters")
        self.strategy_model = strategy_model
        self.signal_id = signal_id
        self.old_params = old_params.copy()
        self.new_params = new_params.copy()
    
    def execute(self) -> bool:
        """Apply new parameters."""
        try:
            for param_name, param_value in self.new_params.items():
                self.strategy_model.update_signal_parameter(self.signal_id, param_name, param_value)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Restore old parameters."""
        try:
            for param_name, param_value in self.old_params.items():
                self.strategy_model.update_signal_parameter(self.signal_id, param_name, param_value)
            return True
        except Exception:
            return False


class MoveSignalCommand(Command):
    """Command for moving signals up/down in the strategy."""
    
    def __init__(self, strategy_model, signal_id: str, old_index: int, new_index: int):
        super().__init__(CommandType.MOVE_SIGNAL, f"Move signal from position {old_index} to {new_index}")
        self.strategy_model = strategy_model
        self.signal_id = signal_id
        self.old_index = old_index
        self.new_index = new_index
    
    def execute(self) -> bool:
        """Move signal to new position."""
        try:
            self.strategy_model.move_signal(self.signal_id, self.new_index)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Move signal back to old position."""
        try:
            self.strategy_model.move_signal(self.signal_id, self.old_index)
            return True
        except Exception:
            return False


class ToggleSignalCommand(Command):
    """Command for enabling/disabling signals."""
    
    def __init__(self, strategy_model, signal_id: str, old_enabled: bool, new_enabled: bool):
        super().__init__(CommandType.TOGGLE_SIGNAL, f"{'Enable' if new_enabled else 'Disable'} signal")
        self.strategy_model = strategy_model
        self.signal_id = signal_id
        self.old_enabled = old_enabled
        self.new_enabled = new_enabled
    
    def execute(self) -> bool:
        """Set new enabled state."""
        try:
            signal_config = self.strategy_model.get_signal(self.signal_id)
            if signal_config:
                signal_config.enabled = self.new_enabled
                self.strategy_model.strategy_changed.emit()
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Restore old enabled state."""
        try:
            signal_config = self.strategy_model.get_signal(self.signal_id)
            if signal_config:
                signal_config.enabled = self.old_enabled
                self.strategy_model.strategy_changed.emit()
            return True
        except Exception:
            return False


class ClearSignalsCommand(Command):
    """Command for clearing all signals from the strategy."""
    
    def __init__(self, strategy_model, signals_backup: List[Any]):
        super().__init__(CommandType.CLEAR_SIGNALS, "Clear all signals")
        self.strategy_model = strategy_model
        self.signals_backup = signals_backup.copy()
    
    def execute(self) -> bool:
        """Clear all signals."""
        try:
            strategy_config = self.strategy_model.get_strategy_config()
            if strategy_config:
                signal_ids = [signal.signal_id for signal in strategy_config.signals]
                for signal_id in signal_ids:
                    self.strategy_model.remove_signal(signal_id)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Restore all signals."""
        try:
            for signal_config in self.signals_backup:
                self.strategy_model.add_signal_with_config(signal_config)
            return True
        except Exception:
            return False


class UndoStack(QObject):
    """
    Manages the undo/redo stack for strategy modifications.
    
    This class maintains a stack of commands and provides methods to execute,
    undo, and redo operations. It also emits signals when the undo/redo state
    changes.
    """
    
    # Signals
    undo_available_changed = Signal(bool)  # undo_available
    redo_available_changed = Signal(bool)  # redo_available
    command_executed = Signal(Command)     # command
    
    def __init__(self, max_size: int = 50):
        super().__init__()
        self.max_size = max_size
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self._executing = False
    
    def execute_command(self, command: Command) -> bool:
        """
        Execute a command and add it to the undo stack.
        
        Args:
            command: The command to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self._executing:
            return False
        
        self._executing = True
        try:
            if command.execute():
                # Add to undo stack
                self.undo_stack.append(command)
                
                # Clear redo stack when new command is executed
                self.redo_stack.clear()
                
                # Limit stack size
                if len(self.undo_stack) > self.max_size:
                    self.undo_stack.pop(0)
                
                # Emit signals
                self.undo_available_changed.emit(True)
                self.redo_available_changed.emit(False)
                self.command_executed.emit(command)
                
                return True
            else:
                return False
        finally:
            self._executing = False
    
    def undo(self) -> bool:
        """
        Undo the last command.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.undo_stack or self._executing:
            return False
        
        self._executing = True
        try:
            command = self.undo_stack.pop()
            if command.undo():
                self.redo_stack.append(command)
                self.undo_available_changed.emit(len(self.undo_stack) > 0)
                self.redo_available_changed.emit(True)
                return True
            else:
                # Put command back if undo failed
                self.undo_stack.append(command)
                return False
        finally:
            self._executing = False
    
    def redo(self) -> bool:
        """
        Redo the last undone command.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redo_stack or self._executing:
            return False
        
        self._executing = True
        try:
            command = self.redo_stack.pop()
            if command.redo():
                self.undo_stack.append(command)
                self.undo_available_changed.emit(True)
                self.redo_available_changed.emit(len(self.redo_stack) > 0)
                return True
            else:
                # Put command back if redo failed
                self.redo_stack.append(command)
                return False
        finally:
            self._executing = False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0 and not self._executing
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0 and not self._executing
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the next command to undo."""
        if self.undo_stack:
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the next command to redo."""
        if self.redo_stack:
            return self.redo_stack[-1].description
        return None
    
    def clear(self):
        """Clear both undo and redo stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.undo_available_changed.emit(False)
        self.redo_available_changed.emit(False)
    
    def get_stack_info(self) -> dict:
        """Get information about the current stack state."""
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'next_undo': self.get_undo_description(),
            'next_redo': self.get_redo_description()
        }
