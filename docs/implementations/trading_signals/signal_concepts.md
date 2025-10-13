# Trading Signal Concepts (Composable)

This document proposes high-quality, implementation-ready concepts for new composable `TradingSignal` classes. Each entry specifies purpose, parameters, required indicator columns (`compute_indicators`), generation logic (`generate(i, data)`), and usage notes with `CompositeStrategy`.

---

## 1) RSI Mean-Reversion with Dynamic Bands

- Goal: Fade short-term extremes; ideal for range-bound regimes.
- Parameters:
    - length: int (e.g., 14)
    - upper_band: int (e.g., 70)
    - lower_band: int (e.g., 30)
    - band_smooth: Optional[int] (EMA smoothing on RSI)
    - exit_mid: bool (exit on RSI returning to midline ~50)
- compute_indicators adds:
    - rsi
    - rsi_ema (optional)
- generate:
    - Long when RSI crosses up from below lower_band; strength ≈ (lower_band − RSI) / lower_band (clamped [0,1]).
    - Short when RSI crosses down from above upper_band; strength ≈ (RSI − upper_band) / (100 − upper_band).
    - Neutral otherwise; optionally weaker signal when outside bands without cross.
- Notes: Combine with volatility/regime filters (e.g., Choppiness) to avoid strong trends.

---

## 2) ADX/DMI Trend Direction

- Goal: Follow directional trends and filter choppy regimes.
- Parameters:
    - length: int (e.g., 14)
    - adx_thresh: float (e.g., 20–25)
- compute_indicators adds:
    - adx, di_plus, di_minus
- generate:
    - Long if di_plus > di_minus and ADX ≥ threshold; strength scales with (di_plus − di_minus) and ADX intensity.
    - Short if di_minus > di_plus and ADX ≥ threshold; symmetric.
    - Neutral when ADX < threshold.
- Notes: Excellent as a trend filter to gate other entry signals.

---

## 3) Supertrend Flip

- Goal: Enter on trend direction changes using Supertrend.
- Parameters:
    - atr_length: int
    - atr_mult: float
- compute_indicators adds:
    - atr, supertrend_line, supertrend_dir ∈ {+1, −1}
- generate:
    - Long on flip from −1 to +1; strength increases as close moves above supertrend_line (normalized by ATR).
    - Short on flip from +1 to −1; symmetric.
    - Neutral otherwise.
- Notes: Doubles as trailing exit/confirmation signal.

---

## 4) Donchian Breakout with Pullback Confirmation

- Goal: Trade breakouts with reduced whipsaws via pullback context.
- Parameters:
    - breakout_len: int (e.g., 20)
    - pullback_len: int (e.g., 5)
    - confirm_close: bool (require close outside the band)
- compute_indicators adds:
    - donchian_high, donchian_low, recent_pullback_high/low
- generate:
    - Long if close > donchian_high with a recent pullback down; strength scales with distance above donchian_high normalized by ATR.
    - Short if close < donchian_low with recent pullback up; symmetric.
    - Neutral otherwise.
- Notes: Combine with ADX filter for strong-trend breakouts.

---

## 5) MACD Momentum State

- Goal: Momentum entries with trend context using MACD and histogram.
- Parameters:
    - fast: int (12)
    - slow: int (26)
    - signal: int (9)
    - zero_line_bias: bool (require MACD on the correct side of zero)
- compute_indicators adds:
    - macd, macd_signal, macd_hist
- generate:
    - Long if MACD > signal and (MACD > 0 if zero_line_bias); strength ~ normalized MACD histogram (e.g., vs rolling std/ATR).
    - Short if MACD < signal and (MACD < 0 if zero_line_bias).
    - Neutral otherwise.
- Notes: Pair with pullback entries for better timing.

---

## 6) Keltner Channel Breakout with BB Squeeze Filter

- Goal: Trade volatility expansions after contractions (squeeze).
- Parameters:
    - ema_len: int (e.g., 20)
    - atr_len: int (e.g., 14)
    - atr_mult: float (e.g., 1.5)
    - squeeze_bb_len: int (e.g., 20)
    - squeeze_bb_std: float (e.g., 2.0)
    - squeeze_thresh: float (threshold on BB width / KC width)
    - min_squeeze_bars: int (bars under threshold before activation)
- compute_indicators adds:
    - ema_mid, kc_upper, kc_lower, bb_upper, bb_lower, squeeze_metric
- generate:
    - Only active if squeeze_metric < threshold for min_squeeze_bars.
    - Long when close > kc_upper; strength increases with normalized distance above kc_upper and tighter prior squeeze.
    - Short when close < kc_lower; symmetric.
    - Neutral otherwise.
- Notes: Strong standalone breakout or activation filter for other signals.

---

## 7) VWAP Deviation Reversion (Intraday)

