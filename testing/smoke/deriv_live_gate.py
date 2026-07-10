"""
APEX ULTRA — Phase 39.3 Live Deriv Contract Verification Gate

Turns Phase 39.2's BLOCKED into READY ONLY after a real Deriv demo verification.
The confirmed contract is DERIVED from the live contracts_for response — no
MULTUP/MULTDOWN/multiplier/duration/stake assumptions. READY is structurally
impossible on simulated data: it requires a real DerivWebSocketTransport.

Modes: --real (live), --dry-run (flow check, ALWAYS BLOCKED). Default: auto.
"""

from __future__ import annotations

import importlib.util
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from infrastructure.broker import ConnectionMonitor  # noqa: E402
from infrastructure.broker.broker_interface import OrderSide  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    ApexOrderIntent,
    DerivDemoAdapter,
    DerivRealAccountBlocked,
    DerivSimulatedTransport,
    DerivWebSocketTransport,
    is_virtual_login,
    live_trading_enabled,
    load_deriv_config,
    map_intent_to_proposal,
    select_contract,
)


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
    blockers: list[str] = []

    if mode == "real":
        if not _ws_available():
            blockers.append("websocket-client not installed (pip install websocket-client)")
        if not load_deriv_config().token_present:
            blockers.append("DERIV_API_TOKEN not set (Deriv VIRTUAL account token)")
        if blockers:
            return _emit(mode, None, None, None, False, blockers, ready=False)

    cfg = load_deriv_config(require_token=(mode == "real"))

    # APEX intent (engine-side, broker-agnostic)
    intent = ApexOrderIntent(
        side=OrderSide.BUY, size=10.0, symbol=cfg.symbol,
        stop_loss=5.0, take_profit=10.0, comment="phase39.3 verification")
    pref_mult = int(os.environ["DERIV_MULTIPLIER"]) if os.environ.get("DERIV_MULTIPLIER") else None

    if mode == "real":
        transport = DerivWebSocketTransport(app_id=cfg.app_id, ws_url=cfg.ws_url)
    else:
        transport = DerivSimulatedTransport(symbol=cfg.symbol, currency=cfg.currency,
                                            is_virtual=True)
    adapter = DerivDemoAdapter(config=cfg.deriv_config(), transport=transport)
    monitor = ConnectionMonitor(adapter, max_reconnect_attempts=5)

    # ---- structural: READY forbidden on simulated data --------------- #
    is_real_transport = isinstance(adapter.transport, DerivWebSocketTransport) \
        and adapter._sim is None
    if not is_real_transport:
        blockers.append("simulated data: READY requires a live DerivWebSocketTransport "
                        "connection (Phase 39.3 forbids READY on simulated data)")

    # ---- 1. connect + authorize + virtual checks --------------------- #
    auth_ok = virtual_ok = login_ok = False
    try:
        monitor.start()
        auth_ok = adapter.is_connected()
        virtual_ok = adapter._is_virtual is True
        login_ok = is_virtual_login(adapter._loginid)
        if not auth_ok:
            blockers.append("authorize failed")
        if not virtual_ok:
            blockers.append("refused: is_virtual !== true")
        if not login_ok:
            blockers.append(f"refused: non-virtual loginid {adapter._loginid}")
    except DerivRealAccountBlocked as e:
        blockers.append(f"refused: {e}")
    except Exception as e:
        blockers.append(f"authorize error: {type(e).__name__}: {e}")

    # ---- live trading flag refusal ----------------------------------- #
    if live_trading_enabled():
        blockers.append("refused: LIVE_TRADING flag is enabled")

    # ---- 2. derive confirmed contract from contracts_for ------------- #
    selection = None
    if adapter.is_connected():
        try:
            raw = adapter._call({"contracts_for": cfg.symbol, "currency": cfg.currency})
            selection = select_contract(
                raw, cfg.symbol,
                needs_sl=intent.stop_loss is not None,
                needs_tp=intent.take_profit is not None,
                size=intent.size, preferred_multiplier=pref_mult)
            if not selection.confirmed:
                blockers.append("missing contract confirmation: "
                                + "; ".join(selection.reasons or ["no qualifying contract"]))
        except Exception as e:
            blockers.append(f"contracts_for error: {e}")

    # ---- 3. execution mapping validation ----------------------------- #
    mapping_pass = False
    mapped_request = None
    if selection is not None and selection.confirmed:
        spec = selection.to_spec()
        spec.multiplier = selection.multiplier if selection.category == "multiplier" else None
        mapped_request = map_intent_to_proposal(intent, spec, cfg.currency)
        needs_limit = intent.stop_loss is not None or intent.take_profit is not None
        has_limit = "limit_order" in mapped_request
        if needs_limit and not has_limit:
            blockers.append("SL/TP cannot be represented by the confirmed contract")
        else:
            mapping_pass = True

    # ---- 4. safety: real account login must be refused --------------- #
    real_login_refused = False
    try:
        DerivDemoAdapter(
            transport=DerivSimulatedTransport(is_virtual=False, loginid="CR5550000")
        ).connect()
        blockers.append("safety: real account login was NOT refused")
    except DerivRealAccountBlocked:
        real_login_refused = True

    # ---- verdict ----------------------------------------------------- #
    ready = (is_real_transport and auth_ok and virtual_ok and login_ok
             and not live_trading_enabled()
             and selection is not None and selection.confirmed
             and mapping_pass and real_login_refused)

    result = _emit(mode, cfg, intent, selection, mapping_pass, blockers, ready,
                   mapped_request=mapped_request)
    result.update({
        "is_real_transport": is_real_transport,
        "connection_ok": auth_ok,
        "virtual_ok": virtual_ok,
        "login_ok": login_ok,
        "contract_confirmed": bool(selection and selection.confirmed),
        "sl_tp_ok": bool(selection and selection.supports_limit_order),
        "symbol": cfg.symbol,
        "contract_type": (f"{selection.contract_type_buy}/{selection.contract_type_sell}"
                          if selection and selection.contract_type_buy else None),
        "category": selection.category if selection else None,
        "stake_model": (f"{selection.basis} (min={selection.min_stake}, "
                        f"max={selection.max_stake})" if selection else None),
        "real_login_refused": real_login_refused,
    })
    return result


