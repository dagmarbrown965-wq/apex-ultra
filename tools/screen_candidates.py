"""APEX ULTRA - W48.0a: candidate independence screen (READ-ONLY).

Enumerates Deriv `active_symbols`, discards ineligible instruments per
docs/PHASE_48_BOUNDARY_AGREEMENT.md Section C, and measures each remaining
candidate's 15-minute return correlation against the two previously-used
real-market series already on disk:

    engine/output/candles_frxEURUSD_900_*.jsonl   (Phase 46)
    engine/output/candles_cryBTCUSD_900_*.jsonl   (Phase 47)

R_100 is exempt from this gate per Amendment v0.1 (structurally an RNG;
tick-only data; no importable structure). Gate order is stage-a independence
then stage-b provenance per Amendment v0.2.

SCOPE LIMIT - this tool computes ONLY the Section E allowlisted statistics:
matched-bar counts and return correlations. It deliberately does NOT compute
or report a candidate's own return standard deviation, autocorrelation,
volatility, trend, indicator series, or any other property. A candidate
examined that way would be contaminated before it was selected. Do not add
"just one more" statistic here.

Facts reused from tools/fetch_candles.py (probed 2026-08-05, not assumed):
  - a candles response arrives in ONE frame; collect must be 1
  - candles are ordered OLDEST-FIRST, fields: epoch/open/high/low/close
  - `end` accepts an epoch integer; the batch ends AT that epoch
  - per-request cap is 1000 candles
  - empty responses are normal at weekends for forex, NOT exhaustion
  - past the history boundary Deriv SILENTLY RETURNS CURRENT DATA while
    echoing the requested `end`; every batch is verified against the range
  - transport.call() cannot send ticks_history (its dispatcher matches the
    key "ticks"), so _ws_roundtrip is used directly

Facts PROBED 2026-08-16 on the first run of this tool (not assumed):
  - "product_type" is NOT an accepted property. Sending it returns
    "Input validation failed: Properties not allowed: product_type."
    The correct request is {"active_symbols": "brief"} and nothing else.
    The earlier draft carried product_type as an assumption; it was wrong,
    and the tool stopped rather than guessing.

Facts ASSUMED about active_symbols and NOT yet probed. The tool fails loudly
rather than guessing if any is wrong:
  - the response carries a list under the key "active_symbols" in one frame
  - each entry carries at least: symbol, display_name, market, submarket
  - synthetic instruments are identifiable by a market name containing
    "synthetic" (a symbol-prefix denylist is applied as a second defence)
Confirm these on first run before trusting any output.

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.screen_candidates
    py -m tools.screen_candidates --limit 5        (smoke test)
    py -m tools.screen_candidates --list-only      (enumerate, fetch nothing)
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time
from pathlib import Path

from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport

GRANULARITY = 900                 # 15-minute bars, matching the stored series
CANDLES_PER_REQUEST = 1000        # observed server cap
SLEEP_BETWEEN_REQUESTS = 1.0
MAX_PAGES_PER_CANDIDATE = 4       # 4000 bars ~= 41 days, ample for 500 matched
MIN_MATCHED_RETURNS = 500         # Section F criterion 2
INDEPENDENCE_CEILING = 0.30       # Section F criterion 2, |r| strictly below

OUTPUT_DIR = Path("engine") / "output"

# Section C.1 - previously used, ineligible for selection.
EXCLUDED_SYMBOLS = {"frxEURUSD", "cryBTCUSD", "R_100"}

# Second defence behind the market-name filter. Deriv synthetic families.
SYNTHETIC_PREFIXES = (
    "R_", "1HZ", "BOOM", "CRASH", "STEP", "JD", "RDBEAR", "RDBULL", "WLD",
    "CRYPTIDX", "RB", "STPRNG",
)

REFERENCE_GLOBS = {
    "frxEURUSD": "engine/output/candles_frxEURUSD_900_*.jsonl",
    "cryBTCUSD": "engine/output/candles_cryBTCUSD_900_*.jsonl",
}


# ----------------------------------------------------------------- helpers

def _pearson(xs: list, ys: list) -> float | None:
    """Pearson correlation. Returns None if undefined (zero variance)."""
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _load_reference(pattern: str) -> dict:
    """Load epoch -> close from the largest matching stored candle file."""
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"no stored series matching {pattern}")
    best_path, best = None, {}
    for p in paths:
        series = {}
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                series[int(rec["epoch"])] = float(rec["close"])
        if len(series) > len(best):
            best_path, best = p, series
    print(f"  reference {Path(best_path).name}: {len(best)} bars")
    return best


def _matched_returns(cand: dict, ref: dict) -> tuple:
    """Aligned simple returns over epochs present in BOTH series.

    A return is formed only from two CONSECUTIVE matched epochs exactly
    GRANULARITY apart, so no return is manufactured across a gap.
    """
    common = sorted(set(cand.keys()) & set(ref.keys()))
    cr, rr = [], []
    for i in range(1, len(common)):
        e0, e1 = common[i - 1], common[i]
        if e1 - e0 != GRANULARITY:
            continue
        c0, c1 = cand[e0], cand[e1]
        r0, r1 = ref[e0], ref[e1]
        if c0 <= 0 or r0 <= 0:
            continue
        cr.append(c1 / c0 - 1.0)
        rr.append(r1 / r0 - 1.0)
    return cr, rr


def _parse_candles(frames: list) -> tuple:
    """Return (candles, saw_frame); candles oldest-first. Mirrors fetch_candles."""
    for f in frames:
        if not isinstance(f, dict):
            continue
        if f.get("error"):
            return [], True
        cs = f.get("candles")
        if cs is None:
            continue
        out = []
        for k in cs:
            try:
                out.append((int(k["epoch"]), float(k["close"])))
            except (KeyError, TypeError, ValueError):
                return [], True
        return out, True
    return [], False


def _fetch_window(t, symbol: str, end_epoch: int) -> tuple:
    """Page backwards from end_epoch. Returns (epoch->close, note)."""
    series: dict = {}
    end_param = int(end_epoch)
    note = None
    for page in range(MAX_PAGES_PER_CANDIDATE):
        res = t._ws_roundtrip(
            {"ticks_history": symbol,
             "count": CANDLES_PER_REQUEST,
             "end": end_param,
             "style": "candles",
             "granularity": GRANULARITY},
            collect=1, timeout=30.0)
        batch, saw_frame = _parse_candles(res.get("_raw_frames") or [])
        if not saw_frame:
            return series, "no_response_frame"
        if not batch:
            return series, "empty_response"
        newest = batch[-1][0]
        # SUBSTITUTION DEFENCE - identical rule to fetch_candles.
        if newest > end_param + GRANULARITY:
            return series, "substitution_detected"
        for epoch, close in batch:
            series[epoch] = close
        end_param = batch[0][0] - 1
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return series, note


# -------------------------------------------------------------------- main

def screen(limit: int | None, list_only: bool) -> int:
    if os.environ.get("LIVE_TRADING", "false").strip().lower() in (
            "1", "true", "yes", "on"):
        print("BLOCKED: LIVE_TRADING is enabled; refusing to run.")
        return 1
    token = os.environ.get("DERIV_API_TOKEN", "")
    app_id = os.environ.get("DERIV_APP_ID", "")
    if not token:
        print("BLOCKED: DERIV_API_TOKEN not set.")
        return 1

    print("=" * 64)
    print("W48.0a - CANDIDATE INDEPENDENCE SCREEN (read-only)")
    print("=" * 64)
    print(f"granularity        : {GRANULARITY}s")
    print(f"ceiling            : |r| < {INDEPENDENCE_CEILING}")
    print(f"min matched returns: {MIN_MATCHED_RETURNS}")
    print()

    print("loading stored reference series")
    references = {name: _load_reference(pat)
                  for name, pat in REFERENCE_GLOBS.items()}
    # Screen against a window both references actually cover.
    ref_end = min(max(s.keys()) for s in references.values())
    print(f"  screening window ends at epoch {ref_end}")
    print()

    t = DerivRestOtpTransport(api_token=token, app_id=app_id or None)
    t.connect()
    results, eligible = [], []
    try:
        auth = t.call({"authorize": token}, timeout=20.0)
        if "error" in auth:
            print("AUTH FAILED: " + str(auth["error"].get("message")))
            return 1
        if auth.get("authorize", {}).get("is_virtual") != 1:
            print("BLOCKED: account is not virtual/demo.")
            return 1
        print("auth ok (virtual account confirmed)")
        print()

        # product_type is NOT accepted by this platform version - probed
        # 2026-08-16. Send "active_symbols" alone.
        res = t._ws_roundtrip(
            {"active_symbols": "brief"},
            collect=1, timeout=30.0)
        symbols = None
        for f in res.get("_raw_frames") or []:
            if isinstance(f, dict) and f.get("error"):
                print("active_symbols ERROR: "
                      + str(f["error"].get("message")))
                return 1
            if isinstance(f, dict) and isinstance(f.get("active_symbols"), list):
                symbols = f["active_symbols"]
                break
        if symbols is None:
            print("ASSUMPTION VIOLATED: no 'active_symbols' list in response.")
            print("Inspect the raw frames before proceeding; do not guess.")
            return 1
        print(f"active_symbols returned {len(symbols)} entries")

        for s in symbols:
            sym = s.get("symbol")
            market = (s.get("market") or "").lower()
            if not sym:
                continue
            if sym in EXCLUDED_SYMBOLS:
                results.append({"symbol": sym, "outcome": "EXCLUDED",
                                "reason": "previously used (Section C.1)"})
                continue
            if "synthetic" in market or sym.startswith(SYNTHETIC_PREFIXES):
                results.append({"symbol": sym, "outcome": "EXCLUDED",
                                "reason": f"synthetic (market={market})"})
                continue
            eligible.append({"symbol": sym, "market": market,
                             "display_name": s.get("display_name")})

        print(f"eligible candidates: {len(eligible)}")
        print()
        if list_only:
            for c in eligible:
                print(f"  {c['symbol']:16s} {c['market']:18s} "
                      f"{c['display_name']}")
            return 0
        if limit:
            eligible = eligible[:limit]
            print(f"--limit in effect: screening first {len(eligible)}")
            print()

        for i, c in enumerate(eligible, 1):
            sym = c["symbol"]
            print(f"[{i}/{len(eligible)}] {sym}")
            series, note = _fetch_window(t, sym, ref_end)
            row = {"symbol": sym, "market": c["market"],
                   "display_name": c["display_name"],
                   "bars_fetched": len(series), "fetch_note": note,
                   "correlations": {}}
            if note in ("no_response_frame", "empty_response"):
                row["outcome"] = "NO_DATA"
                print(f"      {note}; no data")
                results.append(row)
                continue

            verdict, worst = "PASS", 0.0
            for ref_name, ref_series in references.items():
                cr, rr = _matched_returns(series, ref_series)
                r = _pearson(cr, rr)
                row["correlations"][ref_name] = {
                    "n_matched_returns": len(cr),
                    "r": None if r is None else round(r, 4),
                }
                if len(cr) < MIN_MATCHED_RETURNS:
                    verdict = "INSUFFICIENT"
                    print(f"      vs {ref_name}: n={len(cr)} "
                          f"(< {MIN_MATCHED_RETURNS}) - not evaluable")
                    continue
                if r is None:
                    verdict = "INSUFFICIENT"
                    print(f"      vs {ref_name}: correlation undefined")
                    continue
                worst = max(worst, abs(r))
                print(f"      vs {ref_name}: n={len(cr)} r={r:+.4f}")
                if abs(r) >= INDEPENDENCE_CEILING and verdict == "PASS":
                    verdict = "FAIL"

            row["max_abs_r"] = round(worst, 4)
            row["outcome"] = verdict
            print(f"      -> {verdict}")
            results.append(row)
    finally:
        try:
            t.close()
        except Exception:
            pass

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"screening_w48_0a_{ref_end}.json"
    payload = {
        "stage": "W48.0a independence screen",
        "agreement": "docs/PHASE_48_BOUNDARY_AGREEMENT.md v1.0 + v0.1 + v0.2",
        "granularity": GRANULARITY,
        "independence_ceiling": INDEPENDENCE_CEILING,
        "min_matched_returns": MIN_MATCHED_RETURNS,
        "screening_window_end_epoch": ref_end,
        "references": {k: len(v) for k, v in references.items()},
        "r_100_note": "exempt per Amendment v0.1 (RNG, tick-only data)",
        "candidates_screened": len(results),
        "results": results,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    survivors = [r for r in results if r.get("outcome") == "PASS"]
    print()
    print("-" * 64)
    print(f"screened : {len(results)}")
    print(f"survivors: {len(survivors)}")
    for r in survivors:
        print(f"  {r['symbol']:16s} max|r| = {r['max_abs_r']:.4f}")
    if not survivors:
        print("  NONE - Section C no-survivors rule applies. Do NOT relax a")
        print("  threshold; close the phase with the finding or write a new")
        print("  agreement stating the new threshold and its reason first.")
    print("-" * 64)
    print(f"Screening record: {out_path}")
    print("Stage b (provenance) runs on survivors only, per Amendment v0.2.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="W48.0a candidate independence screen (read-only).")
    ap.add_argument("--limit", type=int, default=None,
                    help="screen only the first N eligible candidates")
    ap.add_argument("--list-only", action="store_true",
                    help="enumerate eligible candidates and exit")
    args = ap.parse_args()
    return screen(args.limit, args.list_only)


if __name__ == "__main__":
    sys.exit(main())
