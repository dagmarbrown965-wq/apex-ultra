"""
APEX ULTRA — Demo Broker Validation Runner (Phase 35)

Entry point. Wires the mock broker + monitor + metrics, runs lifecycle and
failure suites, and prints the required report block:

  BUILD / RUNTIME / BROKER TEST / EXECUTION METRICS / DEMO READY STATUS
"""

from __future__ import annotations

import os
import sys
import time

# allow running as a plain script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker import ConnectionMonitor, MarketConfig, MockBroker  # noqa: E402
from testing.broker_validation.demo_report import build_demo_report  # noqa: E402
from testing.broker_validation.execution_metrics import ExecutionMetrics  # noqa: E402
from testing.broker_validation.failure_tests import FailureTester  # noqa: E402
from testing.broker_validation.order_lifecycle import OrderLifecycleTester  # noqa: E402


def run(seed: int = 35) -> dict:
    t_start = time.perf_counter()

    broker = MockBroker(symbol="APEX", market=MarketConfig(mid=100.0), seed=seed)
    monitor = ConnectionMonitor(broker, heartbeat_interval=0.5, max_reconnect_attempts=5)
    metrics = ExecutionMetrics()

    connected = monitor.start()

    # warm heartbeats to seed latency stats
    for _ in range(5):
        monitor.heartbeat()

    lifecycle = OrderLifecycleTester(broker, metrics).run_all()
    failures = FailureTester(broker, monitor, metrics).run_all()

    report = build_demo_report(lifecycle, failures, metrics)
    snap = monitor.snapshot()
    runtime_ms = (time.perf_counter() - t_start) * 1000.0

    print("=" * 60)
    print("APEX ULTRA — PHASE 35 DEMO BROKER VALIDATION")
    print("=" * 60)
    print(f"BUILD:            OK  (modules loaded, 0 import errors)")
    print(f"RUNTIME:          {runtime_ms:6.1f} ms   connected={connected}")
    print(f"                  heartbeats ok={snap.heartbeats_ok} "
          f"missed={snap.heartbeats_missed} "
          f"avg_latency={snap.avg_latency_ms:.2f}ms")
    print("-" * 60)
    print("BROKER TEST:")
    for r in lifecycle:
        print(f"  [{'PASS' if r.passed else 'FAIL'}] {r.name}")
        print(f"         {r.detail}")
    for r in failures:
        rec = f"  recovery={r.recovery_ms:.1f}ms" if r.recovery_ms else ""
        print(f"  [{'PASS' if r.passed else 'FAIL'}] {r.name}{rec}")
        print(f"         {r.detail}")
    print("-" * 60)
    print("EXECUTION METRICS:")
    print(f"  trade count        : {report.trade_count}")
    print(f"  avg slippage       : {report.avg_slippage_bps:.3f} bps")
    print(f"  avg latency        : {metrics.avg_latency_ms:.2f} ms")
    print(f"  total spread cost  : {metrics.total_spread_cost:.4f}")
    print(f"  rejected orders    : {metrics.rejected_orders}")
    print(f"  missed executions  : {metrics.missed_executions}")
    print(f"  fill rate          : {metrics.fill_rate*100:.1f}%")
    print(f"  execution quality  : {report.execution_quality}/100")
    print(f"  broker reliability : {report.broker_reliability}/100")
    rec = f"{report.recovery_time_ms:.1f} ms" if report.recovery_time_ms else "n/a"
    print(f"  recovery time      : {rec}")
    print("-" * 60)
    status = "READY" if report.demo_ready else "NOT READY"
    print(f"DEMO READY STATUS: {status}")
    print(f"  lifecycle {report.lifecycle_pass}/{report.lifecycle_total}  |  "
          f"failures handled {report.failure_handled}/{report.failure_total}")
    print("=" * 60)

    return {"report": report, "metrics": metrics, "snapshot": snap}


if __name__ == "__main__":
    run()
