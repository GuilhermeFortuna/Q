"""
Data handling module for market data, including candle and tick data.
Provides classes and methods to load, process, and manage historical market data for backtesting trading strategies.
"""

from src.data.candle_data import CandleData
from src.data.base import MarketData
from src.data.tick_data import TickData

__all__ = ["MarketData", "CandleData", "TickData"]
