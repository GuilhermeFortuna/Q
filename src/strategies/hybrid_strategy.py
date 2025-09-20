from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.backtester import TradingStrategy, TradeOrder
from src.strategies.signals import TradingSignal, SignalDecision
from src.strategies.composite import weighted_vote


@dataclass
class HybridExecutionConfig:
    """
    Configuration for tick-level execution and exits.

    Attributes
    ----------
    mode : str
        One of {"market", "breakout", "pullback"}.
        - market: enter at the first available tick within the candle window.
        - breakout: for long, enter at first tick >= candle.high; for short, first tick <= candle.low.
        - pullback: for long, enter at first tick <= candle.open - pullback_ticks * tick_value;
                    for short, first tick >= candle.open + pullback_ticks * tick_value.
    pullback_ticks : int
        Number of ticks used in pullback mode. Ignored for other modes.
    tick_value : float
        Monetary or price increment per tick used to convert tick counts into price distances.
    use_mid_when_possible : bool
        If both bid and ask exist, use mid price for comparisons and fills to avoid bias.
    """

    mode: str = "breakout"
    pullback_ticks: int = 2
    tick_value: float = 0.5
    use_mid_when_possible: bool = True


@dataclass
class HybridExitConfig:
    """
    Optional stop-loss/take-profit handling at tick resolution inside each candle.

    Attributes
    ----------
    stop_loss_ticks : Optional[int]
        If set, number of ticks for stop loss from entry price.
    take_profit_ticks : Optional[int]
        If set, number of ticks for take profit from entry price.
    priority : str
        Reserved for future policies on ordering of exit checks.
    tick_exit_decider : Optional[Callable[[int, int, dict, dict], Optional[TradeOrder]]]
        Optional callback checked on every tick j within the candle window [s, e).
        Signature: (candle_index: i, tick_index: j, data: dict, trade_info: dict) -> Optional[TradeOrder].
        If provided and returns a TradeOrder, that order is used to exit immediately.
    """

    stop_loss_ticks: Optional[int] = None
    take_profit_ticks: Optional[int] = None
    priority: str = "by_time"
    tick_exit_decider: Optional[
        Callable[[int, int, dict, dict], Optional[TradeOrder]]
    ] = None


