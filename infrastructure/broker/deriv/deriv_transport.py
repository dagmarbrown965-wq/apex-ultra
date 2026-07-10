"""
APEX ULTRA — Deriv Transport (Phase 38)

Deriv is a WebSocket, message-based API. A request is a JSON object keyed by its
operation (authorize, balance, ticks, proposal, buy, sell,
proposal_open_contract, ping); the response echoes `msg_type` and `req_id`.

  - DerivWebSocketTransport: real connection via `websocket-client`.
  - DerivSimulatedTransport: in-process simulation of Deriv's message shapes
    with fault injection, for offline validation of the adapter's logic.

Demo vs real is decided by the authorized account's `is_virtual` flag, NOT by
the URL (the WS endpoint is identical for both). The adapter enforces that.
"""

from __future__ import annotations

import itertools
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from ..mock_broker import FaultConfig, MarketConfig

DEFAULT_WS_URL = "wss://ws.derivws.com/websockets/v3"


class DerivTransportError(Exception):
    """Base Deriv transport failure."""


class DerivTimeout(DerivTransportError):
    """No response within the deadline."""


class DerivConnectionError(DerivTransportError):
    """WebSocket not open / dropped."""


class DerivTransport(Protocol):
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def is_open(self) -> bool: ...
    def call(self, request: dict, timeout: float = 5.0) -> dict: ...


# --------------------------------------------------------------------------- #
# Real transport (production; requires `pip install websocket-client`)
# --------------------------------------------------------------------------- #
class DerivWebSocketTransport:
    def __init__(self, app_id: str, ws_url: str = DEFAULT_WS_URL) -> None:
        self.app_id = app_id
        self.ws_url = ws_url
        self._ws = None
        self._req_id = itertools.count(1)

    def connect(self) -> None:
        try:
            import websocket  # websocket-client
        except ImportError as e:  # pragma: no cover - environment dependent
            raise DerivConnectionError(
                "websocket-client not installed; run "
                "`pip install websocket-client` to use the live Deriv transport"
            ) from e
        url = f"{self.ws_url}?app_id={self.app_id}"
        try:
            self._ws = websocket.create_connection(url, timeout=10)
        except Exception as e:  # pragma: no cover
            raise DerivConnectionError(f"ws connect failed: {e}") from e

    def close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None

    def is_open(self) -> bool:
        return self._ws is not None and getattr(self._ws, "connected", False)

    def send(self, request: dict) -> int:  # pragma: no cover - needs network
        if not self.is_open():
            raise DerivConnectionError("ws not open")
        req_id = next(self._req_id)
        self._ws.send(json.dumps({**request, "req_id": req_id}))
        return req_id

    def recv(self, timeout: float = 5.0) -> dict:  # pragma: no cover - needs network
        if not self.is_open():
            raise DerivConnectionError("ws not open")
        self._ws.settimeout(timeout)
        try:
            return json.loads(self._ws.recv())
        except Exception as e:
            raise DerivConnectionError(str(e)) from e

    def call(self, request: dict, timeout: float = 5.0) -> dict:  # pragma: no cover
        if not self.is_open():
            raise DerivConnectionError("ws not open")
        req_id = next(self._req_id)
        request = {**request, "req_id": req_id}
        self._ws.settimeout(timeout)
        try:
            self._ws.send(json.dumps(request))
            deadline = time.time() + timeout
            while time.time() < deadline:
                raw = self._ws.recv()
                msg = json.loads(raw)
                # ignore unrelated subscription frames; match our req_id
                if msg.get("req_id") == req_id or "req_id" not in msg:
                    return msg
            raise DerivTimeout(f"no response to {list(request)[0]}")
        except DerivTransportError:
            raise
        except Exception as e:
            raise DerivConnectionError(str(e)) from e


