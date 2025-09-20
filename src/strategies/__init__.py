"""
Strategies Package
------------------

Exports for composing and running strategies and signals.
Existing concrete strategies (e.g., swingtrade.MaCrossover) remain available
for backward compatibility.
"""

from .composite import CompositeStrategy
from .hybrid_strategy import (
    HybridCandleTickStrategy,
    HybridExecutionConfig,
    HybridExitConfig,
)
from .signals import (
    TradingSignal,
    SignalDecision,
    MaCrossoverSignal,
    BollingerBandSignal,
)
from .swingtrade import MaCrossover
from .combiners import (
    GatedCombiner,
    ThresholdedWeightedVote,
    WeightedSignalCombiner,
)

__all__ = [
    'CompositeStrategy',
    'HybridCandleTickStrategy',
    'HybridExecutionConfig',
    'HybridExitConfig',
    'TradingSignal',
    'SignalDecision',
    'MaCrossoverSignal',
    'BollingerBandSignal',
    'MaCrossover',
    'GatedCombiner',
    'ThresholdedWeightedVote',
    'WeightedSignalCombiner',
]
