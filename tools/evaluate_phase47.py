"""APEX ULTRA - W47.3: metrics and verdict (Phase 47, OFFLINE, arithmetic only).

Consumes the W47.2 trades CSV and summary, applies the frozen cost model,
splits in-sample from holdout by ENTRY timestamp, and issues the verdict
mechanically against the criteria locked in
docs/PHASE_47_BOUNDARY_AGREEMENT.md before any backtest existed.

Verdict logic lives here, separate from replay logic, so that the replay
can be audited independently of the evaluation.

SPLIT RULE (locked during protocol review):
    boundary = first_epoch + 0.75 * (last_epoch - first_epoch)
    A trade belongs to the HOLDOUT if its ENTRY timestamp is at or after
    the boundary, regardless of where it exits. This avoids partial
    attribution of trades straddling the boundary.

    The holdout is single-use. A second evaluation of the holdout voids
    the phase.

COST MODEL (frozen, Section B):
    0.01% round-trip, adopted conservatively above the ~0.0034% observed.
    R-multiples from W47.2 are GROSS. Cost expressed in R depends on each
    trade's own risk:
        risk_pct   = (stop_atr * atr_at_entry) / entry_price * 100
        cost_in_R  = 0.01 / risk_pct
    subtracted from that trade's gross R. This is arithmetic, not a new
    decision, but is made visible rather than buried.

SUCCESS HIERARCHY (Section F) - evaluated STRICTLY IN ORDER, stopping at
the first failure. Later criteria may not rescue an earlier failure.
    1. Sample validity : holdout n >= 50
    2. Expectancy      : holdout expectancy > 0.15R
    3. Profit factor   : holdout profit factor > 1.25
    4. Stability       : holdout expectancy >= 75% of in-sample expectancy

Sample tiers: n < 30 insufficient (no verdict) | 30-49 exploratory only
(cannot pass) | n >= 50 evaluable.

Usage (from the repo root):
    py -m tools.evaluate_phase47
"""
from __future__ import annotations

import csv
import glob
import json
import statistics
import sys
from pathlib import Path

OUTPUT_DIR = Path("engine") / "output"
TRADES_GLOB = str(OUTPUT_DIR / "phase47_primary_*_trades.csv")
SUMMARY_GLOB = str(OUTPUT_DIR / "phase47_primary_*_summary.json")

SPREAD_PCT = 0.01          # frozen round-trip cost
SPLIT_FRACTION = 0.75

TIER_INSUFFICIENT = 30
TIER_EVALUABLE = 50
REQ_EXPECTANCY = 0.15
REQ_PROFIT_FACTOR = 1.25
REQ_STABILITY = 0.75


def _load() -> tuple:
    tp = sorted(glob.glob(TRADES_GLOB))
    sp = sorted(glob.glob(SUMMARY_GLOB))
    if not tp or not sp:
        sys.exit("BLOCKED: run tools/backtest_compression_breakout.py first.")
    trades_path, summary_path = Path(tp[-1]), Path(sp[-1])
    with open(summary_path) as f:
        summary = json.load(f)
    if not summary.get("preregistration_match", False):
        sys.exit("BLOCKED: summary is from an EXPLORATORY run. Only the "
                 "pre-registered primary configuration may be evaluated.")
    rows = list(csv.DictReader(open(trades_path)))
    print(f"loaded {len(rows)} trades from {trades_path}")
    return rows, summary, trades_path


def _net_r(row: dict, stop_atr: float) -> float:
    """Gross R minus the frozen round-trip cost expressed in R."""
    entry = float(row["entry_price"])
    atr = float(row["atr_at_entry"])
    risk_pct = (stop_atr * atr) / entry * 100.0
    cost_r = SPREAD_PCT / risk_pct if risk_pct > 0 else 0.0
    return float(row["r_multiple"]) - cost_r


