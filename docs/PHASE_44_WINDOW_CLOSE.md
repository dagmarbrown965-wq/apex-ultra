# APEX ULTRA — PHASE 44 WINDOW CLOSE ASSESSMENT

**Verdict: PASS**

_Assessed 2026-07-24 against docs/PHASE_44_BOUNDARY_AGREEMENT.md (v0.2,
commit 7182c4b) as amended by docs/PHASE_44_AMENDMENT_V0_3.md (commit
91622d6). Every figure below is derived from committed session summary
JSON files and the git log. Re-verify with:
`git log --oneline | Select-String "Window day"`_

## Window

- Opened 2026-07-11 (first valid session, after W44.0 closed).
- Closed 2026-07-24 (day 14).
- Strategy EmaCross 9/21 throughout, unchanged. No optimization, no
  tuning, no engine edits during the window.

## Criteria and results

| Criterion | Required | Actual | Result |
|---|---|---|---|
| Valid sessions | >= 14 | 14 | PASS |
| Days with >= 1 valid session | >= 12 of 14 | 12 | PASS |
| Evaluated closes (total) | >= 10,000 | 15,543 | PASS |
| Abort events | 0 | 0 | PASS |

Grace days: 2 of 2 used (2026-07-12, 2026-07-22). Zero margin
remained; the window passed on the exact minimum for both cadence and
session count.

## Session ledger (all committed; closes = seen - duplicate - rejected)

| Day | Date | Session | Commit | Closes |
|---|---|---|---|---|
| 1 | 07-11 | session004 | 726218c | 1,355 |
| 2 | 07-12 | — | — | MISSED (grace) |
| 3 | 07-13 | session001 | 4461056 | 1,479 |
| 4 | 07-14 | session001 | 0f658d6 | 1,064 |
| 4 | 07-14 | session003 | 19222f6 | 1,031 |
| 5 | 07-15 | session001 | 38e1ca7 | 1,050 |
| 6 | 07-16 | session001 | ab10118 | 1,046 |
| 7 | 07-17 | session001 | 56d8cf0 | 1,048 |
| 8 | 07-18 | session001 | f613cbd | 1,041 |
| 9 | 07-19 | session001 | 89d641f | 1,052 |
| 10 | 07-20 | session001 | 9312018 | 1,047 |
| 11 | 07-21 | session001 | bd690c1 | 1,095 |
| 12 | 07-22 | — | — | MISSED (grace) |
| 13 | 07-23 | session001 | 91264a3 | 1,080 |
| 13 | 07-23 | session002 | 5b36431 | 1,076 |
| 14 | 07-24 | session002 | 75c0738 | 1,079 |
| | | **Total** | | **15,543** |

Every banked session: stopped_by = manual_stop; duration_s >= 1800;
ticks_rejected = 0 (rate 0.00%, tolerance was 2%); pace 1.11-1.29
s/poll (limit 1.5); closes >= 1,031 (floor 900); emit_failures = 0;
live_orders_sent = 0; CP4 PASS; CP5 PASS.

## Invalid sessions (recorded, never committed; artifacts untracked)

| Date | Session | Cause | Failing criterion |
|---|---|---|---|
| 07-11 | session001 | throwaway W44.0 proving run | not a window session |
| 07-11 | session002 | network degradation (8.75 s/poll) | rejects 10.8%, pace |
| 07-11 | session003 | max_signals 50 bound hit early | duration 1787.7s, closes 891 |
| 07-12 | session001 | power outage killed process | no summary file written |
| 07-14 | session002 | WiFi outage mid-run | rejects 33.6%, closes 722 |
| 07-22 | session001 (x2) | token invalidated by Deriv T&C | rejects 100%, closes 0 |
| 07-22 | session001 (retry) | connection degraded mid-run | rejects 76%, closes 282 |
| 07-22 | session002 | connection down | rejects 100%, closes 0 |
| 07-24 | session001 | 60-second pre-flight probe | intentional, not a candidate |

Eight invalid sessions were detected and excluded by the criteria
without judgment calls. Two of them (07-11 session002, 07-14
session002) supplied the evidence that produced Amendment v0.3.

## What the window demonstrated

Structural integrity held under every condition encountered:

- 1,046 signals across 14 sessions passed the frozen bridge (CP4) with
  100% schema validity, 0 rejected, 0 duplicates.
- CP5 confirmed strictly increasing timestamps in every session,
  including the hottest (79 signals) and the sparsest.
- live_orders_sent = 0 in every session, valid and invalid alike. No
  execution path was ever reached.
- CP3 allowlist unchanged (single entry, feed/live_readonly.py:77).
  42.0C regression PASS on every check.

Signal statistics are recorded, not judged, per the agreement:
1,046 signals total, 48-79 per session, direction strictly alternating
long/short (a structural property of a crossing-moment producer, not a
performance claim). Duplicate-read rate held at 40-45% across all
sessions. NOTHING in this document constitutes evidence that the
strategy is profitable, and no such claim is made or implied.

## Operational events (session-voiding, not window-voiding, per v0.2)

- 2026-07-22: Deriv terms-and-conditions acceptance invalidated token
  apex_trade_demo_3 mid-window. Diagnosed from the reject signature
  (100% from poll 1, connection reachable), replaced with a new
  Trade-scope token same day, feed restored. Cost: one missed day.
- 2026-07-11: laptop timezone corrected (UTC-12 -> UTC-5, SA Pacific
  Standard Time, no DST) before any session ran. Epoch-based data
  unaffected.
- 2026-07-15: repository accidentally moved to Downloads\trading bot,
  restored; nine non-window artifacts found staged post-move and
  unstaged before any commit.

## Findings carried forward

1. The measurement gap discovered before the window (session statistics
   existed only in console output) was the single most valuable finding
   of the phase. W44.0 fixed it in 17 lines. Nothing in this window
   would have been verifiable without it.
2. Criteria that can fail are the only criteria worth having. Eight
   invalid sessions prove the gates were live, not decorative.
3. External dependencies (power, network, platform tokens) caused every
   missed day. None were execution errors. A future window should
   consider more than two grace days, or a documented pre-flight probe
   (the 60-second warmup check, used 07-23 and 07-24, proved its value).
4. Amendment v0.3 was written from evidence mid-window and improved the
   criteria without weakening them. That process should be the template.

## Parked items (unchanged, for the next phase to decide)

- W44.1 (optional): --max-polls CLI flag for by-design endings.
- rest403_probe.py: no longer in Downloads; recreate and commit to
  tools/ if the diagnostic is wanted again (it was missed on 07-22).
- .gitattributes for LF/CRLF; editor upgrade; repository relocation to
  a stable path outside Downloads.
- Token apex_trade_demo_4 (or successor): calendar renewal ~90 days
  from 2026-07-22.

## Status after this window

Phase 44 PASSED. The engine produced 14 structurally clean observation
sessions under real live-feed conditions with no execution path ever
reached.

This is NOT a demo-ready or shadow-pass declaration, and it is not
evidence of strategy performance. It is evidence that the observation
apparatus works and that the discipline holds. The next phase is
planned plan-first, as everything here was.
