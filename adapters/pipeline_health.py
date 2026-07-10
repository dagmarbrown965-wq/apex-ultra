"""
APEX ULTRA — Signal Pipeline Health & Latency (Phase 40.2)

Monitoring ONLY. Nothing here alters, generates, or routes signals. It observes
the bridge's flow and reports health + a per-stage latency breakdown.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------- #
# Per-stage latency breakdown
# --------------------------------------------------------------------------- #
@dataclass
class LatencySample:
    engine_emit_ms: float = 0.0      # engine emit -> bridge receive (if provided)
    bridge_receive_ms: float = 0.0   # source.next_signal() call cost
    validation_ms: float = 0.0       # schema validation + hashing
    shadow_record_ms: float = 0.0    # downstream shadow record (filled later)

    @property
    def total_ms(self) -> float:
        return (self.engine_emit_ms + self.bridge_receive_ms
                + self.validation_ms + self.shadow_record_ms)


@dataclass
class LatencyBreakdown:
    samples: list[LatencySample] = field(default_factory=list)

    def add(self, sample: LatencySample) -> None:
        self.samples.append(sample)

    def _avg(self, attr: str) -> float:
        if not self.samples:
            return 0.0
        return sum(getattr(s, attr) for s in self.samples) / len(self.samples)

    def report(self) -> dict:
        return {
            "engine_emit_ms": self._avg("engine_emit_ms"),
            "bridge_receive_ms": self._avg("bridge_receive_ms"),
            "validation_ms": self._avg("validation_ms"),
            "shadow_record_ms": self._avg("shadow_record_ms"),
            "total_ms": self._avg("total_ms"),
        }


# --------------------------------------------------------------------------- #
# Pipeline health monitor
# --------------------------------------------------------------------------- #
@dataclass
class PipelineHealth:
    """Observes signal arrival cadence. `now_fn` is injectable for deterministic
    tests; defaults to wall clock."""
    stale_after_seconds: float = 300.0   # warn if no signal for X
    now_fn: object = time.time

    signals_received: int = 0
    duplicates: int = 0
    rejections: int = 0
    first_signal_ts: Optional[float] = None
    last_signal_ts: Optional[float] = None
    _gaps: list = field(default_factory=list)
    _prev_ts: Optional[float] = None

    def on_signal(self, signal_timestamp: float, *, duplicate: bool = False,
                  rejected: bool = False) -> None:
        self.signals_received += 1
        if duplicate:
            self.duplicates += 1
        if rejected:
            self.rejections += 1
        if self.first_signal_ts is None:
            self.first_signal_ts = signal_timestamp
        if self._prev_ts is not None:
            self._gaps.append(max(0.0, signal_timestamp - self._prev_ts))
        self._prev_ts = signal_timestamp
        self.last_signal_ts = signal_timestamp

    # ------------------------------------------------------------------ #
    @property
    def average_gap_seconds(self) -> float:
        return sum(self._gaps) / len(self._gaps) if self._gaps else 0.0

    @property
    def signals_per_hour(self) -> float:
        if self.first_signal_ts is None or self.last_signal_ts is None:
            return 0.0
        span = self.last_signal_ts - self.first_signal_ts
        if span <= 0:
            return 0.0
        return self.signals_received / (span / 3600.0)

    @property
    def duplicate_rate(self) -> float:
        return self.duplicates / self.signals_received if self.signals_received else 0.0

    @property
    def rejection_rate(self) -> float:
        return self.rejections / self.signals_received if self.signals_received else 0.0

    def seconds_since_last(self, now: Optional[float] = None) -> Optional[float]:
        if self.last_signal_ts is None:
            return None
        now = now if now is not None else self.now_fn()
        return now - self.last_signal_ts

    def status(self, now: Optional[float] = None) -> str:
        if self.signals_received == 0:
            return "NO_SIGNALS"
        since = self.seconds_since_last(now)
        if since is not None and since > self.stale_after_seconds:
            return "STALE"
        return "HEALTHY"

    def report(self, now: Optional[float] = None) -> dict:
        since = self.seconds_since_last(now)
        return {
            "signals_received": self.signals_received,
            "signals_per_hour": self.signals_per_hour,
            "last_signal_timestamp": self.last_signal_ts,
            "seconds_since_last": since,
            "average_signal_gap": self.average_gap_seconds,
            "duplicate_rate": self.duplicate_rate,
            "rejection_rate": self.rejection_rate,
            "status": self.status(now),
        }
