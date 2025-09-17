from __future__ import annotations

from typing import Optional

import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import cross_up, cross_down, clamp01


class RsiMeanReversionSignal(TradingSignal):
    """
    RSI Mean-Reversion with Dynamic Bands

    Emits long when RSI crosses up from below lower_band and short when crosses down from above upper_band.
    Strength is scaled by how far the prior RSI was outside the band.
    """

    def __init__(self, length: int = 14, upper_band: int = 70, lower_band: int = 30,
                 band_smooth: Optional[int] = None, exit_mid: bool = False) -> None:
        self.length = int(length)
        self.upper_band = float(upper_band)
        self.lower_band = float(lower_band)
        self.band_smooth = int(band_smooth) if band_smooth else None
        self.exit_mid = bool(exit_mid)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        candles['rsi'] = pta.rsi(candles['close'], length=self.length)
        if self.band_smooth:
            candles['rsi_ema'] = pta.ema(candles['rsi'], length=self.band_smooth)

    def _r(self, candle, i: int) -> float:
        try:
            if hasattr(candle, 'rsi_ema'):
                return float(candle.rsi_ema[i])
            return float(candle.rsi[i])
        except Exception:
            return 50.0

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i <= 0:
            return SignalDecision()
        candle = data['candle']
        r = self._r(candle, i)
        r_prev = self._r(candle, i - 1)
        info = {
            'rsi': float(getattr(candle, 'rsi')[i]) if hasattr(candle, 'rsi') else None,
            'rsi_prev': float(getattr(candle, 'rsi')[i-1]) if hasattr(candle, 'rsi') and i>0 else None,
            'upper': self.upper_band,
            'lower': self.lower_band,
        }
        # Cross up from below lower
        if r_prev <= self.lower_band and r > self.lower_band:
            strength = clamp01((self.lower_band - r_prev) / max(1e-9, self.lower_band))
            return SignalDecision(side='long', strength=strength, info=info)
        # Cross down from above upper
        if r_prev >= self.upper_band and r < self.upper_band:
            strength = clamp01((r_prev - self.upper_band) / max(1e-9, 100.0 - self.upper_band))
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
