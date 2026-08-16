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

Facts PROBED 2026-08-16 by running this tool:
  - "product_type" is NOT an accepted property of active_symbols. Sending it
    returns "Input validation failed: Properties not allowed: product_type."
    The correct request is {"active_symbols": "brief"} and nothing else.
  - entries do NOT carry a "symbol" key. This platform names it
    "underlying_symbol", with the label in "underlying_symbol_name".
  - entries carry: exchange_is_open, is_trading_suspended, market, pip_size,
    subgroup, submarket, trade_count, underlying_symbol,
    underlying_symbol_name, underlying_symbol_type
  - synthetics ARE identifiable by market ("synthetic_index") and by subgroup
    ("synthetics"). 89 entries: 46 synthetic_index, 25 forex, 12 indices,
    4 commodities, 2 cryptocurrency.
  - underlying_symbol_type is NOT reliable for classification: it reads
    "stockindex" for Volatility 100 (1s) Index. Do not filter on it.
  - `count` IS A TIME WINDOW, NOT A CANDLE CAP. Probed on OTC_HSI: a request
    for count=1000 at granularity=900 returned 205 candles spanning 10.27
    days, and every subsequent page spanned at or under 10.42 days
    (= 1000 * 900s). The server returns whatever candles exist within
    [end - count*granularity, end]. tools/fetch_candles.py lists "per-request
    cap is 1000 candles" among its verified facts; that description is wrong,
    though harmless there because MAX_REQUESTS=100 absorbs the difference.
  - SUSTAINED ticks_history REQUESTS FAIL. A run that screened 3 candidates
    (12 requests) succeeded; a run immediately after failed from candidate 2
    onward with no response frame, for symbols that had just worked. The
    cause is rate limiting or socket death, NOT missing data. This tool now
    aborts on consecutive transport failures rather than recording them as
    per-candidate results - a partial screen presented as a complete one is
    worse than no screen at all.

Facts still ASSUMED and NOT probed:
  - ticks_history accepts the underlying_symbol value as its symbol argument
    (it accepted frxEURUSD and cryBTCUSD in W46.0/W47.1)
  - the exact request budget before throttling; RETRY/backoff below is a
    defensive guess, not a measured limit

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.screen_candidates
    py -m tools.screen_candidates --limit 5        (smoke test)
    py -m tools.screen_candidates --list-only      (enumerate, fetch nothing)
    py -m tools.screen_candidates --resume-from frxGBPUSD
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
SLEEP_BETWEEN_REQUESTS = 2.5      # within a candidate; raised for v0.3 volume
SLEEP_BETWEEN_CANDIDATES = 3.0    # extra pacing between candidates
# `count` is a TIME WINDOW, not a candle cap: the server returns whatever
# exists in [end - count*granularity, end]. At 1000*900s that is 10.42 days
# per request regardless of instrument. A low-duty-cycle market (OTC_HSI:
# short session plus lunch break, ~26 bars/trading day) therefore yields
# ~140 candles per request, not 1000, and needs ~20 pages to reach 2500.
# Early-stop means high-duty-cycle instruments still finish in 3-4.
MAX_PAGES_PER_CANDIDATE = 40
MAX_CONSECUTIVE_EMPTY = 4         # long weekend / market-closed tolerance
WEEKEND_STEP_SECONDS = 86400
MIN_MATCHED_RETURNS = 2500        # Section F criterion 2, raised by Amdt v0.3
INDEPENDENCE_CEILING = 0.30       # Section F criterion 2, |r| strictly below

# Amendment v0.3 correction 1 - structural leg overlap. A cross sharing a leg
# with a previously-used instrument is an algebraic function of it and can
# show near-zero correlation purely through cancellation.
EXCLUDED_LEGS = {"EUR", "USD", "BTC"}
LEG_PREFIXES = ("frx", "cry")


def _legs(symbol: str) -> tuple:
    """Currency legs of a pair symbol, or () if it has no pair structure."""
    for pre in LEG_PREFIXES:
        if symbol.startswith(pre) and len(symbol) == len(pre) + 6:
            rest = symbol[len(pre):]
            return (rest[:3].upper(), rest[3:].upper())
    return ()

