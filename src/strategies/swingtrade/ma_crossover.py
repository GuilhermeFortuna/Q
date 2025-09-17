from __future__ import annotations

from typing import Union, Callable

from src.backtester import TradingStrategy, TradeOrder
from src.strategies import CompositeStrategy
from src.strategies.signals import MaCrossoverSignal


class MaCrossover(TradingStrategy):
    """
    Backward-compatible wrapper around the new composable signals architecture.

    This class preserves the original MaCrossover public API (constructor and
    method signatures) while internally delegating all logic to a
    CompositeStrategy using a single MaCrossoverSignal.

    Notes
    -----
    - Existing code that imports and instantiates MaCrossover will continue to
      work unchanged.
    - Indicator columns written to data['candle'].data remain identical to the
      original implementation to guarantee identical backtest results.
    """

    # Keep MA_FUNCS for backward compatibility in case external code references it
    # (the internal mapping is now handled by MaCrossoverSignal as well)
    MA_FUNCS = MaCrossoverSignal.MA_FUNCS

    def __init__(
        self,
        tick_value: float,
        short_ma_func: Callable = 'jma',
        long_ma_func: Callable = 'sma',
        short_ma_period: int = 9,
        long_ma_period: int = 12,
        delta_tick_factor: float = 1.0,
        always_active: bool = True,
    ) -> None:
        super().__init__()
        # Store attributes to preserve previous observable state
        self.tick_value = tick_value
        self.short_ma_func = short_ma_func
        self.long_ma_func = long_ma_func
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.delta_tick_factor = delta_tick_factor
        self.always_active = always_active

        # Internal composite strategy with a single MaCrossoverSignal
        self._signal = MaCrossoverSignal(
            tick_value=tick_value,
            short_ma_func=short_ma_func,
            long_ma_func=long_ma_func,
            short_ma_period=short_ma_period,
            long_ma_period=long_ma_period,
            delta_tick_factor=delta_tick_factor,
        )
        self.composite = CompositeStrategy(
            signals=[self._signal],
            always_active=always_active,
        )

    @staticmethod
    def buy_condition(
        ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
    ) -> bool:
        # Delegate to signal's condition to avoid logic drift
        return MaCrossoverSignal.buy_condition(
            ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
        )

    @staticmethod
    def sell_condition(
        ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
    ) -> bool:
        return MaCrossoverSignal.sell_condition(
            ma_delta, prior_ma_delta, delta_thresh, prior_delta_thresh
        )

    def compute_indicators(self, data: dict) -> None:
        # Delegate indicator computation to the composite (which calls the signal)
        self.composite.compute_indicators(data)

    def entry_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
        # Delegate decision-making to the composite strategy
        return self.composite.entry_strategy(i, data)

    def exit_strategy(
        self, i: int, data: dict, trade_info: dict
    ) -> Union[TradeOrder, None]:
        return self.composite.exit_strategy(i, data, trade_info)
