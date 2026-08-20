"""APEX ULTRA - W48.0b step 1: identify the reference timezone offset (READ-ONLY).

Establishes the clock convention of the HistData reference series against Deriv,
per docs/PHASE_48_AMENDMENT_V0_7.md Rule 3. Runs ONCE, on one pair. The result
is a property of the SOURCE, not of any candidate, and is reused unchanged for
every candidate in the provenance measurement that follows.

THE OFFSET IS IDENTIFIED, NEVER FITTED.

  - The candidate set is fixed in advance: hour offsets UTC+0, UTC-4, UTC-5,
    each crossed with a bar shift of -1, 0, +1 fifteen-minute bars. Nine
    combinations. UTC+0 is a control expected to fail.
  - Correlation is computed at EVERY combination and the FULL TABLE is printed.
  - Identification requires best r >= 0.90 AND second-best r <= 0.60. One sharp
    peak against a flat field identifies an alignment; a graded field does not.
  - If that test fails the tool HALTS and exits 2. It does NOT return the
    maximum. Selecting best-of-nine from a graded field is fitting, which is
    the thing this project's rules exist to prevent.

Reference handling, per Amendment v0.7:
  Rule 1  source rows are SORTED; the file's arrival order carries no meaning
          (60 backwards steps observed in the July GBPJPY file)
  Rule 2  any minute whose timestamp appears MORE THAN ONCE is dropped whole -
          no row is preferred on price, range or position (cost 0.70%)
  Rule 4  only 15-minute buckets holding all 15 source minutes are used

Deriv handling, reused verbatim from tools/screen_candidates.py:
  - `count` is a TIME WINDOW (count * granularity), not a candle cap
  - `epoch` marks the bar OPEN; bar covers [epoch, epoch+900)
  - substitution defence: a batch newer than requested is discarded
  - sustained requests get throttled; pacing and abort logic carried over

SCOPE - computes matched counts, correlations, and (per the Section E stage-b
allowlist) return standard deviations against the reference. Nothing else. No
indicator, no autocorrelation, no backtest.

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.identify_reference_offset
    py -m tools.identify_reference_offset --csv reference\\DAT_ASCII_GBPJPY_M1_202607.csv --symbol frxGBPJPY
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport

GRANULARITY = 900
MINUTES_PER_BUCKET = 15
CANDLES_PER_REQUEST = 1000
SLEEP_BETWEEN_REQUESTS = 2.5
MAX_PAGES = 12
MAX_CONSECUTIVE_EMPTY = 4
WEEKEND_STEP_SECONDS = 86400

MIN_MATCHED_RETURNS = 500          # Section F criterion 1
IDENTIFY_BEST_MIN = 0.90           # Amendment v0.7 Rule 3, fixed in advance
IDENTIFY_RUNNERUP_MAX = 0.60       # Amendment v0.7 Rule 3, fixed in advance

HOUR_OFFSETS = (0, -4, -5)         # UTC+0 is a control, expected to fail
BAR_SHIFTS = (-1, 0, 1)

OUTPUT_DIR = Path("engine") / "output"
DEFAULT_CSV = Path("reference") / "DAT_ASCII_GBPJPY_M1_202607.csv"
DEFAULT_SYMBOL = "frxGBPJPY"


# ------------------------------------------------------------------ reference

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_reference(path: Path) -> tuple:
    """Return ({bucket_start_naive_epoch: close}, stats) per Amendment v0.7."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = line.split(";")
            if len(p) < 5:
                raise ValueError(f"unexpected column count in {path.name}: {line[:60]}")
            rows.append((p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4])))

    n_in = len(rows)

    # Rule 2 - drop every minute whose timestamp appears more than once.
    counts = Counter(r[0] for r in rows)
    kept = [r for r in rows if counts[r[0]] == 1]
    n_dropped = n_in - len(kept)

    # Rule 1 - sort; arrival order is meaningless.
    kept.sort(key=lambda r: r[0])

    # Rule 4 - complete buckets only.
    buckets = defaultdict(list)
    for ts, o, h, l, c in kept:
        dt = datetime.strptime(ts, "%Y%m%d %H%M%S")
        naive_epoch = calendar.timegm(dt.timetuple())
        start = naive_epoch - (naive_epoch % GRANULARITY)
        buckets[start].append((naive_epoch, c))

    complete = {}
    n_partial = 0
    for start, obs in buckets.items():
        if len(obs) == MINUTES_PER_BUCKET:
            obs.sort()
            complete[start] = obs[-1][1]        # close = last observation in [E, E+900)
        else:
            n_partial += 1

    stats = {
        "rows_in": n_in,
        "rows_dropped_duplicate_minutes": n_dropped,
        "rows_kept": len(kept),
        "buckets_total": len(buckets),
        "buckets_complete": len(complete),
        "buckets_partial_excluded": n_partial,
    }
    return complete, stats


