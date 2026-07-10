"""RegimeDetector — observation -> regime label.

Classifies market context into a label used to fill the canonical `regime`
field. Skeleton only (Phase 42.0A): no implementation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from engine.feed.base import MarketSnapshot


class RegimeDetector(ABC):
    """Abstract regime classifier."""

    @abstractmethod
    def classify(self, snapshot: MarketSnapshot) -> str:
        """Return a regime label for the given snapshot."""
        raise NotImplementedError
