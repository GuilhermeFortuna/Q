# Backtester test package
"""
Pytest configuration and shared fixtures for the backtester tests.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    np.random.seed(42)  # For reproducible test data

    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high_prices = close_prices + np.random.uniform(0, 2, 100)
    low_prices = close_prices - np.random.uniform(0, 2, 100)
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = close_prices[0]
    volumes = np.random.randint(1000, 10000, 100)

    return pd.DataFrame(
        {
            'datetime': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes,
        }
    ).set_index('datetime')


@pytest.fixture
def sample_signals():
    """Create sample trading signals for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    signals = np.random.choice([-1, 0, 1], size=100, p=[0.1, 0.8, 0.1])

    return pd.Series(signals, index=dates, name='signals')
