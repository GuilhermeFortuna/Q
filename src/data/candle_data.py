import datetime as dt
from typing import Optional, Union, List, Literal

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

from . import store as store_utils
from src.backtester.utils import TIMEFRAMES
from .base import MarketData


class CandleData(MarketData):
    def __init__(self, symbol: str, timeframe: str):
        super().__init__(symbol=symbol)
        # Validate timeframe
        if not isinstance(timeframe, str) or timeframe not in TIMEFRAMES.keys():
            raise ValueError(f'Invalid timeframe: {timeframe}')

        self.timeframe = timeframe
        self.df = pd.DataFrame()

    def store_data(
        self,
        *,
        root_dir: Optional[str] = None,
        mode: Literal["upsert", "overwrite"] = "upsert",
    ) -> None:
        """Persist candle data into daily-partitioned Parquet files.

        - Ensures there is a 'datetime' column (kept as column, not index).
        - Groups by day and either upserts or overwrites each daily file.
        """
        if self.df is None or not isinstance(self.df, pd.DataFrame) or self.df.empty:
            raise ValueError("No data to store. self.data is empty or None.")
        if not getattr(self, "timeframe", None):
            raise ValueError("timeframe must be provided for CandleData.store_data().")

        df = self.df.copy()

        # Ensure datetime column exists and is naive
        if isinstance(df.index, pd.DatetimeIndex):
            dt_val = df.index
        elif "datetime" in df.columns:
            dt_val = pd.to_datetime(df["datetime"], errors="coerce")
        else:
            raise ValueError("Data must have a DatetimeIndex or a 'datetime' column.")

        # Drop NaT and remove timezone
        dt_val = pd.to_datetime(dt_val, utc=False)
        if hasattr(dt_val, "tz_localize") and getattr(dt_val, "tz", None) is not None:
            dt_val = dt_val.tz_localize(None)
        df['datetime'] = dt_val

        # Normalize numeric dtypes lightly (OHLC as float)
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "volume" in df.columns:
            # Keep as numeric; allow integers or floats
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        # Group by day
        df["_date"] = df['datetime'].dt.date
        root = root_dir  # pass-through, utils will resolve

        for day, chunk in df.groupby("_date", sort=True):
            path = store_utils.candle_path(
                self.symbol, self.timeframe, day, root_dir=root
            )
            # Prepare chunk
            out = chunk.drop(columns=["_date"])  # keep 'datetime' as column
            out = out.dropna(subset=["datetime"])  # guard
            out = out.sort_values("datetime")

            if mode == "overwrite":
                store_utils.write_parquet_atomic(out, path)
            else:
                store_utils.upsert_daily(out, path, key_cols=["datetime"])  # upsert

    def load_data(
        self,
        date_from: Optional[dt.datetime] = None,
        date_to: Optional[dt.datetime] = None,
        columns: Optional[List[str]] = None,
        root_dir: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load candle data from daily parquet files.

        - If a date range is provided, only load days in the range; otherwise load all available.
        - Returns DataFrame indexed by datetime, sorted ascending, with duplicates on 'datetime' removed.
        """
        # Determine existing paths
        paths = list(
            store_utils.list_existing_daily_paths(
                root_dir=root_dir,
                data_type="candle_data",
                symbol=self.symbol,
                timeframe=self.timeframe,
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

    def import_from_mt5(
        self,
        date_from: dt.datetime,
        date_to: dt.datetime,
        use_tick_volume: Optional[bool] = False,
        mt5_symbol: str | None = None,
        timeframe: str | None = None,
    ) -> pd.DataFrame:
        # Initialize connection to mt5 terminal with default credentials
        if not mt5.initialize():
            error_msg = f"Failed to initialize MT5 connection: {mt5.last_error()}"
            print(error_msg)
            raise ConnectionError(error_msg)

        mt5_symbol = self.symbol if mt5_symbol is None else mt5_symbol
        if timeframe is not None:
            self.timeframe = timeframe
        else:
            timeframe = self.timeframe
            
        df = pd.DataFrame()
        try:
            # Check if symbol exists
            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info is None:
                error_msg = f"Symbol {mt5_symbol} not found in MT5. Available symbols: {mt5.symbols_get()[:5] if mt5.symbols_get() else 'None'}"
                print(error_msg)
                raise ValueError(error_msg)
            
            # Get rates from MT5
            rates = mt5.copy_rates_range(
                mt5_symbol, TIMEFRAMES[timeframe].mt5, date_from, date_to
            )
            
            if rates is None or len(rates) == 0:
                error_msg = f"No data returned from MT5 for symbol {mt5_symbol}, timeframe {timeframe}, from {date_from} to {date_to}. MT5 error: {mt5.last_error()}"
                print(error_msg)
                raise ValueError(error_msg)
                
            df = CandleData.format_candle_data_from_mt5(data=rates)
            
        except Exception as e:
            error_msg = f'Error importing data for symbol {mt5_symbol} from MT5: {str(e)}. MT5 error: {mt5.last_error()}'
            print(error_msg)
            raise ValueError(error_msg)
        finally:
            mt5.shutdown()

        self.df = df
        return df

    @staticmethod
    def format_candle_data_from_mt5(
        data: np.ndarray, use_tick_volume: Optional[bool] = False
    ) -> pd.DataFrame:
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
            # df.set_index('datetime', inplace=True, drop=True)

            # Select volume to use
            if 'volume' not in df.columns and any(
                'volume' in col for col in list(df.columns)
            ):
                df['volume'] = (
                    df['real_volume'].copy()
                    if not use_tick_volume
                    else df['tick_volume'].copy()
                )

            df.drop(columns=['time', 'spread'], inplace=True)
            return df

        else:
            raise ValueError('No data provided. Please provide data to format.')

    def import_from_csv(self, path: str) -> Union[pd.DataFrame, None]:
        for enc in ['latin1', 'utf-8']:
            try:
                df = pd.read_csv(path, decimal=',', encoding=enc)

                if isinstance(df, pd.DataFrame):
                    df.columns = [
                        'datetime',
                        'open',
                        'high',
                        'low',
                        'close',
                        'volume',
                    ]
                    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                    df.sort_values(by='datetime', inplace=True, ascending=True)
                    self.df = df
                    break
                else:
                    continue

            except Exception as e:
                pass
