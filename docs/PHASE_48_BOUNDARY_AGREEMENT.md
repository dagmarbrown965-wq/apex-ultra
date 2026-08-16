# PHASE 48 BOUNDARY AGREEMENT (v1.0 — LOCKED 2026-08-16)

*Status: authoritative once committed to `docs/` on `main`. Level 2 document
under the AI Company Constitution v1.1. This is a PRE-REGISTRATION document:
every value in Sections C, D, E and F was fixed before any candidate instrument
was screened and before any data was fetched. The filesystem is the source of
truth.*

*Assessed against `docs/PHASE_47_CLOSE.md` and
`docs/PHASE_47_BOUNDARY_AGREEMENT.md` (v1.0, commit `121f285`).*

---

# SECTION A — PURPOSE

## What this phase is

Phase 48 acquires and seals two datasets. It forms no hypothesis, tests no
strategy, and issues no verdict about any market behaviour.

Phases 45, 46 and 47 tested three strategies to pre-registered standards and
none demonstrated an edge. The ceiling check that followed (`a1ff0cf`) recorded
the dataset as contaminated for holdout purposes, and Phase 47's holdout is
separately and explicitly spent by design.

The project's single most load-bearing mechanism — the pre-registered,
single-use holdout — therefore has no clean data to operate on. Phase 47
demonstrated what that mechanism is worth: it caught a strategy returning
+37.66R at PF 1.15 in-sample that a researcher without a holdout would have
deployed. Restoring the capability is a prerequisite to further strategy work,
not a preliminary to it.

## What this phase is not

Phase 48 is not a successor to Phase 47 and must not be framed as fixing it. No
result of Phase 48 can support, weaken, or bear on the volatility-compression
hypothesis or any other.

## Relationship to the Phase 47 legitimacy test

`PHASE_47_CLOSE.md` binds successor phases: *"does the proposal originate in a
REASON stated independently of this result, or in the RESULT itself?"*

**Interpretive resolution — ratified 2026-08-16, binding going forward.** The
test prohibits proposals whose *content* is selected to route around a negative
outcome: altered parameters, changed instruments, post-hoc filters, or a
hypothesis chosen because already-seen data suggests it would pass. It does not
prohibit acting on *procedural* knowledge gained from a result, such as knowing
that a holdout has been spent.

This resolution is necessary because the close document's own three suggested
directions were written in light of the Phase 47 result, and the
intrabar-stop-execution direction originates specifically in the disclosed
finding that 215 of 394 trades (54.6%) exited worse than −1.05R. Under a
literal reading of the test, that direction is forbidden. Under this resolution
it is permitted as a measurement-apparatus question — but it is the example
closest to the line, and **any phase proposing it must argue the point
explicitly rather than cite the close document as authorisation.**

**Phase 48 satisfies the test by construction.** It proposes no hypothesis, so
there is nothing for a result to have originated in.

## The contamination this phase does and does not cure

Curable: hypotheses fitted, knowingly or not, to data already examined.
Section E addresses this directly.

Not curable, and not a defect: the researcher has read Phases 45–47 and will
form future hypotheses as someone who knows crossover signals failed on two
instruments and a compression breakout failed out of sample. That is learning,
not leakage. The distinction is whether the *test data* informed the
hypothesis, not whether *any prior experience* did.

---

# SECTION B — ACQUISITION ROUTE

**Both, in sequence.** Two datasets on a single instrument:

| | Dataset | Content | Role |
|---|---|---|---|
| **D1** | Historical | Full 365-day 15m candle history, fetched at phase start | Body available immediately; in-sample material for a future phase |
| **D2** | Forward | D1's end forward to the D2 fetch date | Temporally clean holdout — did not exist when any future hypothesis is written |

**Same instrument, mandatory.** D2 serves as a holdout for a hypothesis formed
on D1 only if it is the same series continued forward. A different instrument
would constitute a generalization test — a weaker and different claim.

## Why forward collection is cheap here

Deriv serves a hard 365-day candle history (measured at 364.996 days in W47.1).
Phase 45's daily collection discipline was forced by the **24-hour tick
limit**: a missed day was lost permanently. That constraint does not apply to
candles — any 15m bar remains retrievable for a year after it prints.

**D2 therefore requires one deferred fetch, not a daily routine.** No collection
incident log, no daily failure mode, no overlap-and-gap reconciliation of the
kind Phase 45 needed across thirteen commits.

This holds only for candles. Any future phase requiring tick granularity
reverts to daily forward collection and must budget accordingly.

