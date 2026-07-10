"""
APEX ULTRA — Burn-In Rules (Phase 36)

Encodes the gating rules for a demo burn-in:

  Minimums:
    - 500 trades
    - 30 days duration

  Stop conditions (any one aborts the burn-in):
    - drawdown > 10%
    - execution failure rate > 5%
    - risk guard malfunction
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class StopReason(str, Enum):
    DRAWDOWN = "drawdown_exceeded"
    EXEC_FAILURE = "execution_failure_exceeded"
    RISK_GUARD = "risk_guard_malfunction"


@dataclass
class BurnInThresholds:
    min_trades: int = 500
    min_duration_days: float = 30.0
    max_drawdown_pct: float = 10.0
    max_exec_failure_rate: float = 0.05


@dataclass
class BurnInEvaluation:
    min_trades_met: bool
    min_duration_met: bool
    stop_triggered: bool
    stop_reasons: list[StopReason] = field(default_factory=list)

    @property
    def minimums_met(self) -> bool:
        return self.min_trades_met and self.min_duration_met


def check_stop_conditions(
    drawdown_pct: float,
    exec_failure_rate: float,
    risk_guard_ok: bool,
    thresholds: BurnInThresholds,
) -> list[StopReason]:
    reasons: list[StopReason] = []
    if drawdown_pct > thresholds.max_drawdown_pct:
        reasons.append(StopReason.DRAWDOWN)
    if exec_failure_rate > thresholds.max_exec_failure_rate:
        reasons.append(StopReason.EXEC_FAILURE)
    if not risk_guard_ok:
        reasons.append(StopReason.RISK_GUARD)
    return reasons


def evaluate(
    trade_count: int,
    duration_days: float,
    drawdown_pct: float,
    exec_failure_rate: float,
    risk_guard_ok: bool,
    thresholds: BurnInThresholds = BurnInThresholds(),
) -> BurnInEvaluation:
    stops = check_stop_conditions(drawdown_pct, exec_failure_rate,
                                  risk_guard_ok, thresholds)
    return BurnInEvaluation(
        min_trades_met=trade_count >= thresholds.min_trades,
        min_duration_met=duration_days >= thresholds.min_duration_days,
        stop_triggered=len(stops) > 0,
        stop_reasons=stops,
    )
