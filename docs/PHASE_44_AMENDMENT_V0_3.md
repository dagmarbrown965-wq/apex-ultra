# PHASE 44 BOUNDARY AGREEMENT — AMENDMENT v0.3

_Status: DRAFT until committed to docs/ on main. Amends the locked v0.2
(docs/PHASE_44_BOUNDARY_AGREEMENT.md, commit 7182c4b). Where this
amendment and v0.2 conflict, this amendment governs. All other v0.2
provisions stand unchanged. The filesystem is the source of truth._

## Evidence base (why this amendment exists)

Session live_signals_2026-07-11_session002 (INVALID, does not count):
- ticks_rejected 151 / ticks_seen 1400 (10.8%); duration_s 12248.5 with
  only 1400 polls (mean 8.75 s/poll against a 1.0 s design) — severe
  feed/network degradation from ~23 minutes in.
- Code inspection (engine/feed/live_readonly.py, poll path) shows
  EXACTLY ONE reject condition: quote absent or without numeric mid.
  ticks_rejected therefore measures FEED AVAILABILITY, not data
  corruption. v0.2's strict-0 unintentionally gated on "perfect network
  for 30+ continuous minutes."
- The session also exposed a gap: the 30-minute duration floor passed
  while throughput collapsed. Duration alone cannot certify a session.
- Diagnostic value banked: CP4 PASS (38/38) and CP5 PASS (strictly
  increasing timestamps) under 38-signal load — the frozen bridge and
  producer guarantees held under the hottest load to date.
- Hypothesis correction logged: machine-sleep was proposed as the cause,
  checked against Windows event logs (System Id 42 / Power-
  Troubleshooter), and REFUTED — no sleep event inside the session
  window. Cause attributed to network degradation per the poll-pace
  arithmetic. Standing rule reaffirmed: hypotheses are tested against
  machine records, including the architect's.

## Amendment 1 — Rejects: absolute becomes rate

v0.2's "ticks_rejected = 0 (strict)" is REPLACED by:

    ticks_rejected / ticks_seen <= 0.02  (2%)

computed from the session summary JSON only. Session002 (10.8%) fails
this by 5x. A healthy session is expected to sit at ~0%.

## Amendment 2 — Throughput criteria (new, both required)

Added to the valid-session criteria:

- PACE: duration_s / polls <= 1.5 seconds per poll.
  (Design pace is ~1.0 s sleep + poll cost; 1.5 tolerates normal
  jitter; session002's 8.75 fails instantly.)
- VOLUME: evaluated closes >= 900 per session, where evaluated closes
  = ticks_seen - ticks_duplicate - ticks_rejected.
  (Observed duplicate rate ~40% implies a healthy 30-minute session
  yields ~1,000+ closes; 900 leaves margin.)

Both are computed from fields already present in the session summary
JSON. No code change required.

## Amendment 3 — Window session artifacts are committed

After each VALID window session, its two artifacts (the signal journal
.jsonl and the session summary .json) are committed together:

    git add <journal> <summary>        (explicit paths, never -A)
    git commit -m "Window day N: session <session_id> (valid)"
    git push

One commit per session. Invalid sessions' artifacts remain on disk but
are NOT committed; they are recorded in the phase log with the reason.
Rationale: the window becomes auditable from the repository alone, and
day-N evidence becomes tamper-evident. The two currently untracked
session002 artifacts remain untracked (invalid session).

## Amendment 4 — Operational preconditions (checklist, not gates)

Before launching any window session:
1. Mains power connected (event log shows a battery-triggered sleep on
   2026-07-10; battery operation is a live risk).
2. Network sanity: at minimum, a quick connectivity check; do not
   launch on a connection known to be degraded.
3. Credentials via three separate Read-Host lines, three separate
   Enters, cls confirmed to have cleared the screen before proceeding.
4. Timer set BEFORE launch (>= 35 minutes recommended for margin over
   the 30-minute floor).
5. Pastes into chat begin at the ==== banner; nothing from chat or
   console output is ever pasted INTO the terminal.

## Recorded, not gated

- Optional future work item W44.1: --max-polls CLI flag for by-design
  session endings. Not required; manual_stop remains valid per v0.2.
  If pursued, W44.1 gets the full treatment: micro-plan, gates, single
  scoped commit.
- Signal statistics remain recorded-not-judged per v0.2. Session002's
  38 signals with rapid alternation are logged as a statistic only.

## Consolidated valid-session criteria (v0.2 as amended — for reference)

ALL of, verified from the filesystem:
- Session summary file present; signal journal present.
- stopped_by in {max_polls, max_signals, manual_stop}.
- emit_failures = 0; live_orders_sent = 0.
- ticks_rejected / ticks_seen <= 0.02.
- duration_s >= 1800.
- duration_s / polls <= 1.5.
- ticks_seen - ticks_duplicate - ticks_rejected >= 900.
- strategy = ema_cross.
- CP4 PASS and CP5 PASS on the session journal.

## Decision log

- 2026-07-11 (post-session002 analysis, decided rested): reject-rate
  tolerance <= 2% (user, per recommendation); throughput = pace AND
  volume (user, per recommendation); valid-session artifacts committed
  per session (user, per recommendation). All three thresholds derived
  from session002 evidence and healthy-session arithmetic, not tuning.