RETRY_BACKOFF_SECONDS = 20.0      # wait + reconnect before counting a failure
ABORT_AFTER_CONSECUTIVE_FAILURES = 3

OUTPUT_DIR = Path("engine") / "output"

# Section C.1 - previously used, ineligible for selection.
EXCLUDED_SYMBOLS = {"frxEURUSD", "cryBTCUSD", "R_100"}

# Second defence behind the market/subgroup filter.
SYNTHETIC_PREFIXES = (
    "R_", "1HZ", "BOOM", "CRASH", "STEP", "JD", "RDBEAR", "RDBULL", "WLD",
    "CRYPTIDX", "RB", "STPRNG",
)

REFERENCE_GLOBS = {
    "frxEURUSD": "engine/output/candles_frxEURUSD_900_*.jsonl",
    "cryBTCUSD": "engine/output/candles_cryBTCUSD_900_*.jsonl",
}

TRANSPORT_FAILURE_NOTES = ("no_response_frame", "api_error")


# ----------------------------------------------------------------- helpers

def _pearson(xs: list, ys: list) -> float | None:
    """Pearson correlation. Returns None if undefined (zero variance)."""
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
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
    """Return (candles, saw_frame, error_message).

    An API error is reported SEPARATELY from a legitimate empty response.
    The previous version collapsed the two, which would have hidden a
    rate-limit message behind an innocuous "empty" note.
    """
    for f in frames:
        if not isinstance(f, dict):
            continue
        if f.get("error"):
            err = f["error"]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            code = err.get("code") if isinstance(err, dict) else None
            return [], True, f"{code}: {msg}" if code else str(msg)
        cs = f.get("candles")
        if cs is None:
            continue
        out = []
        for k in cs:
            try:
                out.append((int(k["epoch"]), float(k["close"])))
            except (KeyError, TypeError, ValueError):
                return [], True, "malformed candle record"
        return out, True, None
    return [], False, None


def _enough(series: dict, references: dict) -> bool:
    """True once every reference has MIN_MATCHED_RETURNS matched returns."""
    for ref in references.values():
        cr, _ = _matched_returns(series, ref)
        if len(cr) < MIN_MATCHED_RETURNS:
            return False
    return True


def _fetch_window(t, symbol: str, end_epoch: int, references: dict,
                  verbose: bool = False) -> tuple:
    """Page backwards from end_epoch, stopping as soon as every reference
    has enough matched returns. Returns (epoch->close, note)."""
    series: dict = {}
    end_param = int(end_epoch)
    empty_streak = 0
    for page in range(MAX_PAGES_PER_CANDIDATE):
        res = t._ws_roundtrip(
            {"ticks_history": symbol,
             "count": CANDLES_PER_REQUEST,
             "end": end_param,
             "style": "candles",
             "granularity": GRANULARITY},
            collect=1, timeout=30.0)
        batch, saw_frame, err = _parse_candles(res.get("_raw_frames") or [])
        if err:
            return series, f"api_error: {err}"
        if not saw_frame:
            return series, "no_response_frame"
        if not batch:
            empty_streak += 1
            if verbose:
                print(f"        page {page + 1:2d}: EMPTY (streak "
                      f"{empty_streak}), stepping back a day from {end_param}")
            if empty_streak >= MAX_CONSECUTIVE_EMPTY:
                return series, "history_exhausted_consecutive_empty"
            end_param -= WEEKEND_STEP_SECONDS
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            continue
        empty_streak = 0
        newest = batch[-1][0]
        if verbose:
            span = (batch[-1][0] - batch[0][0]) / 86400.0
            print(f"        page {page + 1:2d}: end={end_param} "
                  f"returned={len(batch):4d} oldest={batch[0][0]} "
                  f"newest={newest} span={span:6.2f}d")
        # SUBSTITUTION DEFENCE - identical rule to fetch_candles.
        if newest > end_param + GRANULARITY:
            return series, "substitution_detected"
        before = len(series)
        for epoch, close in batch:
            series[epoch] = close
        if verbose:
            matched = {k: len(_matched_returns(series, v)[0])
                       for k, v in references.items()}
            print(f"                  new={len(series) - before:4d} "
                  f"unique_total={len(series):5d} matched={matched}")
        if _enough(series, references):
            return series, "sufficient"
        end_param = batch[0][0] - 1
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return series, "max_pages"