class HybridCandleTickStrategy(TradingStrategy):
    """
    Candle-driven strategy that executes with tick-level precision.

    - Uses provided TradingSignal components to decide direction on candle i.
    - If a side is suggested, slices tick data within [candle[i], candle[i+1]) and
      applies tick-level execution rules to determine exact entry price/time.
    - Optionally, applies tick-level SL/TP checks and/or a custom tick_exit_decider for exits.

    Notes
    -----
    - Engine must be run with primary='candle' (default). Data dict must contain
      both 'candle' and 'tick'.
    - Indicators are computed only on candle data by the given signals.
    - This class intentionally keeps tick-indicator logic minimal for performance; you
      can implement price-action-based micro rules via execution config or a tick_exit_decider.
    """

    def __init__(
        self,
        signals: List[TradingSignal],
        combiner: Optional[
            Callable[[List[SignalDecision]], Tuple[Optional[str], float]]
        ] = None,
        execution: Optional[HybridExecutionConfig] = None,
        exits: Optional[HybridExitConfig] = None,
        always_active: bool = True,
    ) -> None:
        super().__init__()
        if not isinstance(signals, list) or not all(
            isinstance(s, TradingSignal) for s in signals
        ):
            raise TypeError("signals must be a list of TradingSignal instances")
        self.signals = signals
        self.combiner = combiner if combiner is not None else weighted_vote
        self.exec = execution if execution is not None else HybridExecutionConfig()
        self.exit_cfg = exits if exits is not None else HybridExitConfig()
        self.always_active = always_active

    # --- Utilities ---------------------------------------------------------

    @staticmethod
    def _choose_price_arrays(tick) -> Tuple[np.ndarray, pd.DatetimeIndex]:
        dt_arr = tick.datetime_index
        # Prefer mid if bid/ask available
        if hasattr(tick, 'bid') and hasattr(tick, 'ask'):
            price = 0.5 * (
                np.asarray(tick.bid, dtype=float) + np.asarray(tick.ask, dtype=float)
            )
            return price, dt_arr
        # Fall back to common fields
        for field in ("price", "last", "close", "bid", "ask"):
            if hasattr(tick, field):
                return np.asarray(getattr(tick, field), dtype=float), dt_arr
        raise ValueError(
            "Tick data must have a price-like column: price/last/close/bid/ask."
        )

    @staticmethod
    def _slice_ticks_for_candle(candle, tick, i: int) -> Tuple[int, int]:
        """
        Return (start_idx, end_idx) in tick arrays corresponding to candle i time window
        [candle_dt[i], candle_dt[i+1])
        """
        if i + 1 >= len(candle.datetime_index):
            # No next candle to bound the window
            return -1, -1
        start_dt = candle.datetime_index[i]
        end_dt = candle.datetime_index[i + 1]
        t = tick.datetime_index
        # Use searchsorted on numpy int64 timestamps for speed
        t64 = t.view('int64')
        s = int(
            np.searchsorted(t64, np.int64(pd.Timestamp(start_dt).value), side='left')
        )
        e = int(np.searchsorted(t64, np.int64(pd.Timestamp(end_dt).value), side='left'))
        return s, e

    def _aggregate(
        self, i: int, data: dict
    ) -> tuple[Optional[str], float, list[SignalDecision]]:
        decisions = [s.generate(i, data) for s in self.signals]
        side, strength = self.combiner(decisions)
        return side, strength, decisions

    # --- TradingStrategy interface ----------------------------------------

    def compute_indicators(self, data: dict) -> None:
        if 'candle' not in data:
            raise ValueError(
                "Hybrid strategy requires candle data for indicator computation."
            )
        for s in self.signals:
            s.compute_indicators(data)

    def entry_strategy(self, i: int, data: dict):
        if 'candle' not in data or 'tick' not in data:
            # Strategy cannot operate without both granularities
            return None
        candle = data['candle']
        tick = data['tick']

        # Candle-level decision
        side, strength, decisions = self._aggregate(i, data)
        if side not in ("long", "short"):
            return None

        # Find tick window for this candle
        s, e = self._slice_ticks_for_candle(candle, tick, i)
        if s < 0 or e <= s:
            return None  # no ticks found or last candle without a next bound

        price_arr, dt_arr = self._choose_price_arrays(tick)
        # Candle reference levels
        c_open = float(candle.open[i])
        c_high = float(candle.high[i])
        c_low = float(candle.low[i])

        # Select target condition based on execution mode
        if self.exec.mode == 'market':
            j = s  # first tick in window
            price = float(price_arr[j])
            dt = dt_arr[j]
            order_type = 'buy' if side == 'long' else 'sell'
            return TradeOrder(
                type=order_type,
                price=price,
                datetime=dt,
                amount=1,
                info={
                    'decisions': [
                        {
                            'label': sig.__class__.__name__,
                            'side': dec.side,
                            'strength': float(getattr(dec, 'strength', 0.0)),
                        }
                        for sig, dec in zip(self.signals, decisions)
                    ]
                },
            )

        elif self.exec.mode == 'breakout':
            if side == 'long':
                # Enter at first tick touching or exceeding candle high
                mask = price_arr[s:e] >= c_high
            else:
                mask = price_arr[s:e] <= c_low
            rel_idx = np.argmax(mask) if mask.any() else -1
            if rel_idx >= 0:
                j = s + int(rel_idx)
                price = float(price_arr[j])
                dt = dt_arr[j]
                order_type = 'buy' if side == 'long' else 'sell'
                return TradeOrder(
                    type=order_type,
                    price=price,
                    datetime=dt,
                    amount=1,
                    info={
                        'decisions': [
                            {
                                'label': sig.__class__.__name__,
                                'side': dec.side,
                                'strength': float(getattr(dec, 'strength', 0.0)),
                            }
                            for sig, dec in zip(self.signals, decisions)
                        ]
                    },
                )

        elif self.exec.mode == 'pullback':
            delta = self.exec.pullback_ticks * self.exec.tick_value
            if side == 'long':
                level = c_open - delta
                mask = price_arr[s:e] <= level
            else:
                level = c_open + delta
                mask = price_arr[s:e] >= level
            rel_idx = np.argmax(mask) if mask.any() else -1
            if rel_idx >= 0:
                j = s + int(rel_idx)
                price = float(price_arr[j])
                dt = dt_arr[j]
                order_type = 'buy' if side == 'long' else 'sell'
                return TradeOrder(
                    type=order_type,
                    price=price,
                    datetime=dt,
                    amount=1,
                    info={
                        'decisions': [
                            {
                                'label': sig.__class__.__name__,
                                'side': dec.side,
                                'strength': float(getattr(dec, 'strength', 0.0)),
                            }
                            for sig, dec in zip(self.signals, decisions)
                        ]
                    },
                )

        return None

    def exit_strategy(self, i: int, data: dict, trade_info: dict):
        # Optional tick-level SL/TP management and custom callback inside the candle window
        if 'candle' not in data or 'tick' not in data:
            return None
        if (
            self.exit_cfg.stop_loss_ticks is None
            and self.exit_cfg.take_profit_ticks is None
            and self.exit_cfg.tick_exit_decider is None
        ):
            return None

        candle = data['candle']
        tick = data['tick']

        s, e = self._slice_ticks_for_candle(candle, tick, i)
        if s < 0 or e <= s:
            return None

        price_arr, dt_arr = self._choose_price_arrays(tick)
        entry_price = float(trade_info['price'])
        tv = float(self.exec.tick_value)

        # Scan tick-by-tick for the first exit condition met.
        if trade_info['type'] == 'buy':
            sl = entry_price - (self.exit_cfg.stop_loss_ticks or 0) * tv
            tp = entry_price + (self.exit_cfg.take_profit_ticks or 0) * tv
            for j in range(s, e):
                # Custom tick-level exit callback (e.g., micro indicator) takes precedence
                if self.exit_cfg.tick_exit_decider is not None:
                    custom = self.exit_cfg.tick_exit_decider(i, j, data, trade_info)
                    if isinstance(custom, TradeOrder):
                        return custom
                p = float(price_arr[j])
                if self.exit_cfg.stop_loss_ticks is not None and p <= sl:
                    return TradeOrder(
                        type='close',
                        price=p,
                        datetime=dt_arr[j],
                        amount=1,
                        info={'exit': 'stop_loss', 'sl': sl, 'tp': tp},
                    )
                if self.exit_cfg.take_profit_ticks is not None and p >= tp:
                    return TradeOrder(
                        type='close',
                        price=p,
                        datetime=dt_arr[j],
                        amount=1,
                        info={'exit': 'take_profit', 'sl': sl, 'tp': tp},
                    )

        elif trade_info['type'] == 'sell':
            sl = entry_price + (self.exit_cfg.stop_loss_ticks or 0) * tv
            tp = entry_price - (self.exit_cfg.take_profit_ticks or 0) * tv
            for j in range(s, e):
                if self.exit_cfg.tick_exit_decider is not None:
                    custom = self.exit_cfg.tick_exit_decider(i, j, data, trade_info)
                    if isinstance(custom, TradeOrder):
                        return custom
                p = float(price_arr[j])
                if self.exit_cfg.stop_loss_ticks is not None and p >= sl:
                    return TradeOrder(
                        type='close',
                        price=p,
                        datetime=dt_arr[j],
                        amount=1,
                        info={'exit': 'stop_loss', 'sl': sl, 'tp': tp},
                    )
                if self.exit_cfg.take_profit_ticks is not None and p <= tp:
                    return TradeOrder(
                        type='close',
                        price=p,
                        datetime=dt_arr[j],
                        amount=1,
                        info={'exit': 'take_profit', 'sl': sl, 'tp': tp},
                    )

        return None
