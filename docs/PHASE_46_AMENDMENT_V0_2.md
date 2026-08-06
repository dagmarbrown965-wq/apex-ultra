# PHASE 46 BOUNDARY AGREEMENT — AMENDMENT v0.2

_Amends the locked v0.1 (docs/PHASE_46_BOUNDARY_AGREEMENT.md, commit
ecbf230). Where this amendment and v0.1 conflict, this amendment governs.
The pass bar (38%), break-even (35.0%), bracket (0.2%/0.4%), cost model
(0.01%), position policies, and the entire forbidden-response list stand
UNCHANGED._

## IMPORTANT: this amendment was made AFTER seeing a result

This must be stated first and plainly, because it is the pattern this
project's discipline exists to guard against.

The W46.2 resolution run completed before this amendment was drafted. Its
result is recorded here permanently so that any change produced by the
amendment is visible and auditable:

**PRE-AMENDMENT RESULT (block-bounded resolution, commit db5e23f data):**
- Signals examined: 1,323
- Resolved: 1,087 · Wins: 351 · Losses: 736
- **Win rate (pre-cost): 32.29%**
- Unresolved: 236 (**17.84%**) — exceeded the 10% compromise threshold
- Same-bar ambiguous: 0
- Median resolution: 45 bars (11.25h); mean 62.6 bars (15.7h)

If the post-amendment win rate differs materially from 32.29%, that
difference is itself a finding requiring scrutiny, not a result to
celebrate. A methodological change that conveniently lifts a number above
a threshold should be treated as suspect by default.

## Why the amendment is nonetheless justified

The trigger was NOT the win rate. It was the **17.84% unresolved
fraction**, which v0.1 itself defines as a compromised sample. The phase
could not be closed honestly either way without addressing it.

The cause is structural and was not anticipated when v0.1 was written:

- v0.1 required resolution never to cross a contiguous-block boundary.
  Blocks are trading weeks (~480 bars), split by weekend closures.
- Observed median resolution is 45 bars (11.25h), mean 62.6 bars (15.7h)
  — longer than the ~8h estimated from a random-walk model, because real
  prices spend substantial time ranging.
- Any signal firing in roughly the last 60 bars of a trading week
  therefore cannot resolve before Friday close and is truncated.
  ~60/480 ≈ 12.5% of signal opportunities, plus the slow tail, accounts
  for the observed 17.84%.

**The block-boundary rule was inherited from Phase 45, where blocks were
data-collection gaps in a 24/7 synthetic instrument. It does not describe
reality for a market that closes.** A real position held on Friday
afternoon does not vanish at the weekend; it reopens Monday. Refusing to
resolve across a weekend models something that does not happen.

This is a correction to a methodological flaw, not a response to an
unwelcome number. The distinction is that the unresolved fraction was
independently defined as disqualifying in v0.1, before any data existed.

## Amendment 1 — resolution crosses weekend closures

Resolution walks forward through the ENTIRE chronological series, not
only within the signal's own contiguous block. Weekend gaps are traversed.

Signals still resolve as UNRESOLVED when the series itself ends before a
barrier is touched — expected to be a small number of signals near the
end of the 365-day dataset. The >10% compromise threshold still applies
to that residual.

## Amendment 2 — weekend gap-through handling

A weekend gap can open beyond a barrier: Monday's first bar may already
be past Friday's stop or target.

- Such a signal RESOLVES at that bar, in the barrier's direction
  (gapped past target = WIN; gapped past stop = LOSS).
- The outcome is recorded at the BARRIER price, not the gap price, so
  W46.3's arithmetic stays fixed at +0.4%/−0.2% gross per trade.
- **Gap-through cases are counted and reported separately.**

Disclosed limitation: in reality a stop gapped through fills worse than
−0.2% and a target gapped through fills better than +0.4%. These effects
partially offset but are not symmetric, and gaps against a position are
the more common retail experience. If the gap-through count is material
(>2% of resolved signals), the phase close must state that measured
expectancy is optimistic relative to real fills.

## Amendment 3 — same-bar ambiguity rule unchanged

Where a single bar's range spans both barriers, the outcome remains
LOSS (pessimistic; intra-bar path unknowable). The pre-amendment run
produced ZERO such cases; the count continues to be reported.

## What does NOT change

- Pass bar: win rate ≥ 38% under the PRIMARY policy.
- Break-even: 35.0% after the 0.01% round-trip spread.
- Bracket: 0.2% stop / 0.4% target, unchanged.
- Minimum sample: ≥1,000 resolved signals, ≥150 independent windows.
- EmaCross 9/21, unchanged. No re-tuning, no timeframe change, no symbol
  change, no post-hoc filtering — the full v0.1 forbidden list stands.
- Per-block fresh strategy state in W46.1 (signal GENERATION) is
  unchanged. This amendment concerns RESOLUTION only. A strategy should
  not carry EMA state across a market closure; a position should.

## Decision log

- 2026-08-05: W46.2 run returned 17.84% unresolved, exceeding the 10%
  threshold set in v0.1. Advisor identified the cause as the inherited
  block-boundary resolution rule truncating trades at weekend closures —
  a rule appropriate to Phase 45's 24/7 synthetic instrument but not to a
  market that closes. CEO chose cross-weekend resolution (option B of two
  presented; option A was accept-and-disclose). Pre-amendment result
  recorded above in full. Gap-through handling specified conservatively
  (barrier-price resolution, separate counting, disclosure requirement).
