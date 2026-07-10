"""
APEX ULTRA — Demo Broker Adapter (Phase 37)

A real, transport-backed broker adapter that replaces MockBroker as the
execution target. It implements the requested API:

  connect() | disconnect() | getBalance() | getPositions() |
  submitOrder() | closePosition() | getOrderStatus() | heartbeat()

...and satisfies the Phase 35 BrokerConnection contract (is_connected, ping,
get_quote, submit_order, get_position) so the existing validation harness and
the Phase 36 burn-in controller run against it unmodified.

Safety: constructed DEMO-only. ALLOW_LIVE defaults false; live order capability
is structurally disabled regardless of the flag in this phase.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .broker_interface import (
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
from .safety import (
    ConnectionSafety,
    LiveTradingDisabled,
    allow_live_enabled,
    assert_demo_endpoint,
    endpoint_looks_live,
)
from .transport import (
    BrokerTransport,
    SimulatedBrokerTransport,
    TransportConnectionError,
    TransportTimeout,
)


@dataclass
class EndpointSpec:
    """Maps logical operations to REST paths. Swap per broker (the defaults
    below match the SimulatedBrokerTransport and generic REST brokers)."""
    name: str = "GENERIC_DEMO"
    account: str = "/account"
    positions: str = "/positions"
    position: str = "/positions/{symbol}"
    orders: str = "/orders"
    order: str = "/orders/{id}"
    close_position: str = "/positions/{symbol}"
    quote: str = "/quote"
    heartbeat: str = "/heartbeat"
    is_demo: bool = True


# A ready vendor example (Alpaca paper-trading style) for going live later.
ALPACA_PAPER = EndpointSpec(
    name="ALPACA_PAPER",
    account="/v2/account",
    positions="/v2/positions",
    position="/v2/positions/{symbol}",
    orders="/v2/orders",
    order="/v2/orders/{id}",
    close_position="/v2/positions/{symbol}",
    quote="/v2/quote",
    heartbeat="/v2/clock",
    is_demo=True,
)


class DemoBrokerAdapter:
    def __init__(
        self,
        symbol: str = "APEX",
        base_url: str = "https://demo.simulated.local",
        spec: Optional[EndpointSpec] = None,
        transport: Optional[BrokerTransport] = None,
        allow_live: bool = False,
    ) -> None:
        self.symbol = symbol
        self.base_url = base_url
        self.spec = spec or EndpointSpec()
        self._allow_live = allow_live or allow_live_enabled()

        # DEMO-only enforcement at construction time
        assert_demo_endpoint(base_url, self.spec.is_demo)
        self._live_endpoint = endpoint_looks_live(base_url)

        # default to the in-process simulator when no real transport is supplied
        if transport is None:
            transport = SimulatedBrokerTransport(symbol=symbol)
        self.transport = transport
        # expose fault injection whenever the transport is a simulator
        self._sim = transport if isinstance(transport, SimulatedBrokerTransport) else None

        self.safety = ConnectionSafety()
        self._cached_mid: float = 100.0

    # ================================================================== #
    # Requested API
    # ================================================================== #
    def connect(self) -> None:
        reconnecting = self.safety.state in (
            ConnectionState.DISCONNECTED, ConnectionState.RECONNECTING)
        if self._sim is not None:
            self._sim.restore()  # clear any simulated link drop
        try:
            resp = self.transport.request("GET", self.spec.heartbeat, timeout=5.0)
        except (TransportConnectionError, TransportTimeout) as e:
            self.safety.on_disconnected()
            raise BrokerDisconnected(f"connect failed: {e}") from e
        if resp.status_code >= 400:
            self.safety.on_disconnected()
            raise BrokerDisconnected(f"connect rejected: {resp.status_code}")
        if reconnecting and self.safety.reconnect_attempts:
            self.safety.on_reconnect_success()
        else:
            self.safety.on_connected()
        self.safety.on_heartbeat(resp.elapsed_ms)

    def disconnect(self) -> None:
        self.safety.on_disconnected()
        self.safety.state = ConnectionState.DISCONNECTED

    def heartbeat(self) -> float:
        """Returns latency in ms. Marks the link down on failure."""
        try:
            resp = self.transport.request("GET", self.spec.heartbeat, timeout=3.0)
        except (TransportConnectionError, TransportTimeout) as e:
            self.safety.on_disconnected()
            raise BrokerDisconnected(str(e)) from e
        self.safety.on_heartbeat(resp.elapsed_ms)
        return resp.elapsed_ms

    def getBalance(self) -> dict:
        resp = self._call("GET", self.spec.account)
        return {"balance": resp.body.get("balance"),
                "equity": resp.body.get("equity")}

    def getPositions(self) -> list[Position]:
        resp = self._call("GET", self.spec.positions)
        out = []
        for p in resp.body.get("positions", []):
            out.append(Position(p["symbol"], float(p["qty"]),
                                float(p.get("avg_price", 0.0))))
        return out

    def submitOrder(self, order: Order, timeout: float = 5.0) -> OrderResult:
        self._require_demo("submitOrder")
        payload = {
            "symbol": order.symbol,
            "side": order.side.value.lower(),
            "qty": order.qty,
            "type": order.order_type.value.lower(),
        }
        if order.limit_price is not None:
            payload["limit_price"] = order.limit_price

        order.submitted_ts = time.time()
        order.status = OrderStatus.SUBMITTED
        try:
            resp = self._call("POST", self.spec.orders, json=payload, timeout=timeout)
        except BrokerTimeout:
            order.status = OrderStatus.TIMED_OUT
            order.last_update_ts = time.time()
            raise
        except BrokerDisconnected:
            order.last_update_ts = time.time()
            raise

        body = resp.body
        if resp.status_code >= 400 or body.get("status") == "rejected":
            order.status = OrderStatus.REJECTED
            order.last_update_ts = time.time()
            raise OrderRejected(body.get("reason", f"http_{resp.status_code}"))

        order.filled_qty = float(body.get("filled_qty", 0.0))
        order.avg_fill_price = float(body.get("avg_fill_price")) \
            if body.get("avg_fill_price") is not None else None
        order.id = body.get("id", order.id)
        order.status = (OrderStatus.FILLED
                        if abs(order.filled_qty - order.qty) < 1e-9
                        else OrderStatus.PARTIALLY_FILLED)
        order.last_update_ts = time.time()

        fill = Fill(order.id, order.symbol, order.side,
                    order.filled_qty, order.avg_fill_price or 0.0)
        bid, ask = body.get("bid"), body.get("ask")
        quote = (Quote(order.symbol, float(bid), float(ask))
                 if bid is not None and ask is not None else None)
        if quote:
            self._cached_mid = quote.mid
        return OrderResult(order=order, fills=[fill], quote_at_submit=quote)

    def closePosition(self, symbol: str, timeout: float = 5.0) -> dict:
        self._require_demo("closePosition")
        path = self.spec.close_position.format(symbol=symbol)
        resp = self._call("DELETE", path, timeout=timeout)
        return resp.body

    def getOrderStatus(self, order_id: str) -> dict:
        path = self.spec.order.format(id=order_id)
        resp = self._call("GET", path)
        return resp.body

    # ================================================================== #
    # Phase 35 BrokerConnection contract (aliases / bridges)
    # ================================================================== #
    def is_connected(self) -> bool:
        return self.safety.state == ConnectionState.CONNECTED

    def ping(self) -> float:
        return self.heartbeat()

    def get_quote(self, symbol: str) -> Quote:
        resp = self._call("GET", self.spec.quote, params={"symbol": symbol})
        q = Quote(symbol, float(resp.body["bid"]), float(resp.body["ask"]))
        self._cached_mid = q.mid
        return q

    def submit_order(self, order: Order, timeout: float = 5.0) -> OrderResult:
        return self.submitOrder(order, timeout=timeout)

    def get_position(self, symbol: str) -> Position:
        path = self.spec.position.format(symbol=symbol)
        resp = self._call("GET", path)
        b = resp.body
        return Position(symbol, float(b.get("qty", 0.0)),
                        float(b.get("avg_price", 0.0)))

    @property
    def current_mid(self) -> float:
        try:
            return self.get_quote(self.symbol).mid
        except Exception:
            return self._cached_mid

    # ================================================================== #
    # Fault-injection surface (only meaningful with simulated transport).
    # Lets the EXISTING Phase 35 FailureTester drive the adapter unmodified.
    # ================================================================== #
    @property
    def faults(self):
        if self._sim is None:
            raise RuntimeError("fault injection unavailable on a real transport")
        return self._sim.faults

    def force_drop(self) -> None:
        if self._sim is not None:
            self._sim.force_drop()
        self.safety.on_disconnected()

    # ================================================================== #
    # Internals
    # ================================================================== #
    def _require_demo(self, op: str) -> None:
        # Phase 37: live order capability is structurally disabled.
        # A live endpoint can never accept an order here, even if ALLOW_LIVE
        # relaxed the construction guard.
        if self._live_endpoint or not self.spec.is_demo:
            raise LiveTradingDisabled(
                f"{op} blocked: live order capability disabled in Phase 37")

    def _call(self, method: str, path: str, *, params=None, json=None,
              timeout: float = 5.0):
        try:
            resp = self.transport.request(method, path, params=params,
                                          json=json, timeout=timeout)
        except TransportTimeout as e:
            raise BrokerTimeout(str(e)) from e
        except TransportConnectionError as e:
            self.safety.on_disconnected()
            raise BrokerDisconnected(str(e)) from e
        # any successful round-trip is a sign of life
        self.safety.on_heartbeat(resp.elapsed_ms)
        return resp
