# Indicators

Utility indicators for quantitative research. Currently includes a market regime classifier based on moving averages and ATR.

## Contents

- classify_market_regime(candles, ...): Adds columns with SMA(50/200), ATR, volatility buckets, raw and smoothed regime labels, and a numeric regime_code for plotting.
- print_regime_summary(candles): Convenience summary of regime distribution and average durations.
- Regime, VolBucket: Literal types for regimes and volatility buckets.

Exported in `src.indicators.__init__` for easy import.

## Installation

Part of the workspace:

```
uv sync
```

## Usage

```python
import pandas as pd
from src.indicators import classify_market_regime, print_regime_summary

# candles must have columns: open, high, low, close
candles = pd.read_csv("your_ohlc.csv")
classified = classify_market_regime(candles)
print_regime_summary(classified)

# New columns include: 'sma50', 'sma200', 'sma50_slope', 'atr', 'vol_bucket',
# 'regime_raw', 'regime', 'regime_code', 'atr_low_thr', 'atr_high_thr'.
```

## Notes

- Raises ValueError if required OHLC columns are missing.
- Parameters allow tuning of MA lengths, slope sensitivity, ATR length, and minimum regime duration.
