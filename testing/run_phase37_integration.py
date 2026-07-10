"""
APEX ULTRA — Phase 37 Demo Broker Integration Runner

Replaces MockBroker with the real DemoBrokerAdapter and runs the full stack:
  1. Connect the adapter (DEMO-only, ALLOW_LIVE=false).
  2. Snapshot connection safety.
  3. Run the EXISTING Phase 35 lifecycle + failure tests against the adapter.
  4. Drive the EXISTING Phase 36 burn-in (500+ trades) through the adapter.
  5. Enforce safety (refuse live endpoints, refuse live orders).
  6. Print the Phase 37 report block.

Offline note: this run uses SimulatedBrokerTransport so the adapter's own code
paths are validated without network. To validate connectivity to your real
broker, pass RealHttpTransport(base_url=<paper-url>, headers=<auth>) instead —
the same harness runs unchanged.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from infrastructure.broker import (  # noqa: E402
    BrokerConfigError,
    ConnectionMonitor,
    DemoBrokerAdapter,
    MarketConfig,
    SimulatedBrokerTransport,
    allow_live_enabled,
)
from testing.broker_validation.execution_metrics import ExecutionMetrics  # noqa: E402
from testing.broker_validation.failure_tests import FailureTester  # noqa: E402
from testing.broker_validation.order_lifecycle import OrderLifecycleTester  # noqa: E402
from testing.broker_validation.demo_report import _execution_quality  # noqa: E402
from testing.burn_in.burn_in_controller import BurnInController  # noqa: E402


BROKER_NAME = "DEMO-BROKER (adapter)"
BASE_URL = "https://demo.simulated.local"


def _safety_self_check() -> tuple[bool, str]:
    """Confirm the DEMO guard refuses a live endpoint."""
    try:
        DemoBrokerAdapter(base_url="https://api.live.broker.com",
                          spec=None)
        return False, "live endpoint was NOT refused"
    except BrokerConfigError:
        return True, "live endpoint refused; ALLOW_LIVE=" + str(allow_live_enabled())


def run() -> dict:
    # ---- adapter + connection ---------------------------------------- #
    adapter = DemoBrokerAdapter(symbol="APEX", base_url=BASE_URL)
    metrics = ExecutionMetrics()
    monitor = ConnectionMonitor(adapter, heartbeat_interval=0.5,
                                max_reconnect_attempts=5)
    connected = monitor.start()
    for _ in range(3):
        monitor.heartbeat()

    bal = adapter.getBalance()

    # ---- Phase 35 execution validation against the adapter ----------- #
    lifecycle = OrderLifecycleTester(adapter, metrics).run_all()
    failures = FailureTester(adapter, monitor, metrics).run_all()

    by_name = {f.name: f for f in failures}
    lc = {l.name.split(" ")[0]: l for l in lifecycle}  # 'BUY'/'SELL'
    required = {
        "BUY lifecycle": lc["BUY"].passed,
        "SELL lifecycle": lc["SELL"].passed,
        "timeout recovery": by_name["broker_timeout"].passed and adapter.is_connected(),
        "disconnect recovery": (by_name["disconnect_during_order"].passed
                                and by_name["reconnect_after_disconnect"].passed),
        "partial fill handling": by_name["partial_fill"].passed,
    }
    exec_tests_pass = all(required.values())
    recovery = by_name["reconnect_after_disconnect"].recovery_ms

    # ---- Phase 36 burn-in through the adapter ------------------------ #
    burn_sim = SimulatedBrokerTransport(
        symbol="APEX",
        market=MarketConfig(mid=100.0, latency_ms_mean=1.0, latency_ms_jitter=0.5),
        seed=37,
    )
    burn_adapter = DemoBrokerAdapter(symbol="APEX", base_url=BASE_URL,
                                     transport=burn_sim)
    controller = BurnInController(broker_name=BROKER_NAME, seed=36,
                                  broker=burn_adapter)
    burn = controller.run(n_trades=520, sim_days=32.0)
    bstats = burn.session.stats()

    safety_ok, safety_msg = _safety_self_check()
    snap = monitor.snapshot()
    five_hundred_ok = bstats.trade_count >= 500 and not burn.evaluation.stop_triggered

    demo_ready = (
        connected and exec_tests_pass and five_hundred_ok
        and burn.exec_failure_rate <= 0.05 and safety_ok and burn.passed
    )

    # ---- report ------------------------------------------------------ #
    print("=" * 62)
    print("APEX ULTRA — PHASE 37 DEMO BROKER INTEGRATION")
    print("=" * 62)
    print(f"BROKER:            {BROKER_NAME}")
    print(f"                   endpoint={BASE_URL}  spec={adapter.spec.name}  "
          f"mode=DEMO  ALLOW_LIVE={allow_live_enabled()}")
    print(f"                   balance={bal['balance']:,.0f} "
          f"equity={bal['equity']:,.0f}")
    print("-" * 62)
    print("CONNECTION:")
    print(f"  state              : {adapter.safety.state.value}")
    print(f"  connected          : {connected}")
    print(f"  last latency       : {adapter.safety.last_latency_ms:.2f} ms")
    print(f"  avg latency        : {snap.avg_latency_ms:.2f} ms")
    print(f"  reconnect attempts : {monitor.reconnect_attempts}")
    print(f"  disconnect duration: {adapter.safety.total_disconnect_seconds*1000:.1f} ms total")
    print("-" * 62)
    print("EXECUTION TESTS:")
    for name, ok in required.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    rec = f"{recovery:.1f} ms" if recovery else "n/a"
    print(f"  reconnect recovery : {rec}")
    print("-" * 62)
    print("500 TRADE STATUS:")
    print(f"  trades booked      : {bstats.trade_count}  "
          f"(attempts {controller._attempts})  "
          f"min-met={burn.evaluation.min_trades_met}")
    print(f"  win rate           : {bstats.win_rate*100:.1f}%   "
          f"profit factor {bstats.profit_factor:.2f}")
    print(f"  max drawdown       : {bstats.max_drawdown_pct:.2f}%   "
          f"duration {burn.session.duration_days:.1f}d")
    print("-" * 62)
    print("SLIPPAGE:")
    print(f"  avg slippage       : {burn.collector.avg_slippage_bps:.3f} bps")
    print(f"  avg spread         : {burn.collector.avg_spread:.4f}")
    print(f"  avg fill latency   : {burn.collector.avg_latency_ms:.2f} ms")
    print(f"  execution quality  : {_execution_quality(burn.metrics)}/100")
    print("-" * 62)
    print("FAILURES:")
    print(f"  rejected orders    : {burn.metrics.rejected_orders}")
    print(f"  missed executions  : {burn.metrics.missed_executions}")
    print(f"  exec failure rate  : {burn.exec_failure_rate*100:.2f}%  "
          f"(limit 5.00%)")
    print(f"  validation failures: {sum(1 for v in required.values() if not v)}/5")
    print(f"  safety guard       : {'OK' if safety_ok else 'FAIL'} — {safety_msg}")
    print("-" * 62)
    print(f"DEMO READY:          {'YES' if demo_ready else 'NO'}")
    print("=" * 62)

    return {"demo_ready": demo_ready, "burn": burn, "required": required}


if __name__ == "__main__":
    run()
