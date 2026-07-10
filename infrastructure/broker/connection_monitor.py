"""
APEX ULTRA — Broker Connection Monitor (Phase 35)

Tracks the health of a broker link:
  - connection status
  - heartbeat interval
  - reconnect attempts
  - last message timestamp
  - latency measurement (rolling)

It is broker-agnostic: it drives any object implementing BrokerConnection.
Heartbeats are tick-driven (call `heartbeat()`), keeping validation runs
deterministic; an optional background loop is provided for live use.
"""

from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .broker_interface import BrokerConnection, BrokerDisconnected, ConnectionState


@dataclass
class MonitorSnapshot:
    state: ConnectionState
    heartbeat_interval: float
    reconnect_attempts: int
    last_message_ts: Optional[float]
    seconds_since_last_message: Optional[float]
    last_latency_ms: Optional[float]
    avg_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    heartbeats_ok: int
    heartbeats_missed: int


class ConnectionMonitor:
    def __init__(
        self,
        broker: BrokerConnection,
        heartbeat_interval: float = 1.0,
        max_reconnect_attempts: int = 5,
        backoff_base: float = 0.05,
        backoff_cap: float = 1.0,
        latency_window: int = 100,
    ) -> None:
        self.broker = broker
        self.heartbeat_interval = heartbeat_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap

        self.state: ConnectionState = ConnectionState.DISCONNECTED
        self.reconnect_attempts = 0
        self.total_reconnects = 0
        self.last_message_ts: Optional[float] = None
        self.heartbeats_ok = 0
        self.heartbeats_missed = 0

        self._latencies: deque[float] = deque(maxlen=latency_window)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ #
    # State helpers
    # ------------------------------------------------------------------ #
    def mark_message(self, latency_ms: Optional[float] = None) -> None:
        self.last_message_ts = time.time()
        if latency_ms is not None:
            self._latencies.append(latency_ms)

    def start(self) -> bool:
        self.state = ConnectionState.CONNECTING
        try:
            self.broker.connect()
        except Exception:
            self.state = ConnectionState.FAILED
            return False
        if self.broker.is_connected():
            self.state = ConnectionState.CONNECTED
            self.mark_message()
            return True
        self.state = ConnectionState.FAILED
        return False

    # ------------------------------------------------------------------ #
    # Heartbeat
    # ------------------------------------------------------------------ #
    def heartbeat(self) -> bool:
        """Single heartbeat tick. Returns True if healthy, else triggers
        reconnect and returns the post-recovery health."""
        try:
            latency = self.broker.ping()
            self.heartbeats_ok += 1
            self.state = ConnectionState.CONNECTED
            self.mark_message(latency_ms=latency)
            return True
        except BrokerDisconnected:
            self.heartbeats_missed += 1
            self.state = ConnectionState.DISCONNECTED
            return self.reconnect()

    # ------------------------------------------------------------------ #
    # Reconnect with capped exponential backoff
    # ------------------------------------------------------------------ #
    def reconnect(self) -> bool:
        self.state = ConnectionState.RECONNECTING
        self.reconnect_attempts = 0
        for attempt in range(1, self.max_reconnect_attempts + 1):
            self.reconnect_attempts = attempt
            backoff = min(self.backoff_cap, self.backoff_base * (2 ** (attempt - 1)))
            time.sleep(backoff)
            try:
                self.broker.connect()
                if self.broker.is_connected():
                    self.state = ConnectionState.CONNECTED
                    self.total_reconnects += 1
                    self.mark_message()
                    return True
            except Exception:
                continue
        self.state = ConnectionState.FAILED
        return False

    # ------------------------------------------------------------------ #
    # Metrics
    # ------------------------------------------------------------------ #
    def snapshot(self) -> MonitorSnapshot:
        now = time.time()
        lat = list(self._latencies)
        since = (now - self.last_message_ts) if self.last_message_ts else None
        p95 = None
        if len(lat) >= 2:
            ordered = sorted(lat)
            idx = max(0, int(round(0.95 * (len(ordered) - 1))))
            p95 = ordered[idx]
        return MonitorSnapshot(
            state=self.state,
            heartbeat_interval=self.heartbeat_interval,
            reconnect_attempts=self.reconnect_attempts,
            last_message_ts=self.last_message_ts,
            seconds_since_last_message=since,
            last_latency_ms=lat[-1] if lat else None,
            avg_latency_ms=statistics.fmean(lat) if lat else None,
            p95_latency_ms=p95,
            heartbeats_ok=self.heartbeats_ok,
            heartbeats_missed=self.heartbeats_missed,
        )

    # ------------------------------------------------------------------ #
    # Optional background loop (live use, not used by the validation run)
    # ------------------------------------------------------------------ #
    def run_background(self) -> None:
        def _loop() -> None:
            while not self._stop.is_set():
                self.heartbeat()
                self._stop.wait(self.heartbeat_interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_background(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
