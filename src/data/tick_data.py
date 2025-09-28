import datetime as dt

import MetaTrader5 as mt5
import pandas as pd
from tqdm import tqdm

from .base import MarketData


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
