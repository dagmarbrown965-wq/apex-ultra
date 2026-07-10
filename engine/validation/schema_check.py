"""schema_check — emitter-side parity against signal_contract v1.0 (CP0).

Asserts an emitted dict carries EXACTLY the v1.0 field set: no missing fields,
no extras, and in particular that bridge-owned fields (signal_id,
schema_version, signal_hash) are ABSENT pre-bridge. Intended to import the
canonical contract READ-ONLY at test time. Skeleton only (Phase 42.0A): no impl.
"""
from __future__ import annotations

from engine.assemble.signal_builder import V1_FIELDS

# Fields the engine must NOT set; the frozen bridge injects these downstream.
BRIDGE_OWNED_FIELDS = ("signal_id", "schema_version", "signal_hash")


def check_emitter_fields(signal: dict) -> None:
    """Assert `signal` has exactly V1_FIELDS and no bridge-owned fields.

    Phase 42.0A skeleton: not implemented. Implemented in 42.0C.
    """
    raise NotImplementedError
