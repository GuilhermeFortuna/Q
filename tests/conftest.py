"""
Comprehensive test fixtures for the q trading framework.

This module provides shared fixtures used across all test files, including
sample data, mock objects, and test utilities.
"""

import datetime as dt
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.data import CandleData, TickData
from src.backtester import BacktestParameters, Engine, TradeRegistry, TradeOrder
from src.strategies.signals.base import SignalDecision


@pytest.fixture
def sample_ohlcv_data():
    """Basic OHLCV DataFrame for testing."""
    dates = pd.date_range('2024-01-01 10:00:00', periods=100, freq='1H')
    np.random.seed(42)  # For reproducible tests
    
    # Generate realistic price data
    base_price = 100.0
    returns = np.random.normal(0, 0.02, 100)  # 2% volatility
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices)
    
    # Create OHLCV data
    data = {
        'open': prices + np.random.normal(0, 0.001, 100),
        'high': prices + np.abs(np.random.normal(0, 0.005, 100)),
        'low': prices - np.abs(np.random.normal(0, 0.005, 100)),
        'close': prices,
        'volume': np.random.randint(100, 1000, 100)
    }
    
    df = pd.DataFrame(data, index=dates)
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
    
    return df


@pytest.fixture
def sample_tick_data():
    """Tick-level data for testing."""
    start_time = dt.datetime(2024, 1, 1, 9, 0, 0)
    times = [start_time + dt.timedelta(seconds=i*30) for i in range(200)]  # 30-second intervals
    
    np.random.seed(42)
    base_price = 100.0
    prices = [base_price]
    
    for i in range(199):
        change = np.random.normal(0, 0.001)  # Small price changes
        prices.append(prices[-1] + change)
    
    data = {
        'datetime': times,
        'price': prices,
        'volume': np.random.randint(1, 10, 200)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def candle_data_fixture(sample_ohlcv_data):
    """CandleData instance with realistic multi-day data."""
    # Create data spanning multiple days
    dates = pd.date_range('2024-01-01 10:00:00', periods=500, freq='1H')
    np.random.seed(42)
    
    base_price = 100.0
    returns = np.random.normal(0, 0.02, 500)
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices)
    
    data = {
        'open': prices + np.random.normal(0, 0.001, 500),
        'high': prices + np.abs(np.random.normal(0, 0.005, 500)),
        'low': prices - np.abs(np.random.normal(0, 0.005, 500)),
        'close': prices,
        'volume': np.random.randint(100, 1000, 500)
    }
    
    df = pd.DataFrame(data, index=dates)
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
    
    candle_data = CandleData(symbol='TEST', timeframe='60min')
    candle_data.df = df
    return candle_data


@pytest.fixture
def tick_data_fixture(sample_tick_data):
    """TickData instance for testing."""
    tick_data = TickData(symbol='TEST')
    tick_data.df = sample_tick_data
    return tick_data


@pytest.fixture
def backtest_params_fixture():
    """Standard BacktestParameters for testing."""
    return BacktestParameters(
        point_value=10.0,
        cost_per_trade=2.50,
        permit_swingtrade=True,
        entry_time_limit=dt.time(9, 0),
        exit_time_limit=dt.time(17, 0),
        max_trade_day=1,
        bypass_first_exit_check=False
    )


@pytest.fixture
def trade_registry_fixture(backtest_params_fixture):
    """Pre-populated TradeRegistry for testing."""
    registry = TradeRegistry(
        point_value=backtest_params_fixture.point_value,
        cost_per_trade=backtest_params_fixture.cost_per_trade
    )
    
    # Add some sample trades
    base_time = dt.datetime(2024, 1, 1, 10, 0, 0)
    
    # Trade 1: Profitable long trade
    registry.register_order(TradeOrder(
        type='buy',
        price=100.0,
        datetime=base_time,
        comment='entry',
        amount=1
    ))
    registry.register_order(TradeOrder(
        type='close',
        price=105.0,
        datetime=base_time + dt.timedelta(hours=1),
        comment='exit',
        amount=1
    ))
    
    # Trade 2: Losing short trade (start fresh)
    registry.register_order(TradeOrder(
        type='sell',
        price=105.0,
        datetime=base_time + dt.timedelta(hours=2),
        comment='entry',
        amount=1
    ))
    registry.register_order(TradeOrder(
        type='close',
        price=108.0,
        datetime=base_time + dt.timedelta(hours=3),
        comment='exit',
        amount=1
    ))
    
    return registry


@pytest.fixture
def mock_mt5_connection():
    """Mock MT5 connection for data import tests."""
    with patch('MetaTrader5.initialize') as mock_init, \
         patch('MetaTrader5.copy_rates_range') as mock_copy_rates, \
         patch('MetaTrader5.shutdown') as mock_shutdown:
        
        mock_init.return_value = True
        
        # Mock historical data
        mock_data = np.array([
            (1640995200, 100.0, 101.0, 99.0, 100.5, 1000),  # 2022-01-01 00:00:00
            (1640998800, 100.5, 102.0, 100.0, 101.5, 1200),  # 2022-01-01 01:00:00
            (1641002400, 101.5, 103.0, 101.0, 102.0, 1100),  # 2022-01-01 02:00:00
        ], dtype=[('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8')])
        
        mock_copy_rates.return_value = mock_data
        mock_shutdown.return_value = True
        
        yield {
            'initialize': mock_init,
            'copy_rates_range': mock_copy_rates,
            'shutdown': mock_shutdown
        }


@pytest.fixture
def sample_signal_decisions():
    """Sample SignalDecision objects for testing."""
    return [
        SignalDecision(side='long', strength=0.8, info={'rsi': 30}),
        SignalDecision(side='short', strength=0.6, info={'rsi': 70}),
        SignalDecision(side=None, strength=0.0, info={'rsi': 50}),
        SignalDecision(side='long', strength=1.0, info={'macd': 0.5}),
    ]


