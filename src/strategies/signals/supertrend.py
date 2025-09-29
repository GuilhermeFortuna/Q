from __future__ import annotations

import pandas as pd
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import ensure_atr, norm_by_atr


class SupertrendFlipSignal(TradingSignal):
    """
    Supertrend Flip signal.

    Emits long when Supertrend direction flips from -1 to +1, short when flips from +1 to -1.
    Strength scales with distance of close from the supertrend line normalized by ATR.
    """

    def __init__(self, atr_length: int = 10, atr_mult: float = 3.0) -> None:
        self.atr_length = int(atr_length)
        self.atr_mult = float(atr_mult)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        st: pd.DataFrame = pta.supertrend(
            candles['high'], candles['low'], candles['close'], length=self.atr_length, multiplier=self.atr_mult
        )
        # Standardize: line and dir
        # pandas_ta returns columns like [SUPERT, SUPERTd]
        if st is not None and len(st.columns) >= 2:
            # Find main line and direction by name
            line_col = [c for c in st.columns if 'SUPERT' in c and not c.endswith('d')]
            dir_col = [c for c in st.columns if 'SUPERTd' in c]
            if line_col:
                candles['st_line'] = st[line_col[0]]
            else:
                candles['st_line'] = st[st.columns[0]]
            if dir_col:
                candles['st_dir'] = st[dir_col[0]]
            else:
                candles['st_dir'] = st[st.columns[1]]
        ensure_atr(data, length=self.atr_length, col='atr')

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i <= 0:
            return SignalDecision()
        c = data['candle']
        try:
            d_prev = float(c.st_dir[i - 1])
            d_now = float(c.st_dir[i])
            line = float(c.st_line[i])
            close = float(c.close[i])
        except Exception:
            return SignalDecision()
        info = {'st_dir': d_now, 'st_line': line, 'close': close}
        if d_prev == -1 and d_now == 1:
            strength = norm_by_atr(c, i, close - line, atr_col='atr')
            return SignalDecision(side='long', strength=strength, info=info)
        if d_prev == 1 and d_now == -1:
            strength = norm_by_atr(c, i, line - close, atr_col='atr')
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
