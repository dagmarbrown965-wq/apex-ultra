"""
APEX ULTRA — Broker Transport Layer (Phase 37)

Separates the adapter's logic from the network. The adapter talks to a
`BrokerTransport`; in production that is `RealHttpTransport` (urllib + auth
headers), in validation it is `SimulatedBrokerTransport` (an in-process REST
simulator with fault injection). This lets the adapter's request-building,
response-parsing, and reconnect logic be tested with zero network dependency.
"""

from __future__ import annotations

import json as _json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from .mock_broker import FaultConfig, MarketConfig


class TransportError(Exception):
    """Base transport failure."""


class TransportTimeout(TransportError):
    """Request exceeded its deadline."""


class TransportConnectionError(TransportError):
    """Socket/link failure (broker unreachable)."""


@dataclass
class TransportResponse:
    status_code: int
    body: dict[str, Any]
    elapsed_ms: float


class BrokerTransport(Protocol):
    def request(self, method: str, path: str, *,
                params: Optional[dict] = None,
                json: Optional[dict] = None,
                timeout: float = 5.0) -> TransportResponse: ...


# --------------------------------------------------------------------------- #
# Real transport (used in production; not exercised in the offline harness)
# --------------------------------------------------------------------------- #
class RealHttpTransport:
    def __init__(self, base_url: str, headers: Optional[dict] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}

    def request(self, method: str, path: str, *, params=None, json=None,
                timeout: float = 5.0) -> TransportResponse:
        url = f"{self.base_url}{path}"
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"
        data = _json.dumps(json).encode() if json is not None else None
        req = urllib.request.Request(url, data=data, method=method.upper())
        req.add_header("Content-Type", "application/json")
        for k, v in self.headers.items():
            req.add_header(k, v)
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode() or "{}"
                elapsed = (time.perf_counter() - t0) * 1000.0
                return TransportResponse(resp.status, _json.loads(raw), elapsed)
        except urllib.error.HTTPError as e:
            raw = e.read().decode() or "{}"
            elapsed = (time.perf_counter() - t0) * 1000.0
            try:
                body = _json.loads(raw)
            except Exception:
                body = {"message": raw}
            return TransportResponse(e.code, body, elapsed)
        except urllib.error.URLError as e:
            if isinstance(getattr(e, "reason", None), TimeoutError):
                raise TransportTimeout(str(e)) from e
            raise TransportConnectionError(str(e)) from e
        except TimeoutError as e:
            raise TransportTimeout(str(e)) from e


