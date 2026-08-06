"""APEX ULTRA - W46.0: EUR/USD candle history fetch (Phase 46, READ-ONLY).

Pages `ticks_history` backwards in candle mode to assemble a 15-minute OHLC
series for offline evaluation. Governed by
docs/PHASE_46_BOUNDARY_AGREEMENT.md.

Verified facts this tool relies on (probed 2026-08-05, not assumed):
  - a candles response arrives in ONE frame; collect must be 1
  - candles are ordered OLDEST-FIRST, fields: epoch/open/high/low/close
  - `end` accepts an epoch integer; the batch ends AT that epoch
  - per-request cap is 1000 candles
  - WEEKENDS return {"candles": []} -- normal, NOT exhaustion. Forex is
    closed Friday evening to Sunday evening.
  - PAST THE HISTORY BOUNDARY Deriv SILENTLY RETURNS CURRENT DATA while
    echoing the requested `end` correctly. A naive loop would collect
    thousands of duplicate current candles and believe it succeeded.
    This tool verifies every batch against the requested range.
  - transport.call() CANNOT send this request (its dispatcher matches the
    key "ticks"), so _ws_roundtrip is used directly, as get_tick() does.

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.fetch_candles
    py -m tools.fetch_candles --days 300
    py -m tools.fetch_candles --days 3      (smoke test)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport

SYMBOL = "frxEURUSD"
GRANULARITY = 900                 # 15-minute bars
CANDLES_PER_REQUEST = 1000        # observed server cap
SLEEP_BETWEEN_REQUESTS = 1.0
MAX_REQUESTS = 100                # ~23 expected for 300 days; generous cap
MAX_CONSECUTIVE_EMPTY = 4         # long weekend + holiday tolerance
WEEKEND_STEP_SECONDS = 86400      # step back a day on an empty response
OUTPUT_DIR = Path("engine") / "output"


def _parse_candles(frames: list) -> tuple:
    """Return (candles, saw_frame). candles = [(epoch, o, h, l, c), ...]
    oldest-first. saw_frame distinguishes 'valid empty' from 'no response'."""
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
                out.append((int(k["epoch"]), float(k["open"]), float(k["high"]),
                            float(k["low"]), float(k["close"])))
            except (KeyError, TypeError, ValueError):
                return [], True
        return out, True
    return [], False


def fetch(days: float) -> int:
    if os.environ.get("LIVE_TRADING", "false").strip().lower() in (
            "1", "true", "yes", "on"):
        print("BLOCKED: LIVE_TRADING is enabled; refusing to run.")
        return 1

    token = os.environ.get("DERIV_API_TOKEN", "")
    app_id = os.environ.get("DERIV_APP_ID", "")
    if not token:
        print("BLOCKED: DERIV_API_TOKEN not set.")
        return 1

    target_seconds = days * 86400.0
    candles: dict = {}            # epoch -> (o, h, l, c), dedupes overlaps
    end_param = "latest"
    requests_made = 0
    empty_streak = 0
    empty_total = 0
    newest_epoch = None
    oldest_epoch = None
    stop_reason = "target_reached"
    substitution_note = None

    print("=" * 64)
    print("W46.0 - EUR/USD CANDLE HISTORY FETCH (read-only)")
    print("=" * 64)
    print(f"symbol        : {SYMBOL}")
    print(f"granularity   : {GRANULARITY}s (15-minute bars)")
    print(f"target span   : {days} days")
    print(f"per request   : {CANDLES_PER_REQUEST} candles")
    print()

    t = DerivRestOtpTransport(api_token=token, app_id=app_id or None)
    t.connect()
    try:
        auth = t.call({"authorize": token}, timeout=20.0)
        if "error" in auth:
            print("AUTH FAILED: " + str(auth["error"].get("message")))
            return 1
        acct = auth.get("authorize", {})
        if acct.get("is_virtual") != 1:
            print("BLOCKED: account is not virtual/demo.")
            return 1
        print("auth ok (virtual account confirmed)")
        print()

        while requests_made < MAX_REQUESTS:
            res = t._ws_roundtrip(
                {"ticks_history": SYMBOL,
                 "count": CANDLES_PER_REQUEST,
                 "end": end_param,
                 "style": "candles",
                 "granularity": GRANULARITY},
                collect=1, timeout=30.0)
            requests_made += 1

            batch, saw_frame = _parse_candles(res.get("_raw_frames") or [])

            if not saw_frame:
                stop_reason = "no_response_frame"
                print(f"  request {requests_made}: no response frame; stopping.")
                break

            if not batch:
                # empty is normal at weekends: step back a day and retry
                empty_streak += 1
                empty_total += 1
                if empty_streak >= MAX_CONSECUTIVE_EMPTY:
                    stop_reason = "history_exhausted_consecutive_empty"
                    print(f"  request {requests_made}: {empty_streak} consecutive "
                          "empty responses; treating history as exhausted.")
                    break
                if end_param == "latest":
                    stop_reason = "empty_at_latest"
                    print("  empty response at end=latest; stopping.")
                    break
                end_param = int(end_param) - WEEKEND_STEP_SECONDS
                print(f"  request {requests_made}: empty (weekend/holiday), "
                      f"stepping back a day to {end_param}")
                time.sleep(SLEEP_BETWEEN_REQUESTS)
                continue

            empty_streak = 0
            batch_oldest = batch[0][0]
            batch_newest = batch[-1][0]

            # SUBSTITUTION DEFENCE: past the boundary Deriv returns current
            # data while echoing the requested end. If the newest candle is
            # materially newer than what we asked for, discard and stop.
            if isinstance(end_param, int) and batch_newest > end_param + GRANULARITY:
                stop_reason = "history_boundary_substitution"
                substitution_note = {
                    "requested_end": end_param,
                    "returned_newest": batch_newest,
                    "excess_seconds": batch_newest - end_param,
                }
                print(f"  request {requests_made}: SUBSTITUTION DETECTED -- "
                      f"asked for end={end_param}, got newest={batch_newest} "
                      f"({(batch_newest - end_param) / 86400.0:.1f} days newer). "
                      "Batch discarded; history boundary reached.")
                break

            for epoch, o, h, l, c in batch:
                candles[epoch] = (o, h, l, c)

            if newest_epoch is None or batch_newest > newest_epoch:
                newest_epoch = batch_newest
            if oldest_epoch is None or batch_oldest < oldest_epoch:
                oldest_epoch = batch_oldest

            span_days = (newest_epoch - oldest_epoch) / 86400.0
            print(f"  request {requests_made:3d}: {len(batch):5d} candles, "
                  f"oldest {batch_oldest}, span {span_days:6.2f} d, "
                  f"total {len(candles)}")

            if (newest_epoch - oldest_epoch) >= target_seconds:
                stop_reason = "target_reached"
                break

            end_param = batch_oldest - 1
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        else:
            stop_reason = "max_requests_hit"
    finally:
        try:
            t.close()
        except Exception:
            pass

    if not candles:
        print("\nNo candles fetched. Nothing written.")
        return 1

    ordered = sorted(candles.items())
    epochs = [e for e, _ in ordered]

    largest_gap = 0
    gap_at = None
    gaps_over_expected = 0
    for i in range(1, len(epochs)):
        d = epochs[i] - epochs[i - 1]
        if d > GRANULARITY:
            gaps_over_expected += 1
        if d > largest_gap:
            largest_gap = d
            gap_at = epochs[i - 1]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"candles_{SYMBOL}_{GRANULARITY}_{epochs[0]}_{epochs[-1]}"
    data_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(data_path, "w") as f:
        for epoch, (o, h, l, c) in ordered:
            f.write(json.dumps({"epoch": epoch, "open": o, "high": h,
                                "low": l, "close": c}) + "\n")

    span_seconds = epochs[-1] - epochs[0]
    summary = {
        "symbol": SYMBOL,
        "granularity": GRANULARITY,
        "data_path": str(data_path),
        "candle_count": len(ordered),
        "first_epoch": epochs[0],
        "last_epoch": epochs[-1],
        "span_seconds": span_seconds,
        "span_days": round(span_seconds / 86400.0, 3),
        "requests_made": requests_made,
        "empty_responses": empty_total,
        "stop_reason": stop_reason,
        "substitution_note": substitution_note,
        "largest_gap_seconds": largest_gap,
        "largest_gap_after_epoch": gap_at,
        "gaps_over_granularity_count": gaps_over_expected,
        "candles_per_request": CANDLES_PER_REQUEST,
        "note": ("Gaps larger than the granularity are expected at weekends "
                 "(forex closes Fri evening to Sun evening) and are reported, "
                 "never smoothed or backfilled."),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("FETCH SUMMARY")
    for k, v in summary.items():
        if k == "note":
            continue
        print(f"  {k:30s}: {v}")
    print("-" * 64)
    print(f"Data file    : {data_path}")
    print(f"Summary file : {summary_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fetch EUR/USD 15-minute candle history (read-only).")
    ap.add_argument("--days", type=float, default=300.0,
                    help="target span in days (default 300, per the agreement)")
    args = ap.parse_args()
    return fetch(args.days)


if __name__ == "__main__":
    sys.exit(main())
