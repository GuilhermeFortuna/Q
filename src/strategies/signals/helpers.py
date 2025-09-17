from __future__ import annotations

from typing import Optional

import math
import pandas as pd
import pandas_ta as pta


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def safe(value: float | int | None, default: float = 0.0) -> float:
    try:
        v = float(value)
    except Exception:
        return default
    if math.isfinite(v):
        return v
    return default


def safe_div(n: float, d: float, default: float = 0.0) -> float:
    d = float(d)
    if d == 0.0 or not math.isfinite(d):
        return default
    try:
        return float(n) / d
    except Exception:
        return default


def cross_up(series: pd.Series | pd.Index | list | pd.Series, i: int, level: float) -> bool:
    if i <= 0:
        return False
    try:
        prev_val = float(series[i - 1])
        val = float(series[i])
    except Exception:
        return False
    return prev_val <= level and val > level


def cross_down(series: pd.Series | pd.Index | list | pd.Series, i: int, level: float) -> bool:
    if i <= 0:
        return False
    try:
        prev_val = float(series[i - 1])
        val = float(series[i])
    except Exception:
        return False
    return prev_val >= level and val < level


def ensure_atr(data: dict, length: int = 14, col: str = 'atr') -> None:
    """
    Ensure an ATR column exists on data['candle'].data; if not, compute it with given length.
    """
    candles = data['candle'].data
    if col not in candles.columns:
        atr = pta.atr(candles['high'], candles['low'], candles['close'], length=length)
        candles[col] = atr


def norm_by_atr(candle, i: int, distance: float, atr_col: str = 'atr') -> float:
    try:
        atr_val = float(getattr(candle, atr_col)[i])
    except Exception:
        atr_val = 0.0
    if not math.isfinite(atr_val) or atr_val <= 0:
        return clamp01(abs(float(distance)) / 1e-9)
    return clamp01(abs(float(distance)) / atr_val)


def rolling_streak(arr, i: int, direction: int) -> int:
    """
    Compute the number of consecutive bars up to i with sign(direction).
    direction: +1 for up (value > 0), -1 for down (value < 0)
    """
    if i < 0:
        return 0
    count = 0
    sign = 1 if direction >= 0 else -1
    while i - count >= 0:
        v = float(arr[i - count])
        if (sign > 0 and v > 0) or (sign < 0 and v < 0):
            count += 1
        else:
            break
    return count


def has_columns(df: pd.DataFrame, cols: list[str]) -> bool:
    return all(c in df.columns for c in cols)