def _emit(mode, cfg, intent, selection, mapping_pass, blockers, ready,
          mapped_request=None) -> dict:
    line = "=" * 66
    print(line)
    print(f"APEX ULTRA — PHASE 39.3 LIVE DERIV CONTRACT VERIFICATION GATE  [{mode.upper()}]")
    if mode == "dry-run":
        print("  NOTE: simulated transport — BLOCKED by design (no READY on sim data).")
    print(line)
    print(f"PHASE 39.3 STATUS: {'READY' if ready else 'BLOCKED'}")
    print("-" * 66)
    print("CONFIRMED CONTRACT:")
    if selection is not None and (selection.confirmed or selection.contract_type_buy):
        print(f"  symbol         : {selection.symbol}")
        print(f"  contract_type  : {selection.contract_type_buy} / "
              f"{selection.contract_type_sell}  (category={selection.category})")
        print(f"  duration       : {selection.duration_model}")
        print(f"  stake model    : {selection.basis} "
              f"(min={selection.min_stake}, max={selection.max_stake}"
              + (f", multiplier={selection.multiplier}" if selection.multiplier else "")
              + ")")
        print(f"  SL/TP supported: {selection.supports_limit_order}")
        print(f"  available types: {selection.available_types}")
    else:
        print("  (not confirmed — no live contracts_for verification)")
    print("-" * 66)
    print("EXECUTION MAPPING:")
    if intent is not None:
        print("  APEX intent:")
        print(f"    direction    : {intent.side.value}")
        print(f"    risk size    : {intent.size}")
        print(f"    stop loss    : {intent.stop_loss}")
        print(f"    take profit  : {intent.take_profit}")
        print("  Mapped Deriv request:")
        if mapped_request:
            print(f"    contract_type: {mapped_request.get('contract_type')}")
            print(f"    symbol       : {mapped_request.get('symbol')}")
            print(f"    parameters   : "
                  f"{ {k: v for k, v in mapped_request.items() if k != 'limit_order'} }")
            print(f"    limit_order  : {mapped_request.get('limit_order', '(none)')}")
        else:
            print("    (not mapped — contract not confirmed)")
    print(f"  RESULT: {'PASS' if mapping_pass else 'FAIL'}")
    print("-" * 66)
    print("BLOCKERS:")
    if blockers:
        for b in blockers:
            print(f"  - {b}")
    else:
        print("  (none)")
    print(line)
    print(f"PHASE 39.3 STATUS: {'READY' if ready else 'BLOCKED'}")
    print(line)
    return {"ready": ready, "blockers": blockers, "mode": mode,
            "mapping_pass": mapping_pass}


if __name__ == "__main__":
    run()
