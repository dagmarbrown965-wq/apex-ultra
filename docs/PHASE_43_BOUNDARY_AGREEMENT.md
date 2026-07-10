# PHASE 43 -- FOUR-BOUNDARY AGREEMENT (LOCKED)

Status: AGREED (planning artifact -- gates implementation)
Locked: 2026-07-01
Rule: No Phase 43 code exists or may be written except as specified here.
When this document and the running code disagree, the code wins and this
document gets corrected to match.

## Scope

Phase 43 proves that a real-time market-data source can feed the existing
engine -> JSONL -> frozen shadow bridge path without enabling execution.

It does NOT evaluate strategy quality or profitability.
It does NOT begin the official 14-day / 500-opportunity observation window.
It runs ReferenceMA, a PLACEHOLDER. Its observations must NEVER be recorded
or remembered as "the strategy was observed."

## Boundary 1 -- Feed boundary

- Source: existing REST/OTP read-only surface ONLY:
  infrastructure.broker.deriv.rest_shadow_adapter.RestOtpShadowAdapter
  No order-capable endpoint is constructed or imported.
- New file: engine/feed/live_readonly.py -- a MarketFeed subclass.
  Above the line (new code): read client + rolling buffer.
  Below the line (frozen, unchanged): the instant a MarketSnapshot exists,
  the existing strategy -> regime -> risk -> assemble -> emit chain runs
  untouched.
- PINNED: close = _Quote.mid.
  mid = (bid + ask) / 2 where both are present, else quote (fallback in
  _Quote itself). Closes within one buffer may therefore be HETEROGENEOUS.
  Accepted for placeholder plumbing validation. Revisit at Phase 42.1.
- Warmup: in-memory rolling buffer, maxlen >= 20 (implementation uses 25
  for headroom, matching the golden snapshot depth).
    buffer < 20  -> emit nothing (matches ReferenceMA returning None
                    below slow=20; silence is correct, not a fault)
    buffer >= 20 -> ReferenceMA may evaluate
  No synthetic padding. No backfilling. No fabricated candles.

## Boundary 2 -- CP3 (narrowed safety rule)

The blanket "no broker imports" rule is narrowed FOR THE FEED ONLY.

ALLOW (read-data):
  - infrastructure.broker.deriv.rest_shadow_adapter
  - infrastructure.broker.deriv.rest_transport

DENY (execution-capable siblings; scan must fail on any of these):
  - infrastructure.broker.deriv.deriv_adapter
  - infrastructure.broker.demo_broker_adapter
  - infrastructure.broker.mock_broker
  - infrastructure.broker.transport
  - any order / proposal / buy / sell / position / account-mutation surface

The static check fails on execution CAPABILITY, not on legitimate data
access.

NAMED EXPOSURE CHANGE: versus 42.0C, execution surface stays 0; the
network-read + auth surface goes 0 -> 1. This is a deliberate new
permission, not a no-op.

Inherited guards (defense in depth, all pre-existing and unmodified):
  1. Adapter raises ShadowViolation on 7 execution method names.
  2. Transport raises ExecutionForbiddenError on the same names.
  3. Connect refuses any non-virtual account (is_virtual != 1 -> refuse).

## Boundary 3 -- Session handling

- One explicit observation session per run: py -m engine.runner --mode live
- Session ID generated once per run.
- Output: per-session file, e.g.
    engine/output/live_signals_<date>_session<NNN>.jsonl
  Append-only within a session. A restart rotates to a NEW file.
  Sessions never silently mix.
- Bounded by at least one of: max duration, max signal count, manual stop.
  First run: manual stop OR 50 signals, whichever comes first.

## Boundary 4 -- Validation gates

- CP1: engine imports clean.
- CP2: live feed imports and starts; first read returns a parseable quote.
- CP3: static safety per Boundary 2 (allow-list only; deny-list absent).
- CP4: bridge check on the session file:
    Signals received >= 1, Schema valid = all, Rejected = 0,
    Live orders sent = 0.
- CP5: session integrity:
    timestamps strictly increasing; JSONL valid; one session ID per file;
    engine transform DETERMINISTIC given identical buffer input.
    Live closes are EXPECTED to differ across sessions -- byte-identical
    live output is NOT asserted. (The 42.0C byte-determinism test is
    snapshot-path only and remains untouched.)
- 42.0C regression net still green after all Phase 43 work:
    py -m engine.validation.test_m0_regression -> PASS (3/3)

## Hard reminders

- Live orders sent must stay 0. Execution surface must stay 0.
- Never claim DEMO READY or SHADOW PASS.
- The running code is the source of truth, not this document.