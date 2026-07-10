"""
APEX ULTRA — Deriv REST/OTP Transport (Phase 41, EXPERIMENTAL, opt-in)

WHY THIS EXISTS
---------------
Deriv migrated this account to the new developer platform, which issues `pat_`
tokens. Those are rejected by the legacy WebSocket `authorize` flow (confirmed:
auth probe RESULT: FAIL_TOKEN). The new platform authenticates differently:

    PAT (Bearer) --> REST: list accounts --> REST: request OTP for an account
                --> open an authenticated WebSocket URL (OTP embedded)
                --> NO `authorize` message is sent

This module implements that flow behind the SAME adapter-facing contract as the
legacy transport, so the adapter does not change. It is **experimental** and
**opt-in**: nothing constructs it unless explicitly asked.

ISOLATION / CONSTRAINTS (Phase 41 spec)
---------------------------------------
- The legacy DerivWebSocketTransport is NOT modified or imported here.
- No strategy / signal / risk / execution / shadow / UI code is touched.
- The BrokerConnection contract is unchanged; this satisfies the same
  connect()/close()/is_open()/call() interface the adapter already uses.

MILESTONE 1 — READ-ONLY (this file)
-----------------------------------
Implements ONLY:
    authorize  -> authenticate, pick account, confirm virtual, return identity
    balance    -> read account balance
    ping       -> liveness
contracts_for / ticks are provided as best-effort read-only translations where
the new API exposes them; if the exact new-API shape is unconfirmed they return
a structured {"error": {...}} rather than guessing.

buy / sell / proposal / proposal_open_contract are INTENTIONALLY NOT
IMPLEMENTED — they raise NotImplementedError. Do not implement until the
read-only gate (deriv_rest_auth_probe) prints REST AUTH READY.

EVERYTHING NETWORK-FACING IS UNVERIFIED FROM THE BUILD ENVIRONMENT.
Endpoints/field names below follow Deriv's current public docs and are marked
NEEDS-LIVE-VERIFICATION; the probe surfaces the real API error verbatim so the
first live run tells us the truth instead of us guessing.
"""

from __future__ import annotations

import json
import itertools
from typing import Any, Optional

# Reuse ONLY the exception types + interface expectations from the legacy module.
# (Importing exceptions is not "modifying" the legacy transport; we raise the
#  same types so the adapter's except-clauses behave identically.)
from .deriv_transport import (
    DerivTransportError,
    DerivTimeout,
    DerivConnectionError,
)

# --- New-API endpoints (NEEDS-LIVE-VERIFICATION) ---------------------------- #
# Base REST host for the new options trading API.
REST_BASE = "https://api.derivws.com/trading/v1"
# Account listing + OTP endpoints (per current docs; confirm exact paths live).
ACCOUNTS_PATH = "/options/accounts"
OTP_PATH_TMPL = "/options/accounts/{account_id}/otp"
# Authenticated WS URL is RETURNED by the OTP call; we do not hardcode it.
# Public (no-auth) market-data WS, if needed for ticks:
PUBLIC_WS = "wss://api.derivws.com/trading/v1/options/ws/public"


class DerivRestError(DerivTransportError):
    """A REST/OTP-layer failure carrying the raw API error for diagnostics."""

    def __init__(self, message: str, *, raw: Any = None, status: Optional[int] = None):
        super().__init__(message)
        self.raw = raw
        self.status = status


class ExecutionForbiddenError(DerivTransportError):
    """
    Raised if any execution/trading method is invoked on this transport.
    Milestone 2 is read-only market data; trading is hard-blocked.
    """


def _redact(token: str) -> str:
    if not token:
        return "<empty>"
    if len(token) <= 12:
        return f"len={len(token)} <short,hidden>"
    return f"len={len(token)} prefix={token[:6]} suffix={token[-4:]}"


