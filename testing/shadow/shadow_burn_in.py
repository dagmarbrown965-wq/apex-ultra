"""
APEX ULTRA — Phase 40 Deriv Demo Shadow Burn-In

Runs APEX ULTRA against a REAL Deriv demo account in SHADOW MODE: connect,
authorize a virtual account, subscribe to market data, consume signals from the
existing pipeline, and record what WOULD have happened — WITHOUT sending any
order. Live order capability does not exist on this path (ShadowBrokerView).

Preconditions (hard):
  - `apex_demo_ready --real` must return READY before a real burn-in starts.
  - If BLOCKED, this stops immediately and prints the blockers.

Minimum duration: 14 calendar days AND 500 shadow opportunities (both).

Modes:
  --real      Real Deriv demo shadow burn-in (requires READY + a live signal
              source wired in).
  --dry-run   Offline flow check using the synthetic replay fixture. Clearly
              labelled; never a real burn-in result.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker import MarketConfig  # noqa: E402
from infrastructure.broker.broker_interface import OrderSide  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    DerivDemoAdapter,
    DerivSimulatedTransport,
    DerivWebSocketTransport,
    ShadowBrokerView,
    ShadowRecorder,
    ShadowViolation,
    live_trading_enabled,
    load_contract_spec,
    load_deriv_config,
    select_contract,
)
from testing.preflight import apex_demo_ready  # noqa: E402

MIN_DAYS = 14
MIN_OPPORTUNITIES = 500


def _ws_available() -> bool:
    return importlib.util.find_spec("websocket") is not None


def _pick_mode(argv: list[str]) -> str:
    if "--dry-run" in argv:
        return "dry-run"
    if "--real" in argv:
        return "real"
    cfg = load_deriv_config()
    return "real" if (cfg.token_present and _ws_available()) else "dry-run"


def _run_preflight(mode: str) -> dict:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = apex_demo_ready.run(["--real"] if mode == "real" else ["--dry-run"])
    return res


def run(argv: list[str] | None = None, signal_source=None) -> dict:
    argv = argv if argv is not None else sys.argv[1:]
    mode = _pick_mode(argv)
    cfg = load_deriv_config(require_token=False)  # preflight enforces readiness

    # ---- 1. PRECONDITION: preflight gate ----------------------------- #
    pf = _run_preflight(mode)
    required = "READY" if mode == "real" else "DRY-RUN PASSED"
    if pf["status"] != required:
        print("=" * 68)
        print("APEX ULTRA PHASE 40 SHADOW BURN-IN — PRECONDITION FAILED")
        print("=" * 68)
        print(f"Preflight status: {pf['status']} (required: {required})")
        print("Burn-in did NOT start. Blockers:")
        for b in pf.get("blockers", []) or ["(see preflight report)"]:
            print(f"  - {b}")
        print("=" * 68)
        print("STATUS: FAIL (precondition not met)")
        print("=" * 68)
        return {"status": "FAIL", "reason": "precondition", "preflight": pf}

    # ---- hard safety: this phase forbids live trading ---------------- #
    if live_trading_enabled():
        print("STATUS: FAIL — LIVE_TRADING=true is not permitted in shadow phase")
        return {"status": "FAIL", "reason": "live_trading_flag"}

    # ---- 2. Connect (real Deriv demo) + shadow view ------------------ #
    if mode == "real":
        transport = DerivWebSocketTransport(app_id=cfg.app_id, ws_url=cfg.ws_url)
    else:
        transport = DerivSimulatedTransport(
            symbol=cfg.symbol, currency=cfg.currency, is_virtual=True,
            tick_latency=True,
            market=MarketConfig(mid=1000.0, spread=0.4,
                                latency_ms_mean=1.5, latency_ms_jitter=0.6))
    adapter = DerivDemoAdapter(config=cfg.deriv_config(), transport=transport)
    view = ShadowBrokerView(adapter)  # no order methods exist on this path
    view.connect()

    if not view.is_connected() or view.is_virtual is not True:
        print("STATUS: FAIL — could not establish a virtual-account connection")
        return {"status": "FAIL", "reason": "connection"}

    # confirm contract spec from contracts_for (for would-be mapping)
    spec = load_contract_spec()
    try:
        cf = view.contracts_for(cfg.symbol)
        sel = select_contract(cf, cfg.symbol, needs_sl=True, needs_tp=True, size=10.0)
        if sel.confirmed:
            spec = sel.to_spec()
            spec.multiplier = sel.multiplier if sel.category == "multiplier" else None
    except Exception:
        pass

    # ---- 3. Signal source -------------------------------------------- #
    if signal_source is None:
        if mode == "real":
            print("STATUS: FAIL — no live signal source wired. Inject the existing "
                  "APEX signal stream via run(signal_source=...).")
            return {"status": "FAIL", "reason": "no_signal_source"}
        # dry-run only: synthetic fixture
        from testing.shadow.signal_replay import ShadowSignalReplay
        sim_days = 15.0
        per = (sim_days * 86400.0) / 520
        signal_source = ShadowSignalReplay(seed=40, start_ts=time.time(),
                                           seconds_per_signal=per)

    # ---- 4. Shadow loop ---------------------------------------------- #
    recorder = ShadowRecorder()
    start_sim = signal_source._ts if hasattr(signal_source, "_ts") else time.time()
    n = 520 if mode != "real" else MIN_OPPORTUNITIES
    last_ts = start_sim
    for i in range(1, n + 1):
        sig = signal_source.next()
        if sig is None:
            break  # source exhausted / idle — stop accumulating (may yield EXTEND)
        last_ts = sig.timestamp

        # observe market (real quote + measured latency)
        t0 = time.perf_counter()
        try:
            quote = view.get_quote(sig.symbol)
        except Exception:
            recorder.record_missed()
            continue
        latency_ms = (time.perf_counter() - t0) * 1000.0

        recorder.record(sig, quote, latency_ms, spec, cfg.currency)

        # occasional connection drop + reconnect (resilience, dry-run)
        if mode != "real" and i % 150 == 0:
            view.force_drop()
            recorder.record_connection_failure()
            try:
                view.connect()
                recorder.record_reconnect(view.is_connected())
            except Exception:
                pass

    duration_days = (last_ts - start_sim) / 86400.0

    # ---- 5. Completion + status -------------------------------------- #
    met_opps = len(recorder.events) >= MIN_OPPORTUNITIES
    met_days = duration_days >= MIN_DAYS
    live_orders = view.live_orders_sent  # structurally 0
    safety_ok = (live_orders == 0
                 and recorder.connection_failures == recorder.reconnect_successes)

    if live_orders != 0:
        status = "FAIL"
    elif not (met_opps and met_days):
        status = "EXTEND"
    elif not safety_ok:
        status = "FAIL"
    else:
        status = "PASS"

    _report(mode, cfg, view, recorder, duration_days, met_opps, met_days,
            live_orders, status)
    return {"status": status, "events": len(recorder.events),
            "duration_days": duration_days, "live_orders": live_orders}


def _report(mode, cfg, view, rec, duration_days, met_opps, met_days,
            live_orders, status) -> None:
    line = "=" * 68
    print(line)
    print(f"APEX ULTRA PHASE 40 SHADOW REPORT          [mode: {mode.upper()}]")
    if mode == "dry-run":
        print("  NOTE: simulated transport + synthetic signals — flow check only,")
        print("        NOT a real shadow burn-in result.")
    print(line)
    print(f"Connection        : Deriv {cfg.ws_url} "
          f"({'connected' if view.is_connected() else 'down'})")
    print(f"Account           : {view.loginid}  virtual={view.is_virtual}")
    print(f"Duration          : {duration_days:.1f} days "
          f"(min {MIN_DAYS}: {'met' if met_days else 'NOT met'})")
    print(f"Signals           : {len(rec.events)} "
          f"(min {MIN_OPPORTUNITIES}: {'met' if met_opps else 'NOT met'})")
    print(f"Accepted          : {len(rec.accepted_events)}")
    print(f"Rejected          : {len(rec.rejected_events)}")
    print(f"Risk blocks       : {rec.risk_blocks}")
    print(f"Connection events : failures={rec.connection_failures} "
          f"reconnect_ok={rec.reconnect_successes}")
    print("-" * 68)
    print("Estimated performance:")
    pf = rec.profit_factor()
    print(f"  Win rate        : {rec.win_rate_estimate()*100:.1f}% "
          f"({len(rec.resolved)} resolved)")
    print(f"  Profit factor   : {'inf' if pf == float('inf') else f'{pf:.2f}'}")
    print(f"  Average R       : {rec.average_rr():.2f}")
    print(f"  Max simulated DD: {rec.max_simulated_drawdown():.2f} R")
    rp = rec.regime_performance()
    ap = rec.asset_performance()
    if rp:
        print(f"  Regime perf     : "
              + ", ".join(f"{k} {v*100:.0f}%" for k, v in sorted(rp.items())))
    if ap:
        print(f"  Asset perf      : "
              + ", ".join(f"{k} {v*100:.0f}%" for k, v in sorted(ap.items())))
    print("-" * 68)
    print("Execution:")
    print(f"  Average latency : {rec.avg_latency_ms():.2f} ms")
    print(f"  Average spread  : {rec.avg_spread():.4f}")
    print(f"  Missed signals  : {rec.missed_signals}")
    print("-" * 68)
    print("Safety:")
    print(f"  Live orders sent: {live_orders}")
    print(f"  Risk guard blocks: {rec.risk_blocks}")
    print(f"  Connection fails : {rec.connection_failures} "
          f"(recovered {rec.reconnect_successes})")
    print(line)
    print(f"STATUS: {status}")
    if status == "EXTEND":
        print("  Minimums not yet met — continue the shadow burn-in.")
    if mode == "dry-run":
        print("  (dry-run: simulated — does not constitute a real shadow pass)")
    print(line)


if __name__ == "__main__":
    run()
