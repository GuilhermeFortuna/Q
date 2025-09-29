"""
This module provides an abstract base class for handling market data, as well as
concrete implementations for candle and tick data. It includes features for
fetching and formatting market data from MetaTrader 5 (MT5), as well as
utilities for importing data from CSV files. The code supports operations
on both candle and tick data structures.

Classes:
    - MarketData: Abstract base class defining the interface for market data management.
    - CandleData: Handles operations specific to candlestick data, including
      formatting and data import.
    - TickData: Handles operations specific to tick data, including batch
      date handling and formatting.

Static Methods:
    - MarketData.connect_to_mt5: Establishes a connection to the MT5 trading
      terminal for data retrieval.
    - CandleData.format_candle_data_from_mt5: Formats raw MT5 candle data into
      structured Pandas DataFrame.
    - CandleData.import_from_mt5: Imports candle data from MT5 within a specified
      date range and timeframe.
    - CandleData.import_from_csv: Imports candle data from a CSV file.
    - TickData.generate_date_ranges: Divides a datetime range into smaller
      stepped ranges.
"""

import time
from abc import ABC, abstractmethod
from typing import Optional

import MetaTrader5 as mt5
import pandas as pd


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


if __name__ == '__main__':
    pass
