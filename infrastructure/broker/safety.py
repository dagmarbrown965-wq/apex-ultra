"""
APEX ULTRA — Broker Safety Layer (Phase 37)

Two responsibilities:

1. ConnectionSafety: live tracking of connection state, latency, last
   heartbeat, reconnect attempts, and cumulative disconnect duration.

2. DEMO-only enforcement: the adapter refuses to operate against a live
   endpoint. ALLOW_LIVE defaults to false and live order capability is
   structurally disabled in this phase regardless of the flag.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

from .broker_interface import ConnectionState


class BrokerConfigError(Exception):
    """Invalid / unsafe broker configuration."""


class LiveTradingDisabled(Exception):
    """Attempted a live action while live capability is disabled."""


def allow_live_enabled() -> bool:
    """ALLOW_LIVE flag. Defaults to false. Even when true, live ORDER
    capability remains disabled in Phase 37 (see DemoBrokerAdapter)."""
    return os.environ.get("ALLOW_LIVE", "false").strip().lower() == "true"


def endpoint_looks_live(base_url: str) -> bool:
    """Heuristic: does this URL point at a live trading endpoint?"""
    u = base_url.lower()
    looks_live = any(tok in u for tok in ("api.live", "live.", "/live", "trade-api"))
    looks_demo = any(tok in u for tok in
                     ("paper", "demo", "practice", "sandbox", "test", "localhost",
                      "127.0.0.1", "simulated"))
    return looks_live and not looks_demo


def assert_demo_endpoint(base_url: str, declared_demo: bool) -> None:
    """Block obviously-live endpoints unless explicitly allowed."""
    if not declared_demo:
        raise BrokerConfigError("adapter must be constructed in DEMO mode")
    if endpoint_looks_live(base_url) and not allow_live_enabled():
        raise BrokerConfigError(
            f"endpoint '{base_url}' looks live; refusing (ALLOW_LIVE is false)")


@dataclass
class ConnectionSafety:
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_latency_ms: Optional[float] = None
    last_heartbeat_ts: Optional[float] = None
    reconnect_attempts: int = 0
    total_reconnects: int = 0
    total_disconnect_seconds: float = 0.0
    _disconnect_started: Optional[float] = field(default=None, repr=False)

    # ------------------------------------------------------------------ #
    def on_connected(self) -> None:
        if self._disconnect_started is not None:
            self.total_disconnect_seconds += time.time() - self._disconnect_started
            self._disconnect_started = None
        self.state = ConnectionState.CONNECTED

    def on_disconnected(self) -> None:
        if self.state != ConnectionState.DISCONNECTED and self._disconnect_started is None:
            self._disconnect_started = time.time()
        self.state = ConnectionState.DISCONNECTED

    def on_heartbeat(self, latency_ms: float) -> None:
        self.last_latency_ms = latency_ms
        self.last_heartbeat_ts = time.time()
        self.state = ConnectionState.CONNECTED

    def on_reconnect_attempt(self) -> None:
        self.reconnect_attempts += 1
        self.state = ConnectionState.RECONNECTING

    def on_reconnect_success(self) -> None:
        self.total_reconnects += 1
        self.on_connected()

    @property
    def seconds_since_heartbeat(self) -> Optional[float]:
        if self.last_heartbeat_ts is None:
            return None
        return time.time() - self.last_heartbeat_ts

    @property
    def current_disconnect_seconds(self) -> float:
        if self._disconnect_started is None:
            return 0.0
        return time.time() - self._disconnect_started
