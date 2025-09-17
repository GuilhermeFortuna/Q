from __future__ import annotations

import pandas_ta as pta
from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.signals.helpers import clamp01


class AdxDmiSignal(TradingSignal):
    """
    ADX/DMI Trend Direction signal.

    Emits long if +DI > -DI with ADX >= threshold, short if -DI > +DI with ADX >= threshold.
    """

    def __init__(self, length: int = 14, adx_thresh: float = 25.0) -> None:
        self.length = int(length)
        self.adx_thresh = float(adx_thresh)

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        dmi = pta.adx(candles['high'], candles['low'], candles['close'], length=self.length)
        # pandas_ta returns [DMP, DMN, ADX] or [ADX, DMP, DMN] depending on version.
        # Choose by name if available, else by position.
        cols = list(dmi.columns)
        name_map = {c.lower(): c for c in cols}
        if any('adx' in c.lower() for c in cols):
            adx_col = [c for c in cols if 'adx' in c.lower()][0]
            dmp_col = [c for c in cols if 'dmp' in c.lower() or '+di' in c.lower() or 'pdi' in c.lower()][0]
            dmn_col = [c for c in cols if 'dmn' in c.lower() or '-di' in c.lower() or 'mdi' in c.lower()][0]
            candles['adx'] = dmi[adx_col]
            candles['di_plus'] = dmi[dmp_col]
            candles['di_minus'] = dmi[dmn_col]
        else:
            candles['adx'] = dmi[cols[0]]
            candles['di_plus'] = dmi[cols[1]]
            candles['di_minus'] = dmi[cols[2]]

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i < 1:
            return SignalDecision()
        c = data['candle']
        try:
            adx = float(c.adx[i])
            di_p = float(c.di_plus[i])
            di_m = float(c.di_minus[i])
        except Exception:
            return SignalDecision()
        info = {'adx': adx, '+DI': di_p, '-DI': di_m, 'thresh': self.adx_thresh}
        if not (adx >= self.adx_thresh):
            return SignalDecision(side=None, strength=0.0, info=info)
        if di_p > di_m:
            diff = clamp01((di_p - di_m) / 100.0)
            strength = clamp01(diff * (adx / max(self.adx_thresh, 1e-9)))
            return SignalDecision(side='long', strength=strength, info=info)
        elif di_m > di_p:
            diff = clamp01((di_m - di_p) / 100.0)
            strength = clamp01(diff * (adx / max(self.adx_thresh, 1e-9)))
            return SignalDecision(side='short', strength=strength, info=info)
        return SignalDecision(side=None, strength=0.0, info=info)
