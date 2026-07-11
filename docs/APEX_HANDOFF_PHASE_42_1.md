# APEX ULTRA -- Handoff (Phase 42.1 + 42.1a COMPLETE)

_Re-verify every claim below against the filesystem and running code before
relying on it. When a document and the code disagree, the code wins._

## PHASE 42.1 + 42.1a -- PASSED (2026-07-10, all gates green, verified live)

Real strategy (EmaCross, EMA 9/21 crossing-moment producer with per-session
sign state) replaced the ReferenceMA placeholder behind the unchanged
Strategy interface. Verified on the 42.1a code:

- Session: engine/output/live_signals_2026-07-10_session003.jsonl
  224 polls, 94 duplicate ticks skipped, 0 rejects, 1 signal
  (ts 1783746140.0, dir short, score 0.0268), 0 emit failures.
- 42.0C regression: PASS (3/3), run AFTER the 42.1a file was installed.
- CP3 gate: PASS -- same single allowlist entry (feed/live_readonly.py:77),
  no new entries.
- CP4 gate: PASS -- frozen bridge accepted 1/1 session003 signals,
  0 rejected, Live orders sent: 0.
- CP5 gate: PASS on session003.
- Git: commit 550f262 on private GitHub repo
  (github.com/dagmarbrown965-wq/apex-ultra). VERIFY PUSHED: at handoff
  time the push of 550f262 was still pending; `git status` must say
  "up to date with origin/main".

## HONESTY RECORD (read before trusting earlier commits)

- Session001 (2 signals) ran the ORIGINAL 42.1 code, which had a known
  duplicate-cross defect (two shorts 2s apart; cause: previous-relationship
  reconstruction from prices[:-1] over a sliding buffer flips sign near
  crossings). Recorded in docs/PHASE_42_1_ADDENDUM.md section C.
- Session002 ALSO ran the 42.1 code, despite commit 47d97a9 claiming the
  42.1a fix. Cause: stale-artifact substitution -- the revised download
  saved as "ema_cross (1).py" and the copy command installed the stale
  original. Caught because the commit diff did not list ema_cross.py.
  Commit 47d97a9's message ("observation clock eligible") is WRONG;
  550f262 corrects the record.
- Session003 is the first session on genuine 42.1a code
  (probe-verified: _last_sign present at line 83 before the run).
- The 14-day/500 observation window has NOT started. It is ELIGIBLE to
  start now, but Phase 44 must first define (plan-first) what counts as
  an observation, session cadence, and pass criteria. No session to date
  counts toward the window. NOT DEMO READY. NOT SHADOW PASS.

## What this phase added / changed

- engine/strategy/ema_cross.py -- NEW. EmaCross(9/21), emits only on a
  sign change of (fast EMA - slow EMA); first sufficient evaluation
  records the sign and stays silent; parameters locked, no tuning.
- engine/runner.py -- MODIFIED (permitted: strategy selection mechanism).
  STRATEGY_CLASSES table; run_live(strategy_name=...); --strategy CLI
  flag (default reference_ma, so default invocation unchanged); banner
  is honest about which strategy is producing. run_once UNTOUCHED
  (pinned to ReferenceMA; 42.0C byte-identical path).
- docs/PHASE_42_1_BOUNDARY_AGREEMENT.md -- locked five-point agreement.
- docs/PHASE_42_1_ADDENDUM.md -- token-scope exposure change + defect
  record.
- .gitignore -- NEW (__pycache__/, *.pyc, *.pyo, .env); committed .pyc
  files purged from the repo.
- rest403_probe.py -- standalone diagnostic (stdlib only, engine-free),
  currently ONLY in ~/Downloads. RECOMMENDED: copy into tools/ and
  commit; it proved its worth today.

## Named exposure change (Deriv platform, forced)

Deriv's developer platform (developers.deriv.com) no longer offers a
read-only token scope. GET /trading/v1/options/accounts returns 403
"Insufficient scopes" (verbatim, probe-verified) for insights-only and
account-management tokens; Trade scope is REQUIRED even to list accounts.
The live-feed token is therefore trade-scoped by necessity. Execution
prevention rests entirely on code guards, all verified live today:
adapter chose demo account DOT...79 and ignored real account ROT...99;
ShadowViolation (7 names); ExecutionForbiddenError (transport, trading
ops unimplemented); LIVE_TRADING=true refuses to run; no execution code
path in run_live. Live orders sent: 0 in all three sessions.

Token hygiene: single active token apex_trade_demo_2 (Trade scope only,
expires ~2026-10-08, stored offline). All other tokens deleted. Two
tokens were exposed in chat logs on 2026-07-10; both revoked same day.
Standing rules: credentials via Read-Host then cls; share terminal
output from the banner down only.

## Lessons carried forward (additions this phase)

- STALE-ARTIFACT SUBSTITUTION is placeholder-failure's cousin: a
  successful copy of the wrong file passes every gate that does not
  inspect content. Standing rule: every file install ends with a content
  probe (Select-String for a string only the new version contains).
  A commit diff that does not list the file you claim to have changed
  is a red alert, not a formality.
- Debug from the API's verbatim words, not from guesses: the transport
  captured the 403 body but the adapter discarded it; a 60-line
  standalone probe read "Insufficient scopes" and ended the guessing.
  Probe outside the engine before touching frozen code.
- Browser duplicate-download naming ("file (1).py") plus a same-named
  stale file is a trap; delete stale downloads immediately after install.
- Credential prompts need labels that state what they are NOT
  ("numeric app id ONLY, not the token"); the token went into the
  app-id prompt once.
- New-platform quirks: app IDs are alphanumeric now (not numeric);
  pat_ tokens require the Deriv-App-ID header; token creation lives at
  developers.deriv.com/dashboard/tokens/create; token max expiry 90 days
  -- calendar the renewal or the feed dies silently ~2026-10-08.

## Re-run / sanity commands

```powershell
cd $HOME\Downloads\APEX_ULTRA\apex_ultra
git status                                      # up to date with origin
py -m engine.validation.test_m0_regression      # -> PASS (3/3)
py -m engine.validation.check_cp3_imports       # -> CP3: PASS
py -m engine.runner                             # snapshot path, unchanged
# live session (Read-Host for both env vars, then cls, never in chat):
py -m engine.runner --mode live --strategy ema_cross --max-signals 3
py -m testing.shadow.signal_bridge_check --journal <session file>
py -m engine.validation.check_cp5_session --journal <session file>
# content probe for the strategy actually installed:
Select-String -Path .\engine\strategy\ema_cross.py -Pattern "_last_sign"
```

## NEXT: Phase 44 -- observation window (NOT STARTED, plan first)

Define BEFORE any session counts: what one observation is (a signal? a
session? a close evaluated?), session cadence and duration toward the
14-day/500 target, what is measured (structural integrity only vs.
signal statistics), and the pass/fail criteria at window end. No
optimization / no tuning rules hold; EmaCross parameters stay 9/21 for
the entire window. The filesystem remains the source of truth.
