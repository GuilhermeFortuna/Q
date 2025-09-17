from __future__ import annotations

import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision


class ChoppinessRegimeFilter(TradingSignal):
    """
    Choppiness Index Regime Filter.

    Emits neutral decisions with regime info. Optionally, if baseline_ma_len is set, emits a weak bias
    following the price relative to the baseline in trend regimes.
    """

    def __init__(self, length: int = 14, chop_low: float = 38.0, chop_high: float = 62.0,
                 baseline_ma_len: int | None = None) -> None:
        self.length = int(length)
        self.chop_low = float(chop_low)
        self.chop_high = float(chop_high)
        self.baseline_ma_len = int(baseline_ma_len) if baseline_ma_len else None

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        candles['choppiness'] = pta.chop(candles['high'], candles['low'], candles['close'], length=self.length)
        if self.baseline_ma_len:
            candles['base_ma'] = pta.ema(candles['close'], length=self.baseline_ma_len)

    def generate(self, i: int, data: dict) -> SignalDecision:
        c = data['candle']
        try:
            chop = float(c.choppiness[i])
        except Exception:
            return SignalDecision()
        trend = chop < self.chop_low
        range_ = chop > self.chop_high
        info = {'choppiness': chop, 'trend': trend, 'range': range_}
        # Default neutral
        if not self.baseline_ma_len or not trend:
            return SignalDecision(side=None, strength=0.0, info=info)
        # Weak bias following baseline when trending
        try:
            close = float(c.close[i])
            base = float(c.base_ma[i])
        except Exception:
            return SignalDecision(side=None, strength=0.0, info=info)
        if close > base:
            return SignalDecision(side='long', strength=0.2, info=info)
        elif close < base:
            return SignalDecision(side='short', strength=0.2, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
