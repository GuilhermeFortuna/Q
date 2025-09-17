from __future__ import annotations

import pandas as pd
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01


class MacdMomentumSignal(TradingSignal):
    """
    MACD Momentum State signal.
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, zero_line_bias: bool = True,
                 std_len: int = 50) -> None:
        self.fast = int(fast)
        self.slow = int(slow)
        self.signal = int(signal)
        self.zero_line_bias = bool(zero_line_bias)
        self.std_len = int(std_len)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        macd_df: pd.DataFrame = pta.macd(candles['close'], fast=self.fast, slow=self.slow, signal=self.signal)
        # Columns likely: MACD_{fast}_{slow}_{signal}, MACDh_{...}, MACDs_{...}
        cols = list(macd_df.columns)
        # Try to pick by name irrespective of order
        macd_col = next((c for c in cols if 'macd' in c.lower() and not c.lower().endswith('h') and not c.lower().endswith('s')), cols[0])
        signal_col = next((c for c in cols if c.lower().endswith('s')), cols[-1])
        hist_col = next((c for c in cols if c.lower().endswith('h')), cols[1 if len(cols) > 1 else 0])
        candles['macd'] = macd_df[macd_col]
        candles['macd_signal'] = macd_df[signal_col]
        candles['macd_hist'] = macd_df[hist_col]
        candles['macd_hist_std'] = candles['macd_hist'].rolling(self.std_len).std()

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i <= 0:
            return SignalDecision()
        c = data['candle']
        try:
            macd = float(c.macd[i])
            sig = float(c.macd_signal[i])
            hist = float(c.macd_hist[i])
            std = float(c.macd_hist_std[i]) if hasattr(c, 'macd_hist_std') else 0.0
        except Exception:
            return SignalDecision()
        info = {'macd': macd, 'signal': sig, 'hist': hist, 'hist_std': std}
        if macd > sig and (macd > 0 if self.zero_line_bias else True):
            base = abs(hist) / max(1e-9, std) if std and std > 0 else abs(hist)
            strength = clamp01(base)
            return SignalDecision(side='long', strength=strength, info=info)
        if macd < sig and (macd < 0 if self.zero_line_bias else True):
            base = abs(hist) / max(1e-9, std) if std and std > 0 else abs(hist)
            strength = clamp01(base)
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
