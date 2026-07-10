# APEX ULTRA -- Handoff (Phase 43 COMPLETE)

_Re-verify every claim below against the filesystem and running code before
relying on it. When a document and the code disagree, the code wins._

## PHASE 43 -- PASSED (2026-07-01, all gates green, verified live)

Live observation loop validated end-to-end on real Deriv demo market data:

- Session: engine/output/live_signals_2026-07-01_session001.jsonl
  51 polls, 22 duplicate ticks skipped (R_100 ticked ~2s vs 1s poll),
  29 real closes (19 warmup + 10 signals), 0 rejects, 0 emit failures.
- CP3 gate:  PASS (py -m engine.validation.check_cp3_imports)
- CP4 gate:  PASS -- frozen bridge accepted 10/10 live-originated signals,
  0 rejected, Live orders sent: 0
  (py -m testing.shadow.signal_bridge_check --journal <session file>)
- CP5 gate:  PASS (py -m engine.validation.check_cp5_session --journal ...)
  strictly increasing numeric epochs 1782971590 -> 1782971608
- 42.0C regression: still PASS (3/3) after all Phase 43 work.

HONESTY CONSTRAINT (unchanged): Phase 43 ran ReferenceMA, a PLACEHOLDER.
It validated LIVE PLUMBING, not a strategy. These observations must NOT be
recorded as "the strategy was observed." The 14-day/500 observation clock
has NOT started. NOT DEMO READY. NOT SHADOW PASS.

## What Phase 43 added (all new, nothing frozen touched)

- docs/PHASE_43_BOUNDARY_AGREEMENT.md -- locked four-boundary agreement
- engine/feed/live_readonly.py -- buffering read-only live feed:
  close = _Quote.mid (pinned), 20-close warmup, maxlen 25, duplicate-epoch
  re-reads skipped and counted, lazy allowlisted broker import in connect()
- engine/runner.py -- extended: run_once UNCHANGED (default path identical);
  run_live added (--mode live, per-session files
  live_signals_<date>_session<NNN>.jsonl, bounded by --max-signals or
  Ctrl+C, LIVE_TRADING=true refuses to run, one signal per NEW close so
  timestamps strictly increase by construction)
- engine/validation/check_cp3_imports.py -- permanent CP3 gate:
  allow ONLY rest_shadow_adapter + rest_transport, ONLY in
  feed/live_readonly.py, ONLY lazily; deny adapters.*/testing.* and all
  other infrastructure.*; teeth-tested against 7 violation classes
- engine/validation/check_cp5_session.py -- session integrity gate:
  JSONL valid, v1.0 shape, no bridge fields, numeric strictly-increasing
  timestamps, single symbol/strategy, per-session filename; teeth-tested
  against 8 defect classes. Deliberately does NOT assert byte-identical
  live output (live closes differ by design; 42.0C covers transform
  determinism on the snapshot path).

## Named exposure change (agreed, Boundary 2)

Execution surface: still 0. Network-read+auth surface: 0 -> 1 (the live
feed authenticates and reads ticks). Guards inherited unmodified:
ShadowViolation on 7 execution names (adapter), ExecutionForbiddenError
(transport), non-virtual account refused at connect.

## Security note (ACTION MAY BE PENDING -- verify)

The pat_ token used for the first live session was exposed in plaintext
(chat log + PowerShell history) during setup. Required cleanup: revoke and
regenerate the PAT on the Deriv developer platform (read-only scope), and
delete pat_ lines from (Get-PSReadLineOption).HistorySavePath. If this has
not been confirmed done, do it before the next live session.

## Re-run / sanity commands

```powershell
cd $HOME\Downloads\APEX_ULTRA\apex_ultra
py -m engine.validation.test_m0_regression      # -> PASS (3/3)
py -m engine.validation.check_cp3_imports       # -> CP3: PASS
py -m engine.runner                             # snapshot path, unchanged
# live session (set DERIV_API_TOKEN + DERIV_APP_ID first, never in chat):
py -m engine.runner --mode live --max-signals 10
py -m testing.shadow.signal_bridge_check --journal <session file>
py -m engine.validation.check_cp5_session --journal <session file>
```

## NEXT: Phase 42.1 -- real strategy (NOT STARTED, plan first)

Swap genuine logic behind the Strategy interface. Plan-first rules:
- Define "done" BEFORE starting: 42.1 has no CP4-style pass/fail gate
  ("good strategy" is not a question the bridge can answer).
- No optimization / no tuning rules hold.
- The ApexV5_*.jsx dashboard is a SPEC reference only; no portable logic.
- Only after 42.1 is the producer does the 14-day/500 demo observation
  window (Phase 44+) begin to mean anything.

## Lessons carried forward (additions this phase)

- Placeholder text in commands is a real failure mode: three separate
  incidents of template strings being run literally (token, filename,
  example line). Deploy scripts now self-verify; credential setup should
  use Read-Host prompts, never edit-the-quotes lines.
- PS 5.1 reads BOM-less UTF-8 as ANSI (Get-Content without -Encoding).
  Standing rule: artifacts and verify steps are ASCII-only; files written
  via WriteAllText with BOM-less UTF8Encoding.
- Poll cadence vs tick cadence: R_100 ticked ~2s against a 1s poll; the
  duplicate-epoch guard skipped 22/51 reads in the first session. Without
  it, half the buffer would have been double-counted closes.
- The filesystem remains the source of truth. The CP3/CP5 gates are now
  permanent runnable tools, not chat-history assertions.