from __future__ import annotations

from typing import Callable, Optional

import pandas_ta as pta

from src.strategies.signals.base import TradingSignal, SignalDecision


class MaCrossoverSignal(TradingSignal):
    """
    Moving Average Crossover as a composable TradingSignal.

    Reuses the indicator computation from the original MaCrossover strategy and
    emits a SignalDecision when a crossover (with threshold) occurs.

    Parameters
    ----------
    tick_value : float
        Tick value of the instrument (used to scale the delta threshold).
    short_ma_func : str
        Key for the short MA function (e.g., 'ema', 'sma', 'jma', ...).
    long_ma_func : str
        Key for the long MA function (e.g., 'ema', 'sma', 'jma', ...).
    short_ma_period : int
        Period for the short moving average.
    long_ma_period : int
        Period for the long moving average.
    delta_tick_factor : float
        Multiplier for the threshold in ticks.
    """

    MA_FUNCS = {
        'sma': pta.sma,
        'ema': pta.ema,
        'dema': pta.dema,
        'jma': pta.jma,
        't3': pta.t3,
        'trima': pta.trima,
        'fwma': pta.fwma,
    }

    def __init__(
        self,
        tick_value: float,
        short_ma_func: Callable | str = 'jma',
        long_ma_func: Callable | str = 'sma',
        short_ma_period: int = 9,
        long_ma_period: int = 12,
        delta_tick_factor: float = 1.0,
    ) -> None:
        self.tick_value = tick_value
        # Keep compatibility with existing string keys
        self.short_ma_func = (
            self.MA_FUNCS[short_ma_func]
            if isinstance(short_ma_func, str)
            else short_ma_func
        )
        self.long_ma_func = (
            self.MA_FUNCS[long_ma_func]
            if isinstance(long_ma_func, str)
            else long_ma_func
        )
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.delta_tick_factor = delta_tick_factor

    @staticmethod
    def buy_condition(
        ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
    ) -> bool:
        return prior_ma_delta <= prior_delta_thresh and ma_delta > delta_thresh

    @staticmethod
    def sell_condition(
        ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
    ) -> bool:
        return prior_ma_delta >= -prior_delta_thresh and ma_delta < -delta_thresh

    # Reuse the same indicator computation as the original strategy
    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data

        # Compute moving averages
        candles['short_ma'] = self.short_ma_func(
            candles['close'], length=self.short_ma_period
        )
        candles['long_ma'] = self.long_ma_func(
            candles['close'], length=self.long_ma_period
        )
        candles['ma_delta'] = candles['short_ma'] - candles['long_ma']
        candles['delta_thresh'] = self.tick_value * self.delta_tick_factor

    def generate(self, i: int, data: dict) -> SignalDecision:
        candle = data['candle']

        if i <= 0:
            return SignalDecision(side=None, strength=0.0, info={})

        close = float(candle.close[i])
        ma_delta = float(candle.ma_delta[i])
        prior_ma_delta = float(candle.ma_delta[i - 1])
        delta_thresh = float(candle.delta_thresh[i])
        prior_delta_thresh = float(candle.delta_thresh[i - 1])

        info = {
            'close': close,
            'ma_delta': ma_delta,
            'prior_ma_delta': prior_ma_delta,
            'delta_thresh': delta_thresh,
            'prior_delta_thresh': prior_delta_thresh,
        }

        # Buy conditions
        if self.buy_condition(
            ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
        ):
            return SignalDecision(side='long', strength=1.0, info=info)

        # Sell conditions
        if self.sell_condition(
            ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
        ):
            return SignalDecision(side='short', strength=1.0, info=info)

        return SignalDecision(side=None, strength=0.0, info=info)