# -------------------------------------------------------------------- main

def screen(limit: int | None, list_only: bool, resume_from: str | None,
           debug_symbol: str | None = None) -> int:
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
    ref_end = min(max(s.keys()) for s in references.values())
    print(f"  screening window ends at epoch {ref_end}")
    print()

    t = DerivRestOtpTransport(api_token=token, app_id=app_id or None)
    t.connect()
    results, eligible = [], []
    aborted, abort_reason = False, None
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

        res = t._ws_roundtrip({"active_symbols": "brief"},
                              collect=1, timeout=30.0)
        symbols = None
        for f in res.get("_raw_frames") or []:
            if isinstance(f, dict) and f.get("error"):
                print("active_symbols ERROR: " + str(f["error"].get("message")))
                return 1
            if isinstance(f, dict) and isinstance(f.get("active_symbols"), list):
                symbols = f["active_symbols"]
                break
        if symbols is None:
            print("ASSUMPTION VIOLATED: no 'active_symbols' list in response.")
            return 1
        print(f"active_symbols returned {len(symbols)} entries")

        if not symbols or not isinstance(symbols[0], dict):
            print("ASSUMPTION VIOLATED: entries are not objects.")
            return 1
        sym_key = next((k for k in ("underlying_symbol", "symbol")
                        if k in symbols[0]), None)
        if sym_key is None:
            print("ASSUMPTION VIOLATED: entries carry no symbol key.")
            print("keys present : " + ", ".join(sorted(symbols[0].keys())))
            print("first entry  : " + json.dumps(symbols[0])[:400])
            return 1
        name_key = ("underlying_symbol_name"
                    if "underlying_symbol_name" in symbols[0]
                    else "display_name")
        print(f"symbol key in use: {sym_key}")

        markets_seen: dict = {}
        n_nosym = n_prev = n_synth = n_susp = n_legs = 0
        for s in symbols:
            sym = s.get(sym_key)
            market = (s.get("market") or "").lower()
            subgroup = (s.get("subgroup") or "").lower()
            markets_seen[market] = markets_seen.get(market, 0) + 1
            if not sym:
                n_nosym += 1
                continue
            if s.get("is_trading_suspended"):
                n_susp += 1
                results.append({"symbol": sym, "outcome": "EXCLUDED",
                                "reason": "trading suspended"})
                continue
            if sym in EXCLUDED_SYMBOLS:
                n_prev += 1
                results.append({"symbol": sym, "outcome": "EXCLUDED",
                                "reason": "previously used (Section C.1)"})
                continue
            # NOTE: underlying_symbol_type is unreliable (reads "stockindex"
            # for Volatility 100). Classify on market/subgroup/prefix only.
            if ("synthetic" in market or "synthetic" in subgroup
                    or sym.startswith(SYNTHETIC_PREFIXES)):
                n_synth += 1
                results.append({"symbol": sym, "outcome": "EXCLUDED",
                                "reason": f"synthetic (market={market},"
                                          f" subgroup={subgroup})"})
                continue
            shared = sorted(set(_legs(sym)) & EXCLUDED_LEGS)
            if shared:
                n_legs += 1
                results.append({"symbol": sym, "outcome": "EXCLUDED",
                                "reason": "shares currency leg "
                                          f"{'/'.join(shared)} with a "
                                          "previously-used instrument "
                                          "(Amendment v0.3)"})
                continue
            eligible.append({"symbol": sym, "market": market,
                             "display_name": s.get(name_key)})

        print()
        print("markets present in active_symbols:")
        for m, n in sorted(markets_seen.items(), key=lambda kv: -kv[1]):
            print(f"  {m or '(blank)':24s} {n:3d}")
        print()
        print("selection funnel:")
        print(f"  entries returned      : {len(symbols)}")
        print(f"  skipped, no symbol key: {n_nosym}")
        print(f"  excluded, suspended   : {n_susp}")
        print(f"  excluded, prev. used  : {n_prev}")
        print(f"  excluded, synthetic   : {n_synth}")
        print(f"  excluded, shared leg  : {n_legs}   (Amendment v0.3)")
        print(f"  ELIGIBLE              : {len(eligible)}")
        print()

        if list_only:
            for c in eligible:
                print(f"  {c['symbol']:16s} {c['market']:18s} "
                      f"{c['display_name']}")
            return 0

        if debug_symbol:
            eligible = [c for c in eligible if c["symbol"] == debug_symbol]
            if not eligible:
                print(f"--debug-symbol {debug_symbol}: not in eligible list.")
                return 1
            print(f"--debug-symbol {debug_symbol}: per-page diagnostic run. "
                  "This is a PROBE, not a screen.")
            print()

        if resume_from:
            names = [c["symbol"] for c in eligible]
            if resume_from not in names:
                print(f"--resume-from {resume_from}: not in eligible list.")
                return 1
            skipped = names.index(resume_from)
            eligible = eligible[skipped:]
            print(f"--resume-from {resume_from}: skipping {skipped} already "
                  "screened; MERGE this run's record with the earlier one.")
            print()
        if limit:
            eligible = eligible[:limit]
            print(f"--limit in effect: screening first {len(eligible)}")
            print()

        consecutive_failures = 0
        for i, c in enumerate(eligible, 1):
            sym = c["symbol"]
            print(f"[{i}/{len(eligible)}] {sym}")
            series, note = _fetch_window(t, sym, ref_end, references,
                                         verbose=bool(debug_symbol))

            if note and note.startswith(TRANSPORT_FAILURE_NOTES):
                print(f"      TRANSPORT FAILURE: {note}")
                print(f"      backing off {RETRY_BACKOFF_SECONDS:.0f}s and "
                      "reconnecting, then retrying once")
                time.sleep(RETRY_BACKOFF_SECONDS)
                try:
                    t.close()
                except Exception:
                    pass
                try:
                    t.connect()
                    a = t.call({"authorize": token}, timeout=20.0)
                    if "error" in a:
                        raise RuntimeError(a["error"].get("message"))
                    series, note = _fetch_window(t, sym, ref_end, references)
                except Exception as exc:  # noqa: BLE001
                    note = f"reconnect_failed: {exc}"

            if note and note.startswith(TRANSPORT_FAILURE_NOTES + (
                    "reconnect_failed",)):
                consecutive_failures += 1
                results.append({"symbol": sym, "market": c["market"],
                                "outcome": "TRANSPORT_FAILURE",
                                "fetch_note": note})
                print(f"      unrecovered ({consecutive_failures} in a row)")
                if consecutive_failures >= ABORT_AFTER_CONSECUTIVE_FAILURES:
                    aborted = True
                    abort_reason = (
                        f"{consecutive_failures} consecutive transport "
                        f"failures at candidate {i}/{len(eligible)} ({sym})")
                    for rest in eligible[i:]:
                        results.append({"symbol": rest["symbol"],
                                        "market": rest["market"],
                                        "outcome": "UNSCREENED",
                                        "fetch_note": "run aborted"})
                    print()
                    print("ABORTED: " + abort_reason)
                    break
                time.sleep(SLEEP_BETWEEN_CANDIDATES)
                continue
            consecutive_failures = 0

            row = {"symbol": sym, "market": c["market"],
                   "display_name": c["display_name"],
                   "bars_fetched": len(series), "fetch_note": note,
                   "correlations": {}}
            if not series:
                row["outcome"] = "NO_DATA"
                print(f"      {note}; no data")
                results.append(row)
                time.sleep(SLEEP_BETWEEN_CANDIDATES)
                continue

            verdict, worst = "PASS", 0.0
            for ref_name, ref_series in references.items():
                cr, rr = _matched_returns(series, ref_series)
                r = _pearson(cr, rr)
                row["correlations"][ref_name] = {
                    "n_matched_returns": len(cr),
                    "r": None if r is None else round(r, 4),
                }
                if len(cr) < MIN_MATCHED_RETURNS or r is None:
                    verdict = "INSUFFICIENT"
                    print(f"      vs {ref_name}: n={len(cr)} - not evaluable")
                    continue
                worst = max(worst, abs(r))
                print(f"      vs {ref_name}: n={len(cr)} r={r:+.4f}")
                if abs(r) >= INDEPENDENCE_CEILING and verdict == "PASS":
                    verdict = "FAIL"

            row["max_abs_r"] = round(worst, 4)
            row["outcome"] = verdict
            print(f"      -> {verdict}")
            results.append(row)
            time.sleep(SLEEP_BETWEEN_CANDIDATES)
    finally:
        try:
            t.close()
        except Exception:
            pass

    screened = [r for r in results
                if r.get("outcome") in ("PASS", "FAIL", "INSUFFICIENT",
                                        "NO_DATA")]
    survivors = [r for r in results if r.get("outcome") == "PASS"]
    complete = ((not aborted) and limit is None and resume_from is None
                and debug_symbol is None)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if complete else "_PARTIAL"
    # Filename carries the sample requirement so the v0.3 re-screen cannot
    # overwrite or be confused with the superseded n>=500 record.
    out_path = (OUTPUT_DIR /
                f"screening_w48_0a_{ref_end}_n{MIN_MATCHED_RETURNS}"
                f"{suffix}.json")
    payload = {
        "stage": "W48.0a independence screen",
        "agreement": "docs/PHASE_48_BOUNDARY_AGREEMENT.md v1.0 + v0.1 + v0.2",
        "run_complete": complete,
        "aborted": aborted,
        "abort_reason": abort_reason,
        "limit_applied": limit,
        "resume_from": resume_from,
        "granularity": GRANULARITY,
        "independence_ceiling": INDEPENDENCE_CEILING,
        "min_matched_returns": MIN_MATCHED_RETURNS,
        "screening_window_end_epoch": ref_end,
        "references": {k: len(v) for k, v in references.items()},
        "r_100_note": "exempt per Amendment v0.1 (RNG, tick-only data)",
        "candidates_evaluated": len(screened),
        "results": results,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print()
    print("-" * 64)
    print(f"evaluated: {len(screened)} of {len(eligible)} attempted")
    if not complete:
        print()
        print("*** THIS RUN IS NOT A COMPLETE SCREEN ***")
        if aborted:
            print(f"    aborted: {abort_reason}")
        if limit is not None:
            print(f"    --limit {limit} was applied")
        if resume_from is not None:
            print(f"    --resume-from {resume_from} was applied")
        print("    The survivor list below is NOT the W48.0a result and must")
        print("    NOT be committed as one. Re-run to completion first.")
    print()
    print(f"survivors so far: {len(survivors)}")
    for r in survivors:
        print(f"  {r['symbol']:16s} max|r| = {r['max_abs_r']:.4f}")
    if complete and not survivors:
        print("  NONE - Section C no-survivors rule applies. Do NOT relax a")
        print("  threshold; close the phase with the finding or write a new")
        print("  agreement stating the new threshold and its reason first.")
    print("-" * 64)
    print(f"Screening record: {out_path}")
    if complete:
        print("Stage b (provenance) runs on survivors only, per Amendment v0.2.")
    return 0 if complete else 2


def main() -> int:
    ap = argparse.ArgumentParser(
        description="W48.0a candidate independence screen (read-only).")
    ap.add_argument("--limit", type=int, default=None,
                    help="screen only the first N eligible candidates")
    ap.add_argument("--list-only", action="store_true",
                    help="enumerate eligible candidates and exit")
    ap.add_argument("--resume-from", type=str, default=None,
                    help="start at this symbol (records merge manually)")
    ap.add_argument("--debug-symbol", type=str, default=None,
                    help="per-page diagnostic for one symbol (a PROBE, "
                         "not a screen; always writes _PARTIAL)")
    args = ap.parse_args()
    return screen(args.limit, args.list_only, args.resume_from,
                  args.debug_symbol)


if __name__ == "__main__":
    sys.exit(main())
