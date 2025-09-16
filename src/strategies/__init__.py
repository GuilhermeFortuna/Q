"""
Strategies Package
------------------

Exports for composing and running strategies and signals.
Existing concrete strategies (e.g., swingtrade.MaCrossover) remain available
for backward compatibility.
"""

from .composite import CompositeStrategy
from .signals import (
    TradingSignal,
    SignalDecision,
    MaCrossoverSignal,
    BollingerBandSignal,
)
from .swingtrade import MaCrossover

__all__ = [
    'CompositeStrategy',
    'TradingSignal',
    'SignalDecision',
    'MaCrossoverSignal',
    'BollingerBandSignal',
    'MaCrossover',
]
