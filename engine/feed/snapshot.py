"""CapturedSnapshotFeed — load a captured price snapshot from JSON.

Phase 42.0B-M0 feed. Reads a static JSON file of recent closing prices and
returns a MarketSnapshot. Deterministic, offline, no network. Imports nothing
from any broker, Deriv transport, websocket, or account surface.

Timestamp handling: the canonical signal contract requires a NUMERIC timestamp
(epoch seconds) so the bridge can float()-coerce it. This feed accepts either a
number or an ISO-8601 string in the snapshot file and normalizes to a float
epoch, so the emitted signal is always contract-correct.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from engine.feed.base import MarketFeed, MarketSnapshot


def _to_epoch(value) -> float:
    """Return a float epoch (seconds) from a number or ISO-8601 string."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    # tolerate a trailing 'Z' (UTC) which fromisoformat historically rejected
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


class CapturedSnapshotFeed(MarketFeed):
    """A read-only feed backed by a captured JSON snapshot on disk.

    Expected JSON shape:
        {
          "symbol": "R_100",
          "timestamp": 1782691200.0,            # epoch seconds, OR ISO-8601 string
          "prices": [<float>, <float>, ...]     # oldest -> newest closes
        }
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def snapshot(self, symbol: str) -> MarketSnapshot:
        """Return a MarketSnapshot loaded from the captured JSON file.

        The `symbol` argument is validated against the file's symbol so a
        snapshot is never silently used for the wrong instrument. The timestamp
        is normalized to a numeric epoch (contract requirement).
        """
        with open(self._path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        file_symbol = data["symbol"]
        if symbol != file_symbol:
            raise ValueError(
                f"requested symbol {symbol!r} does not match snapshot "
                f"symbol {file_symbol!r}"
            )

        prices = tuple(float(p) for p in data["prices"])
        timestamp = _to_epoch(data["timestamp"])
        return MarketSnapshot(
            symbol=file_symbol,
            timestamp=timestamp,
            prices=prices,
        )
