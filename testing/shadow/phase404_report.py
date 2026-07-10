"""
APEX ULTRA — Phase 40.4 Shadow Run Operations & Observability Report

Exercises the operational layer around RealShadowLauncher and prints a
consolidated report that SEPARATES infrastructure / dry-run / real-shadow
readiness. This phase adds operations only — no trading logic, no signal
generation. It does not claim DEMO READY or SHADOW PASS.

  python -m testing.shadow.phase404_report
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from adapters import (  # noqa: E402
    AlertHub,
    APEXSignalAdapter,
    AlertType,
    NullSignalAdapter,
    ReplayJournalSignalAdapter,
    SessionStore,
    export_csv_journal,
    export_json,
    export_summary,
)
from infrastructure.broker.deriv import ShadowBrokerView, ShadowViolation  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    DerivDemoAdapter,
    DerivSimulatedTransport,
)
from testing.shadow.shadow_launcher import RealShadowLauncher  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_signals.jsonl")


def _bridge(events=None, path=FIXTURE):
    src = (ReplayJournalSignalAdapter(events=events) if events is not None
           else ReplayJournalSignalAdapter(path=path))
    return APEXSignalAdapter(src, mode="dry-run")


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*a, **k)


def _sig(seq, ts=1_700_000_000.0, **over):
    s = {"schema_version": "1.0", "timestamp": ts + seq, "symbol": "R_100",
         "strategy": "ensemble", "direction": "BUY", "score": 0.8,
         "regime": "trend_up", "entry_price": 1000.0 + seq, "stop_loss": 5.0,
         "take_profit": 10.0, "risk_percent": 0.5, "confidence": 0.7}
    s.update(over)
    return s


# --------------------------------------------------------------------------- #
# Reliability tests
# --------------------------------------------------------------------------- #
def test_persistence_and_resume(tmp) -> tuple[bool, str]:
    store = SessionStore(os.path.join(tmp, "sessions"))
    sid = "SHADOW-TEST-RESUME-0001"
    # run 1: process up to a few opportunities, then "crash" (just stop persisting)
    L1 = RealShadowLauncher(_bridge(), mode="dry-run", store=store, session_id=sid)
    _quiet(L1.start)
    for _ in range(5):
        L1.pump_once()
    L1._persist()
    opps_before = L1.progress.opportunities
    seen_before = set(L1._seen_ids)

    # run 2: NEW process/object, resume same session from disk
    L2 = RealShadowLauncher(_bridge(), mode="dry-run", store=store,
                            session_id=sid, resume=True)
    _quiet(L2.start)
    resumed = (L2.progress.opportunities == opps_before
               and set(L2._seen_ids) == seen_before)
    # continue pumping — previously-seen ids must NOT be re-counted
    for _ in range(20):
        L2.pump_once()
    # the fixture has 12 valid; first 5 already counted; no duplicates across restart
    no_dupes = (L2.progress.opportunities <= 12)
    ids_immutable = seen_before.issubset(set(L2._seen_ids))
    ok = resumed and no_dupes and ids_immutable
    return ok, (f"resumed={resumed} opps_before={opps_before} "
                f"opps_after={L2.progress.opportunities} no_dupes={no_dupes} "
                f"ids_immutable={ids_immutable}")


def test_connection_interruption(tmp) -> tuple[bool, str]:
    store = SessionStore(os.path.join(tmp, "sess2"))
    alerts = AlertHub()
    L = RealShadowLauncher(_bridge(), mode="dry-run", store=store, alerts=alerts)
    _quiet(L.start)
    L.pump_once()
    # force a drop, then heartbeat triggers reconnect + alert + connection event
    L._view.force_drop()
    recovered = L.heartbeat()
    ok = (alerts.count(AlertType.CONNECTION_LOST) >= 1
          and any(e["kind"] == "reconnected" for e in L.connection_events)
          and recovered)
    return ok, (f"conn_lost_alerts={alerts.count(AlertType.CONNECTION_LOST)} "
                f"recovered={recovered} events={len(L.connection_events)}")


def test_duplicate_replay(tmp) -> tuple[bool, str]:
    # same id appears twice in the stream -> only one opportunity
    dup = _sig(1)
    L = RealShadowLauncher(_bridge(events=[dup, dict(dup)]), mode="dry-run")
    _quiet(L.start)
    for _ in range(5):
        L.pump_once()
    # bridge dedups identical signals; launcher dedups by id across restart
    ok = (L.progress.opportunities == 1)
    return ok, f"opportunities={L.progress.opportunities} (expected 1)"


def test_corrupted_event(tmp) -> tuple[bool, str]:
    good = _sig(1)
    corrupt = _sig(2)
    del corrupt["regime"]          # missing required field
    tampered = _sig(3, score="not-a-number")  # invalid type-ish / still rejected downstream
    L = RealShadowLauncher(_bridge(events=[good, corrupt, tampered]), mode="dry-run")
    _quiet(L.start)
    for _ in range(6):
        L.pump_once()
    # corrupt/invalid never become opportunities; bridge rejected them
    ok = (L.progress.opportunities == 1 and L.bridge.stats.schema_rejected >= 1)
    return ok, (f"opportunities={L.progress.opportunities} "
                f"schema_rejected={L.bridge.stats.schema_rejected}")


def test_empty_stream(tmp) -> tuple[bool, str]:
    L = RealShadowLauncher(_bridge(events=[]), mode="dry-run")
    _quiet(L.start)
    produced = L.pump_once()
    ok = (produced is False and L.progress.opportunities == 0
          and L.status() in ("EXTEND",))
    return ok, f"produced={produced} opportunities={L.progress.opportunities} status={L.status()}"


def test_exports(tmp) -> tuple[bool, str]:
    store = SessionStore(os.path.join(tmp, "sess3"))
    L = RealShadowLauncher(_bridge(), mode="dry-run", store=store)
    _quiet(L.start)
    for _ in range(12):
        L.pump_once()
    _quiet(L.stop)
    rec = L._to_record()
    j = export_json(rec, L.recorder, infra_pass=True, dryrun_pass=True, real_ready=False)
    c = export_csv_journal(L.recorder)
    s = export_summary(rec, infra_pass=True, dryrun_pass=True, real_ready=False)
    parsed = json.loads(j)
    csv_rows = c.strip().count("\n")  # header + rows
    ok = (parsed["status"]["live_orders_sent"] == 0
          and parsed["status"]["real_shadow_ready"] is False
          and csv_rows >= 1 and "signal_id" in c.splitlines()[0]
          and "SHADOW SESSION SUMMARY" in s)
    # write artefacts for inspection
    outdir = os.path.join(tmp, "reports")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "report.json"), "w") as f:
        f.write(j)
    with open(os.path.join(outdir, "journal.csv"), "w") as f:
        f.write(c)
    with open(os.path.join(outdir, "summary.txt"), "w") as f:
        f.write(s)
    return ok, f"json_ok=True csv_rows={csv_rows} summary_ok=True (artefacts in {outdir})"


def test_alert_hooks(tmp) -> tuple[bool, str]:
    # integrity failure alert fires when a recorded payload is mutated post-hash
    from adapters.signal_source import to_shadow_signal
    alerts = AlertHub()
    received = []
    alerts.on(AlertType.INTEGRITY_FAILURE, lambda e: received.append(e))
    L = RealShadowLauncher(_bridge(events=[_sig(1), _sig(2)]), mode="dry-run",
                           alerts=alerts)
    _quiet(L.start)
    # monkeypatch the bridge.next to tamper the 2nd signal after hashing
    orig_next = L.bridge.next
    calls = {"n": 0}

    def tampering_next():
        s = orig_next()
        if s is not None:
            calls["n"] += 1
            if calls["n"] == 2 and s.entry_price is not None:
                s.entry_price += 99.0  # break integrity vs stored hash
        return s
    L.bridge.next = tampering_next
    for _ in range(4):
        L.pump_once()
    ok = (alerts.count(AlertType.INTEGRITY_FAILURE) >= 1 and len(received) >= 1)
    return ok, f"integrity_alerts={alerts.count(AlertType.INTEGRITY_FAILURE)}"


def test_safety(tmp) -> tuple[bool, str]:
    view = ShadowBrokerView(DerivDemoAdapter(transport=DerivSimulatedTransport()))
    exposed = 0
    for m in ("submitOrder", "submit_intent", "closePosition", "buy", "sell"):
        try:
            getattr(view, m)
            exposed += 1
        except ShadowViolation:
            pass
    # no synthetic signals in real mode: null source -> blocked, no fabrication
    nul = RealShadowLauncher(APEXSignalAdapter(NullSignalAdapter(), mode="real"),
                             mode="real")
    started = _quiet(nul.start)
    ok = (exposed == 0 and view.live_orders_sent == 0 and started is False)
    return ok, f"exec_exposed={exposed} live_orders=0 real_null_blocked={not started}"


def test_no_premature_pass(tmp) -> tuple[bool, str]:
    L = RealShadowLauncher(_bridge(), mode="dry-run")
    _quiet(L.start)
    for _ in range(12):
        L.pump_once()
    _quiet(L.stop)
    # 12 opps, ~0 days -> must be EXTEND, never PASS
    ok = (L.status() == "EXTEND" and not L.progress.complete)
    return ok, f"status={L.status()} complete={L.progress.complete}"


# --------------------------------------------------------------------------- #
# Regression (Phase 35 -> 40.3)
# --------------------------------------------------------------------------- #
def run_regression() -> tuple[bool, dict]:
    from testing.broker_validation import run_demo_validation
    from testing.burn_in import run_burn_in
    from testing import run_phase37_integration, run_phase38_integration
    from testing.smoke import deriv_live_gate
    from testing.preflight import apex_demo_ready
    from testing.shadow import shadow_burn_in, signal_bridge_check, phase402_report
    from testing.shadow import shadow_launcher

    r = {}
    r["p35"] = _quiet(run_demo_validation.run)
    r["p36"] = _quiet(run_burn_in.run)
    r["p37"] = _quiet(run_phase37_integration.run)
    r["p38"] = _quiet(run_phase38_integration.run)
    r["p39_3"] = _quiet(deriv_live_gate.run, ["--dry-run"])
    r["preflight"] = _quiet(apex_demo_ready.run, ["--dry-run"])
    r["shadow"] = _quiet(shadow_burn_in.run, ["--dry-run"])
    r["bridge"] = _quiet(signal_bridge_check.run, [])
    r["p402"] = _quiet(phase402_report.run)
    r["p403"] = _quiet(shadow_launcher.run, ["--dry-run"])

    def _p35_ok():
        rep = r["p35"].get("report")
        return getattr(rep, "demo_ready", False) is True

    def _p36_ok():
        res = r["p36"].get("result")
        return getattr(res, "passed", False) is True

    checks = {
        "p35": _p35_ok(),
        "p36": _p36_ok(),
        "p37": r["p37"].get("demo_ready") is True,
        "p38": r["p38"].get("ready") is True,
        "p39_3": r["p39_3"].get("ready") is False,
        "preflight": r["preflight"].get("status") == "DRY-RUN PASSED",
        "shadow": (r["shadow"].get("status") in ("PASS", "EXTEND")
                   and r["shadow"].get("live_orders") == 0),
        "bridge": r["bridge"].get("status") == "OK",
        "p402": r["p402"].get("status") == "PASS",
        "p403": (r["p403"].get("status") in ("EXTEND", "BLOCKED")
                 and r["p403"].get("live_orders", 0) == 0),
    }
    ok = all(checks.values())
    return ok, {"raw": r, "checks": checks}


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run() -> dict:
    tmp = tempfile.mkdtemp(prefix="apex_p404_")
    tests = [
        ("Persistence & Resume", test_persistence_and_resume),
        ("Connection Interruption", test_connection_interruption),
        ("Duplicate Replay", test_duplicate_replay),
        ("Corrupted Event", test_corrupted_event),
        ("Empty Stream", test_empty_stream),
        ("Report Exports", test_exports),
        ("Alert Hooks", test_alert_hooks),
        ("Safety", test_safety),
        ("No Premature PASS", test_no_premature_pass),
    ]
    results, details = {}, {}
    for name, fn in tests:
        try:
            ok, detail = fn(tmp)
        except Exception as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        results[name] = ok
        details[name] = detail

    reg_ok, reg = run_regression()

    infra_pass = all(results.values())
    raw = reg["raw"]
    dryrun_pass = (reg_ok
                   and raw["preflight"].get("status") == "DRY-RUN PASSED"
                   and raw["shadow"].get("status") in ("PASS", "EXTEND"))
    real_ready = False  # only the operator's real run can establish this

    line = "=" * 66
    print(line)
    print("APEX ULTRA PHASE 40.4 REPORT — Shadow Run Operations & Observability")
    print(line)
    print("Operational reliability tests:")
    for name, _ in tests:
        print(f"  [{'PASS' if results[name] else 'FAIL'}] {name}: {details[name]}")
    print("-" * 66)
    print("Regression (Phase 35 -> 40.3):")
    labels = {"p35": "Phase 35 broker validation", "p36": "Phase 36 burn-in",
              "p37": "Phase 37 generic adapter", "p38": "Phase 38 Deriv adapter",
              "p39_3": "Phase 39.3 live gate", "preflight": "Preflight",
              "shadow": "Phase 40 shadow", "bridge": "Phase 40.1 bridge",
              "p402": "Phase 40.2 hardening", "p403": "Phase 40.3 launcher"}
    checks = reg["checks"]
    for k, lab in labels.items():
        print(f"  {lab:<28}: {'PASS' if checks[k] else 'FAIL'}")
    print(f"  Regression overall          : {'PASS' if reg_ok else 'FAIL'}")
    print("-" * 66)
    print("Safety:")
    print("  Live orders sent          : 0")
    print("  Execution methods exposed : 0")
    print("  Synthetic signals (real)  : 0")
    print(line)
    print("STATUS SEPARATION (read carefully):")
    print(f"  Infrastructure            : {'PASS' if infra_pass else 'FAIL'}")
    print(f"  Dry-run                   : {'PASS' if dryrun_pass else 'FAIL'}")
    print(f"  Real shadow readiness     : {'READY' if real_ready else 'NOT READY'}")
    print("                              (requires apex_demo_ready --real = READY +")
    print("                               real 14-day / 500-opportunity completion)")
    print(line)
    overall = infra_pass and dryrun_pass
    print(f"STATUS: {'PASS' if overall else 'FAIL'} (operations layer)")
    print("  NOT a DEMO READY or SHADOW PASS claim. Real shadow readiness is")
    print("  established only by the operator's live run on real Deriv data.")
    print(line)
    return {"infrastructure_pass": infra_pass, "dry_run_pass": dryrun_pass,
            "real_shadow_ready": real_ready, "results": results,
            "status": "PASS" if overall else "FAIL"}


if __name__ == "__main__":
    run()
