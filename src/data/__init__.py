"""
Data handling module for market data, including candle and tick data.
Provides classes and methods to load, process, and manage historical market data for backtesting trading strategies.
"""

from .base import MarketData
from .candle_data import CandleData
from .tick_data import TickData


__all__ = ["MarketData", "CandleData", "TickData"]
