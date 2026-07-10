"""
APEX ULTRA — Signal Schema v1.0 (Phase 40.2)

Bridge-side validation built on the shared signal contract. Only validates,
identifies, and hashes signals the engine already produced — never generates,
infers, scores, sizes, or executes.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from infrastructure.signal_contract import (  # noqa: E402
    HASH_FIELDS,
    SCHEMA_FIELDS,
    SCHEMA_VERSION,
    compute_signal_hash,
    make_signal_id,
    normalize_direction,
    verify_signal_hash,
)

REQUIRED_FIELDS = list(SCHEMA_FIELDS)
REQUIRED_NONNULL = [
    "timestamp", "symbol", "strategy", "direction", "score", "regime",
    "entry_price", "risk_percent", "confidence",
]


class SchemaError(Exception):
    pass


def validate_schema(sig: dict) -> tuple[bool, list[str], bool]:
    """Validate against schema v1.0.

    Returns (ok, problems, version_mismatch). schema_version/signal_id may be
    injected by the bridge, so their absence is not a problem here.
    """
    if not isinstance(sig, dict):
        return False, ["<not-a-dict>"], False

    version_mismatch = False
    sv = sig.get("schema_version")
    if sv is not None and str(sv) != SCHEMA_VERSION:
        version_mismatch = True

    problems: list[str] = []
    for f in REQUIRED_FIELDS:
        if f in ("schema_version", "signal_id"):
            continue
        if f not in sig:
            problems.append(f)
    for f in REQUIRED_NONNULL:
        if sig.get(f) is None and f not in problems:
            problems.append(f)
    if "direction" not in problems and normalize_direction(sig.get("direction")) is None:
        problems.append("direction")

    # numeric fields must be coercible — a corrupted value is rejected here
    # rather than crashing downstream translation.
    for f in ["timestamp", "score", "entry_price", "risk_percent", "confidence",
              "stop_loss", "take_profit"]:
        v = sig.get(f)
        if v is None or f in problems:
            continue
        try:
            float(v)
        except (TypeError, ValueError):
            problems.append(f)

    ok = (len(problems) == 0) and not version_mismatch
    return ok, problems, version_mismatch
