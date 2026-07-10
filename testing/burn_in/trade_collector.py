"""
APEX ULTRA — Live Trade Collector (Phase 36)

Records the full per-trade dossier for every demo trade:

  signal timestamp | signal score | regime | strategy | asset
  entry signal price | actual fill price | slippage | spread | latency
  exit reason | P&L

This is a passive recorder. It does not influence routing or sizing.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class DemoTradeRecord:
    trade_id: int
    signal_ts: float
    signal_score: float
    regime: str
    strategy: str
    asset: str
    entry_signal_price: float
    actual_fill_price: float
    slippage_bps: float
    spread: float
    latency_ms: float
    exit_reason: str
    pnl: float
    r_multiple: float


class LiveTradeCollector:
    def __init__(self) -> None:
        self.trades: list[DemoTradeRecord] = []

    def add(self, record: DemoTradeRecord) -> None:
        self.trades.append(record)

    def __len__(self) -> int:
        return len(self.trades)

    # ------------------------------------------------------------------ #
    @property
    def avg_slippage_bps(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.slippage_bps for t in self.trades) / len(self.trades)

    @property
    def avg_latency_ms(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.latency_ms for t in self.trades) / len(self.trades)

    @property
    def avg_spread(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.spread for t in self.trades) / len(self.trades)

    def exit_reason_breakdown(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.trades:
            out[t.exit_reason] = out.get(t.exit_reason, 0) + 1
        return out

    def to_csv(self) -> str:
        if not self.trades:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(asdict(self.trades[0]).keys()))
        writer.writeheader()
        for t in self.trades:
            writer.writerow(asdict(t))
        return buf.getvalue()
