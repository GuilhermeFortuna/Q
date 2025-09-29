from __future__ import annotations

import numpy as np
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01


class VolumeSpikeExhaustionSignal(TradingSignal):
    """
    Volume Spike Exhaustion Reversal.
    Requires 'volume' column to operate; otherwise remains neutral.
    """

    def __init__(self, vol_len: int = 20, vol_spike_mult: float = 2.0,
                 range_len: int = 20, range_spike_mult: float = 2.0,
                 proximity_ratio: float = 0.2) -> None:
        self.vol_len = int(vol_len)
        self.vol_spike_mult = float(vol_spike_mult)
        self.range_len = int(range_len)
        self.range_spike_mult = float(range_spike_mult)
        self.proximity_ratio = float(proximity_ratio)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        if 'volume' not in candles.columns:
            candles['vol_ma'] = np.nan
            candles['tr'] = np.nan
            candles['tr_ma'] = np.nan
            candles['vol_spike'] = False
            candles['tr_spike'] = False
            return
        candles['vol_ma'] = candles['volume'].rolling(self.vol_len).mean()
        tr = pta.true_range(candles['high'], candles['low'], candles['close'])
        candles['tr'] = tr
        candles['tr_ma'] = tr.rolling(self.range_len).mean()
        candles['vol_spike'] = candles['volume'] > (self.vol_spike_mult * candles['vol_ma'])
        candles['tr_spike'] = candles['tr'] > (self.range_spike_mult * candles['tr_ma'])

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i <= 0:
            return SignalDecision()
        c = data['candle']
        try:
            vol_spike = bool(c.vol_spike[i])
            tr_spike = bool(c.tr_spike[i])
            tr = float(c.tr[i])
            close = float(c.close[i])
            open_ = float(c.open[i])
            high = float(c.high[i])
            low = float(c.low[i])
            prev_close = float(c.close[i - 1])
            vol = float(c.volume[i]) if hasattr(c, 'volume') else np.nan
            vol_ma = float(c.vol_ma[i]) if hasattr(c, 'vol_ma') else np.nan
            tr_ma = float(c.tr_ma[i]) if hasattr(c, 'tr_ma') else np.nan
        except Exception:
            return SignalDecision()
        info = {
            'vol_spike': vol_spike, 'tr_spike': tr_spike, 'tr': tr, 'close': close,
            'vol': vol, 'vol_ma': vol_ma, 'tr_ma': tr_ma
        }
        if tr <= 0 or not (vol_spike and tr_spike):
            return SignalDecision(side=None, strength=0.0, info=info)
        # Proximity logic
        near_low = (close - low) / max(1e-9, tr) <= self.proximity_ratio
        near_high = (high - close) / max(1e-9, tr) <= self.proximity_ratio
        down_context = close < open_ or close < prev_close
        up_context = close > open_ or close > prev_close
        if near_low and down_context:
            # reversal up
            intensity = 0.5 * ((vol / max(1e-9, vol_ma)) + (tr / max(1e-9, tr_ma))) if vol_ma and tr_ma else 1.0
            prox = clamp01(1.0 - (close - low) / max(1e-9, tr))
            strength = clamp01(intensity * prox)
            return SignalDecision(side='long', strength=strength, info=info)
        if near_high and up_context:
            intensity = 0.5 * ((vol / max(1e-9, vol_ma)) + (tr / max(1e-9, tr_ma))) if vol_ma and tr_ma else 1.0
            prox = clamp01(1.0 - (high - close) / max(1e-9, tr))
            strength = clamp01(intensity * prox)
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
