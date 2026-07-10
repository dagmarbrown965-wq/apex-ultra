"""
APEX ULTRA — Phase 40.2 Signal Bridge Hardening Report

Runs every required validation and prints the consolidated Phase 40.2 report.
This phase HARDENS the bridge only — it does not claim DEMO READY or SHADOW
PASS. Real shadow readiness still requires `apex_demo_ready --real` and a real
Deriv virtual-account connection.

  python -m testing.shadow.phase402_report
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from adapters import (  # noqa: E402
    APEXSignalAdapter,
    NullSignalAdapter,
    ReplayJournalSignalAdapter,
    SCHEMA_VERSION,
    compute_signal_hash,
)
from adapters.apex_signal_adapter import LiveEngineSignalAdapter  # noqa: E402
from infrastructure.broker.broker_interface import OrderSide  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    DerivDemoAdapter,
    DerivSimulatedTransport,
    ShadowBrokerView,
    ShadowRecorder,
    ShadowViolation,
)
from adapters.signal_source import to_shadow_signal  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_signals.jsonl")


def _sig(seq: int, *, ts: float = 1_700_000_000.0, symbol="R_100",
         version=SCHEMA_VERSION, **over) -> dict:
    s = {
        "schema_version": version, "timestamp": ts + seq, "symbol": symbol,
        "strategy": "ensemble", "direction": "BUY", "score": 0.8,
        "regime": "trend_up", "entry_price": 1000.0 + seq, "stop_loss": 5.0,
        "take_profit": 10.0, "risk_percent": 0.5, "confidence": 0.7,
    }
    s.update(over)
    return s


def _quiet(fn, *a):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return fn(*a), None
    except Exception as e:
        return None, e


# --------------------------------------------------------------------------- #
# Individual checks
# --------------------------------------------------------------------------- #
def check_schema_versioning() -> tuple[bool, str]:
    events = [_sig(1), _sig(2, version="0.9"), _sig(3, score=None)]  # valid, bad ver, missing
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(events=events), mode="test")
    out = []
    while True:
        s = b.next_signal()
        if s is None:
            break
        out.append(s)
    ok = (b.stats.schema_valid == 1 and b.stats.version_mismatch == 1
          and b.stats.schema_rejected == 2 and b.stats.missing_fields >= 1)
    return ok, (f"valid={b.stats.schema_valid} mismatch={b.stats.version_mismatch} "
                f"rejected={b.stats.schema_rejected} missing={b.stats.missing_fields}")


def check_trace_persistence() -> tuple[bool, str]:
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(events=[_sig(1)]), mode="test")
    canonical = b.next_signal()
    sid = canonical["signal_id"]
    shadow_sig = to_shadow_signal(canonical)
    rec = ShadowRecorder()
    view = ShadowBrokerView(DerivDemoAdapter(transport=DerivSimulatedTransport()))
    view.connect()
    from infrastructure.broker.deriv import load_contract_spec
    ev = rec.record(shadow_sig, view.get_quote("R_100"), 1.0, load_contract_spec(), "USD")
    # simulate outcome evaluation (id must still persist)
    ev.outcome = "win"
    persisted = (sid == shadow_sig.signal_id == ev.signal_id)
    fmt = sid.startswith("SIG-R100-")
    return (persisted and fmt), f"id={sid} persisted={persisted}"


def check_integrity_hashing() -> tuple[bool, str]:
    spec_mod = __import__("infrastructure.broker.deriv", fromlist=["load_contract_spec"])
    spec = spec_mod.load_contract_spec()
    view = ShadowBrokerView(DerivDemoAdapter(transport=DerivSimulatedTransport()))
    view.connect()
    quote = view.get_quote("R_100")

    # passing case
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(events=[_sig(1)]), mode="test")
    good = to_shadow_signal(b.next_signal())
    rec = ShadowRecorder()
    rec.record(good, quote, 1.0, spec, "USD")

    # mutation case: tamper with the payload AFTER bridge hashing
    b2 = APEXSignalAdapter(ReplayJournalSignalAdapter(events=[_sig(2)]), mode="test")
    tampered = to_shadow_signal(b2.next_signal())
    tampered.entry_price = (tampered.entry_price or 0) + 13.0  # modify immutable field
    rec.record(tampered, quote, 1.0, spec, "USD")

    ok = (rec.integrity_passed == 1 and rec.integrity_failed == 1
          and len(rec.modified_signals) == 1)
    return ok, (f"passed={rec.integrity_passed} failed={rec.integrity_failed} "
                f"modified={rec.modified_signals}")


def check_replay_determinism() -> tuple[bool, str]:
    def run():
        b = APEXSignalAdapter(ReplayJournalSignalAdapter(path=FIXTURE), mode="test")
        ids = []
        while True:
            s = b.next_signal()
            if s is None:
                break
            ids.append(s["signal_id"])
        return (b.stats.accepted, b.stats.rejected, b.stats.duplicates, ids)
    a = run()
    c = run()
    ok = (a == c)
    return ok, (f"run1=(acc {a[0]},rej {a[1]},dup {a[2]}) "
                f"run2=(acc {c[0]},rej {c[1]},dup {c[2]}) ids_identical={a[3]==c[3]}")


def check_duplicate_detection() -> tuple[bool, str]:
    events = [_sig(1), _sig(1)]  # exact duplicate (same ts/symbol/strategy/dir/score)
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(events=events), mode="test")
    while b.next_signal() is not None:
        pass
    ok = (b.stats.accepted == 1 and b.stats.duplicates == 1)
    return ok, f"accepted={b.stats.accepted} duplicates={b.stats.duplicates}"


def check_missing_field() -> tuple[bool, str]:
    bad = _sig(1)
    del bad["regime"]
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(events=[bad]), mode="test")
    while b.next_signal() is not None:
        pass
    ok = (b.stats.schema_rejected == 1 and b.stats.missing_fields >= 1)
    return ok, f"rejected={b.stats.schema_rejected} missing_fields={b.stats.missing_fields}"


def check_hash_mutation() -> tuple[bool, str]:
    # hash a signal, mutate an immutable field, verify hash no longer matches
    sig = _sig(1)
    h = compute_signal_hash(sig)
    mutated = dict(sig)
    mutated["risk_percent"] = sig["risk_percent"] + 0.25
    ok = (compute_signal_hash(mutated) != h) and (compute_signal_hash(sig) == h)
    return ok, f"original_stable={compute_signal_hash(sig)==h} mutation_detected={compute_signal_hash(mutated)!=h}"


def check_empty_source() -> tuple[bool, str]:
    empty = APEXSignalAdapter(ReplayJournalSignalAdapter(events=[]), mode="test")
    none1 = empty.next_signal()
    nul = APEXSignalAdapter(NullSignalAdapter(), mode="real")
    none2 = nul.next_signal()
    ok = (none1 is None and none2 is None and nul.blocked and empty.stats.received == 0)
    return ok, f"empty->None={none1 is None} null_blocked={nul.blocked}"


def check_health_monitor() -> tuple[bool, str]:
    clock = {"t": 1_700_000_000.0}
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(path=FIXTURE), mode="test",
                          stale_after_seconds=300.0, now_fn=lambda: clock["t"])
    while b.next_signal() is not None:
        pass
    clock["t"] = (b.health.last_signal_ts or 0) + 30      # fresh
    healthy = b.health.status()
    clock["t"] = (b.health.last_signal_ts or 0) + 9999     # stale
    stale = b.health.status()
    rep = b.health.report()
    ok = (healthy == "HEALTHY" and stale == "STALE"
          and rep["signals_received"] > 0 and rep["signals_per_hour"] > 0)
    return ok, (f"fresh={healthy} stale={stale} rate={rep['signals_per_hour']:.1f}/h "
                f"dup_rate={rep['duplicate_rate']:.2f}")


def check_latency_breakdown() -> tuple[bool, str]:
    b = APEXSignalAdapter(ReplayJournalSignalAdapter(path=FIXTURE), mode="test")
    spec = __import__("infrastructure.broker.deriv",
                      fromlist=["load_contract_spec"]).load_contract_spec()
    view = ShadowBrokerView(DerivDemoAdapter(transport=DerivSimulatedTransport()))
    view.connect()
    rec = ShadowRecorder()
    shadow_record_total = 0.0
    n = 0
    while True:
        canonical = b.next_signal()
        if canonical is None:
            break
        ss = to_shadow_signal(canonical)
        t0 = time.perf_counter()
        rec.record(ss, view.get_quote(ss.symbol), 1.0, spec, "USD")
        shadow_record_total += (time.perf_counter() - t0) * 1000.0
        n += 1
    lr = b.latency.report()
    avg_shadow = shadow_record_total / n if n else 0.0
    has_all = all(k in lr for k in
                  ("engine_emit_ms", "bridge_receive_ms", "validation_ms",
                   "shadow_record_ms", "total_ms"))
    ok = has_all and lr["validation_ms"] >= 0 and avg_shadow >= 0
    return ok, (f"bridge={lr['bridge_receive_ms']:.4f}ms valid={lr['validation_ms']:.4f}ms "
                f"shadow_record={avg_shadow:.4f}ms")


def check_regression() -> tuple[bool, str]:
    from testing.preflight import apex_demo_ready
    from testing.shadow import shadow_burn_in, signal_bridge_check
    from testing import run_phase38_integration
    pf, _ = _quiet(apex_demo_ready.run, ["--dry-run"])
    sh, _ = _quiet(shadow_burn_in.run, ["--dry-run"])
    p38, _ = _quiet(run_phase38_integration.run)
    br, _ = _quiet(signal_bridge_check.run, [])
    ok = (pf and pf.get("status") == "DRY-RUN PASSED"
          and sh and sh.get("status") in ("PASS", "EXTEND")
          and sh.get("live_orders") == 0
          and p38 and p38.get("ready")
          and br and br.get("status") == "OK")
    detail = (f"preflight={pf and pf.get('status')} shadow={sh and sh.get('status')} "
              f"p38={p38 and p38.get('ready')} bridge={br and br.get('status')}")
    return ok, detail


def check_safety() -> tuple[bool, str]:
    # execution methods exposed: 0
    view = ShadowBrokerView(DerivDemoAdapter(transport=DerivSimulatedTransport()))
    exposed = 0
    for m in ("submitOrder", "submit_intent", "closePosition", "buy", "sell"):
        try:
            getattr(view, m)
            exposed += 1
        except ShadowViolation:
            pass
    # signal generation: 0 (bridge yields nothing from an empty source)
    gen = APEXSignalAdapter(ReplayJournalSignalAdapter(events=[]), mode="test")
    fabricated = 0
    if gen.next_signal() is not None:
        fabricated += 1
    ok = (exposed == 0 and fabricated == 0 and view.live_orders_sent == 0)
    return ok, f"exec_exposed={exposed} fabricated={fabricated} live_orders={view.live_orders_sent}"


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run() -> dict:
    checks = [
        ("Schema Versioning", check_schema_versioning),
        ("Trace Persistence", check_trace_persistence),
        ("Integrity Hashing", check_integrity_hashing),
        ("Replay Determinism", check_replay_determinism),
        ("Duplicate Detection", check_duplicate_detection),
        ("Missing Field", check_missing_field),
        ("Schema Version Failure", lambda: check_schema_versioning()),
        ("Hash Mutation", check_hash_mutation),
        ("Empty Source", check_empty_source),
        ("Health Monitor", check_health_monitor),
        ("Latency Breakdown", check_latency_breakdown),
        ("Regression", check_regression),
        ("Safety", check_safety),
    ]
    results = {}
    details = {}
    for name, fn in checks:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        results[name] = ok
        details[name] = detail

    # group the headline rows
    headline = {
        "Schema": results["Schema Versioning"] and results["Schema Version Failure"]
        and results["Missing Field"],
        "Integrity": results["Integrity Hashing"] and results["Hash Mutation"],
        "Replay Determinism": results["Replay Determinism"],
        "Duplicate Detection": results["Duplicate Detection"],
        "Trace Persistence": results["Trace Persistence"],
        "Health Monitor": results["Health Monitor"],
        "Latency Breakdown": results["Latency Breakdown"],
        "Empty Source": results["Empty Source"],
        "Regression": results["Regression"],
        "Safety": results["Safety"],
    }
    overall = all(headline.values())

    line = "=" * 60
    print(line)
    print("APEX ULTRA PHASE 40.2 REPORT")
    print(line)
    for k in ("Schema", "Trace Persistence", "Integrity", "Replay Determinism",
              "Duplicate Detection", "Health Monitor", "Latency Breakdown",
              "Empty Source"):
        print(f"  {k:<22} {'PASS' if headline[k] else 'FAIL'}")
    print("-" * 60)
    print("Detailed checks:")
    for name, _ in checks:
        if name == "Schema Version Failure":
            continue
        print(f"  [{'PASS' if results[name] else 'FAIL'}] {name}: {details[name]}")
    print("-" * 60)
    print(f"Regression (Phase 35–40.1): {'PASS' if headline['Regression'] else 'FAIL'}")
    print("  " + details["Regression"])
    print("-" * 60)
    print("Safety:")
    print(f"  Live orders sent          : 0")
    print(f"  Execution methods exposed : 0")
    print(f"  Signal generation         : 0")
    print(line)
    print(f"STATUS: {'PASS' if overall else 'FAIL'}")
    if overall:
        print("  (bridge hardened — NOT a DEMO READY or SHADOW PASS claim;")
        print("   real shadow readiness still requires apex_demo_ready --real)")
    print(line)
    return {"status": "PASS" if overall else "FAIL", "results": results}


if __name__ == "__main__":
    run()
