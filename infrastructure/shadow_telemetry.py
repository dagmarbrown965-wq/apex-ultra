"""
APEX ULTRA — Shadow Telemetry Contract (Phase 40.4)

Shared, neutral definitions used by both the launcher and the operations layer:
the persisted session-record schema and the alert event taxonomy. Pure data —
no signal generation, scoring, sizing, execution, or external I/O.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

TELEMETRY_VERSION = "1.0"


class AlertType(str, Enum):
    CONNECTION_LOST = "connection_lost"
    STALE_SIGNAL_FEED = "stale_signal_feed"
    INTEGRITY_FAILURE = "integrity_failure"
    RISK_ANOMALY = "risk_anomaly"
    SESSION_STOPPED = "session_stopped"


@dataclass
class ConnectionEvent:
    wall_ts: float
    kind: str            # "connected" | "lost" | "reconnected"
    detail: str = ""


@dataclass
class SessionRecord:
    """The durable state of a shadow session. Serializable to JSON."""
    telemetry_version: str = TELEMETRY_VERSION
    session_id: str = ""
    mode: str = "real"
    state: str = "CREATED"

    start_wall: Optional[float] = None
    end_wall: Optional[float] = None
    first_signal_ts: Optional[float] = None
    last_signal_ts: Optional[float] = None

    opportunities: int = 0
    heartbeats_ok: int = 0
    heartbeats_missed: int = 0
    last_heartbeat_wall: Optional[float] = None

    integrity_passed: int = 0
    integrity_failed: int = 0
    modified_signals: list = field(default_factory=list)

    connection_events: list = field(default_factory=list)   # list[dict]
    seen_signal_ids: list = field(default_factory=list)      # for resume dedup

    stop_reason: str = ""
    final_verdict: str = "EXTEND"     # never PASS until the period actually completes

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SessionRecord":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})
