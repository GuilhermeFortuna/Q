from typing import Type, Dict, Any

import optuna

from src.backtester.engine import Engine, BacktestParameters
from src.backtester.strategy import TradingStrategy


class Optimizer:
    """
    Manages the optimization of a trading strategy using Optuna.
    """

    def __init__(
        self,
        strategy_class: Type[TradingStrategy],
        config: Dict[str, Any],
        backtest_config: BacktestParameters,
    ):
        pass
