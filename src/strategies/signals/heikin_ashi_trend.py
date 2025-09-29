from __future__ import annotations

import pandas as pd
import numpy as np
import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01, rolling_streak


class HeikinAshiTrendContinuationSignal(TradingSignal):
    """
    Heikin-Ashi Trend Continuation signal.
    """

    def __init__(self, min_streak: int = 2, body_ratio_thresh: float = 0.6, wick_filter: bool = True) -> None:
        self.min_streak = int(min_streak)
        self.body_ratio_thresh = float(body_ratio_thresh)
        self.wick_filter = bool(wick_filter)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        ha: pd.DataFrame = pta.ha(candles['open'], candles['high'], candles['low'], candles['close'])
        # Standardize names
        candles['ha_open'] = ha[ha.columns[0]]
        candles['ha_high'] = ha[ha.columns[1]]
        candles['ha_low'] = ha[ha.columns[2]]
        candles['ha_close'] = ha[ha.columns[3]]
        # Derived metrics
        body = (candles['ha_close'] - candles['ha_open']).abs()
        tr = candles['ha_high'] - candles['ha_low']
        candles['ha_body_ratio'] = (body / tr).replace([np.inf, -np.inf], np.nan)
        candles['ha_color'] = np.where(candles['ha_close'] > candles['ha_open'], 1, -1)
        candles['ha_upper_wick'] = candles['ha_high'] - candles[['ha_close', 'ha_open']].max(axis=1)
        candles['ha_lower_wick'] = candles[['ha_close', 'ha_open']].min(axis=1) - candles['ha_low']
        candles['ha_tr'] = tr

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i < self.min_streak:
            return SignalDecision()
        c = data['candle']
        try:
            color = int(c.ha_color[i])
            body_ratio = float(c.ha_body_ratio[i])
            upper_w = float(c.ha_upper_wick[i])
            lower_w = float(c.ha_lower_wick[i])
            tr = float(c.ha_tr[i])
        except Exception:
            return SignalDecision()
        info = {'ha_color': color, 'ha_body_ratio': body_ratio, 'upper_wick': upper_w, 'lower_wick': lower_w}
        # Compute color change array proxy using real close-open difference
        try:
            diff_arr = data['candle'].ha_color
        except Exception:
            return SignalDecision()
        streak_up = rolling_streak(diff_arr, i, direction=+1)
        streak_dn = rolling_streak(diff_arr, i, direction=-1)
        if color == 1 and streak_up >= self.min_streak and (body_ratio >= self.body_ratio_thresh):
            if self.wick_filter and tr > 0 and (upper_w / tr) > 0.3:
                return SignalDecision(side=None, strength=0.0, info=info)
            # Strength scales with streak and body ratio
            strength = clamp01((streak_up / (self.min_streak + 2)) * clamp01(body_ratio))
            return SignalDecision(side='long', strength=strength, info=info)
        if color == -1 and streak_dn >= self.min_streak and (body_ratio >= self.body_ratio_thresh):
            if self.wick_filter and tr > 0 and (lower_w / tr) > 0.3:
                return SignalDecision(side=None, strength=0.0, info=info)
            strength = clamp01((streak_dn / (self.min_streak + 2)) * clamp01(body_ratio))
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
