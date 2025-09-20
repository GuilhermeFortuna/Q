import datetime as dt
import multiprocessing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Generator
from typing import Optional

import numpy as np
import pandas as pd

from src.backtester.data import MarketData, CandleData, TickData
from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeRegistry, TradeOrder
from src.bridge import data_manager


@dataclass
class BacktestParameters:
    """
    Dataclass for backtest parameters.
    """

    point_value: float
    cost_per_trade: float
    permit_swingtrade: bool = False
    entry_time_limit: Optional[dt.time] = None
    exit_time_limit: Optional[dt.time] = None
    max_trade_day: Optional[int] = None
    bypass_first_exit_check: bool = False

    def __post_init__(self):

        if not isinstance(self.point_value, float):
            raise TypeError('point_value must be a float.')

        if not isinstance(self.cost_per_trade, float):
            raise TypeError('cost_per_trade must be a float.')

        if not isinstance(self.permit_swingtrade, bool):
            raise TypeError('permit_swingtrade must be a bool.')

        if self.entry_time_limit is not None and not isinstance(
            self.entry_time_limit, dt.time
        ):
            raise TypeError('entry_time_limit must be a datetime.time.')

        if self.exit_time_limit is not None and not isinstance(
            self.exit_time_limit, dt.time
        ):
            raise TypeError('exit_time_limit must be a datetime.time.')

        if self.max_trade_day is not None and not isinstance(self.max_trade_day, int):
            raise TypeError('max_trade_day must be an int.')

        if not isinstance(self.bypass_first_exit_check, bool):
            raise TypeError('bypass_first_exit_check must be a bool.')


@dataclass
class EngineDataChunk:
    name: str
    date: dt.date
    data: np.ndarray


class EngineData(ABC):
    def __init__(self, data_obj: MarketData):
        if not issubclass(data_obj.__class__, MarketData):
            raise TypeError('data must be an instance of a subclass of MarketData.')
        elif data_obj.data is None or not isinstance(data_obj.data, pd.DataFrame):
            raise ValueError('data must be a pandas DataFrame.')

        self.symbol = data_obj.symbol
        self.data = data_obj.data
        self._dtype_map = None

    def prepare(self, data: Optional[pd.DataFrame] = None) -> np.ndarray:
        df = self.data if data is None else data
        arr = np.zeros(shape=(len(df),), dtype=self.dtype_map)
        for col, dtype in self.dtype_map:
            if col == 'datetime':
                if 'datetime' in df.columns:
                    arr[col] = df['datetime'].astype('int64').to_numpy()
                else:
                    # datetime as index
                    arr[col] = df.index.view('int64')
            else:
                arr[col] = df[col].astype(dtype).to_numpy()
        return arr

    @abstractmethod
    def compartmentalize(self) -> Generator:
        raise NotImplementedError


class EngineCandleData(EngineData):
    NAME = 'candle'

    def __init__(self, data_obj: CandleData):
        super().__init__(data_obj=data_obj)
        self.timeframe = data_obj.timeframe
        self.dtype_map = [
            (col, 'float64') if col != 'datetime' else (col, 'int64')
            for col in self.data.reset_index().columns
        ]

    def set_values_as_attrs(self) -> None:
        self.datetime_index = self.data.index.copy()
        self.index = np.array(range(len(self.datetime_index)), dtype='int64')
        for col in self.data.columns:
            setattr(self, col, self.data[col].values)

    def compartmentalize(self) -> Generator:
        if self.data is None:
            raise ValueError(
                'No data to compartmentalize. Load data to OHLCData.data first.'
            )

        for dt, data in self.data.groupby(self.data.index.date):
            inst = self.__class__(
                CandleData(symbol=self.symbol, timeframe=self.timeframe, data=data)
            )
            yield inst


class EngineTickData(EngineData):
    NAME = 'tick'

    def __init__(self, data_obj: TickData):
        super().__init__(data_obj=data_obj)
        self.dtype_map = [
            (col, 'float64') if col != 'datetime' else (col, 'int64')
            for col in self.data.columns
        ]

    def compartmentalize(self):
        if 'datetime' in self.data.columns:
            grouped = self.data.groupby(self.data['datetime'].dt.date)
        else:
            grouped = self.data.groupby(self.data.index.date)
        for date, group in grouped:
            yield EngineDataChunk(name='tick', date=date, data=self.prepare(data=group))