# --------------------------------------------------------------------------- #
# Simulated transport (offline validation of the adapter's Deriv logic)
# --------------------------------------------------------------------------- #
class DerivSimulatedTransport:
    def __init__(
        self,
        symbol: str = "R_100",
        starting_balance: float = 10_000.0,
        currency: str = "USD",
        is_virtual: bool = True,
        loginid: Optional[str] = None,
        market: Optional[MarketConfig] = None,
        seed: int = 38,
        tick_latency: bool = False,
    ) -> None:
        self.symbol = symbol
        self.currency = currency
        self.is_virtual = is_virtual
        self.loginid = loginid or ("VRTC1234567" if is_virtual else "CR7654321")
        self.market = market or MarketConfig(mid=1000.0, spread=0.4)
        self.tick_latency = tick_latency
        self.faults = FaultConfig()
        self._rng = random.Random(seed)
        self._spot = self.market.mid
        self._balance = starting_balance
        self._authorized = False
        self._dropped = False
        self._contract_seq = 0
        self._proposal_seq = 0
        self._proposals: dict[str, dict] = {}
        self._contracts: dict[str, dict] = {}
        self.positions: dict[str, dict] = {}
        self._pending: list[dict] = []
        self._stream_active = False
        self._stream_symbol = symbol

    # -- link state ----------------------------------------------------- #
    def connect(self) -> None:
        self._dropped = False

    def close(self) -> None:
        self._authorized = False

    def is_open(self) -> bool:
        return not self._dropped

    def force_drop(self) -> None:
        self._dropped = True

    def restore(self) -> None:
        self._dropped = False

    # -- streaming (tick subscription) ---------------------------------- #
    def send(self, request: dict) -> int:
        if self._dropped:
            raise DerivConnectionError("ws link down")
        if "ticks" in request and request.get("subscribe"):
            self._stream_active = True
            self._stream_symbol = request.get("ticks", self.symbol)
            return 1
        # non-stream request: resolve now, deliver on next recv()
        self._pending.append(self.call(request))
        return 1

    def recv(self, timeout: float = 5.0) -> dict:
        if self._dropped:
            raise DerivConnectionError("ws link down")
        if self._pending:
            self._latency()
            return self._pending.pop(0)
        if self._stream_active:
            self._latency()
            return self._tick_response({"ticks": self._stream_symbol})
        raise DerivTimeout("no streamed data")

    # -- routing -------------------------------------------------------- #
    def call(self, request: dict, timeout: float = 5.0) -> dict:
        if self._dropped:
            raise DerivConnectionError("ws link down")
        if "ping" in request:
            self._latency()
            return {"msg_type": "ping", "ping": "pong"}
        if "time" in request:
            return {"msg_type": "time", "time": int(time.time())}
        if "authorize" in request:
            return self._authorize(request)
        if "balance" in request:
            self._latency()
            return {"msg_type": "balance",
                    "balance": {"balance": self._balance,
                                "currency": self.currency,
                                "loginid": self.loginid}}
        if "ticks" in request:
            return self._tick_response(request)
        if "contracts_for" in request:
            return self._contracts_for(request)
        if "proposal" in request:
            return self._proposal(request)
        if "buy" in request:
            return self._buy(request, timeout)
        if "sell" in request:
            return self._sell(request)
        if "proposal_open_contract" in request:
            return self._open_contract(request)
        return {"error": {"code": "UnrecognisedRequest", "message": "unknown"}}

    # -- handlers ------------------------------------------------------- #
    def _authorize(self, request: dict) -> dict:
        self._authorized = True
        return {"msg_type": "authorize",
                "authorize": {"loginid": self.loginid,
                              "is_virtual": 1 if self.is_virtual else 0,
                              "balance": self._balance,
                              "currency": self.currency,
                              "account_list": [
                                  {"loginid": self.loginid,
                                   "is_virtual": 1 if self.is_virtual else 0}]}}

    def _tick_response(self, request: dict) -> dict:
        if self.tick_latency:
            self._latency()
        self._tick()
        half = self.market.spread / 2.0
        return {"msg_type": "tick",
                "tick": {"symbol": request.get("ticks", self.symbol),
                         "quote": self._spot,
                         "bid": self._spot - half,
                         "ask": self._spot + half,
                         "epoch": int(time.time())}}

    def _contracts_for(self, request: dict) -> dict:
        # Mirrors Deriv's contracts_for shape. Field names/values should be
        # re-verified against the live response; parsing is defensive.
        sym = request.get("contracts_for", self.symbol)
        return {"msg_type": "contracts_for",
                "contracts_for": {
                    "symbol": sym,
                    "min_stake": "0.35",
                    "max_stake": "2000.00",
                    "available": [
                        {"contract_type": "MULTUP", "contract_category": "multiplier",
                         "multiplier_range": [30, 60, 100, 150, 200, 300],
                         "min_stake": "1.00", "max_stake": "2000.00",
                         "supports_limit_order": 1,
                         "underlying_symbol": sym},
                        {"contract_type": "MULTDOWN", "contract_category": "multiplier",
                         "multiplier_range": [30, 60, 100, 150, 200, 300],
                         "min_stake": "1.00", "max_stake": "2000.00",
                         "supports_limit_order": 1,
                         "underlying_symbol": sym},
                        {"contract_type": "CALL", "contract_category": "callput",
                         "min_contract_duration": "1m", "max_contract_duration": "365d",
                         "min_stake": "0.35", "max_stake": "50000.00",
                         "supports_limit_order": 0, "underlying_symbol": sym},
                        {"contract_type": "PUT", "contract_category": "callput",
                         "min_contract_duration": "1m", "max_contract_duration": "365d",
                         "min_stake": "0.35", "max_stake": "50000.00",
                         "supports_limit_order": 0, "underlying_symbol": sym},
                    ]}}

    def _proposal(self, request: dict) -> dict:
        self._tick()
        self._proposal_seq += 1
        pid = f"prop-{self._proposal_seq}"
        side = self._side_of(request)
        half = self.market.spread / 2.0
        ask = (self._spot + half) if side == "buy" else (self._spot - half)
        self._proposals[pid] = {"side": side, "spot": self._spot, "ask": ask,
                                "symbol": request.get("symbol", self.symbol),
                                "amount": float(request.get("amount", 1.0)),
                                "limit_order": request.get("limit_order"),
                                "multiplier": request.get("multiplier"),
                                "contract_type": request.get("contract_type")}
        return {"msg_type": "proposal",
                "proposal": {"id": pid, "ask_price": ask, "spot": self._spot,
                             "limit_order": request.get("limit_order"),
                             "payout": float(request.get("amount", 1.0)) * 1.95}}

    def _buy(self, request: dict, timeout: float) -> dict:
        if self.faults.timeout_next:
            self.faults.timeout_next = False
            time.sleep(min(0.02, timeout))
            raise DerivTimeout("no buy ack")
        if self.faults.reject_next:
            self.faults.reject_next = False
            return {"msg_type": "buy",
                    "error": {"code": "InsufficientBalance",
                              "message": self.faults.reject_reason}}
        if self.faults.disconnect_during_next:
            self.faults.disconnect_during_next = False
            self._latency()
            self.force_drop()
            raise DerivConnectionError("dropped before buy ack")

        self._latency()
        pid = request.get("buy")
        prop = self._proposals.get(pid) if isinstance(pid, str) else None
        side = prop["side"] if prop else "buy"
        amount = prop["amount"] if prop else float(request.get("price", 1.0))
        self._tick()
        half = self.market.spread / 2.0
        base = (self._spot + half) if side == "buy" else (self._spot - half)
        slip = abs(self._rng.gauss(self.market.extra_slippage_bps, 0.6)) / 1e4
        entry = base + base * slip if side == "buy" else base - base * slip

        filled = amount
        partial = False
        if self.faults.partial_fill_next:
            self.faults.partial_fill_next = False
            filled = round(amount * self.faults.partial_fill_ratio, 8)
            partial = True

        self._contract_seq += 1
        cid = f"{self._contract_seq:09d}"
        self._contracts[cid] = {"contract_id": cid, "side": side,
                                "entry_spot": entry, "amount": filled,
                                "symbol": prop["symbol"] if prop else self.symbol,
                                "limit_order": prop.get("limit_order") if prop else None,
                                "multiplier": prop.get("multiplier") if prop else None,
                                "is_sold": 0, "status": "open", "profit": 0.0}
        self._balance = round(self._balance - filled, 4)  # stake deducted
        self._apply(side, filled, entry)
        return {"msg_type": "buy",
                "buy": {"contract_id": cid, "buy_price": entry,
                        "start_spot": entry, "longcode": "demo contract",
                        "transaction_id": self._contract_seq,
                        "filled_amount": filled, "partial": partial}}

    def _sell(self, request: dict) -> dict:
        cid = str(request.get("sell"))
        c = self._contracts.get(cid)
        if not c or c["is_sold"]:
            return {"msg_type": "sell",
                    "error": {"code": "NoOpenPosition", "message": "nothing to sell"}}
        self._latency()
        self._tick()
        half = self.market.spread / 2.0
        exit_side = "sell" if c["side"] == "buy" else "buy"
        exit_spot = (self._spot - half) if exit_side == "sell" else (self._spot + half)
        # multiplier-style P/L: directional move on the staked amount
        if c["side"] == "buy":
            profit = (exit_spot - c["entry_spot"]) * c["amount"]
        else:
            profit = (c["entry_spot"] - exit_spot) * c["amount"]
        profit = round(profit, 4)
        c["is_sold"] = 1
        c["status"] = "sold"
        c["exit_spot"] = exit_spot
        c["profit"] = profit
        # stake was deducted on buy; return stake + profit on sell (net = profit)
        self._balance = round(self._balance + c["amount"] + profit, 4)
        self._apply(exit_side, c["amount"], exit_spot)
        return {"msg_type": "sell",
                "sell": {"contract_id": cid, "sold_for": round(exit_spot, 4),
                         "profit": profit, "balance_after": self._balance,
                         "transaction_id": self._contract_seq}}

    def _open_contract(self, request: dict) -> dict:
        cid = str(request["proposal_open_contract"].get("contract_id"))
        c = self._contracts.get(cid)
        if not c:
            return {"msg_type": "proposal_open_contract",
                    "error": {"code": "InvalidContract", "message": "unknown"}}
        return {"msg_type": "proposal_open_contract",
                "proposal_open_contract": {
                    "contract_id": cid, "is_sold": c["is_sold"],
                    "status": c["status"], "entry_spot": c["entry_spot"],
                    "profit": c.get("profit", 0.0),
                    "limit_order": c.get("limit_order"),
                    "multiplier": c.get("multiplier"),
                    "underlying": c["symbol"]}}

    # -- internals ------------------------------------------------------ #
    def _side_of(self, request: dict) -> str:
        ct = str(request.get("contract_type", "MULTUP")).upper()
        return "sell" if ct in ("MULTDOWN", "PUT", "SELL") else "buy"

    def _apply(self, side: str, qty: float, price: float) -> None:
        pos = self.positions.setdefault(
            self.symbol, {"symbol": self.symbol, "qty": 0.0, "avg_price": 0.0})
        signed = qty if side == "buy" else -qty
        new_qty = pos["qty"] + signed
        if pos["qty"] == 0 or (pos["qty"] > 0) == (signed > 0):
            total = abs(pos["qty"]) + abs(signed)
            if total > 0:
                pos["avg_price"] = (abs(pos["qty"]) * pos["avg_price"]
                                    + abs(signed) * price) / total
        pos["qty"] = round(new_qty, 8)
        if abs(pos["qty"]) < 1e-9:
            pos["qty"] = 0.0
            pos["avg_price"] = 0.0

    def _tick(self) -> None:
        self._spot += self.market.drift
        self._spot += self._rng.uniform(-self.market.spread, self.market.spread) * 0.1

    def _latency(self) -> None:
        ms = max(0.5, self._rng.gauss(self.market.latency_ms_mean,
                                      self.market.latency_ms_jitter))
        time.sleep(ms / 1000.0)

    @property
    def spot(self) -> float:
        return self._spot
