"""
APEX ULTRA — APEX Signal Adapters + Hardened Bridge (Phase 40.1 / 40.2)

Three read-only sources and one validating, hardened bridge:

  A) LiveEngineSignalAdapter    — receives real APEX signal events (push queue).
  B) ReplayJournalSignalAdapter — deterministically replays a saved journal.
  C) NullSignalAdapter          — no source; fails safely (-> BLOCKED).

  APEXSignalAdapter (v1.0)       — stamps schema_version + trace signal_id +
                                   integrity hash, validates schema, de-duplicates,
                                   tracks flow / health / latency, and yields
                                   Phase 40 ShadowSignals. Never generates or
                                   infers signals, never calls strategy/risk code,
                                   never exposes execution methods.
"""

from __future__ import annotations

import json
import queue
import time
from dataclasses import dataclass, field
from typing import Optional

from .signal_source import NoSignalSource, SignalSource, dedup_key, to_shadow_signal
from .signal_schema import validate_schema
from .pipeline_health import LatencyBreakdown, LatencySample, PipelineHealth
from infrastructure.signal_contract import (
    SCHEMA_VERSION,
    compute_signal_hash,
    make_signal_id,
)


# --------------------------------------------------------------------------- #
# A) Live engine adapter
# --------------------------------------------------------------------------- #
class LiveEngineSignalAdapter:
    """Receives signals the APEX engine PUSHES. The engine wires its existing
    signal-emit hook to call `push(event)`. Never pulls from strategy/risk code."""

    def __init__(self, poll_timeout: float = 0.5, maxsize: int = 100_000) -> None:
        self._q: "queue.Queue[dict]" = queue.Queue(maxsize=maxsize)
        self.poll_timeout = poll_timeout

    def push(self, event: dict) -> None:
        self._q.put(event)

    def next_signal(self) -> Optional[dict]:
        try:
            return self._q.get(timeout=self.poll_timeout)
        except queue.Empty:
            return None


# --------------------------------------------------------------------------- #
# B) Replay adapter (deterministic)
# --------------------------------------------------------------------------- #
class ReplayJournalSignalAdapter:
    """Replays recorded signals from a saved journal (JSON array or JSONL).
    Fully deterministic: same journal -> same sequence, every run. No randomness."""

    def __init__(self, path: Optional[str] = None,
                 events: Optional[list[dict]] = None) -> None:
        if events is not None:
            self._events = [dict(e) for e in events]
        elif path is not None:
            self._events = self._load(path)
        else:
            self._events = []
        self._i = 0

    @staticmethod
    def _load(path: str) -> list[dict]:
        with open(path, "r") as f:
            text = f.read().strip()
        if not text:
            return []
        if text[0] == "[":
            return json.loads(text)
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def reset(self) -> None:
        self._i = 0

    def next_signal(self) -> Optional[dict]:
        if self._i >= len(self._events):
            return None
        ev = dict(self._events[self._i])  # defensive copy — never mutate the journal
        self._i += 1
        return ev


# --------------------------------------------------------------------------- #
# C) Null adapter
# --------------------------------------------------------------------------- #
class NullSignalAdapter:
    """No signal source. Fails safely so the burn-in is BLOCKED."""

    def next_signal(self) -> Optional[dict]:
        raise NoSignalSource("no signal source configured")


# --------------------------------------------------------------------------- #
# Flow stats
# --------------------------------------------------------------------------- #
@dataclass
class SignalFlowStats:
    received: int = 0
    schema_valid: int = 0
    schema_rejected: int = 0
    missing_fields: int = 0
    version_mismatch: int = 0
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    no_source: bool = False


# --------------------------------------------------------------------------- #
# Hardened bridge
# --------------------------------------------------------------------------- #
class APEXSignalAdapter:
    def __init__(self, source: SignalSource, mode: str = "real",
                 name: Optional[str] = None, stale_after_seconds: float = 300.0,
                 now_fn=time.time) -> None:
        self.source = source
        self.mode = mode
        self.name = name or type(source).__name__
        self.stats = SignalFlowStats()
        self.health = PipelineHealth(stale_after_seconds=stale_after_seconds,
                                     now_fn=now_fn)
        self.latency = LatencyBreakdown()
        self._seen: set = set()
        self._seq = 0
        self._exhausted = False

    # -- canonical interface ------------------------------------------- #
    def next_signal(self) -> Optional[dict]:
        """Return the next VALID, non-duplicate, v1.0-stamped signal dict, or
        None when the source has nothing."""
        while True:
            sample = LatencySample()

            t0 = time.perf_counter()
            try:
                raw = self.source.next_signal()
            except NoSignalSource:
                self.stats.no_source = True
                self._exhausted = True
                return None
            sample.bridge_receive_ms = (time.perf_counter() - t0) * 1000.0

            if raw is None:
                self._exhausted = True
                return None

            self.stats.received += 1
            # engine emit latency (only if the event carries an emit timestamp)
            emit_ts = raw.get("emit_monotonic")
            if isinstance(emit_ts, (int, float)):
                sample.engine_emit_ms = max(0.0, (time.perf_counter() - emit_ts) * 1000.0)

            v0 = time.perf_counter()
            sig = dict(raw)  # work on a copy; never mutate the source event
            sig.setdefault("schema_version", SCHEMA_VERSION)

            ok, problems, version_mismatch = validate_schema(sig)
            if version_mismatch:
                self.stats.version_mismatch += 1
            if not ok:
                self.stats.schema_rejected += 1
                self.stats.rejected += 1
                self.stats.missing_fields += len(problems)
                sample.validation_ms = (time.perf_counter() - v0) * 1000.0
                self.latency.add(sample)
                self.health.on_signal(self._safe_ts(sig), rejected=True)
                continue
            self.stats.schema_valid += 1

            # trace id — assign once, never regenerate downstream
            if not sig.get("signal_id"):
                self._seq += 1
                sig["signal_id"] = make_signal_id(sig.get("symbol"),
                                                  sig.get("timestamp"), self._seq)
            # integrity hash — computed at bridge receive, persists downstream
            sig["signal_hash"] = compute_signal_hash(sig)
            sample.validation_ms = (time.perf_counter() - v0) * 1000.0

            key = dedup_key(sig)
            if key in self._seen:
                self.stats.duplicates += 1
                self.stats.rejected += 1
                self.latency.add(sample)
                self.health.on_signal(self._safe_ts(sig), duplicate=True, rejected=True)
                continue
            self._seen.add(key)

            self.stats.accepted += 1
            self.latency.add(sample)
            self.health.on_signal(self._safe_ts(sig))
            self._last_sample = sample
            return sig

    @staticmethod
    def _safe_ts(sig: dict) -> float:
        try:
            return float(sig.get("timestamp"))
        except (TypeError, ValueError):
            return 0.0

    # -- Phase 40 compatibility ---------------------------------------- #
    def next(self):
        """Return the next ShadowSignal for the Phase 40 loop, or None."""
        sig = self.next_signal()
        if sig is None:
            return None
        return to_shadow_signal(sig)

    @property
    def has_source(self) -> bool:
        return not isinstance(self.source, NullSignalAdapter)

    @property
    def blocked(self) -> bool:
        return self.stats.no_source or isinstance(self.source, NullSignalAdapter)
