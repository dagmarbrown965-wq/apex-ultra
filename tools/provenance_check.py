"""APEX ULTRA - W48.0b step 2: provenance verification (READ-ONLY).

Measures each W48.0a survivor against its independent HistData reference and
applies Section F criterion 1: return correlation r >= 0.95 over n >= 500
matched 15-minute bars.

NOTHING IS HARDCODED THAT COULD DRIFT:

  - the candidate pool is read from the committed W48.0a screening record
    (outcome == PASS), not from a list in this file
  - the clock offset is read from the committed identification record
    (engine/output/reference_offset_*.json); if that record does not carry an
    identified offset, this tool refuses to run
  - the Amendment v0.7 reference rules (sort / drop duplicated minutes /
    complete buckets only) are IMPORTED from tools.identify_reference_offset
    rather than reimplemented, so there is exactly one implementation of them
    and it is the one already verified against the July GBPJPY file

Per Amendment v0.4 the four OTC_ index survivors are NOT VERIFIABLE - no
independent reference is obtainable - and are excluded from this stage. They are
carried into the record as such, not as criterion-1 failures.

Per Amendment v0.8, if several candidates clear the floor the dataset is the one
with the LOWEST independence max|r|, read from the screening record. Provenance
is a floor, not a quantity to maximise. That rule is disclosed in v0.8 as not
outcome-blind.

DISCLOSURE carried into the output: frxGBPJPY's figure is not independent of the
clock identification, because the offset was identified using frxGBPJPY. The
other six are measured at an offset fixed before they were touched.

SCOPE - matched counts, return correlations, and return standard deviations
against the reference. Nothing else.

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.provenance_check
    py -m tools.provenance_check --dry-run          (no network; report readiness)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport

# Single implementation of the Amendment v0.7 rules and the maths - imported,
# not copied. These were verified against DAT_ASCII_GBPJPY_M1_202607.csv.
from tools.identify_reference_offset import (
    GRANULARITY,
    MAX_CONSECUTIVE_EMPTY,
    MAX_PAGES,
    SLEEP_BETWEEN_REQUESTS,
    WEEKEND_STEP_SECONDS,
    load_reference,
    matched_returns,
    pearson,
    sha256,
    stdev,
    _parse,
)

PROVENANCE_FLOOR = 0.95          # Section F criterion 1
MIN_MATCHED_RETURNS = 500        # Section F criterion 1

SLEEP_BETWEEN_CANDIDATES = 3.0
AUTH_RETRIES = 4                 # accounts endpoint fails intermittently
AUTH_BACKOFF_SECONDS = 15.0
ABORT_AFTER_CONSECUTIVE_FAILURES = 3

OUTPUT_DIR = Path("engine") / "output"
REFERENCE_DIR = Path("reference")
SCREENING_GLOB = "engine/output/screening_w48_0a_*_n2500.json"
OFFSET_GLOB = "engine/output/reference_offset_*.json"

# frxGBPJPY -> GBPJPY, for matching HistData filenames
def pair_code(symbol: str) -> str:
    return symbol[3:] if symbol.startswith(("frx", "cry")) else symbol


def load_screening() -> tuple:
    paths = sorted(glob.glob(SCREENING_GLOB))
    paths = [p for p in paths if "_PARTIAL" not in p]
    if not paths:
        raise SystemExit(f"BLOCKED: no complete screening record matching {SCREENING_GLOB}")
    path = paths[-1]
    with open(path) as f:
        rec = json.load(f)
    if not rec.get("run_complete"):
        raise SystemExit(f"BLOCKED: screening record {path} is not a complete run")
    survivors = [r for r in rec["results"] if r.get("outcome") == "PASS"]
    return path, rec, survivors


def load_offset() -> tuple:
    paths = sorted(glob.glob(OFFSET_GLOB))
    if not paths:
        raise SystemExit(f"BLOCKED: no identification record matching {OFFSET_GLOB}")
    path = paths[-1]
    with open(path) as f:
        rec = json.load(f)
    ident = rec.get("identified")
    if not ident:
        raise SystemExit(
            f"BLOCKED: {path} carries no identified offset. Amendment v0.7 Rule 3 "
            "forbids proceeding on an unidentified alignment.")
    return path, ident


def find_reference(code: str) -> Path | None:
    hits = sorted(REFERENCE_DIR.glob(f"DAT_ASCII_{code}_M1_*.csv"))
    return hits[-1] if hits else None


def fetch_deriv(t, symbol: str, end_epoch: int, back_to: int) -> dict:
    series: dict = {}
    end_param = int(end_epoch)
    empty = 0
    for page in range(MAX_PAGES):
        res = t._ws_roundtrip(
            {"ticks_history": symbol, "count": 1000, "end": end_param,
             "style": "candles", "granularity": GRANULARITY},
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
        if newest > end_param + GRANULARITY:
            print(f"        page {page+1}: SUBSTITUTION DETECTED; batch discarded")
            break
        series.update(batch)
        oldest = min(batch)
        print(f"        page {page+1:2d}: {len(batch):5d} bars, oldest {oldest}, total {len(series)}")
        if oldest <= back_to:
            break
        end_param = oldest - 1
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return series


def connect_and_authorize(token: str, app_id: str):
    """The accounts endpoint fails intermittently - observed twice on
    2026-08-19, then succeeded twice with identical credentials. Retry."""
    last = None
    for attempt in range(1, AUTH_RETRIES + 1):
        t = DerivRestOtpTransport(api_token=token, app_id=app_id or None)
        try:
            t.connect()
            auth = t.call({"authorize": token}, timeout=20.0)
            if "error" in auth:
                last = str(auth["error"].get("message"))
                print(f"  auth attempt {attempt}/{AUTH_RETRIES} failed: {last}")
                try:
                    t.close()
                except Exception:
                    pass
                if attempt < AUTH_RETRIES:
                    time.sleep(AUTH_BACKOFF_SECONDS)
                continue
            acct = auth.get("authorize", {})
            if acct.get("is_virtual") != 1:
                try:
                    t.close()
                except Exception:
                    pass
                raise SystemExit("BLOCKED: account is not virtual/demo.")
            print(f"  auth ok on attempt {attempt} "
                  f"(virtual account {acct.get('loginid')})")
            return t
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            print(f"  auth attempt {attempt}/{AUTH_RETRIES} error: {last}")
            try:
                t.close()
            except Exception:
                pass
            if attempt < AUTH_RETRIES:
                time.sleep(AUTH_BACKOFF_SECONDS)
    raise SystemExit(f"BLOCKED: authorize failed {AUTH_RETRIES} times; last: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description="W48.0b provenance verification (read-only).")
    ap.add_argument("--dry-run", action="store_true",
                    help="report readiness without touching the network")
    args = ap.parse_args()

    if os.environ.get("LIVE_TRADING", "false").strip().lower() in ("1", "true", "yes", "on"):
        print("BLOCKED: LIVE_TRADING is enabled; refusing to run.")
        return 1

    screen_path, screen_rec, survivors = load_screening()
    offset_path, ident = load_offset()
    hours, bars = ident["hours"], ident["bars"]

    print("=" * 72)
    print("W48.0b STEP 2 - PROVENANCE VERIFICATION (read-only)")
    print("=" * 72)
    print(f"screening record  : {screen_path}")
    print(f"offset record     : {offset_path}")
    print(f"identified offset : UTC{hours:+d}, bar shift {bars:+d} "
          f"(r={ident['r']:+.5f}, n={ident['n']})")
    print(f"floor             : r >= {PROVENANCE_FLOOR} over n >= {MIN_MATCHED_RETURNS}")
    print(f"survivors in scope: {len(survivors)}")
    print()

    # Amendment v0.4: OTC_ index products are NOT VERIFIABLE, not failures.
    plan = []
    for s in survivors:
        sym = s["symbol"]
        if not sym.startswith("frx"):
            plan.append({"symbol": sym, "independence_max_abs_r": s.get("max_abs_r"),
                         "outcome": "NOT_VERIFIABLE",
                         "reason": "no obtainable independent reference (Amendment v0.4)"})
            continue
        ref_path = find_reference(pair_code(sym))
        plan.append({"symbol": sym, "independence_max_abs_r": s.get("max_abs_r"),
                     "reference": str(ref_path) if ref_path else None})

    todo = [p for p in plan if "reference" in p and p["reference"]]
    missing = [p for p in plan if "reference" in p and not p["reference"]]

    print("READINESS")
    for p in plan:
        if p.get("outcome") == "NOT_VERIFIABLE":
            print(f"  {p['symbol']:12s} excluded  - {p['reason']}")
        elif p["reference"]:
            print(f"  {p['symbol']:12s} ready     - {Path(p['reference']).name}")
        else:
            print(f"  {p['symbol']:12s} NO REFERENCE in {REFERENCE_DIR}/")
    print()
    if missing:
        print(f"{len(missing)} candidate(s) have no reference file. They will be recorded")
        print("as NOT_VERIFIABLE for this run, which is a statement about available")
        print("data and not about the instrument. Download them and re-run for a")
        print("complete result.")
        print()
    if args.dry_run:
        print("--dry-run: nothing fetched, nothing written.")
        return 0
    if not todo:
        print("BLOCKED: no candidate has a reference file.")
        return 1

    token = os.environ.get("DERIV_API_TOKEN", "")
    app_id = os.environ.get("DERIV_APP_ID", "")
    if not token:
        print("BLOCKED: DERIV_API_TOKEN not set.")
        return 1

    results = list(p for p in plan if p.get("outcome") == "NOT_VERIFIABLE")
    for p in missing:
        results.append({**p, "outcome": "NOT_VERIFIABLE",
                        "reason": f"no reference file present in {REFERENCE_DIR}/"})

    t = connect_and_authorize(token, app_id)
    aborted, abort_reason = False, None
    consecutive = 0
    try:
        for i, p in enumerate(todo, 1):
            sym = p["symbol"]
            ref_path = Path(p["reference"])
            print(f"[{i}/{len(todo)}] {sym}  ({ref_path.name})")
            ref, rstats = load_reference(ref_path)
            digest = sha256(ref_path)
            if not ref:
                results.append({**p, "outcome": "NO_DATA",
                                "reason": "no complete buckets in reference",
                                "reference_sha256": digest,
                                "reference_stats": rstats})
                continue
            lo, hi = min(ref), max(ref)
            try:
                der = fetch_deriv(t, sym, hi + 2 * 86400, lo - 2 * 86400)
                consecutive = 0
            except Exception as exc:  # noqa: BLE001
                consecutive += 1
                print(f"      TRANSPORT FAILURE: {exc}  ({consecutive} in a row)")
                results.append({**p, "outcome": "TRANSPORT_FAILURE",
                                "reason": str(exc), "reference_sha256": digest})
                if consecutive >= ABORT_AFTER_CONSECUTIVE_FAILURES:
                    aborted = True
                    abort_reason = f"{consecutive} consecutive transport failures at {sym}"
                    for rest in todo[i:]:
                        results.append({**rest, "outcome": "UNSCREENED",
                                        "reason": "run aborted"})
                    print(f"\nABORTED: {abort_reason}")
                    break
                time.sleep(SLEEP_BETWEEN_CANDIDATES)
                continue

            rr, dd = matched_returns(ref, der, hours, bars)
            r = pearson(rr, dd) if len(rr) >= 2 else None
            n = len(rr)
            if n < MIN_MATCHED_RETURNS or r is None:
                verdict = "INSUFFICIENT"
            elif r >= PROVENANCE_FLOOR:
                verdict = "PASS"
            else:
                verdict = "FAIL"
            print(f"      n={n}  r={'n/a' if r is None else f'{r:+.5f}'}  -> {verdict}")
            results.append({
                **p, "outcome": verdict,
                "reference_sha256": digest, "reference_stats": rstats,
                "deriv_bars": len(der), "n_matched_returns": n,
                "r": None if r is None else round(r, 6),
                "sd_reference": None if not rr else round(stdev(rr), 8),
                "sd_deriv": None if not dd else round(stdev(dd), 8),
            })
            time.sleep(SLEEP_BETWEEN_CANDIDATES)
    finally:
        try:
            t.close()
        except Exception:
            pass

    passers = [r for r in results if r.get("outcome") == "PASS"]
    complete = (not aborted) and not missing

    # Amendment v0.8: lowest independence max|r| among passers.
    selected = None
    if passers:
        ranked = sorted(passers, key=lambda x: x["independence_max_abs_r"])
        selected = ranked[0]

    print()
    print("-" * 72)
    print(f"{'symbol':12s} {'indep max|r|':>13s} {'prov r':>9s} {'n':>7s}   outcome")
    for r in sorted(results, key=lambda x: (x.get("outcome") != "PASS",
                                            x.get("independence_max_abs_r") or 9)):
        ind = r.get("independence_max_abs_r")
        pr = r.get("r")
        print(f"{r['symbol']:12s} {('' if ind is None else f'{ind:.4f}'):>13s} "
              f"{('' if pr is None else f'{pr:+.5f}'):>9s} "
              f"{str(r.get('n_matched_returns','')):>7s}   {r['outcome']}")
    print()
    if not complete:
        print("*** THIS RUN IS NOT A COMPLETE VERIFICATION ***")
        if aborted:
            print(f"    aborted: {abort_reason}")
        if missing:
            print(f"    {len(missing)} candidate(s) had no reference file")
        print("    Any selection below is PROVISIONAL and must not be committed")
        print("    as the Phase 48 instrument. Complete the run first.")
        print()
    if selected:
        print(f"SELECTED (Amendment v0.8, lowest independence max|r| among passers):")
        print(f"    {selected['symbol']}  independence max|r| = "
              f"{selected['independence_max_abs_r']:.4f}  provenance r = {selected['r']:+.5f}")
        if selected["symbol"] == "frxGBPJPY":
            print("    DISCLOSURE: frxGBPJPY's provenance figure is not independent of")
            print("    the clock identification, which was performed on frxGBPJPY.")
    elif complete:
        print("NO CANDIDATE CLEARED THE FLOOR.")
        print("Section C's no-survivors rule governs: close the phase with that")
        print("finding. Do NOT relax the threshold.")
    print("-" * 72)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if complete else "_PARTIAL"
    out = OUTPUT_DIR / f"provenance_w48_0b{suffix}.json"
    with open(out, "w") as f:
        json.dump({
            "stage": "W48.0b step 2 - provenance verification",
            "agreement": "docs/PHASE_48_BOUNDARY_AGREEMENT.md v1.0 + v0.1-v0.8",
            "run_complete": complete,
            "aborted": aborted,
            "abort_reason": abort_reason,
            "screening_record": screen_path,
            "offset_record": offset_path,
            "identified_offset": ident,
            "provenance_floor": PROVENANCE_FLOOR,
            "min_matched_returns": MIN_MATCHED_RETURNS,
            "selection_rule": "lowest independence max|r| among passers (Amendment v0.8)",
            "selected": None if not selected else selected["symbol"],
            "disclosure": ("frxGBPJPY's provenance figure is not independent of the "
                           "clock identification, which was performed on frxGBPJPY"),
            "results": results,
        }, f, indent=2)
    print(f"Record: {out}")
    return 0 if complete else 2


if __name__ == "__main__":
    sys.exit(main())