class DerivRestOtpTransport:
    """
    Experimental transport implementing the adapter contract
    (connect / close / is_open / call) over Deriv's new REST/OTP API.

    Construct explicitly to opt in, e.g.:

        from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport
        transport = DerivRestOtpTransport(api_token=os.environ["DERIV_API_TOKEN"])
        adapter = DerivAdapter(config=..., transport=transport)

    Nothing creates this automatically.
    """

    def __init__(
        self,
        api_token: str,
        *,
        app_id: Optional[str] = None,
        rest_base: str = REST_BASE,
        prefer_virtual: bool = True,
        http_timeout: float = 20.0,
    ) -> None:
        self.api_token = api_token
        # PAT tokens require a Deriv-App-ID header (per live API: HTTP 401
        # "Deriv-App-ID header is required for PAT tokens"). Falls back to the
        # DERIV_APP_ID env var if not passed explicitly.
        import os as _os
        self.app_id = app_id or _os.environ.get("DERIV_APP_ID", "")
        self.rest_base = rest_base.rstrip("/")
        self.prefer_virtual = prefer_virtual
        self.http_timeout = http_timeout

        self._ws = None
        self._req_id = itertools.count(1)
        self._account: Optional[dict] = None   # chosen account record
        self._ws_url: Optional[str] = None      # authenticated WS URL from OTP
        self._authorized = False

    # ------------------------------------------------------------------ #
    # HTTP helper (stdlib only; no new deps)
    # ------------------------------------------------------------------ #
    def _http(self, method: str, path: str, *, body: Optional[dict] = None) -> tuple[int, Any]:
        import urllib.request
        import urllib.error

        url = self.rest_base + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.api_token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        # Required for PAT tokens (live API: 401 without it).
        if self.app_id:
            req.add_header("Deriv-App-ID", self.app_id)
        try:
            with urllib.request.urlopen(req, timeout=self.http_timeout) as resp:
                status = resp.getcode()
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            # surface the API's error body verbatim — critical for the probe
            try:
                raw = e.read().decode("utf-8")
            except Exception:
                raw = ""
            return e.code, _try_json(raw)
        except urllib.error.URLError as e:
            raise DerivConnectionError(f"REST connect failed: {e}") from e
        return status, _try_json(raw)

    # ------------------------------------------------------------------ #
    # Lifecycle (adapter contract)
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        """
        Establish the authenticated session WITHOUT sending a legacy authorize.
        Auth is completed lazily in the translated `authorize` call so the
        adapter's existing connect()->call({"authorize":...}) flow still works.
        We only validate the token is present here.
        """
        if not self.api_token:
            raise DerivConnectionError("no api_token provided to REST transport")
        # Connection proper (OTP WS) is opened during the translated authorize,
        # because the adapter expects authorize to be where identity is resolved.
        self._authorized = False

    def close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None
        self._authorized = False

    def is_open(self) -> bool:
        # "Open" once we've authenticated and (optionally) opened the OTP WS.
        return self._authorized

    # ------------------------------------------------------------------ #
    # Translation layer: legacy request dict -> new API -> legacy response
    # ------------------------------------------------------------------ #
    def call(self, request: dict, timeout: float = 5.0) -> dict:
        if "ping" in request:
            return {"msg_type": "ping", "ping": "pong" if self._authorized else "pong"}
        if "authorize" in request:
            return self._authorize(request["authorize"])
        if "balance" in request:
            return self._balance()
        if "contracts_for" in request:
            return self._contracts_for(request)
        if "ticks" in request:
            return self._ticks(request)
        # --- Milestone 1: trading ops intentionally unavailable ----------
        if any(k in request for k in ("proposal", "buy", "sell", "proposal_open_contract")):
            raise NotImplementedError(
                "REST/OTP transport is read-only (Milestone 1). Trading ops are "
                "not implemented until the auth/read-only gate passes "
                "(deriv_rest_auth_probe -> REST AUTH READY)."
            )
        return {"error": {"code": "UnrecognisedRequest", "message": "unknown op"}}

    # ------------------------------------------------------------------ #
    # authorize: PAT -> list accounts -> choose -> OTP -> identity
    # Returns the SAME shape the adapter expects from legacy authorize:
    #   {"msg_type":"authorize","authorize":{loginid,is_virtual,balance,currency}}
    # or {"error": {...}} on failure.
    # ------------------------------------------------------------------ #
    def _authorize(self, token: str) -> dict:
        # 1. list accounts (Bearer PAT)
        status, payload = self._http("GET", ACCOUNTS_PATH)
        if status >= 400 or _is_error(payload):
            return _err("RestAuthFailed",
                        f"accounts listing failed (HTTP {status})", raw=payload)

        accounts = _coerce_accounts(payload)
        if not accounts:
            return _err("NoAccounts",
                        "no accounts returned by REST accounts endpoint",
                        raw=payload)

        # 2. choose account (prefer virtual/demo)
        chosen = _choose_account(accounts, prefer_virtual=self.prefer_virtual)
        if chosen is None:
            return _err("NoVirtualAccount",
                        "no virtual/demo account available on this token",
                        raw={"accounts": accounts})
        self._account = chosen

        # 3. request OTP -> authenticated WS URL (NEEDS-LIVE-VERIFICATION)
        acct_id = chosen.get("account_id") or chosen.get("loginid") or chosen.get("id")
        if not acct_id:
            return _err("AccountIdMissing",
                        "chosen account has no id field", raw=chosen)
        status, otp_payload = self._http(
            "POST", OTP_PATH_TMPL.format(account_id=acct_id), body={})
        if status >= 400 or _is_error(otp_payload):
            return _err("OtpFailed",
                        f"OTP request failed (HTTP {status})", raw=otp_payload)

        self._ws_url = _extract_ws_url(otp_payload)
        # We do NOT require opening the WS for Milestone 1 identity/balance,
        # but record auth success once identity is resolved.
        self._authorized = True

        is_virtual = bool(_account_is_virtual(chosen))
        loginid = chosen.get("loginid") or chosen.get("account_id") or str(acct_id)
        currency = chosen.get("currency") or chosen.get("cur") or "USD"
        balance = _account_balance(chosen)

        return {
            "msg_type": "authorize",
            "authorize": {
                "loginid": loginid,
                "is_virtual": 1 if is_virtual else 0,
                "balance": balance,
                "currency": currency,
                "account_list": [
                    {"loginid": loginid, "is_virtual": 1 if is_virtual else 0}
                ],
                # carry-through for diagnostics (ignored by adapter):
                "_rest_ws_url_present": bool(self._ws_url),
            },
        }

    def _balance(self) -> dict:
        if not self._authorized or not self._account:
            return _err("NotAuthorized", "authorize first")
        # If the accounts payload already carried balance, reuse it; otherwise
        # re-fetch the chosen account. (NEEDS-LIVE-VERIFICATION on exact path.)
        bal = _account_balance(self._account)
        cur = self._account.get("currency") or "USD"
        loginid = self._account.get("loginid") or self._account.get("account_id")
        if bal is None:
            return _err("BalanceUnavailable",
                        "balance not present in account record; "
                        "live API path unconfirmed", raw=self._account)
        return {"msg_type": "balance",
                "balance": {"balance": bal, "currency": cur, "loginid": loginid}}

    def _contracts_for(self, request: dict) -> dict:
        # Delegate to the named market-data method (capture-first).
        sym = request.get("contracts_for", "")
        return self.get_contract_availability(sym)

    def _ticks(self, request: dict) -> dict:
        sym = request.get("ticks", "")
        return self.get_tick(sym)

    # ================================================================== #
    # Milestone 2 — OTP WebSocket + READ-ONLY market data
    # ================================================================== #
    def _ensure_ws(self) -> Optional[dict]:
        """
        Open the authenticated OTP WebSocket if not already open.
        Returns None on success, or an {"error": {...}} dict on failure.
        The OTP is embedded in self._ws_url; NO authorize message is sent.
        """
        if self._ws is not None:
            return None
        if not self._ws_url:
            return _err("NoOtpUrl", "no OTP websocket URL; call authorize() first")
        try:
            import websocket  # websocket-client
        except ImportError as e:
            return _err("NoWebsocketClient",
                        "websocket-client not installed: " + str(e))
        try:
            self._ws = websocket.create_connection(self._ws_url, timeout=15)
        except Exception as e:
            return _err("OtpWsConnectFailed", f"could not open OTP ws: {e}")
        return None

    def _ws_roundtrip(self, request: dict, *, collect: int = 1,
                      timeout: float = 12.0) -> dict:
        """
        Send one request on the OTP WS and collect up to `collect` messages.
        ALWAYS returns the raw frames under "_raw_frames" so the probe can
        display the true response shape (rule #4: capture, don't guess).
        """
        err = self._ensure_ws()
        if err:
            return err
        req_id = next(self._req_id)
        payload = {**request, "req_id": req_id}
        frames: list = []
        try:
            self._ws.send(json.dumps(payload))
            self._ws.settimeout(timeout)
            import time as _t
            deadline = _t.time() + timeout
            while len(frames) < collect and _t.time() < deadline:
                raw = self._ws.recv()
                try:
                    msg = json.loads(raw)
                except Exception:
                    msg = {"_unparsable": raw[:500]}
                frames.append(msg)
                # stop early on an error frame
                if isinstance(msg, dict) and msg.get("error"):
                    break
        except Exception as e:
            return _err("OtpWsError", f"ws round-trip failed: {e}",
                        raw={"sent": list(request)[0], "frames": frames})
        return {"_raw_frames": frames, "_sent": list(request)[0]}

    def _ws_forget_all(self, stream_type: str) -> None:
        if self._ws is None:
            return
        try:
            self._ws.send(json.dumps({"forget_all": stream_type}))
            self._ws.settimeout(3.0)
            self._ws.recv()
        except Exception:
            pass

    # ---- named read-only methods (used by the market-data probe) ------- #
    def get_account_info(self) -> dict:
        """Return resolved identity from authorize() (no new network call)."""
        if not self._authorized or not self._account:
            return _err("NotAuthorized", "authorize first")
        a = self._account
        return {
            "loginid": a.get("loginid") or a.get("account_id"),
            "is_virtual": 1 if _account_is_virtual(a) else 0,
            "currency": a.get("currency") or "USD",
            "account_type": a.get("account_type") or a.get("type"),
        }

    def get_balance(self) -> dict:
        """Read-only balance (named wrapper over the translated balance)."""
        return self._balance()

    def get_active_symbols(self) -> dict:
        """Discover tradable symbol names (rule #4: don't assume R_100 exists)."""
        return self._ws_roundtrip({"active_symbols": "brief"}, collect=1, timeout=12.0)

    def get_tick(self, symbol: str) -> dict:
        """
        One-shot latest tick via ticks_history (count=1). Capture-first:
        returns raw frames plus a best-effort parse under "tick" if the
        legacy shape is present.
        """
        if not symbol:
            return _err("NoSymbol", "symbol required")
        res = self._ws_roundtrip(
            {"ticks_history": symbol, "count": 1, "end": "latest", "style": "ticks"},
            collect=1, timeout=12.0)
        if "error" in res:
            return res
        parsed = _parse_tick_history(res.get("_raw_frames", []))
        res["tick"] = parsed   # may be None if shape differs (then raw is shown)
        return res

    def subscribe_ticks(self, symbol: str, count: int = 3) -> dict:
        """
        Subscribe to a few streaming ticks, then forget. Read-only.
        Returns raw frames + best-effort parsed ticks list.
        """
        if not symbol:
            return _err("NoSymbol", "symbol required")
        res = self._ws_roundtrip(
            {"ticks": symbol, "subscribe": 1}, collect=count, timeout=20.0)
        self._ws_forget_all("ticks")
        if "error" in res:
            return res
        ticks = [t for t in (_parse_tick_stream(f) for f in res.get("_raw_frames", [])) if t]
        res["ticks"] = ticks
        return res

    def get_contract_availability(self, symbol: str) -> dict:
        """
        contracts_for the symbol (legacy shape expected on the OTP WS).
        Capture-first; parses available contract types if present.
        """
        if not symbol:
            return _err("NoSymbol", "symbol required")
        res = self._ws_roundtrip({"contracts_for": symbol}, collect=1, timeout=12.0)
        if "error" in res:
            return res
        res["available"] = _parse_contracts_for(res.get("_raw_frames", []))
        return res

    # ---- EXECUTION: hard-blocked in this phase ------------------------- #
    # These exist ONLY to raise. There is no code path that can place,
    # price, or close a trade through this transport in Milestone 2.
    def _forbidden(self, name: str):
        raise ExecutionForbiddenError(
            f"{name}() is disabled: REST/OTP transport is READ-ONLY market data "
            "(Milestone 2). Execution is not implemented in this phase.")

    def proposal(self, *a, **k): self._forbidden("proposal")
    def buy(self, *a, **k): self._forbidden("buy")
    def sell(self, *a, **k): self._forbidden("sell")
    def place_order(self, *a, **k): self._forbidden("place_order")
    def sell_contract(self, *a, **k): self._forbidden("sell_contract")
    def buy_contract(self, *a, **k): self._forbidden("buy_contract")


