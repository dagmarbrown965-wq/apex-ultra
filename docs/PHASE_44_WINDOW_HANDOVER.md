# APEX ULTRA — PHASE 44 WINDOW HANDOVER

_Prepared Day 5 (2026-07-15) ahead of an advisor/model transition
expected ~2026-07-17. Re-verify every claim below against the
filesystem before relying on it. When a document and the code disagree,
the code wins. When this document and the git log disagree, the git
log wins._

## Role and governance

The reader assumes the Strategic Advisor seat per the AI Company
Constitution v1.1 (Level 1, in the project structure): challenge weak
ideas with evidence, never simply agree, CEO (DagmarBrown) decides.
Level 2 governing documents for this project, both on main:

- docs/PHASE_44_BOUNDARY_AGREEMENT.md  (v0.2, commit 7182c4b)
- docs/PHASE_44_AMENDMENT_V0_3.md      (commit 91622d6)

Read both in full before advising on anything. The amendment's
consolidated criteria section is the operative valid-session test.

## Window state as of Day 5 morning (verify: git log --oneline | Select-String "Window day")

- Window: 2026-07-11 through 2026-07-24 (14 calendar days).
- Requirements: >=1 valid session on >=12 of 14 days; >=14 valid
  sessions total; >=10,000 evaluated closes total; zero abort events.
- Day 1 (07-11) VALID   commit 726218c  1,355 closes
- Day 2 (07-12) MISSED  power outage killed session pre-summary;
                        grace day 1 of 2 SPENT
- Day 3 (07-13) VALID   commit 4461056  1,479 closes
- Day 4 (07-14) VALID x2  commits 0f658d6 (1,064) + 19222f6 (1,031)
                        (double-day cleared the arithmetic debt from
                        the missed Day 2; a second same-day session is
                        permitted, max two per day by standing rule)
- Running totals: 5 valid sessions; 4,929 closes; 1 grace day left.

## The daily routine (proven; do not improvise)

1. Preconditions (Amendment 4): laptop on MAINS power (confirmed, not
   assumed); network sane; phone timer set 35+ minutes, not started.
2. Credentials — three separate lines, three separate Enters, never
   queued; then cls; visually confirm the screen is blank:
     $env:DERIV_API_TOKEN = Read-Host "DERIV_API_TOKEN (the pat_ token, NOT the app id)"
     $env:DERIV_APP_ID = Read-Host "DERIV_APP_ID (alphanumeric app id ONLY, not the token)"
     cls
3. Launch, starting the timer on Enter, then hands off:
     py -m engine.runner --mode live --strategy ema_cross --max-signals 500
   NOTE: --max-polls does NOT exist as a CLI flag (verified via
   --help; recommending it was a logged advisor error). 500 signals is
   deliberately unreachable in 35 min; the timer is the real bound.
4. Timer rings -> Ctrl+C ONCE -> wait for SESSION SUMMARY -> record the
   output_path (.jsonl) and Summary file (.json) it prints.
5. Gates (substitute the real printed paths; never type placeholder
   text literally):
     py -m testing.shadow.signal_bridge_check --journal <journal>
     py -m engine.validation.check_cp5_session --journal <journal>
6. Get-Content the summary JSON. Valid-session check (ALL must hold):
   stopped_by in {max_polls, max_signals, manual_stop};
   duration_s >= 1800; ticks_rejected/ticks_seen <= 0.02;
   duration_s/polls <= 1.5; ticks_seen - ticks_duplicate -
   ticks_rejected >= 900; emit_failures = 0; live_orders_sent = 0;
   strategy = ema_cross; CP4 PASS; CP5 PASS.
7. If valid, commit BOTH artifacts with explicit paths (never -A):
     git add <journal> <summary>
     git commit -m "Window day N: session <session_id> (valid)"
     git push
   Day numbering follows the calendar day of the window (07-11 = day 1),
   so missed days leave visible gaps. Invalid sessions are NEVER
   committed; their artifacts stay on disk untracked, logged with reason.

## Abort conditions (window VOID — from v0.2, unchanged)

