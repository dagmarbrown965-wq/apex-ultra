"""runner - orchestrate engine cycles (feed -> ... -> emit).

Phase 42.0B-M0 demonstration flow (unchanged, default):

    snapshot.json
        -> CapturedSnapshotFeed.snapshot()
        -> ReferenceMA.evaluate()        (Decision | None)
        -> SimpleRegime.classify()       (regime label)
        -> DescriptiveBracket.bracket()  (descriptive metadata)
        -> build_signal()                (canonical v1.0 dict)
        -> JsonlEmitter.append()         (one JSONL line)

Phase 43 addition (opt-in, --mode live): the SAME chain fed by
LiveReadonlyFeed instead of the captured snapshot, in a bounded observation
loop. Governed by docs/PHASE_43_BOUNDARY_AGREEMENT.md. The live loop:

  - reads ticks via the allowlisted read-only surface ONLY (network+auth,
    demo-account-only, enforced by the adapter's own guards);
  - buffers closes (close = mid, pinned) with a 20-close warmup;
  - emits at most one signal per NEW close, so emitted timestamps are
    strictly increasing (CP5) by construction;
  - writes to a per-session file live_signals_<date>_session<NNN>.jsonl -
    sessions never silently mix;
  - is bounded: --max-signals (default 50) or Ctrl+C, whichever first;
  - sends NO orders. There is no code path to any execution surface here.

Phase 42.1 addition (opt-in, --strategy): the live loop can select which
strategy is the producer. Default remains reference_ma, so the default
invocation is unchanged. Governed by docs/PHASE_42_1_BOUNDARY_AGREEMENT.md.
run_once is UNTOUCHED and always uses ReferenceMA (42.0C regression path).

Imports nothing from any broker or execution module at module level. The
default invocation `py -m engine.runner` behaves exactly as it did in 42.0B.
"""
from __future__ import annotations

import os

from engine.assemble.signal_builder import build_signal
from engine.emit.jsonl_writer import JsonlEmitter
from engine.feed.snapshot import CapturedSnapshotFeed
from engine.regime.simple import SimpleRegime
from engine.risk.descriptive_bracket import DescriptiveBracket
from engine.strategy.ema_cross import EmaCross
from engine.strategy.reference_ma import ReferenceMA

# Default paths, resolved relative to this file so the runner works regardless
# of the current working directory.
_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SNAPSHOT = os.path.join(_ENGINE_DIR, "output", "sample_snapshot.json")
DEFAULT_OUTPUT = os.path.join(_ENGINE_DIR, "output", "live_signals.jsonl")
OUTPUT_DIR = os.path.join(_ENGINE_DIR, "output")

# Phase 42.1: named strategy classes selectable in live mode. run_once does
# NOT consult this table; the snapshot/regression path is pinned to
# ReferenceMA and is byte-identical to 42.0B.
STRATEGY_CLASSES = {
    "reference_ma": ReferenceMA,
    "ema_cross": EmaCross,
}


def run_once(
    snapshot_path: str = DEFAULT_SNAPSHOT,
    output_path: str = DEFAULT_OUTPUT,
    symbol: str = "R_100",
) -> "dict | None":
    """Run one feed->strategy->regime->risk->assemble->emit cycle.

    Returns the emitted signal dict, or None if the strategy produced no signal.
    """
    feed = CapturedSnapshotFeed(snapshot_path)
    strategy = ReferenceMA()
    regime_detector = SimpleRegime()
    risk = DescriptiveBracket()
    emitter = JsonlEmitter(output_path)

    snap = feed.snapshot(symbol)

    decision = strategy.evaluate(snap)
    if decision is None:
        return None

    regime = regime_detector.classify(snap)
    bracket = risk.bracket(decision, snap)
    signal = build_signal(decision, regime, bracket, snap, strategy.name)

    emitter.append(signal)
    return signal


# --------------------------------------------------------------------------- #
# Phase 43 - live observation loop (opt-in via --mode live)
# --------------------------------------------------------------------------- #
def next_session_path(output_dir: str = OUTPUT_DIR, date_str: str = "") -> str:
    """Return a fresh per-session output path; never reuses an existing file.

    Pattern: live_signals_<YYYY-MM-DD>_session<NNN>.jsonl - a restart rotates
    to a new file, so sessions never silently mix (Boundary 3).
    """
    import datetime
    import re

    if not date_str:
        date_str = datetime.date.today().isoformat()
    pattern = re.compile(
        r"^live_signals_" + re.escape(date_str) + r"_session(\d{3})\.jsonl$")
    highest = 0
    if os.path.isdir(output_dir):
        for name in os.listdir(output_dir):
            m = pattern.match(name)
            if m:
                highest = max(highest, int(m.group(1)))
    return os.path.join(
        output_dir, f"live_signals_{date_str}_session{highest + 1:03d}.jsonl")


