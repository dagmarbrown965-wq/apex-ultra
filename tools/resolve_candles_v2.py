"""APEX ULTRA - W46.2 v2: cross-weekend signal resolution (Phase 46, OFFLINE).

Supersedes the block-bounded resolution in tools/resolve_candles.py, which
remains committed and runnable as the artefact behind the pre-amendment
result (32.29% pre-cost, 17.84% unresolved).

Governed by docs/PHASE_46_BOUNDARY_AGREEMENT.md as amended by
docs/PHASE_46_AMENDMENT_V0_2.md. No engine/ files touched. No costs
applied here -- the 0.01% spread is applied in W46.3.

WHAT CHANGED FROM v1, and why (amendment v0.2):
  v1 refused to resolve a signal past its contiguous block, so every trade
  open at a Friday close was truncated as UNRESOLVED. That rule was
  inherited from Phase 45, where blocks were collection gaps in a 24/7
  synthetic instrument. It does not describe a market that closes: a real
  position held on Friday reopens Monday. 17.84% of signals were being
  discarded for modelling something that does not happen.

  v2 walks forward through the ENTIRE chronological series. Weekend gaps
  are traversed. A signal is UNRESOLVED only if the dataset itself ends
  first.

GAP-THROUGH HANDLING (amendment v0.2, Amendment 2):
  A weekend gap can open beyond a barrier -- Monday's first bar may
  already be past Friday's stop or target.
    - Such a signal RESOLVES at that bar, in the barrier's direction.
    - The outcome is recorded at the BARRIER price, not the gap price, so
      W46.3's arithmetic stays fixed at +0.4% / -0.2% gross.
    - Gap-throughs are COUNTED and reported separately.
  Disclosed limitation: in reality a stop gapped through fills worse than
  -0.2% and a target gapped through fills better than +0.4%. If the
  gap-through count exceeds 2% of resolved signals, the phase close must
  state that measured expectancy is optimistic relative to real fills.

UNCHANGED FROM v1:
  - Same-bar ambiguity (bar range spans both barriers) records LOSS,
    pessimistic, counted and reported.
  - Long : target if high >= take_profit; stop if low  <= stop_loss
    Short: target if low  <= take_profit; stop if high >= stop_loss

Usage (from the repo root):
    py -m tools.resolve_candles_v2
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
GAP_THROUGH_DISCLOSE_FRACTION = 0.02


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
                merged[int(k["epoch"])] = (float(k["open"]), float(k["high"]),
                                           float(k["low"]))
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


def _block_index_map(ordered: list) -> dict:
    """Blocks are still computed, for REPORTING only. Resolution no longer
    stops at a block edge (that is the whole point of amendment v0.2)."""
    block_of = {0: 0} if ordered else {}
    bi = 0
    for i in range(1, len(ordered)):
        if ordered[i][0] - ordered[i - 1][0] > GRANULARITY:
            bi += 1
        block_of[i] = bi
    return block_of, bi + 1 if ordered else 0


def run() -> int:
    ordered = _load_candles()
    signals, signal_path = _load_signals()
    block_of, block_count = _block_index_map(ordered)
    print(f"{block_count} contiguous block(s) -- resolution now crosses them")

    epochs = [e for e, _ in ordered]
    index_of = {e: i for i, e in enumerate(epochs)}
    n = len(ordered)

    resolutions = []
    wins = losses = unresolved = 0
    ambiguous = 0
    gap_through = 0
    not_in_series = 0
    bars_to_resolve = []
    weekends_crossed_total = 0

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

        outcome = "UNRESOLVED"
        resolved_epoch = None
        bars = None
        was_ambiguous = False
        was_gap_through = False
        weekends_crossed = 0

        for i in range(start_idx + 1, n):          # crosses block edges
            epoch, (o, high, low) = ordered[i]
            gapped = (epoch - ordered[i - 1][0]) > GRANULARITY
            if gapped:
                weekends_crossed += 1

            if direction == "long":
                hit_target = high >= target
                hit_stop = low <= stop
                opened_past_target = gapped and o >= target
                opened_past_stop = gapped and o <= stop
            else:
                hit_target = low <= target
                hit_stop = high >= stop
                opened_past_target = gapped and o <= target
                opened_past_stop = gapped and o >= stop

            if hit_target and hit_stop:
                outcome = "LOSS"       # pessimistic; intra-bar path unknown
                resolved_epoch = epoch
                bars = i - start_idx
                was_ambiguous = True
                was_gap_through = opened_past_target or opened_past_stop
                break
            if hit_target:
                outcome = "WIN"
                resolved_epoch = epoch
                bars = i - start_idx
                was_gap_through = opened_past_target
                break
            if hit_stop:
                outcome = "LOSS"
                resolved_epoch = epoch
                bars = i - start_idx
                was_gap_through = opened_past_stop
                break

        if outcome == "WIN":
            wins += 1
        elif outcome == "LOSS":
            losses += 1
        else:
            unresolved += 1
        if was_ambiguous:
            ambiguous += 1
        if was_gap_through:
            gap_through += 1
        if bars is not None:
            bars_to_resolve.append(bars)
            weekends_crossed_total += weekends_crossed

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
            "block_index": block_of.get(start_idx),
            "weekends_crossed": weekends_crossed if bars is not None else None,
            "same_bar_ambiguous": was_ambiguous,
            "gap_through": was_gap_through,
        })

    resolved = wins + losses
    win_rate = (wins / resolved) if resolved else 0.0
    unresolved_fraction = (unresolved / len(resolutions)) if resolutions else 0.0
    ambiguous_fraction = (ambiguous / resolved) if resolved else 0.0
    gap_fraction = (gap_through / resolved) if resolved else 0.0

    stem = f"resolutions_candles_v2_{epochs[0]}_{epochs[-1]}"
    res_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(res_path, "w") as f:
        for r in resolutions:
            f.write(json.dumps(r) + "\n")

    summary = {
        "symbol": SYMBOL,
        "granularity": GRANULARITY,
        "resolution_rule": "cross-weekend (amendment v0.2)",
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
        "gap_through_count": gap_through,
        "gap_through_fraction": round(gap_fraction, 4),
        "gap_through_requires_disclosure": gap_fraction > GAP_THROUGH_DISCLOSE_FRACTION,
        "win_rate_pre_cost": round(win_rate, 4),
        "median_bars_to_resolve": (statistics.median(bars_to_resolve)
                                   if bars_to_resolve else None),
        "mean_bars_to_resolve": (round(statistics.fmean(bars_to_resolve), 1)
                                 if bars_to_resolve else None),
        "median_hours_to_resolve": (round(statistics.median(bars_to_resolve)
                                          * GRANULARITY / 3600.0, 2)
                                    if bars_to_resolve else None),
        "weekend_crossings_total": weekends_crossed_total,
        "contiguous_block_count": block_count,
        "resolution_path": str(res_path),
        "pre_amendment_reference": {
            "rule": "block-bounded (v0.1)",
            "resolved": 1087,
            "win_rate_pre_cost": 0.3229,
            "unresolved_fraction": 0.1784,
        },
        "note": ("Outcomes are recorded at barrier prices even when a gap "
                 "opened past the barrier, so W46.3 arithmetic stays fixed. "
                 "Gap-throughs are counted; see amendment v0.2 Amendment 2."),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("RESOLUTION SUMMARY (v2, cross-weekend)")
    for k, v in summary.items():
        if k in ("note", "pre_amendment_reference"):
            continue
        print(f"  {k:32s}: {v}")
    print("-" * 64)
    print("  PRE-AMENDMENT REFERENCE (v1, block-bounded):")
    print(f"    resolved 1087, win rate 0.3229, unresolved 17.84%")
    print("-" * 64)
    if summary["unresolved_exceeds_threshold"]:
        print("WARNING: unresolved fraction still exceeds 10%.")
    if summary["gap_through_requires_disclosure"]:
        print(f"NOTE: gap-throughs are {gap_fraction:.1%} of resolved signals "
              "(>2%). Measured expectancy is OPTIMISTIC relative to real "
              "fills; this must be disclosed in the phase close.")
    print(f"Resolution file : {res_path}")
    print(f"Summary file    : {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