def _dist(vals: list) -> dict:
    if not vals:
        return {}
    s = sorted(vals)
    return {
        "min": round(s[0], 4),
        "p25": round(s[len(s) // 4], 4),
        "median": round(statistics.median(s), 4),
        "p75": round(s[(3 * len(s)) // 4], 4),
        "max": round(s[-1], 4),
        "mean": round(statistics.fmean(s), 4),
    }


def _histogram(vals: list) -> dict:
    edges = [-5, -3, -2, -1.5, -1, -0.5, 0, 0.5, 1, 2, 3, 5, 10]
    buckets = {}
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        buckets[f"[{lo},{hi})"] = sum(1 for v in vals if lo <= v < hi)
    buckets["<-5"] = sum(1 for v in vals if v < -5)
    buckets[">=10"] = sum(1 for v in vals if v >= 10)
    return buckets


def _max_drawdown_r(vals: list) -> float:
    peak = 0.0
    cum = 0.0
    dd = 0.0
    for v in vals:
        cum += v
        peak = max(peak, cum)
        dd = min(dd, cum - peak)
    return round(dd, 4)


def _metrics(rows: list, stop_atr: float) -> dict:
    n = len(rows)
    if n == 0:
        return {"trades": 0}
    nets = [_net_r(r, stop_atr) for r in rows]
    wins = [v for v in nets if v > 0]
    losses = [v for v in nets if v <= 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    reasons = {}
    for r in rows:
        reasons[r["exit_reason"]] = reasons.get(r["exit_reason"], 0) + 1
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / n, 4),
        "expectancy_r": round(statistics.fmean(nets), 4),
        "total_r": round(sum(nets), 3),
        "profit_factor": round(pf, 4) if pf != float("inf") else "inf",
        "max_drawdown_r": _max_drawdown_r(nets),
        "r_distribution": _dist(nets),
        "r_histogram": _histogram(nets),
        "mae_r_distribution": _dist([float(r["mae_r"]) for r in rows]),
        "mfe_r_distribution": _dist([float(r["mfe_r"]) for r in rows]),
        "exit_reasons": reasons,
        "mean_bars_held": round(statistics.fmean(
            [int(r["bars_held"]) for r in rows]), 1),
    }


def run() -> int:
    rows, w472, trades_path = _load()
    stop_atr = w472["parameters"]["stop_atr"]

    first_epoch = w472["first_epoch"]
    last_epoch = w472["last_epoch"]
    boundary = int(first_epoch + SPLIT_FRACTION * (last_epoch - first_epoch))

    in_sample = [r for r in rows if int(r["entry_epoch"]) < boundary]
    holdout = [r for r in rows if int(r["entry_epoch"]) >= boundary]

    ism = _metrics(in_sample, stop_atr)
    hom = _metrics(holdout, stop_atr)

    # --- close-only bias quantification (both directions) ---------------
    worse_than_1r = sum(1 for r in rows if _net_r(r, stop_atr) < -1.05)
    worse_frac = worse_than_1r / len(rows) if rows else 0.0

    # --- verdict, strictly ordered --------------------------------------
    n_ho = hom.get("trades", 0)
    if n_ho < TIER_INSUFFICIENT:
        tier = "insufficient"
    elif n_ho < TIER_EVALUABLE:
        tier = "exploratory_only"
    else:
        tier = "evaluable"

    checks = []
    verdict = None

    ok = tier == "evaluable"
    checks.append({"criterion": "1. sample validity (holdout n >= 50)",
                   "value": n_ho, "required": TIER_EVALUABLE, "passed": ok})
    if not ok:
        verdict = ("INSUFFICIENT SAMPLE" if tier == "insufficient"
                   else "EXPLORATORY ONLY - CANNOT PASS")

    if verdict is None:
        v = hom["expectancy_r"]
        ok = v > REQ_EXPECTANCY
        checks.append({"criterion": "2. expectancy > 0.15R", "value": v,
                       "required": REQ_EXPECTANCY, "passed": ok})
        if not ok:
            verdict = "FAIL"

    if verdict is None:
        v = hom["profit_factor"]
        ok = (v == "inf") or (v > REQ_PROFIT_FACTOR)
        checks.append({"criterion": "3. profit factor > 1.25", "value": v,
                       "required": REQ_PROFIT_FACTOR, "passed": ok})
        if not ok:
            verdict = "FAIL"

    if verdict is None:
        ise = ism.get("expectancy_r", 0.0)
        ratio = (hom["expectancy_r"] / ise) if ise > 0 else None
        ok = ratio is not None and ratio >= REQ_STABILITY
        checks.append({"criterion": "4. holdout >= 75% of in-sample expectancy",
                       "value": (round(ratio, 4) if ratio is not None
                                 else "in-sample expectancy <= 0"),
                       "required": REQ_STABILITY, "passed": ok})
        if not ok:
            verdict = "FAIL"

    if verdict is None:
        verdict = "PASS"

    disclosures = [
        "CLOSE-ONLY EXECUTION, both bias directions. Stops and trails are "
        "evaluated on bar close only, as the pre-registration requires. "
        "FAVOURABLE: a bar piercing the stop intrabar but closing back "
        "inside does not exit, whereas a resting stop order would have "
        "filled. UNFAVOURABLE: a bar closing well beyond the stop exits at "
        f"that close, not at the stop, producing losses worse than -1R "
        f"({worse_than_1r} trades, {worse_frac:.1%}, exited worse than "
        "-1.05R). The NET direction of these opposing effects is an "
        "empirical question and is not claimed here.",
        f"Cost model frozen at {SPREAD_PCT}% round-trip against ~0.0034% "
        "observed; conservative by roughly 3x.",
        "Overnight funding on held positions and slippage on stop fills "
        "are NOT modelled. Spread widening during volatile expansion - the "
        "exact condition this strategy trades into - is not modelled.",
        f"{w472.get('ignored_signals')} breakout signals were suppressed by "
        "the one-position-at-a-time rule. Measured results describe that "
        "constrained strategy, not the unconstrained signal.",
        "Single instrument, single year, single parameter set. A pass would "
        "justify further investigation, not capital.",
    ]

    out = {
        "phase": "47",
        "work_item": "W47.3",
        "trades_source": str(trades_path),
        "trades_sha256_from_w472": w472.get("trades_sha256"),
        "candle_sha256_from_w472": w472.get("candle_sha256"),
        "preregistration_match": w472.get("preregistration_match"),
        "split": {
            "rule": "by entry timestamp; holdout is entry >= boundary",
            "fraction_in_sample": SPLIT_FRACTION,
            "first_epoch": first_epoch,
            "boundary_epoch": boundary,
            "last_epoch": last_epoch,
        },
        "cost_model": {
            "spread_pct_round_trip": SPREAD_PCT,
            "applied": "per trade, cost_in_R = 0.01 / risk_pct",
        },
        "in_sample": ism,
        "holdout": hom,
        "holdout_sample_tier": tier,
        "criteria_checked": checks,
        "verdict": verdict,
        "disclosures": disclosures,
    }

    stem = trades_path.stem.replace("_trades", "_evaluation")
    out_path = OUTPUT_DIR / f"{stem}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    def show(label, m):
        print()
        print("=" * 68)
        print(label)
        print("=" * 68)
        for k in ("trades", "wins", "losses", "win_rate", "expectancy_r",
                  "total_r", "profit_factor", "max_drawdown_r",
                  "mean_bars_held", "exit_reasons"):
            print(f"  {k:22s}: {m.get(k)}")
        print(f"  {'R distribution':22s}: {m.get('r_distribution')}")
        print(f"  {'MAE (R)':22s}: {m.get('mae_r_distribution')}")
        print(f"  {'MFE (R)':22s}: {m.get('mfe_r_distribution')}")

    show("IN-SAMPLE (first 75%)", ism)
    show("HOLDOUT (most recent 25%) - SINGLE USE", hom)

    print()
    print("=" * 68)
    print("R-MULTIPLE HISTOGRAM (holdout, net of costs)")
    print("=" * 68)
    for k, v in hom.get("r_histogram", {}).items():
        if v:
            print(f"  {k:12s} {'#' * min(v, 50)} {v}")

    print()
    print("=" * 68)
    print("VERDICT (criteria locked before any backtest)")
    print("=" * 68)
    print(f"  holdout sample tier : {tier}")
    for c in checks:
        mark = "PASS" if c["passed"] else "FAIL"
        print(f"  [{mark}] {c['criterion']}")
        print(f"         value {c['value']}, required {c['required']}")
    print()
    print(f"  VERDICT: {verdict}")
    print("=" * 68)
    print()
    print("DISCLOSURES")
    for d in disclosures:
        print("  - " + d)
    print()
    print(f"Evaluation file : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