# --------------------------------------------------------------------------- #
# Simulated transport (in-process REST simulator for offline validation)
# --------------------------------------------------------------------------- #
class SimulatedBrokerTransport:
    """Mimics a broker DEMO REST API. Routes by path keyword so it works with
    generic or vendor-style paths (e.g. /account or /v2/account)."""

    def __init__(self, symbol: str = "APEX", starting_balance: float = 100_000.0,
                 market: Optional[MarketConfig] = None, seed: int = 37) -> None:
        self.symbol = symbol
        self.market = market or MarketConfig()
        self.faults = FaultConfig()
        self._rng = random.Random(seed)
        self._mid = self.market.mid
        self._balance = starting_balance
        self._equity = starting_balance
        self._positions: dict[str, dict] = {}
        self._orders: dict[str, dict] = {}
        self._order_seq = 0
        self._dropped = False  # simulated link loss

    # -- link state ----------------------------------------------------- #
    def force_drop(self) -> None:
        self._dropped = True

    def restore(self) -> None:
        self._dropped = False

    # -- routing -------------------------------------------------------- #
    def request(self, method: str, path: str, *, params=None, json=None,
                timeout: float = 5.0) -> TransportResponse:
        if self._dropped:
            raise TransportConnectionError("link down")

        p = path.lower()
        method = method.upper()
        t0 = time.perf_counter()

        if "heartbeat" in p or "clock" in p or "ping" in p:
            self._latency()
            return self._ok({"status": "ok", "ts": time.time()}, t0)
        if "quote" in p:
            return self._handle_quote(params, t0)
        if "account" in p or "balance" in p:
            self._latency()
            return self._ok({"balance": self._balance, "equity": self._equity}, t0)
        if "orders" in p and method == "POST":
            return self._handle_submit(json or {}, timeout, t0)
        if "orders" in p and method == "GET":
            return self._handle_order_status(path, t0)
        if "positions" in p and method == "DELETE":
            return self._handle_close(path, t0)
        if "positions" in p and method == "GET":
            return self._handle_positions(path, t0)

        return self._ok({"message": "not found", "path": path}, t0, status=404)

    # -- handlers ------------------------------------------------------- #
    def _handle_quote(self, params, t0) -> TransportResponse:
        self._tick()
        half = self.market.spread / 2.0
        return self._ok(
            {"symbol": (params or {}).get("symbol", self.symbol),
             "bid": self._mid - half, "ask": self._mid + half,
             "ts": time.time()},
            t0,
        )

    def _handle_submit(self, payload: dict, timeout: float, t0) -> TransportResponse:
        # fault: timeout
        if self.faults.timeout_next:
            self.faults.timeout_next = False
            time.sleep(min(0.02, timeout))
            raise TransportTimeout("no order ack")
        # fault: rejection -> broker NACK (HTTP 4xx)
        if self.faults.reject_next:
            self.faults.reject_next = False
            return self._ok(
                {"status": "rejected", "reason": self.faults.reject_reason},
                t0, status=422,
            )
        # fault: disconnect mid-order
        if self.faults.disconnect_during_next:
            self.faults.disconnect_during_next = False
            self._latency()
            self.force_drop()
            raise TransportConnectionError("dropped before ack")

        self._latency()
        self._order_seq += 1
        oid = f"SRV-{self._order_seq:06d}"
        side = str(payload.get("side", "buy")).lower()
        qty = float(payload.get("qty", 0))
        self._tick()
        half = self.market.spread / 2.0
        base = (self._mid + half) if side == "buy" else (self._mid - half)
        slip = abs(self._rng.gauss(self.market.extra_slippage_bps, 0.6)) / 1e4
        fill_price = base + base * slip if side == "buy" else base - base * slip

        fill_qty = qty
        status = "filled"
        if self.faults.partial_fill_next:
            self.faults.partial_fill_next = False
            fill_qty = round(qty * self.faults.partial_fill_ratio, 8)
            status = "partially_filled"

        self._apply_fill(side, fill_qty, fill_price)
        order = {
            "id": oid, "symbol": payload.get("symbol", self.symbol),
            "side": side, "qty": qty, "filled_qty": fill_qty,
            "avg_fill_price": fill_price, "status": status,
            "bid": self._mid - half, "ask": self._mid + half,
            "ts": time.time(),
        }
        self._orders[oid] = order
        return self._ok(order, t0)

    def _handle_order_status(self, path: str, t0) -> TransportResponse:
        oid = path.rstrip("/").split("/")[-1]
        order = self._orders.get(oid)
        if not order:
            return self._ok({"message": "unknown order", "id": oid}, t0, status=404)
        return self._ok(order, t0)

    def _handle_positions(self, path: str, t0) -> TransportResponse:
        self._latency()
        seg = path.rstrip("/").split("/")[-1]
        if seg.lower() not in ("positions", "v2") and seg in self._positions:
            return self._ok(self._positions[seg], t0)
        if seg.lower() not in ("positions", "v2"):
            return self._ok({"symbol": seg, "qty": 0, "avg_price": 0}, t0)
        return self._ok({"positions": list(self._positions.values())}, t0)

    def _handle_close(self, path: str, t0) -> TransportResponse:
        self._latency()
        sym = path.rstrip("/").split("/")[-1]
        pos = self._positions.get(sym)
        if not pos or abs(pos["qty"]) < 1e-9:
            return self._ok({"symbol": sym, "closed_qty": 0}, t0)
        qty = pos["qty"]
        side = "sell" if qty > 0 else "buy"
        self._tick()
        half = self.market.spread / 2.0
        price = (self._mid - half) if side == "sell" else (self._mid + half)
        self._apply_fill(side, abs(qty), price)
        return self._ok({"symbol": sym, "closed_qty": abs(qty),
                         "price": price, "status": "filled"}, t0)

    # -- internals ------------------------------------------------------ #
    def _apply_fill(self, side: str, qty: float, price: float) -> None:
        pos = self._positions.setdefault(
            self.symbol, {"symbol": self.symbol, "qty": 0.0, "avg_price": 0.0})
        signed = qty if side == "buy" else -qty
        new_qty = pos["qty"] + signed
        if pos["qty"] == 0 or (pos["qty"] > 0) == (signed > 0):
            total = abs(pos["qty"]) + abs(signed)
            if total > 0:
                pos["avg_price"] = (
                    abs(pos["qty"]) * pos["avg_price"] + abs(signed) * price
                ) / total
        pos["qty"] = round(new_qty, 8)
        if abs(pos["qty"]) < 1e-9:
            pos["qty"] = 0.0
            pos["avg_price"] = 0.0

    def _tick(self) -> None:
        self._mid += self.market.drift
        self._mid += self._rng.uniform(-self.market.spread, self.market.spread) * 0.1

    def _latency(self) -> None:
        ms = max(0.5, self._rng.gauss(self.market.latency_ms_mean,
                                      self.market.latency_ms_jitter))
        time.sleep(ms / 1000.0)

    @property
    def mid(self) -> float:
        return self._mid

    def _ok(self, body, t0, status: int = 200) -> TransportResponse:
        return TransportResponse(status, body, (time.perf_counter() - t0) * 1000.0)
