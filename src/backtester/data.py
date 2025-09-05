import datetime as dt
import time
from abc import ABC, abstractmethod
from typing import Optional, Union
from src.backtester.utils import TIMEFRAMES

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from tqdm import tqdm


class MarketData(ABC):
    def __init__(self, symbol: str, data: Optional[pd.DataFrame] = None, **kwargs):
        if not isinstance(symbol, str):
            raise TypeError('symbol must be a string.')

        if data is not None and not isinstance(data, pd.DataFrame):
            raise TypeError('data must either be None or be a pandas DataFrame.')

        self.symbol = symbol
        self.data = data

    @abstractmethod
    def store_data(self) -> None:
        pass

    @abstractmethod
    def load_data(self) -> Optional[pd.DataFrame]:
        pass

    @staticmethod
    def connect_to_mt5(attempts: int = 3, wait: int = 2) -> bool:
        '''
        Attempt to connect to MT5 terminal.

        :param attempts: int. Number of attempts before failing.
        :param wait: int. Seconds to wait between attempts.
        :return: bool. True if connection was successful. False otherwise.
        '''

        num_attempts = 0

        # Attempt to establish a connection with MT5 terminal, if not already connected.
        if mt5.terminal_info() is None:
            while num_attempts < attempts:

                connection = mt5.initialize()

                if connection:
                    return True
                else:
                    num_attempts += 1
                    time.sleep(wait)

            raise ConnectionError(
                'Unable to establish a connection with the MT5 terminal. Check internet connection and try again.'
            )

        else:
            return True


class CandleData(MarketData):
    def __init__(
        self, symbol: str, timeframe: str, data: Optional[pd.DataFrame] = None
    ):
        super().__init__(symbol=symbol, data=data)
        if not isinstance(timeframe, str):
            raise TypeError(
                f'timeframe must be a string. Received obj of type: {type(timeframe)}'
            )

        self.timeframe = timeframe

    def store_data(self) -> None:
        pass

    def load_data(self) -> None:
        pass

    @staticmethod
    def format_candle_data_from_mt5(data: np.ndarray) -> pd.DataFrame:
        """
        Formats raw candle data obtained from MetaTrader 5 (MT5) into a structured
        pandas DataFrame. The function processes the input array, converts the
        time column into a datetime format, drops unnecessary columns, and sets
        the datetime column as the DataFrame index.

        :param data: The raw data as a NumPy ndarray containing candle information
                     from MT5. Data must include columns for 'time', 'spread',
                     and other relevant trading information.
        :type data: np.ndarray
        :return: A pandas DataFrame with the formatted candle data. The DataFrame
                 includes trading data indexed by datetime with specific columns
                 retained and unnecessary ones removed.
        :rtype: pd.DataFrame
        :raises ValueError: If no data is provided (None or empty array).
        """
        if data is not None:
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['time'], unit='s')
            df.drop(columns=['time', 'spread'], inplace=True)
            df.set_index('datetime', inplace=True, drop=True)
            return df

        else:
            raise ValueError('No data provided. Please provide data to format.')

    @staticmethod
    def import_from_mt5(
        mt5_symbol: str,
        timeframe: str,
        date_from: dt.datetime,
        date_to: dt.datetime,
    ):
        # Validate timeframe
        if not isinstance(timeframe, str) or timeframe not in TIMEFRAMES.keys():
            raise ValueError(f'Invalid timeframe: {timeframe}')

        # Initialize connection to mt5 terminal with default credentials
        mt5.initialize()

        try:
            df = CandleData.format_candle_data_from_mt5(
                data=mt5.copy_rates_range(
                    mt5_symbol, TIMEFRAMES[timeframe].mt5, date_from, date_to
                )
            )
        except:
            print(f'Error importing data for symbol {mt5_symbol} from MT5.')
            df = pd.DataFrame()

        finally:
            mt5.shutdown()

        return df

    @staticmethod
    def import_from_csv(path: str) -> Union[pd.DataFrame, None]:
        errors = []
        for enc in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv(path, decimal=',', encoding=enc)
                df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                df['datetime'] = pd.to_datetime(
                    df['datetime'], format='%d/%m/%Y %H:%M', errors='raise'
                )
                df = df.set_index('datetime', inplace=False)[::-1].copy()
                return df

            except Exception as e:
                errors.append(e)
                continue

        for error in errors:
            print(error)


