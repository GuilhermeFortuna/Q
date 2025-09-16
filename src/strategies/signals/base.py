from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from abc import ABC, abstractmethod


SignalSide = Literal["long", "short"]


@dataclass
class SignalDecision:
    """
    Represents a decision emitted by a TradingSignal at a specific bar (index).

    Attributes:
        side: Optional direction suggestion. "long" for buy bias, "short" for sell bias, or None for neutral.
        strength: Confidence/weight of the signal in [0.0, 1.0].
        info: Extra diagnostic data about the signal computation (for debugging/visualization).
    """

    side: Optional[SignalSide] = None
    strength: float = 0.0
    info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Clamp strength to [0, 1]
        if self.strength < 0.0:
            self.strength = 0.0
        elif self.strength > 1.0:
            self.strength = 1.0


class TradingSignal(ABC):
    """
    Base interface for composable trading signals.

    Each signal can:
    - compute_indicators: pre-compute indicator columns on data['candle'].data DataFrame.
    - generate: emit a SignalDecision for a given index i.

    Notes on data access:
    The backtesting engine will call strategy.compute_indicators(data) and afterwards
    call data['candle'].set_values_as_attrs(), which exposes dataframe columns as
    numpy arrays on data['candle'] (e.g., candle.close[i]). Therefore, compute_indicators
    should add any required indicator columns to data['candle'].data.
    """

    @abstractmethod
    def compute_indicators(self, data: dict) -> None:
        """Add necessary indicator columns to data['candle'].data in-place."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, i: int, data: dict) -> SignalDecision:
        """
        Produce a SignalDecision for bar index i using the prepared indicators.
        """
        raise NotImplementedError
