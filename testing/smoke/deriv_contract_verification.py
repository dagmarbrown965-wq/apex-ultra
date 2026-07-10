"""
APEX ULTRA — Phase 39.2 Real Deriv Contract Verification

Verifies the ACTUAL Deriv account contract configuration via contracts_for and,
on a successful live verification + validation order, clears the readiness gate
to READY. Offline/dry-run runs remain BLOCKED (a simulated contracts_for is not
a real verification).

Modes: --real (live Deriv), --dry-run (simulated). Default: auto.
Do not continue to burn-in until this prints READY from a --real run.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker import ConnectionMonitor  # noqa: E402
from infrastructure.broker.broker_interface import OrderSide  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    ApexOrderIntent,
    DerivDemoAdapter,
    DerivRealAccountBlocked,
    DerivSimulatedTransport,
    DerivWebSocketTransport,
    confirm_apex_mapping,
    is_virtual_login,
    live_trading_enabled,
    load_contract_spec,
    load_deriv_config,
    verify_contracts_for,
)
from testing.broker_validation.execution_metrics import ExecutionMetrics  # noqa: E402


def _ws_available() -> bool:
    return importlib.util.find_spec("websocket") is not None


def _pick_mode(argv: list[str]) -> str:
    if "--dry-run" in argv:
        return "dry-run"
    if "--real" in argv:
        return "real"
    cfg = load_deriv_config()
    return "real" if (cfg.token_present and _ws_available()) else "dry-run"


def run(argv: list[str] | None = None) -> dict:
    argv = argv if argv is not None else sys.argv[1:]
    mode = _pick_mode(argv)

    if mode == "real":
        missing = []
        if not _ws_available():
            missing.append("websocket-client not installed (pip install websocket-client)")
        if not load_deriv_config().token_present:
            missing.append("DERIV_API_TOKEN not set (Deriv VIRTUAL account token)")
        if missing:
            _blocked_preamble(missing)
            return {"ready": False, "blockers": missing, "mode": "real"}

    cfg = load_deriv_config(require_token=(mode == "real"))
    spec = load_contract_spec()
    size = 10.0

    if mode == "real":
        transport = DerivWebSocketTransport(app_id=cfg.app_id, ws_url=cfg.ws_url)
    else:
        transport = DerivSimulatedTransport(symbol=cfg.symbol, currency=cfg.currency,
                                            is_virtual=True)
    adapter = DerivDemoAdapter(config=cfg.deriv_config(), transport=transport)
    monitor = ConnectionMonitor(adapter, max_reconnect_attempts=5)
    metrics = ExecutionMetrics()

    R = {"AUTH": False, "CONTRACT CONFIRMATION": False, "PROPOSAL": False,
         "BUY": False, "OPEN STATUS": False, "CLOSE": False,
         "BALANCE RECONCILIATION": False}
    blockers: list[str] = []
    verification = None
    mapping_rows: list[tuple] = []
    mapping_ok = False
    demo_balance = final_balance = final_pl = None

    # ----- 1-2. Connect + authorize ---------------------------------- #
    try:
        monitor.start()
        R["AUTH"] = (adapter.is_connected() and adapter._is_virtual is True
                     and is_virtual_login(adapter._loginid))
        if not R["AUTH"]:
            blockers.append("authorize/virtual-account check failed")
    except DerivRealAccountBlocked as e:
        blockers.append(f"authorize blocked: {e}")
    except Exception as e:
        blockers.append(f"authorize failed: {type(e).__name__}: {e}")

    if adapter.is_connected():
        # ----- 3. contracts_for verification ------------------------- #
        try:
            raw = adapter._call({"contracts_for": cfg.symbol,
                                 "currency": cfg.currency})
            verification = verify_contracts_for(raw, spec, cfg.symbol, size)
            R["CONTRACT CONFIRMATION"] = verification.confirmed
            if not verification.confirmed:
                blockers += [f"contract: {i}" for i in verification.issues]
        except Exception as e:
            blockers.append(f"contracts_for: {e}")

        # ----- 4. APEX mapping vs actual fields ---------------------- #
        if verification is not None:
            mapping_ok, mapping_rows, map_issues = confirm_apex_mapping(spec, verification)
            blockers += [f"mapping: {m}" for m in map_issues]

        # ----- 5. One DEMO validation order -------------------------- #
        bal = adapter.getBalance()
        demo_balance = bal.get("balance")
        contract_id = None

        intent = ApexOrderIntent(OrderSide.BUY, size, cfg.symbol,
                                 stop_loss=5.0, take_profit=10.0,
                                 comment="phase39.2 verification order")
        try:
            from infrastructure.broker.deriv import map_intent_to_proposal
            prop = adapter.transport.call(
                map_intent_to_proposal(intent, spec, cfg.currency), timeout=10.0)
            R["PROPOSAL"] = "proposal" in prop and "error" not in prop
            if not R["PROPOSAL"]:
                blockers.append(f"proposal: {prop.get('error')}")
        except Exception as e:
            blockers.append(f"proposal: {e}")

        try:
            mid0 = adapter.current_mid
            t0 = time.perf_counter()
            result = adapter.submit_intent(intent, spec, timeout=10.0)
            metrics.record_fill(result, (time.perf_counter() - t0) * 1000.0, mid0)
            contract_id = result.order.id
            R["BUY"] = result.order.filled_qty > 0 and bool(contract_id)
        except Exception as e:
            blockers.append(f"buy: {e}")

        if contract_id:
            try:
                poc = adapter.getOrderStatus(contract_id)
                R["OPEN STATUS"] = (poc.get("contract_id") == contract_id
                                    and poc.get("limit_order") is not None)
            except Exception as e:
                blockers.append(f"open status: {e}")
            try:
                close = adapter.closePosition(cfg.symbol, timeout=10.0)
                R["CLOSE"] = close.get("closed") is True
                final_pl = close.get("profit")
            except Exception as e:
                blockers.append(f"close: {e}")
            try:
                final_balance = adapter.getBalance().get("balance")
                if None not in (final_balance, demo_balance, final_pl):
                    R["BALANCE RECONCILIATION"] = abs(
                        (final_balance - demo_balance) - final_pl) < 1e-2
            except Exception as e:
                blockers.append(f"balance reconciliation: {e}")

    # ----- SAFETY ---------------------------------------------------- #
    real_blocked = False
    try:
        DerivDemoAdapter(
            transport=DerivSimulatedTransport(is_virtual=False, loginid="CR5550000")
        ).connect()
    except DerivRealAccountBlocked:
        real_blocked = True
    live_disabled = not live_trading_enabled()

    # ----- READY / BLOCKED ------------------------------------------- #
    confirmation_is_live = (mode == "real")
    if not confirmation_is_live:
        blockers.append("dry-run: contracts_for is simulated — run --real to confirm")
    trade_ok = all(R.values())
    ready = (confirmation_is_live and trade_ok and mapping_ok
             and real_blocked and live_disabled)

    _print_report(mode, cfg, spec, verification, mapping_rows, mapping_ok, R,
                   metrics, demo_balance, final_balance, final_pl,
                   real_blocked, live_disabled, blockers, ready)
    return {"ready": ready, "results": R, "blockers": blockers, "mode": mode}


def _blocked_preamble(missing: list[str]) -> None:
    print("=" * 66)
    print("APEX ULTRA — PHASE 39.2 REAL DERIV CONTRACT VERIFICATION  [mode: REAL]")
    print("=" * 66)
    print("Cannot verify live contract — prerequisites missing:")
    for m in missing:
        print(f"  - {m}")
    print("\nOffline flow check: "
          "python -m testing.smoke.deriv_contract_verification --dry-run")
    print("=" * 66)
    print("PHASE 39.2 STATUS: BLOCKED")
    print("=" * 66)


def _print_report(mode, cfg, spec, v, mapping_rows, mapping_ok, R, metrics,
                  demo_balance, final_balance, final_pl, real_blocked,
                  live_disabled, blockers, ready) -> None:
    line = "=" * 66
    print(line)
    print(f"APEX ULTRA — PHASE 39.2 REAL DERIV CONTRACT VERIFICATION  [mode: {mode.upper()}]")
    if mode == "dry-run":
        print("  NOTE: contracts_for is SIMULATED here; a --real run is required")
        print("        to genuinely confirm the contract and reach READY.")
    print(line)
    print("CONFIRMED CONTRACT:")
    if v is not None:
        print(f"  symbol         : {v.symbol}  (exists={v.symbol_exists})")
        print(f"  contract_type  : {v.contract_type}  category={v.contract_category}")
        print(f"  available types: {v.available_types}")
        print(f"  parameters     : {v.parameters()}")
        print(f"  stake model    : {v.stake_model}  "
              f"(min={v.min_stake}, max={v.max_stake})")
        print(f"  SL supported   : {v.sl_supported}")
        print(f"  TP supported   : {v.tp_supported}")
        print(f"  close supported: {v.close_supported}")
    else:
        print("  (not verified — not connected)")
    print("-" * 66)
    print("APEX MAPPING (-> actual Deriv fields):")
    for apex_f, deriv_f, val in mapping_rows:
        print(f"  {apex_f:<16} -> {deriv_f:<28} = {val}")
    print(f"  mapping valid  : {mapping_ok}")
    print("-" * 66)
    print("VALIDATION ORDER:")
    for k in ("AUTH", "CONTRACT CONFIRMATION", "PROPOSAL", "BUY", "OPEN STATUS",
              "CLOSE", "BALANCE RECONCILIATION"):
        print(f"  {k:<24}: {'PASS' if R[k] else 'FAIL'}")
    print(f"  (slippage {metrics.avg_slippage_bps:.3f} bps, P/L {final_pl}, "
          f"balance {demo_balance} -> {final_balance})")
    print("-" * 66)
    print("SAFETY:")
    print(f"  real account blocked : {'PASS' if real_blocked else 'FAIL'}")
    print(f"  live trading disabled: {'PASS' if live_disabled else 'FAIL'} "
          f"(LIVE_TRADING={live_trading_enabled()})")
    if blockers:
        print("-" * 66)
        print("BLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
    print(line)
    print(f"PHASE 39.2 STATUS: {'READY' if ready else 'BLOCKED'}")
    if not ready:
        print("  -> Do NOT continue to burn-in until READY (from a --real run).")
    print(line)


if __name__ == "__main__":
    run()
