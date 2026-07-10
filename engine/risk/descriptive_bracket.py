"""DescriptiveBracket â€” SIGNAL METADATA generation. NOT trading risk management.

Phase 42.0B-M0. Fills the required descriptive contract fields stop_loss,
take_profit, and risk_percent from the Decision direction and the snapshot's
last price, using FIXED declared constants.

This is NOT order sizing, margin, leverage, or position management. By design it
accepts ONLY Decision + MarketSnapshot and has no parameter, attribute, or import
that exposes balance, equity, or account state. It cannot size a position.
"""
from __future__ import annotations

from engine.feed.base import MarketSnapshot
from engine.risk.base import Bracket, RiskModel


class DescriptiveBracket(RiskModel):
    """Descriptive bracket from fixed constants around the last price.

    Fixed, declared constants (NOT tuned, NOT optimized):
      stop_pct    : distance of stop from entry, as a fraction of entry price.
      target_pct  : distance of target from entry, as a fraction of entry price.
      risk_percent: a descriptive constant written into the signal metadata.

    For a long: stop below entry, target above. For a short: mirrored.
    """

    def __init__(
        self,
        stop_pct: float = 0.01,
        target_pct: float = 0.02,
        risk_percent: float = 1.0,
    ) -> None:
        self.stop_pct = stop_pct
        self.target_pct = target_pct
        self.risk_percent = risk_percent

    def bracket(self, decision, snapshot: MarketSnapshot) -> Bracket:
        prices = snapshot.prices
        if not prices:
            raise ValueError("cannot build a bracket from an empty price series")
        entry = float(prices[-1])

        if decision.direction == "long":
            stop = entry * (1.0 - self.stop_pct)
            target = entry * (1.0 + self.target_pct)
        elif decision.direction == "short":
            stop = entry * (1.0 + self.stop_pct)
            target = entry * (1.0 - self.target_pct)
        else:
            raise ValueError(f"unknown direction: {decision.direction!r}")

        return Bracket(
            entry_price=entry,
            stop_loss=stop,
            take_profit=target,
            risk_percent=self.risk_percent,
        )
