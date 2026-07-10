"""
APEX ULTRA — Phase 39.1 Deriv DEMO Readiness Gate

A gate (READY / BLOCKED), not an optimizer. It:
  1. Confirms Deriv account mode (authorize, is_virtual, VRTC login).
  2. Confirms the trading instrument (symbol, contract type, proposal params) by
     checking the candidate contract type against contracts_for — NO assumption
     of MULTUP/MULTDOWN/multiplier is treated as confirmed on its own.
  3. Confirms the APEX->Deriv execution mapping (side, size, SL, TP, close).
  4. Runs ONE demo validation trade and reports each step.

The gate only returns READY from a REAL, live virtual-account run with the
contract type confirmed. Offline/dry-run runs are BLOCKED by design.

Modes: --real (live Deriv), --dry-run (simulated transport). Default: auto.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker import ConnectionMonitor  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    ApexOrderIntent,
    DerivDemoAdapter,
    DerivRealAccountBlocked,
    DerivSimulatedTransport,
    DerivWebSocketTransport,
    describe_mapping,
    is_virtual_login,
    live_trading_enabled,
    load_contract_spec,
    load_deriv_config,
    map_intent_to_proposal,
    validate_mapping,
)
from infrastructure.broker.broker_interface import OrderSide  # noqa: E402
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
        if not load_contract_spec().confirmed:
            missing.append("DERIV_CONTRACT_CONFIRMED not true — confirm contract type first")
        if missing:
            print("=" * 64)
            print("APEX ULTRA — PHASE 39.1 DERIV DEMO READINESS GATE  [mode: REAL]")
            print("=" * 64)
            print("Cannot run live gate — prerequisites missing:")
            for m in missing:
                print(f"  - {m}")
            print("\nRun an offline flow check with: "
                  "python -m testing.smoke.deriv_readiness_gate --dry-run")
            print("=" * 64)
            print("PHASE 39.1 STATUS: BLOCKED")
            return {"ready": False, "blockers": missing, "mode": "real"}

    cfg = load_deriv_config(require_token=(mode == "real"))
    spec = load_contract_spec()

    if mode == "real":
        transport = DerivWebSocketTransport(app_id=cfg.app_id, ws_url=cfg.ws_url)
    else:
        transport = DerivSimulatedTransport(symbol=cfg.symbol, currency=cfg.currency,
                                            is_virtual=True)
    adapter = DerivDemoAdapter(config=cfg.deriv_config(), transport=transport)
    monitor = ConnectionMonitor(adapter, max_reconnect_attempts=5)
    metrics = ExecutionMetrics()

    R = {"AUTH": False, "TICK STREAM": False, "PROPOSAL": False, "BUY": False,
         "OPEN CONTRACT": False, "CLOSE": False, "BALANCE RECONCILIATION": False}
    blockers: list[str] = []
    auth_virtual = auth_login_ok = False
    instrument_confirmed = False
    available_types: list[str] = []
    mapping_ok = False
    demo_balance = final_balance = final_pl = None

    # ===================== 1. Account mode ============================ #
    try:
        monitor.start()
        authorized = adapter.is_connected()
        auth_virtual = adapter._is_virtual is True
        auth_login_ok = is_virtual_login(adapter._loginid)
        R["AUTH"] = authorized and auth_virtual and auth_login_ok
    except DerivRealAccountBlocked as e:
        blockers.append(f"authorize blocked: {e}")
    except Exception as e:
        blockers.append(f"authorize failed: {type(e).__name__}: {e}")

    # ===================== 2. Instrument ============================= #
    proposal_params = {}
    if adapter.is_connected():
        ok_contract, available_types, issues = adapter.confirm_contract(spec)
        instrument_confirmed = ok_contract
        if not ok_contract:
            blockers += issues
        # build the candidate proposal params for the report
        sample_intent = ApexOrderIntent(OrderSide.BUY, cfg_size := 10.0, cfg.symbol,
                                        stop_loss=5.0, take_profit=10.0)
        proposal_params = map_intent_to_proposal(sample_intent, spec, cfg.currency)

        # ===================== 3. Execution mapping ================== #
        mapping_ok, map_issues = validate_mapping(sample_intent, spec)
        if not mapping_ok:
            blockers += [f"mapping: {m}" for m in map_issues]

        # ===================== 4. ONE validation trade ============== #
        bal = adapter.getBalance()
        demo_balance = bal.get("balance")

        # TICK STREAM
        try:
            ticks = adapter.stream_ticks(count=3, timeout=10.0)
            R["TICK STREAM"] = len(ticks) >= 1
        except Exception as e:
            blockers.append(f"tick stream: {e}")

        # PROPOSAL (explicit, read-only)
        contract_id = None
        try:
            prop = adapter.transport.call(proposal_params, timeout=10.0)
            R["PROPOSAL"] = "proposal" in prop and "error" not in prop
            if not R["PROPOSAL"]:
                blockers.append(f"proposal: {prop.get('error')}")
        except Exception as e:
            blockers.append(f"proposal: {e}")

        # BUY (via mapped intent: side/size/SL/TP)
        try:
            intent = ApexOrderIntent(OrderSide.BUY, 10.0, cfg.symbol,
                                     stop_loss=5.0, take_profit=10.0,
                                     comment="phase39.1 validation")
            mid0 = adapter.current_mid
            t0 = time.perf_counter()
            result = adapter.submit_intent(intent, spec, timeout=10.0)
            exec_lat = (time.perf_counter() - t0) * 1000.0
            metrics.record_fill(result, exec_lat, mid0)
            contract_id = result.order.id
            R["BUY"] = result.order.filled_qty > 0 and bool(contract_id)
        except Exception as e:
            blockers.append(f"buy: {e}")

        # OPEN CONTRACT
        if contract_id:
            try:
                poc = adapter.getOrderStatus(contract_id)
                lo = poc.get("limit_order")
                R["OPEN CONTRACT"] = (poc.get("contract_id") == contract_id
                                      and lo is not None)
                if lo is None:
                    blockers.append("open contract: limit_order (SL/TP) not echoed")
            except Exception as e:
                blockers.append(f"open contract: {e}")

            # CLOSE
            try:
                close = adapter.closePosition(cfg.symbol, timeout=10.0)
                R["CLOSE"] = close.get("closed") is True
                final_pl = close.get("profit")
            except Exception as e:
                blockers.append(f"close: {e}")

            # BALANCE RECONCILIATION
            try:
                final_balance = adapter.getBalance().get("balance")
                if (final_balance is not None and demo_balance is not None
                        and final_pl is not None):
                    delta = final_balance - demo_balance
                    R["BALANCE RECONCILIATION"] = abs(delta - final_pl) < 1e-2
            except Exception as e:
                blockers.append(f"balance reconciliation: {e}")

    # ===================== SAFETY =================================== #
    real_blocked = False
    try:
        DerivDemoAdapter(
            transport=DerivSimulatedTransport(is_virtual=False, loginid="CR5550000")
        ).connect()
    except DerivRealAccountBlocked:
        real_blocked = True
    live_disabled = not live_trading_enabled()

    # ===================== READY / BLOCKED ========================== #
    trade_lines_ok = all(R.values())
    if mode != "real":
        blockers.append("dry-run: not a live Deriv connection (run --real for READY)")
    if mode == "real" and not instrument_confirmed:
        blockers.append("contract type not confirmed via live contracts_for")
    safety_ok = real_blocked and live_disabled
    ready = (mode == "real" and trade_lines_ok and auth_virtual and auth_login_ok
             and instrument_confirmed and mapping_ok and safety_ok)

    # ===================== REPORT =================================== #
    line = "=" * 64
    print(line)
    print(f"APEX ULTRA — PHASE 39.1 DERIV DEMO READINESS GATE  [mode: {mode.upper()}]")
    if mode == "dry-run":
        print("  NOTE: simulated transport — instrument confirmation is simulated;")
        print("        a live --real run is required to reach READY.")
    print(line)
    print("ACCOUNT MODE:")
    print(f"  loginid          : {adapter._loginid}")
    print(f"  is_virtual===true: {auth_virtual}")
    print(f"  VRTC/demo format : {auth_login_ok}")
    print("-" * 64)
    print("INSTRUMENT (candidate — confirm before live):")
    print(f"  symbol           : {cfg.symbol}")
    print(f"  contract type    : BUY={spec.contract_type_buy}  "
          f"SELL={spec.contract_type_sell}  (confirmed_live={instrument_confirmed})")
    print(f"  contracts_for    : {available_types or 'n/a'}")
    print(f"  proposal params  : {proposal_params or 'n/a'}")
    print(f"  candidate note   : {spec.candidate_note}")
    print("-" * 64)
    print("EXECUTION MAPPING (APEX -> Deriv):")
    if adapter.is_connected():
        for apex_f, deriv_f, val in describe_mapping(
                ApexOrderIntent(OrderSide.BUY, 10.0, cfg.symbol,
                                stop_loss=5.0, take_profit=10.0),
                spec, cfg.currency):
            print(f"  {apex_f:<14} -> {deriv_f:<28} = {val}")
        print(f"  mapping valid    : {mapping_ok}")
    else:
        print("  (skipped — not connected)")
    print("-" * 64)
    print("ONE DEMO VALIDATION TRADE:")
    for k in ("AUTH", "TICK STREAM", "PROPOSAL", "BUY", "OPEN CONTRACT", "CLOSE",
              "BALANCE RECONCILIATION"):
        print(f"  {k:<24}: {'PASS' if R[k] else 'FAIL'}")
    print(f"  (slippage {metrics.avg_slippage_bps:.3f} bps, "
          f"P/L {final_pl}, balance {demo_balance} -> {final_balance})")
    print("-" * 64)
    print("SAFETY:")
    print(f"  real account blocked : {'PASS' if real_blocked else 'FAIL'}")
    print(f"  live trading disabled: {'PASS' if live_disabled else 'FAIL'} "
          f"(LIVE_TRADING={live_trading_enabled()})")
    if blockers:
        print("-" * 64)
        print("BLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
    print(line)
    print(f"PHASE 39.1 STATUS: {'READY' if ready else 'BLOCKED'}")
    print(line)

    return {"ready": ready, "results": R, "blockers": blockers, "mode": mode}


if __name__ == "__main__":
    run()
