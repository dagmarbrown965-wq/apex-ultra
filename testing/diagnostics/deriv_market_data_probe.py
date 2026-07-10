import json, os, sys
from infrastructure.broker.deriv.rest_transport import (
    DerivRestOtpTransport, ExecutionForbiddenError,
    DerivTransportError, DerivConnectionError, _redact)

EXEC = ("proposal","buy","sell","place_order","sell_contract","buy_contract")

def show_raw(label, obj):
    print("    --- RAW " + label + " ---")
    try: print("    " + json.dumps(obj, indent=2)[:2500].replace("\n","\n    "))
    except Exception: print("    " + repr(obj)[:2500])

def fail(stage, msg, raw=None):
    print("\n" + "="*64)
    print("FAILED at " + stage + ": " + msg)
    if raw is not None: show_raw(stage, raw)
    print("="*64)
    print("\nSTATUS:\nBLOCKED  (read-only market data NOT proven)")
    return 1

def main():
    print("="*64)
    print("APEX ULTRA - DERIV REST MARKET-DATA PROBE  [Phase 41.0 read-only]")
    print("="*64)
    token = os.environ.get("DERIV_API_TOKEN","")
    app_id = os.environ.get("DERIV_APP_ID","")
    symbol = os.environ.get("DERIV_SYMBOL","R_100")
    live = os.environ.get("LIVE_TRADING","false").strip().lower() in ("1","true","yes","on")
    print("\nTOKEN        : " + _redact(token))
    print("Deriv-App-ID : " + (app_id or "(missing!)"))
    print("symbol       : " + symbol)
    print("LIVE_TRADING : " + str(live))
    if live: return fail("SAFETY","LIVE_TRADING is enabled; refusing")
    if not token: return fail("SAFETY","DERIV_API_TOKEN not set")

    res = {}
    t = DerivRestOtpTransport(api_token=token, app_id=app_id or None)

    print("\n[REST AUTH]")
    try:
        t.connect(); auth = t.call({"authorize": token}, timeout=20.0)
    except (DerivConnectionError, DerivTransportError) as e:
        return fail("REST AUTH", str(e))
    if "error" in auth:
        return fail("REST AUTH", str(auth["error"].get("code"))+": "+str(auth["error"].get("message")), raw=auth["error"].get("raw"))
    acct = auth["authorize"]
    print("    loginid    : " + str(acct.get("loginid")))
    print("    is_virtual : " + str(acct.get("is_virtual")))
    res["Authentication"]="PASS"

    print("\n[ACCOUNT]")
    if acct.get("is_virtual") != 1:
        return fail("ACCOUNT","account is NOT virtual/demo")
    print("    virtual/demo confirmed"); res["Virtual Account"]="PASS"

    print("\n[BALANCE]")
    bal = t.get_balance()
    if "error" in bal: return fail("BALANCE", str(bal["error"].get("message")), raw=bal["error"].get("raw"))
    b = bal.get("balance",{})
    print("    balance    : " + str(b.get("balance")) + " " + str(b.get("currency")))
    res["Balance Retrieval"]="PASS"

    print("\n[SYMBOL DISCOVERY] active_symbols")
    syms = t.get_active_symbols()
    if "error" in syms:
        print("    note: " + str(syms["error"].get("message")))
        show_raw("active_symbols", syms["error"].get("raw"))
    else:
        show_raw("active_symbols first frame", (syms.get("_raw_frames") or [None])[0])

    print("\n[TICKS]")
    tick = t.get_tick(symbol)
    if "error" in tick:
        return fail("TICKS", str(tick["error"].get("message")), raw=tick.get("error"))
    if tick.get("tick"):
        print("    latest tick: " + str(tick["tick"])); res["Tick Stream"]="PASS"
    else:
        print("    tick shape not recognised - RAW below (adapt, do not guess):")
        show_raw("ticks_history", tick.get("_raw_frames")); res["Tick Stream"]="NEEDS-RAW"
    sub = t.subscribe_ticks(symbol, count=3)
    if "error" not in sub and sub.get("ticks"):
        print("    streamed " + str(len(sub["ticks"])) + " ticks; first: " + str(sub["ticks"][0]))
    elif "error" not in sub:
        print("    subscribe frames differ - RAW:"); show_raw("ticks subscribe", sub.get("_raw_frames"))

    print("\n[CONTRACT AVAILABILITY]")
    cav = t.get_contract_availability(symbol)
    if "error" in cav:
        print("    error: " + str(cav["error"].get("message")))
        show_raw("contracts_for", cav.get("_raw_frames") or cav.get("error")); res["Contract Discovery"]="NEEDS-RAW"
    elif cav.get("available"):
        types = sorted({c.get("contract_type") for c in cav["available"] if c.get("contract_type")})
        print("    contract types: " + str(types)); res["Contract Discovery"]="PASS"
    else:
        print("    contracts_for shape not recognised - RAW below:")
        show_raw("contracts_for", cav.get("_raw_frames")); res["Contract Discovery"]="NEEDS-RAW"

    print("\n[EXECUTION SURFACE]")
    exposed = 0
    for name in EXEC:
        m = getattr(t, name, None)
        if m is None: continue
        try:
            m(); print("    !! " + name + " did NOT raise"); exposed += 1
        except ExecutionForbiddenError: pass
        except TypeError:
            try:
                m(None); print("    !! " + name + " did NOT raise"); exposed += 1
            except ExecutionForbiddenError: pass
    print("    execution methods exposed: " + str(exposed))
    try: t.close()
    except Exception: pass
    if exposed != 0:
        return fail("EXECUTION SURFACE", str(exposed) + " exposed")

    needs = [k for k,v in res.items() if v=="NEEDS-RAW"]
    print("\n" + "="*64)
    print("PHASE 41.0 - REST MARKET DATA VALIDATION\n")
    for label in ("Authentication","Virtual Account","Balance Retrieval","Tick Stream","Contract Discovery"):
        print(label.ljust(20) + " " + res.get(label,"MISSING"))
    print("\n" + "Trading Capability".ljust(20) + " BLOCKED")
    print("Execution Surface".ljust(20) + " " + str(exposed))
    print("\nSTATUS:")
    if needs:
        print("READ-ONLY MARKET DATA PARTIAL - capture RAW for: " + ", ".join(needs))
        return 2
    print("READ-ONLY MARKET DATA READY")
    return 0

sys.exit(main())
