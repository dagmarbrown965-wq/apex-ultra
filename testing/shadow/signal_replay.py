"""
APEX ULTRA — Shadow Signal Replay (Phase 40, TEST FIXTURE)

A deterministic, synthetic signal source used ONLY for offline dry-run flow
checks of the shadow burn-in machinery. It stands in for the real APEX signal +
risk pipeline and is NEVER a substitute for real signals in a --real run.

It does not implement, replace, or modify strategy/indicator/signal/risk logic.
In a real run, the operator injects the actual signal stream instead of this.
"""

from __future__ import annotations

import random

from infrastructure.broker.broker_interface import OrderSide
from infrastructure.broker.deriv import ShadowSignal

SYMBOLS = ["R_100", "R_75", "R_50"]
STRATEGIES = ["ensemble", "regime_trend", "mean_revert", "breakout"]
REGIMES = ["trend_up", "trend_down", "range", "high_vol", "low_vol"]


class ShadowSignalReplay:
    """Synthetic signal generator (fixture). Yields ShadowSignal objects with
    predetermined outcomes so win-rate/R metrics can be exercised offline."""

    def __init__(self, seed: int = 40, target_win_rate: float = 0.53,
                 reject_rate: float = 0.08, start_ts: float = 0.0,
                 seconds_per_signal: float = 0.0) -> None:
        self._rng = random.Random(seed)
        self.target_win_rate = target_win_rate
        self.reject_rate = reject_rate
        self._ts = start_ts
        self._dt = seconds_per_signal

    def next(self) -> ShadowSignal:
        self._ts += self._dt
        accepted = self._rng.random() >= self.reject_rate
        win = self._rng.random() < self.target_win_rate
        if accepted:
            r = round(self._rng.uniform(1.2, 2.4), 2) if win else -1.0
            outcome = "win" if win else "loss"
        else:
            r, outcome = 0.0, None
        return ShadowSignal(
            timestamp=self._ts,
            symbol=self._rng.choice(SYMBOLS),
            strategy=self._rng.choice(STRATEGIES),
            direction=OrderSide.BUY if self._rng.random() < 0.5 else OrderSide.SELL,
            score=round(self._rng.uniform(0.5, 0.99), 3),
            regime=self._rng.choice(REGIMES),
            risk_size=round(self._rng.uniform(5.0, 20.0), 2),
            stop_loss=round(self._rng.uniform(3.0, 8.0), 2),
            take_profit=round(self._rng.uniform(8.0, 16.0), 2),
            accepted=accepted,
            reject_reason="" if accepted else "risk_guard",
            outcome=outcome,
            r_multiple=r,
        )
