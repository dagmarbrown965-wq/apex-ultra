"""
APEX ULTRA — Demo Report (Phase 35)

Aggregates lifecycle results, failure results, and execution metrics into the
broker-validation report:

  Execution Quality | Broker Reliability | Average Slippage
  Failure Count     | Recovery Time      | Trade Count
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .execution_metrics import ExecutionMetrics
from .failure_tests import FailureResult
from .order_lifecycle import LifecycleResult


@dataclass
class DemoReport:
    execution_quality: float        # 0-100 score
    broker_reliability: float       # 0-100 score
    avg_slippage_bps: float
    failure_count: int              # failure tests that did NOT pass
    recovery_time_ms: Optional[float]
    trade_count: int
    lifecycle_pass: int
    lifecycle_total: int
    failure_handled: int
    failure_total: int
    demo_ready: bool


def _execution_quality(metrics: ExecutionMetrics) -> float:
    # Penalize slippage and latency; reward fills. Bounded 0-100.
    slip_penalty = min(40.0, abs(metrics.avg_slippage_bps) * 4.0)
    lat_penalty = min(30.0, metrics.avg_latency_ms / 2.0)
    fill_bonus = metrics.fill_rate * 30.0
    return round(max(0.0, 70.0 - slip_penalty - lat_penalty + fill_bonus), 1)


def build_demo_report(
    lifecycle: list[LifecycleResult],
    failures: list[FailureResult],
    metrics: ExecutionMetrics,
) -> DemoReport:
    lc_pass = sum(1 for r in lifecycle if r.passed)
    f_handled = sum(1 for r in failures if r.passed)
    f_total = len(failures)
    recovery = next((r.recovery_ms for r in failures
                     if r.name == "reconnect_after_disconnect"), None)

    reliability = round((f_handled / f_total) * 100.0, 1) if f_total else 0.0
    exec_quality = _execution_quality(metrics)

    demo_ready = (
        lc_pass == len(lifecycle)
        and f_handled == f_total
        and exec_quality >= 60.0
        and metrics.fill_rate >= 0.5
    )

    return DemoReport(
        execution_quality=exec_quality,
        broker_reliability=reliability,
        avg_slippage_bps=round(metrics.avg_slippage_bps, 3),
        failure_count=f_total - f_handled,
        recovery_time_ms=round(recovery, 2) if recovery is not None else None,
        trade_count=metrics.fill_count,
        lifecycle_pass=lc_pass,
        lifecycle_total=len(lifecycle),
        failure_handled=f_handled,
        failure_total=f_total,
        demo_ready=demo_ready,
    )
