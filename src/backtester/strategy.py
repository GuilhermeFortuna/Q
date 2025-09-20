from abc import ABC, abstractmethod
from typing import Union, Callable

import pandas_ta as pta

from src.backtester.trades import TradeOrder


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
    def exit_strategy(self, i: int, data: dict, trade_info) -> Union[TradeOrder, None]:
        pass
