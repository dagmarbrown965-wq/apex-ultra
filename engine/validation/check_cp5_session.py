"""CP5 session integrity check - Phase 43 (Boundary 4).

Validates one per-session live signal file:

  1. Every line is valid JSON (UTF-8, one object per line).
  2. Every signal has exactly the v1.0 fields - and NO bridge-owned fields
     (signal_id / schema_version / signal_hash must be absent pre-bridge).
  3. Every timestamp is numeric (epoch seconds).
  4. Timestamps are STRICTLY increasing across the file.
  5. All signals share one symbol and one strategy (one session, one producer).
  6. The filename matches the per-session pattern (sessions never mix).

Deliberately NOT checked: byte-identical output across sessions. Live closes
are expected to differ between sessions; the engine transform's determinism
given identical buffer input is guaranteed by the 42.0C regression net, not
re-tested here. (See the agreement, Boundary 4 / CP5.)

Run:  py -m engine.validation.check_cp5_session --journal PATH
Exit: 0 = CP5 PASS, 1 = failures listed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

V1_FIELDS = frozenset({
    "timestamp", "symbol", "strategy", "direction", "score", "regime",
    "entry_price", "stop_loss", "take_profit", "risk_percent", "confidence",
})
BRIDGE_OWNED = frozenset({"signal_id", "schema_version", "signal_hash"})
SESSION_NAME = re.compile(r"^live_signals_\d{4}-\d{2}-\d{2}_session\d{3}\.jsonl$")


def check(path: str):
    """Return (failures, stats). failures is a list of printable strings."""
    failures = []
    stats = {"lines": 0, "signals": 0, "first_ts": None, "last_ts": None}

    name = os.path.basename(path)
    if not SESSION_NAME.match(name):
        failures.append(
            f"filename '{name}' does not match the per-session pattern "
            "live_signals_<YYYY-MM-DD>_session<NNN>.jsonl")

    if not os.path.isfile(path):
        failures.append(f"file not found: {path}")
        return failures, stats

    prev_ts = None
    symbols, strategies = set(), set()
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if not raw.strip():
                continue
            stats["lines"] += 1
            try:
                sig = json.loads(raw)
            except json.JSONDecodeError as e:
                failures.append(f"line {lineno}: invalid JSON: {e.msg}")
                continue
            if not isinstance(sig, dict):
                failures.append(f"line {lineno}: not a JSON object")
                continue
            stats["signals"] += 1

            fields = set(sig)
            leaked = fields & BRIDGE_OWNED
            if leaked:
                failures.append(
                    f"line {lineno}: bridge-owned field(s) present pre-bridge: "
                    f"{sorted(leaked)}")
            missing = V1_FIELDS - fields
            extra = fields - V1_FIELDS - BRIDGE_OWNED
            if missing:
                failures.append(f"line {lineno}: missing v1.0 field(s): {sorted(missing)}")
            if extra:
                failures.append(f"line {lineno}: unexpected field(s): {sorted(extra)}")

            ts = sig.get("timestamp")
            if not isinstance(ts, (int, float)) or isinstance(ts, bool):
                failures.append(f"line {lineno}: timestamp not numeric: {ts!r}")
            else:
                if stats["first_ts"] is None:
                    stats["first_ts"] = ts
                stats["last_ts"] = ts
                if prev_ts is not None and ts <= prev_ts:
                    failures.append(
                        f"line {lineno}: timestamp not strictly increasing "
                        f"({ts} <= {prev_ts})")
                prev_ts = ts

            symbols.add(sig.get("symbol"))
            strategies.add(sig.get("strategy"))

    if stats["signals"] == 0:
        failures.append("no signals in file (need >= 1 for CP4/CP5)")
    if len(symbols) > 1:
        failures.append(f"multiple symbols in one session: {sorted(map(str, symbols))}")
    if len(strategies) > 1:
        failures.append(f"multiple strategies in one session: {sorted(map(str, strategies))}")

    return failures, stats


def main() -> int:
    parser = argparse.ArgumentParser(prog="engine.validation.check_cp5_session")
    parser.add_argument("--journal", required=True, help="per-session JSONL path")
    args = parser.parse_args()

    print("=" * 64)
    print("CP5 SESSION INTEGRITY CHECK (Phase 43)")
    print("=" * 64)
    print(f"journal : {args.journal}")
    failures, stats = check(args.journal)
    print(f"signals : {stats['signals']}")
    if stats["first_ts"] is not None:
        print(f"ts span : {stats['first_ts']} -> {stats['last_ts']}")
    print()
    if failures:
        print(f"CP5: FAIL ({len(failures)} problem(s))")
        for line in failures:
            print("  " + line)
        return 1
    print("CP5: PASS (valid JSONL; v1.0 shape; no bridge fields; numeric,")
    print("     strictly increasing timestamps; single symbol/strategy;")
    print("     per-session filename)")
    return 0


if __name__ == "__main__":
    sys.exit(main())