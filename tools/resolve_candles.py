"""APEX ULTRA - W46.2: signal resolution over EUR/USD candles (Phase 46, OFFLINE).

For every signal produced by tools/replay_candles.py, walks the candle series
FORWARD from the signal's bar and records whether the take-profit or the
stop-loss barrier was touched first.

Governed by docs/PHASE_46_BOUNDARY_AGREEMENT.md. No engine/ files touched.
No costs applied here -- the 0.01% spread is applied at the expectancy
stage (W46.3), keeping "what price did" separate from "what it was worth".

Improvement over Phase 45's tick resolution: OHLC gives each bar's true
intra-bar extremes, so a barrier is detected when the bar's HIGH or LOW
reaches it, not merely when a sampled quote happened to be beyond it. A
bar whose high touches the target counts as a hit even if it closed below
-- which is what actually happens in a real market.

Rules fixed in the approved W46.2 micro-plan:
  - Resolution NEVER crosses a contiguous-block boundary. Blocks split
    wherever the epoch gap exceeds GRANULARITY, i.e. at every weekend.
  - Long : target hit if high >= take_profit; stop hit if low  <= stop_loss
    Short: target hit if low  <= take_profit; stop hit if high >= stop_loss
  - If a single bar's range spans BOTH barriers, the outcome is recorded
    as LOSS. The intra-bar path is unknowable from OHLC, so the
    pessimistic assumption is taken deliberately. These cases are counted
    and reported; on 15-minute bars with a 0.2%/0.4% bracket they are
    expected to be materially more common than the zero seen in Phase 45.
    If the count is large, that is a LIMITATION TO DISCLOSE, not a rule
    to revise after the fact.
  - If the block ends before either barrier is touched, the outcome is
    UNRESOLVED, excluded from the win rate, and reported separately.
    Agreement: >10% unresolved = compromised sample.

Usage (from the repo root):
    py -m tools.resolve_candles
"""
from __future__ import annotations

import glob
import json
import statistics
import sys
from pathlib import Path

SYMBOL = "frxEURUSD"
GRANULARITY = 900
OUTPUT_DIR = Path("engine") / "output"
CANDLE_GLOB = str(OUTPUT_DIR / f"candles_{SYMBOL}_{GRANULARITY}_*.jsonl")
SIGNAL_GLOB = str(OUTPUT_DIR / "replay_candles_*.jsonl")

UNRESOLVED_WARN_FRACTION = 0.10


