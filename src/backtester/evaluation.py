# Evaluation module for strategy results
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional

from .trades import TradeRegistry


@dataclass(frozen=True)
class AcceptanceCriteria:
    """Hard gates to quickly reject poor or fragile strategies.

    All thresholds use common sense units:
    - drawdown is a fraction in [0,1] (e.g., 0.25 == 25%)
    - rates are fractions in [0,1] (e.g., 0.55 == 55%)
    - other metrics are as-is
    """

    min_trades: int = 150
    min_profit_factor: float = 1.20
    max_drawdown: float = 0.25
    min_sharpe: Optional[float] = None
    min_cagr: Optional[float] = None
    min_win_rate: Optional[float] = None
    max_consecutive_losses: Optional[int] = None


@dataclass(frozen=True)
class EvaluationResult:
    score: float
    passed: bool
    label: str
    reasons: List[str]
    metrics: Dict[str, float]


class StrategyEvaluator:
    """Scores and classifies strategy results based on metrics.

    The evaluator computes a weighted score in [0,1] based on the provided
    metrics and determines a label among {A, B, C, REJECT} according to the
    acceptance gates and final score.
    """

    def __init__(
        self,
        criteria: AcceptanceCriteria,
        weights: Optional[Dict[str, float]] = None,
        target_cagr: float = 0.20,
    ) -> None:
        self.criteria = criteria
        self.target_cagr = target_cagr
        # Default weights prioritize risk-adjusted robustness
        self.weights = weights or {
            "profit_factor": 0.35,
            "max_drawdown": 0.30,  # lower is better (handled via transform)
            "win_rate": 0.10,
            "trades": 0.10,
            # optional if present
            "sharpe": 0.10,
            "cagr": 0.05,
        }

    def evaluate(self, metrics: Mapping[str, float]) -> EvaluationResult:
        reasons: List[str] = []
        passed = self._check_gates(metrics, reasons)
        score = self._score(metrics)
        label = self._label(score, passed)
        return EvaluationResult(
            score=score,
            passed=passed,
            label=label,
            reasons=reasons,
            metrics=dict(metrics),
        )

    def score_only(self, metrics: Mapping[str, float]) -> float:
        """Public scoring helper: compute only the normalized score in [0,1]."""
        return self._score(metrics)

    def _check_gates(self, m: Mapping[str, float], reasons: List[str]) -> bool:
        c = self.criteria
        ok = True
        # Required trades
        if int(m.get("trades", 0)) < c.min_trades:
            ok = False
            reasons.append(f"trades<{c.min_trades}")
        # Profit factor
        if m.get("profit_factor", 0.0) < c.min_profit_factor:
            ok = False
            reasons.append(f"profit_factor<{c.min_profit_factor}")
        # Max drawdown as fraction
        dd = m.get("max_drawdown", None)
        if dd is not None and dd > c.max_drawdown:
            ok = False
            reasons.append(f"max_drawdown>{c.max_drawdown}")
        # Optional gates
        if c.min_sharpe is not None and m.get("sharpe", 0.0) < c.min_sharpe:
            ok = False
            reasons.append(f"sharpe<{c.min_sharpe}")
        if c.min_cagr is not None and m.get("cagr", 0.0) < c.min_cagr:
            ok = False
            reasons.append(f"cagr<{c.min_cagr}")
        if c.min_win_rate is not None and m.get("win_rate", 0.0) < c.min_win_rate:
            ok = False
            reasons.append(f"win_rate<{c.min_win_rate}")
        if (
            c.max_consecutive_losses is not None
            and m.get("max_consecutive_losses", 0) > c.max_consecutive_losses
        ):
            ok = False
            reasons.append(f"max_consecutive_losses>{c.max_consecutive_losses}")
        return ok

    def _score(self, m: Mapping[str, float]) -> float:
        # Helpers
        def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
            return max(a, min(b, float(x)))

        # Normalized component scores in [0,1]
        pf = float(m.get("profit_factor", 1.0))
        pf_score = clamp((pf - 1.0) / 1.5)  # PF 2.5+ -> ~1.0

        dd = m.get("max_drawdown", None)
        if dd is None:
            dd_score = 0.5
        else:
            # lower DD -> higher score, full score if dd <= half the max allowed
            dd_score = clamp(1.0 - (float(dd) / max(self.criteria.max_drawdown, 1e-9)))

        sharpe = float(m.get("sharpe", 0.0))
        sharpe_score = clamp(sharpe / 2.0)  # Sharpe 2.0 -> 1.0

        cagr = float(m.get("cagr", 0.0))
        cagr_score = clamp(cagr / max(self.target_cagr, 1e-9))  # target_cagr -> 1.0

        trades = float(m.get("trades", 0.0))
        trades_score = clamp(
            (trades - float(self.criteria.min_trades))
            / max(float(self.criteria.min_trades), 1.0)
        )

        win_rate = float(m.get("win_rate", 0.0))  # 0..1
        win_rate_score = clamp((win_rate - 0.5) / 0.4)  # 90% -> 1, 50% -> 0

        # Optional stability penalty if available (0..1 where 1=stable)
        stability = float(m.get("oos_stability", 1.0))
        stability = clamp(stability, 0.0, 1.0)

        components: Dict[str, float] = {
            "profit_factor": pf_score,
            "max_drawdown": dd_score,
            "sharpe": sharpe_score,
            "cagr": cagr_score,
            "trades": trades_score,
            "win_rate": win_rate_score,
        }

        # Weighted sum
        wsum = 0.0
        wtot = 0.0
        for k, w in self.weights.items():
            v = components.get(k, 0.0)
            wsum += float(w) * float(v)
            wtot += float(w)
        base = wsum / max(wtot, 1e-9)

        # Apply stability penalty multiplicatively if present
        return clamp(base * stability)

    def _label(self, score: float, passed: bool) -> str:
        if not passed:
            return "REJECT"
        if score >= 0.80:
            return "A"
        if score >= 0.60:
            return "B"
        return "C"


