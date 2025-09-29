from __future__ import annotations

import pandas as pd
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01, ensure_atr


class MtfMaAlignmentFilter(TradingSignal):
    """
    Multi-Timeframe MA Alignment filter.

    Uses higher timeframe MA aligned to lower timeframe index. If no higher timeframe data is provided,
    falls back to applying a longer MA on the lower timeframe series.
    """

    def __init__(self, ht_ma_len: int = 50, lt_ma_len: int = 20, alignment_mode: str = 'ht_only', cap: float = 0.4) -> None:
        self.ht_ma_len = int(ht_ma_len)
        self.lt_ma_len = int(lt_ma_len)
        self.alignment_mode = str(alignment_mode)
        self.cap = float(cap)

    def compute_indicators(self, data: dict) -> None:
        lt = data['candle'].data
        lt['lt_ma'] = pta.ema(lt['close'], length=self.lt_ma_len)
        # Try to fetch higher timeframe candle data
        ht_ma_on_lt = None
        if 'ht_candle' in data and hasattr(data['ht_candle'], 'data'):
            ht = data['ht_candle'].data
            if isinstance(ht.index, pd.DatetimeIndex) and isinstance(lt.index, pd.DatetimeIndex):
                ht_ma = pta.ema(ht['close'], length=self.ht_ma_len)
                # Merge-asof to align ht_ma to lt index
                df_ht = pd.DataFrame({'ht_ma': ht_ma})
                df_ht = df_ht.sort_index()
                df_lt = pd.DataFrame(index=lt.index).sort_index()
                aligned = pd.merge_asof(df_lt.reset_index(), df_ht.reset_index(), left_on='index', right_on='index', direction='backward')
                aligned.index = df_lt.index
                ht_ma_on_lt = aligned['ht_ma']
        if ht_ma_on_lt is None:
            # Fallback: approximate using longer MA on LT
            lt['ht_ma'] = pta.ema(lt['close'], length=self.ht_ma_len)
        else:
            lt['ht_ma'] = ht_ma_on_lt.values
        ensure_atr(data, length=14, col='atr')

    def generate(self, i: int, data: dict) -> SignalDecision:
        c = data['candle']
        try:
            close = float(c.close[i])
            ht_ma = float(c.ht_ma[i])
            lt_ma = float(c.lt_ma[i])
            atr = float(c.atr[i]) if hasattr(c, 'atr') else None
        except Exception:
            return SignalDecision()
        info = {'close': close, 'ht_ma': ht_ma, 'lt_ma': lt_ma}
        if close > ht_ma and (self.alignment_mode != 'ht_and_lt' or lt_ma > ht_ma):
            dist = (close - ht_ma) / max(1e-9, atr) if atr else abs(close - ht_ma)
            strength = clamp01(min(self.cap, dist))
            return SignalDecision(side='long', strength=strength, info=info)
        if close < ht_ma and (self.alignment_mode != 'ht_and_lt' or lt_ma < ht_ma):
            dist = (ht_ma - close) / max(1e-9, atr) if atr else abs(ht_ma - close)
            strength = clamp01(min(self.cap, dist))
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
