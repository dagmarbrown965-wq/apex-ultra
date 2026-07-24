"""APEX ULTRA - W45.1: offline signal replay (Phase 45, READ-ONLY / OFFLINE).

Merges all engine/output/ticks_R_100_*.jsonl files, deduplicates by epoch,
and drives the REAL EmaCross(9/21) -> SimpleRegime -> DescriptiveBracket ->
build_signal chain over the resulting series -- the identical classes the
live runner uses, imported verbatim, never reimplemented or modified.

Governed by docs/PHASE_45_BOUNDARY_AGREEMENT.md and its amendments v0.2/v0.3.
No engine/ files are touched. Produces a signal journal in the same v1.0
shape as live journals, plus a summary describing the merge, contiguity,
and generation.

Design notes (decided in the W45.1 micro-plan, approved before this file
was written):
  - ReplayFeed mirrors LiveReadonlyFeed's contract exactly: maxlen=25
    buffer, WARMUP_CLOSES=20 gate, duplicate-epoch skip. It does NOT
    reimplement any strategy math.
  - MarketSnapshot.timestamp is passed as the numeric epoch (int/float),
    matching what live signals actually carried (verified in committed
    journals), not the dataclass's stale `str` type hint. This is a
    replication-of-reality choice, not an engine fix, and engine/ is not
    touched to "correct" it.
  - Contiguous blocks are computed by splitting the merged series wherever
    the gap between consecutive epochs exceeds EXPECTED_TICK_SECONDS.
    Independent-window counting (Amendment v0.2/v0.3) is computed PER
    BLOCK, never across a gap.

Usage (from the repo root):
    py -m tools.replay_signals
"""
from __future__ import annotations

import glob
import json
import sys
from collections import deque
from pathlib import Path

from engine.feed.base import MarketSnapshot
from engine.strategy.ema_cross import EmaCross
from engine.regime.simple import SimpleRegime
from engine.risk.descriptive_bracket import DescriptiveBracket
from engine.assemble.signal_builder import build_signal

SYMBOL = "R_100"
WARMUP_CLOSES = 20     # matches engine/feed/live_readonly.py WARMUP_CLOSES
BUFFER_MAXLEN = 25     # matches engine/feed/live_readonly.py BUFFER_MAXLEN
EXPECTED_TICK_SECONDS = 2
RESOLUTION_SECONDS = 105 * 60  # ~105 min expected time to hit +2%/-1% barrier

OUTPUT_DIR = Path("engine") / "output"
TICK_GLOB = str(OUTPUT_DIR / "ticks_R_100_*.jsonl")


class ReplayFeed:
    """Offline stand-in for LiveReadonlyFeed. Same buffer contract, same
    warmup gate, same duplicate-epoch skip. Reads from a static series
    instead of the network. Never touches engine/feed/live_readonly.py."""

    def __init__(self) -> None:
        self._closes: deque = deque(maxlen=BUFFER_MAXLEN)
        self._last_epoch = None
        self.ticks_seen = 0
        self.ticks_duplicate = 0

    def push(self, epoch: int, quote: float) -> bool:
        self.ticks_seen += 1
        if self._last_epoch is not None and epoch == self._last_epoch:
            self.ticks_duplicate += 1
            return False
        self._closes.append(float(quote))
        self._last_epoch = epoch
        return True

    @property
    def depth(self) -> int:
        return len(self._closes)

    def snapshot(self, symbol: str, epoch) -> MarketSnapshot:
        # NOTE: timestamp passed as the numeric epoch (int), matching what
        # live signals actually carried, not the dataclass's `str` hint.
        return MarketSnapshot(symbol=symbol, timestamp=epoch,
                               prices=tuple(self._closes))