## Schedule

| Event | Date | Note |
|---|---|---|
| D1 fetch | On lock | Immediate; unaffected by token expiry |
| **D2 interval** | **75 days** | Ratified 2026-08-16 |
| D2 fetch | ~2026-10-30 | Requires a valid token on that date |

**Justification of the 75-day interval.** Phase 47 produced 106 holdout trades
from ~91 days of BTC 15m data. At comparable trade density, 75 days yields
roughly 85–90 trades — comfortably above the n ≥ 50 evaluable tier of the Phase
47 sample-validity rule, with margin for a less trade-dense hypothesis. Trade
density under a future hypothesis is unknown; Section F criterion 5 is the
backstop, and a D2 that fails it is rejected rather than stretched.

The alternative of a 90-day interval was considered and rejected on token
arithmetic: Deriv caps token lifetime at 90 days, so a token renewed on the
lock date expires ~2026-11-14, and a 90-day interval would land the D2 fetch
with effectively zero margin. 75 days leaves roughly two weeks.

---

# SECTION C — INSTRUMENT SELECTION CRITERIA

**The instrument is determined by rule, not by name.** This agreement
pre-registers the selection criteria; the instrument is whatever survives them
in the W48.0 screening pass. Naming an instrument here would reintroduce
researcher discretion at exactly the point this phase exists to remove it.

All criteria must hold:

1. **Not previously used.** Not `frxEURUSD`, `cryBTCUSD`, or `R_100`.
2. **Independence gate.** Bar-to-bar return correlation against each
   previously-used instrument below the Section F ceiling, on matched
   timestamps.
3. **Provenance gate.** Validated against an independent public reference in
   the manner of W47.0 (Deriv `cryBTCUSD` vs Binance BTCUSDT, r = 0.9979).
   **Excludes all synthetic indices**, which have no external referent — and
   Phase 45 established that `R_100` fails structurally as a random number
   generator.
4. **Sufficient history.** Full 365-day window available and
   substitution-defence-verified.
5. **Sample sufficiency.** Bar count large enough that a future phase can
   pre-register a holdout meeting the n ≥ 50 evaluable tier under a range of
   candidate hypotheses. ~35,000 bars on a 24/7 market at 15m; ~24,250 on a
   five-day market.
6. **Collection viability.** The instrument must be one the project is prepared
   to still be collecting on 2026-10-30.

**The provenance gate runs first**, per the W47.0 precedent — a CEO instruction
in Phase 47 that the close document credits as correct, since failure there
ends the phase in twenty minutes rather than after a full fetch.

**Screening pass (W48.0).** Both gates run on ~500 matched bars and are cheap.
Candidate instruments are screened against both *before* any full fetch is
committed to. **Every instrument screened is recorded with its correlations and
outcome, including rejections.** Which instruments failed and why is part of the
record; a screening log showing only the winner is a defect.

**If no candidate survives**, the phase does not proceed by relaxing a
threshold. It closes with the finding that no independent instrument is
available on this platform under these criteria, and any subsequent relaxation
requires a new agreement stating the new threshold and the reason, in advance.

---

# SECTION D — ACQUISITION FREEZE

Exhaustive. Anything not stated is a defect in this agreement, to be resolved
by amendment before fetching, never by implementer discretion.

1. Reuse `tools/fetch_candles.py` **verbatim**; it is already parameterised by
   symbol with `frxEURUSD` preserved as default, verified in W47.1. A modified
   fetcher would require its own verification and is out of scope.
2. Every fetched batch has returned epochs verified against the requested
   range. Substituted batches are discarded and the boundary recorded. The
   substitution defence fired at request 37 on both prior fetches; **a fetch in
   which it does not fire at all is anomalous and must be reported**, not
   assumed benign.
3. All gaps reported with duration and timestamp. Never smoothed, interpolated,
   or filled. For a 24/7 instrument any gap is an anomaly; for a five-day
   instrument, weekend gaps are expected and intra-session gaps are not.
4. SHA-256 of each completed data file computed and recorded in its summary at
   acquisition time, before any analysis exists.
5. D2's fetch requests the interval from D1's last epoch forward. Any overlap is
   recorded, not trimmed. Contiguity between D1 and D2 is asserted in D2's
   summary and is a Section F acceptance criterion.
6. Bulk `.jsonl` output is already covered by existing `.gitignore` patterns
   (`candles_*.jsonl`); summaries remain committed per `46a2c12`. **Verify the
   pattern matches the chosen symbol's filenames before the first commit.**
