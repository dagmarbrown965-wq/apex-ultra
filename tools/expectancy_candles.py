"""APEX ULTRA - W46.3: expectancy (Phase 46, OFFLINE, arithmetic only).

Reads the W46.2 v2 cross-weekend resolutions journal, applies the
EUR/USD spread, and computes expectancy under both position policies.

Governed by docs/PHASE_46_BOUNDARY_AGREEMENT.md as amended by
docs/PHASE_46_AMENDMENT_V0_2.md. No engine/ imports, no network, no new
data. Pure arithmetic over data already committed.

Policies:
  PRIMARY (decisive)   : every resolved signal counted independently.
  SECONDARY (indicative): one position at a time.

Cost model (measured 2026-08-05 from 12 live bid/ask samples):
  observed spread 0.0069%-0.0087% round-trip; the agreement adopts
  0.01% as a conservative stated assumption, above the worst observed.
    WIN  = +0.4% - 0.01% = +0.39%
    LOSS = -0.2% - 0.01% = -0.21%
    Break-even win rate = 0.21 / 0.60 = 35.0%

Pre-committed falsification criteria (locked 2026-08-05, before any
EUR/USD evaluation data existed):
    >= 1,000 resolved signals
    >= 150 independent resolution windows
    win rate >= 38% under the PRIMARY policy

Usage (from the repo root):
    py -m tools.expectancy_candles
"""
from __future__ import annotations

import glob
import json
import math
import sys
from pathlib import Path

OUTPUT_DIR = Path("engine") / "output"
RESOLUTION_GLOB = str(OUTPUT_DIR / "resolutions_candles_v2_*.jsonl")

TARGET_PCT = 0.4
STOP_PCT = 0.2
SPREAD_PCT = 0.01            # conservative, above worst observed
RESOLUTION_SECONDS = 13 * 3600   # measured median 13h

REQUIRED_N = 1000
REQUIRED_WINDOWS = 150
REQUIRED_WIN_RATE = 0.38
BREAK_EVEN = 0.35