class Engine:
    DATA_TYPES = {
        'candle': EngineCandleData,
        'tick': EngineTickData,
    }

    def __init__(
        self,
        parameters: BacktestParameters,
        strategy: TradingStrategy,
        data: dict,
    ):
        if not isinstance(parameters, BacktestParameters):
            raise TypeError('parameters must be an instance of BacktestParameters.')

        if not isinstance(strategy, TradingStrategy):
            raise TypeError('strategy must be an instance of TradingStrategy.')

        self.parameters = parameters
        self.strategy = strategy
        self.trades = TradeRegistry(
            point_value=parameters.point_value, cost_per_trade=parameters.cost_per_trade
        )

        # Handle data
        if data == {}:
            raise ValueError(
                'Engine received empty data dictionary. Please provide data to run backtest.'
            )

        self.data = {}

        for name, data_obj in data.items():
            if name not in Engine.DATA_TYPES:
                raise ValueError(
                    f'Invalid data type: {name}. Valid data types are: {list(Engine.DATA_TYPES.keys())}'
                )
            if isinstance(data_obj, EngineData):
                self.data[name] = data_obj
            else:
                self.data[name] = Engine.DATA_TYPES[name](data_obj)

    '''
    def run_backtest(self, distributed: bool = False, **kwargs) -> None:
        from tqdm import tqdm

        if distributed:

            # Get data generators
            candle_data_generator = self.candles.compartmentalize() if self.candles is not None else None
            tick_data_generator = self.ticks.compartmentalize() if self.ticks is not None else None

            # Create pool of workers
            pool = multiprocessing.Pool(
                multiprocessing.cpu_count() if 'num_workers' not in kwargs else kwargs['num_workers']
            )

            #
            try:
                results = []
                #for result in tqdm(pool.imap())

            finally:
                pool.close()
                pool.join()

        else:
            raise NotImplementedError('Distributed backtesting is not yet implemented.')
    '''

    @staticmethod
    def manage_backtest_execution(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            use_multiprocessing = kwargs.pop('use_multiprocessing', False)
            kwargs.pop('num_processes', None)
            if use_multiprocessing:
                raise NotImplementedError('Multiprocessing is not yet implemented.')
            self.strategy.compute_indicators(self.data)
            self.data['candle'].set_values_as_attrs()
            return func(self, *args, **kwargs)

        return wrapper

    @manage_backtest_execution
    def run_backtest(self, display_progress: bool = False) -> None:
        from tqdm import tqdm

        candle = self.data['candle']
        n = len(candle.data)
        if n < 2:
            # nothing to iterate; still ensure final close if any open trade
            if self.trades.open_trade_info is not None and n > 0:
                self.trades._close_position(
                    price=candle.close[0],
                    datetime_val=candle.datetime_index[0],
                    comment='Insufficient data to continue. Closing open trade.',
                )
            data_manager.set_backtest_results(self.trades)
            return self.trades

        index = np.arange(n, dtype='int64')
        pbar = (
            tqdm(total=n - 1, desc='Running backtest', colour='yellow')
            if display_progress
            else None
        )

        last_idx = 0
        for i in index[1:]:
            last_idx = i

            if self.trades.open_trade_info is None:
                order = self.strategy.entry_strategy(i, self.data)
                if isinstance(order, TradeOrder):
                    self.trades.register_order(order)

            if self.trades.open_trade_info is not None:
                order = self.strategy.exit_strategy(
                    i, self.data, trade_info=self.trades.open_trade_info
                )
                if isinstance(order, TradeOrder):
                    self.trades.register_order(order)

            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

        if self.trades.open_trade_info is not None:
            self.trades._close_position(
                price=candle.close[last_idx],
                datetime_val=candle.datetime_index[last_idx],
                comment='No more data to process. Closing open trade.',
            )

        data_manager.set_backtest_results(self.trades)
        return self.trades


if __name__ == '__main__':
    pass
