"""
APEX ULTRA — Shared Signal Contract (Phase 40.2)

The single source of truth for the trace-id format and the integrity hash, used
by BOTH the adapters/ bridge and the infrastructure shadow recorder so the id
and hash persist unchanged across the pipeline. Pure functions only — no signal
generation, scoring, sizing, or execution.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

SCHEMA_VERSION = "1.0"

SCHEMA_FIELDS = [
    "schema_version", "signal_id", "timestamp", "symbol", "strategy",
    "direction", "score", "regime", "entry_price", "stop_loss", "take_profit",
    "risk_percent", "confidence",
]

# Immutable fields the integrity hash is computed over, in fixed order.
HASH_FIELDS = [
    "timestamp", "symbol", "strategy", "direction", "score", "entry_price",
    "stop_loss", "take_profit", "risk_percent",
]

_BUY = {"BUY", "LONG", "UP", "B"}
_SELL = {"SELL", "SHORT", "DOWN", "S"}


def normalize_direction(value) -> Optional[str]:
    """Canonical 'BUY'/'SELL' string (broker-agnostic, serializable)."""
    if value is None:
        return None
    v = str(getattr(value, "value", value)).strip().upper()
    if v in _BUY:
        return "BUY"
    if v in _SELL:
        return "SELL"
    return None


def make_signal_id(symbol, timestamp, seq: int) -> str:
    """SIG-<SYMBOL>-<YYYYMMDD>-<NNNNNN>. Deterministic given inputs."""
    sym = str(symbol or "UNK").replace("_", "").upper()
    try:
        day = datetime.fromtimestamp(float(timestamp), tz=timezone.utc).strftime("%Y%m%d")
    except (TypeError, ValueError, OSError):
        day = "00000000"
    return f"SIG-{sym}-{day}-{seq:06d}"


def _canonical(value) -> str:
    if isinstance(value, float):
        return repr(round(value, 10))
    return "" if value is None else str(value)


def compute_signal_hash(fields: dict) -> str:
    """SHA-256 over HASH_FIELDS in fixed order. `direction` is canonicalized so
    'BUY'/OrderSide.BUY/'long' all hash identically."""
    parts = []
    for f in HASH_FIELDS:
        v = fields.get(f)
        if f == "direction":
            v = normalize_direction(v)
        parts.append(f"{f}={_canonical(v)}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def verify_signal_hash(fields: dict, expected_hash: str) -> bool:
    return compute_signal_hash(fields) == expected_hash
