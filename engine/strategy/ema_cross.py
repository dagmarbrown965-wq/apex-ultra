"""EmaCross -- real EMA-crossover strategy (Phase 42.1, revised 42.1a).

Emits a Decision ONLY at the crossing moment:

  - fast EMA moves from below the slow EMA to above it -> "long"
  - fast EMA moves from above the slow EMA to below it -> "short"
  - otherwise                                          -> None

Silence is the normal output.

42.1a revision (see docs/PHASE_42_1_ADDENDUM.md section C): the original
implementation reconstructed the "previous" relationship from prices[:-1].
Over a SLIDING buffer (live feed, maxlen 25) that reconstruction sees a
different window than the prior evaluation actually saw, and EMA seeding
from the first window element can flip the sign while the EMAs hover near
equality -- i.e. exactly around genuine crossings -- producing duplicate
signals. Fix: the strategy now remembers the last relationship sign it
computed (+1 fast above slow, -1 fast below slow) and emits only when the
newly computed sign differs from the remembered one. The first evaluation
with sufficient data only RECORDS the sign and emits nothing (no invented
"previous" state). If the EMAs are exactly equal, the remembered sign is
kept and nothing is emitted.

Determinism: given the same sequence of snapshots from a fresh instance,
the output sequence is identical. One instance = one session (the runner
constructs a fresh strategy per session, so no state leaks across
sessions). The snapshot/regression path (run_once) uses ReferenceMA and
is unaffected; a single EmaCross evaluation on a fresh instance returns
None by design.

Parameters remain FIXED by docs/PHASE_42_1_BOUNDARY_AGREEMENT.md:
fast=9, slow=21. This revision is a correctness fix, not tuning.

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
    """EMA(9/21) crossing-moment producer with per-session sign state.

    direction: "long" on a cross up, "short" on a cross down.
    conviction: relative EMA gap at the cross, bounded scaling as in the
    reference (gap %% of slow EMA x10, clamped to [0, 100], mapped to
    [0, 1]). At a fresh cross the gap is naturally small, so conviction
    will typically be low -- that is honest, not a bug.

    Returns None when: insufficient data (< slow closes); first
    sufficient evaluation (sign recorded, nothing emitted); EMAs exactly
    equal; or no sign change since the last evaluation.
    """

    name = "ema_cross"

    def __init__(self, fast: int = 9, slow: int = 21) -> None:
        if fast <= 0 or slow <= 0:
            raise ValueError("EMA periods must be positive")
        if fast >= slow:
            raise ValueError("fast period must be shorter than slow period")
        self.fast = fast
        self.slow = slow
        self._last_sign = 0  # 0 = unknown; +1 fast above slow; -1 below

    def evaluate(self, snapshot: MarketSnapshot) -> "Decision | None":
        prices = snapshot.prices
        if len(prices) < self.slow:
            return None  # cannot form the slow EMA -- no signal

        curr_fast = _ema(prices, self.fast)
        curr_slow = _ema(prices, self.slow)
        rel = curr_fast - curr_slow

        if rel > 0.0:
            sign = 1
        elif rel < 0.0:
            sign = -1
        else:
            return None  # exactly equal: keep remembered sign, stay silent

        if self._last_sign == 0:
            self._last_sign = sign
            return None  # first reading: record, do not invent a cross

        if sign == self._last_sign:
            return None  # no cross since last evaluation -- genuine silence

        # sign changed: this IS the crossing moment
        self._last_sign = sign
        direction = "long" if sign > 0 else "short"
        gap_pct = abs(rel) / abs(curr_slow) * 100.0
        score = max(0.0, min(100.0, gap_pct * 10.0))
        return Decision(direction=direction, conviction=score / 100.0)
