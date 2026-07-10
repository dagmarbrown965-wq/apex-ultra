"""
APEX ULTRA — Pre-Demo Preflight Consolidation (Phase 39.4)

A single command that proves every safety gate is satisfied before any Deriv
demo execution is allowed:

    python -m testing.preflight.apex_demo_ready            # auto (real if able)
    python -m testing.preflight.apex_demo_ready --dry-run  # simulated flow check
    python -m testing.preflight.apex_demo_ready --real     # live Deriv gate

It executes Phases 35, 36, 37, 38, 39, 39.1, 39.2, 39.3 and aggregates their
results into one readiness verdict.

HARD RULES (Phase 39.4):
  - Even if LIVE_TRADING=true, the preflight FAILS — this phase is DEMO ONLY.
  - No simulated data may produce READY. Simulation can only yield
    "DRY-RUN PASSED — NOT DEMO READY".

This module adds NO trading functionality. It only verifies.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker.deriv import live_trading_enabled, load_deriv_config  # noqa: E402

from testing.broker_validation import run_demo_validation  # noqa: E402  (Phase 35)
from testing.burn_in import run_burn_in  # noqa: E402  (Phase 36)
from testing import run_phase37_integration  # noqa: E402  (Phase 37)
from testing import run_phase38_integration  # noqa: E402  (Phase 38)
from testing.smoke import deriv_smoke_test  # noqa: E402  (Phase 39)
from testing.smoke import deriv_readiness_gate  # noqa: E402  (Phase 39.1)
from testing.smoke import deriv_contract_verification  # noqa: E402  (Phase 39.2)
from testing.smoke import deriv_live_gate  # noqa: E402  (Phase 39.3)


def _ws_available() -> bool:
    return importlib.util.find_spec("websocket") is not None


def _pick_mode(argv: list[str]) -> str:
    if "--dry-run" in argv:
        return "dry-run"
    if "--real" in argv:
        return "real"
    cfg = load_deriv_config()
    return "real" if (cfg.token_present and _ws_available()) else "dry-run"


def _quiet(fn, *args):
    """Run a phase runner, swallowing its stdout; capture result or exception."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return fn(*args), None
    except Exception as e:  # a crashing phase is itself a blocker
        return None, e


def run(argv: list[str] | None = None) -> dict:
    argv = argv if argv is not None else sys.argv[1:]
    mode = _pick_mode(argv)
    verbose = "--verbose" in argv
    mode_args = ["--real"] if mode == "real" else ["--dry-run"]

    blockers: list[str] = []

    # ============================================================= #
    # Execute every phase (output suppressed unless --verbose)
    # ============================================================= #
    p35, e35 = _quiet(run_demo_validation.run)
    p36, e36 = _quiet(run_burn_in.run)
    p37, e37 = _quiet(run_phase37_integration.run)
    p38, e38 = _quiet(run_phase38_integration.run)
    p39, e39 = _quiet(deriv_smoke_test.run, mode_args)
    p391, e391 = _quiet(deriv_readiness_gate.run, mode_args)
    p392, e392 = _quiet(deriv_contract_verification.run, mode_args)
    p393, e393 = _quiet(deriv_live_gate.run, mode_args)

    for name, err in [("Phase35", e35), ("Phase36", e36), ("Phase37", e37),
                      ("Phase38", e38), ("Phase39", e39), ("Phase39.1", e391),
                      ("Phase39.2", e392), ("Phase39.3", e393)]:
        if err is not None:
            blockers.append(f"{name} crashed: {type(err).__name__}: {err}")

    # ============================================================= #
    # Extract sub-results
    # ============================================================= #
    rep35 = p35.get("report") if p35 else None
    lifecycle_ok = bool(rep35 and rep35.lifecycle_pass == rep35.lifecycle_total)
    failure_ok = bool(rep35 and rep35.failure_handled == rep35.failure_total)

    burn = p36.get("result") if p36 else None
    bstats = burn.session.stats() if burn else None
    trade_gate_ok = bool(burn and bstats and bstats.trade_count >= 500
                         and not burn.evaluation.stop_triggered)
    risk_guard_ok = bool(burn and burn.risk_guard_ok)
    try:
        from testing.broker_validation.demo_report import _execution_quality
        exec_quality = _execution_quality(burn.metrics) if burn else None
    except Exception:
        exec_quality = None

    adapter_safety_ok = bool(p37 and p37.get("demo_ready"))
    deriv_adapter_ok = bool(p38 and p38.get("ready"))
    smoke_ok = bool(p39 and p39.get("status") == "PASS")
    mapping_phase_ok = bool(p391 and all(p391.get("results", {}).values()))

    g = p393 or {}
    connection_ok = bool(g.get("connection_ok"))
    virtual_ok = bool(g.get("virtual_ok") and g.get("login_ok"))
    contracts_confirmed = bool(g.get("contract_confirmed"))
    contract_type_ok = bool(g.get("contract_type"))
    mapping_ok = bool(g.get("mapping_pass"))
    sl_tp_ok = bool(g.get("sl_tp_ok"))
    is_real_transport = bool(g.get("is_real_transport"))
    real_login_refused = bool(g.get("real_login_refused"))

    cfg = load_deriv_config()
    shadow_ok = cfg.shadow_mode is True
    no_live_capability = (not live_trading_enabled()) and real_login_refused

    live_confirmed = is_real_transport and connection_ok and virtual_ok

    # ============================================================= #
    # READY criteria (the 10 gating conditions)
    # ============================================================= #
    criteria = [
        ("Deriv connection successful", connection_ok),
        ("Account is virtual/demo", virtual_ok),
        ("contracts_for confirmed", contracts_confirmed),
        ("Contract type confirmed", contract_type_ok),
        ("Execution mapping confirmed", mapping_ok and mapping_phase_ok),
        ("SL/TP compatibility confirmed", sl_tp_ok),
        ("Shadow mode enabled", shadow_ok),
        ("No live trading capability", no_live_capability),
        ("Broker lifecycle tests pass", lifecycle_ok),
        ("Failure recovery tests pass", failure_ok),
    ]
    for label, ok in criteria:
        if not ok:
            blockers.append(f"unmet: {label}")

    # supporting infra checks (not in the 10 but must not be broken)
    for label, ok in [("Phase 36 risk guard", risk_guard_ok),
                      ("Phase 37 adapter safety", adapter_safety_ok),
                      ("Phase 38 Deriv adapter", deriv_adapter_ok),
                      ("Phase 39 smoke test", smoke_ok)]:
        if not ok:
            blockers.append(f"unmet: {label}")

    # ============================================================= #
    # HARD SAFETY ASSERTION (Phase 39.4 req 4)
    # ============================================================= #
    hard_fail = False
    if live_trading_enabled():
        blockers.append("HARD FAIL: LIVE_TRADING=true — this phase is DEMO ONLY")
        hard_fail = True

    # ============================================================= #
    # Verdict
    #   - LIVE_TRADING=true -> always BLOCKED (hard fail).
    #   - clean + live connection -> READY.
    #   - clean + simulated      -> DRY-RUN PASSED (never READY).
    #   - anything failing       -> BLOCKED.
    # ============================================================= #
    clean = len(blockers) == 0  # hard_fail and any unmet criterion add blockers
    if hard_fail:
        status = "BLOCKED"
    elif clean and live_confirmed:
        status = "READY"
    elif clean and not live_confirmed:
        status = "DRY-RUN PASSED"
    else:
        status = "BLOCKED"

    _print_report(mode, cfg, g, criteria, status, blockers,
                  exec_quality, bstats, trade_gate_ok, lifecycle_ok, failure_ok,
                  shadow_ok, live_confirmed)

    if verbose:
        print("\n[verbose] sub-phase return values:")
        for n, p in [("35", p35), ("36", bool(p36)), ("37", p37 and p37.get('demo_ready')),
                     ("38", p38 and p38.get('ready')), ("39", p39 and p39.get('status')),
                     ("39.1", p391 and p391.get('ready')),
                     ("39.2", p392 and p392.get('ready')),
                     ("39.3", p393 and p393.get('ready'))]:
            print(f"  Phase {n}: {p if not hasattr(p, 'demo_ready') else 'ok'}")

    return {"status": status, "blockers": blockers, "mode": mode,
            "criteria": criteria}


