"""
GUI Dialogs Package

This package contains dialog windows for the Backtester GUI,
providing specialized interfaces for specific tasks.

Dialogs:
- StrategySaveDialog: Save strategy configuration
- DataImportDialog: Import data from various sources
- ParameterEditDialog: Edit signal parameters
"""

from .strategy_save import StrategySaveDialog
from .data_import import DataImportDialog
from .parameter_edit import ParameterEditDialog

__all__ = [
    'StrategySaveDialog',
    'DataImportDialog',
    'ParameterEditDialog',
]


