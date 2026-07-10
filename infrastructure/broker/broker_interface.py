"""
APEX ULTRA — Broker Interface (Phase 35)

Defines the contract every broker adapter must satisfy, plus the data models
that flow through the order lifecycle. The real DEMO broker adapter and the
mock broker both implement `BrokerConnection`, so the validation layer can run
identically against either.

This module is pure infrastructure: it does NOT contain strategy, indicator,
signal-generation, or UI logic.
"""

from __future__ import annotations

import abc
import itertools
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol, runtime_checkable


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"            # created locally, not yet sent
    SUBMITTED = "SUBMITTED"        # acknowledged by broker
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class ConnectionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"


# --------------------------------------------------------------------------- #
# Exceptions (broker-side faults the validation layer must survive)
# --------------------------------------------------------------------------- #
class BrokerError(Exception):
    """Base class for all broker faults."""


class BrokerTimeout(BrokerError):
    """Broker did not respond within the deadline."""


class OrderRejected(BrokerError):
    """Broker actively rejected the order (margin, symbol, sizing, etc.)."""

    def __init__(self, reason: str = "rejected"):
        super().__init__(reason)
        self.reason = reason


class BrokerDisconnected(BrokerError):
    """Connection dropped mid-operation."""


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
_order_seq = itertools.count(1)


@dataclass
class Order:
    symbol: str
    side: OrderSide
    qty: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    # expected_price is the reference price the signal/strategy assumed when the
    # order was created. It is the baseline for slippage measurement.
    expected_price: Optional[float] = None

    id: str = field(default_factory=lambda: f"APX-{next(_order_seq):06d}")
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    avg_fill_price: Optional[float] = None

    created_ts: float = field(default_factory=time.time)
    submitted_ts: Optional[float] = None
    last_update_ts: Optional[float] = None

    @property
    def remaining_qty(self) -> float:
        return max(0.0, self.qty - self.filled_qty)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            OrderStatus.FILLED,
            OrderStatus.REJECTED,
            OrderStatus.CANCELLED,
            OrderStatus.TIMED_OUT,
        )


@dataclass
class Fill:
    order_id: str
    symbol: str
    side: OrderSide
    qty: float
    price: float
    ts: float = field(default_factory=time.time)


@dataclass
class Position:
    symbol: str
    qty: float = 0.0          # signed: positive = long, negative = short
    avg_price: float = 0.0

    @property
    def is_flat(self) -> bool:
        return abs(self.qty) < 1e-9


@dataclass
class Quote:
    symbol: str
    bid: float
    ask: float
    ts: float = field(default_factory=time.time)

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        return self.ask - self.bid


@dataclass
class OrderResult:
    """Returned by submit_order. Carries the resulting order + its fills."""
    order: Order
    fills: list[Fill] = field(default_factory=list)
    quote_at_submit: Optional[Quote] = None


# --------------------------------------------------------------------------- #
# Broker contract
# --------------------------------------------------------------------------- #
@runtime_checkable
class BrokerConnection(Protocol):
    """
    Minimal surface the validation layer depends on. Any real DEMO adapter
    only needs to implement these methods to be drop-in compatible.
    """

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    def ping(self) -> float:
        """Round-trip heartbeat. Returns measured latency in milliseconds."""
        ...

    def get_quote(self, symbol: str) -> Quote: ...
    def submit_order(self, order: Order, timeout: float = 5.0) -> OrderResult: ...
    def get_position(self, symbol: str) -> Position: ...


class BaseBroker(abc.ABC):
    """Optional ABC for adapters that prefer inheritance over the Protocol."""

    @abc.abstractmethod
    def connect(self) -> None: ...

    @abc.abstractmethod
    def disconnect(self) -> None: ...

    @abc.abstractmethod
    def is_connected(self) -> bool: ...

    @abc.abstractmethod
    def ping(self) -> float: ...

    @abc.abstractmethod
    def get_quote(self, symbol: str) -> Quote: ...

    @abc.abstractmethod
    def submit_order(self, order: Order, timeout: float = 5.0) -> OrderResult: ...

    @abc.abstractmethod
    def get_position(self, symbol: str) -> Position: ...