7. Commits in this phase use explicit paths, never `git add -A`. Seven rejected
   Phase 44 session journals are deliberately untracked in `engine/output/`;
   sweeping them in would silently reverse a validity decision recorded by the
   Phase 44 window close.

---

# SECTION E — QUARANTINE PROTOCOL

The substance of the phase. Data that has been examined is not clean, so
acquisition must be separated from inspection by rule rather than intention.

## Permitted at acquisition (structural allowlist — exhaustive)

- Bar count; first and last epoch; total span in days
- Gap inventory: count, duration, timestamp of each
- Provenance correlation and return standard deviation against the external
  reference, on matched timestamps, limited to the gate sample (W47.0 used 500
  bars)
- Independence correlation against previously-used instruments, same sample
  bound
- Substitution-defence trigger point
- File SHA-256 and byte size
- D1/D2 contiguity check: last epoch of D1 against first epoch of D2

## Forbidden until a hypothesis is pre-registered

Everything else. Explicitly including, and not limited to: return
autocorrelation at any lag; volatility clustering measures; ATR or any indicator
series; compression-episode or signal counts; drawdown or trend statistics;
plotting the price series; and any backtest, exploratory or otherwise.

## Rationale

The allowlist admits only statistics answering *"is this dataset structurally
sound and does it reflect a real market?"* It excludes every statistic that
could inform *"what strategy might work here?"* A researcher who has seen the
second class can no longer honestly claim a later hypothesis was formed
independently of the data.

## Seal enforcement — enforced unread

The sealed data files are not opened after acquisition until a hypothesis is
pre-registered. Only the summaries are readable.

**Mechanism.** Technical enforcement is not available on a single-operator
machine, so enforcement is by audit trail:

1. Any script that reads a sealed data file **must be committed to `main`
   before it is executed.** Git history is therefore the complete log of
   everything that has ever touched the data.
2. Each sealed summary records the SHA-256, the acquisition date, and the commit
   at which the seal was established.
3. A future phase pre-registering against a sealed dataset cites that hash and
   states the commit range within which no reading script was committed.

An unlogged read leaves no trace; this mechanism cannot make cheating
impossible. It makes cheating require a deliberate, documented act of omission
rather than a moment of curiosity — the same standard the single-use holdout
already operates under.

**If a hash cannot be reproduced, that dataset's provenance is void and it may
not serve as a holdout.**

---

# SECTION F — ACCEPTANCE AND REJECTION CRITERIA

Phase 48 produces no verdict about market behaviour. Its verdict is on the
datasets, evaluated strictly in order. Thresholds ratified 2026-08-16.

| # | Criterion | Requirement |
|---|---|---|
| 1 | Provenance | Return correlation vs external reference **≥ 0.95**, n ≥ 500 matched bars |
| 2 | Independence | \|Return correlation\| vs each previously-used instrument **< 0.30**, n ≥ 500 matched bars |
| 3 | Completeness | Bar count **≥ 97%** of arithmetic expectation for the span; no single gap > 6h on a 24/7 instrument |
| 4 | Integrity | Substitution defence fired and boundary measured; all gaps inventoried |
| 5 | Sufficiency | Bar count supports a future n ≥ 50 holdout per C.5 |
| 6 | Contiguity (D2 only) | D2's first epoch continues D1's last; any overlap recorded, no gap unexplained |
| 7 | Seal | SHA-256 recorded; reading-script commit trail clean; no forbidden statistic computed |

## Justification of thresholds

**Provenance ≥ 0.95.** W47.0 achieved 0.9979, but that reflects Deriv mirroring
a large liquid spot market with an easily matched reference. A less liquid
instrument, or one referenced against a venue with timing offsets, can be
genuinely real and score lower. 0.95 leaves room for venue differences while
rejecting synthetic construction decisively — `R_100` would score near zero
against any external referent.

**Independence < 0.30.** r = 0.30 is r² = 0.09, under a tenth of variance
shared. Above that, a material fraction of the new series' movement is movement
already studied. **Known consequence: this ceiling is strict and will likely
exclude most liquid FX crosses** (dollar-factor correlation to EUR/USD) **and
the major crypto pairs** (BTC beta). The candidate set may sit in a different
asset class entirely. That is the intended effect, and the W48.0 screening pass
makes discovering it cheap. The Section C no-survivors rule governs if it
excludes everything.