# --------------------------------------------------------------------------- #
# Helpers (pure; no I/O)
# --------------------------------------------------------------------------- #
def _try_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return {"_raw": raw}


def _is_error(payload: Any) -> bool:
    return isinstance(payload, dict) and (
        "error" in payload or "errors" in payload or payload.get("status") == "error")


def _err(code: str, message: str, *, raw: Any = None) -> dict:
    return {"error": {"code": code, "message": message, "raw": raw}}


def _coerce_accounts(payload: Any) -> list[dict]:
    """Normalize whatever the accounts endpoint returns into a list of dicts."""
    if isinstance(payload, list):
        return [a for a in payload if isinstance(a, dict)]
    if isinstance(payload, dict):
        for key in ("accounts", "data", "results", "items"):
            v = payload.get(key)
            if isinstance(v, list):
                return [a for a in v if isinstance(a, dict)]
    return []


def _account_is_virtual(acct: dict) -> bool:
    # Try common shapes: is_virtual flag, account_type, or VRTC login prefix.
    if "is_virtual" in acct:
        return bool(acct["is_virtual"])
    at = str(acct.get("account_type") or acct.get("type") or "").lower()
    if at in ("demo", "virtual"):
        return True
    login = str(acct.get("loginid") or acct.get("account_id") or acct.get("id") or "")
    return login.upper().startswith("VRT")