# ---------------------------------------------------------------------- deriv

def _parse(frames: list) -> tuple:
    for f in frames:
        if not isinstance(f, dict):
            continue
        if f.get("error"):
            e = f["error"]
            return {}, True, str(e.get("message") if isinstance(e, dict) else e)
        cs = f.get("candles")
        if cs is None:
            continue
        out = {}
        for k in cs:
            try:
                out[int(k["epoch"])] = float(k["close"])
            except (KeyError, TypeError, ValueError):
                return {}, True, "malformed candle record"
        return out, True, None
    return {}, False, None


def fetch_deriv(t, symbol: str, end_epoch: int, back_to: int) -> dict:
    series = {}
    end_param = int(end_epoch)
    empty = 0
    for page in range(MAX_PAGES):
        res = t._ws_roundtrip(
            {"ticks_history": symbol, "count": CANDLES_PER_REQUEST,
             "end": end_param, "style": "candles", "granularity": GRANULARITY},
            collect=1, timeout=30.0)
        batch, saw, err = _parse(res.get("_raw_frames") or [])
        if err:
            raise RuntimeError(f"api_error: {err}")
        if not saw:
            raise RuntimeError("no_response_frame")
        if not batch:
            empty += 1
            if empty >= MAX_CONSECUTIVE_EMPTY:
                break
            end_param -= WEEKEND_STEP_SECONDS
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            continue
        empty = 0
        newest = max(batch)
        if newest > end_param + GRANULARITY:      # substitution defence
            print(f"      SUBSTITUTION DETECTED at page {page+1}; batch discarded")
            break
        series.update(batch)
        oldest = min(batch)
        print(f"      page {page+1:2d}: {len(batch):5d} bars, oldest {oldest}, total {len(series)}")
        if oldest <= back_to:
            break
        end_param = oldest - 1
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return series


# ------------------------------------------------------------------- measure

def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def stdev(xs):
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def matched_returns(ref: dict, der: dict, hours: int, bars: int) -> tuple:
    """Shift reference into UTC epochs and pair with Deriv on identical bars."""
    shifted = {}
    for naive_start, close in ref.items():
        # file-time is UTC+hours, so UTC = naive - hours
        shifted[naive_start - hours * 3600 + bars * GRANULARITY] = close
    common = sorted(set(shifted) & set(der))
    rr, dd = [], []
    for i in range(1, len(common)):
        e0, e1 = common[i - 1], common[i]
        if e1 - e0 != GRANULARITY:
            continue
        r0, r1 = shifted[e0], shifted[e1]
        d0, d1 = der[e0], der[e1]
        if r0 <= 0 or d0 <= 0:
            continue
        rr.append(r1 / r0 - 1.0)
        dd.append(d1 / d0 - 1.0)
    return rr, dd


# ---------------------------------------------------------------------- main

