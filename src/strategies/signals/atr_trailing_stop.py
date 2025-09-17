from __future__ import annotations

import pandas as pd
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import ensure_atr, norm_by_atr


class AtrTrailingStopReversalSignal(TradingSignal):
    """
    ATR Trailing Stop Reversal using chandelier-like trails.
    """

    def __init__(self, atr_len: int = 14, atr_mult: float = 3.0, method: str = 'chandelier') -> None:
        self.atr_len = int(atr_len)
        self.atr_mult = float(atr_mult)
        self.method = str(method)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        ensure_atr(data, length=self.atr_len, col='atr')
        if self.method == 'chandelier':
            highest = candles['high'].rolling(self.atr_len).max()
            lowest = candles['low'].rolling(self.atr_len).min()
            candles['trail_long'] = highest - self.atr_mult * candles['atr']
            candles['trail_short'] = lowest + self.atr_mult * candles['atr']
        else:
            # fallback to chandelier
            highest = candles['high'].rolling(self.atr_len).max()
            lowest = candles['low'].rolling(self.atr_len).min()
            candles['trail_long'] = highest - self.atr_mult * candles['atr']
            candles['trail_short'] = lowest + self.atr_mult * candles['atr']

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i <= 0:
            return SignalDecision()
        c = data['candle']
        try:
            close_prev = float(c.close[i - 1])
            close_now = float(c.close[i])
            tl = float(c.trail_long[i])
            ts = float(c.trail_short[i])
        except Exception:
            return SignalDecision()
        info = {'trail_long': tl, 'trail_short': ts, 'close': close_now}
        # Cross above short trail => long
        if close_prev <= ts and close_now > ts:
            strength = norm_by_atr(c, i, close_now - ts, atr_col='atr')
            return SignalDecision(side='long', strength=strength, info=info)
        # Cross below long trail => short
        if close_prev >= tl and close_now < tl:
            strength = norm_by_atr(c, i, tl - close_now, atr_col='atr')
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