def metrics_from_trade_registry(tr: TradeRegistry) -> Dict[str, float]:
    """Extract a standard metrics mapping from a TradeRegistry.

    Returns keys:
    - trades: int
    - profit_factor: float
    - max_drawdown: float (fraction, e.g., 0.23 for 23%)
    - win_rate: float (fraction, e.g., 0.55)
    - Optional: cagr, sharpe, max_consecutive_losses, oos_stability if they exist
    """
    # Ensure computed fields are available
    tr._process_trades()

    # Drawdown from internal calculator (percentage)
    dd_info = tr._compute_maximum_drawdown()
    dd_frac = None
    if isinstance(dd_info, dict) and dd_info.get("drawdown_relative") is not None:
        try:
            dd_frac = float(dd_info["drawdown_relative"]) / 100.0
        except Exception:
            dd_frac = None

    # Accuracy property returns percentage (0..100); convert to fraction
    try:
        acc_pct = tr.accuracy
        win_rate = float(acc_pct) / 100.0 if acc_pct is not None else 0.0
    except Exception:
        win_rate = 0.0

    # Optional attributes: default to sensible values
    def get_optional(name: str, default: float = 0.0) -> float:
        try:
            return float(getattr(tr, name))
        except Exception:
            return default

    metrics: Dict[str, float] = {
        "trades": (
            float(len(tr.trades)) if getattr(tr, "trades", None) is not None else 0.0
        ),
        "profit_factor": float(getattr(tr, "profit_factor", 0.0)),
        "max_drawdown": dd_frac if dd_frac is not None else 0.0,
        "win_rate": win_rate,
        # Optionals
        "sharpe": get_optional("sharpe", 0.0),
        "cagr": get_optional("cagr", 0.0),
        "max_consecutive_losses": get_optional("max_consecutive_losses", 0.0),
        "oos_stability": get_optional("oos_stability", 1.0),
    }
    return metrics


def oos_stability_from_two_runs(
    registry_is: TradeRegistry,
    registry_oos: TradeRegistry,
    evaluator: StrategyEvaluator,
) -> float:
    """Compute a simple out-of-sample stability metric.

    Returns a value in [0,1], where 1.0 means identical scores and 0.0 means
    maximally divergent (|score_is - score_oos| == 1).
    """
    m_is = metrics_from_trade_registry(registry_is)
    m_oos = metrics_from_trade_registry(registry_oos)
    s_is = evaluator.score_only(m_is)
    s_oos = evaluator.score_only(m_oos)
    return max(0.0, 1.0 - abs(s_is - s_oos))
