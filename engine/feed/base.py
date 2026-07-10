"""MarketFeed — read-only observation contract.

A feed yields a MarketSnapshot for a symbol. It exposes NO order, account, or
execution surface of any kind. Skeleton only (Phase 42.0A): no implementation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarketSnapshot:
    """An immutable read-only view of recent market state.

    Fields are intentionally minimal at 42.0A and will be populated by concrete
    feeds in later milestones. Contains observations only — never account state.
    """

    symbol: str
    timestamp: str
    prices: tuple = field(default_factory=tuple)


class MarketFeed(ABC):
    """Abstract read-only feed. No broker methods exist on this surface."""

    @abstractmethod
    def snapshot(self, symbol: str) -> "MarketSnapshot":
        """Return a read-only MarketSnapshot for the given symbol."""
        raise NotImplementedError
