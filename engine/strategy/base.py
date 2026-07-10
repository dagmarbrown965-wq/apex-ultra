"""Strategy — observation -> Decision | None.

A strategy reads a MarketSnapshot and returns a Decision (direction + raw
conviction) or None when it has no signal. It does NOT compute stop_loss,
take_profit, or risk_percent — those are descriptive metadata produced by the
risk layer. Skeleton only (Phase 42.0A): no implementation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from engine.feed.base import MarketSnapshot


@dataclass(frozen=True)
class Decision:
    """A directional intent with raw conviction in [0, 1].

    Carries NO price levels and NO risk numbers — only what the strategy itself
    decides. Brackets and metadata are added downstream.
    """

    direction: str          # e.g. "long" / "short" — concrete sets defined later
    conviction: float       # raw conviction in [0, 1]


class Strategy(ABC):
    """Abstract strategy. Silence (None) is a valid, common output."""

    name: str = "abstract"

    @abstractmethod
    def evaluate(self, snapshot: MarketSnapshot) -> "Decision | None":
        """Return a Decision, or None when there is no signal."""
        raise NotImplementedError
