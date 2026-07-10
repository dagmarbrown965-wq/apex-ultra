"""
APEX ULTRA — Signal Source Interface (Phase 40.1)

A read-only bridge between the existing APEX signal pipeline and the Phase 40
shadow burn-in. It CONSUMES signals the engine already produced — it never
generates signals, infers them, or calls strategy/indicator/risk functions.

Canonical signal schema (returned by SignalSource.next_signal()):
  {
    timestamp, symbol, strategy, direction, score, regime,
    entry_price, stop_loss, take_profit, risk_percent, confidence
  }
"""

from __future__ import annotations

import sys
import os
from typing import Optional, Protocol, runtime_checkable

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from infrastructure.broker.broker_interface import OrderSide  # noqa: E402
from infrastructure.broker.deriv import ShadowSignal  # noqa: E402


# fields that must be present in every signal
REQUIRED_FIELDS = [
    "timestamp", "symbol", "strategy", "direction", "score", "regime",
    "entry_price", "stop_loss", "take_profit", "risk_percent", "confidence",
]
# of those, these must also be non-null (stop_loss/take_profit may be null)
REQUIRED_NONNULL = [
    "timestamp", "symbol", "strategy", "direction", "score", "regime",
    "entry_price", "risk_percent", "confidence",
]

_BUY = {"BUY", "LONG", "UP", "B"}
_SELL = {"SELL", "SHORT", "DOWN", "S"}


class NoSignalSource(Exception):
    """Raised by a source that has no signals to provide (e.g. NullAdapter)."""


@runtime_checkable
class SignalSource(Protocol):
    """Read-only signal provider. Returns the next canonical signal dict, or
    None when no signal is currently available / the source is exhausted."""
    def next_signal(self) -> Optional[dict]: ...


def normalize_direction(value) -> Optional[OrderSide]:
    if isinstance(value, OrderSide):
        return value
    if value is None:
        return None
    v = str(value).strip().upper()
    if v in _BUY:
        return OrderSide.BUY
    if v in _SELL:
        return OrderSide.SELL
    return None


def validate_signal(sig: dict) -> tuple[bool, list[str]]:
    """Returns (ok, missing_or_invalid_fields)."""
    if not isinstance(sig, dict):
        return False, ["<not-a-dict>"]
    problems: list[str] = []
    for f in REQUIRED_FIELDS:
        if f not in sig:
            problems.append(f)
    for f in REQUIRED_NONNULL:
        if sig.get(f) is None and f not in problems:
            problems.append(f)
    if "direction" not in problems and normalize_direction(sig.get("direction")) is None:
        problems.append("direction")
    return (len(problems) == 0, problems)


def dedup_key(sig: dict) -> tuple:
    return (sig.get("timestamp"), sig.get("symbol"), sig.get("strategy"),
            str(sig.get("direction")), sig.get("score"))


def to_shadow_signal(sig: dict) -> ShadowSignal:
    """Translate a validated canonical signal into a Phase 40 ShadowSignal.

    NOTE: risk sizing is NOT recomputed here. risk_percent is forwarded as the
    engine's risk intent; the would-be order size carries that value. The shadow
    layer records it; no risk formula is applied in the bridge.
    """
    direction = normalize_direction(sig.get("direction"))
    risk_percent = float(sig.get("risk_percent", 0.0))
    return ShadowSignal(
        timestamp=float(sig["timestamp"]),
        symbol=str(sig["symbol"]),
        strategy=str(sig["strategy"]),
        direction=direction,
        score=float(sig["score"]),
        regime=str(sig["regime"]),
        risk_size=risk_percent,                 # forwarded; not recomputed
        stop_loss=sig.get("stop_loss"),
        take_profit=sig.get("take_profit"),
        accepted=risk_percent > 0,
        reject_reason="" if risk_percent > 0 else "zero_risk_percent",
        outcome=None,                           # resolved from market data (real)
        r_multiple=0.0,
        signal_id=sig.get("signal_id"),         # v1.0 trace id (no regeneration)
        signal_hash=sig.get("signal_hash"),     # v1.0 integrity hash
        entry_price=sig.get("entry_price"),
    )
