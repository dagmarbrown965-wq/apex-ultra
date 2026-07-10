"""LiveReadonlyFeed - Phase 43 live observation feed (READ-ONLY).

Governed by docs/PHASE_43_BOUNDARY_AGREEMENT.md (locked). Summary of the
boundary this file implements:

- Source: infrastructure.broker.deriv.rest_shadow_adapter.RestOtpShadowAdapter
  ONLY (the 41.1-validated read surface). Imported LAZILY inside connect() so
  that importing engine.* never touches broker code (CP1), and so the CP3
  static scan sees exactly one allowlisted import site.
- close = _Quote.mid (PINNED). mid is (bid+ask)/2 where both exist, else
  quote - closes within one buffer may be heterogeneous; accepted for
  placeholder plumbing, revisit at 42.1.
- Rolling in-memory buffer, maxlen=25 (headroom over the required 20).
  While the buffer holds fewer than 20 closes, snapshot() still returns a
  truthful MarketSnapshot with the short prices tuple - ReferenceMA returns
  None below slow=20, so silence happens in the STRATEGY, exactly as it does
  on the captured path. No synthetic padding, no backfill, no fabrication.
- Duplicate re-reads (same epoch as the last accepted tick) are SKIPPED and
  counted - a close is never double-counted when polling faster than ticks
  arrive.
- No order, proposal, buy, sell, position, or account-mutation surface is
  imported, constructed, or called. Execution stays impossible.

The feed is dependency-injectable: pass adapter= for tests (no network);
pass api_token=/app_id= for a real session (network, demo-account-only,
enforced by the adapter's own ShadowViolation guard at connect).
"""
from __future__ import annotations

import time
from collections import deque

from engine.feed.base import MarketFeed, MarketSnapshot

WARMUP_CLOSES = 20      # ReferenceMA slow period; below this the strategy is silent
BUFFER_MAXLEN = 25      # matches the golden snapshot depth; headroom over warmup


class FeedNotConnectedError(RuntimeError):
    """poll()/snapshot() used before connect(), or after disconnect()."""


class LiveReadonlyFeed(MarketFeed):
    """Read-only live feed: polls quotes, buffers mids, emits MarketSnapshots.

    Usage (real):
        feed = LiveReadonlyFeed(api_token=..., app_id=..., symbol="R_100")
        feed.connect()                 # demo-only enforced by the adapter
        feed.poll()                    # one tick -> one close into the buffer
        snap = feed.snapshot("R_100")  # truthful view of the buffer

    Usage (test): LiveReadonlyFeed(adapter=fake, symbol="R_100")
    """

    def __init__(self, *, adapter=None, api_token: str = "",
                 app_id: str = "", symbol: str = "R_100") -> None:
        self._adapter = adapter          # injected (tests) or built in connect()
        self._api_token = api_token
        self._app_id = app_id
        self.symbol = symbol
        self._closes: deque = deque(maxlen=BUFFER_MAXLEN)
        self._last_epoch: float = 0.0    # epoch of the newest accepted tick
        self._connected = adapter is not None
        # observability counters (read by the runner; never sent anywhere)
        self.ticks_seen = 0
        self.ticks_rejected = 0
        self.ticks_duplicate = 0

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        """Open the read-only adapter. Demo-only is enforced by the adapter
        itself (ShadowViolation on non-virtual accounts) - inherited guard."""
        if self._adapter is None:
            # LAZY allowlisted import - the single broker touchpoint (CP3).
            from infrastructure.broker.deriv.rest_shadow_adapter import (
                RestOtpShadowAdapter,
            )
            self._adapter = RestOtpShadowAdapter(
                api_token=self._api_token,
                app_id=self._app_id or None,
                symbol=self.symbol,
            )
        connect = getattr(self._adapter, "connect", None)
        if callable(connect):
            connect()
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False
        if self._adapter is not None:
            disconnect = getattr(self._adapter, "disconnect", None)
            if callable(disconnect):
                try:
                    disconnect()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # data path: one poll -> at most one close
    # ------------------------------------------------------------------ #
    def poll(self) -> bool:
        """Fetch one quote; append its mid as one close.

        Returns True if a close was accepted, False if the tick was absent,
        unusable (no numeric mid), or a duplicate re-read of the last tick
        (same epoch). Everything skipped is counted, never invented.
        """
        if not self._connected or self._adapter is None:
            raise FeedNotConnectedError("connect() before poll()")
        q = self._adapter.get_quote(self.symbol)
        self.ticks_seen += 1
        mid = getattr(q, "mid", None) if q is not None else None
        if not isinstance(mid, (int, float)):
            self.ticks_rejected += 1
            return False
        epoch = getattr(q, "epoch", None)
        # Duplicate read: polling faster than ticks arrive returns the SAME
        # tick again (same epoch). That is a re-read, not a new close - skip
        # it so a close is never double-counted. Counted, never invented.
        if (isinstance(epoch, (int, float)) and self._closes
                and float(epoch) == self._last_epoch):
            self.ticks_duplicate += 1
            return False
        self._closes.append(float(mid))
        if isinstance(epoch, (int, float)):
            self._last_epoch = float(epoch)
        else:
            # tick carried no epoch: fall back to receipt time (numeric,
            # contract-correct).
            self._last_epoch = time.time()
        return True

    # ------------------------------------------------------------------ #
    # feed contract
    # ------------------------------------------------------------------ #
    @property
    def is_warm(self) -> bool:
        return len(self._closes) >= WARMUP_CLOSES

    @property
    def depth(self) -> int:
        return len(self._closes)

    def snapshot(self, symbol: str) -> MarketSnapshot:
        """Truthful view of the buffer, oldest -> newest.

        Never pads, never backfills. Below warmup the prices tuple is simply
        short, and ReferenceMA correctly returns None - silence by design.
        """
        if not self._connected:
            raise FeedNotConnectedError("connect() before snapshot()")
        if symbol != self.symbol:
            raise ValueError(
                f"requested symbol {symbol!r} does not match feed "
                f"symbol {self.symbol!r}"
            )
        return MarketSnapshot(
            symbol=self.symbol,
            timestamp=self._last_epoch,   # numeric epoch (contract requirement)
            prices=tuple(self._closes),
        )