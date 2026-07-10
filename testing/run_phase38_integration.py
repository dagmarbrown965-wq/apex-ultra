"""
APEX ULTRA — Phase 38 Deriv DEMO Integration Runner

Swaps the generic endpoint spec for the Deriv WebSocket adapter and runs:
  - Phase 35 lifecycle + failure tests against the Deriv adapter
  - Phase 36 burn-in controller through the Deriv adapter
  - Deriv safety checks (DEMO ONLY, real-account blocking, LIVE_TRADING=false)

Offline note: uses DerivSimulatedTransport (mimics Deriv's message protocol) so
the adapter's Deriv-specific logic is validated without network. For a real
connectivity run, pass DerivWebSocketTransport(app_id=...) with a virtual-account
token; the same harness runs unchanged.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from infrastructure.broker import ConnectionMonitor, MarketConfig  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    DerivConfig,
    DerivDemoAdapter,
    DerivRealAccountBlocked,
    DerivSimulatedTransport,
    live_trading_enabled,
)
from testing.broker_validation.demo_report import _execution_quality  # noqa: E402
from testing.broker_validation.execution_metrics import ExecutionMetrics  # noqa: E402
from testing.broker_validation.failure_tests import FailureTester  # noqa: E402
from testing.broker_validation.order_lifecycle import OrderLifecycleTester  # noqa: E402
from testing.burn_in.burn_in_controller import BurnInController  # noqa: E402


def _real_account_block_check() -> tuple[bool, str]:
    """Confirm a real (non-virtual) account is refused."""
    real_tx = DerivSimulatedTransport(is_virtual=False, loginid="CR9001122")
    adapter = DerivDemoAdapter(transport=real_tx)
    try:
        adapter.connect()
        return False, "REAL account was NOT blocked"
    except DerivRealAccountBlocked as e:
        return True, str(e)


def run() -> dict:
    cfg = DerivConfig(symbol="R_100")

    # ---- adapter + connection (virtual/demo account) ----------------- #
    adapter = DerivDemoAdapter(config=cfg)
    metrics = ExecutionMetrics()
    monitor = ConnectionMonitor(adapter, heartbeat_interval=0.5,
                                max_reconnect_attempts=5)
    connected = monitor.start()
    for _ in range(3):
        monitor.heartbeat()

    bal = adapter.getBalance()

    # ---- Phase 35 validation against Deriv adapter ------------------- #
    lifecycle = OrderLifecycleTester(adapter, metrics).run_all(
        symbol=cfg.symbol, qty=10.0, price=adapter.current_mid)
    failures = FailureTester(adapter, monitor, metrics).run_all()
    by_name = {f.name: f for f in failures}
    lc = {l.name.split(" ")[0]: l for l in lifecycle}
    lifecycle_ok = all(l.passed for l in lifecycle)
    failures_ok = all(f.passed for f in failures)

    # ---- Phase 36 burn-in through Deriv adapter ---------------------- #
    burn_tx = DerivSimulatedTransport(
        symbol="R_100",
        market=MarketConfig(mid=1000.0, spread=0.4,
                            latency_ms_mean=1.0, latency_ms_jitter=0.5),
        seed=38,
    )
    burn_adapter = DerivDemoAdapter(config=cfg, transport=burn_tx)
    controller = BurnInController(broker_name="DERIV-DEMO", seed=36,
                                  broker=burn_adapter)
    burn = controller.run(n_trades=520, sim_days=32.0)
    bstats = burn.session.stats()

    real_blocked, real_msg = _real_account_block_check()
    snap = monitor.snapshot()
    ready_500 = (bstats.trade_count >= 500 and not burn.evaluation.stop_triggered
                 and burn.exec_failure_rate <= 0.05)

    # ---- report ------------------------------------------------------ #
    print("=" * 62)
    print("APEX ULTRA — PHASE 38 DERIV DEMO ADAPTER")
    print("=" * 62)
    print("Connection:")
    print(f"  broker           : Deriv (WebSocket)  app_id={cfg.app_id}")
    print(f"  endpoint         : {cfg.ws_url}")
    print(f"  account          : {adapter._loginid}  "
          f"virtual={adapter._is_virtual}  LIVE_TRADING={live_trading_enabled()}")
    print(f"  state            : {adapter.safety.state.value}  connected={connected}")
    print(f"  balance          : {bal['balance']:,.2f} {bal['currency']}")
    print(f"  symbol           : {cfg.symbol}")
    print("-" * 62)
    print("Latency:")
    print(f"  last heartbeat   : {adapter.safety.last_latency_ms:.2f} ms")
    print(f"  avg heartbeat    : {snap.avg_latency_ms:.2f} ms")
    print(f"  avg fill latency : {burn.collector.avg_latency_ms:.2f} ms")
    print("-" * 62)
    print("Order lifecycle:")
    print(f"  [{'PASS' if lc['BUY'].passed else 'FAIL'}] BUY  (proposal->buy->contract->position)")
    print(f"  [{'PASS' if lc['SELL'].passed else 'FAIL'}] SELL (sell contract->close->flat)")
    print(f"  [{'PASS' if by_name['broker_timeout'].passed else 'FAIL'}] timeout recovery")
    print(f"  [{'PASS' if by_name['disconnect_during_order'].passed and by_name['reconnect_after_disconnect'].passed else 'FAIL'}] disconnect + reconnect recovery")
    print(f"  [{'PASS' if by_name['partial_fill'].passed else 'FAIL'}] partial fill handling")
    rec = by_name['reconnect_after_disconnect'].recovery_ms
    print(f"  reconnect time   : {rec:.1f} ms" if rec else "  reconnect time   : n/a")
    print("-" * 62)
    print("Rejected orders:")
    print(f"  validation rejects: {metrics.rejected_orders}  "
          f"missed: {metrics.missed_executions}")
    print(f"  burn-in rejects   : {burn.metrics.rejected_orders}  "
          f"missed: {burn.metrics.missed_executions}")
    print(f"  exec failure rate : {burn.exec_failure_rate*100:.2f}%  (limit 5.00%)")
    print("-" * 62)
    print("Slippage:")
    print(f"  avg slippage     : {burn.collector.avg_slippage_bps:.3f} bps")
    print(f"  avg spread       : {burn.collector.avg_spread:.4f}")
    print(f"  execution quality: {_execution_quality(burn.metrics)}/100")
    print("-" * 62)
    print("500 trade readiness:")
    print(f"  trades booked    : {bstats.trade_count} / 500  "
          f"({'READY' if ready_500 else 'NOT READY'})")
    print(f"  win rate         : {bstats.win_rate*100:.1f}%   "
          f"PF {bstats.profit_factor:.2f}   maxDD {bstats.max_drawdown_pct:.2f}%")
    print(f"  duration         : {burn.session.duration_days:.1f} / 30 days")
    print("-" * 62)
    print("Safety:")
    print(f"  default mode     : DEMO ONLY")
    print(f"  real account     : {'BLOCKED (OK)' if real_blocked else 'NOT BLOCKED — BAD'}")
    print(f"                     {real_msg}")
    print("=" * 62)
    overall = (connected and lifecycle_ok and failures_ok and ready_500
               and real_blocked)
    print(f"PHASE 38 STATUS:   {'DEMO READY' if overall else 'NOT READY'}")
    print("=" * 62)

    return {"ready": overall, "burn": burn}


if __name__ == "__main__":
    run()
