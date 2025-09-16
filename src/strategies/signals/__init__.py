"""
Composable Trading Signals
-------------------------

This package exposes simple signal components that can be combined by
CompositeStrategy to form richer strategies without duplicating code.
"""

from .base import TradingSignal, SignalDecision
from .ma_crossover import MaCrossoverSignal
from .bbands import BollingerBandSignal

__all__ = [
    'TradingSignal',
    'SignalDecision',
    'MaCrossoverSignal',
    'BollingerBandSignal',
]