def _account_balance(acct: dict):
    for k in ("balance", "amount", "available_balance"):
        v = acct.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict) and isinstance(v.get("amount"), (int, float)):
            return float(v["amount"])
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                pass
    return None


def _choose_account(accounts: list[dict], *, prefer_virtual: bool) -> Optional[dict]:
    if prefer_virtual:
        for a in accounts:
            if _account_is_virtual(a):
                return a
        return None  # Milestone 1 is demo-only; do not fall back to real
    return accounts[0] if accounts else None


def _extract_ws_url(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    for k in ("ws_url", "url", "websocket_url", "wss"):
        v = payload.get(k)
        if isinstance(v, str) and v.startswith("ws"):
            return v
    # sometimes nested under data/result
    for parent in ("data", "result"):
        sub = payload.get(parent)
        if isinstance(sub, dict):
            u = _extract_ws_url(sub)
            if u:
                return u
    return None


# --- capture-first parsers: return None if the expected shape is absent ----- #
# (Rule #4: do not invent mappings. If None, the probe shows the raw frame.)
def _parse_tick_history(frames: list) -> Optional[dict]:
    for f in frames:
        if not isinstance(f, dict):
            continue
        # legacy ticks_history -> {"history":{"prices":[...],"times":[...]}}
        hist = f.get("history")
        if isinstance(hist, dict) and hist.get("prices") and hist.get("times"):
            try:
                return {"quote": float(hist["prices"][-1]),
                        "epoch": int(hist["times"][-1])}
            except Exception:
                return None
        # some variants return a single {"tick":{...}}
        tick = f.get("tick")
        if isinstance(tick, dict) and "quote" in tick:
            return {"quote": tick.get("quote"), "epoch": tick.get("epoch"),
                    "bid": tick.get("bid"), "ask": tick.get("ask")}
    return None


def _parse_tick_stream(frame: Any) -> Optional[dict]:
    if not isinstance(frame, dict):
        return None
    tick = frame.get("tick")
    if isinstance(tick, dict) and "quote" in tick:
        return {"symbol": tick.get("symbol"), "quote": tick.get("quote"),
                "epoch": tick.get("epoch"), "bid": tick.get("bid"),
                "ask": tick.get("ask")}
    return None


def _parse_contracts_for(frames: list) -> Optional[list]:
    for f in frames:
        if not isinstance(f, dict):
            continue
        cf = f.get("contracts_for")
        if isinstance(cf, dict) and isinstance(cf.get("available"), list):
            out = []
            for c in cf["available"]:
                if isinstance(c, dict):
                    out.append({
                        "contract_type": c.get("contract_type"),
                        "contract_category": c.get("contract_category"),
                        "min_stake": c.get("min_stake"),
                        "max_stake": c.get("max_stake"),
                    })
            return out
    return None