def _load() -> tuple:
    paths = sorted(glob.glob(RESOLUTION_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no resolutions file matching {RESOLUTION_GLOB}. "
                 "Run tools/resolve_candles_v2.py first.")
    path = paths[-1]
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    print(f"loaded {len(rows)} resolution records from {path}")
    return rows, path


def _net_pct(outcome: str) -> float:
    if outcome == "WIN":
        return TARGET_PCT - SPREAD_PCT
    return -STOP_PCT - SPREAD_PCT


def _stats(trades: list) -> dict:
    """trades = [(outcome, net_pct, block_index)]"""
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    wins = sum(1 for o, _, _ in trades if o == "WIN")
    win_rate = wins / n
    nets = [p for _, p, _ in trades]
    expectancy = sum(nets) / n

    se = math.sqrt(win_rate * (1.0 - win_rate) / n)
    naive_lo, naive_hi = win_rate - 1.96 * se, win_rate + 1.96 * se

    by_block: dict = {}
    for o, _, b in trades:
        d = by_block.setdefault(b, [0, 0])
        d[1] += 1
        if o == "WIN":
            d[0] += 1
    rates = [w / t for w, t in by_block.values() if t > 0]
    if len(rates) > 1:
        mean_b = sum(rates) / len(rates)
        var_b = sum((r - mean_b) ** 2 for r in rates) / (len(rates) - 1)
        se_b = math.sqrt(var_b / len(rates))
        block_lo, block_hi = mean_b - 1.96 * se_b, mean_b + 1.96 * se_b
    else:
        mean_b = rates[0] if rates else None
        block_lo = block_hi = None

    return {
        "trades": n,
        "wins": wins,
        "losses": n - wins,
        "win_rate": round(win_rate, 4),
        "expectancy_pct_per_trade": round(expectancy, 4),
        "total_return_pct": round(sum(nets), 2),
        "naive_ci95_low": round(naive_lo, 4),
        "naive_ci95_high": round(naive_hi, 4),
        "blocks_used": len(rates),
        "block_mean_win_rate": (round(mean_b, 4) if mean_b is not None else None),
        "block_ci95_low": (round(block_lo, 4) if block_lo is not None else None),
        "block_ci95_high": (round(block_hi, 4) if block_hi is not None else None),
    }


def run() -> int:
    rows, source = _load()

    primary = [(r["outcome"], _net_pct(r["outcome"]), r["block_index"])
               for r in rows if r["outcome"] in ("WIN", "LOSS")]

    secondary = []
    busy_until = None
    for r in sorted(rows, key=lambda x: x["timestamp"]):
        if r["outcome"] not in ("WIN", "LOSS"):
            continue
        if busy_until is not None and r["timestamp"] < busy_until:
            continue
        secondary.append((r["outcome"], _net_pct(r["outcome"]), r["block_index"]))
        busy_until = r["resolved_epoch"]

    p = _stats(primary)
    s = _stats(secondary)

    spans = [r["timestamp"] for r in rows]
    total_span = max(spans) - min(spans) if spans else 0
    windows = total_span / RESOLUTION_SECONDS

    gap_through = sum(1 for r in rows if r.get("gap_through"))
    gap_fraction = gap_through / len(primary) if primary else 0.0

    n_ok = p.get("trades", 0) >= REQUIRED_N
    w_ok = windows >= REQUIRED_WINDOWS
    wr_ok = p.get("win_rate", 0.0) >= REQUIRED_WIN_RATE

    summary = {
        "resolution_source": source,
        "cost_model": {
            "spread_pct_round_trip": SPREAD_PCT,
            "win_gross_pct": TARGET_PCT,
            "loss_gross_pct": -STOP_PCT,
            "win_net_pct": round(TARGET_PCT - SPREAD_PCT, 4),
            "loss_net_pct": round(-STOP_PCT - SPREAD_PCT, 4),
            "break_even_win_rate": BREAK_EVEN,
        },
        "independent_windows": round(windows, 1),
        "gap_through_count": gap_through,
        "gap_through_fraction": round(gap_fraction, 4),
        "primary_every_signal": p,
        "secondary_one_at_a_time": s,
        "pre_committed_criteria": {
            "required_resolved_signals": REQUIRED_N,
            "required_independent_windows": REQUIRED_WINDOWS,
            "required_win_rate": REQUIRED_WIN_RATE,
            "resolved_signals_met": n_ok,
            "independent_windows_met": w_ok,
            "win_rate_met": wr_ok,
            "verdict": "PASS" if (n_ok and w_ok and wr_ok) else "FAIL",
        },
        "phase_45_reference": {
            "instrument": "R_100 (synthetic)",
            "win_rate": 0.3178,
            "break_even": 0.345,
            "verdict": "FAIL",
        },
        "disclosures": [
            "Gap-throughs are recorded at barrier prices; real fills on "
            "gapped stops are worse than -0.2%, so measured expectancy is "
            "OPTIMISTIC relative to live trading.",
            "Spread assumed constant at 0.01%; real spreads widen during "
            "news and illiquid sessions.",
            "Cross-weekend resolution assumes a position can be held "
            "through the close, which incurs swap/rollover costs not "
            "modelled here.",
        ],
    }

    out_path = OUTPUT_DIR / (Path(source).stem.replace(
        "resolutions_candles_v2_", "expectancy_candles_") + ".json")
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
    print("EXPECTANCY - SECONDARY (one at a time, indicative)")
    print("=" * 64)
    for k, v in s.items():
        print(f"  {k:28s}: {v}")
    print()
    print("=" * 64)
    print("PRE-COMMITTED CRITERIA")
    print("=" * 64)
    c = summary["pre_committed_criteria"]
    print(f"  resolved >= {REQUIRED_N}            : {c['resolved_signals_met']} ({p.get('trades')})")
    print(f"  windows  >= {REQUIRED_WINDOWS}             : {c['independent_windows_met']} ({round(windows,1)})")
    print(f"  win rate >= {REQUIRED_WIN_RATE}           : {c['win_rate_met']} ({p.get('win_rate')})")
    print(f"  break-even after costs      : {BREAK_EVEN}")
    print(f"  VERDICT                     : {c['verdict']}")
    print("=" * 64)
    print("  Phase 45 reference (R_100 synthetic): 31.78%, FAIL")
    print("=" * 64)
    print(f"Summary file : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