def _print_report(mode, cfg, g, criteria, status, blockers, exec_quality,
                  bstats, trade_gate_ok, lifecycle_ok, failure_ok, shadow_ok,
                  live_confirmed) -> None:
    line = "=" * 68
    print(line)
    print(f"APEX ULTRA DEMO READINESS REPORT          [preflight mode: {mode.upper()}]")
    print(line)
    print("READY CRITERIA:")
    for label, ok in criteria:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 68)
    conn = "LIVE" if live_confirmed else ("simulated" if mode == "dry-run" else "not connected")
    print(f"Connection        : {conn}")
    print(f"Account           : {g.get('symbol') and 'virtual/demo' if g.get('virtual_ok') else 'unverified'}"
          f"  (virtual={g.get('virtual_ok')}, login_ok={g.get('login_ok')})")
    print(f"Symbol            : {g.get('symbol') or cfg.symbol}")
    print(f"Contract          : {g.get('category') or '(unconfirmed)'}")
    print(f"Contract Type     : {g.get('contract_type') or '(unconfirmed)'}")
    print(f"Stake Model       : {g.get('stake_model') or '(unconfirmed)'}")
    print(f"SL/TP             : {'supported' if g.get('sl_tp_ok') else 'unconfirmed'}")
    print(f"Shadow Mode       : {'enabled' if shadow_ok else 'DISABLED'}")
    print(f"Lifecycle         : {'PASS' if lifecycle_ok else 'FAIL'}")
    print(f"Failure Recovery  : {'PASS' if failure_ok else 'FAIL'}")
    print(f"Execution Quality : {exec_quality if exec_quality is not None else 'n/a'}/100")
    print(f"500 Trade Gate    : {'PASS' if trade_gate_ok else 'FAIL'} "
          f"({bstats.trade_count if bstats else 0} trades)")
    print("-" * 68)
    if blockers:
        print("BLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
    else:
        print("BLOCKERS: (none)")
    print(line)
    print(f"FINAL STATUS: {status}")
    if status == "DRY-RUN PASSED":
        print("              NOT DEMO READY — simulated data cannot grant READY.")
        print("              Run with --real against a Deriv VIRTUAL account to verify.")
    print(line)


if __name__ == "__main__":
    run()
