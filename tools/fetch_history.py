"""APEX ULTRA - W45.0b: R_100 tick history fetch (Phase 45, READ-ONLY).

Pages `ticks_history` backwards to assemble a contiguous tick series for
offline evaluation. Governed by docs/PHASE_45_BOUNDARY_AGREEMENT.md and
docs/PHASE_45_AMENDMENT_V0_2.md.

Verified facts this tool relies on (probed 2026-07-24, not assumed):
  - a ticks_history response arrives in ONE frame; collect must be 1
    (collect>1 blocks until timeout because Deriv sends nothing further)
  - history.prices / history.times are ordered OLDEST-FIRST
  - `end` accepts an epoch integer; the batch ends AT that epoch
  - transport.call() CANNOT send this request (its dispatcher matches the
    key "ticks" and would return UnrecognisedRequest), so _ws_roundtrip
    is used directly, exactly as get_tick() does internally

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.fetch_history
    py -m tools.fetch_history --days 14
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport

SYMBOL = "R_100"
TICKS_PER_REQUEST = 1000
SLEEP_BETWEEN_REQUESTS = 1.0     # be polite; Deriv throttles
MAX_REQUESTS = 400               # hard stop; ~46 days at 5000 ticks/request
OUTPUT_DIR = Path("engine") / "output"
EXPECTED_TICK_SECONDS = 2        # R_100 ticks every 2 seconds


def _parse_history_frame(frames: list) -> list:
    """Return [(epoch, quote), ...] oldest-first, or [] if the shape differs.

    Deliberately does NOT reuse _parse_tick_history from the transport:
    that helper returns only prices[-1]/times[-1] (it was written for the
    count=1 case) and would silently discard the batch.
    """
    for f in frames:
        if not isinstance(f, dict):
            continue
        if f.get("error"):
            return []
        hist = f.get("history")
        if isinstance(hist, dict) and hist.get("prices") and hist.get("times"):
            prices = hist["prices"]
            times = hist["times"]
            if len(prices) != len(times):
                return []
            out = []
            for p, e in zip(prices, times):
                try:
                    out.append((int(e), float(p)))
                except (TypeError, ValueError):
                    return []
            return out
    return []


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
    ticks: dict = {}          # epoch -> quote (dedupes overlapping batches)
    end_param = "latest"
    requests_made = 0
    newest_epoch = None
    oldest_epoch = None
    stop_reason = "target_reached"

    print("=" * 64)
    print("W45.0b - R_100 TICK HISTORY FETCH (read-only)")
    print("=" * 64)
    print(f"symbol        : {SYMBOL}")
    print(f"target span   : {days} days ({int(target_seconds)} s)")
    print(f"per request   : {TICKS_PER_REQUEST} ticks")
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
                 "count": TICKS_PER_REQUEST,
                 "end": end_param,
                 "style": "ticks"},
                collect=1, timeout=20.0)
            requests_made += 1

            batch = _parse_history_frame(res.get("_raw_frames") or [])
            if not batch:
                stop_reason = "empty_or_unrecognised_response"
                print(f"  request {requests_made}: no usable data; stopping.")
                break

            for epoch, quote in batch:
                ticks[epoch] = quote

            batch_oldest = batch[0][0]
            batch_newest = batch[-1][0]
            if newest_epoch is None or batch_newest > newest_epoch:
                newest_epoch = batch_newest
            if oldest_epoch is None or batch_oldest < oldest_epoch:
                oldest_epoch = batch_oldest

            span_days = (newest_epoch - oldest_epoch) / 86400.0
            print(f"  request {requests_made:3d}: {len(batch):5d} ticks, "
                  f"oldest {batch_oldest}, span so far {span_days:.2f} d, "
                  f"total {len(ticks)}")

            if batch_oldest >= (end_param if isinstance(end_param, int) else batch_oldest + 1):
                if requests_made > 1:
                    stop_reason = "history_exhausted_no_progress"
                    print("  no backward progress; history exhausted.")
                    break

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

    if not ticks:
        print("\nNo ticks fetched. Nothing written.")
        return 1

    ordered = sorted(ticks.items())
    epochs = [e for e, _ in ordered]

    # contiguity: report the largest gap; never smooth or invent ticks
    largest_gap = 0
    gap_at = None
    gaps_over_expected = 0
    for i in range(1, len(epochs)):
        d = epochs[i] - epochs[i - 1]
        if d > EXPECTED_TICK_SECONDS:
            gaps_over_expected += 1
        if d > largest_gap:
            largest_gap = d
            gap_at = epochs[i - 1]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"ticks_{SYMBOL}_{epochs[0]}_{epochs[-1]}"
    data_path = OUTPUT_DIR / f"{stem}.jsonl"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    with open(data_path, "w") as f:
        for epoch, quote in ordered:
            f.write(json.dumps({"epoch": epoch, "quote": quote}) + "\n")

    span_seconds = epochs[-1] - epochs[0]
    summary = {
        "symbol": SYMBOL,
        "data_path": str(data_path),
        "tick_count": len(ordered),
        "first_epoch": epochs[0],
        "last_epoch": epochs[-1],
        "span_seconds": span_seconds,
        "span_days": round(span_seconds / 86400.0, 3),
        "requests_made": requests_made,
        "stop_reason": stop_reason,
        "expected_tick_seconds": EXPECTED_TICK_SECONDS,
        "largest_gap_seconds": largest_gap,
        "largest_gap_after_epoch": gap_at,
        "gaps_over_expected_count": gaps_over_expected,
        "ticks_per_request": TICKS_PER_REQUEST,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print("-" * 64)
    print("FETCH SUMMARY")
    for k, v in summary.items():
        print(f"  {k:26s}: {v}")
    print("-" * 64)
    print(f"Data file    : {data_path}")
    print(f"Summary file : {summary_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch R_100 tick history (read-only).")
    ap.add_argument("--days", type=float, default=14.0,
                    help="target span in days (default 14, per amendment v0.2)")
    args = ap.parse_args()
    return fetch(args.days)


if __name__ == "__main__":
    sys.exit(main())


