"""EmaCross -- real EMA-crossover strategy (Phase 42.1).

Unlike ReferenceMA (which reports "long"/"short" on EVERY close where the
EMAs differ), EmaCross emits a Decision ONLY at the crossing moment:

  - fast EMA moves from at-or-below the slow EMA to above it  -> "long"
  - fast EMA moves from at-or-above the slow EMA to below it  -> "short"
  - otherwise                                                 -> None

Silence is the normal output. Deterministic and stateless: the previous
relationship is recomputed from prices[:-1], so no state is carried between
calls and the snapshot path stays reproducible.

Parameters are FIXED by docs/PHASE_42_1_BOUNDARY_AGREEMENT.md: fast=9,
slow=21. No tuning against live data.

Imports nothing from any broker or execution surface. Computes no order,
no size, no price levels.
"""
from __future__ import annotations

from engine.feed.base import MarketSnapshot
from engine.strategy.base import Decision, Strategy


def _ema(values: tuple, period: int) -> float:
    """Plain exponential moving average over `values`, returning the last EMA.

    Deterministic. Seeds with the first value, then applies the standard
    smoothing constant k = 2 / (period + 1). (Same construction as the
    reference implementation; duplicated here so this module depends only
    on the Strategy contract, not on the placeholder file.)
    """
    if not values:
        raise ValueError("cannot compute EMA over empty price series")
    k = 2.0 / (period + 1.0)
    ema = float(values[0])
    for v in values[1:]:
        ema = float(v) * k + ema * (1.0 - k)
    return ema


class EmaCross(Strategy):
    """EMA(9/21) crossing-moment producer.

    direction: "long" on a cross up, "short" on a cross down.
    conviction: relative EMA gap at the cross, same bounded scaling as the
    reference (gap %% of slow EMA x10, clamped to [0, 100], mapped to
    [0, 1]). At a fresh cross the gap is naturally small, so conviction
    will typically be low -- that is honest, not a bug.

    Returns None when there is insufficient data (needs slow+1 closes to
    know both the previous and current relationship) or when no cross
    occurred on the newest close.
    """

    name = "ema_cross"

    def __init__(self, fast: int = 9, slow: int = 21) -> None:
        if fast <= 0 or slow <= 0:
            raise ValueError("EMA periods must be positive")
        if fast >= slow:
            raise ValueError("fast period must be shorter than slow period")
        self.fast = fast
        self.slow = slow

    def evaluate(self, snapshot: MarketSnapshot) -> "Decision | None":
        prices = snapshot.prices
        if len(prices) < self.slow + 1:
            return None  # cannot form previous + current slow EMA -- no signal

        prev = tuple(prices[:-1])

        prev_rel = _ema(prev, self.fast) - _ema(prev, self.slow)
        curr_fast = _ema(prices, self.fast)
        curr_slow = _ema(prices, self.slow)
        curr_rel = curr_fast - curr_slow

        if prev_rel <= 0.0 and curr_rel > 0.0:
            direction = "long"
        elif prev_rel >= 0.0 and curr_rel < 0.0:
            direction = "short"
        else:
            return None  # no cross on the newest close -- genuine silence

        gap_pct = abs(curr_rel) / abs(curr_slow) * 100.0
        score = max(0.0, min(100.0, gap_pct * 10.0))
        return Decision(direction=direction, conviction=score / 100.0)