def run_live(
    *,
    feed=None,
    output_path: str = "",
    symbol: str = "R_100",
    max_signals: int = 50,
    poll_interval: float = 1.0,
    max_polls: int = 0,
    strategy_name: str = "reference_ma",
) -> dict:
    """Bounded live observation loop. Returns a summary dict (also printed).

    feed=None builds a real LiveReadonlyFeed from DERIV_API_TOKEN /
    DERIV_APP_ID env vars (network). Tests inject a fake-adapter feed.
    max_polls=0 means unbounded polls (stop on max_signals or Ctrl+C).
    strategy_name selects the producer (Phase 42.1); default reference_ma
    keeps prior behavior identical.
    """
    import time as _time

    if os.environ.get("LIVE_TRADING", "false").strip().lower() in (
            "1", "true", "yes", "on"):
        raise SystemExit("BLOCKED: LIVE_TRADING is enabled; refusing to run.")

    if strategy_name not in STRATEGY_CLASSES:
        raise SystemExit(
            f"BLOCKED: unknown strategy '{strategy_name}'. "
            f"Known: {', '.join(sorted(STRATEGY_CLASSES))}")

    if feed is None:
        from engine.feed.live_readonly import LiveReadonlyFeed
        token = os.environ.get("DERIV_API_TOKEN", "")
        if not token:
            raise SystemExit("BLOCKED: DERIV_API_TOKEN not set.")
        feed = LiveReadonlyFeed(
            api_token=token,
            app_id=os.environ.get("DERIV_APP_ID", ""),
            symbol=symbol,
        )

    if not output_path:
        output_path = next_session_path()
    session_id = os.path.basename(output_path)

    strategy = STRATEGY_CLASSES[strategy_name]()
    regime_detector = SimpleRegime()
    risk = DescriptiveBracket()
    emitter = JsonlEmitter(output_path)

    print("=" * 64)
    print("LIVE OBSERVATION (read-only)")
    print("=" * 64)
    print(f"session : {session_id}")
    print(f"symbol  : {symbol}")
    print(f"strategy: {strategy.name}")
    print(f"bound   : {max_signals} signals or Ctrl+C, whichever first")
    if strategy.name == "reference_ma":
        print("NOTE    : ReferenceMA is a PLACEHOLDER. This validates "
              "PLUMBING,")
        print("          not a strategy. Not part of any observation window.")
    print()

    signals_emitted = 0
    emit_failures = 0
    last_emitted_ts = float("-inf")
    polls = 0
    stopped_by = "max_signals"

    feed.connect()
    try:
        while signals_emitted < max_signals:
            if max_polls and polls >= max_polls:
                stopped_by = "max_polls"
                break
            polls += 1
            new_close = feed.poll()
            if not new_close:
                _time.sleep(poll_interval)
                continue
            if not feed.is_warm:
                print(f"  warmup {feed.depth}/20 closes", end="\r")
                _time.sleep(poll_interval)
                continue

            snap = feed.snapshot(symbol)
            decision = strategy.evaluate(snap)
            if decision is None:
                _time.sleep(poll_interval)
                continue
            # one signal per NEW close; never emit a non-advancing timestamp
            if snap.timestamp <= last_emitted_ts:
                _time.sleep(poll_interval)
                continue

            regime = regime_detector.classify(snap)
            bracket = risk.bracket(decision, snap)
            signal = build_signal(decision, regime, bracket, snap, strategy.name)
            if emitter.append(signal):
                signals_emitted += 1
                last_emitted_ts = snap.timestamp
                print(f"  signal {signals_emitted}/{max_signals}  "
                      f"ts={signal['timestamp']}  dir={signal['direction']}  "
                      f"score={signal['score']}")
            else:
                emit_failures += 1
            _time.sleep(poll_interval)
    except KeyboardInterrupt:
        stopped_by = "manual_stop"
        print("\n  manual stop (Ctrl+C)")
    finally:
        feed.disconnect()

    summary = {
        "session": session_id,
        "output_path": output_path,
        "stopped_by": stopped_by,
        "polls": polls,
        "ticks_seen": feed.ticks_seen,
        "ticks_rejected": feed.ticks_rejected,
        "ticks_duplicate": feed.ticks_duplicate,
        "buffer_depth": feed.depth,
        "signals_emitted": signals_emitted,
        "emit_failures": emit_failures,
        "live_orders_sent": 0,
    }
    print()
    print("-" * 64)
    print("SESSION SUMMARY")
    for k, v in summary.items():
        print(f"  {k:16s}: {v}")
    print("-" * 64)
    print("Live orders sent : 0 (no execution code path exists in this loop)")
    print("Next (CP4, manual): py -m testing.shadow.signal_bridge_check "
          f"--journal {output_path}")
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="engine.runner")
    parser.add_argument("--mode", choices=("snapshot", "live"),
                        default="snapshot")
    parser.add_argument("--max-signals", type=int, default=50)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--symbol", default="R_100")
    parser.add_argument("--strategy", choices=sorted(STRATEGY_CLASSES),
                        default="reference_ma")
    args = parser.parse_args()

    if args.mode == "live":
        run_live(symbol=args.symbol, max_signals=args.max_signals,
                 poll_interval=args.poll_interval,
                 strategy_name=args.strategy)
    else:
        result = run_once()
        if result is None:
            print("ENGINE: no signal produced (no-signal condition)")
        else:
            print("ENGINE: emitted 1 signal")
            for key in (
                "timestamp", "symbol", "strategy", "direction", "score", "regime",
                "entry_price", "stop_loss", "take_profit", "risk_percent", "confidence",
            ):
                print(f"  {key}: {result[key]}")
