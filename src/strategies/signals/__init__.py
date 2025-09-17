"""
Composable Trading Signals
-------------------------

This package exposes simple signal components that can be combined by
CompositeStrategy to form richer strategies without duplicating code.
"""

from .base import TradingSignal, SignalDecision
from .ma_crossover import MaCrossoverSignal
from .bbands import BollingerBandSignal
from .helpers import *  # utilities (not exported via __all__)

# New composable signals
from .rsi_mean_reversion import RsiMeanReversionSignal
from .adx_dmi import AdxDmiSignal
from .supertrend import SupertrendFlipSignal
from .donchian_breakout import DonchianBreakoutSignal
from .macd_momentum import MacdMomentumSignal
from .keltner_squeeze import KeltnerSqueezeBreakoutSignal
from .vwap_deviation import VwapDeviationReversionSignal
from .volume_spike_exhaustion import VolumeSpikeExhaustionSignal
from .atr_trailing_stop import AtrTrailingStopReversalSignal
from .heikin_ashi_trend import HeikinAshiTrendContinuationSignal
from .mtf_ma_alignment import MtfMaAlignmentFilter
from .choppiness_filter import ChoppinessRegimeFilter

__all__ = [
    'TradingSignal',
    'SignalDecision',
    'MaCrossoverSignal',
    'BollingerBandSignal',
    'RsiMeanReversionSignal',
    'AdxDmiSignal',
    'SupertrendFlipSignal',
    'DonchianBreakoutSignal',
    'MacdMomentumSignal',
    'KeltnerSqueezeBreakoutSignal',
    'VwapDeviationReversionSignal',
    'VolumeSpikeExhaustionSignal',
    'AtrTrailingStopReversalSignal',
    'HeikinAshiTrendContinuationSignal',
    'MtfMaAlignmentFilter',
    'ChoppinessRegimeFilter',
]
