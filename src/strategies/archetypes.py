from __future__ import annotations

from typing import List, Optional, Tuple

from src.strategies.composite import CompositeStrategy, weighted_vote
from src.strategies.signals import (
    SignalDecision,
    # Filters / regimes
    MtfMaAlignmentFilter,
    ChoppinessRegimeFilter,
    # Trend strength / confirmations
    AdxDmiSignal,
    DonchianBreakoutSignal,
    # Entries / triggers
    SupertrendFlipSignal,
    KeltnerSqueezeBreakoutSignal,
    RsiMeanReversionSignal,
    BollingerBandSignal,
    # Exits / stops
    AtrTrailingStopReversalSignal,
    # Volume
    VolumeSpikeExhaustionSignal,
)


# --- Custom combiner for the Range Fader ---

def conservative_agreement_combiner(decisions: List[SignalDecision]) -> Tuple[Optional[str], float]:
    """
    Require regime to be 'range' (via ChoppinessRegimeFilter) and force all non-neutral
    entry signals (RSI, Bollinger Bands) to agree on direction. If conditions are met,
    return (agreed_side, 1.0); otherwise (None, 0.0).

    Identification heuristic:
    - Regime decision is the one whose info contains the 'range' key.
    - RSI decision exposes 'rsi' in info.
    - Bollinger decision exposes 'bb_lower'/'bb_upper' in info.
    """
    # Gate by regime: we need range == True
    regime_range = None
    for d in decisions:
        if isinstance(d.info, dict) and 'range' in d.info:
            regime_range = bool(d.info.get('range'))
            break
    if not regime_range:
        return None, 0.0

    # Collect entry decisions (non-neutral) for RSI and BBands
    entry_sides: List[str] = []
    for d in decisions:
        if d.side is None:
            continue
        info = d.info if isinstance(d.info, dict) else {}
        is_rsi = 'rsi' in info
        is_bb = ('bb_lower' in info) or ('bb_upper' in info)
        if is_rsi or is_bb:
            entry_sides.append(d.side)

    if not entry_sides:
        return None, 0.0

    # All non-neutral entry signals must agree
    if all(s == entry_sides[0] for s in entry_sides):
        return entry_sides[0], 1.0

    return None, 0.0


# --- Archetype factories ---

def create_momentum_rider_strategy() -> CompositeStrategy:
    """
    Trend-following strategy:
    - Regime filter: MtfMaAlignmentFilter (higher-timeframe alignment; falls back to longer MA if no HT data)
    - Trend confirmation: AdxDmiSignal
    - Entry trigger: SupertrendFlipSignal
    - Exit logic: AtrTrailingStopReversalSignal (stop-and-reverse trail)

    Combiner: default weighted_vote
    always_active: True
    """
    signals = [
        MtfMaAlignmentFilter(ht_ma_len=50, lt_ma_len=20, alignment_mode='ht_only', cap=0.4),
        AdxDmiSignal(length=14, adx_thresh=25.0),
        SupertrendFlipSignal(atr_length=10, atr_mult=3.0),
        AtrTrailingStopReversalSignal(atr_len=14, atr_mult=3.0, method='chandelier'),
    ]
    return CompositeStrategy(signals=signals, combiner=weighted_vote, always_active=True)


def create_range_fader_strategy() -> CompositeStrategy:
    """
    Mean-reversion in ranging regimes:
    - Regime: ChoppinessRegimeFilter (gate: requires range)
    - Entries: RSI mean-reversion + Bollinger Bands

    Combiner: conservative_agreement_combiner (all non-neutral entries must agree; regime must be in range)
    always_active: False
    """
    signals = [
        ChoppinessRegimeFilter(length=14, chop_low=38.0, chop_high=62.0, baseline_ma_len=None),
        RsiMeanReversionSignal(length=14, upper_band=70, lower_band=30, band_smooth=5, exit_mid=False),
        BollingerBandSignal(length=20, std=2.0, mamode=None),
    ]
    return CompositeStrategy(signals=signals, combiner=conservative_agreement_combiner, always_active=False)


def create_volatility_breakout_strategy() -> CompositeStrategy:
    """
    Breakout from low-volatility squeezes:
    - Core: KeltnerSqueezeBreakoutSignal
    - Confirmation: DonchianBreakoutSignal
    - Volume confirmation: VolumeSpikeExhaustionSignal (will often be neutral; used to prefer stronger breakouts)
    - Exit: AtrTrailingStopReversalSignal

    Combiner: default weighted_vote
    always_active: False
    """
    signals = [
        KeltnerSqueezeBreakoutSignal(
            ema_len=20, atr_len=14, atr_mult=1.5,
            squeeze_bb_len=20, squeeze_bb_std=2.0, squeeze_thresh=1.0, min_squeeze_bars=5,
        ),
        DonchianBreakoutSignal(breakout_len=20, pullback_len=5, confirm_close=True),
        VolumeSpikeExhaustionSignal(vol_len=20, vol_spike_mult=2.0, range_len=20, range_spike_mult=2.0, proximity_ratio=0.2),
        AtrTrailingStopReversalSignal(atr_len=14, atr_mult=3.0, method='chandelier'),
    ]
    return CompositeStrategy(signals=signals, combiner=weighted_vote, always_active=False)
