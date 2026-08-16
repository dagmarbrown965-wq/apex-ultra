"""APEX ULTRA - W48.0b precondition: Deriv candle epoch alignment (READ-ONLY).

Establishes whether the `epoch` field on a Deriv candle marks the bar's OPEN
time or its CLOSE time. Required by docs/PHASE_48_AMENDMENT_V0_4.md before any
provenance correlation is trusted: a one-bar misalignment between Deriv candles
and a resampled external reference would depress correlation and could reject a
faithful instrument.

METHOD - Deriv is compared against itself, no external data needed.

Fetch the same window at granularity 900 (15-minute) and granularity 60
(1-minute). For a 15-minute bar with epoch E:

  OPEN convention  -> E labels the bar covering [E, E+900), so it should
                      aggregate the 1-minute bars at E .. E+840:
                        open  == open(E)
                        close == close(E+840)
                        high  == max(high) over those 15
                        low   == min(low)  over those 15

  CLOSE convention -> E labels the bar ending at E, covering [E-900, E), so it
                      should aggregate the 1-minute bars at E-900 .. E-60.

Each testable 15-minute bar votes for whichever hypothesis reproduces it. A
clean result is unanimous; anything else means the convention is not what
either hypothesis describes and must be investigated before use.

INSTRUMENT CHOICE - cryBTCUSD. Deliberately a previously-used, already
contaminated instrument: this probe measures API semantics, not market
behaviour, so it must not touch a Phase 48 candidate. BTC is also 24/7, so
there are no session gaps to confuse the aggregation.

SCOPE - computes nothing but the aggregation comparison. No returns, no
correlations, no statistics about any candidate.

Facts reused from tools/fetch_candles.py and tools/screen_candidates.py:
  - one frame per response; collect must be 1
  - candles oldest-first, fields epoch/open/high/low/close
  - `count` is a TIME WINDOW (count * granularity), not a candle cap
  - transport.call() cannot send ticks_history; use _ws_roundtrip

Sends no execution ops. Writes only under engine/output/.

Usage (from the repo root, credentials already in the environment):
    py -m tools.probe_epoch_alignment
    py -m tools.probe_epoch_alignment --symbol cryBTCUSD --bars 20
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from infrastructure.broker.deriv.rest_transport import DerivRestOtpTransport

COARSE = 900
FINE = 60
FINE_PER_COARSE = COARSE // FINE          # 15
OUTPUT_DIR = Path("engine") / "output"
TOL = 1e-9                                 # relative tolerance on price compare


def _parse_ohlc(frames: list) -> tuple:
    """Return (bars, saw_frame, error). bars = {epoch: (o,h,l,c)}."""
    for f in frames:
        if not isinstance(f, dict):
            continue
        if f.get("error"):
            err = f["error"]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            return {}, True, str(msg)
        cs = f.get("candles")
        if cs is None:
            continue
        out = {}
        for k in cs:
            try:
                out[int(k["epoch"])] = (float(k["open"]), float(k["high"]),
                                        float(k["low"]), float(k["close"]))
            except (KeyError, TypeError, ValueError):
                return {}, True, "malformed candle record"
        return out, True, None
    return {}, False, None


def _close(a: float, b: float) -> bool:
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= TOL * scale


def _aggregate(fine: dict, start_epoch: int) -> tuple | None:
    """OHLC of the 15 one-minute bars starting at start_epoch, or None."""
    epochs = [start_epoch + i * FINE for i in range(FINE_PER_COARSE)]
    if any(e not in fine for e in epochs):
        return None
    rows = [fine[e] for e in epochs]
    return (rows[0][0],
            max(r[1] for r in rows),
            min(r[2] for r in rows),
            rows[-1][3])


def probe(symbol: str, bars: int) -> int:
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
    print("W48.0b PRECONDITION - CANDLE EPOCH ALIGNMENT PROBE (read-only)")
    print("=" * 64)
    print(f"symbol : {symbol}   (API-semantics probe; not a candidate)")
    print(f"testing: does epoch mark the bar's OPEN or its CLOSE?")
    print()

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

        res = t._ws_roundtrip(
            {"ticks_history": symbol, "count": 200, "end": "latest",
             "style": "candles", "granularity": COARSE},
            collect=1, timeout=30.0)
        coarse, saw, err = _parse_ohlc(res.get("_raw_frames") or [])
        if err or not saw or not coarse:
            print(f"coarse fetch failed: {err or 'no frame'}")
            return 1
        print(f"15-minute bars fetched: {len(coarse)}")
        time.sleep(2.0)

        # Drop the newest coarse bar: it may still be forming.
        coarse_epochs = sorted(coarse)[:-1]
        # Test the most recent `bars` complete ones.
        test_epochs = coarse_epochs[-bars:]
        # One-minute window must cover [min-900, max+900].
        fine_end = max(test_epochs) + COARSE
        need_seconds = (fine_end - (min(test_epochs) - COARSE)) + COARSE
        count = min(5000, max(200, need_seconds // FINE + 60))

        res = t._ws_roundtrip(
            {"ticks_history": symbol, "count": int(count), "end": int(fine_end),
             "style": "candles", "granularity": FINE},
            collect=1, timeout=30.0)
        fine, saw, err = _parse_ohlc(res.get("_raw_frames") or [])
        if err or not saw or not fine:
            print(f"fine fetch failed: {err or 'no frame'}")
            return 1
        print(f"1-minute  bars fetched: {len(fine)} "
              f"(requested window {int(count) * FINE}s ending {fine_end})")
        print()
    finally:
        try:
            t.close()
        except Exception:
            pass

    votes = {"open": 0, "close": 0, "neither": 0, "untestable": 0}
    rows = []
    for e in test_epochs:
        o, h, l, c = coarse[e]
        agg_open = _aggregate(fine, e)                 # [E, E+900)
        agg_close = _aggregate(fine, e - COARSE)       # [E-900, E)

        def matches(agg):
            return agg is not None and all(
                _close(x, y) for x, y in zip(agg, (o, h, l, c)))

        m_open, m_close = matches(agg_open), matches(agg_close)
        if agg_open is None and agg_close is None:
            verdict = "untestable"
        elif m_open and not m_close:
            verdict = "open"
        elif m_close and not m_open:
            verdict = "close"
        elif m_open and m_close:
            verdict = "ambiguous"
        else:
            verdict = "neither"
        votes[verdict] = votes.get(verdict, 0) + 1
        rows.append({"epoch": e, "verdict": verdict,
                     "coarse": [o, h, l, c],
                     "agg_from_E": list(agg_open) if agg_open else None,
                     "agg_from_E_minus_900": (list(agg_close)
                                              if agg_close else None)})
        print(f"  {e}  -> {verdict}")

    print()
    print("-" * 64)
    for k, v in votes.items():
        if v:
            print(f"  {k:11s}: {v}")

    decided = None
    if votes.get("open", 0) and not votes.get("close", 0) \
            and not votes.get("neither", 0):
        decided = "epoch marks the bar OPEN  ->  bar covers [epoch, epoch+900)"
    elif votes.get("close", 0) and not votes.get("open", 0) \
            and not votes.get("neither", 0):
        decided = "epoch marks the bar CLOSE ->  bar covers [epoch-900, epoch)"

    print()
    if decided:
        print("RESULT: " + decided)
    else:
        print("RESULT: NOT DECIDED. The convention is not cleanly either")
        print("hypothesis. Do NOT proceed to provenance until this is")
        print("understood - inspect the record below before assuming.")
    print("-" * 64)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"probe_epoch_alignment_{symbol}_{max(test_epochs)}.json"
    with open(out, "w") as f:
        json.dump({"symbol": symbol, "granularity_coarse": COARSE,
                   "granularity_fine": FINE, "votes": votes,
                   "decided": decided, "bars": rows}, f, indent=2)
    print(f"Record: {out}")
    return 0 if decided else 2


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Probe Deriv candle epoch alignment (read-only).")
    ap.add_argument("--symbol", type=str, default="cryBTCUSD",
                    help="API-semantics probe instrument (default cryBTCUSD)")
    ap.add_argument("--bars", type=int, default=20,
                    help="how many complete 15-minute bars to test")
    args = ap.parse_args()
    return probe(args.symbol, args.bars)


if __name__ == "__main__":
    sys.exit(main())
