"""APEX ULTRA broker infrastructure (Phase 35)."""

from .broker_interface import (
    BaseBroker,
    BrokerConnection,
    BrokerDisconnected,
    BrokerError,
    BrokerTimeout,
    ConnectionState,
    Fill,
    Order,
    OrderRejected,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Quote,
)
from .connection_monitor import ConnectionMonitor, MonitorSnapshot
from .mock_broker import FaultConfig, MarketConfig, MockBroker
from .demo_broker_adapter import ALPACA_PAPER, DemoBrokerAdapter, EndpointSpec
from .safety import (
    BrokerConfigError,
    ConnectionSafety,
    LiveTradingDisabled,
    allow_live_enabled,
    assert_demo_endpoint,
)
from .transport import (
    BrokerTransport,
    RealHttpTransport,
    SimulatedBrokerTransport,
    TransportConnectionError,
    TransportError,
    TransportTimeout,
)

__all__ = [
    "BaseBroker",
    "BrokerConnection",
    "BrokerDisconnected",
    "BrokerError",
    "BrokerTimeout",
    "ConnectionState",
    "Fill",
    "Order",
    "OrderRejected",
    "OrderResult",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Position",
    "Quote",
    "ConnectionMonitor",
    "MonitorSnapshot",
    "FaultConfig",
    "MarketConfig",
    "MockBroker",
    "ALPACA_PAPER",
    "DemoBrokerAdapter",
    "EndpointSpec",
    "BrokerConfigError",
    "ConnectionSafety",
    "LiveTradingDisabled",
    "allow_live_enabled",
    "assert_demo_endpoint",
    "BrokerTransport",
    "RealHttpTransport",
    "SimulatedBrokerTransport",
    "TransportConnectionError",
    "TransportError",
    "TransportTimeout",
]
