from __future__ import annotations

import pandas as pd
import numpy as np

from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01, cross_up, cross_down


class VwapDeviationReversionSignal(TradingSignal):
    """
    VWAP Deviation Reversion (Intraday)

    Requires 'volume' column to compute VWAP. If not present, this signal remains neutral.
    """

    def __init__(self, std_len: int = 20, dev_mult: float = 2.0) -> None:
        self.std_len = int(std_len)
        self.dev_mult = float(dev_mult)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        # If volume missing, we can't compute VWAP; mark columns as NaN to keep downstream safe
        if 'volume' not in candles.columns:
            candles['vwap'] = np.nan
            candles['vwap_dev'] = np.nan
            candles['vwap_dev_std'] = np.nan
            return
        # Session id by date (assumes datetime index)
        if not isinstance(candles.index, pd.DatetimeIndex):
            idx_date = pd.to_datetime(candles.index)
        else:
            idx_date = candles.index
        session_id = idx_date.date
        candles['session_id'] = session_id
        tp = (candles['high'] + candles['low'] + candles['close']) / 3.0
        pv = tp * candles['volume']
        candles['cum_pv'] = pv.groupby(candles['session_id']).cumsum()
        candles['cum_vol'] = candles['volume'].groupby(candles['session_id']).cumsum()
        candles['vwap'] = candles['cum_pv'] / candles['cum_vol']
        candles['vwap_dev'] = candles['close'] - candles['vwap']
        candles['vwap_dev_std'] = candles['vwap_dev'].rolling(self.std_len).std()

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i <= 0:
            return SignalDecision()
        c = data['candle']
        try:
            dev = float(c.vwap_dev[i])
            dev_prev = float(c.vwap_dev[i - 1])
            std = float(c.vwap_dev_std[i])
        except Exception:
            return SignalDecision()
        thresh = self.dev_mult * (std if std and np.isfinite(std) else 0.0)
        info = {'vwap_dev': dev, 'dev_std': std, 'thresh': self.dev_mult}
        if std and std > 0 and np.isfinite(std):
            # Crosses back inside thresholds (contraction)
            if dev_prev <= -thresh and dev > -thresh:
                strength = clamp01(abs(dev) / max(1e-9, std))
                return SignalDecision(side='long', strength=strength, info=info)
            if dev_prev >= thresh and dev < thresh:
                strength = clamp01(abs(dev) / max(1e-9, std))
                return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
