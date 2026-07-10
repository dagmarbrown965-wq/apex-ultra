"""
APEX ULTRA — Execution Metrics (Phase 35)

Collects per-order execution quality data and aggregates it:
  - order latency
  - expected price
  - fill price
  - slippage (adverse, signed by side)
  - spread cost
  - rejected orders
  - missed executions

"Missed execution" = an order the system intended to place that never reached a
fill (timeout / disconnect / unhandled). Rejections are tracked separately
because they are a clean broker NACK, not a lost intent.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Optional

from infrastructure.broker import Order, OrderResult, OrderSide, Quote


@dataclass
class ExecutionRecord:
    order_id: str
    symbol: str
    side: OrderSide
    qty: float
    requested_qty: float
    expected_price: float
    fill_price: Optional[float]
    latency_ms: float
    slippage_per_unit: float       # adverse slippage in price units (>0 = worse)
    slippage_bps: float
    spread_cost_per_unit: float    # half-spread crossed
    spread_cost_total: float
    filled: bool
    rejected: bool = False
    missed: bool = False
    note: str = ""


@dataclass
class ExecutionMetrics:
    records: list[ExecutionRecord] = field(default_factory=list)
    rejected_orders: int = 0
    missed_executions: int = 0

    # ------------------------------------------------------------------ #
    # Recording
    # ------------------------------------------------------------------ #
    def record_fill(
        self,
        result: OrderResult,
        latency_ms: float,
        expected_price: float,
        quote_at_submit: Optional[Quote] = None,
    ) -> ExecutionRecord:
        order = result.order
        quote = quote_at_submit or result.quote_at_submit
        fill_price = order.avg_fill_price or expected_price

        # adverse slippage: positive means the fill was worse than expected
        if order.side == OrderSide.BUY:
            slip = fill_price - expected_price
        else:
            slip = expected_price - fill_price
        slip_bps = (slip / expected_price) * 1e4 if expected_price else 0.0

        half_spread = (quote.spread / 2.0) if quote else 0.0
        spread_total = half_spread * order.filled_qty

        rec = ExecutionRecord(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            qty=order.filled_qty,
            requested_qty=order.qty,
            expected_price=expected_price,
            fill_price=fill_price,
            latency_ms=latency_ms,
            slippage_per_unit=slip,
            slippage_bps=slip_bps,
            spread_cost_per_unit=half_spread,
            spread_cost_total=spread_total,
            filled=order.filled_qty > 0,
            note="partial" if order.filled_qty < order.qty else "",
        )
        self.records.append(rec)
        return rec

    def record_rejected(self, order: Order, expected_price: float, reason: str) -> ExecutionRecord:
        self.rejected_orders += 1
        rec = ExecutionRecord(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            qty=0.0,
            requested_qty=order.qty,
            expected_price=expected_price,
            fill_price=None,
            latency_ms=0.0,
            slippage_per_unit=0.0,
            slippage_bps=0.0,
            spread_cost_per_unit=0.0,
            spread_cost_total=0.0,
            filled=False,
            rejected=True,
            note=reason,
        )
        self.records.append(rec)
        return rec

    def record_missed(self, order: Order, expected_price: float, reason: str) -> ExecutionRecord:
        self.missed_executions += 1
        rec = ExecutionRecord(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            qty=0.0,
            requested_qty=order.qty,
            expected_price=expected_price,
            fill_price=None,
            latency_ms=0.0,
            slippage_per_unit=0.0,
            slippage_bps=0.0,
            spread_cost_per_unit=0.0,
            spread_cost_total=0.0,
            filled=False,
            missed=True,
            note=reason,
        )
        self.records.append(rec)
        return rec

    # ------------------------------------------------------------------ #
    # Aggregates
    # ------------------------------------------------------------------ #
    @property
    def filled_records(self) -> list[ExecutionRecord]:
        return [r for r in self.records if r.filled]

    @property
    def avg_latency_ms(self) -> float:
        lat = [r.latency_ms for r in self.filled_records]
        return statistics.fmean(lat) if lat else 0.0

    @property
    def avg_slippage_bps(self) -> float:
        s = [r.slippage_bps for r in self.filled_records]
        return statistics.fmean(s) if s else 0.0

    @property
    def avg_slippage_per_unit(self) -> float:
        s = [r.slippage_per_unit for r in self.filled_records]
        return statistics.fmean(s) if s else 0.0

    @property
    def total_spread_cost(self) -> float:
        return sum(r.spread_cost_total for r in self.filled_records)

    @property
    def fill_count(self) -> int:
        return len(self.filled_records)

    @property
    def fill_rate(self) -> float:
        attempted = self.fill_count + self.rejected_orders + self.missed_executions
        return self.fill_count / attempted if attempted else 0.0