- Goal: Mean-revert to session VWAP after extreme deviations.
- Parameters:
    - session_reset: str (e.g., daily)
    - std_len: int (rolling std length for deviation)
    - dev_mult: float (e.g., 2.0)
- compute_indicators adds:
    - session_vwap, vwap_dev = close − vwap, vwap_dev_std
- generate:
    - Long if vwap_dev < −dev_mult · vwap_dev_std and deviation starts to contract (e.g., cross up threshold); strength ∝ |deviation|/std.
    - Short if vwap_dev > +dev_mult · vwap_dev_std with bearish contraction cue.
    - Neutral otherwise.
- Notes: Best for intraday futures; beware low-liquidity periods and lunch hours.

---

## 8) Volume Spike Exhaustion Reversal

- Goal: Fade climax moves identified by simultaneous spikes in volume and range.
- Parameters:
    - vol_len: int (e.g., 20)
    - vol_spike_mult: float (e.g., 2.0)
    - range_len: int
    - range_spike_mult: float
    - proximity_ratio: float (close-to-extreme proximity filter)
- compute_indicators adds:
    - vol_ma, true_range, tr_ma, spike_flags
- generate:
    - Long if vol and range both exceed multipliers and close is near bar low after down move; strength scales with spike intensity and proximity.
    - Short if near bar high after up move.
    - Neutral otherwise.
- Notes: Contrarian by design; pair with regime/trend filters to avoid catching strong trends.

---

## 9) ATR Trailing Stop Reversal

- Goal: Reverse positions on ATR-based trailing stop crosses.
- Parameters:
    - atr_len: int (e.g., 14)
    - atr_mult: float (e.g., 3.0)
    - method: str ("chandelier" or "swing-extremes")
- compute_indicators adds:
    - atr, trail_long, trail_short
- generate:
    - Long when close crosses above trail_short; strength ∝ distance above stop normalized by ATR.
    - Short when close crosses below trail_long; symmetric.
    - Neutral otherwise.
- Notes: Works as both entry and exit; synergizes with `always_active=True`.

---

## 10) Heikin-Ashi Trend Continuation

- Goal: Smooth trend detection and continuation entries.
- Parameters:
    - min_streak: int (e.g., 2–3)
    - body_ratio_thresh: float (min body/true range)
    - wick_filter: bool or thresholds (limit counter-trend wicks)
- compute_indicators adds:
    - ha_open, ha_high, ha_low, ha_close, ha_color, ha_body_ratio
- generate:
    - Long when consecutive bullish HA candles with sufficient body and weak upper wicks; strength scales with streak length and body quality.
    - Short with bearish criteria.
    - Neutral otherwise.
- Notes: Good for filtering chop and confirming pullback ends.

---

## 11) Multi-Timeframe MA Alignment Filter

- Goal: Trade with higher-timeframe direction alignment.
- Parameters:
    - ht_timeframe: str or ratio (e.g., 4× current)
    - ht_ma_len: int (e.g., 50)
    - lt_ma_len: int (e.g., 20)
    - alignment_mode: str ("ht_only" or "ht_and_lt")
- compute_indicators adds:
    - ht_ma_on_lt_index (aligned), lt_ma
- generate:
    - Long if close > ht_ma and optionally lt_ma > ht_ma; strength ∝ distance above ht_ma normalized by ATR.
    - Short if below.
    - Neutral otherwise.
- Notes: Typically a filter (low strength) to combine with entry signals.

---

## 12) Choppiness Index Regime Filter

- Goal: Enable/disable other signals based on trendiness vs range regimes.
- Parameters:
    - length: int (e.g., 14)
    - chop_low: float (e.g., 38)
    - chop_high: float (e.g., 62)
- compute_indicators adds:
    - choppiness (0–100)
- generate:
    - Neutral with strength 0, but info marks regime: trend if < chop_low, range if > chop_high.
    - Optional weak long/short bias in trend regime with price >/< a baseline MA.
- Notes: Use to gate trend-followers (MACD, ADX, Donchian) vs mean-reversion (RSI, VWAP dev).

---

## Combining within CompositeStrategy

- Trend-following stack:
    - ADX/DMI + Supertrend + Donchian or Keltner breakout, with Multi-Timeframe MA Alignment as a filter.
    - Combiner: default weighted_vote or conservative agreement for stronger consensus.

- Mean-reversion stack:
    - RSI Mean-Reversion + VWAP Deviation + Choppiness (“range” regime).
    - Combiner: thresholded weighted_vote to avoid weak extremes.

- Hybrid:
    - MACD Momentum + Keltner Breakout (activated by BB Squeeze) + ATR Trailing Stop for exits/inversions.

- Risk control:
    - Use regime filters (Choppiness) as low-strength, gating signals that reduce or nullify aggregate strength in unfavorable regimes.
