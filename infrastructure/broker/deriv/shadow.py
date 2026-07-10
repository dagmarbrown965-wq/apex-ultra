"""
APEX ULTRA — Deriv Shadow Layer (Phase 40)

Shadow mode observes a REAL Deriv demo account and records what WOULD have
happened — without ever sending an order. It consumes signals + risk-sized
intents produced by the existing pipeline (it does NOT generate signals or
compute risk), maps them to would-be Deriv requests via the existing execution
mapping (read-only), and records the full context.

Structural safety: ShadowBrokerView exposes only read/observe methods. There is
no code path from the shadow controller to submitOrder/buy/sell — "Live orders
sent: 0" is guaranteed by construction, not by a flag.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from typing import Optional

from ..broker_interface import OrderSide
from .execution_mapping import ApexOrderIntent, DerivContractSpec, map_intent_to_proposal


class ShadowViolation(Exception):
    """Raised if anything attempts to place an order in shadow mode."""


@dataclass
class ShadowSignal:
    """Output of the existing strategy+risk pipeline (the seam). The shadow layer
    consumes these; it does not create them."""
    timestamp: float
    symbol: str
    strategy: str
    direction: OrderSide
    score: float
    regime: str
    risk_size: float                 # produced by the risk engine (not recomputed)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    accepted: bool = True            # pipeline's accept/reject decision
    reject_reason: str = ""
    # outcome is resolved from subsequent market data (real) or fixture (dry-run)
    outcome: Optional[str] = None    # "win" | "loss" | None (open/unresolved)
    r_multiple: float = 0.0
    # v1.0 contract — persist trace id + integrity hash through the pipeline
    signal_id: Optional[str] = None
    signal_hash: Optional[str] = None
    entry_price: Optional[float] = None


@dataclass
class ShadowEvent:
    timestamp: float
    symbol: str
    strategy: str
    signal_direction: str
    signal_score: float
    regime: str
    expected_entry: float
    market_price: float
    spread: float
    latency_ms: float
    risk_size: float
    would_be_order_size: float
    would_be_stop_loss: Optional[float]
    would_be_take_profit: Optional[float]
    reason: str                      # acceptance / rejection reason
    accepted: bool
    outcome: Optional[str] = None
    r_multiple: float = 0.0
    would_be_request: dict = field(default_factory=dict)
    signal_id: Optional[str] = None
    signal_hash: Optional[str] = None
    integrity_ok: bool = True


# --------------------------------------------------------------------------- #
# No-execution broker view
# --------------------------------------------------------------------------- #
class ShadowBrokerView:
    """Read-only facade over the Deriv adapter. Order methods are absent and any
    attempt to reach them raises ShadowViolation."""

    _FORBIDDEN = ("submitOrder", "submit_order", "submit_intent",
                  "closePosition", "buy", "sell")

    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.live_orders_sent = 0  # invariant: stays 0

    # explicit read-only passthroughs
    def connect(self): return self._adapter.connect()
    def disconnect(self): return self._adapter.disconnect()
    def heartbeat(self): return self._adapter.heartbeat()
    def is_connected(self): return self._adapter.is_connected()
    def getBalance(self): return self._adapter.getBalance()
    def get_quote(self, symbol): return self._adapter.get_quote(symbol)
    def stream_ticks(self, count=5, timeout=10.0):
        return self._adapter.stream_ticks(count=count, timeout=timeout)
    def contracts_for(self, symbol=None): return self._adapter.contracts_for(symbol)
    def force_drop(self): return self._adapter.force_drop()  # for resilience tests

    @property
    def symbol(self): return self._adapter.symbol

    @property
    def current_mid(self): return self._adapter.current_mid

    @property
    def safety(self): return self._adapter.safety

    @property
    def is_virtual(self): return getattr(self._adapter, "_is_virtual", None)

    @property
    def loginid(self): return getattr(self._adapter, "_loginid", None)

    def __getattr__(self, name):
        if name in self._FORBIDDEN:
            raise ShadowViolation(
                f"'{name}' is forbidden in shadow mode — no live orders permitted")
        raise AttributeError(name)


# --------------------------------------------------------------------------- #
# Recorder + metrics
# --------------------------------------------------------------------------- #
class ShadowRecorder:
    def __init__(self) -> None:
        self.events: list[ShadowEvent] = []
        self.missed_signals = 0
        self.risk_blocks = 0
        self.connection_failures = 0
        self.reconnect_successes = 0
        # v1.0 integrity tracking (bridge-receive hash vs shadow-record recompute)
        self.integrity_passed = 0
        self.integrity_failed = 0
        self.modified_signals: list = []

    # ------------------------------------------------------------------ #
    def record(self, signal: ShadowSignal, quote, latency_ms: float,
               spec: DerivContractSpec, currency: str) -> ShadowEvent:
        mid = quote.mid
        spread = quote.spread
        # would-be order mapping (read-only use of the existing mapping)
        would_be_request = {}
        wb_size = signal.risk_size if signal.accepted else 0.0
        if signal.accepted and signal.risk_size > 0:
            intent = ApexOrderIntent(
                side=signal.direction, size=signal.risk_size, symbol=signal.symbol,
                stop_loss=signal.stop_loss, take_profit=signal.take_profit)
            try:
                would_be_request = map_intent_to_proposal(intent, spec, currency)
            except Exception as e:
                would_be_request = {"error": str(e)}
        reason = ("accepted" if signal.accepted
                  else f"rejected: {signal.reject_reason or 'risk'}")
        if not signal.accepted:
            self.risk_blocks += 1

        # integrity: recompute the hash from the recorded immutable fields and
        # compare to the hash stamped at bridge-receive. A mismatch means the
        # payload was modified between bridge and shadow record.
        integrity_ok = True
        if signal.signal_hash is not None:
            from infrastructure.signal_contract import compute_signal_hash
            recomputed = compute_signal_hash({
                "timestamp": signal.timestamp, "symbol": signal.symbol,
                "strategy": signal.strategy, "direction": signal.direction,
                "score": signal.score, "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss, "take_profit": signal.take_profit,
                "risk_percent": signal.risk_size,
            })
            integrity_ok = (recomputed == signal.signal_hash)
            if integrity_ok:
                self.integrity_passed += 1
            else:
                self.integrity_failed += 1
                self.modified_signals.append(signal.signal_id)

        ev = ShadowEvent(
            timestamp=signal.timestamp, symbol=signal.symbol, strategy=signal.strategy,
            signal_direction=signal.direction.value, signal_score=signal.score,
            regime=signal.regime, expected_entry=mid, market_price=mid, spread=spread,
            latency_ms=latency_ms, risk_size=signal.risk_size,
            would_be_order_size=wb_size, would_be_stop_loss=signal.stop_loss,
            would_be_take_profit=signal.take_profit, reason=reason,
            accepted=signal.accepted, outcome=signal.outcome,
            r_multiple=signal.r_multiple, would_be_request=would_be_request,
            signal_id=signal.signal_id, signal_hash=signal.signal_hash,
            integrity_ok=integrity_ok)
        self.events.append(ev)
        return ev

    def record_missed(self) -> None:
        self.missed_signals += 1

    def record_connection_failure(self) -> None:
        self.connection_failures += 1

    def record_reconnect(self, ok: bool) -> None:
        if ok:
            self.reconnect_successes += 1

    # ------------------------------------------------------------------ #
    # Aggregates
    # ------------------------------------------------------------------ #
    @property
    def accepted_events(self) -> list[ShadowEvent]:
        return [e for e in self.events if e.accepted]

    @property
    def rejected_events(self) -> list[ShadowEvent]:
        return [e for e in self.events if not e.accepted]

    @property
    def resolved(self) -> list[ShadowEvent]:
        return [e for e in self.accepted_events if e.outcome in ("win", "loss")]

    def win_rate_estimate(self) -> float:
        r = self.resolved
        if not r:
            return 0.0
        return sum(1 for e in r if e.outcome == "win") / len(r)

    def _win_r(self) -> list[float]:
        return [e.r_multiple for e in self.resolved if e.outcome == "win"]

    def _loss_r(self) -> list[float]:
        return [abs(e.r_multiple) for e in self.resolved if e.outcome == "loss"]

    def average_rr(self) -> float:
        w, l = self._win_r(), self._loss_r()
        aw = statistics.fmean(w) if w else 0.0
        al = statistics.fmean(l) if l else 0.0
        return (aw / al) if al else 0.0

    def profit_factor(self) -> float:
        gw, gl = sum(self._win_r()), sum(self._loss_r())
        return (gw / gl) if gl else (float("inf") if gw else 0.0)

    def max_simulated_drawdown(self) -> float:
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for e in self.resolved:
            equity += e.r_multiple if e.outcome == "win" else -abs(e.r_multiple)
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        return max_dd  # in R units

    def _perf_by(self, key) -> dict[str, float]:
        groups: dict[str, list[ShadowEvent]] = {}
        for e in self.resolved:
            groups.setdefault(key(e), []).append(e)
        return {k: (sum(1 for e in v if e.outcome == "win") / len(v))
                for k, v in groups.items() if v}

    def regime_performance(self) -> dict[str, float]:
        return self._perf_by(lambda e: e.regime)

    def asset_performance(self) -> dict[str, float]:
        return self._perf_by(lambda e: e.symbol)

    def avg_latency_ms(self) -> float:
        lat = [e.latency_ms for e in self.events]
        return statistics.fmean(lat) if lat else 0.0

    def avg_spread(self) -> float:
        sp = [e.spread for e in self.events]
        return statistics.fmean(sp) if sp else 0.0
