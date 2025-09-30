import datetime as dt
from typing import Optional, List, Literal

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from tqdm import tqdm

from . import store as store_utils
from .base import MarketData


class TickData(MarketData):
    DEFAULT_BATCH_IMPORT_STEP_DAYS = 15

    def __init__(self, symbol: str):
        super().__init__(symbol=symbol)
        self.df = pd.DataFrame()

    def store_data(
        self,
        *,
        root_dir: Optional[str] = None,
        mode: Literal["upsert", "overwrite"] = "upsert",
    ) -> None:
        """Persist tick data into daily-partitioned Parquet files.

        Normalizes columns so that a 'price' column exists (renaming 'last' if needed),
        ensures a 'datetime' column exists, and writes per-day files with upsert/overwrite modes.
        """
        if self.df is None or not isinstance(self.df, pd.DataFrame) or self.df.empty:
            raise ValueError("No data to store. self.data is empty or None.")

        df = self.df.copy()

        # Normalize price column
        if "price" not in df.columns and "last" in df.columns:
            df = df.rename(columns={"last": "price"})

        # Ensure datetime column exists and is naive
        if isinstance(df.index, pd.DatetimeIndex):
            dt_vals = df.index
        elif "datetime" in df.columns:
            dt_vals = pd.to_datetime(df["datetime"], errors="coerce")
        else:
            raise ValueError("Data must have a DatetimeIndex or a 'datetime' column.")

        dt_vals = pd.to_datetime(dt_vals, utc=False)
        if hasattr(dt_vals, "tz_localize") and getattr(dt_vals, "tz", None) is not None:
            dt_vals = dt_vals.tz_localize(None)
        df["datetime"] = dt_vals

        # Coerce numeric types
        if "price" in df.columns:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
        if "volume" in df.columns:
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        # Group by day
        df["_date"] = df["datetime"].dt.date
        root = root_dir
        for day, chunk in df.groupby("_date", sort=True):
            path = store_utils.tick_path(self.symbol, day, root_dir=root)
            out = (
                chunk.drop(columns=["_date"])
                .dropna(subset=["datetime"])
                .sort_values("datetime")
            )
            if mode == "overwrite":
                store_utils.write_parquet_atomic(out, path)
            else:
                store_utils.upsert_daily(
                    out, path, key_cols=["datetime"]
                )  # later could include ['datetime','price','volume']

    def load_data(
        self,
        date_from: Optional[dt.datetime] = None,
        date_to: Optional[dt.datetime] = None,
        columns: Optional[List[str]] = None,
        root_dir: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load tick data from daily parquet files and normalize schema.

        Returns DataFrame indexed by datetime, sorted ascending, with duplicates on 'datetime' removed.
        """
        paths = list(
            store_utils.list_existing_daily_paths(
                root_dir=root_dir,
                data_type="tick_data",
                symbol=self.symbol,
                timeframe=None,
                date_from=date_from,
                date_to=date_to,
            )
        )
        if not paths:
            self.df = pd.DataFrame()
            return self.df

        frames = []
        for p in sorted(paths):
            df = store_utils.read_parquet_if_exists(p)
            if df is not None and not df.empty:
                frames.append(df)
        if not frames:
            self.df = pd.DataFrame()
            return self.df

        df_all = pd.concat(frames, axis="index", ignore_index=True)

        # Ensure datetime column and filter by exact datetime range if provided
        if "datetime" not in df_all.columns:
            if isinstance(df_all.index, pd.DatetimeIndex):
                df_all = df_all.reset_index()
            else:
                raise ValueError("Loaded data missing 'datetime' column")
        df_all["datetime"] = pd.to_datetime(df_all["datetime"], utc=False)

        if date_from is not None:
            df_all = df_all[df_all["datetime"] >= date_from]
        if date_to is not None:
            df_all = df_all[df_all["datetime"] <= date_to]

        # Normalize columns: last->price if needed
        if "price" not in df_all.columns and "last" in df_all.columns:
            df_all = df_all.rename(columns={"last": "price"})

        # Select columns if requested (ensure datetime is present)
        if columns is not None:
            cols = ["datetime"] + [
                c for c in columns if c != "datetime" and c in df_all.columns
            ]
            df_all = df_all.loc[:, [c for c in cols if c in df_all.columns]]

        # Deduplicate and sort
        df_all = df_all.drop_duplicates(subset=["datetime"], keep="last")
        df_all = df_all.sort_values("datetime").set_index("datetime")

        self.df = df_all
        return df_all

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
            self.df = df

        # Regular import
        else:
            df = import_ticks(mt5_symbol, date_from, date_to)
            mt5.shutdown()
            self.df = df
