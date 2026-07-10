"""
APEX ULTRA — Shadow Operations Layer (Phase 40.4)

Operational controls around RealShadowLauncher:
  - SessionStore    : persist/resume session state to disk (JSON).
  - AlertHub        : in-process alert hooks (interfaces only; no external I/O).
  - exporters       : JSON report, CSV opportunity journal, text summary.

No trading logic, no signal generation. The store records what the launcher
observed; resume restores it so opportunities are never double-counted and
trace IDs stay immutable.
"""

from __future__ import annotations

import csv
import io
import json
import os
import time
from dataclasses import asdict
from typing import Callable, Optional

from infrastructure.shadow_telemetry import (
    AlertType,
    ConnectionEvent,
    SessionRecord,
)


# --------------------------------------------------------------------------- #
# Persistent session storage
# --------------------------------------------------------------------------- #
class SessionStore:
    """Durable JSON store keyed by session_id. Atomic writes (tmp + replace)."""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, session_id: str) -> str:
        safe = session_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.directory, f"{safe}.json")

    def exists(self, session_id: str) -> bool:
        return os.path.exists(self._path(session_id))

    def save(self, record: SessionRecord) -> None:
        path = self._path(record.session_id)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(record.to_dict(), f, indent=2, sort_keys=True)
        os.replace(tmp, path)  # atomic on same filesystem

    def load(self, session_id: str) -> Optional[SessionRecord]:
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return SessionRecord.from_dict(json.load(f))

    def list_sessions(self) -> list[str]:
        return sorted(f[:-5] for f in os.listdir(self.directory)
                      if f.endswith(".json"))


# --------------------------------------------------------------------------- #
# Alerting hooks (interfaces only — no external services connected)
# --------------------------------------------------------------------------- #
class AlertHub:
    """Register callbacks for alert types. Dispatch is in-process only; wiring a
    real notifier (email/Slack/PagerDuty) is a future phase."""

    def __init__(self) -> None:
        self._hooks: dict[AlertType, list[Callable]] = {a: [] for a in AlertType}
        self.history: list[dict] = []

    def on(self, alert: AlertType, callback: Callable) -> None:
        self._hooks[alert].append(callback)

    def fire(self, alert: AlertType, **payload) -> None:
        entry = {"alert": alert.value, "wall_ts": time.time(), **payload}
        self.history.append(entry)
        for cb in self._hooks[alert]:
            try:
                cb(entry)
            except Exception:
                pass  # a misbehaving hook must never break the shadow session

    def count(self, alert: Optional[AlertType] = None) -> int:
        if alert is None:
            return len(self.history)
        return sum(1 for h in self.history if h["alert"] == alert.value)


# --------------------------------------------------------------------------- #
# Report exporters
# --------------------------------------------------------------------------- #
def export_json(record: SessionRecord, recorder, *, infra_pass: bool,
                dryrun_pass: bool, real_ready: bool) -> str:
    payload = {
        "session": record.to_dict(),
        "summary": {
            "opportunities": record.opportunities,
            "integrity_passed": record.integrity_passed,
            "integrity_failed": record.integrity_failed,
            "heartbeats_ok": record.heartbeats_ok,
            "heartbeats_missed": record.heartbeats_missed,
            "final_verdict": record.final_verdict,
        },
        "status": {
            "infrastructure_pass": infra_pass,
            "dry_run_pass": dryrun_pass,
            "real_shadow_ready": real_ready,
            "live_orders_sent": 0,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def export_csv_journal(recorder) -> str:
    """CSV of the would-be opportunity journal. Records, never orders."""
    cols = ["signal_id", "timestamp", "symbol", "strategy", "signal_direction",
            "signal_score", "regime", "expected_entry", "market_price", "spread",
            "latency_ms", "risk_size", "would_be_order_size", "would_be_stop_loss",
            "would_be_take_profit", "reason", "accepted", "outcome", "r_multiple",
            "integrity_ok", "signal_hash"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for ev in getattr(recorder, "events", []):
        w.writerow({c: getattr(ev, c, "") for c in cols})
    return buf.getvalue()


def export_summary(record: SessionRecord, *, infra_pass: bool, dryrun_pass: bool,
                   real_ready: bool, alert_counts: Optional[dict] = None) -> str:
    days = 0.0
    if record.first_signal_ts and record.last_signal_ts:
        days = max(0.0, (record.last_signal_ts - record.first_signal_ts) / 86400.0)
    lines = [
        "APEX ULTRA — SHADOW SESSION SUMMARY",
        f"  session_id     : {record.session_id}",
        f"  mode           : {record.mode}",
        f"  state          : {record.state}",
        f"  opportunities  : {record.opportunities} / 500",
        f"  observed days  : {days:.2f} / 14",
        f"  heartbeats     : ok={record.heartbeats_ok} missed={record.heartbeats_missed}",
        f"  integrity      : passed={record.integrity_passed} failed={record.integrity_failed}",
        f"  connection evts: {len(record.connection_events)}",
        f"  stop reason    : {record.stop_reason or '(running)'}",
        f"  final verdict  : {record.final_verdict}",
    ]
    if alert_counts:
        lines.append(f"  alerts         : {alert_counts}")
    lines += [
        "  ---- status separation ----",
        f"  infrastructure PASS      : {infra_pass}",
        f"  dry-run PASS             : {dryrun_pass}",
        f"  real shadow readiness    : {'READY' if real_ready else 'NOT READY'}",
        f"  live orders sent         : 0",
    ]
    return "\n".join(lines)
