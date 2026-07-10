"""
APEX ULTRA — Deriv REST/OTP Auth Probe (Phase 41, Milestone 1, read-only)

Exercises the EXPERIMENTAL DerivRestOtpTransport through the same legacy-shaped
calls the adapter uses, but ONLY the read-only ones:

    authorize -> identity + is_virtual
    balance   -> account balance

It sends NO trading messages. buy/sell/proposal are not implemented in the
transport yet and are not called here.

OUTPUT CONTRACT (per Phase 41 spec):
    REST AUTH READY                  (all read-only checks passed, demo account)
    BLOCKED: <exact API error>       (with the verbatim error payload)

It never prints "DEMO READY" — that claim belongs only to the real engine gate
(apex_demo_ready) once a working transport passes it.

Run:
    py -m testing.diagnostics.deriv_rest_auth_probe

Reads DERIV_API_TOKEN (PAT) from the environment. The token is never printed in
full — only a redacted fingerprint.
"""

from __future__ import annotations

import json
import os
import sys

from infrastructure.broker.deriv.rest_transport import (
    DerivRestOtpTransport,
    DerivTransportError,
    DerivConnectionError,
    _redact,
)


def _blocked(msg: str, raw=None) -> int:
    print("\n" + "=" * 64)
    print(f"BLOCKED: {msg}")
    if raw is not None:
        print("\nExact API payload:")
        try:
            print(json.dumps(raw, indent=2)[:4000])
        except Exception:
            print(repr(raw)[:4000])
    print("=" * 64)
    print("\n(No DEMO READY claim. This only reports the REST auth/read-only state.)")
    return 1


def main() -> int:
    print("=" * 64)
    print("APEX ULTRA — DERIV REST/OTP AUTH PROBE   [Milestone 1, read-only]")
    print("=" * 64)

    token = os.environ.get("DERIV_API_TOKEN", "")
    app_id = os.environ.get("DERIV_APP_ID", "")
    print(f"\n[1] TOKEN         : {_redact(token)}")
    if not token:
        return _blocked("DERIV_API_TOKEN not set")
    print(f"    kind          : {'pat_ (new platform)' if token.startswith('pat_') else token[:3] + '…'}")
    print(f"    Deriv-App-ID  : {app_id if app_id else '(not set — PAT tokens require this!)'}")

    transport = DerivRestOtpTransport(api_token=token, app_id=app_id or None)

    # --- connect (no network in legacy sense; validates token presence) --- #
    print("\n[2] CONNECT       : initialising REST transport")
    try:
        transport.connect()
    except DerivConnectionError as e:
        return _blocked(f"connect failed: {e}")

    # --- authorize: REST accounts -> choose virtual -> OTP -> identity ---- #
    print("[3] AUTHORIZE     : PAT -> REST accounts -> OTP session")
    try:
        auth = transport.call({"authorize": token}, timeout=20.0)
    except DerivConnectionError as e:
        return _blocked(f"network error reaching REST API: {e}")
    except DerivTransportError as e:
        return _blocked(f"transport error: {e}")

    if "error" in auth:
        err = auth["error"]
        return _blocked(
            f"{err.get('code','?')}: {err.get('message','')}",
            raw=err.get("raw"))

    acct = auth.get("authorize", {})
    loginid = acct.get("loginid")
    is_virtual = acct.get("is_virtual")
    print(f"    loginid       : {loginid}")
    print(f"    is_virtual    : {is_virtual}")
    print(f"    otp ws url    : {'present' if acct.get('_rest_ws_url_present') else 'absent'}")

    # --- confirm virtual/demo -------------------------------------------- #
    print("\n[4] ACCOUNT TYPE  : confirming virtual/demo")
    if is_virtual != 1:
        return _blocked(f"account {loginid} is not virtual/demo (is_virtual={is_virtual})")

    # --- balance (read-only) --------------------------------------------- #
    print("[5] BALANCE       : reading account balance")
    bal = transport.call({"balance": 1})
    if "error" in bal:
        err = bal["error"]
        return _blocked(f"balance: {err.get('code','?')}: {err.get('message','')}",
                        raw=err.get("raw"))
    b = bal.get("balance", {})
    print(f"    balance       : {b.get('balance')} {b.get('currency')}")
    print(f"    loginid       : {b.get('loginid')}")

    # --- all read-only checks passed ------------------------------------- #
    print("\n" + "=" * 64)
    print("REST AUTH READY")
    print("=" * 64)
    print("Authenticated, identity resolved, virtual/demo confirmed, balance read.")
    print("Trading ops remain unimplemented until this milestone is accepted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