**Completeness ≥ 97%.** W47.1 observed five sub-hour gaps totalling 0.07% of the
series. A 3% tolerance is generous against observed behaviour while still
rejecting a materially broken series. The 6-hour single-gap rule catches a
sustained outage that a percentage threshold could absorb unnoticed.

**No later criterion may rescue an earlier failure.** Carried forward from Phase
47 Section F. Failure at criterion 1 or 2 means the instrument was wrongly
chosen and selection returns to Section C, with the rejection recorded.

---

# SECTION G — OPERATIONAL PRECONDITIONS

1. **Token renewal — blocking for D2, not for D1.** `apex_trade_demo_2` expires
   ~2026-10-08; the D2 fetch is scheduled ~2026-10-30. A renewed token must be
   in place before that date. Deriv caps token lifetime at 90 days, so a
   renewal on or after ~2026-08-16 covers the D2 fetch with roughly two weeks
   of margin. **Calendar it — the documented failure mode is silence, not an
   error.**
2. **Repository location.** Currently under `Downloads`. Move before this phase
   generates new primary evidence.
3. **Stale-artifact hygiene.** Delete
   `Downloads\trading bot\files (80)\ema_cross.py`. Standing rule since the
   session002 incident.
4. **CP4 trap.** `engine/output/live_signals.jsonl` is a 253-byte stub from
   2026-06-30 and is the path the M0 regression output suggests handing to CP4.
   Running that command verbatim reports PASS on nothing. Fix or delete.

## Verification status at lock

All gates confirmed green at commit `0e1b441` on 2026-08-16:

| Gate | Result |
|---|---|
| M0 engine regression | PASS (3/3) |
| CP3 static import gate | PASS — single allowlist entry, unchanged |
| CP4 signal bridge | PASS — 73/73 accepted, 0 rejected, **live orders sent: 0** |
| CP5 session integrity | PASS |
| `_last_sign` content probe | HIT — genuine 42.1a code |

---

# SECTION H — WORK ITEMS

| ID | Work | Gate |
|---|---|---|
| W48.0 | Candidate screening pass: provenance then independence, ~500 matched bars each, all candidates logged including rejections | Section C |
| W48.1 | D1 fetch, full 365-day history on the surviving instrument | Section D, F 1–5 |
| W48.2 | D1 seal: SHA-256, summary, seal commit | Section E |
| W48.3 | Token renewal, calendared before 2026-10-08 | Section G.1 |
| W48.4 | D2 fetch ~2026-10-30 | Section D, F 6 |
| W48.5 | D2 seal and phase close assessment | Section E, F 7 |

**Nothing in this phase produces or evaluates a trading signal.** Any work item
that appears to require one is a defect in this agreement.

---

## Carried forward to a future phase

Observation recorded 2026-08-16, outside Phase 48's scope and not acted on here:
signal density in the Phase 44 window varied by roughly two orders of magnitude
between sessions — from 1 signal in `live_signals_2026-07-11_session001` to 73
in `live_signals_2026-07-24_session002` over a ~35-minute span. Phase 44 was
correctly scoped to structural integrity and did not measure signal statistics.
Any future hypothesis assuming a stable signal rate should establish that
assumption rather than inherit it.

---

## Decision log

* 2026-08-16 — Session opened for Phase 44 definition per stale instructions;
  filesystem verification established that Phase 44 closed PASS on 2026-07-24
  and Phases 45, 46, 47 have since closed FAIL. State reconciled and recorded
  in `APEX_STATE_2026-08-16.md`. All four gates re-verified green at `0e1b441`;
  frozen code confirmed unchanged across three phases apart from the Phase
  44-authorised `runner.py` modification (`e27d099`).
* 2026-08-16 — Acquisition-first direction selected by CEO over
  reasoning-first-on-contaminated-data and consolidate-and-stop. Advisor
  drafted v0.1 with five open decisions. CEO selected both-in-sequence
  acquisition and enforced-unread sealing. Advisor's v0.2 added the
  same-instrument requirement for D2, established that candle forward
  collection requires one deferred fetch rather than Phase 45's daily
  discipline (the 24h limit binds ticks, not candles), specified the
  commit-before-read audit mechanism, and proposed three acceptance thresholds
  with justification. CEO ratified the thresholds, the interpretive resolution
  of the Phase 47 legitimacy test, and the instrument-by-rule construction.
  Advisor set the D2 interval at 75 days on token arithmetic, recorded above.
  All values locked before any candidate was screened.
