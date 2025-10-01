__version__ = "0.1.0"
__description__ = "A package for strategy optimization using Optuna."

# from .engine import Optimizer
from .database import DBStorage

__all__ = ['DBStorage']


def get_package_info():
    """Return package information as a dictionary."""
    return {
        'name': 'optimizer',
        'version': __version__,
        'description': __description__,
    }
