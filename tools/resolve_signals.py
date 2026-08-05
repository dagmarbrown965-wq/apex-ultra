"""APEX ULTRA - W45.2: signal resolution engine (Phase 45, OFFLINE).

For every signal produced by tools/replay_signals.py, walks the merged tick
series FORWARD from the signal's epoch and records whether the take-profit
or the stop-loss barrier was touched first.

Governed by docs/PHASE_45_BOUNDARY_AGREEMENT.md and amendments v0.2/v0.3.
No engine/ files are touched. No costs are applied here -- the 0.2-point
spread is applied at the expectancy stage (W45.3), keeping "what price did"
separate from "what it would have been worth".

Rules fixed in the approved W45.2 micro-plan:
  - Resolution NEVER crosses a contiguous-block boundary. Blocks are
    rebuilt with the same rule replay_signals.py uses: a gap greater than
    EXPECTED_TICK_SECONDS splits the series.
  - Long:  target = entry * 1.02, stop = entry * 0.99
    Short: target = entry * 0.98, stop = entry * 1.01
    (Mirrors DescriptiveBracket's fixed 1%/2% constants; the signal's own
    recorded stop_loss/take_profit values are used directly, not recomputed.)
  - If a single tick is beyond BOTH barriers, the outcome is recorded as
    LOSS. The intra-tick path is unknowable from quote data, so the
    pessimistic assumption is taken deliberately. These cases are counted
    and reported so their influence is visible.
  - If the block ends before either barrier is touched, the outcome is
    UNRESOLVED. Unresolved signals are excluded from the win rate and
    reported separately (agreement: >10% unresolved = compromised sample).

Usage (from the repo root):
    py -m tools.resolve_signals
"""
from __future__ import annotations

import glob
import json
import statistics
import sys
from pathlib import Path

EXPECTED_TICK_SECONDS = 2
OUTPUT_DIR = Path("engine") / "output"
TICK_GLOB = str(OUTPUT_DIR / "ticks_R_100_*.jsonl")
SIGNAL_GLOB = str(OUTPUT_DIR / "replay_signals_*.jsonl")

UNRESOLVED_WARN_FRACTION = 0.10


def _load_ticks() -> list:
    """Merge every tick file, dedupe by epoch, sort oldest-first."""
    paths = sorted(glob.glob(TICK_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no tick files found matching {TICK_GLOB}")
    merged: dict = {}
    for p in paths:
        with open(p, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                merged[int(rec["epoch"])] = float(rec["quote"])
    ordered = sorted(merged.items())
    print(f"merged {len(paths)} tick file(s), {len(ordered)} unique epochs")
    return ordered


def _load_signals() -> list:
    """Load the most recent replay signal journal (largest epoch span)."""
    paths = sorted(glob.glob(SIGNAL_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no signal file found matching {SIGNAL_GLOB}. "
                 "Run tools/replay_signals.py first.")
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
    """Return [(start_idx, end_idx)] inclusive contiguous-block ranges."""
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
    ordered = _load_ticks()
    signals, signal_path = _load_signals()
    blocks = _blocks(ordered)
    print(f"{len(blocks)} contiguous block(s)")

    epochs = [e for e, _ in ordered]
    # epoch -> index, for locating a signal's start position quickly
    index_of = {e: i for i, e in enumerate(epochs)}
    # index -> block number, so a walk knows where its block ends
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
    durations = []

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
        was_ambiguous = False

        for i in range(start_idx + 1, end_idx + 1):
            epoch, quote = ordered[i]
            if direction == "long":
                hit_target = quote >= target
                hit_stop = quote <= stop
            else:
                hit_target = quote <= target
                hit_stop = quote >= stop

            if hit_target and hit_stop:
                # intra-tick path unknowable; pessimistic assumption
                outcome = "LOSS"
                resolved_epoch = epoch
                was_ambiguous = True
                break
            if hit_target:
                outcome = "WIN"
                resolved_epoch = epoch
                break
            if hit_stop:
                outcome = "LOSS"
                resolved_epoch = epoch
                break

        if outcome == "WIN":
            wins += 1
        elif outcome == "LOSS":
            losses += 1
        else:
            unresolved += 1
        if was_ambiguous:
            ambiguous += 1

        seconds = (resolved_epoch - ts) if resolved_epoch is not None else None
        if seconds is not None:
            durations.append(seconds)

        resolutions.append({
            "timestamp": ts,
            "direction": direction,
            "entry_price": entry,
            "stop_loss": stop,
            "take_profit": target,
            "outcome": outcome,
            "resolved_epoch": resolved_epoch,
            "seconds_to_resolve": seconds,
            "block_index": bi,
            "same_tick_ambiguous": was_ambiguous,
        })

    resolved = wins + losses
    win_rate = (wins / resolved) if resolved else 0.0
    unresolved_fraction = (unresolved / len(resolutions)) if resolutions else 0.0

    stem = f"resolutions_{epochs[0]}_{epochs[-1]}"
    res_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(res_path, "w") as f:
        for r in resolutions:
            f.write(json.dumps(r) + "\n")

    summary = {
        "signal_source": signal_path,
        "signals_examined": len(signals),
        "signals_not_in_tick_series": not_in_series,
        "resolutions_written": len(resolutions),
        "resolved": resolved,
        "wins": wins,
        "losses": losses,
        "unresolved": unresolved,
        "unresolved_fraction": round(unresolved_fraction, 4),
        "unresolved_exceeds_threshold": unresolved_fraction > UNRESOLVED_WARN_FRACTION,
        "same_tick_ambiguous_count": ambiguous,
        "win_rate": round(win_rate, 4),
        "median_seconds_to_resolve": (round(statistics.median(durations), 1)
                                      if durations else None),
        "mean_seconds_to_resolve": (round(statistics.fmean(durations), 1)
                                    if durations else None),
        "contiguous_block_count": len(blocks),
        "resolution_path": str(res_path),
        "note": ("No costs applied at this stage. The 0.2-point spread is "
                 "applied in W45.3. Win rate here is pre-cost and carries no "
                 "pass/fail meaning on its own."),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("RESOLUTION SUMMARY")
    for k, v in summary.items():
        if k == "note":
            continue
        print(f"  {k:30s}: {v}")
    print("-" * 64)
    if summary["unresolved_exceeds_threshold"]:
        print("WARNING: unresolved fraction exceeds 10% -- per the agreement "
              "the sample is treated as compromised; more data required.")
    print(f"Resolution file : {res_path}")
    print(f"Summary file    : {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
