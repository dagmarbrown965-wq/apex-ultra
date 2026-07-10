"""
APEX ULTRA — Mock Broker (Phase 35)

A deterministic, fault-injectable broker used for DEMO validation. It models a
simple bid/ask market with configurable latency, spread, and slippage, and can
be driven into specific failure modes (timeout, rejection, partial fill,
disconnect mid-order) so the validation layer can prove it recovers.

Swap this out for the real DEMO adapter once it implements BrokerConnection.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional

from .broker_interface import (
    BaseBroker,
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


@dataclass
class FaultConfig:
    """One-shot or probabilistic fault injection."""
    timeout_next: bool = False          # next order times out
    reject_next: bool = False           # next order is rejected
    reject_reason: str = "insufficient_margin"
    partial_fill_next: bool = False     # next order only partially fills
    partial_fill_ratio: float = 0.5
    disconnect_during_next: bool = False  # drop connection mid-order
    drop_on_next_ping: bool = False     # heartbeat discovers a dead link


@dataclass
class MarketConfig:
    mid: float = 100.0
    spread: float = 0.04                # absolute bid/ask spread
    drift: float = 0.0                  # per-tick mid drift
    extra_slippage_bps: float = 1.5     # mean adverse slippage beyond half-spread
    latency_ms_mean: float = 8.0
    latency_ms_jitter: float = 4.0


class MockBroker(BaseBroker):
    def __init__(
        self,
        symbol: str = "APEX",
        market: Optional[MarketConfig] = None,
        seed: int = 35,
    ) -> None:
        self.symbol = symbol
        self.market = market or MarketConfig()
        self.faults = FaultConfig()
        self._rng = random.Random(seed)
        self._state = ConnectionState.DISCONNECTED
        self._positions: dict[str, Position] = {}
        self._mid = self.market.mid

    # ------------------------------------------------------------------ #
    # Connection lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        self._state = ConnectionState.CONNECTING
        self._sleep_latency()
        self._state = ConnectionState.CONNECTED

    def disconnect(self) -> None:
        self._state = ConnectionState.DISCONNECTED

    def force_drop(self) -> None:
        """Simulate an unexpected link loss (not a clean disconnect)."""
        self._state = ConnectionState.DISCONNECTED

    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED

    @property
    def current_mid(self) -> float:
        return self._mid

    def ping(self) -> float:
        if self.faults.drop_on_next_ping:
            self.faults.drop_on_next_ping = False
            self.force_drop()
            raise BrokerDisconnected("heartbeat lost")
        if not self.is_connected():
            raise BrokerDisconnected("ping on closed connection")
        t0 = time.perf_counter()
        self._sleep_latency()
        return (time.perf_counter() - t0) * 1000.0

    # ------------------------------------------------------------------ #
    # Market data
    # ------------------------------------------------------------------ #
    def _tick(self) -> None:
        self._mid += self.market.drift
        # small random walk so repeated quotes are not identical
        self._mid += self._rng.uniform(-self.market.spread, self.market.spread) * 0.1

    def get_quote(self, symbol: str) -> Quote:
        if not self.is_connected():
            raise BrokerDisconnected("quote on closed connection")
        self._tick()
        half = self.market.spread / 2.0
        return Quote(symbol=symbol, bid=self._mid - half, ask=self._mid + half)

    # ------------------------------------------------------------------ #
    # Order submission (the heart of fault injection)
    # ------------------------------------------------------------------ #
    def submit_order(self, order: Order, timeout: float = 5.0) -> OrderResult:
        if not self.is_connected():
            raise BrokerDisconnected("submit on closed connection")

        quote = self.get_quote(order.symbol)
        order.submitted_ts = time.time()
        order.status = OrderStatus.SUBMITTED

        # --- timeout fault ------------------------------------------------
        if self.faults.timeout_next:
            self.faults.timeout_next = False
            # simulate a stalled broker: sleep past the deadline, then raise
            time.sleep(min(0.02, timeout))  # bounded so the suite stays fast
            order.status = OrderStatus.TIMED_OUT
            order.last_update_ts = time.time()
            raise BrokerTimeout(f"no fill ack within {timeout}s")

        # --- rejection fault ---------------------------------------------
        if self.faults.reject_next:
            self.faults.reject_next = False
            order.status = OrderStatus.REJECTED
            order.last_update_ts = time.time()
            raise OrderRejected(self.faults.reject_reason)

        # --- disconnect mid-order ----------------------------------------
        if self.faults.disconnect_during_next:
            self.faults.disconnect_during_next = False
            self._sleep_latency()
            self.force_drop()
            order.last_update_ts = time.time()
            raise BrokerDisconnected("link dropped before fill ack")

        # --- normal / partial fill ---------------------------------------
        self._sleep_latency()
        fill_qty = order.qty
        if self.faults.partial_fill_next:
            self.faults.partial_fill_next = False
            fill_qty = round(order.qty * self.faults.partial_fill_ratio, 8)

        fill_price = self._fill_price(order.side, quote)
        fill = Fill(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            qty=fill_qty,
            price=fill_price,
        )
        order.filled_qty = fill_qty
        order.avg_fill_price = fill_price
        order.status = (
            OrderStatus.FILLED
            if abs(fill_qty - order.qty) < 1e-9
            else OrderStatus.PARTIALLY_FILLED
        )
        order.last_update_ts = time.time()
        self._apply_fill(fill)
        return OrderResult(order=order, fills=[fill], quote_at_submit=quote)

    # ------------------------------------------------------------------ #
    # Positions
    # ------------------------------------------------------------------ #
    def get_position(self, symbol: str) -> Position:
        return self._positions.get(symbol, Position(symbol=symbol))

    def _apply_fill(self, fill: Fill) -> None:
        pos = self._positions.setdefault(fill.symbol, Position(symbol=fill.symbol))
        signed = fill.qty if fill.side == OrderSide.BUY else -fill.qty
        new_qty = pos.qty + signed
        if pos.qty == 0 or (pos.qty > 0) == (signed > 0):
            # opening or adding in same direction -> blend avg price
            total = abs(pos.qty) + abs(signed)
            if total > 0:
                pos.avg_price = (
                    abs(pos.qty) * pos.avg_price + abs(signed) * fill.price
                ) / total
        # reducing / closing keeps existing avg_price until flat
        pos.qty = round(new_qty, 8)
        if abs(pos.qty) < 1e-9:
            pos.qty = 0.0
            pos.avg_price = 0.0

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _fill_price(self, side: OrderSide, quote: Quote) -> float:
        # cross the spread, then add adverse slippage
        base = quote.ask if side == OrderSide.BUY else quote.bid
        slip = abs(self._rng.gauss(self.market.extra_slippage_bps, 0.6)) / 1e4
        slip_amt = base * slip
        return base + slip_amt if side == OrderSide.BUY else base - slip_amt

    def _sleep_latency(self) -> None:
        ms = max(
            0.5,
            self._rng.gauss(self.market.latency_ms_mean, self.market.latency_ms_jitter),
        )
        time.sleep(ms / 1000.0)
