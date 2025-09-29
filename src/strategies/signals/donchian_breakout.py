from __future__ import annotations

import pandas as pd
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import ensure_atr, norm_by_atr, clamp01


class DonchianBreakoutSignal(TradingSignal):
    """
    Donchian Breakout with Pullback Confirmation.
    """

    def __init__(self, breakout_len: int = 20, pullback_len: int = 5, confirm_close: bool = True) -> None:
        self.breakout_len = int(breakout_len)
        self.pullback_len = int(pullback_len)
        self.confirm_close = bool(confirm_close)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        candles['donch_high'] = candles['high'].rolling(self.breakout_len).max()
        candles['donch_low'] = candles['low'].rolling(self.breakout_len).min()
        candles['pull_high'] = candles['high'].rolling(self.pullback_len).max()
        candles['pull_low'] = candles['low'].rolling(self.pullback_len).min()
        ensure_atr(data, length=max(14, self.breakout_len // 2), col='atr')

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i < max(self.breakout_len, self.pullback_len):
            return SignalDecision()
        c = data['candle']
        close = float(c.close[i])
        dh = float(c.donch_high[i - 1])  # compare against prior band to avoid lookahead
        dl = float(c.donch_low[i - 1])
        # Pullback proxy: within last pullback_len bars, price moved counter to breakout
        recent_low = float(c.pull_low[i - 1])
        recent_high = float(c.pull_high[i - 1])
        info = {'close': close, 'donch_high': dh, 'donch_low': dl, 'recent_low': recent_low, 'recent_high': recent_high}

        # Up breakout condition
        pullback_ok_up = recent_low < float(c.close[i - self.pullback_len]) if i >= self.pullback_len else True
        if (close > dh if self.confirm_close else float(c.high[i]) > dh) and pullback_ok_up:
            dist = close - dh
            strength = norm_by_atr(c, i, dist, atr_col='atr')
            return SignalDecision(side='long', strength=strength, info=info)

        # Down breakout condition
        pullback_ok_dn = recent_high > float(c.close[i - self.pullback_len]) if i >= self.pullback_len else True
        if (close < dl if self.confirm_close else float(c.low[i]) < dl) and pullback_ok_dn:
            dist = dl - close
            strength = norm_by_atr(c, i, dist, atr_col='atr')
            return SignalDecision(side='short', strength=strength, info=info)

        return SignalDecision(side=None, strength=0.0, info=info)
