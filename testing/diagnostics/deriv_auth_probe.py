import json, sys, time
from infrastructure.broker.deriv.config_loader import load_deriv_config
from infrastructure.broker.deriv.deriv_transport import (
    DerivWebSocketTransport, DerivTransportError, DerivConnectionError)

def mask(t):
    if not t: return "<empty>"
    if len(t) <= 12: return f"len={len(t)} value=<short,hidden>"
    return f"len={len(t)} prefix={t[:8]!r} suffix={t[-6:]!r}"

def main():
    print("="*60); print("APEX ULTRA - DERIV AUTH PROBE  [authorize only]"); print("="*60)
    cfg = load_deriv_config(require_token=False)
    tok = cfg.api_token
    print("\n[1] TOKEN FORMAT (local)")
    print("    token :", mask(tok))
    print("    app_id:", repr(cfg.app_id))
    print("    ws_url:", cfg.ws_url)
    if not tok or tok == "DEMO-TOKEN":
        print("\nRESULT: FAIL_TOKEN_FORMAT (missing/placeholder)"); return 2
    kind = "pat_ (new platform PAT)" if tok.startswith("pat_") else ("a1- (legacy)" if tok.startswith("a1-") else "unknown prefix")
    print("    kind  :", kind)
    print("\n[2] ENDPOINT (open websocket)")
    tr = DerivWebSocketTransport(app_id=cfg.app_id, ws_url=cfg.ws_url)
    try:
        t0=time.time(); tr.connect(); print(f"    connect: OK ({(time.time()-t0)*1000:.0f} ms)")
    except DerivConnectionError as e:
        print("    connect: FAIL -", e); print("\nRESULT: FAIL_ENDPOINT"); return 3
    print("\n[3] AUTHORIZE (only request sent)")
    try:
        resp = tr.call({"authorize": tok}, timeout=15.0)
    except DerivTransportError as e:
        print("    transport error:", e); print("\nRESULT: FAIL_ENDPOINT"); tr.close(); return 3
    safe = json.loads(json.dumps(resp))
    if isinstance(safe.get("echo_req"), dict) and "authorize" in safe["echo_req"]:
        safe["echo_req"]["authorize"] = "<redacted>"
    print("    raw response:"); print(json.dumps(safe, indent=2))
    tr.close()
    err = resp.get("error")
    if err:
        c = err.get("code",""); print("\n    error code:", c, "| message:", err.get("message",""))
        if c == "InvalidToken":
            print("\nRESULT: FAIL_TOKEN  (token rejected by legacy authorize)")
            print("Not app-id, not endpoint, not format, not account-type."); return 10
        if c in ("InvalidAppID","InvalidApplicationID"):
            print("\nRESULT: FAIL_APPID"); return 11
        print("\nRESULT: FAIL_OTHER"); return 12
    a = resp.get("authorize")
    if isinstance(a, dict):
        iv = a.get("is_virtual"); print("\n    authorized: YES | loginid:", a.get("loginid"), "| is_virtual:", iv)
        if iv == 1: print("\nRESULT: OK_DEMO"); return 0
        print("\nRESULT: OK_REAL (real account; would block on is_virtual)"); return 20
    print("\nRESULT: FAIL_OTHER (no error, no authorize)"); return 12

sys.exit(main())
