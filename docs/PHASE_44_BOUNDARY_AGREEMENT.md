# PHASE 44 BOUNDARY AGREEMENT (v0.2 — LOCK CANDIDATE)

_Status: DRAFT until committed to docs/ on main. Once committed, this
agreement is locked for the duration of the observation window. The
filesystem is the source of truth; every claim herein is verifiable
from files on disk._

## Purpose

Define the 14-day / volume-floor observation window for EmaCross (9/21)
before any session counts toward it. No optimization, no tuning:
EmaCross parameters stay 9/21 for the entire window.

## W44.0 — Prerequisite: session summary persistence (BLOCKS window start)

Scope: `run_live` in engine/runner.py ONLY. `run_once` untouched
(42.0C byte-identical path preserved).

Change: the existing summary dict (runner.py ~line 230) gains fields:
`start_ts`, `end_ts`, `strategy`, `symbol`, `poll_interval`,
`max_signals`, `max_polls`. The dict is written as JSON to
`engine/output/session_summary_<session_id>.json` alongside the
existing print. No other behavior changes.

Gates to close W44.0 (all must pass, in order):
1. Micro-plan approved: exact diff described in prose before code.
2. 42.0C regression: PASS (3/3).
3. CP3: PASS, allowlist unchanged (single entry, feed/live_readonly.py:77).
4. Commit diff lists engine/runner.py and NOTHING else.
5. Content probe: `Select-String -Path .\engine\runner.py -Pattern
   "session_summary_"` hits.
6. One throwaway live session (does NOT count toward the window)
   produces a summary file with sane values in every field.

## Definitions

- **Evaluated closes** = `ticks_seen − ticks_duplicate − ticks_rejected`,
  computed from the session summary file only.
- **Session duration** = `end_ts − start_ts`, from the summary file only.
- If a value is not in the summary file, it does not exist.

## Valid session (unit of validity)

ALL of the following, verified from the filesystem:
- Session summary file present in engine/output/.
- Signal journal file present (may contain zero signals).
- `stopped_by` ∈ {`max_polls`, `max_signals`, `manual_stop`}.
- `emit_failures` = 0.
- `live_orders_sent` = 0.
- `ticks_rejected` = 0 (strict; may be loosened only by a v0.3
  amendment citing evidence from invalid sessions).
- Duration ≥ 30 minutes (1800 s). This floor binds regardless of how
  the session ended; a manual_stop at 25 minutes is an invalid session.
- `strategy` = `ema_cross`.
- CP4 (signal_bridge_check) PASS on the session journal.
- CP5 (check_cp5_session) PASS on the session journal.

An invalid session does not count and is logged with its reason. An
invalid session does not by itself void the window (see Aborts).

Recommended launch shape (not mandated): `--max-polls 2400`
(~40 min at 1.0 s poll interval) so sessions end by design and clear
the 30-minute floor with margin.

## Window

- 14 consecutive calendar days, starting the day of the first valid
  session after (a) this agreement is committed and (b) W44.0 gates
  are closed.
- Cadence: ≥1 valid session on ≥12 of the 14 days (2 grace days).
- Total ≥14 valid sessions.
- Total evaluated closes across all valid sessions ≥10,000 (backstop).

## Measured vs. recorded

- **Gated (structural integrity):** the valid-session criteria above;
  zero CP3 allowlist growth; regression green on any mid-window re-run.
- **Recorded, NOT judged (signal statistics):** signal count, direction
  mix, scores, inter-signal spacing. No minimum, no maximum, no quality
  opinion. Judging signal quality mid-window is tuning pressure;
  tuning is banned.

## Pass / fail at window end

- **PASS:** cadence met AND ≥14 valid sessions AND ≥10,000 evaluated
  closes AND zero abort events.
- **FAIL:** any of the above unmet at day 14. A failed window is a
  finding: diagnose, fix process (never parameters), restart the clock.

## Immediate aborts (window VOID)

- Any `live_orders_sent` > 0.
- Any ShadowViolation.
- Any new CP3 allowlist entry.
- Any change to EmaCross parameters or strategy code.
- Any edit under engine/ during the window other than an emergency
  fix; an emergency fix itself voids the window, which restarts only
  after all gates re-pass.

## Operational events (session-voiding, not window-voiding)

- Token renewal (expiry ~2026-10-08; calendar it — safely past a July
  window; clause is future-proofing).
- Machine reboot mid-session.
- Feed outage mid-session.

## Standing rules (carried forward, unchanged)

- Filesystem over chat history; re-verify before relying.
- No code before a locked micro-plan.
- Credentials via Read-Host then cls; share output banner-down.
- Every file install ends with a content probe.
- Delete stale downloads immediately after install.

## Sequencing

1. Commit this file as docs/PHASE_44_BOUNDARY_AGREEMENT.md (locks it).
2. Micro-plan W44.0 (prose diff, approved before code).
3. Implement W44.0; run gates 2–6; commit; push.
4. Throwaway proving session (not counted).
5. Window starts on the next valid session.

## Decision log

- 2026-07-11: duration floor 30 min (user); all three stop reasons
  valid (user; architect recommended max_polls-only — duration floor
  accepted as the binding discipline instead); ticks_rejected strict 0
  (architect recommendation, user deferred).