def _load_and_merge() -> list:
    """Read every ticks_R_100_*.jsonl file, dedupe by epoch, sort. Returns
    [(epoch, quote), ...] oldest-first. Disagreements on quote for the same
    epoch across files are reported as warnings, never silently resolved."""
    paths = sorted(glob.glob(TICK_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no tick files found matching {TICK_GLOB}")

    merged: dict = {}
    conflicts = 0
    for p in paths:
        with open(p, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                epoch = int(rec["epoch"])
                quote = float(rec["quote"])
                if epoch in merged and merged[epoch] != quote:
                    conflicts += 1
                merged[epoch] = quote

    ordered = sorted(merged.items())
    print(f"merged {len(paths)} file(s), {len(ordered)} unique epochs"
          f"{f', {conflicts} quote conflicts (kept last-seen)' if conflicts else ''}")
    return ordered, paths


def _contiguous_blocks(ordered: list) -> list:
    """Split [(epoch, quote), ...] into contiguous blocks wherever the gap
    exceeds EXPECTED_TICK_SECONDS. Returns a list of (start_idx, end_idx)
    inclusive index ranges into `ordered`."""
    if not ordered:
        return []
    blocks = []
    start = 0
    for i in range(1, len(ordered)):
        if ordered[i][0] - ordered[i - 1][0] > EXPECTED_TICK_SECONDS:
            blocks.append((start, i - 1))
            start = i
    blocks.append((start, len(ordered) - 1))
    return blocks


def run() -> int:
    ordered, source_files = _load_and_merge()
    blocks = _contiguous_blocks(ordered)

    total_span = ordered[-1][0] - ordered[0][0] if len(ordered) > 1 else 0
    block_summaries = []
    total_independent_windows = 0.0
    for (s, e) in blocks:
        span = ordered[e][0] - ordered[s][0]
        windows = span / RESOLUTION_SECONDS
        total_independent_windows += windows
        block_summaries.append({
            "start_epoch": ordered[s][0],
            "end_epoch": ordered[e][0],
            "span_seconds": span,
            "tick_count": e - s + 1,
            "independent_windows": round(windows, 2),
        })

    print(f"{len(blocks)} contiguous block(s); "
          f"~{total_independent_windows:.1f} independent windows total")

    strategy = EmaCross()          # fresh instance: fresh per-session state
    regime_detector = SimpleRegime()
    risk = DescriptiveBracket()
    feed = ReplayFeed()

    signals = []
    warmup_excluded = 0
    for epoch, quote in ordered:
        accepted = feed.push(epoch, quote)
        if not accepted:
            continue
        if feed.depth < WARMUP_CLOSES:
            warmup_excluded += 1
            continue
        snap = feed.snapshot(SYMBOL, epoch)
        decision = strategy.evaluate(snap)
        if decision is None:
            continue
        regime = regime_detector.classify(snap)
        bracket = risk.bracket(decision, snap)
        signal = build_signal(decision, regime, bracket, snap, strategy.name)
        signals.append(signal)

    if not signals:
        print("\nNo signals generated. Nothing written.")
        return 1

    stem = f"replay_signals_{ordered[0][0]}_{ordered[-1][0]}"
    sig_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(sig_path, "w") as f:
        for s in signals:
            f.write(json.dumps(s) + "\n")

    summary = {
        "source_files": [str(p) for p in source_files],
        "unique_ticks": len(ordered),
        "ticks_duplicate_in_replay": feed.ticks_duplicate,
        "first_epoch": ordered[0][0],
        "last_epoch": ordered[-1][0],
        "total_span_seconds": total_span,
        "total_span_days": round(total_span / 86400.0, 3),
        "contiguous_block_count": len(blocks),
        "contiguous_blocks": block_summaries,
        "total_independent_windows": round(total_independent_windows, 2),
        "warmup_excluded_ticks": warmup_excluded,
        "signals_generated": len(signals),
        "signal_path": str(sig_path),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("REPLAY SUMMARY")
    for k, v in summary.items():
        if k == "contiguous_blocks":
            continue
        print(f"  {k:26s}: {v}")
    print("-" * 64)
    print(f"Signal file  : {sig_path}")
    print(f"Summary file : {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
