"""build_signal â€” compose the canonical signal_contract v1.0 dict.

Combines a Decision, regime label, descriptive Bracket, and snapshot into the
exact v1.0 field set:

    timestamp, symbol, strategy, direction, score, regime,
    entry_price, stop_loss, take_profit, risk_percent, confidence

Does NOT set signal_id, schema_version, or signal_hash â€” those are injected by
the frozen bridge (APEXSignalAdapter) downstream.
"""
from __future__ import annotations

from engine.feed.base import MarketSnapshot
from engine.risk.base import Bracket
from engine.strategy.base import Decision

# Canonical signal_contract v1.0 field order (emitter-side; pre-bridge).
# signal_id / schema_version / signal_hash are intentionally absent here.
V1_FIELDS = (
    "timestamp",
    "symbol",
    "strategy",
    "direction",
    "score",
    "regime",
    "entry_price",
    "stop_loss",
    "take_profit",
    "risk_percent",
    "confidence",
)


def build_signal(
    decision: Decision,
    regime: str,
    bracket: Bracket,
    snapshot: MarketSnapshot,
    strategy_name: str,
) -> dict:
    """Return a canonical v1.0 signal dict (pre-bridge).

    score is derived from the Decision's conviction (0-1) as a 0-100 value;
    confidence carries the raw conviction. Both are descriptive only.
    """
    score = round(decision.conviction * 100.0, 4)
    confidence = round(decision.conviction, 4)

    return {
        "timestamp": snapshot.timestamp,
        "symbol": snapshot.symbol,
        "strategy": strategy_name,
        "direction": decision.direction,
        "score": score,
        "regime": regime,
        "entry_price": round(bracket.entry_price, 6),
        "stop_loss": round(bracket.stop_loss, 6),
        "take_profit": round(bracket.take_profit, 6),
        "risk_percent": bracket.risk_percent,
        "confidence": confidence,
    }
