"""
APEX ULTRA — Phase 39 Real Deriv DEMO Smoke Test

Connects to Deriv and validates AUTH / MARKET DATA / EXECUTION / SAFETY, then
prints the smoke-test report.

Modes:
  --real      Connect to the live Deriv WebSocket (wss://ws.derivws.com/...).
              Requires `pip install websocket-client` and a DERIV_API_TOKEN for
              a VIRTUAL (demo) account.
  --dry-run   Use the in-process DerivSimulatedTransport. Validates the smoke
              harness flow WITHOUT a network connection (no live data).

Default: auto — real if a token + websocket-client are available, else dry-run
with a clear notice.

Required env for a real run:
  DERIV_APP_ID, DERIV_API_TOKEN (virtual token), optional DERIV_ACCOUNT_LOGIN,
  DERIV_SYMBOL, DERIV_CURRENCY. LIVE_TRADING must be false (default).
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker import ConnectionMonitor  # noqa: E402
from infrastructure.broker.broker_interface import Order, OrderSide  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    DerivDemoAdapter,
    DerivRealAccountBlocked,
    DerivSimulatedTransport,
    DerivWebSocketTransport,
    live_trading_enabled,
    load_deriv_config,
    verify_virtual_account,
)
from testing.broker_validation.execution_metrics import ExecutionMetrics  # noqa: E402


def _ws_lib_available() -> bool:
    return importlib.util.find_spec("websocket") is not None


def _pick_mode(argv: list[str]) -> str:
    if "--dry-run" in argv:
        return "dry-run"
    if "--real" in argv:
        return "real"
    cfg = load_deriv_config()
    if cfg.token_present and _ws_lib_available():
        return "real"
    return "dry-run"


class Check:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, bool, str]] = []

    def add(self, section: str, label: str, ok: bool, detail: str = "") -> bool:
        self.items.append((section, label, ok, detail))
        return ok

    def section(self, name: str) -> list[tuple]:
        return [i for i in self.items if i[0] == name]

    @property
    def all_pass(self) -> bool:
        return all(ok for _, _, ok, _ in self.items)


def run(argv: list[str] | None = None) -> dict:
    argv = argv if argv is not None else sys.argv[1:]
    mode = _pick_mode(argv)

    # preflight for real mode: surface missing prerequisites clearly
    if mode == "real":
        missing = []
        if not _ws_lib_available():
            missing.append("websocket-client not installed (pip install websocket-client)")
        pre = load_deriv_config()
        if not pre.token_present:
            missing.append("DERIV_API_TOKEN not set (use a Deriv VIRTUAL account token)")
        if missing:
            print("=" * 64)
            print("APEX ULTRA — PHASE 39 DERIV DEMO SMOKE TEST   [mode: REAL]")
            print("=" * 64)
            print("Cannot start a live run — prerequisites missing:")
            for m in missing:
                print(f"  - {m}")
            print("\nFix the above, or run a flow check with:")
            print("  python -m testing.smoke.deriv_smoke_test --dry-run")
            print("=" * 64)
            print("STATUS: FAIL")
            return {"status": "FAIL", "mode": "real", "missing": missing}

    cfg = load_deriv_config(require_token=(mode == "real"))
    chk = Check()

    if mode == "real":
        transport = DerivWebSocketTransport(app_id=cfg.app_id, ws_url=cfg.ws_url)
    else:
        transport = DerivSimulatedTransport(symbol=cfg.symbol,
                                            currency=cfg.currency, is_virtual=True)

    adapter = DerivDemoAdapter(config=cfg.deriv_config(), transport=transport)
    metrics = ExecutionMetrics()
    monitor = ConnectionMonitor(adapter, max_reconnect_attempts=5)

    ticks_received = 0
    latencies: list[float] = []
    orders_attempted = orders_filled = rejected = 0
    demo_balance = final_balance = None
    final_pl = None

    # ============================== AUTH ============================== #
    try:
        monitor.start()  # connect() -> transport.connect + authorize + is_virtual guard
        chk.add("AUTH", "authorize succeeds", adapter.is_connected(),
                f"loginid={adapter._loginid}")
        chk.add("AUTH", "account is_virtual === true", adapter._is_virtual is True,
                f"is_virtual={adapter._is_virtual}")
    except DerivRealAccountBlocked as e:
        chk.add("AUTH", "authorize succeeds", False, str(e))
        chk.add("AUTH", "account is_virtual === true", False, "blocked")
    except Exception as e:
        chk.add("AUTH", "authorize succeeds", False, f"{type(e).__name__}: {e}")

    # real accounts are rejected (logic check, runs in both modes)
    real_adapter = DerivDemoAdapter(
        transport=DerivSimulatedTransport(is_virtual=False, loginid="CR5550000"))
    try:
        real_adapter.connect()
        chk.add("AUTH", "real accounts are rejected", False, "real account connected")
    except DerivRealAccountBlocked:
        chk.add("AUTH", "real accounts are rejected", True, "real account refused")

    if adapter.is_connected():
        bal = adapter.getBalance()
        demo_balance = bal.get("balance")

        # ========================= MARKET DATA ======================= #
        try:
            ticks = adapter.stream_ticks(count=5, timeout=10.0)
            ticks_received += len(ticks)
            latencies += [lat for _, lat in ticks]
            chk.add("MARKET DATA", "subscribe ticks", True, f"{len(ticks)} frames")
            chk.add("MARKET DATA", "receive live ticks", len(ticks) >= 3,
                    f"{len(ticks)} received")
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
            chk.add("MARKET DATA", "measure latency", avg_lat > 0,
                    f"{avg_lat:.2f} ms avg")
        except Exception as e:
            chk.add("MARKET DATA", "subscribe ticks", False, str(e))

        # reconnect handling
        try:
            adapter.force_drop()
            t0 = time.perf_counter()
            recovered = monitor.reconnect()
            rec_ms = (time.perf_counter() - t0) * 1000.0
            more = adapter.stream_ticks(count=2, timeout=10.0) if recovered else []
            ticks_received += len(more)
            latencies += [lat for _, lat in more]
            chk.add("MARKET DATA", "handle reconnect", recovered and len(more) > 0,
                    f"recovered in {rec_ms:.1f}ms, +{len(more)} ticks")
        except Exception as e:
            chk.add("MARKET DATA", "handle reconnect", False, str(e))

        # ========================== EXECUTION ======================== #
        stake = 10.0
        # 1. proposal request
        try:
            prop = adapter.transport.call({
                "proposal": 1, "amount": stake, "basis": "stake",
                "contract_type": adapter.config.contract_type_buy,
                "symbol": cfg.symbol, "currency": cfg.currency, "multiplier": 100,
            }, timeout=10.0)
            chk.add("EXECUTION", "proposal request",
                    "proposal" in prop and "error" not in prop,
                    f"ask={prop.get('proposal', {}).get('ask_price')}")
        except Exception as e:
            chk.add("EXECUTION", "proposal request", False, str(e))

        # 2-3. buy demo contract + receive contract_id
        contract_id = None
        try:
            mid0 = adapter.current_mid
            order = Order(cfg.symbol, OrderSide.BUY, stake, expected_price=mid0)
            orders_attempted += 1
            t0 = time.perf_counter()
            result = adapter.submitOrder(order, timeout=10.0)
            exec_latency = (time.perf_counter() - t0) * 1000.0
            metrics.record_fill(result, exec_latency, mid0)
            orders_filled += 1
            contract_id = result.order.id
            chk.add("EXECUTION", "buy demo contract", result.order.filled_qty > 0,
                    f"fill={result.order.avg_fill_price:.4f}")
            chk.add("EXECUTION", "receive contract_id", bool(contract_id),
                    f"contract_id={contract_id}")
        except Exception as e:
            rejected += 1
            chk.add("EXECUTION", "buy demo contract", False, str(e))
            chk.add("EXECUTION", "receive contract_id", False, "no contract")

        # 4. monitor proposal_open_contract
        if contract_id:
            try:
                poc = adapter.getOrderStatus(contract_id)
                chk.add("EXECUTION", "monitor proposal_open_contract",
                        poc.get("contract_id") == contract_id,
                        f"status={poc.get('status')}")
            except Exception as e:
                chk.add("EXECUTION", "monitor proposal_open_contract", False, str(e))

            # 5. close contract
            try:
                close = adapter.closePosition(cfg.symbol, timeout=10.0)
                chk.add("EXECUTION", "close contract", close.get("closed") is True,
                        f"sold_for={close.get('sold_for')}")
                final_pl = close.get("profit")
            except Exception as e:
                chk.add("EXECUTION", "close contract", False, str(e))

            # 6. verify final P/L (balance delta consistent with reported profit)
            try:
                final_balance = adapter.getBalance().get("balance")
                delta = (final_balance - demo_balance) if (
                    final_balance is not None and demo_balance is not None) else None
                consistent = (delta is not None and final_pl is not None
                              and abs(delta - final_pl) < 1e-2)
                chk.add("EXECUTION", "verify final P/L", consistent,
                        f"P/L={final_pl} balance delta={delta}")
            except Exception as e:
                chk.add("EXECUTION", "verify final P/L", False, str(e))

    # ============================= SAFETY ============================ #
    chk.add("SAFETY", "LIVE_TRADING=false blocks real accounts",
            not live_trading_enabled(),
            f"LIVE_TRADING={live_trading_enabled()}")
    # no real endpoint capability: order path is guarded even if account were real
    guard = DerivDemoAdapter(transport=DerivSimulatedTransport(is_virtual=False))
    guard._is_virtual = False
    try:
        guard.submitOrder(Order(cfg.symbol, OrderSide.BUY, 1, expected_price=1))
        chk.add("SAFETY", "no real endpoint capability", False, "order not blocked")
    except DerivRealAccountBlocked:
        chk.add("SAFETY", "no real endpoint capability", True,
                "real-account orders blocked")
    chk.add("SAFETY", "shadow mode remains default", cfg.shadow_mode is True,
            f"shadow_mode={cfg.shadow_mode}")

    # ============================= REPORT ============================ #
    avg_slip = metrics.avg_slippage_bps
    avg_exec_lat = metrics.avg_latency_ms
    avg_tick_lat = sum(latencies) / len(latencies) if latencies else 0.0

    print("=" * 64)
    print(f"APEX ULTRA — PHASE 39 DERIV DEMO SMOKE TEST   [mode: {mode.upper()}]")
    if mode == "dry-run":
        print("  NOTE: simulated transport — NOT a live Deriv connection.")
        print("        run with --real (token + websocket-client) for live data.")
    print("=" * 64)
    for section in ("AUTH", "MARKET DATA", "EXECUTION", "SAFETY"):
        print(f"{section}:")
        for _, label, ok, detail in chk.section(section):
            mark = "\u2713" if ok else "\u2717"
            print(f"  {mark} {label}" + (f"   ({detail})" if detail else ""))
    if cfg.warnings:
        print("WARNINGS:")
        for w in cfg.warnings:
            print(f"  ! {w}")
    print("-" * 64)
    print("REPORT:")
    print(f"  Connection              : Deriv {cfg.ws_url} "
          f"({'connected' if adapter.is_connected() else 'not connected'})")
    print(f"  Latency                 : {avg_tick_lat:.2f} ms avg "
          f"(heartbeat {adapter.safety.last_latency_ms or 0:.2f} ms)")
    print(f"  Ticks received          : {ticks_received}")
    print(f"  Orders attempted        : {orders_attempted}")
    print(f"  Orders filled           : {orders_filled}")
    print(f"  Rejected                : {rejected}")
    print(f"  Average slippage        : {avg_slip:.3f} bps")
    print(f"  Average execution latency: {avg_exec_lat:.2f} ms")
    print(f"  Demo balance            : "
          f"{demo_balance if demo_balance is None else f'{demo_balance:,.2f}'} {cfg.currency}")
    print(f"  Final balance           : "
          f"{final_balance if final_balance is None else f'{final_balance:,.2f}'} {cfg.currency}")
    print("-" * 64)
    status = "PASS" if chk.all_pass else "FAIL"
    print(f"STATUS: {status}")
    print("=" * 64)

    return {"status": status, "checks": chk, "mode": mode}


if __name__ == "__main__":
    run()
