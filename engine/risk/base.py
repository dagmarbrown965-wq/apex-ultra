"""RiskModel — descriptive bracket metadata, NOT execution risk.

Maps a Decision + MarketSnapshot to a Bracket (entry_price, stop_loss,
take_profit, risk_percent) that fills required *descriptive* contract fields.

Explicitly NOT order sizing, margin, leverage, or position management. The
signature deliberately excludes any account/balance/equity input so this layer
cannot drift into execution sizing. Skeleton only (Phase 42.0A): no impl.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from engine.feed.base import MarketSnapshot
from engine.strategy.base import Decision


@dataclass(frozen=True)
class Bracket:
    """Descriptive price/risk metadata for a signal. Not an order."""

    entry_price: float
    stop_loss: float
    take_profit: float
    risk_percent: float


class RiskModel(ABC):
    """Abstract descriptive-bracket producer."""

    @abstractmethod
    def bracket(self, decision: Decision, snapshot: MarketSnapshot) -> "Bracket":
        """Return descriptive bracket metadata. No account state is consulted."""
        raise NotImplementedError
