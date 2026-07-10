"""APEX ULTRA signal-source adapters (Phase 40.1)."""

from .signal_source import (
    NoSignalSource,
    REQUIRED_FIELDS,
    SignalSource,
    normalize_direction,
    to_shadow_signal,
    validate_signal,
)
from .apex_signal_adapter import (
    APEXSignalAdapter,
    LiveEngineSignalAdapter,
    NullSignalAdapter,
    ReplayJournalSignalAdapter,
    SignalFlowStats,
)

__all__ = [
    "NoSignalSource",
    "REQUIRED_FIELDS",
    "SignalSource",
    "normalize_direction",
    "to_shadow_signal",
    "validate_signal",
    "APEXSignalAdapter",
    "LiveEngineSignalAdapter",
    "NullSignalAdapter",
    "ReplayJournalSignalAdapter",
    "SignalFlowStats",
]

from .signal_schema import REQUIRED_NONNULL, SCHEMA_VERSION, validate_schema
from .pipeline_health import LatencyBreakdown, LatencySample, PipelineHealth
from infrastructure.signal_contract import (
    HASH_FIELDS,
    compute_signal_hash,
    make_signal_id,
    verify_signal_hash,
)

__all__ += [
    "REQUIRED_NONNULL", "SCHEMA_VERSION", "validate_schema",
    "LatencyBreakdown", "LatencySample", "PipelineHealth",
    "HASH_FIELDS", "compute_signal_hash", "make_signal_id", "verify_signal_hash",
]

from .shadow_ops import (
    AlertHub,
    SessionStore,
    export_csv_journal,
    export_json,
    export_summary,
)
from infrastructure.shadow_telemetry import AlertType, ConnectionEvent, SessionRecord

__all__ += [
    "AlertHub", "SessionStore", "export_csv_journal", "export_json",
    "export_summary", "AlertType", "ConnectionEvent", "SessionRecord",
]
