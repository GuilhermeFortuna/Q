"""
Swingtrade Strategies
---------------------

This package contains trading strategies designed for swing trading,
typically holding positions for more than a single day.
"""

from .ma_crossover import MaCrossover

__all__ = [
    "MaCrossover",
]