class TickData(MarketData):
    DEFAULT_BATCH_IMPORT_STEP_DAYS = 15

    def __init__(self, symbol: str, data: Optional[pd.DataFrame] = None):
        super().__init__(symbol=symbol, data=data)

    def store_data(self) -> None:
        pass

    def load_data(self) -> None:
        pass

    def _format_ticks(self, data: np.ndarray) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df = df[['time', 'last', 'volume']].copy()
        df.rename(columns={'time': 'datetime', 'last': 'price'}, inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
        df.sort_index(inplace=True)
        return df.loc[~(df['price'] == 0)].copy()

    @staticmethod
    def generate_date_ranges(
        date_from: dt.datetime, date_to: dt.datetime, step_days: int
    ) -> list:
        """
        Divides a continuous datetime range into equal chunks based on the specified step_days.
        The function ensures each chunk contains evenly distributed timestamps covering
        the full range between `date_from` and `date_to`.

        :param date_from: The starting datetime of the range. Timestamps will
                          begin from midnight of this date.
        :param date_to: The ending datetime of the range. Timestamps will extend
                        until the last minute of this date.
        :param step_days: The number of days per division or approximate window size
                          for each chunk of datetime ranges.
        :return: A list of Pandas `DatetimeIndex` objects, where each element in the
                 list represents a chunk of datetime ranges.
        """
        import math

        df, dt = date_from.replace(hour=0, minute=0, second=0), date_to.replace(
            hour=23, minute=59, second=59
        )
        date_range = pd.date_range(df, dt)
        div = math.ceil(len(date_range) / step_days)
        step = math.ceil(len(date_range) / div)
        return [
            (
                date_range[i],
                (
                    date_range[i + step]
                    if (i + step) <= len(date_range) - 1
                    else date_range[-1]
                ),
            )
            for i in range(0, len(date_range) - 1, step)
        ]

    def import_from_mt5(
        self,
        mt5_symbol: str,
        date_from: dt.datetime,
        date_to: dt.datetime,
        batch_import: bool = False,
        **kwargs,
    ) -> pd.DataFrame:
        def import_ticks(
            mt5_symbol: str, date_from: dt.datetime, date_to: dt.datetime
        ) -> pd.DataFrame:
            return self._format_ticks(
                data=mt5.copy_ticks_range(
                    mt5_symbol, date_from, date_to, mt5.COPY_TICKS_ALL
                )
            )

        # Connect to mt5 terminal
        TickData.connect_to_mt5()

        # Perform batch import and import data incrementally
        if batch_import:

            step_days = kwargs.get('step_days', TickData.DEFAULT_BATCH_IMPORT_STEP_DAYS)
            datetime_chunks = TickData.generate_date_ranges(
                date_from, date_to, step_days=step_days
            )
            df = pd.DataFrame()
            pbar = tqdm(
                total=len(datetime_chunks), desc='Importing tick data', colour='yellow'
            )
            for start, end in datetime_chunks:
                df = pd.concat(
                    [
                        df,
                        import_ticks(
                            mt5_symbol=mt5_symbol, date_from=start, date_to=end
                        ),
                    ],
                    axis='index',
                )
                pbar.update(1)

            mt5.shutdown()
            return df

        # Regular import
        else:
            df = import_ticks(mt5_symbol, date_from, date_to)
            mt5.shutdown()
            return df


if __name__ == '__main__':

    source_path = r'F:\New_Backup_03_2025\PyQuant\data\ccm_60min_atualizado.csv'
    destination_path = r'C:\Users\Guilherme\PycharmProjects\nautilus_trader\test_scripts\ccm_60min.parquet'

    data = CandleData.import_from_csv(path=source_path)
    data.to_parquet(destination_path)
    print(f'Sucessfully saved to: {destination_path}')
