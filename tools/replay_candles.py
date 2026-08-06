"""APEX ULTRA - W46.1: signal generation over EUR/USD candles (Phase 46, OFFLINE).

Drives the REAL EmaCross(9/21) -> SimpleRegime -> DescriptiveBracket ->
build_signal chain over the 15-minute OHLC series fetched by W46.0. The
strategy, regime detector, bracket class, and signal builder are imported
verbatim from engine/ -- never reimplemented, never modified.

Governed by docs/PHASE_46_BOUNDARY_AGREEMENT.md.

The ONE declared behavioural difference from Phase 45, specified in the
agreement before any data was evaluated:

    DescriptiveBracket is instantiated with stop_pct=0.002 and
    target_pct=0.004 (0.2% / 0.4%) instead of its R_100 defaults of
    0.01 / 0.02. This uses the class's EXISTING constructor parameters;
    the class itself is untouched. The 1:2 ratio is preserved. Rationale
    (recorded in the agreement): EUR/USD moves ~0.0353% per 15-minute
    bar, so a 1% stop would take days to resolve; 0.2%/0.4% resolves in
    ~8 hours, matching Phase 45's trade cadence.

Design decisions from the approved micro-plan:
  - CLOSES drive the strategy, exactly as the live feed did. Highs and
    lows are carried through for W46.2 resolution but are never shown to
    EmaCross -- the strategy's inputs stay identical in kind to Phase 45.
  - Candles split into contiguous blocks wherever the epoch gap exceeds
    the granularity (i.e. at every weekend close).
  - A FRESH EmaCross instance is created per block. Its docstring
    specifies one instance per session; carrying EMA state across a
    ~51-hour market closure would be dishonest. Cost: the first 20 bars
    of each block produce no signals.

Usage (from the repo root):
    py -m tools.replay_candles
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

SYMBOL = "frxEURUSD"
GRANULARITY = 900
WARMUP_CLOSES = 20      # matches engine/feed/live_readonly.py
BUFFER_MAXLEN = 25      # matches engine/feed/live_readonly.py
STOP_PCT = 0.002        # 0.2%, per the Phase 46 agreement
TARGET_PCT = 0.004      # 0.4%, per the Phase 46 agreement

OUTPUT_DIR = Path("engine") / "output"
CANDLE_GLOB = str(OUTPUT_DIR / f"candles_{SYMBOL}_{GRANULARITY}_*.jsonl")


class CandleReplayFeed:
    """Offline feed over stored candles. Mirrors ReplayFeed's contract:
    same buffer length, same warmup gate. Closes only -- highs and lows
    are held by the caller for resolution, not exposed to the strategy."""

    def __init__(self) -> None:
        self._closes: deque = deque(maxlen=BUFFER_MAXLEN)

    def reset(self) -> None:
        self._closes.clear()

    def push(self, close: float) -> None:
        self._closes.append(float(close))

    @property
    def depth(self) -> int:
        return len(self._closes)

    def snapshot(self, symbol: str, epoch: int) -> MarketSnapshot:
        # timestamp carried as the numeric epoch, matching live journals
        return MarketSnapshot(symbol=symbol, timestamp=epoch,
                              prices=tuple(self._closes))


def _load_candles() -> tuple:
    paths = sorted(glob.glob(CANDLE_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no candle file matching {CANDLE_GLOB}. "
                 "Run tools/fetch_candles.py first.")
    merged: dict = {}
    for p in paths:
        with open(p, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                k = json.loads(line)
                merged[int(k["epoch"])] = (float(k["open"]), float(k["high"]),
                                           float(k["low"]), float(k["close"]))
    ordered = sorted(merged.items())
    print(f"merged {len(paths)} candle file(s), {len(ordered)} unique candles")
    return ordered, paths


def _blocks(ordered: list) -> list:
    if not ordered:
        return []
    blocks = []
    start = 0
    for i in range(1, len(ordered)):
        if ordered[i][0] - ordered[i - 1][0] > GRANULARITY:
            blocks.append((start, i - 1))
            start = i
    blocks.append((start, len(ordered) - 1))
    return blocks


def run() -> int:
    ordered, source_files = _load_candles()
    blocks = _blocks(ordered)
    print(f"{len(blocks)} contiguous block(s) "
          f"(weekend closures split the series)")

    regime_detector = SimpleRegime()
    risk = DescriptiveBracket(stop_pct=STOP_PCT, target_pct=TARGET_PCT)

    signals = []
    warmup_excluded = 0
    per_block = []

    for bi, (s, e) in enumerate(blocks):
        strategy = EmaCross()          # fresh state per block, per micro-plan
        feed = CandleReplayFeed()
        count_before = len(signals)

        for i in range(s, e + 1):
            epoch, (o, h, l, c) = ordered[i]
            feed.push(c)
            if feed.depth < WARMUP_CLOSES:
                warmup_excluded += 1
                continue
            snap = feed.snapshot(SYMBOL, epoch)
            decision = strategy.evaluate(snap)
            if decision is None:
                continue
            regime = regime_detector.classify(snap)
            bracket = risk.bracket(decision, snap)
            signals.append(build_signal(decision, regime, bracket, snap,
                                        strategy.name))

        per_block.append({
            "block_index": bi,
            "start_epoch": ordered[s][0],
            "end_epoch": ordered[e][0],
            "candles": e - s + 1,
            "signals": len(signals) - count_before,
        })

    if not signals:
        print("\nNo signals generated. Nothing written.")
        return 1

    stem = f"replay_candles_{ordered[0][0]}_{ordered[-1][0]}"
    sig_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(sig_path, "w") as f:
        for sig in signals:
            f.write(json.dumps(sig) + "\n")

    span = ordered[-1][0] - ordered[0][0]
    summary = {
        "symbol": SYMBOL,
        "granularity": GRANULARITY,
        "source_files": [str(p) for p in source_files],
        "candles": len(ordered),
        "first_epoch": ordered[0][0],
        "last_epoch": ordered[-1][0],
        "span_days": round(span / 86400.0, 3),
        "contiguous_block_count": len(blocks),
        "warmup_excluded_candles": warmup_excluded,
        "signals_generated": len(signals),
        "signals_per_1000_candles": round(len(signals) / len(ordered) * 1000, 1),
        "bracket_stop_pct": STOP_PCT,
        "bracket_target_pct": TARGET_PCT,
        "strategy_state": "fresh EmaCross instance per contiguous block",
        "signal_path": str(sig_path),
        "per_block": per_block,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("REPLAY SUMMARY")
    for k, v in summary.items():
        if k in ("per_block", "source_files"):
            continue
        print(f"  {k:28s}: {v}")
    print("-" * 64)
    print(f"Signal file  : {sig_path}")
    print(f"Summary file : {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
