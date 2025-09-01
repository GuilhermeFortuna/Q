from abc import ABC, abstractmethod
from typing import Union, Callable

import pandas_ta as pta

from backtester.trades import TradeOrder


class TradingStrategy(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def compute_indicators(self, data: dict) -> None:
        pass

    @abstractmethod
    def entry_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
        pass

    @abstractmethod
    def exit_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
        pass

class MaCrossover(TradingStrategy):
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
            short_ma_func: Callable = 'jma',
            long_ma_func: Callable = 'sma',
            short_ma_period: int = 9,
            long_ma_period: int = 12,
            delta_tick_factor: float = 1.0,
            always_active: bool = True,
    ):
        super().__init__()
        self.tick_value = tick_value
        self.short_ma_func = self.MA_FUNCS[short_ma_func]
        self.long_ma_func = self.MA_FUNCS[long_ma_func]
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.delta_tick_factor = delta_tick_factor
        self.always_active = always_active

    @staticmethod
    def buy_condition(ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh) -> bool:
        return prior_ma_delta <= prior_delta_thresh and ma_delta > delta_thresh

    @staticmethod
    def sell_condition(ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh) -> bool:
        return prior_ma_delta >= -prior_delta_thresh and ma_delta < -delta_thresh

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data

        # Compute moving averages
        candles['short_ma'] = self.short_ma_func(candles['close'], length=self.short_ma_period)
        candles['long_ma'] = self.long_ma_func(candles['close'], length=self.long_ma_period)
        candles['ma_delta'] = candles['short_ma'] - candles['long_ma']
        candles['delta_thresh'] = self.tick_value * self.delta_tick_factor

    def entry_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
        candle = data['candle']
        datetime = data['candle'].datetime_index[i]
        order = None

        if i > 0:
            close = candle.close[i]
            ma_delta = candle.ma_delta[i]
            prior_ma_delta = candle.ma_delta[i - 1]
            delta_thresh = candle.delta_thresh[i]
            prior_delta_thresh = candle.delta_thresh[i - 1]

            # Buy conditions
            if self.buy_condition(
                    ma_delta,
                    prior_ma_delta,
                    delta_thresh,
                    prior_delta_thresh
            ):
                order = TradeOrder(type='buy', price=close, datetime=datetime, amount=1)

            # Sell conditions
            elif self.sell_condition(
                ma_delta,
                prior_ma_delta,
                delta_thresh,
                prior_delta_thresh,
            ):
                order = TradeOrder(type='sell', price=close, datetime=datetime, amount=1)

        return order

    def exit_strategy(self, i: int, data: dict, trade_info: dict) -> Union[TradeOrder, None]:
        candle = data['candle']
        datetime = data['candle'].datetime_index[i]
        order = None

        close = candle.close[i]
        ma_delta = candle.ma_delta[i]
        prior_ma_delta = candle.ma_delta[i - 1]
        delta_thresh = candle.delta_thresh[i]
        prior_delta_thresh = candle.delta_thresh[i - 1]

        # Conditions to exit long position
        if trade_info['type'] == 'buy':
            if self.always_active and self.sell_condition(
                    ma_delta,
                    prior_ma_delta,
                    delta_thresh,
                    prior_delta_thresh
            ):
                order = TradeOrder(type='invert', price=close, datetime=datetime, amount=1)

            elif not self.always_active and ma_delta < delta_thresh:
                order = TradeOrder(type='close', price=close, datetime=datetime, amount=1)

        # Conditions to exit short position
        elif trade_info['type'] == 'sell':
            if self.always_active and self.buy_condition(
                    ma_delta,
                    prior_ma_delta,
                    delta_thresh,
                    prior_delta_thresh
            ):
                order = TradeOrder(type='invert', price=close, datetime=datetime, amount=1)

            elif not self.always_active and ma_delta > delta_thresh:
                order = TradeOrder(type='close', price=close, datetime=datetime, amount=1)

        return order
