import numpy as np
import pandas as pd
from typing import Literal, Tuple

Regime = Literal['Bull', 'Bear', 'Sideways']
VolBucket = Literal['Low', 'Med', 'High']


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()


def _atr(
    high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14
) -> pd.Series:
    # True Range components
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # Wilder's smoothing approximation via EMA
    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def _classify_trend_row(
    close: float, sma50: float, sma200: float, slope50: float, slope_eps: float
) -> Regime:
    if np.isnan([close, sma50, sma200, slope50]).any():
        return 'Sideways'
    # Bullish if above long MA, short > long, and short MA rising
    if (close > sma200) and (sma50 > sma200) and (slope50 > slope_eps):
        return 'Bull'
    # Bearish if below long MA, short < long, and short MA falling
    if (close < sma200) and (sma50 < sma200) and (slope50 < -slope_eps):
        return 'Bear'
    return 'Sideways'


def _smooth_with_min_duration(labels: pd.Series, min_bars: int = 10) -> pd.Series:
    """
    Enforce minimum duration per regime to reduce flicker.
    If a switch is shorter than min_bars, revert to previous regime.
    """
    labels = labels.copy().fillna('Sideways')
    if labels.empty:
        return labels

    current = labels.iloc[0]
    run_len = 1
    out = [current]

    for i in range(1, len(labels)):
        val = labels.iloc[i]
        if val == current:
            run_len += 1
            out.append(current)
        else:
            # Look-ahead window to confirm persistence
            # If the next (min_bars - 1) are not mostly the new label, keep current
            window = labels.iloc[i : i + min_bars]
            if (window == val).sum() >= int(np.ceil(min_bars * 0.6)):
                current = val
                run_len = 1
                out.append(current)
            else:
                out.append(current)
    return pd.Series(out, index=labels.index)


def _bucket_volatility(
    atr: pd.Series, q_low: float = 0.3, q_high: float = 0.7
) -> Tuple[pd.Series, float, float]:
    # Use in-sample quantiles as a simple first pass (can be switched to rolling percentiles later)
    valid = atr.dropna()
    if valid.empty:
        return pd.Series(index=atr.index, dtype=object), np.nan, np.nan
    low_thr = valid.quantile(q_low)
    high_thr = valid.quantile(q_high)

    def _bucket(x: float) -> VolBucket:
        if np.isnan(x):
            return 'Med'
        if x <= low_thr:
            return 'Low'
        if x >= high_thr:
            return 'High'
        return 'Med'

    buckets = atr.apply(_bucket)
    return buckets, low_thr, high_thr


def classify_market_regime(
    candles: pd.DataFrame,
    sma_short: int = 50,
    sma_long: int = 200,
    slope_lookback: int = 3,
    slope_eps: float = 0.0,  # flatness tolerance (% of price per bar); computed below if 0.0
    atr_len: int = 14,
    min_duration: int = 10,
) -> pd.DataFrame:
    """
    Add columns:
      - 'sma50', 'sma200', 'sma50_slope'
      - 'atr', 'vol_bucket' in {'Low','Med','High'}
      - 'regime_raw' in {'Bull','Bear','Sideways'}
      - 'regime' (smoothed)
      - 'regime_code' in {1,0,-1}
    """
    candles = candles.copy()

    # Basic OHLC sanity
    required_cols = {'open', 'high', 'low', 'close'}
    missing = required_cols - set(candles.columns)
    if missing:
        raise ValueError(f'Missing required OHLC columns: {missing}')

    # Moving averages and slope
    candles['sma50'] = _sma(candles['close'], sma_short)
    candles['sma200'] = _sma(candles['close'], sma_long)

    # Slope of SMA50 over slope_lookback bars, expressed in price units per bar
    candles['sma50_slope'] = candles['sma50'].diff(periods=slope_lookback) / max(
        slope_lookback, 1
    )

    # Adaptive slope epsilon if not provided: small fraction of median price per bar
    if slope_eps == 0.0:
        med_price = candles['close'].median()
        # 0.02% of median price per bar as a default flatness threshold
        slope_eps = 0.0002 * med_price

    # ATR and volatility buckets
    candles['atr'] = _atr(
        candles['high'], candles['low'], candles['close'], length=atr_len
    )
    vol_bucket, low_thr, high_thr = _bucket_volatility(candles['atr'])
    candles['vol_bucket'] = vol_bucket

    # Raw trend classification
    candles['regime_raw'] = [
        _classify_trend_row(c, s50, s200, slope, slope_eps)
        for c, s50, s200, slope in zip(
            candles['close'].values,
            candles['sma50'].values,
            candles['sma200'].values,
            candles['sma50_slope'].values,
        )
    ]

    # Smooth to enforce minimum duration/hysteresis
    candles['regime'] = _smooth_with_min_duration(
        candles['regime_raw'], min_bars=min_duration
    )

    # Numeric code for plotting
    map_code = {'Bull': 1, 'Sideways': 0, 'Bear': -1}
    candles['regime_code'] = candles['regime'].map(map_code).astype('float')

    # Attach thresholds for reference (constant columns for visibility, optional)
    candles['atr_low_thr'] = low_thr
    candles['atr_high_thr'] = high_thr

    return candles


def _print_regime_summary(candles: pd.DataFrame) -> None:
    if candles.empty or 'regime' not in candles.columns:
        print('No regime data to summarize.')
        return

    counts = candles['regime'].value_counts(dropna=False)
    total = counts.sum()
    print('\nRegime distribution:')
    for k in ['Bull', 'Sideways', 'Bear']:
        n = int(counts.get(k, 0))
        pct = 100.0 * n / total if total else 0.0
        print(f'  {k:8s}: {n:6d} ({pct:5.1f}%)')

    # Average duration per regime
    runs = []
    prev = None
    run_len = 0
    for val in candles['regime']:
        if val == prev:
            run_len += 1
        else:
            if prev is not None:
                runs.append((prev, run_len))
            prev = val
            run_len = 1
    if prev is not None:
        runs.append((prev, run_len))
    if runs:
        print('\nAverage duration (bars):')
        for k in ['Bull', 'Sideways', 'Bear']:
            lens = [l for r, l in runs if r == k]
            avg = np.mean(lens) if lens else 0.0
            print(f'  {k:8s}: {avg:6.1f}')
    print()
