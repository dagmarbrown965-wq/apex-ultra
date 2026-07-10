"""ReferenceMA â€” deterministic EMA-crossover reference strategy.

Phase 42.0B-M0. Purpose is NOT profitability or optimization â€” only to prove the
signal path with a real, deterministic computation. Computes a fast and slow EMA
over the snapshot's closing prices and emits a Decision when they cross / differ.

Imports nothing from any broker or execution surface. Computes no order, no size.
"""
from __future__ import annotations

from engine.feed.base import MarketSnapshot
from engine.strategy.base import Decision, Strategy


def _ema(values: tuple, period: int) -> float:
    """Plain exponential moving average over `values`, returning the last EMA.

    Deterministic. Seeds with the first value, then applies the standard
    smoothing constant k = 2 / (period + 1).
    """
    if not values:
        raise ValueError("cannot compute EMA over empty price series")
    k = 2.0 / (period + 1.0)
    ema = float(values[0])
    for v in values[1:]:
        ema = float(v) * k + ema * (1.0 - k)
    return ema


class ReferenceMA(Strategy):
    """Minimal EMA-crossover producer (fast vs slow).

    direction: "long" when fast EMA > slow EMA, "short" when fast < slow.
    score: 0-100, scaled from the relative gap between the EMAs (bounded).
    Returns None only when there is insufficient data or the EMAs are exactly
    equal (a genuine no-signal condition).
    """

    name = "reference_ma"

    def __init__(self, fast: int = 5, slow: int = 20) -> None:
        if fast <= 0 or slow <= 0:
            raise ValueError("EMA periods must be positive")
        if fast >= slow:
            raise ValueError("fast period must be shorter than slow period")
        self.fast = fast
        self.slow = slow

    def evaluate(self, snapshot: MarketSnapshot) -> "Decision | None":
        prices = snapshot.prices
        if len(prices) < self.slow:
            return None  # not enough data to form the slow EMA â€” no signal

        fast_ema = _ema(prices, self.fast)
        slow_ema = _ema(prices, self.slow)

        if fast_ema == slow_ema:
            return None  # exactly flat â€” genuine no-signal

        direction = "long" if fast_ema > slow_ema else "short"

        # Score: relative EMA gap as a percentage of the slow EMA, scaled and
        # clamped to [0, 100]. Deterministic, descriptive only.
        gap_pct = abs(fast_ema - slow_ema) / abs(slow_ema) * 100.0
        score = max(0.0, min(100.0, gap_pct * 10.0))

        return Decision(direction=direction, conviction=score / 100.0)
