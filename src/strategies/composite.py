from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Tuple

from src.backtester import TradingStrategy, TradeOrder
from src.strategies.signals import TradingSignal, SignalDecision


def weighted_vote(decisions: Iterable[SignalDecision]) -> Tuple[Optional[str], float]:
    """
    Default combiner: sums strengths as + for long, - for short.

    Returns a tuple (side, strength):
    - side in {"long", "short", None}
    - strength in [0, 1]
    """
    long_sum = 0.0
    short_sum = 0.0

    for d in decisions:
        if d.side == 'long':
            long_sum += max(0.0, min(1.0, d.strength))
        elif d.side == 'short':
            short_sum += max(0.0, min(1.0, d.strength))

    net = long_sum - short_sum
    total = long_sum + short_sum

    if total == 0.0:
        return None, 0.0
    if net == 0.0:
        return None, 0.0

    side = 'long' if net > 0 else 'short'
    # Normalize absolute net by total to get a confidence in [0, 1]
    strength = min(1.0, max(0.0, abs(net) / total))
    return side, strength


class CompositeStrategy(TradingStrategy):
    """
    Composite strategy that aggregates multiple TradingSignal components.

    Parameters
    ----------
    signals : list[TradingSignal]
        A list of signal instances to be computed and combined.
    combiner : Callable[[list[SignalDecision]], tuple[Optional[str], float]]
        Function that aggregates signals into an overall decision (side, strength).
        Defaults to a weighted vote by signal strength.
    always_active : bool
        If True, opposite aggregate signals will invert the position; if False,
        opposite signals will close the position.

    Example
    -------
    from src.strategies.signals.ma_crossover import MaCrossoverSignal
    from src.strategies.signals.bbands import BollingerBandSignal
    from src.strategies.composite import CompositeStrategy

    signals = [
        MaCrossoverSignal(tick_value=0.25, short_ma_period=9, long_ma_period=21),
        BollingerBandSignal(length=20, std=2.0)
    ]
    strategy = CompositeStrategy(signals=signals, always_active=True)
    """

    def __init__(
        self,
        signals: List[TradingSignal],
        combiner: Optional[Callable[[List[SignalDecision]], tuple[Optional[str], float]]] = None,
        always_active: bool = True,
    ) -> None:
        super().__init__()
        if not isinstance(signals, list) or not all(isinstance(s, TradingSignal) for s in signals):
            raise TypeError("signals must be a list of TradingSignal instances")
        self.signals = signals
        self.combiner = combiner if combiner is not None else weighted_vote
        self.always_active = always_active

    def compute_indicators(self, data: dict) -> None:
        for s in self.signals:
            s.compute_indicators(data)

    def _aggregate(self, i: int, data: dict) -> tuple[Optional[str], float, list[SignalDecision]]:
        decisions = [s.generate(i, data) for s in self.signals]
        side, strength = self.combiner(decisions)
        return side, strength, decisions

    def entry_strategy(self, i: int, data: dict):
        candle = data['candle']
        dt = candle.datetime_index[i]
        price = float(candle.close[i])

        side, strength, decisions = self._aggregate(i, data)
        # Label decisions for analysis/reporting
        labeled = [
            {
                'label': sig.__class__.__name__,
                'side': dec.side,
                'strength': float(max(0.0, min(1.0, getattr(dec, 'strength', 0.0))))
            }
            for sig, dec in zip(self.signals, decisions)
        ]
        if side == 'long':
            return TradeOrder(type='buy', price=price, datetime=dt, amount=1, info={'decisions': labeled})
        elif side == 'short':
            return TradeOrder(type='sell', price=price, datetime=dt, amount=1, info={'decisions': labeled})
        else:
            return None

    def exit_strategy(self, i: int, data: dict, trade_info: dict):
        candle = data['candle']
        dt = candle.datetime_index[i]
        price = float(candle.close[i])

        side, strength, decisions = self._aggregate(i, data)
        labeled = [
            {
                'label': sig.__class__.__name__,
                'side': dec.side,
                'strength': float(max(0.0, min(1.0, getattr(dec, 'strength', 0.0))))
            }
            for sig, dec in zip(self.signals, decisions)
        ]

        if trade_info['type'] == 'buy':
            if side == 'short':
                if self.always_active:
                    return TradeOrder(type='invert', price=price, datetime=dt, amount=1, info={'decisions': labeled})
                else:
                    return TradeOrder(type='close', price=price, datetime=dt, amount=1, info={'decisions': labeled})

        elif trade_info['type'] == 'sell':
            if side == 'long':
                if self.always_active:
                    return TradeOrder(type='invert', price=price, datetime=dt, amount=1, info={'decisions': labeled})
                else:
                    return TradeOrder(type='close', price=price, datetime=dt, amount=1, info={'decisions': labeled})

        return None