def run(csv_path: Path, symbol: str) -> int:
    if os.environ.get("LIVE_TRADING", "false").strip().lower() in ("1", "true", "yes", "on"):
        print("BLOCKED: LIVE_TRADING is enabled; refusing to run.")
        return 1
    token = os.environ.get("DERIV_API_TOKEN", "")
    app_id = os.environ.get("DERIV_APP_ID", "")
    if not token:
        print("BLOCKED: DERIV_API_TOKEN not set.")
        return 1
    if not csv_path.exists():
        print(f"BLOCKED: reference file not found: {csv_path}")
        return 1

    print("=" * 68)
    print("W48.0b STEP 1 - REFERENCE OFFSET IDENTIFICATION (read-only)")
    print("=" * 68)
    print(f"reference : {csv_path.name}")
    digest = sha256(csv_path)
    print(f"sha256    : {digest}")
    print(f"symbol    : {symbol}")
    print(f"identify  : best r >= {IDENTIFY_BEST_MIN}, runner-up r <= {IDENTIFY_RUNNERUP_MAX}")
    print(f"minimum n : {MIN_MATCHED_RETURNS} matched returns")
    print()

    ref, rstats = load_reference(csv_path)
    for k, v in rstats.items():
        print(f"  {k:34s}: {v}")
    if not ref:
        print("BLOCKED: no complete buckets in reference.")
        return 1
    lo, hi = min(ref), max(ref)
    print(f"  {'naive bucket range':34s}: {lo} .. {hi}")
    print()

    # Deriv window: widen by a day either side so every candidate offset is covered.
    end_epoch = hi + 2 * 86400
    back_to = lo - 2 * 86400

    t = DerivRestOtpTransport(api_token=token, app_id=app_id or None)
    t.connect()
    try:
        auth = t.call({"authorize": token}, timeout=20.0)
        if "error" in auth:
            print("AUTH FAILED: " + str(auth["error"].get("message")))
            return 1
        if auth.get("authorize", {}).get("is_virtual") != 1:
            print("BLOCKED: account is not virtual/demo.")
            return 1
        print("auth ok (virtual account confirmed)")
        print(f"fetching {symbol} 15m bars")
        der = fetch_deriv(t, symbol, end_epoch, back_to)
    finally:
        try:
            t.close()
        except Exception:
            pass

    print(f"  deriv bars fetched: {len(der)}")
    if not der:
        print("BLOCKED: no Deriv bars.")
        return 1
    print()

    print("OFFSET TABLE - every combination, printed in full")
    print(f"  {'hours':>6} {'bars':>5} {'n':>7} {'r':>9}   {'sd_ref':>9} {'sd_deriv':>9}")
    table = []
    for hours in HOUR_OFFSETS:
        for bars in BAR_SHIFTS:
            rr, dd = matched_returns(ref, der, hours, bars)
            r = pearson(rr, dd) if len(rr) >= 2 else None
            row = {
                "hours": hours, "bars": bars, "n": len(rr),
                "r": None if r is None else round(r, 6),
                "sd_reference": None if not rr else round(stdev(rr), 8),
                "sd_deriv": None if not dd else round(stdev(dd), 8),
                "evaluable": len(rr) >= MIN_MATCHED_RETURNS,
            }
            table.append(row)
            rs = "     n/a" if r is None else f"{r:+9.5f}"
            sr = "      n/a" if row["sd_reference"] is None else f"{row['sd_reference']:9.6f}"
            sd = "      n/a" if row["sd_deriv"] is None else f"{row['sd_deriv']:9.6f}"
            flag = "" if row["evaluable"] else "   (n below minimum - not evaluable)"
            print(f"  {hours:>6} {bars:>5} {len(rr):>7} {rs}   {sr} {sd}{flag}")
    print()

    usable = [row for row in table if row["evaluable"] and row["r"] is not None]
    ranked = sorted(usable, key=lambda x: abs(x["r"]), reverse=True)

    identified = None
    if len(ranked) >= 1:
        best = ranked[0]
        runner = ranked[1] if len(ranked) > 1 else None
        ok_best = abs(best["r"]) >= IDENTIFY_BEST_MIN
        ok_runner = runner is None or abs(runner["r"]) <= IDENTIFY_RUNNERUP_MAX
        print(f"  best      : hours={best['hours']} bars={best['bars']} "
              f"r={best['r']:+.5f} n={best['n']}")
        if runner:
            print(f"  runner-up : hours={runner['hours']} bars={runner['bars']} "
                  f"r={runner['r']:+.5f} n={runner['n']}")
        print(f"  best >= {IDENTIFY_BEST_MIN}: {ok_best}    "
              f"runner-up <= {IDENTIFY_RUNNERUP_MAX}: {ok_runner}")
        if ok_best and ok_runner:
            identified = {"hours": best["hours"], "bars": best["bars"],
                          "r": best["r"], "n": best["n"]}

    print()
    print("-" * 68)
    if identified:
        print(f"IDENTIFIED: reference clock is UTC{identified['hours']:+d}, "
              f"bar shift {identified['bars']:+d}")
        print(f"            r = {identified['r']:+.5f} over n = {identified['n']}")
        print("            Use this offset unchanged for every candidate.")
    else:
        print("NOT IDENTIFIED - HALTING.")
        print("The field is graded rather than peaked, or no combination reached")
        print("the minimum sample. Per Amendment v0.7 Rule 3 the maximum is NOT")
        print("selected. Investigate before proceeding; do not proceed to")
        print("provenance measurement on an unidentified alignment.")
    print("-" * 68)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"reference_offset_{symbol}_{csv_path.stem}.json"
    with open(out, "w") as f:
        json.dump({
            "stage": "W48.0b step 1 - reference offset identification",
            "agreement": "docs/PHASE_48_BOUNDARY_AGREEMENT.md v1.0 + v0.1-v0.7",
            "reference_file": csv_path.name,
            "reference_sha256": digest,
            "reference_stats": rstats,
            "symbol": symbol,
            "deriv_bars_fetched": len(der),
            "identification_rule": {
                "best_min": IDENTIFY_BEST_MIN,
                "runnerup_max": IDENTIFY_RUNNERUP_MAX,
                "min_matched_returns": MIN_MATCHED_RETURNS,
                "hour_offsets": list(HOUR_OFFSETS),
                "bar_shifts": list(BAR_SHIFTS),
            },
            "table": table,
            "identified": identified,
        }, f, indent=2)
    print(f"Record: {out}")
    return 0 if identified else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Identify reference timezone offset (read-only).")
    ap.add_argument("--csv", type=str, default=str(DEFAULT_CSV))
    ap.add_argument("--symbol", type=str, default=DEFAULT_SYMBOL)
    args = ap.parse_args()
    return run(Path(args.csv), args.symbol)


if __name__ == "__main__":
    sys.exit(main())
