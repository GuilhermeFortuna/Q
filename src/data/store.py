import os
import shutil
import uuid
import warnings
from datetime import date, datetime, timedelta
from typing import Generator, Iterable, Optional, Union, List
from pathlib import Path
import pandas as pd


# ------------------------------
# Root resolution
# ------------------------------

DEFAULT_DATA_ROOT = Path(__file__).parent / "data"


def resolve_root_dir(root_dir: Optional[str] = None) -> str:
    """Resolve the root directory for on-disk data storage.

    Precedence: function arg > env DATA_ROOT > default (src/data/data).
    Ensures the directory exists.
    """
    root = root_dir or os.environ.get("DATA_ROOT", DEFAULT_DATA_ROOT)
    os.makedirs(root, exist_ok=True)
    return root


# ------------------------------
# Path builders
# ------------------------------


def _daily_partition_path(root: str, *parts: str, d: date) -> str:
    year = f"year={d.year:04d}"
    month = f"month={d.month:02d}"
    day = f"day={d.day:02d}"
    folder = os.path.join(root, *parts, year, month, day)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "data.parquet")


def candle_path(
    symbol: str, timeframe: str, d: date, root_dir: Optional[str] = None
) -> str:
    root = resolve_root_dir(root_dir)
    return _daily_partition_path(root, "candle_data", symbol, timeframe, d=d)


def tick_path(symbol: str, d: date, root_dir: Optional[str] = None) -> str:
    root = resolve_root_dir(root_dir)
    return _daily_partition_path(root, "tick_data", symbol, d=d)


# ------------------------------
# IO helpers
# ------------------------------


def write_parquet_atomic(
    df: pd.DataFrame, path: str, compression: str = "snappy"
) -> None:
    """Write parquet to a temporary file then atomically replace the target.

    Ensures parent directory exists. Uses snappy compression by default.
    """
    if df is None:
        raise ValueError("df cannot be None")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Write to a temp file in the same directory to make replace atomic on Windows too
    tmp_path = os.path.join(os.path.dirname(path), f".{uuid.uuid4().hex}.tmp.parquet")
    try:
        # Always keep datetime as a column (never as index) when writing.
        df_to_write = df.copy()
        if (
            isinstance(df_to_write.index, pd.DatetimeIndex)
            and "datetime" not in df_to_write.columns
        ):
            df_to_write = df_to_write.reset_index()
        # Parquet write
        df_to_write.to_parquet(tmp_path, compression=compression, index=False)
        # Replace
        if os.path.exists(path):
            os.replace(tmp_path, path)
        else:
            shutil.move(tmp_path, path)
    finally:
        # Cleanup on failure
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def read_parquet_if_exists(path: str) -> pd.DataFrame:
    """Read parquet if it exists, otherwise return empty DataFrame."""
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path)
        # Ensure datetime column exists (not stored as index)
        if "datetime" not in df.columns and isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
        return df
    except Exception as e:
        warnings.warn(f"Failed to read parquet at {path}: {e}")
        return pd.DataFrame()


def upsert_daily(df_new: pd.DataFrame, path: str, key_cols: List[str]) -> None:
    """Merge df_new into existing file at path, drop duplicates by key_cols, sort by datetime, and write back.

    Assumes df_new contains a 'datetime' column as naive UTC timestamps.
    """
    if df_new is None or df_new.empty:
        return

    # Read existing
    df_old = read_parquet_if_exists(path)

    # Concatenate
    frames = []
    if not df_old.empty:
        frames.append(df_old)
    frames.append(df_new)
    df_all = pd.concat(frames, axis="index", ignore_index=True)

    # Normalize datetime
    if "datetime" not in df_all.columns:
        raise ValueError("upsert_daily requires a 'datetime' column")
    df_all["datetime"] = pd.to_datetime(df_all["datetime"], utc=False)

    # Drop duplicates by keys
    df_all = df_all.drop_duplicates(subset=key_cols, keep="last")

    # Sort by datetime
    df_all = df_all.sort_values("datetime").reset_index(drop=True)

    write_parquet_atomic(df_all, path)


# ------------------------------
# Range helpers
# ------------------------------


def iter_dates(
    date_from: Optional[Union[date, datetime]], date_to: Optional[Union[date, datetime]]
) -> Generator[date, None, None]:
    """Yield daily dates from date_from to date_to inclusive. If one is None, yields only the other; if both None, yields nothing."""
    if date_from is None and date_to is None:
        return
    if isinstance(date_from, datetime):
        start = date_from.date()
    elif isinstance(date_from, date):
        start = date_from
    elif date_from is None and isinstance(date_to, (date, datetime)):
        # single day iteration when only end provided
        start = date_to.date() if isinstance(date_to, datetime) else date_to
    else:
        start = date.today()

    if isinstance(date_to, datetime):
        end = date_to.date()
    elif isinstance(date_to, date):
        end = date_to
    elif date_to is None and isinstance(date_from, (date, datetime)):
        end = date_from.date() if isinstance(date_from, datetime) else date_from
    else:
        end = start

    if start > end:
        step = -1
    else:
        step = 1

    cur = start
    while True:
        yield cur
        if cur == end:
            break
        cur = cur + timedelta(days=step)


def list_existing_daily_paths(
    *,
    root_dir: Optional[str],
    data_type: str,  # 'candle_data' or 'tick_data'
    symbol: str,
    timeframe: Optional[str] = None,
    date_from: Optional[Union[date, datetime]] = None,
    date_to: Optional[Union[date, datetime]] = None,
) -> Iterable[str]:
    """Yield existing daily parquet paths for the given parameters.

    If a date range is provided, we build expected paths and check for existence (avoids scanning).
    If no range is provided, we walk the specific symbol/timeframe directory only.
    """
    root = resolve_root_dir(root_dir)

    if data_type not in ("candle_data", "tick_data"):
        raise ValueError("data_type must be 'candle_data' or 'tick_data'")

    base = os.path.join(root, data_type, symbol)
    if data_type == "candle_data":
        if not timeframe:
            raise ValueError("timeframe is required for candle_data path listing")
        base = os.path.join(base, timeframe)

    # If range provided, construct paths directly
    if date_from is not None or date_to is not None:
        for d in iter_dates(date_from, date_to):
            if data_type == "candle_data":
                p = candle_path(symbol, timeframe or "", d, root_dir=root)
            else:
                p = tick_path(symbol, d, root_dir=root)
            if os.path.exists(p):
                yield p
        return

    # Otherwise, walk within base (limited scope) and collect data.parquet paths
    if not os.path.exists(base):
        return
    for year in os.listdir(base):
        y_path = os.path.join(base, year)
        if not os.path.isdir(y_path) or not year.startswith("year="):
            continue
        for month in os.listdir(y_path):
            m_path = os.path.join(y_path, month)
            if not os.path.isdir(m_path) or not month.startswith("month="):
                continue
            for day in os.listdir(m_path):
                d_path = os.path.join(m_path, day)
                if not os.path.isdir(d_path) or not day.startswith("day="):
                    continue
                f = os.path.join(d_path, "data.parquet")
                if os.path.exists(f):
                    yield f
