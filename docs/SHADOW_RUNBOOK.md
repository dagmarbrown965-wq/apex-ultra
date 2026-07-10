# APEX ULTRA — Shadow Run Operations Runbook (Phase 40.4)

Operational guide for running, monitoring, persisting, resuming, and reporting a
real Deriv-demo shadow session. This layer adds **operations only** — no trading
logic. `Live orders sent` is always `0`, structurally.

## Preconditions (your machine)

1. Deriv demo API token + App ID, `websocket-client` installed, project files present.
2. Confirm readiness:
   ```bash
   python -m testing.preflight.apex_demo_ready --real     # must print FINAL STATUS: READY
   ```
   The launcher refuses to start until this is READY.

## Starting a real shadow session

```python
from adapters import APEXSignalAdapter, LiveEngineSignalAdapter, SessionStore, AlertHub
from testing.shadow.shadow_launcher import RealShadowLauncher

live   = LiveEngineSignalAdapter()                      # engine calls live.push(signal_dict)
bridge = APEXSignalAdapter(live, mode="real")           # validates / traces / hashes
store  = SessionStore("var/shadow_sessions")            # durable JSON state
alerts = AlertHub()                                     # in-process alert hooks

launcher = RealShadowLauncher(bridge, mode="real", store=store, alerts=alerts)
launcher.run()                                          # gates on READY, then observes
```

Your engine's existing signal-emit hook pushes canonical v1.0 dicts into
`live.push(...)`. The launcher consumes them, records would-be trades, and never
sends an order.

## Persistence & resume

State is written to `SessionStore` (atomic JSON per `session_id`): id, timestamps,
heartbeats, opportunity count, integrity counts, connection events, stop reason,
and the running verdict. To resume after a restart, reuse the **same session_id**
with `resume=True`:

```python
launcher = RealShadowLauncher(bridge, mode="real", store=store,
                              session_id="SHADOW-...", resume=True)
launcher.run()
```

On resume the launcher restores progress and the set of seen `signal_id`s, so
**opportunities are never double-counted** and **trace IDs stay immutable**.

## Alerting hooks (interfaces only)

Register callbacks; nothing is sent externally yet:

```python
from adapters import AlertType
alerts.on(AlertType.CONNECTION_LOST,   lambda e: ...)
alerts.on(AlertType.STALE_SIGNAL_FEED, lambda e: ...)
alerts.on(AlertType.INTEGRITY_FAILURE, lambda e: ...)
alerts.on(AlertType.RISK_ANOMALY,      lambda e: ...)
alerts.on(AlertType.SESSION_STOPPED,   lambda e: ...)
```

Wiring a real notifier (email/Slack/PagerDuty) is a future phase.

## Reports & exports

```python
from adapters import export_json, export_csv_journal, export_summary
rec = launcher._to_record()
open("report.json","w").write(export_json(rec, launcher.recorder,
        infra_pass=True, dryrun_pass=True, real_ready=False))
open("journal.csv","w").write(export_csv_journal(launcher.recorder))
open("summary.txt","w").write(export_summary(rec,
        infra_pass=True, dryrun_pass=True, real_ready=False))
```

- **JSON report** — full session record + summary + status block.
- **CSV opportunity journal** — one row per would-be trade (trace id, hash, context, reason).
- **Text summary** — human-readable status with the three-way separation.

## Completion & status

- `EXTEND` — minimums not yet met; keep running.
- `PASS` — **only** after 14 calendar days **and** 500 opportunities are both met.
- `BLOCKED` — preflight not READY, no live bridge, or `LIVE_TRADING=true`.
- `FAIL` — a safety violation (never expected; live orders are structurally impossible).

The launcher does **not** declare SHADOW PASS until the real observation period
actually completes. Infrastructure passing and dry-run passing are reported
separately from real shadow readiness, which only your live run establishes.

## Validate the ops layer

```bash
python -m testing.shadow.phase404_report      # reliability tests + regression + status separation
```
