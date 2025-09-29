from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional, List, Tuple

from src.strategies.signals import SignalDecision


def _clip01(x: float) -> float:
    """Clip a number to the inclusive range [0.0, 1.0]."""
    try:
        xf = float(x)
    except Exception:
        return 0.0
    if xf < 0.0:
        return 0.0
    if xf > 1.0:
        return 1.0
    return xf


class SignalCombiner(ABC):
    """
    Abstract base class for signal combiners.
    """

    @abstractmethod
    def combine(
        self, decisions: Iterable[SignalDecision]
    ) -> Tuple[Optional[str], float]:
        """
        Takes an iterable of SignalDecision objects and returns a single
        combined decision as a (side, strength) tuple.
        """
        raise NotImplementedError

    def __call__(
        self, decisions: Iterable[SignalDecision]
    ) -> Tuple[Optional[str], float]:
        return self.combine(decisions)


class GatedCombiner(SignalCombiner):
    """
    Combiner that gates entry signals by one or more filter signals.

    A trade signal is emitted only if the configured filter signals are active
    (side is not None and strength > 0). If filters are active, the entry
    signals are tallied. If require_entry_agreement is True, all non-neutral
    entry signals must agree on the same side, otherwise neutral is returned.

    Parameters
    ----------
    filter_indices : list[int]
        Indices of filter signals within the CompositeStrategy.signals list.
    entry_indices : list[int]
        Indices of entry signals within the CompositeStrategy.signals list.
    require_all_filters : bool
        If True, all filters must be active; otherwise at least one active
        filter is sufficient.
    require_entry_agreement : bool
        If True, all active entry signals must agree on side; otherwise a
        weighted vote among entry signals determines the side.
    """

    def __init__(
        self,
        filter_indices: List[int],
        entry_indices: List[int],
        require_all_filters: bool = False,
        require_entry_agreement: bool = True,
    ):
        self.fi = list(filter_indices)
        self.ei = list(entry_indices)
        self.require_all_filters = require_all_filters
        self.require_entry_agreement = require_entry_agreement

    def combine(
        self, decisions: Iterable[SignalDecision]
    ) -> Tuple[Optional[str], float]:
        decs = list(decisions)
        # Validate indices: if any out-of-bounds, return neutral safely.
        if any(k < 0 or k >= len(decs) for k in self.fi + self.ei):
            return None, 0.0

        # Determine if filters are active
        active_flags: List[bool] = []
        for k in self.fi:
            d = decs[k]
            active_flags.append(
                (getattr(d, 'side', None) is not None)
                and (_clip01(getattr(d, 'strength', 0.0)) > 0.0)
            )
        if not active_flags:
            # No filters configured: let entries decide
            filters_active = True
        else:
            filters_active = (
                all(active_flags) if self.require_all_filters else any(active_flags)
            )
        if not filters_active:
            return None, 0.0

        # Tally entry signals
        long_sum = 0.0
        short_sum = 0.0
        entry_sides: List[str] = []
        for k in self.ei:
            d = decs[k]
            s = _clip01(getattr(d, 'strength', 0.0))
            sd = getattr(d, 'side', None)
            if sd == 'long':
                long_sum += s
                entry_sides.append('long')
            elif sd == 'short':
                short_sum += s
                entry_sides.append('short')

        total = long_sum + short_sum
        if total == 0.0:
            return None, 0.0

        if self.require_entry_agreement:
            if not entry_sides:
                return None, 0.0
            agree = all(x == entry_sides[0] for x in entry_sides)
            if not agree:
                return None, 0.0

        net = long_sum - short_sum
        if net == 0.0:
            return None, 0.0
        side = 'long' if net > 0.0 else 'short'
        strength = min(1.0, abs(net) / total) if total > 0.0 else 0.0
        return side, strength


