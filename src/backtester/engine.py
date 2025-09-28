import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Generator
from typing import Optional

import numpy as np
import pandas as pd

from src.data import MarketData, CandleData, TickData
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
        self._dtype_map = []

    @property
    def dtype_map(self):
        return self._dtype_map

    @dtype_map.setter
    def dtype_map(self, value):
        self._dtype_map = value

    def prepare(self, data: Optional[pd.DataFrame] = None) -> np.ndarray:
        df = self.data if data is None else data
        arr = np.zeros(shape=(len(df),), dtype=self.dtype_map)
        for col, dtype in self.dtype_map:
            if col == 'datetime':
                if 'datetime' in df.columns:
                    arr[col] = pd.to_datetime(df['datetime']).astype('int64').to_numpy()
                else:
                    # datetime as index
                    idx = pd.DatetimeIndex(df.index)
                    arr[col] = idx.view('int64')
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
        # Always include datetime field explicitly; assume timeline is the index
        self.dtype_map = [('datetime', 'int64')] + [
            (col, 'float64') for col in self.data.columns
        ]

    def set_values_as_attrs(self) -> None:
        # Ensure sorted timeline and standardized pandas.DatetimeIndex
        if isinstance(self.data.index, pd.DatetimeIndex):
            if not self.data.index.is_monotonic_increasing:
                self.data = self.data.sort_index()
            dt_index = pd.DatetimeIndex(self.data.index.copy())
        else:
            # If index is not datetime, try to use a datetime column
            if 'datetime' in self.data.columns:
                if not pd.Series(self.data['datetime']).is_monotonic_increasing:
                    self.data = self.data.sort_values('datetime')
                dt_index = pd.DatetimeIndex(
                    pd.to_datetime(self.data['datetime'].values)
                )
            else:
                # fallback to creating a range index as timeline
                dt_index = pd.DatetimeIndex(pd.to_datetime(self.data.index))
        self.datetime_index = dt_index
        self.index = np.arange(len(self.datetime_index), dtype='int64')
        for col in self.data.columns:
            setattr(self, col, self.data[col].to_numpy())

    def compartmentalize(self) -> Generator:
        if self.data is None:
            raise ValueError(
                'No data to compartmentalize. Load data to OHLCData.data first.'
            )

        for dt_val, data in self.data.groupby(self.data.index.date):
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

    def set_values_as_attrs(self) -> None:
        """Expose numpy arrays for hot path to avoid pandas overhead."""
        # Sort by time to guarantee monotonic timeline
        if 'datetime' in self.data.columns:
            if not pd.Series(self.data['datetime']).is_monotonic_increasing:
                self.data = self.data.sort_values('datetime')
            dt_src = self.data['datetime']
        else:
            if (
                not isinstance(self.data.index, pd.DatetimeIndex)
                or not self.data.index.is_monotonic_increasing
            ):
                self.data = self.data.sort_index()
            dt_src = self.data.index
        # Standardize to pandas.DatetimeIndex for consistency with candles
        self.datetime_index = pd.DatetimeIndex(pd.to_datetime(dt_src))
        self.index = np.arange(len(self.data), dtype='int64')
        for col in self.data.columns:
            setattr(self, col, self.data[col].to_numpy())

    def compartmentalize(self):
        if 'datetime' in self.data.columns:
            day_index = pd.to_datetime(self.data['datetime']).dt.floor('D')
        else:
            day_index = pd.to_datetime(self.data.index).floor('D')
        grouped = self.data.groupby(day_index)
        for date, group in grouped:
            yield EngineDataChunk(
                name='tick', date=date.date(), data=self.prepare(data=group)
            )


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

    @staticmethod
    def manage_backtest_execution(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            use_multiprocessing = kwargs.pop('use_multiprocessing', False)
            kwargs.pop('num_processes', None)
            if use_multiprocessing:
                raise NotImplementedError('Multiprocessing is not yet implemented.')
            # Pre-compute indicators
            self.strategy.compute_indicators(self.data)
            # Prepare fast access for present data types
            if 'candle' in self.data and hasattr(
                self.data['candle'], 'set_values_as_attrs'
            ):
                self.data['candle'].set_values_as_attrs()
            if 'tick' in self.data and hasattr(
                self.data['tick'], 'set_values_as_attrs'
            ):
                self.data['tick'].set_values_as_attrs()
            return func(self, *args, **kwargs)

        return wrapper

    @manage_backtest_execution
    def run_backtest(
        self, display_progress: bool = False, primary: str = 'auto'
    ) -> TradeRegistry:
        from tqdm import tqdm

        # Decide the primary data timeline to iterate on
        if primary == 'auto':
            if 'candle' in self.data:
                primary_key = 'candle'
            elif 'tick' in self.data:
                primary_key = 'tick'
            else:
                raise ValueError('No supported data source found for backtest.')
        else:
            if primary not in self.data:
                raise ValueError(f'Primary data "{primary}" not found in Engine.data.')
            primary_key = primary

        # Candle-driven loop (default behaviour stays intact)
        if primary_key == 'candle':
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
                        i, self.data, self.trades.open_trade_info
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

        # Tick-driven loop (high granularity)
        tick = self.data['tick']
        n = len(tick.data)

        # Choose a price-like field for forced closes
        price_attr = next(
            (a for a in ('price', 'last', 'close', 'bid', 'ask') if hasattr(tick, a)),
            None,
        )
        if price_attr is None:
            raise ValueError(
                'Tick data must have a price-like column: price/last/close/bid/ask.'
            )
        price_arr = getattr(tick, price_attr)
        dt_arr = tick.datetime_index

        if n < 2:
            if self.trades.open_trade_info is not None and n > 0:
                # If both bid and ask exist, use mid for safety
                if hasattr(tick, 'bid') and hasattr(tick, 'ask'):
                    final_price = 0.5 * (tick.bid[0] + tick.ask[0])
                else:
                    final_price = price_arr[0]
                self.trades._close_position(
                    price=float(final_price),
                    datetime_val=dt_arr[0],
                    comment='Insufficient data to continue. Closing open trade.',
                )
            data_manager.set_backtest_results(self.trades)
            return self.trades

        pbar = (
            tqdm(total=n - 1, desc='Running tick backtest', colour='yellow')
            if display_progress
            else None
        )

        last_idx = 0
        for i in range(1, n):
            last_idx = i
            if self.trades.open_trade_info is None:
                order = self.strategy.entry_strategy(i, self.data)
                if isinstance(order, TradeOrder):
                    self.trades.register_order(order)
            if self.trades.open_trade_info is not None:
                order = self.strategy.exit_strategy(i, self.data)
                if isinstance(order, TradeOrder):
                    self.trades.register_order(order)
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

        if self.trades.open_trade_info is not None:
            if hasattr(tick, 'bid') and hasattr(tick, 'ask'):
                final_price = 0.5 * (tick.bid[last_idx] + tick.ask[last_idx])
            else:
                final_price = price_arr[last_idx]
            self.trades._close_position(
                price=float(final_price),
                datetime_val=dt_arr[last_idx],
                comment='No more data to process. Closing open trade.',
            )

        data_manager.set_backtest_results(self.trades)
        return self.trades


if __name__ == '__main__':
    pass
