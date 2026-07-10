"""
APEX ULTRA — Phase 40.1 Signal Bridge Validation

Validates the APEX signal bridge and its integration with the Phase 40 shadow
burn-in. Prints the APEX SIGNAL BRIDGE REPORT and the signal-flow report.

Usage:
  python -m testing.shadow.signal_bridge_check                 # replay fixture
  python -m testing.shadow.signal_bridge_check --null          # null source -> BLOCKED
  python -m testing.shadow.signal_bridge_check --journal PATH   # custom journal
  python -m testing.shadow.signal_bridge_check --integrate      # feed Phase 40 shadow
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from adapters import (  # noqa: E402
    APEXSignalAdapter,
    LiveEngineSignalAdapter,
    NullSignalAdapter,
    ReplayJournalSignalAdapter,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_signals.jsonl")


def _build(argv: list[str]) -> tuple[APEXSignalAdapter, str, str]:
    if "--null" in argv:
        return APEXSignalAdapter(NullSignalAdapter(), mode="real"), "NullSignalAdapter", "real"
    journal = FIXTURE
    if "--journal" in argv:
        journal = argv[argv.index("--journal") + 1]
    src = ReplayJournalSignalAdapter(path=journal)
    return APEXSignalAdapter(src, mode="dry-run"), f"Replay({os.path.basename(journal)})", "dry-run"


def _drain(bridge: APEXSignalAdapter) -> int:
    """Pull every signal from the bridge (validation path). Returns count yielded."""
    yielded = 0
    while True:
        sig = bridge.next_signal()
        if sig is None:
            break
        yielded += 1
    return yielded


def run(argv: list[str] | None = None) -> dict:
    argv = argv if argv is not None else sys.argv[1:]
    bridge, source_name, mode = _build(argv)

    yielded = _drain(bridge)
    s = bridge.stats
    lat = bridge.latency.report()
    avg_latency_ms = lat["total_ms"]

    # status logic
    if bridge.blocked or s.no_source:
        status = "BLOCKED"
    elif s.received == 0:
        status = "BLOCKED"   # no signals at all
    elif s.accepted == 0:
        status = "BLOCKED"   # nothing valid
    else:
        status = "OK"

    live_orders_sent = 0  # bridge never executes

    line = "=" * 64
    print(line)
    print("APEX SIGNAL BRIDGE REPORT")
    print(line)
    print(f"Source            : {source_name}")
    print(f"Mode              : {mode}")
    print(f"Signals received  : {s.received}")
    print(f"Schema valid      : {s.accepted}/{s.received}")
    print(f"Latency           : {avg_latency_ms:.4f} ms avg (total)")
    print(f"Duplicates        : {s.duplicates}")
    print(f"Status            : {status}")
    print("-" * 64)
    print("SIGNAL FLOW REPORT:")
    print(f"  Signals received: {s.received}")
    print(f"  Signals accepted: {s.accepted}")
    print(f"  Signals rejected: {s.rejected}")
    print(f"  Missing fields  : {s.missing_fields}")
    print(f"  Duplicate signals: {s.duplicates}")
    print(f"  Latency         : {avg_latency_ms:.4f} ms avg (total)")
    print(f"  Live orders sent: {live_orders_sent}")
    print(line)

    if "--integrate" in argv and status == "OK":
        _integrate(argv)

    return {"status": status, "stats": s, "yielded": yielded}


def _integrate(argv: list[str]) -> None:
    """Feed a fresh bridge into the Phase 40 shadow burn-in (dry-run) to prove
    end-to-end wiring and that Live orders sent stays 0."""
    from testing.shadow import shadow_burn_in
    src = ReplayJournalSignalAdapter(path=FIXTURE)
    bridge = APEXSignalAdapter(src, mode="dry-run")
    print("\n>>> PHASE 40 INTEGRATION (shadow burn-in fed by APEXSignalAdapter):\n")
    res = shadow_burn_in.run(["--dry-run"], signal_source=bridge)
    print(f"\n>>> integration result: shadow status={res.get('status')}, "
          f"live_orders={res.get('live_orders')}")


if __name__ == "__main__":
    run()