class ThresholdedWeightedVote(SignalCombiner):
    """
    Like weighted_vote but emits only if absolute net >= threshold.

    threshold is on the absolute net (long_sum - short_sum) scale, not normalized.
    """

    def __init__(self, threshold: float):
        thr = float(threshold)
        if thr < 0.0:
            thr = 0.0
        self.thr = thr

    def combine(
        self, decisions: Iterable[SignalDecision]
    ) -> Tuple[Optional[str], float]:
        long_sum = 0.0
        short_sum = 0.0
        for d in decisions:
            s = _clip01(getattr(d, 'strength', 0.0))
            sd = getattr(d, 'side', None)
            if sd == 'long':
                long_sum += s
            elif sd == 'short':
                short_sum += s
        net = long_sum - short_sum
        total = long_sum + short_sum
        if total == 0.0:
            return None, 0.0
        if abs(net) < self.thr:
            return None, 0.0
        side = 'long' if net > 0.0 else 'short'
        strength = min(1.0, abs(net) / total) if total > 0.0 else 0.0
        return side, strength


essential_types = (int, float)


class WeightedSignalCombiner(SignalCombiner):
    """
    Weight each incoming signal strength by a provided weight vector before tallying.

    Parameters
    ----------
    weights : list[float]
        Non-negative weights per signal, matching the number/order of signals.
    normalize_weights : bool
        If True, weights will be scaled to sum to 1 (when sum > 0).
    """

    def __init__(
        self,
        weights: List[float],
        normalize_weights: bool = False,
    ):
        self.base_weights = [
            float(w) if isinstance(w, essential_types) else 0.0 for w in list(weights)
        ]
        self.base_weights = [w if w > 0.0 else 0.0 for w in self.base_weights]
        self.normalize_weights = normalize_weights

    def combine(
        self, decisions: Iterable[SignalDecision]
    ) -> Tuple[Optional[str], float]:
        decs = list(decisions)
        if len(decs) != len(self.base_weights):
            raise ValueError(
                f"weights length ({len(self.base_weights)}) must match decisions length ({len(decs)})"
            )
        w = self.base_weights
        if self.normalize_weights:
            ssum = sum(w)
            if ssum > 0.0:
                w = [x / ssum for x in w]

        long_sum = 0.0
        short_sum = 0.0
        for i, d in enumerate(decs):
            s = _clip01(getattr(d, 'strength', 0.0)) * w[i]
            sd = getattr(d, 'side', None)
            if sd == 'long':
                long_sum += s
            elif sd == 'short':
                short_sum += s

        net = long_sum - short_sum
        total = long_sum + short_sum
        if total == 0.0 or net == 0.0:
            return None, 0.0
        side = 'long' if net > 0.0 else 'short'
        strength = min(1.0, abs(net) / total)
        return side, strength


class HybridSignalCombiner(SignalCombiner):
    """
    Convenience combiner for HybridCandleTickStrategy.

    Wraps either a WeightedSignalCombiner or GatedCombiner (or any SignalCombiner)
    and exposes a unified interface for use in hybrid strategies. Also exposes
    class methods to build from common configurations.
    """

    def __init__(self, combiner: SignalCombiner):
        if not isinstance(combiner, SignalCombiner):
            raise TypeError("combiner must be an instance of SignalCombiner")
        self._inner = combiner

    def combine(
        self, decisions: Iterable[SignalDecision]
    ) -> Tuple[Optional[str], float]:
        return self._inner.combine(decisions)

    @classmethod
    def from_weights(
        cls, weights: List[float], normalize_weights: bool = False
    ) -> 'HybridSignalCombiner':
        return cls(
            WeightedSignalCombiner(weights=weights, normalize_weights=normalize_weights)
        )

    @classmethod
    def gated(
        cls,
        filter_indices: List[int],
        entry_indices: List[int],
        require_all_filters: bool = False,
        require_entry_agreement: bool = True,
    ) -> 'HybridSignalCombiner':
        return cls(
            GatedCombiner(
                filter_indices=filter_indices,
                entry_indices=entry_indices,
                require_all_filters=require_all_filters,
                require_entry_agreement=require_entry_agreement,
            )
        )
