from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision


class BollingerBandSignal(TradingSignal):
    """
    Bollinger Bands signal.

    Emits:
    - long when close < lower band
    - short when close > upper band

    Parameters
    ----------
    length : int
        Rolling window length for the middle band (moving average).
    std : float
        Standard deviation multiplier for band distance.
    mamode : Optional[str]
        Moving average mode for pandas-ta (e.g., 'sma', 'ema'). Defaults to library default when None.
    """

    def __init__(self, length: int = 20, std: float = 2.0, mamode: Optional[str] = None) -> None:
        self.length = length
        self.std = float(std)
        self.mamode = mamode

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        bb: pd.DataFrame = pta.bbands(
            candles['close'], length=self.length, std=self.std, mamode=self.mamode
        )
        # Expect columns like BBL_<len>_<std>, BBM_<len>_<std>, BBU_<len>_<std>
        # Merge and standardize column names
        candles[['bb_lower', 'bb_middle', 'bb_upper']] = bb[[bb.columns[0], bb.columns[1], bb.columns[2]]]
        # Precompute band width to help strength calculation
        candles['bb_width'] = candles['bb_upper'] - candles['bb_lower']

    def generate(self, i: int, data: dict) -> SignalDecision:
        candle = data['candle']
        if i < 0:
            return SignalDecision()

        close = float(candle.close[i])
        lower = float(candle.bb_lower[i])
        upper = float(candle.bb_upper[i])
        width = float(candle.bb_width[i]) if hasattr(candle, 'bb_width') else max(1e-9, float(upper - lower))

        info = {'close': close, 'bb_lower': lower, 'bb_upper': upper, 'bb_width': width}

        if close < lower:
            # Normalize distance to width as a rough strength proxy
            strength = min(1.0, (lower - close) / width) if width > 0 else 1.0
            return SignalDecision(side='long', strength=strength, info=info)
        elif close > upper:
            strength = min(1.0, (close - upper) / width) if width > 0 else 1.0
            return SignalDecision(side='short', strength=strength, info=info)
        else:
            return SignalDecision(side=None, strength=0.0, info=info)