Any live_orders_sent > 0; any ShadowViolation; any new CP3 allowlist
entry; any change to EmaCross parameters or strategy code; any edit
under engine/ during the window (an emergency fix voids and restarts).
No optimization, no tuning. EmaCross stays 9/21. Signal statistics are
recorded, never judged.

## Incident and lesson log (this window)

- 07-11: trade-scoped token + app id exposed in chat (cls typed
  without Enter merged into next command; paste began above banner).
  Token apex_trade_demo_2 revoked same session; apex_trade_demo_3
  active, Trade scope (platform forces it), expiry ~2026-10-09,
  renewal calendared ~10-01. Standing fixes: three-line credential
  ritual; pastes selected from the ==== banner down only.
- 07-11: three consecutive Notepad hand-edit failures (including a
  silent mid-string mangle); resolved by revert-to-baseline plus an
  anchor-verified one-shot patch script. Standing preference: scripted
  anchored edits for any multi-line change; always re-read the edited
  region afterward.
- 07-11 (session002): network degradation -> 10.8% rejects, 8.75 s/poll.
  Drove Amendment v0.3 (rate tolerance + pace + volume criteria).
- 07-12: power outage killed a session before the summary write; the
  missing-summary-file criterion invalidated it cleanly (this is the
  documented residual risk of the manual_stop path, working as designed).
- 07-14 (session002): WiFi outage mid-run -> 33.6% rejects, 722 closes;
  invalid, caught by v0.3 criteria. Operator lesson: when the
  connection dies mid-session, Ctrl+C immediately; the session is
  already lost.
- 07-14 (session003): phone hotspot VALIDATED as fallback (0 rejects,
  1.29 s/poll, valid session on cellular).
- Advisor (architect) error log, all caught by verify-before-relying:
  recommended a nonexistent --max-polls CLI flag; proposed a
  machine-sleep hypothesis refuted by Windows event logs (System Id 42
  / Power-Troubleshooter are the checkable sources); set --max-signals
  50 without checking observed signal rates (a 50-bound session ended
  12.3 s short of the duration floor); built a time-of-day fatigue
  narrative on a laptop clock that was 7 hours wrong (timezone since
  corrected to SA Pacific Standard Time, UTC-5, no DST, clock synced).

## Environment facts

- Windows laptop, PowerShell. Python via the py launcher.
- Repo: $HOME\Downloads\APEX_ULTRA\apex_ultra
  (github.com/dagmarbrown965-wq/apex-ultra, branch main).
- Engine HEAD state includes W44.0 (commit e27d099): run_live writes
  session_summary_<id>.json alongside the journal; run_once untouched.
- Known-good gates: py -m engine.validation.test_m0_regression
  (PASS 3/3), py -m engine.validation.check_cp3_imports (PASS, single
  allowlist entry feed/live_readonly.py:77).
- Untracked non-window artifacts in engine/output/ are PERMANENT
  residents (throwaway + invalid sessions); do not commit or delete.
- Operator works rotating shifts (7-2 / 2-10 / 10-7); sessions anchor
  to best-rested time relative to shift, one per calendar day, max two.
- Jamaica power/WiFi are intermittent: mains precondition and the
  hotspot fallback exist for documented reasons.

## Parked items (decide with the CEO, never unilaterally)

- W44.1 (optional): --max-polls CLI flag for by-design endings; full
  micro-plan + gates + single scoped commit if pursued; NOT during the
  window (engine/ edits void it).
- Possible v0.4: harden the network precondition if a third mid-session
  degradation occurs (two so far: 07-11, 07-14).
- rest403_probe.py still in ~/Downloads; candidate for tools/ + commit.
- .gitattributes for the LF/CRLF warnings; editor upgrade (VS Code or
  Notepad++) as a logged between-items environment change.

## After the window ends (2026-07-24)

Judge PASS/FAIL strictly per v0.2-as-amended. A failed window is a
finding: diagnose, fix process (never parameters), restart the clock.
If PASS: the next phase is planned plan-first, same as everything here.
