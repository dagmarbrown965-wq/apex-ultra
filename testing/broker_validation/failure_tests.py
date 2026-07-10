"""
APEX ULTRA — Failure Tests (Phase 35)

Drives the mock broker into each adverse condition and asserts the system
handles it gracefully (no crash, correct classification, recovery where
applicable):

  - broker timeout
  - rejected order
  - partial fill
  - disconnect during order
  - reconnect after disconnect

Each test returns a FailureResult with pass/fail + recovery timing where
relevant. Recovery time is captured for the reconnect path.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from infrastructure.broker import (
    BrokerDisconnected,
    BrokerTimeout,
    ConnectionMonitor,
    MockBroker,
    Order,
    OrderRejected,
    OrderSide,
    OrderStatus,
)
from .execution_metrics import ExecutionMetrics


@dataclass
class FailureResult:
    name: str
    passed: bool
    detail: str
    recovery_ms: Optional[float] = None


class FailureTester:
    def __init__(self, broker: MockBroker, monitor: ConnectionMonitor,
                 metrics: ExecutionMetrics) -> None:
        self.broker = broker
        self.monitor = monitor
        self.metrics = metrics

    # ------------------------------------------------------------------ #
    def test_timeout(self) -> FailureResult:
        self.broker.faults.timeout_next = True
        order = Order("APEX", OrderSide.BUY, 5, expected_price=100.0)
        try:
            self.broker.submit_order(order, timeout=0.02)
            return FailureResult("broker_timeout", False, "no timeout raised")
        except BrokerTimeout as e:
            self.metrics.record_missed(order, 100.0, f"timeout:{e}")
            ok = order.status == OrderStatus.TIMED_OUT
            return FailureResult("broker_timeout", ok,
                                 f"classified={order.status.value}")

    def test_rejected(self) -> FailureResult:
        self.broker.faults.reject_next = True
        order = Order("APEX", OrderSide.BUY, 5, expected_price=100.0)
        try:
            self.broker.submit_order(order)
            return FailureResult("rejected_order", False, "no rejection raised")
        except OrderRejected as e:
            self.metrics.record_rejected(order, 100.0, e.reason)
            ok = order.status == OrderStatus.REJECTED
            return FailureResult("rejected_order", ok, f"reason={e.reason}")

    def test_partial_fill(self) -> FailureResult:
        self.broker.faults.partial_fill_next = True
        self.broker.faults.partial_fill_ratio = 0.4
        order = Order("APEX", OrderSide.BUY, 10, expected_price=100.0)
        t0 = time.perf_counter()
        result = self.broker.submit_order(order)
        lat = (time.perf_counter() - t0) * 1000.0
        self.metrics.record_fill(result, lat, 100.0)
        ok = (order.status == OrderStatus.PARTIALLY_FILLED
              and 0 < order.filled_qty < order.qty)
        return FailureResult("partial_fill", ok,
                             f"{order.filled_qty}/{order.qty} filled")

    def test_disconnect_during_order(self) -> FailureResult:
        self.broker.faults.disconnect_during_next = True
        order = Order("APEX", OrderSide.BUY, 5, expected_price=100.0)
        try:
            self.broker.submit_order(order)
            return FailureResult("disconnect_during_order", False,
                                 "no disconnect raised")
        except BrokerDisconnected:
            self.metrics.record_missed(order, 100.0, "disconnect_mid_order")
            ok = not self.broker.is_connected()
            return FailureResult("disconnect_during_order", ok,
                                 "link dropped, order marked missed")

    def test_reconnect_after_disconnect(self) -> FailureResult:
        # ensure we are in a dropped state, then heartbeat-driven recovery
        if self.broker.is_connected():
            self.broker.force_drop()
        self.broker.faults.drop_on_next_ping = False
        t0 = time.perf_counter()
        recovered = self.monitor.reconnect()
        recovery_ms = (time.perf_counter() - t0) * 1000.0
        ok = recovered and self.broker.is_connected()
        return FailureResult(
            "reconnect_after_disconnect", ok,
            f"attempts={self.monitor.reconnect_attempts} recovered={recovered}",
            recovery_ms=recovery_ms,
        )

    # ------------------------------------------------------------------ #
    def run_all(self) -> list[FailureResult]:
        results = [
            self.test_timeout(),
            self.test_rejected(),
            self.test_partial_fill(),
            self.test_disconnect_during_order(),
            self.test_reconnect_after_disconnect(),
        ]
        # leave the broker healthy for downstream phases
        if not self.broker.is_connected():
            self.monitor.reconnect()
        return results
