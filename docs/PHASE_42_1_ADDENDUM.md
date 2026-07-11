# APEX ULTRA -- Phase 42.1 Addendum (2026-07-10)

_Re-verify every claim against the filesystem and running code before
relying on it. When a document and the code disagree, the code wins._

## A. Named exposure change: token scope (forced by platform)

Deriv's developer platform (developers.deriv.com) no longer offers a
read-only token scope. The accounts-listing endpoint the frozen
transport calls (GET /trading/v1/options/accounts) returns HTTP 403
"Insufficient scopes" for tokens with only Application insights or
Account management. Verified verbatim via standalone probe
(rest403_probe.py, not part of the engine) on 2026-07-10.

Consequence: the live feed token is TRADE-SCOPED BY NECESSITY, not by
choice. Execution prevention therefore rests entirely on code guards:

  - adapter refuses non-virtual accounts at connect
    (verified live: chose DOT...79 demo, ignored ROT...99 real)
  - ShadowViolation on 7 execution names (adapter)
  - ExecutionForbiddenError (transport); trading ops unimplemented
  - LIVE_TRADING=true refuses to run (runner)
  - no code path from run_live to any execution surface

This is the same configuration Phase 43 actually validated (its token
was also trade-scoped). Recording it here makes it explicit.

Token hygiene: single active token (apex_trade_demo_2, Trade scope
only, 90-day expiry ~2026-10-08, stored offline). All prior tokens
deleted, including two exposed in chat logs on 2026-07-10 (both
revoked same day). Standing rules: credentials entered via Read-Host
followed by cls; terminal output shared only from the banner down.

## B. Phase 42.1 result (2026-07-10): DONE per locked definition

  (a) 42.0C regression: PASS (3/3)  [re-verified post-install]
  (b) CP3: PASS, no new allowlist entries
  (c) Live session live_signals_2026-07-10_session001.jsonl:
      282 polls, 130 duplicate ticks skipped, 2 rejected ticks
      (feed validation, noise level), 2 signals emitted, 0 emit
      failures; CP4 accepted 2/2, 0 rejected, Live orders sent: 0;
      CP5 PASS (epochs 1783744042 -> 1783744044).

## C. Known defect -> Phase 42.1a (fix BEFORE observation clock)

The live session emitted two "short" signals 2 seconds apart. A pure
crossing-moment strategy cannot do that. Cause: the stateless
previous-relationship reconstruction (prices[:-1]) is computed over a
SLIDING 25-close buffer; once the buffer is full, each new close also
drops the oldest, so the reconstructed "previous" window differs from
the window the prior evaluation saw. EMA seeding from the first
window element can then flip the sign while fast and slow EMAs hover
near equality (i.e., exactly around genuine crossings), producing
duplicate signals.

42.1a scope (correctness fix, NOT tuning): EmaCross tracks the last
relationship sign it emitted/observed within a session and emits only
on an actual sign change from that remembered state. Parameters stay
9/21. Snapshot path unaffected (single evaluation has no prior state).

Clock rule restated: the 14-day/500-observation window starts only
after 42.1a is the producer and all gates pass again. The 2026-07-10
session does NOT count toward the window.
