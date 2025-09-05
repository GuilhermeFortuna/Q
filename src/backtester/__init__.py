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
from .strategy import TradingStrategy, MaCrossover

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
    # Strategy classes
    "TradingStrategy",
    "MaCrossover",
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


# Convenience imports for common use cases
def create_simple_backtest(
    symbol, timeframe, data_path, strategy_config, backtest_params
):
    """
    Convenience function to create a simple backtest setup.

    Args:
        symbol (str): Trading symbol
        timeframe (str): Data timeframe
        data_path (str): Path to CSV data file
        strategy_config (dict): Strategy configuration parameters
        backtest_params (dict): Backtest parameter configuration

    Returns:
        Engine: Configured backtesting engine ready to run

    Example:
        >>> engine = create_simple_backtest(
        ...     symbol='MSFT',
        ...     timeframe='60min',
        ...     data_path='data.csv',
        ...     strategy_config={'short_period': 9, 'long_period': 21},
        ...     backtest_params={'point_value': 450.0, 'cost_per_trade': 2.5}
        ... )
        >>> results = engine.run_backtest(display_progress=True)
    """
    # Load data
    candles = CandleData(symbol=symbol, timeframe=timeframe)
    candles.data = CandleData.import_from_csv(data_path)

    # Create strategy with default MaCrossover if not specified
    if 'strategy_type' not in strategy_config:
        strategy = MaCrossover(
            tick_value=strategy_config.get('tick_value', 0.01),
            short_ma_func=strategy_config.get('short_ma_func', 'ema'),
            short_ma_period=strategy_config.get('short_period', 9),
            long_ma_func=strategy_config.get('long_ma_func', 'sma'),
            long_ma_period=strategy_config.get('long_period', 21),
            delta_tick_factor=strategy_config.get('delta_factor', 1.0),
            always_active=strategy_config.get('always_active', True),
        )
    else:
        raise NotImplementedError(
            "Custom strategy types not yet supported in convenience function"
        )

    # Create parameters
    params = BacktestParameters(**backtest_params)

    # Create and return engine
    return Engine(parameters=params, strategy=strategy, data={'candle': candles})


# Package initialization
def get_package_info():
    """Return package information as a dictionary."""
    return {
        'name': 'backtester',
        'version': __version__,
        'description': __description__,
        'components': {
            'data_classes': ['MarketData', 'CandleData', 'TickData'],
            'strategy_classes': ['TradingStrategy', 'MaCrossover'],
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
        assert issubclass(MaCrossover, TradingStrategy)

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
