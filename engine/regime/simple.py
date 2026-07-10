"""SimpleRegime â€” minimal descriptive regime classification.

Phase 42.0B-M0. Classifies market context into one of four descriptive labels
used to fill the canonical `regime` field. METADATA ONLY â€” it does not and must
not control execution. Deterministic; derived from the snapshot's price series.

Allowed outputs:
    TRENDING_BULL, TRENDING_BEAR, RANGE, HIGH_VOLATILITY
"""
from __future__ import annotations

from engine.feed.base import MarketSnapshot
from engine.regime.base import RegimeDetector

ALLOWED_REGIMES = ("TRENDING_BULL", "TRENDING_BEAR", "RANGE", "HIGH_VOLATILITY")


class SimpleRegime(RegimeDetector):
    """Descriptive regime classifier over recent closes.

    Logic (deterministic, descriptive, minimal):
      - volatility = stdev of simple returns over the series.
      - drift      = (last - first) / first.
      If volatility exceeds `vol_threshold` -> HIGH_VOLATILITY.
      Else if |drift| < `flat_threshold`    -> RANGE.
      Else TRENDING_BULL (drift > 0) or TRENDING_BEAR (drift < 0).
    """

    def __init__(self, vol_threshold: float = 0.02, flat_threshold: float = 0.005) -> None:
        self.vol_threshold = vol_threshold
        self.flat_threshold = flat_threshold

    def classify(self, snapshot: MarketSnapshot) -> str:
        prices = snapshot.prices
        if len(prices) < 2:
            return "RANGE"  # insufficient data -> least-committal label

        returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1]
            for i in range(1, len(prices))
            if prices[i - 1] != 0
        ]
        if not returns:
            return "RANGE"

        mean_r = sum(returns) / len(returns)
        var = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        volatility = var ** 0.5

        drift = (prices[-1] - prices[0]) / prices[0] if prices[0] != 0 else 0.0

        if volatility > self.vol_threshold:
            return "HIGH_VOLATILITY"
        if abs(drift) < self.flat_threshold:
            return "RANGE"
        return "TRENDING_BULL" if drift > 0 else "TRENDING_BEAR"
