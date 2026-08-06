"""APEX ULTRA - Candidate 1 ceiling check: BTC mean-reversion after large moves.

DESCRIPTIVE MEASUREMENT ONLY. No strategy, no entries, no stops, no
expectancy, no execution. It answers one question:

    After a 15-minute bar whose return exceeds 2 standard deviations,
    what does price do over the next 1-3 bars?

This is a CEILING CHECK, not a phase. Its purpose is to establish whether
the available magnitude could plausibly clear costs, cheaply, before any
pre-registered phase is designed. A positive result here is NOT evidence
of an edge; it is only permission to design a proper test.

Reads the committed BTC candle JSONL written by tools/fetch_candles.py.
Standard library only - no numpy, no pandas.

Usage (from the repo root):
    py -m tools.ceiling_btc_reversion
"""
from __future__ import annotations

import glob
import json
import math
import statistics
import sys
from pathlib import Path

SYMBOL = "cryBTCUSD"
GRANULARITY = 900
OUTPUT_DIR = Path("engine") / "output"
CANDLE_GLOB = str(OUTPUT_DIR / f"candles_{SYMBOL}_{GRANULARITY}_*.jsonl")

THRESHOLD_SIGMA = 2.0
LOOKAHEADS = (1, 2, 3)
SPREAD_ROUND_TRIP_PCT = 0.0048     # worst of 6 live samples, project record


def _load() -> list:
    paths = sorted(glob.glob(CANDLE_GLOB))
    if not paths:
        sys.exit(f"BLOCKED: no candle file matching {CANDLE_GLOB}")
    path = Path(paths[-1])
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                k = json.loads(line)
                rows.append((int(k["epoch"]), float(k["close"])))
    rows.sort()
    print(f"loaded {len(rows)} candles from {path.name}")
    return rows


def _pct(vals: list, p: float) -> float:
    s = sorted(vals)
    i = int(p * (len(s) - 1))
    return s[i]


def _report(label: str, revs: list) -> dict:
    """revs are signed so that POSITIVE = price moved back against the
    original move (reversion). Negative = continuation."""
    if not revs:
        return {}
    mean = statistics.fmean(revs)
    med = statistics.median(revs)
    sd = statistics.pstdev(revs)
    wins = sum(1 for r in revs if r > 0)
    # standard error of the mean, to see if the mean is distinguishable
    # from zero at all
    se = sd / math.sqrt(len(revs))
    print(f"  {label:24s} n={len(revs):5d}  mean={mean*100:+.4f}%  "
          f"med={med*100:+.4f}%  win={wins/len(revs)*100:5.1f}%  "
          f"sd={sd*100:.4f}%  mean/se={mean/se if se else 0:+.2f}")
    return {"n": len(revs), "mean": mean, "median": med, "sd": sd,
            "win_rate": wins / len(revs), "mean_over_se": (mean / se) if se else 0.0}


def run() -> int:
    rows = _load()
    closes = [c for _, c in rows]
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]

    sigma = statistics.pstdev(rets)
    threshold = THRESHOLD_SIGMA * sigma

    print()
    print("=" * 70)
    print("CEILING CHECK - BTC mean-reversion after large 15m moves")
    print("=" * 70)
    print(f"  return observations : {len(rets)}")
    print(f"  return stdev        : {sigma*100:.4f}%")
    print(f"  threshold ({THRESHOLD_SIGMA}x)     : {threshold*100:.4f}%")

    big = [i for i, r in enumerate(rets) if abs(r) >= threshold]
    ups = [i for i in big if rets[i] > 0]
    downs = [i for i in big if rets[i] < 0]
    print(f"  bars beyond threshold: {len(big)}  "
          f"({len(big)/len(rets)*100:.2f}% of bars)")
    print(f"    up moves   : {len(ups)}")
    print(f"    down moves : {len(downs)}")

    if len(big) < 30:
        print("\nToo few large moves to say anything. Inconclusive.")
        return 1

    results = {}
    for k in LOOKAHEADS:
        print()
        print(f"--- lookahead {k} bar(s) " + "-" * 44)
        idx = [i for i in big if i + k < len(rets)]

        def rev_for(subset):
            out = []
            for i in subset:
                fwd = sum(rets[i + 1:i + 1 + k])
                out.append(-math.copysign(1.0, rets[i]) * fwd)
            return out

        all_rev = rev_for(idx)
        up_rev = rev_for([i for i in idx if rets[i] > 0])
        dn_rev = rev_for([i for i in idx if rets[i] < 0])

        results[k] = {
            "all": _report("all large moves", all_rev),
            "after_up": _report("after UP moves", up_rev),
            "after_down": _report("after DOWN moves", dn_rev),
        }

        if all_rev:
            frac = statistics.fmean(
                [r / abs(rets[i]) for r, i in zip(all_rev, idx)])
            print(f"  mean reversion as a fraction of the original move: "
                  f"{frac*100:+.1f}%")
            print(f"  distribution: p25={_pct(all_rev,0.25)*100:+.4f}%  "
                  f"p75={_pct(all_rev,0.75)*100:+.4f}%  "
                  f"min={min(all_rev)*100:+.4f}%  max={max(all_rev)*100:+.4f}%")

    # ---- verdict on the 1-bar horizon ---------------------------------
    k1 = results[1]["all"]
    mean1 = k1["mean"]
    net = mean1 * 100 - SPREAD_ROUND_TRIP_PCT

    print()
    print("=" * 70)
    print("CEILING VERDICT (1-bar horizon)")
    print("=" * 70)
    print(f"  gross mean reversion    : {mean1*100:+.4f}%")
    print(f"  worst-case round-trip   : -{SPREAD_ROUND_TRIP_PCT:.4f}%")
    print(f"  net before slippage     : {net:+.4f}%")
    print(f"  mean / standard error   : {k1['mean_over_se']:+.2f}")
    print()

    if mean1 <= 0:
        print("  DEAD. No reversion at the 1-bar horizon; the mean is zero or")
        print("  negative, meaning large moves CONTINUE on average.")
    elif net <= 0:
        print("  DEAD AT CEILING CHECK. Gross reversion exists but does not")
        print("  survive the spread alone, before any slippage.")
    elif abs(k1["mean_over_se"]) < 2.0:
        print("  NOT DISTINGUISHABLE FROM ZERO. The mean is positive but")
        print("  within two standard errors of zero, so it is consistent with")
        print("  noise. More data would be needed, and the effect is small")
        print("  regardless.")
    else:
        print("  SURVIVES the ceiling check on magnitude and significance.")
        print("  This is NOT an edge. It is permission to design a")
        print("  pre-registered phase with a holdout.")

    print()
    print("NOT MODELLED, and each pushes the real figure DOWN:")
    print("  - Entry slippage. Entering after a sharp move is the expensive")
    print("    case; the 0.0048% spread was sampled in calm conditions.")
    print("  - Spread widening during volatility, which is exactly when")
    print("    these signals fire.")
    print("  - Any stop or risk control, which would truncate winners.")
    print("  - The mean is not capturable: you cannot trade the average, only")
    print("    individual outcomes drawn from a wide distribution.")
    print()
    print("This measurement used the FULL dataset. If a phase follows, it")
    print("must pre-register a holdout that this check has not touched.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