@pytest.fixture
def simple_strategy():
    """Simple test strategy for backtesting."""
    from src.backtester.strategy import TradingStrategy
    
    class SimpleTestStrategy(TradingStrategy):
        def compute_indicators(self, data: dict) -> None:
            # Add a simple moving average
            if 'candle' in data:
                candle = data['candle']
                if hasattr(candle, 'df'):
                    # Original CandleData
                    df = candle.df
                    df['sma_10'] = df['close'].rolling(10).mean()
                else:
                    # EngineCandleData - compute SMA on numpy arrays
                    close_prices = candle.close
                    if len(close_prices) >= 10:
                        sma_10 = np.convolve(close_prices, np.ones(10)/10, mode='valid')
                        # Pad with NaN for the first 9 values
                        sma_10 = np.concatenate([np.full(9, np.nan), sma_10])
                        candle.sma_10 = sma_10
                    else:
                        # Not enough data for SMA
                        candle.sma_10 = np.full(len(close_prices), np.nan)
        
        def entry_strategy(self, i: int, data: dict):
            if 'candle' not in data or i < 10:
                return None
            
            candle = data['candle']
            if i >= 10 and candle.close[i] > candle.sma_10[i]:
                return TradeOrder(
                    type='buy',
                    price=float(candle.close[i]),
                    datetime=candle.datetime_index[i],
                    comment='sma_crossover',
                    amount=1
                )
            return None
        
        def exit_strategy(self, i: int, data: dict, trade_info=None):
            if 'candle' not in data or i < 10:
                return None
            
            candle = data['candle']
            if i >= 10 and candle.close[i] < candle.sma_10[i]:
                return TradeOrder(
                    type='close',
                    price=float(candle.close[i]),
                    datetime=candle.datetime_index[i],
                    comment='sma_crossover_exit',
                    amount=1
                )
            return None
    
    return SimpleTestStrategy()


@pytest.fixture
def multi_day_candle_data():
    """CandleData spanning multiple days for daytrade testing."""
    # Create data spanning 3 days
    dates = pd.date_range('2024-01-01 09:00:00', periods=72, freq='1H')  # 3 days * 24 hours
    
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0, 0.01, 72)
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices)
    
    data = {
        'open': prices + np.random.normal(0, 0.001, 72),
        'high': prices + np.abs(np.random.normal(0, 0.005, 72)),
        'low': prices - np.abs(np.random.normal(0, 0.005, 72)),
        'close': prices,
        'volume': np.random.randint(100, 1000, 72)
    }
    
    df = pd.DataFrame(data, index=dates)
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
    
    candle_data = CandleData(symbol='TEST', timeframe='60min')
    candle_data.df = df
    return candle_data


@pytest.fixture
def sample_metrics():
    """Sample performance metrics for evaluation testing."""
    return {
        'profit_factor': 1.5,
        'max_drawdown': 0.15,
        'win_rate': 0.6,
        'trades': 100,
        'sharpe': 1.2,
        'cagr': 0.25,
        'consecutive_losses': 3
    }


@pytest.fixture
def acceptance_criteria():
    """Standard acceptance criteria for testing."""
    from src.backtester.evaluation import AcceptanceCriteria
    return AcceptanceCriteria(
        min_trades=50,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        min_sharpe=1.0,
        min_cagr=0.15,
        min_win_rate=0.5,
        max_consecutive_losses=5
    )


@pytest.fixture
def strategy_evaluator(acceptance_criteria):
    """StrategyEvaluator instance for testing."""
    from src.backtester.evaluation import StrategyEvaluator
    return StrategyEvaluator(acceptance_criteria)


# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "gui: GUI tests (requires PySide6)")
    config.addinivalue_line("markers", "mt5: Tests requiring MetaTrader 5")


# Test data generation helpers
def create_trending_data(start_price: float = 100.0, periods: int = 100, 
                        trend: float = 0.001, volatility: float = 0.02) -> pd.DataFrame:
    """Create trending price data for testing."""
    dates = pd.date_range('2024-01-01', periods=periods, freq='1H')
    np.random.seed(42)
    
    returns = np.random.normal(trend, volatility, periods)
    prices = [start_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices)
    
    data = {
        'open': prices + np.random.normal(0, 0.001, periods),
        'high': prices + np.abs(np.random.normal(0, 0.005, periods)),
        'low': prices - np.abs(np.random.normal(0, 0.005, periods)),
        'close': prices,
        'volume': np.random.randint(100, 1000, periods)
    }
    
    df = pd.DataFrame(data, index=dates)
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
    
    return df


def create_ranging_data(start_price: float = 100.0, periods: int = 100, 
                       range_size: float = 0.05) -> pd.DataFrame:
    """Create ranging/sideways price data for testing."""
    dates = pd.date_range('2024-01-01', periods=periods, freq='1H')
    np.random.seed(42)
    
    # Create sine wave with noise for ranging behavior
    x = np.linspace(0, 4 * np.pi, periods)
    base_prices = start_price + range_size * start_price * np.sin(x) / 2
    
    data = {
        'open': base_prices + np.random.normal(0, 0.001, periods),
        'high': base_prices + np.abs(np.random.normal(0, 0.005, periods)),
        'low': base_prices - np.abs(np.random.normal(0, 0.005, periods)),
        'close': base_prices,
        'volume': np.random.randint(100, 1000, periods)
    }
    
    df = pd.DataFrame(data, index=dates)
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
    
    return df


# Cleanup fixtures for file I/O tests
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up any test files created during tests."""
    yield
    # Add cleanup logic here if needed
    pass
