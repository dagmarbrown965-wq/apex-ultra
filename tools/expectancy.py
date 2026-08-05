"""APEX ULTRA - W45.3: expectancy (Phase 45, OFFLINE, arithmetic only).

Reads the W45.2 resolutions journal, applies the empirically-established
0.2-point round-trip spread, and computes expectancy under both position
policies defined in docs/PHASE_45_AMENDMENT_V0_2.md.

Governed by docs/PHASE_45_BOUNDARY_AGREEMENT.md and amendments v0.2/v0.3.
No engine/ imports, no network, no new data. Pure arithmetic over data
already committed.

Policies (roles as set by Amendment v0.2):
  PRIMARY (decisive)  : every resolved signal counted independently.
  SECONDARY (indicative): one position at a time -- a signal is taken only
                          if no earlier trade is still open.

Cost model: spread is 0.2 price points, paid round-trip, expressed per
trade as a percentage of that trade's own entry price. Net outcomes:
    WIN  = +2.0% - cost_pct
    LOSS = -1.0% - cost_pct

Pre-committed falsification criteria (locked before any data existed):
    n >= 1,000 resolved signals AND win rate >= 38%
Break-even after costs is ~34.5%; a driftless random walk with barriers at
-1% and +2% produces ~33.3% by construction.

Usage (from the repo root):
    py -m tools.expectancy
"""
from __future__ import annotations

import glob
import json
import math
import sys
from pathlib import Path

OUTPUT_DIR = Path("engine") / "output"
RESOLUTION_GLOB = str(OUTPUT_DIR / "resolutions_*.jsonl")

SPREAD_POINTS = 0.2
TARGET_PCT = 2.0
STOP_PCT = 1.0

REQUIRED_N = 1000
REQUIRED_WIN_RATE = 0.38
BREAK_EVEN_AFTER_COSTS = 0.345


def _load_resolutions() -> tuple:
    paths = sorted(glob.glob(RESOLUTION_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no resolutions file matching {RESOLUTION_GLOB}. "
                 "Run tools/resolve_signals.py first.")
    path = paths[-1]
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    print(f"loaded {len(rows)} resolution records from {path}")
    return rows, path


def _net_pct(outcome: str, entry: float) -> float:
    cost_pct = (SPREAD_POINTS / entry) * 100.0
    if outcome == "WIN":
        return TARGET_PCT - cost_pct
    return -STOP_PCT - cost_pct


def _stats(trades: list) -> dict:
    """trades = [(outcome, net_pct, block_index)] for resolved trades only."""
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    wins = sum(1 for o, _, _ in trades if o == "WIN")
    losses = n - wins
    win_rate = wins / n
    nets = [p for _, p, _ in trades]
    expectancy = sum(nets) / n
    total_return = sum(nets)

    # naive binomial standard error on the win rate
    se = math.sqrt(win_rate * (1.0 - win_rate) / n)
    naive_lo = win_rate - 1.96 * se
    naive_hi = win_rate + 1.96 * se

    # block-based estimate: treat each contiguous block's win rate as one
    # observation, since overlapping trades inside a block share a price path
    by_block: dict = {}
    for o, _, b in trades:
        d = by_block.setdefault(b, [0, 0])
        d[1] += 1
        if o == "WIN":
            d[0] += 1
    block_rates = [w / t for w, t in by_block.values() if t > 0]
    if len(block_rates) > 1:
        mean_b = sum(block_rates) / len(block_rates)
        var_b = sum((r - mean_b) ** 2 for r in block_rates) / (len(block_rates) - 1)
        se_b = math.sqrt(var_b / len(block_rates))
        block_lo = mean_b - 1.96 * se_b
        block_hi = mean_b + 1.96 * se_b
    else:
        mean_b = block_rates[0] if block_rates else None
        block_lo = block_hi = None

    return {
        "trades": n,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4),
        "expectancy_pct_per_trade": round(expectancy, 4),
        "total_return_pct": round(total_return, 2),
        "naive_ci95_low": round(naive_lo, 4),
        "naive_ci95_high": round(naive_hi, 4),
        "blocks_used": len(block_rates),
        "block_mean_win_rate": (round(mean_b, 4) if mean_b is not None else None),
        "block_ci95_low": (round(block_lo, 4) if block_lo is not None else None),
        "block_ci95_high": (round(block_hi, 4) if block_hi is not None else None),
    }


def run() -> int:
    rows, source = _load_resolutions()

    # PRIMARY: every resolved signal, independently
    primary = []
    for r in rows:
        if r["outcome"] not in ("WIN", "LOSS"):
            continue
        primary.append((r["outcome"], _net_pct(r["outcome"], float(r["entry_price"])),
                        r["block_index"]))

    # SECONDARY: one position at a time, chronological
    secondary = []
    busy_until = None
    for r in sorted(rows, key=lambda x: x["timestamp"]):
        if r["outcome"] not in ("WIN", "LOSS"):
            continue
        ts = r["timestamp"]
        if busy_until is not None and ts < busy_until:
            continue
        secondary.append((r["outcome"], _net_pct(r["outcome"], float(r["entry_price"])),
                          r["block_index"]))
        busy_until = r["resolved_epoch"]

    p = _stats(primary)
    s = _stats(secondary)

    n_ok = p.get("trades", 0) >= REQUIRED_N
    wr_ok = p.get("win_rate", 0.0) >= REQUIRED_WIN_RATE

    summary = {
        "resolution_source": source,
        "cost_model": {
            "spread_points": SPREAD_POINTS,
            "applied": "round-trip, as pct of each trade's own entry price",
            "win_gross_pct": TARGET_PCT,
            "loss_gross_pct": -STOP_PCT,
            "break_even_win_rate_after_costs": BREAK_EVEN_AFTER_COSTS,
        },
        "primary_every_signal": p,
        "secondary_one_at_a_time": s,
        "pre_committed_criteria": {
            "required_resolved_signals": REQUIRED_N,
            "required_win_rate": REQUIRED_WIN_RATE,
            "resolved_signals_met": n_ok,
            "win_rate_met": wr_ok,
            "verdict": "PASS" if (n_ok and wr_ok) else "FAIL",
        },
        "note": ("Criteria were locked before any data was collected. "
                 "Per the agreement, a negative result is accepted as a "
                 "finding; re-tuning EMA periods, bracket ratios, symbol, "
                 "or post-hoc signal filters is forbidden."),
    }

    stem = Path(source).stem.replace("resolutions_", "expectancy_")
    out_path = OUTPUT_DIR / f"{stem}.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("=" * 64)
    print("EXPECTANCY - PRIMARY (every signal, decisive)")
    print("=" * 64)
    for k, v in p.items():
        print(f"  {k:28s}: {v}")
    print()
    print("=" * 64)
    print("EXPECTANCY - SECONDARY (one at a time, indicative only)")
    print("=" * 64)
    for k, v in s.items():
        print(f"  {k:28s}: {v}")
    print()
    print("=" * 64)
    print("PRE-COMMITTED CRITERIA")
    print("=" * 64)
    c = summary["pre_committed_criteria"]
    print(f"  resolved >= {REQUIRED_N:<6}          : {c['resolved_signals_met']}")
    print(f"  win rate >= {REQUIRED_WIN_RATE:<6}        : {c['win_rate_met']}")
    print(f"  break-even after costs      : {BREAK_EVEN_AFTER_COSTS}")
    print(f"  VERDICT                     : {c['verdict']}")
    print("=" * 64)
    print(f"Summary file : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
