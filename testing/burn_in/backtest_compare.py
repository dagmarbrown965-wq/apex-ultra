"""
APEX ULTRA — Backtest vs Demo Comparison (Phase 36)

Compares predicted (backtest) performance against actual (demo) performance and
reports performance drift.

  Predicted: win rate, average R:R, drawdown
  Actual:    win rate, average R:R, drawdown
  Output:    Performance Drift %

The backtest baseline is supplied as input. Wire it to the real backtest output;
the defaults below are placeholders for the controlled demo run.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BacktestBaseline:
    win_rate: float          # fraction, e.g. 0.57
    avg_rr: float            # e.g. 1.8
    max_drawdown_pct: float  # e.g. 6.0


@dataclass
class DemoActual:
    win_rate: float
    avg_rr: float
    max_drawdown_pct: float


@dataclass
class DriftReport:
    backtest_wr: float
    demo_wr: float
    wr_drift_pp: float        # percentage points (demo - backtest)

    backtest_rr: float
    demo_rr: float
    rr_drift_pct: float       # relative % change

    backtest_dd: float
    demo_dd: float
    dd_drift_pp: float        # percentage points

    overall_drift_pct: float  # composite magnitude
    within_tolerance: bool


def compare(baseline: BacktestBaseline, actual: DemoActual,
            wr_tol_pp: float = 5.0, rr_tol_pct: float = 20.0,
            dd_tol_pp: float = 4.0) -> DriftReport:
    wr_drift_pp = (actual.win_rate - baseline.win_rate) * 100.0
    rr_drift_pct = (
        (actual.avg_rr - baseline.avg_rr) / baseline.avg_rr * 100.0
        if baseline.avg_rr else 0.0
    )
    dd_drift_pp = actual.max_drawdown_pct - baseline.max_drawdown_pct

    # composite drift magnitude (worst-case orientation:
    # WR down = bad, RR down = bad, DD up = bad)
    composite = (
        abs(min(0.0, wr_drift_pp)) * 1.0
        + abs(min(0.0, rr_drift_pct)) * 0.3
        + abs(max(0.0, dd_drift_pp)) * 1.0
    )

    within = (
        abs(wr_drift_pp) <= wr_tol_pp
        and abs(rr_drift_pct) <= rr_tol_pct
        and dd_drift_pp <= dd_tol_pp
    )

    return DriftReport(
        backtest_wr=baseline.win_rate * 100.0,
        demo_wr=actual.win_rate * 100.0,
        wr_drift_pp=wr_drift_pp,
        backtest_rr=baseline.avg_rr,
        demo_rr=actual.avg_rr,
        rr_drift_pct=rr_drift_pct,
        backtest_dd=baseline.max_drawdown_pct,
        demo_dd=actual.max_drawdown_pct,
        dd_drift_pp=dd_drift_pp,
        overall_drift_pct=round(composite, 2),
        within_tolerance=within,
    )
