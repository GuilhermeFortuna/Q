from __future__ import annotations

import pandas as pd
import numpy as np
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01


class KeltnerSqueezeBreakoutSignal(TradingSignal):
    """
    Keltner Channel Breakout with Bollinger Band Squeeze filter.
    """

    def __init__(self,
                 ema_len: int = 20,
                 atr_len: int = 14,
                 atr_mult: float = 1.5,
                 squeeze_bb_len: int = 20,
                 squeeze_bb_std: float = 2.0,
                 squeeze_thresh: float = 1.0,
                 min_squeeze_bars: int = 5) -> None:
        self.ema_len = int(ema_len)
        self.atr_len = int(atr_len)
        self.atr_mult = float(atr_mult)
        self.squeeze_bb_len = int(squeeze_bb_len)
        self.squeeze_bb_std = float(squeeze_bb_std)
        self.squeeze_thresh = float(squeeze_thresh)
        self.min_squeeze_bars = int(min_squeeze_bars)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        kc: pd.DataFrame = pta.kc(
            candles['high'], candles['low'], candles['close'],
            length=self.ema_len, scalar=self.atr_mult, mamode='ema', atr_length=self.atr_len
        )
        # Expect KCLe, KCBm, KCCe or similar - standardize to kc_lower, ema_mid, kc_upper
        if kc is not None and len(kc.columns) >= 3:
            # Try by name first; fallback by order
            lower_col = next((c for c in kc.columns if c.lower().startswith('kcl')), kc.columns[0])
            mid_col = next((c for c in kc.columns if c.lower().startswith('kcb')), kc.columns[1])
            upper_col = next((c for c in kc.columns if c.lower().startswith('kcu')), kc.columns[2])
            candles['kc_lower'] = kc[lower_col]
            candles['ema_mid'] = kc[mid_col]
            candles['kc_upper'] = kc[upper_col]
        bb: pd.DataFrame = pta.bbands(candles['close'], length=self.squeeze_bb_len, std=self.squeeze_bb_std)
        if bb is not None and len(bb.columns) >= 3:
            candles['bb_lower'] = bb[bb.columns[0]]
            candles['bb_middle'] = bb[bb.columns[1]]
            candles['bb_upper'] = bb[bb.columns[2]]
        # squeeze metric: BB width / KC width
        kc_width = (candles['kc_upper'] - candles['kc_lower']).replace(0.0, np.nan)
        bb_width = (candles['bb_upper'] - candles['bb_lower'])
        candles['squeeze_metric'] = bb_width / kc_width
        # rolling count of squeeze condition
        cond = candles['squeeze_metric'] < self.squeeze_thresh
        candles['squeeze_count'] = cond.rolling(self.min_squeeze_bars).sum()

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i < max(self.ema_len, self.squeeze_bb_len, self.min_squeeze_bars):
            return SignalDecision()
        c = data['candle']
        try:
            sc = float(c.squeeze_count[i])
            close = float(c.close[i])
            ku = float(c.kc_upper[i])
            kl = float(c.kc_lower[i])
            kw = float(ku - kl)
            sm = float(c.squeeze_metric[i])
        except Exception:
            return SignalDecision()
        info = {'squeeze_count': sc, 'squeeze_metric': sm, 'kc_upper': ku, 'kc_lower': kl, 'close': close}
        active = sc >= self.min_squeeze_bars and np.isfinite(sm)
        if not active or kw <= 0:
            return SignalDecision(side=None, strength=0.0, info=info)
        # Breakouts
        if close > ku:
            base = (close - ku) / max(1e-9, kw)
            # Stronger if squeeze_metric smaller (tighter squeeze)
            squeeze_factor = clamp01(1.5 - clamp01(sm))  # sm<1 boosts, >1 reduces
            strength = clamp01(base * (0.5 + 0.5 * squeeze_factor))
            return SignalDecision(side='long', strength=strength, info=info)
        if close < kl:
            base = (kl - close) / max(1e-9, kw)
            squeeze_factor = clamp01(1.5 - clamp01(sm))
            strength = clamp01(base * (0.5 + 0.5 * squeeze_factor))
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
