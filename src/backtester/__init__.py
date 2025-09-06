"""
PyQuant Backtester

A Python framework for defining, backtesting, and analyzing trading strategies
on historical market data.

This package provides comprehensive tools to simulate trading strategies against
historical price data with flexible strategy definitions, multiple data sources,
and detailed performance analysis.
"""

# Core data handling
from .data import MarketData, CandleData, TickData

# Strategy framework
from .strategy import TradingStrategy

# Backtesting engine
from .engine import Engine, BacktestParameters

# Trade management and analysis
from .trades import TradeOrder, TradeRegistry

# Utilities and constants
from .utils import TIMEFRAMES, TimeframeInfo

# Package metadata
__version__ = "0.1.0"
__author__ = "qcrew"
__email__ = ""
__description__ = "Backtesting engine for trading strategies"

# Define what gets imported with "from backtester import *"
__all__ = [
    # Data classes
    "MarketData",
    "CandleData",
    "TickData",
    # Strategy interface
    "TradingStrategy",
    # Engine classes
    "Engine",
    "BacktestParameters",
    # Trade classes
    "TradeOrder",
    "TradeRegistry",
    # Utilities
    "TIMEFRAMES",
    "TimeframeInfo",
    # Package info
    "__version__",
]


# Package initialization
def get_package_info():
    """Return package information as a dictionary."""
    return {
        'name': 'backtester',
        'version': __version__,
        'description': __description__,
        'components': {
            'data_classes': ['MarketData', 'CandleData', 'TickData'],
            'strategy_classes': ['TradingStrategy'],
            'engine_classes': ['Engine', 'BacktestParameters'],
            'trade_classes': ['TradeOrder', 'TradeRegistry'],
            'utilities': ['TIMEFRAMES', 'MARKET_DATA_LAYOUT', 'TimeframeInfo'],
        },
        'key_features': [
            'MT5 integration for live data',
            'CSV data import capability',
            'Flexible strategy framework',
            'Comprehensive performance metrics',
            'Built-in technical indicators',
            'Trade registry with tax calculations',
            'Progress tracking and visualization',
        ],
    }


# Validate package integrity on import
def _validate_package():
    """Internal function to validate package components on import."""
    try:
        # Test core imports
        assert MarketData is not None
        assert CandleData is not None
        assert TradingStrategy is not None
        assert Engine is not None
        assert TradeOrder is not None

        # Validate key relationships
        assert issubclass(CandleData, MarketData)
        assert issubclass(TickData, MarketData)
        assert issubclass(TradingStrategy)

        return True
    except (AssertionError, ImportError) as e:
        import warnings

        warnings.warn(f"Package validation failed: {e}")
        return False


# Run validation on import
_PACKAGE_VALID = _validate_package()

if not _PACKAGE_VALID:
    import warnings

    warnings.warn("Backtester package may not be fully functional due to import issues")
