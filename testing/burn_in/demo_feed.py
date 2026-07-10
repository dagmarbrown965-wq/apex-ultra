"""
APEX ULTRA — Demo Feed Fixture (Phase 36)

TEST FIXTURE ONLY. This is a deterministic synthetic feed used to drive the
burn-in controller during controlled demo runs. It stands in for an upstream
signal stream / recorded replay. It does NOT implement, replace, or modify the
production strategies, indicators, or signal-generation logic — it only emits
pre-shaped signal envelopes plus a predetermined outcome so the burn-in
machinery can be exercised end to end.

Swap this for a real recorded signal replay when running against live demo data.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from infrastructure.broker import OrderSide


REGIMES = ["trend_up", "trend_down", "range", "high_vol", "low_vol"]
STRATEGIES = ["ensemble", "regime_trend", "mean_revert", "breakout"]
ASSETS = ["APEX", "BTCUSD", "ETHUSD", "EURUSD"]
WIN_EXITS = ["take_profit", "trail_stop", "signal_flip"]
LOSS_EXITS = ["stop_loss", "regime_change", "time_exit"]


@dataclass
class DemoSignal:
    seq: int
    ts: float
    score: float
    regime: str
    strategy: str
    asset: str
    side: OrderSide
    entry_signal_price: float
    # predetermined outcome (fixture-controlled, not a prediction)
    will_win: bool
    r_target: float
    exit_reason: str


class DemoFeed:
    """Deterministic generator of DemoSignals with a target win rate."""

    def __init__(self, seed: int = 36, target_win_rate: float = 0.53,
                 start_ts: float = 0.0, seconds_per_trade: float = 0.0) -> None:
        self._rng = random.Random(seed)
        self.target_win_rate = target_win_rate
        self._seq = 0
        self._ts = start_ts
        self._dt = seconds_per_trade

    def next(self) -> DemoSignal:
        self._seq += 1
        self._ts += self._dt
        will_win = self._rng.random() < self.target_win_rate
        if will_win:
            r_target = round(self._rng.uniform(1.2, 2.4), 2)
            exit_reason = self._rng.choice(WIN_EXITS)
        else:
            r_target = 1.0  # fixed 1R loss at stop
            exit_reason = self._rng.choice(LOSS_EXITS)

        return DemoSignal(
            seq=self._seq,
            ts=self._ts,
            score=round(self._rng.uniform(0.5, 0.99), 3),
            regime=self._rng.choice(REGIMES),
            strategy=self._rng.choice(STRATEGIES),
            asset=self._rng.choice(ASSETS),
            side=OrderSide.BUY if self._rng.random() < 0.5 else OrderSide.SELL,
            entry_signal_price=round(self._rng.uniform(50.0, 250.0), 2),
            will_win=will_win,
            r_target=r_target,
            exit_reason=exit_reason,
        )
