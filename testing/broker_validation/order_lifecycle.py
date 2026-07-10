"""
APEX ULTRA — Order Lifecycle Tests (Phase 35)

Exercises the full demo order path end to end:

  BUY :  signal -> risk -> order -> fill -> position (opened)
  SELL:  signal -> risk -> order -> fill -> close   (flat)

The "risk" step is an injected gate (RiskGate). The default demo gate is
permissive and is part of the TEST harness only — it does NOT replace or modify
the production RiskManager. Wire the real risk manager in via `risk_gate` for
integrated runs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from infrastructure.broker import (
    BrokerConnection,
    Order,
    OrderResult,
    OrderSide,
    OrderType,
)
from .execution_metrics import ExecutionMetrics


@dataclass
class SignalIntent:
    """A signal already produced upstream. Scaffolding only — not generation."""
    symbol: str
    side: OrderSide
    qty: float
    expected_price: float
    score: float = 0.0
    regime: str = "unknown"
    strategy: str = "n/a"


@dataclass
class RiskDecision:
    approved: bool
    qty: float
    reason: str = "ok"


# A RiskGate maps (intent, current_position_qty) -> RiskDecision
RiskGate = Callable[[SignalIntent, float], RiskDecision]


def permissive_demo_gate(intent: SignalIntent, position_qty: float) -> RiskDecision:
    """Default harness gate. Approves as-is. Replace with real RiskManager."""
    if intent.qty <= 0:
        return RiskDecision(False, 0.0, "non_positive_qty")
    return RiskDecision(True, intent.qty, "ok")


@dataclass
class LifecycleResult:
    name: str
    passed: bool
    detail: str
    order_id: Optional[str] = None


class OrderLifecycleTester:
    def __init__(
        self,
        broker: BrokerConnection,
        metrics: ExecutionMetrics,
        risk_gate: RiskGate = permissive_demo_gate,
    ) -> None:
        self.broker = broker
        self.metrics = metrics
        self.risk_gate = risk_gate

    # ------------------------------------------------------------------ #
    def _route(self, intent: SignalIntent) -> OrderResult:
        pos = self.broker.get_position(intent.symbol)
        decision = self.risk_gate(intent, pos.qty)
        if not decision.approved:
            order = Order(intent.symbol, intent.side, intent.qty,
                          expected_price=intent.expected_price)
            self.metrics.record_rejected(order, intent.expected_price,
                                          f"risk:{decision.reason}")
            raise RuntimeError(f"risk rejected: {decision.reason}")

        order = Order(
            symbol=intent.symbol,
            side=intent.side,
            qty=decision.qty,
            order_type=OrderType.MARKET,
            expected_price=intent.expected_price,
        )
        t0 = time.perf_counter()
        result = self.broker.submit_order(order)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        self.metrics.record_fill(result, latency_ms, intent.expected_price)
        return result

    # ------------------------------------------------------------------ #
    def test_buy_cycle(self, symbol: str, qty: float, price: float) -> LifecycleResult:
        before = self.broker.get_position(symbol).qty
        intent = SignalIntent(symbol, OrderSide.BUY, qty, price,
                              score=0.8, regime="trend", strategy="demo")
        try:
            result = self._route(intent)
        except Exception as e:
            return LifecycleResult("BUY signal->risk->order->fill->position",
                                   False, str(e))
        after = self.broker.get_position(symbol).qty
        opened = abs((after - before) - result.order.filled_qty) < 1e-6
        ok = result.order.filled_qty > 0 and opened and after > before
        return LifecycleResult(
            "BUY signal->risk->order->fill->position", ok,
            f"pos {before:.2f} -> {after:.2f} @ {result.order.avg_fill_price:.4f}",
            result.order.id,
        )

    def test_sell_cycle(self, symbol: str, qty: float, price: float) -> LifecycleResult:
        # Ensure there is a long position to close first.
        if self.broker.get_position(symbol).qty < qty:
            warm = SignalIntent(symbol, OrderSide.BUY, qty, price)
            self._route(warm)
        before = self.broker.get_position(symbol).qty
        intent = SignalIntent(symbol, OrderSide.SELL, qty, price,
                              score=0.7, regime="trend", strategy="demo")
        try:
            result = self._route(intent)
        except Exception as e:
            return LifecycleResult("SELL signal->risk->order->fill->close",
                                   False, str(e))
        after = self.broker.get_position(symbol).qty
        closed = (before - after) > 0
        ok = result.order.filled_qty > 0 and closed
        return LifecycleResult(
            "SELL signal->risk->order->fill->close", ok,
            f"pos {before:.2f} -> {after:.2f} @ {result.order.avg_fill_price:.4f}",
            result.order.id,
        )

    def run_all(self, symbol: str = "APEX", qty: float = 10.0,
                price: float = 100.0) -> list[LifecycleResult]:
        return [
            self.test_buy_cycle(symbol, qty, price),
            self.test_sell_cycle(symbol, qty, price),
        ]
