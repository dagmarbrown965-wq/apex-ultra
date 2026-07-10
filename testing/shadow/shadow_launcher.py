"""
APEX ULTRA — Phase 40.3 Real Shadow Launcher

The launcher LAYER only. It orchestrates existing components — it adds no
trading capability and generates no signals:

    apex_demo_ready --real (READY)  ->  real virtual-account connection
        ->  live APEX signal bridge (Phase 40.1/40.2)
        ->  shadow recorder (Phase 40)  ->  14-day / 500-opportunity observation

Hard guarantees:
  - Will not start unless `apex_demo_ready --real` returns READY.
  - Requires a live signal bridge (APEXSignalAdapter over a real source).
  - Uses the hardened Phase 40.2 schema (validation/trace-id/integrity happen
    inside the bridge; the launcher just moves bridge output to the recorder).
  - Live orders sent = 0, structurally (ShadowBrokerView has no order methods).
  - Never claims SHADOW PASS until the observation period actually completes.

This module modifies no strategy/indicator/signal/risk/execution/UI code.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from adapters import APEXSignalAdapter, NullSignalAdapter  # noqa: E402
from infrastructure.broker.deriv import (  # noqa: E402
    DerivDemoAdapter,
    DerivWebSocketTransport,
    ShadowBrokerView,
    ShadowRecorder,
    ShadowViolation,
    live_trading_enabled,
    load_contract_spec,
    load_deriv_config,
    select_contract,
)
from testing.preflight import apex_demo_ready  # noqa: E402
from infrastructure.shadow_telemetry import AlertType as _AlertType  # noqa: E402

MIN_DAYS = 14
MIN_OPPORTUNITIES = 500


class SessionState(str, Enum):
    CREATED = "CREATED"
    GATING = "GATING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"


class ShadowLauncherError(Exception):
    pass


@dataclass
class ShadowProgress:
    opportunities: int = 0
    start_wall: Optional[float] = None
    first_signal_ts: Optional[float] = None
    last_signal_ts: Optional[float] = None
    last_heartbeat_wall: Optional[float] = None
    heartbeats_ok: int = 0
    heartbeats_missed: int = 0

    @property
    def observed_days(self) -> float:
        if self.first_signal_ts is None or self.last_signal_ts is None:
            return 0.0
        return max(0.0, (self.last_signal_ts - self.first_signal_ts) / 86400.0)

    @property
    def met_opportunities(self) -> bool:
        return self.opportunities >= MIN_OPPORTUNITIES

    @property
    def met_duration(self) -> bool:
        return self.observed_days >= MIN_DAYS

    @property
    def complete(self) -> bool:
        # both minimums required (whichever comes later)
        return self.met_opportunities and self.met_duration

    def remaining(self) -> dict:
        return {
            "opportunities_remaining": max(0, MIN_OPPORTUNITIES - self.opportunities),
            "days_remaining": max(0.0, MIN_DAYS - self.observed_days),
        }


class RealShadowLauncher:
    """Controllable real-shadow session. Drive it with start()/poll()/stop(), or
    run a bounded loop via run()."""

    def __init__(self, signal_bridge: APEXSignalAdapter,
                 heartbeat_interval: float = 30.0, session_id: Optional[str] = None,
                 mode: str = "real", store=None, alerts=None,
                 resume: bool = False) -> None:
        self.bridge = signal_bridge
        self.heartbeat_interval = heartbeat_interval
        self.session_id = session_id or self._new_session_id()
        self.mode = mode

        self.state = SessionState.CREATED
        self.progress = ShadowProgress()
        self.recorder = ShadowRecorder()
        self.blockers: list[str] = []

        self._view: Optional[ShadowBrokerView] = None
        self._spec = load_contract_spec()
        self._cfg = load_deriv_config(require_token=False)
        self._stop_requested = False

        # Phase 40.4 ops
        self.store = store
        self.alerts = alerts
        self.resume = resume
        self.stop_reason = ""
        self.connection_events: list = []
        self._seen_ids: set = set()
        self._integrity_failed_seen = 0

    def _to_record(self):
        from infrastructure.shadow_telemetry import SessionRecord
        p, rec = self.progress, self.recorder
        return SessionRecord(
            session_id=self.session_id, mode=self.mode, state=self.state.value,
            start_wall=p.start_wall, end_wall=self.progress.last_signal_ts and None,
            first_signal_ts=p.first_signal_ts, last_signal_ts=p.last_signal_ts,
            opportunities=p.opportunities, heartbeats_ok=p.heartbeats_ok,
            heartbeats_missed=p.heartbeats_missed,
            last_heartbeat_wall=p.last_heartbeat_wall,
            integrity_passed=rec.integrity_passed, integrity_failed=rec.integrity_failed,
            modified_signals=list(rec.modified_signals),
            connection_events=list(self.connection_events),
            seen_signal_ids=sorted(self._seen_ids),
            stop_reason=self.stop_reason, final_verdict=self.status())

    def _persist(self) -> None:
        if self.store is not None:
            with contextlib.suppress(Exception):
                self.store.save(self._to_record())

    def _alert(self, alert_type, **payload) -> None:
        if self.alerts is not None:
            self.alerts.fire(alert_type, session_id=self.session_id, **payload)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _new_session_id() -> str:
        ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        return f"SHADOW-{ts}-{uuid.uuid4().hex[:6].upper()}"

    # ------------------------------------------------------------------ #
    # Gate
    # ------------------------------------------------------------------ #
    def _check_preflight(self) -> bool:
        self.state = SessionState.GATING
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pf = apex_demo_ready.run(["--real"] if self.mode == "real" else ["--dry-run"])
        required = "READY" if self.mode == "real" else "DRY-RUN PASSED"
        if pf.get("status") != required:
            self.blockers = pf.get("blockers", []) or [f"preflight={pf.get('status')}"]
            return False
        return True

    def _require_bridge(self) -> bool:
        if self.bridge is None or isinstance(self.bridge.source, NullSignalAdapter):
            self.blockers.append("no live signal bridge wired (NullSignalAdapter)")
            return False
        return True

    # ------------------------------------------------------------------ #
    # Start / connect
    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        # resume: restore prior progress so opportunities are not double-counted
        if self.resume and self.store is not None and self.store.exists(self.session_id):
            prior = self.store.load(self.session_id)
            if prior is not None:
                self.progress.opportunities = prior.opportunities
                self.progress.first_signal_ts = prior.first_signal_ts
                self.progress.last_signal_ts = prior.last_signal_ts
                self.progress.heartbeats_ok = prior.heartbeats_ok
                self.progress.heartbeats_missed = prior.heartbeats_missed
                self.recorder.integrity_passed = prior.integrity_passed
                self.recorder.integrity_failed = prior.integrity_failed
                self.recorder.modified_signals = list(prior.modified_signals)
                self.connection_events = list(prior.connection_events)
                self._seen_ids = set(prior.seen_signal_ids)  # immutable trace-id dedup
                self._integrity_failed_seen = prior.integrity_failed

        if live_trading_enabled():
            self.blockers.append("LIVE_TRADING=true is not permitted in shadow phase")
            self.state = SessionState.BLOCKED
            return False
        if not self._check_preflight():
            self.state = SessionState.BLOCKED
            return False
        if not self._require_bridge():
            self.state = SessionState.BLOCKED
            return False

        # real virtual-account connection, wrapped so no order method exists
        if self.mode == "real":
            transport = DerivWebSocketTransport(app_id=self._cfg.app_id,
                                                ws_url=self._cfg.ws_url)
        else:
            from infrastructure.broker.deriv import DerivSimulatedTransport
            transport = DerivSimulatedTransport(symbol=self._cfg.symbol,
                                                currency=self._cfg.currency,
                                                is_virtual=True, tick_latency=True)
        adapter = DerivDemoAdapter(config=self._cfg.deriv_config(), transport=transport)
        self._view = ShadowBrokerView(adapter)
        try:
            self._view.connect()
        except Exception as e:
            self.blockers.append(f"connection failed: {e}")
            self.state = SessionState.BLOCKED
            return False
        if not self._view.is_connected() or self._view.is_virtual is not True:
            self.blockers.append("not a virtual-account connection")
            self.state = SessionState.BLOCKED
            return False

        # confirm contract spec from live contracts_for (for would-be mapping)
        with contextlib.suppress(Exception):
            cf = self._view.contracts_for(self._cfg.symbol)
            sel = select_contract(cf, self._cfg.symbol, needs_sl=True,
                                  needs_tp=True, size=10.0)
            if sel.confirmed:
                self._spec = sel.to_spec()
                self._spec.multiplier = (sel.multiplier
                                         if sel.category == "multiplier" else None)

        self.progress.start_wall = self.progress.start_wall or time.time()
        self.progress.last_heartbeat_wall = time.time()
        self.state = SessionState.RUNNING
        self.connection_events.append(
            {"wall_ts": time.time(), "kind": "connected", "detail": self.session_id})
        self._persist()
        return True

    # ------------------------------------------------------------------ #
    # Heartbeat
    # ------------------------------------------------------------------ #
    def heartbeat(self) -> bool:
        if self._view is None:
            return False
        try:
            self._view.heartbeat()
            self.progress.heartbeats_ok += 1
            self.progress.last_heartbeat_wall = time.time()
            return True
        except Exception as e:
            self.progress.heartbeats_missed += 1
            self.recorder.record_connection_failure()
            self.connection_events.append(
                {"wall_ts": time.time(), "kind": "lost", "detail": str(e)[:120]})
            self._alert(_AlertType.CONNECTION_LOST, detail=str(e)[:120])
            with contextlib.suppress(Exception):
                self._view.connect()
                if self._view.is_connected():
                    self.recorder.record_reconnect(True)
                    self.connection_events.append(
                        {"wall_ts": time.time(), "kind": "reconnected", "detail": ""})
            self._persist()
            return self._view.is_connected()

    # ------------------------------------------------------------------ #
    # Pump one opportunity from the bridge into the recorder
    # ------------------------------------------------------------------ #
    def pump_once(self) -> bool:
        """Pull one ShadowSignal from the bridge and record it. Returns False if
        the bridge currently has nothing."""
        if self.state != SessionState.RUNNING or self._view is None:
            return False
        sig = self.bridge.next()  # hardened bridge: validated, traced, hashed
        if sig is None:
            return False
        # resume-safe dedup: never re-count a signal_id seen before a restart
        if sig.signal_id and sig.signal_id in self._seen_ids:
            return True  # consumed, but not a new opportunity
        if sig.signal_id:
            self._seen_ids.add(sig.signal_id)

        try:
            quote = self._view.get_quote(sig.symbol)
        except Exception:
            self.recorder.record_missed()
            return True
        t0 = time.perf_counter()
        ev = self.recorder.record(sig, quote, (time.perf_counter() - t0) * 1000.0,
                                  self._spec, self._cfg.currency)
        p = self.progress
        p.opportunities += 1
        if p.first_signal_ts is None:
            p.first_signal_ts = sig.timestamp
        p.last_signal_ts = sig.timestamp

        # alerts (hooks only; no external services)
        if self.recorder.integrity_failed > self._integrity_failed_seen:
            self._integrity_failed_seen = self.recorder.integrity_failed
            self._alert(_AlertType.INTEGRITY_FAILURE, signal_id=sig.signal_id)
        if not ev.accepted and "risk" in (ev.reason or "").lower():
            self._alert(_AlertType.RISK_ANOMALY, signal_id=sig.signal_id,
                        reason=ev.reason)
        if self.bridge.health.status() == "STALE":
            self._alert(_AlertType.STALE_SIGNAL_FEED, signal_id=sig.signal_id)

        if p.opportunities % 25 == 0:
            self._persist()
        return True

    # ------------------------------------------------------------------ #
    # Controls
    # ------------------------------------------------------------------ #
    def request_stop(self, reason: str = "operator_request") -> None:
        self._stop_requested = True
        self.stop_reason = reason

    def stop(self, reason: str = "") -> None:
        self._stop_requested = True
        if reason:
            self.stop_reason = reason
        if not self.stop_reason:
            self.stop_reason = ("observation_complete" if self.progress.complete
                                else "stopped")
        if self._view is not None:
            with contextlib.suppress(Exception):
                self._view.disconnect()
            self.connection_events.append(
                {"wall_ts": time.time(), "kind": "lost", "detail": "session stop"})
        self.state = (SessionState.COMPLETE if self.progress.complete
                      else SessionState.STOPPED)
        self._alert(_AlertType.SESSION_STOPPED, reason=self.stop_reason,
                    verdict=self.status())
        self._persist()

    # ------------------------------------------------------------------ #
    # Status
    # ------------------------------------------------------------------ #
    def status(self) -> str:
        """PASS only when the observation period actually completes."""
        if self.state in (SessionState.BLOCKED,):
            return "BLOCKED"
        if (self._view is not None and self._view.live_orders_sent != 0):
            return "FAIL"
        if self.progress.complete:
            return "PASS"
        if self.state in (SessionState.RUNNING, SessionState.STOPPED,
                          SessionState.CREATED, SessionState.GATING):
            return "EXTEND"
        return "EXTEND"

    # ------------------------------------------------------------------ #
    # Bounded run (for real use the operator loops start()->pump/heartbeat->stop)
    # ------------------------------------------------------------------ #
    def run(self, max_opportunities: Optional[int] = None,
            heartbeat_every: int = 50) -> dict:
        if not self.start():
            self._report()
            return {"session_id": self.session_id, "status": "BLOCKED",
                    "blockers": self.blockers}
        cap = max_opportunities if max_opportunities is not None else 10_000_000
        i = 0
        while not self._stop_requested and i < cap:
            produced = self.pump_once()
            if not produced:
                break  # bridge idle/exhausted (real run keeps looping live)
            i += 1
            if i % heartbeat_every == 0:
                self.heartbeat()
        self.stop()
        self._report()
        return {"session_id": self.session_id, "status": self.status(),
                "opportunities": self.progress.opportunities,
                "observed_days": self.progress.observed_days,
                "live_orders": self._view.live_orders_sent if self._view else 0,
                "complete": self.progress.complete}

    # ------------------------------------------------------------------ #
    def _report(self) -> None:
        p = self.progress
        rec = self.recorder
        live_orders = self._view.live_orders_sent if self._view else 0
        rem = p.remaining()
        line = "=" * 66
        print(line)
        print(f"APEX ULTRA PHASE 40.3 SHADOW LAUNCHER   [mode: {self.mode.upper()}]")
        if self.mode == "dry-run":
            print("  NOTE: simulated — NOT a real shadow session and NOT a SHADOW PASS.")
        print(line)
        print(f"Session ID        : {self.session_id}")
        print(f"State             : {self.state.value}")
        print(f"Connection        : Deriv {self._cfg.ws_url} "
              f"({'connected' if (self._view and self._view.is_connected()) else 'down'})")
        if self._view is not None:
            print(f"Account           : {self._view.loginid} "
                  f"virtual={self._view.is_virtual}")
        print(f"Signal source     : {self.bridge.name if self.bridge else 'none'}")
        print("-" * 66)
        print("Progress:")
        print(f"  Opportunities   : {p.opportunities} / {MIN_OPPORTUNITIES} "
              f"({'met' if p.met_opportunities else 'NOT met'}, "
              f"{rem['opportunities_remaining']} remaining)")
        print(f"  Observed window : {p.observed_days:.2f} / {MIN_DAYS} days "
              f"({'met' if p.met_duration else 'NOT met'}, "
              f"{rem['days_remaining']:.2f} remaining)")
        print(f"  Heartbeats      : ok={p.heartbeats_ok} missed={p.heartbeats_missed}")
        print(f"  Bridge flow     : received={self.bridge.stats.received} "
              f"accepted={self.bridge.stats.accepted} "
              f"rejected={self.bridge.stats.rejected}")
        print(f"  Integrity       : passed={rec.integrity_passed} "
              f"failed={rec.integrity_failed}")
        print("-" * 66)
        print("Safety:")
        print(f"  Live orders sent: {live_orders}")
        if self.blockers:
            print("-" * 66)
            print("BLOCKERS:")
            for b in self.blockers:
                print(f"  - {b}")
        print(line)
        status = self.status()
        print(f"STATUS: {status}")
        if status == "EXTEND":
            print("  Observation period not yet complete — continue running.")
            print("  (SHADOW PASS is only declared once 14 days AND 500 opportunities")
            print("   are both met.)")
        print(line)


# --------------------------------------------------------------------------- #
# CLI entry — real run requires an injected live signal bridge
# --------------------------------------------------------------------------- #
def run(argv: list[str] | None = None, signal_bridge: Optional[APEXSignalAdapter] = None):
    argv = argv if argv is not None else sys.argv[1:]
    mode = "dry-run" if "--dry-run" in argv else "real"

    if signal_bridge is None:
        if mode == "real":
            print("=" * 66)
            print("APEX ULTRA PHASE 40.3 SHADOW LAUNCHER   [mode: REAL]")
            print("=" * 66)
            print("Cannot start: no live signal bridge supplied.")
            print("Wire your engine's signal emit to a LiveEngineSignalAdapter and pass")
            print("  run(['--real'], signal_bridge=APEXSignalAdapter(live_adapter))")
            print("=" * 66)
            print("STATUS: BLOCKED")
            return {"status": "BLOCKED", "reason": "no_signal_bridge"}
        # dry-run flow check uses the replay fixture bridge (clearly simulated)
        from adapters import ReplayJournalSignalAdapter
        fx = os.path.join(os.path.dirname(__file__), "fixtures", "sample_signals.jsonl")
        signal_bridge = APEXSignalAdapter(ReplayJournalSignalAdapter(path=fx),
                                          mode="dry-run")

    launcher = RealShadowLauncher(signal_bridge, mode=mode)
    return launcher.run(max_opportunities=(None if mode == "real" else 10_000))


if __name__ == "__main__":
    run()