def _load_candles() -> list:
    paths = sorted(glob.glob(CANDLE_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no candle file matching {CANDLE_GLOB}")
    merged: dict = {}
    for p in paths:
        with open(p, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                k = json.loads(line)
                merged[int(k["epoch"])] = (float(k["high"]), float(k["low"]))
    ordered = sorted(merged.items())
    print(f"merged {len(paths)} candle file(s), {len(ordered)} unique candles")
    return ordered


def _load_signals() -> tuple:
    paths = sorted(glob.glob(SIGNAL_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no signal file matching {SIGNAL_GLOB}. "
                 "Run tools/replay_candles.py first.")
    path = paths[-1]
    signals = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                signals.append(json.loads(line))
    print(f"loaded {len(signals)} signals from {path}")
    return signals, path


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
    ordered = _load_candles()
    signals, signal_path = _load_signals()
    blocks = _blocks(ordered)
    print(f"{len(blocks)} contiguous block(s)")

    epochs = [e for e, _ in ordered]
    index_of = {e: i for i, e in enumerate(epochs)}
    block_of = {}
    block_end = {}
    for bi, (s, e) in enumerate(blocks):
        for i in range(s, e + 1):
            block_of[i] = bi
        block_end[bi] = e

    resolutions = []
    wins = losses = unresolved = 0
    ambiguous = 0
    not_in_series = 0
    bars_to_resolve = []

    for sig in signals:
        ts = int(sig["timestamp"])
        entry = float(sig["entry_price"])
        stop = float(sig["stop_loss"])
        target = float(sig["take_profit"])
        direction = sig["direction"]

        start_idx = index_of.get(ts)
        if start_idx is None:
            not_in_series += 1
            continue

        bi = block_of[start_idx]
        end_idx = block_end[bi]

        outcome = "UNRESOLVED"
        resolved_epoch = None
        bars = None
        was_ambiguous = False

        for i in range(start_idx + 1, end_idx + 1):
            epoch, (high, low) = ordered[i]
            if direction == "long":
                hit_target = high >= target
                hit_stop = low <= stop
            else:
                hit_target = low <= target
                hit_stop = high >= stop

            if hit_target and hit_stop:
                outcome = "LOSS"          # pessimistic; intra-bar path unknown
                resolved_epoch = epoch
                bars = i - start_idx
                was_ambiguous = True
                break
            if hit_target:
                outcome = "WIN"
                resolved_epoch = epoch
                bars = i - start_idx
                break
            if hit_stop:
                outcome = "LOSS"
                resolved_epoch = epoch
                bars = i - start_idx
                break

        if outcome == "WIN":
            wins += 1
        elif outcome == "LOSS":
            losses += 1
        else:
            unresolved += 1
        if was_ambiguous:
            ambiguous += 1
        if bars is not None:
            bars_to_resolve.append(bars)

        resolutions.append({
            "timestamp": ts,
            "direction": direction,
            "entry_price": entry,
            "stop_loss": stop,
            "take_profit": target,
            "outcome": outcome,
            "resolved_epoch": resolved_epoch,
            "bars_to_resolve": bars,
            "seconds_to_resolve": (bars * GRANULARITY) if bars else None,
            "block_index": bi,
            "same_bar_ambiguous": was_ambiguous,
        })

    resolved = wins + losses
    win_rate = (wins / resolved) if resolved else 0.0
    unresolved_fraction = (unresolved / len(resolutions)) if resolutions else 0.0
    ambiguous_fraction = (ambiguous / resolved) if resolved else 0.0

    stem = f"resolutions_candles_{epochs[0]}_{epochs[-1]}"
    res_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(res_path, "w") as f:
        for r in resolutions:
            f.write(json.dumps(r) + "\n")

    summary = {
        "symbol": SYMBOL,
        "granularity": GRANULARITY,
        "signal_source": signal_path,
        "signals_examined": len(signals),
        "signals_not_in_series": not_in_series,
        "resolutions_written": len(resolutions),
        "resolved": resolved,
        "wins": wins,
        "losses": losses,
        "unresolved": unresolved,
        "unresolved_fraction": round(unresolved_fraction, 4),
        "unresolved_exceeds_threshold": unresolved_fraction > UNRESOLVED_WARN_FRACTION,
        "same_bar_ambiguous_count": ambiguous,
        "same_bar_ambiguous_fraction": round(ambiguous_fraction, 4),
        "win_rate_pre_cost": round(win_rate, 4),
        "median_bars_to_resolve": (statistics.median(bars_to_resolve)
                                   if bars_to_resolve else None),
        "mean_bars_to_resolve": (round(statistics.fmean(bars_to_resolve), 1)
                                 if bars_to_resolve else None),
        "median_hours_to_resolve": (round(statistics.median(bars_to_resolve)
                                          * GRANULARITY / 3600.0, 2)
                                    if bars_to_resolve else None),
        "contiguous_block_count": len(blocks),
        "resolution_path": str(res_path),
        "note": ("No costs applied at this stage; the 0.01% spread is applied "
                 "in W46.3. Ambiguous bars (range spanning both barriers) are "
                 "recorded as LOSS by the pre-committed pessimistic rule."),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("RESOLUTION SUMMARY")
    for k, v in summary.items():
        if k == "note":
            continue
        print(f"  {k:32s}: {v}")
    print("-" * 64)
    if summary["unresolved_exceeds_threshold"]:
        print("WARNING: unresolved fraction exceeds 10% -- per the agreement "
              "the sample is treated as compromised.")
    if ambiguous_fraction > 0.10:
        print(f"NOTE: {ambiguous_fraction:.1%} of resolved signals were "
              "same-bar ambiguous and recorded as LOSS by the pessimistic "
              "rule. This biases the result downward and MUST be disclosed "
              "as a limitation. It is not grounds for revising the rule.")
    print(f"Resolution file : {res_path}")
    print(f"Summary file    : {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
