from optuna.storages import JournalStorage
from optuna.storages.journal import JournalFileBackend
import sys
import os

PROJECT_ROOT_PATH = os.path.abspath(__file__.split('src')[0])


class DBStorage:
    """
    Manages storage paths for optimization results.
    """

    def __init__(self):
        # Validate optimization structure
        self.base_path = os.path.join(PROJECT_ROOT_PATH, 'optimization')
        self.storage_base_path = os.path.join(self.base_path, 'storage')
        self._validate_optimization_structure()

        # Validate current file path
        self.file_name = sys.argv[0]
        self.file_path = os.path.join(os.getcwd(), self.file_name)
        self._validate_current_file_path()

        # Construct study path
        self.study_name = self.file_name
        self.study_path = self.resolve_study_path()

    def _validate_optimization_structure(self) -> None:
        if not os.path.exists(self.base_path):
            raise FileNotFoundError(f"Base path '{self.base_path}' does not exist.")
        if not os.path.exists(self.storage_base_path):
            raise FileNotFoundError(
                f"Storage path '{self.storage_base_path}' does not exist."
            )

    def _validate_current_file_path(self) -> None:
        if self.base_path not in self.file_path:
            raise ValueError(
                f"Current path '{self.file_path}' is not within the optimization base path set in src/optimizer/config.py: '{self.base_path}'."
            )

    def resolve_study_path(self) -> str:
        relative_path = (
            self.file_path.split(self.base_path)[-1].strip(os.sep).strip('.py')
        )
        study_path = os.path.join(self.storage_base_path, f'{relative_path}.log')
        return study_path
