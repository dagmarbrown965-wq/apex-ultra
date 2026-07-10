"""
APEX ULTRA — Deriv DEMO Adapter (Phase 38)

Replaces the generic endpoint spec with Deriv's WebSocket protocol while keeping
the Phase 35 BrokerConnection contract, so the existing lifecycle/failure tests
and the Phase 36 burn-in controller run against it unmodified.

Implements:
  1. Deriv authentication (authorize token)
  2. WebSocket connection
  3. Account balance retrieval
  4. Price subscription (ticks)
  5. Buy request (proposal -> buy)
  6. Sell/close request (sell contract)
  7. Contract/order status tracking (proposal_open_contract)
  8. Heartbeat monitoring (ping/pong)

Safety: DEMO ONLY. LIVE_TRADING defaults false. Real (non-virtual) accounts are
blocked outright, and real order capability is disabled regardless of the flag.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from ..broker_interface import (
    BrokerDisconnected,
    BrokerTimeout,
    ConnectionState,
    Fill,
    Order,
    OrderRejected,
    OrderResult,
    OrderSide,
    OrderStatus,
    Position,
    Quote,
)
from ..safety import ConnectionSafety
from .deriv_transport import (
    DEFAULT_WS_URL,
    DerivConnectionError,
    DerivSimulatedTransport,
    DerivTimeout,
    DerivTransport,
)


class DerivRealAccountBlocked(Exception):
    """Refused because the authorized account is a real (non-virtual) account."""


def live_trading_enabled() -> bool:
    """LIVE_TRADING flag. Defaults false. Even when true, real order capability
    stays disabled in Phase 38."""
    return os.environ.get("LIVE_TRADING", "false").strip().lower() == "true"


@dataclass
class DerivConfig:
    app_id: str = "1089"               # Deriv's public demo app_id
    api_token: str = "DEMO-TOKEN"
    ws_url: str = DEFAULT_WS_URL
    symbol: str = "R_100"              # Volatility 100 Index (24/7 on demo)
    currency: str = "USD"
    contract_type_buy: str = "MULTUP"
    contract_type_sell: str = "MULTDOWN"


class DerivDemoAdapter:
    def __init__(
        self,
        config: Optional[DerivConfig] = None,
        transport: Optional[DerivTransport] = None,
    ) -> None:
        self.config = config or DerivConfig()
        self.symbol = self.config.symbol

        if transport is None:
            transport = DerivSimulatedTransport(symbol=self.symbol)
        self.transport = transport
        self._sim = transport if isinstance(transport, DerivSimulatedTransport) else None

        self.safety = ConnectionSafety()
        self._is_virtual: Optional[bool] = None
        self._loginid: Optional[str] = None
        self._cached_mid: float = 1000.0
        self._open_contracts: dict[str, str] = {}  # symbol -> last contract_id

    # ================================================================== #
    # 1-2. Authentication + WebSocket connection
    # ================================================================== #
    def connect(self) -> None:
        reconnecting = self.safety.state in (
            ConnectionState.DISCONNECTED, ConnectionState.RECONNECTING)
        try:
            self.transport.connect()
            auth = self._call({"authorize": self.config.api_token})
        except (DerivConnectionError, DerivTimeout) as e:
            self.safety.on_disconnected()
            raise BrokerDisconnected(f"deriv connect failed: {e}") from e

        if "error" in auth:
            self.safety.on_disconnected()
            raise BrokerDisconnected(f"authorize error: {auth['error'].get('message')}")

        acct = auth["authorize"]
        self._is_virtual = bool(acct.get("is_virtual", 0))
        self._loginid = acct.get("loginid")

        # --- SAFETY: block real accounts ---------------------------------
        if not self._is_virtual:
            self.safety.on_disconnected()
            if not live_trading_enabled():
                raise DerivRealAccountBlocked(
                    f"account {self._loginid} is REAL; refusing "
                    "(LIVE_TRADING is false, DEMO ONLY)")
            # even with the flag on, Phase 38 has no real trading capability
            raise DerivRealAccountBlocked(
                f"account {self._loginid} is REAL; real trading disabled in Phase 38")

        if reconnecting and self.safety.reconnect_attempts:
            self.safety.on_reconnect_success()
        else:
            self.safety.on_connected()
        self.heartbeat()

    def disconnect(self) -> None:
        try:
            self.transport.close()
        finally:
            self.safety.on_disconnected()
            self.safety.state = ConnectionState.DISCONNECTED

    # ================================================================== #
    # 8. Heartbeat
    # ================================================================== #
    def heartbeat(self) -> float:
        t0 = time.perf_counter()
        try:
            resp = self._call({"ping": 1})
        except (DerivConnectionError, DerivTimeout) as e:
            self.safety.on_disconnected()
            raise BrokerDisconnected(str(e)) from e
        latency = (time.perf_counter() - t0) * 1000.0
        if resp.get("ping") != "pong":
            raise BrokerDisconnected("bad heartbeat response")
        self.safety.on_heartbeat(latency)
        return latency

    # ================================================================== #
    # 3. Account balance
    # ================================================================== #
    def getBalance(self) -> dict:
        self._require_virtual("getBalance")
        resp = self._call({"balance": 1})
        b = resp.get("balance", {})
        return {"balance": b.get("balance"), "currency": b.get("currency"),
                "loginid": b.get("loginid"), "equity": b.get("balance")}

    # ================================================================== #
    # 4. Price subscription / quote
    # ================================================================== #
    def subscribePrice(self, symbol: Optional[str] = None) -> Quote:
        return self.get_quote(symbol or self.symbol)

    def stream_ticks(self, count: int = 5, timeout: float = 5.0) -> list[tuple]:
        """Subscribe to live ticks and read `count` frames, returning
        (tick, latency_ms) pairs. Used by the smoke test for live market data."""
        self.transport.send({"ticks": self.symbol, "subscribe": 1})
        out: list[tuple] = []
        for _ in range(count):
            t0 = time.perf_counter()
            try:
                frame = self.transport.recv(timeout)
            except (DerivConnectionError, DerivTimeout) as e:
                self.safety.on_disconnected()
                raise BrokerDisconnected(str(e)) from e
            lat = (time.perf_counter() - t0) * 1000.0
            tick = frame.get("tick")
            if tick:
                bid = float(tick.get("bid", tick["quote"]))
                ask = float(tick.get("ask", tick["quote"]))
                self._cached_mid = (bid + ask) / 2.0
                self.safety.on_heartbeat(lat)
                out.append((tick, lat))
        return out

    def get_quote(self, symbol: str) -> Quote:
        resp = self._call({"ticks": symbol, "subscribe": 1})
        if "error" in resp:
            raise BrokerDisconnected(resp["error"].get("message", "tick error"))
        t = resp["tick"]
        half = self.config_spread() / 2.0
        bid = float(t.get("bid", t["quote"] - half))
        ask = float(t.get("ask", t["quote"] + half))
        q = Quote(symbol, bid, ask)
        self._cached_mid = q.mid
        return q

    def config_spread(self) -> float:
        return self._sim.market.spread if self._sim else 0.4

    # ================================================================== #
    # 5-6. Buy / Sell-close
    # ================================================================== #
    def submitOrder(self, order: Order, timeout: float = 5.0) -> OrderResult:
        self._require_virtual("submitOrder")
        order.submitted_ts = time.time()
        order.status = OrderStatus.SUBMITTED

        # SELL that reduces an existing long -> close the open contract
        if order.side == OrderSide.SELL and self.symbol in self._open_contracts:
            return self._close_contract(order)

        # otherwise open a new contract (BUY=long, SELL=short)
        ctype = (self.config.contract_type_buy if order.side == OrderSide.BUY
                 else self.config.contract_type_sell)
        try:
            prop = self._call({
                "proposal": 1, "amount": order.qty, "basis": "stake",
                "contract_type": ctype, "symbol": order.symbol,
                "currency": self.config.currency, "multiplier": 100,
            }, timeout=timeout)
            if "error" in prop:
                order.status = OrderStatus.REJECTED
                raise OrderRejected(prop["error"].get("message", "proposal error"))

            buy = self._call({"buy": prop["proposal"]["id"],
                              "price": prop["proposal"]["ask_price"]}, timeout=timeout)
        except BrokerTimeout:
            order.status = OrderStatus.TIMED_OUT
            order.last_update_ts = time.time()
            raise
        except BrokerDisconnected:
            order.last_update_ts = time.time()
            raise

        if "error" in buy:
            order.status = OrderStatus.REJECTED
            order.last_update_ts = time.time()
            raise OrderRejected(buy["error"].get("message", "buy error"))

        b = buy["buy"]
        cid = b["contract_id"]
        self._open_contracts[order.symbol] = cid
        fill_price = float(b["buy_price"])
        filled = float(b.get("filled_amount", order.qty))

        order.id = str(cid)
        order.filled_qty = filled
        order.avg_fill_price = fill_price
        order.status = (OrderStatus.FILLED if abs(filled - order.qty) < 1e-9
                        else OrderStatus.PARTIALLY_FILLED)
        order.last_update_ts = time.time()

        half = self.config_spread() / 2.0
        quote = Quote(order.symbol, fill_price - half, fill_price + half)
        self._cached_mid = quote.mid
        fill = Fill(order.id, order.symbol, order.side, filled, fill_price)
        return OrderResult(order=order, fills=[fill], quote_at_submit=quote)

    def closePosition(self, symbol: str, timeout: float = 5.0) -> dict:
        self._require_virtual("closePosition")
        cid = self._open_contracts.get(symbol)
        if not cid:
            return {"symbol": symbol, "closed": False, "reason": "no open contract"}
        resp = self._call({"sell": cid, "price": 0}, timeout=timeout)
        if "error" in resp:
            raise OrderRejected(resp["error"].get("message", "sell error"))
        self._open_contracts.pop(symbol, None)
        sell = resp["sell"]
        return {"symbol": symbol, "closed": True,
                "sold_for": sell.get("sold_for"),
                "profit": sell.get("profit"),
                "balance_after": sell.get("balance_after"),
                "contract_id": cid}

    def _close_contract(self, order: Order) -> OrderResult:
        cid = self._open_contracts.get(self.symbol)
        resp = self._call({"sell": cid, "price": 0})
        if "error" in resp:
            order.status = OrderStatus.REJECTED
            raise OrderRejected(resp["error"].get("message", "sell error"))
        self._open_contracts.pop(self.symbol, None)
        sold_for = float(resp["sell"]["sold_for"])
        order.id = str(cid)
        order.filled_qty = order.qty
        order.avg_fill_price = sold_for
        order.status = OrderStatus.FILLED
        order.last_update_ts = time.time()
        half = self.config_spread() / 2.0
        quote = Quote(order.symbol, sold_for - half, sold_for + half)
        fill = Fill(order.id, order.symbol, order.side, order.qty, sold_for)
        return OrderResult(order=order, fills=[fill], quote_at_submit=quote)

    # ================================================================== #
    # 7. Contract / order status
    # ================================================================== #
    def getOrderStatus(self, contract_id: str) -> dict:
        resp = self._call({"proposal_open_contract": {"contract_id": contract_id}})
        if "error" in resp:
            return {"contract_id": contract_id, "error": resp["error"]}
        return resp["proposal_open_contract"]

    # ================================================================== #
    # Instrument confirmation + intent-based execution (Phase 39.1)
    # ================================================================== #
    def contracts_for(self, symbol: Optional[str] = None) -> dict:
        """Deriv contracts_for: contract types available for a symbol."""
        resp = self._call({"contracts_for": symbol or self.symbol,
                           "currency": self.config.currency})
        if "error" in resp:
            raise BrokerDisconnected(resp["error"].get("message", "contracts_for error"))
        return resp.get("contracts_for", {})

    def confirm_contract(self, spec) -> tuple[bool, list[str], list[str]]:
        """Confirm the spec's candidate contract types are available for the
        symbol. Returns (ok, available_types, issues)."""
        issues: list[str] = []
        try:
            cf = self.contracts_for(self.symbol)
        except Exception as e:
            return False, [], [f"contracts_for failed: {e}"]
        available = [c.get("contract_type") for c in cf.get("available", [])]
        if spec.contract_type_buy not in available:
            issues.append(f"{spec.contract_type_buy} not available for {self.symbol}")
        if spec.contract_type_sell not in available:
            issues.append(f"{spec.contract_type_sell} not available for {self.symbol}")
        return (len(issues) == 0, available, issues)

    def submit_intent(self, intent, spec, timeout: float = 5.0) -> OrderResult:
        """Execute an ApexOrderIntent (side/size/SL/TP) via proposal->buy using
        the confirmed contract spec, mapping limit_order for SL/TP."""
        from .execution_mapping import map_intent_to_proposal
        self._require_virtual("submit_intent")

        order = Order(intent.symbol, intent.side, intent.size,
                      expected_price=self._cached_mid)
        order.submitted_ts = time.time()
        order.status = OrderStatus.SUBMITTED

        req = map_intent_to_proposal(intent, spec, self.config.currency)
        try:
            prop = self._call(req, timeout=timeout)
            if "error" in prop:
                order.status = OrderStatus.REJECTED
                raise OrderRejected(prop["error"].get("message", "proposal error"))
            buy = self._call({"buy": prop["proposal"]["id"],
                              "price": prop["proposal"]["ask_price"]}, timeout=timeout)
        except BrokerTimeout:
            order.status = OrderStatus.TIMED_OUT
            order.last_update_ts = time.time()
            raise
        if "error" in buy:
            order.status = OrderStatus.REJECTED
            order.last_update_ts = time.time()
            raise OrderRejected(buy["error"].get("message", "buy error"))

        b = buy["buy"]
        cid = b["contract_id"]
        self._open_contracts[intent.symbol] = cid
        fill_price = float(b["buy_price"])
        filled = float(b.get("filled_amount", intent.size))
        order.id = str(cid)
        order.filled_qty = filled
        order.avg_fill_price = fill_price
        order.status = (OrderStatus.FILLED if abs(filled - intent.size) < 1e-9
                        else OrderStatus.PARTIALLY_FILLED)
        order.last_update_ts = time.time()
        half = self.config_spread() / 2.0
        quote = Quote(intent.symbol, fill_price - half, fill_price + half)
        self._cached_mid = quote.mid
        fill = Fill(order.id, intent.symbol, intent.side, filled, fill_price)
        return OrderResult(order=order, fills=[fill], quote_at_submit=quote)

    # ================================================================== #
    # Phase 35 BrokerConnection contract bridges
    # ================================================================== #
    def is_connected(self) -> bool:
        return self.safety.state == ConnectionState.CONNECTED

    def ping(self) -> float:
        return self.heartbeat()

    def submit_order(self, order: Order, timeout: float = 5.0) -> OrderResult:
        return self.submitOrder(order, timeout=timeout)

    def get_position(self, symbol: str) -> Position:
        if self._sim is not None:
            p = self._sim.positions.get(symbol, {"qty": 0.0, "avg_price": 0.0})
            return Position(symbol, float(p["qty"]), float(p["avg_price"]))
        # real mode: derive from open contract tracking (qty granularity only)
        return Position(symbol, 0.0, 0.0)

    @property
    def current_mid(self) -> float:
        try:
            return self.get_quote(self.symbol).mid
        except Exception:
            return self._cached_mid

    # ================================================================== #
    # Fault-injection surface (simulated transport only)
    # ================================================================== #
    @property
    def faults(self):
        if self._sim is None:
            raise RuntimeError("fault injection unavailable on the live transport")
        return self._sim.faults

    def force_drop(self) -> None:
        if self._sim is not None:
            self._sim.force_drop()
        self.safety.on_disconnected()

    # ================================================================== #
    # Internals
    # ================================================================== #
    def _require_virtual(self, op: str) -> None:
        if self._is_virtual is False:
            raise DerivRealAccountBlocked(
                f"{op} blocked: real account, DEMO ONLY in Phase 38")

    def _call(self, request: dict, timeout: float = 5.0) -> dict:
        try:
            resp = self.transport.call(request, timeout=timeout)
        except DerivTimeout as e:
            raise BrokerTimeout(str(e)) from e
        except DerivConnectionError as e:
            self.safety.on_disconnected()
            raise BrokerDisconnected(str(e)) from e
        self.safety.on_heartbeat(self.safety.last_latency_ms or 0.0)
        return resp
