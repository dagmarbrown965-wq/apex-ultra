# PHASE 49 BOUNDARY AGREEMENT — v1.0 DRAFT

**STATUS: DRAFT. NOT RATIFIED. NOT AUTHORITATIVE.**

*Becomes authoritative only when committed to `docs/` on `main`, per the Phase
48 v1.0 convention. Until then no dataset may be opened, no statistic computed,
and no implementation begun.*

*Sections A and C drafted 2026-11-16. Sections B, D, E and F are outstanding;
this document is incomplete by design and must not be ratified in this state.*

**Versioning convention, stated explicitly because conventions differ across
phases in this project and a tool now checks them:** this agreement is **v1.0**,
and amendments form a separate **v0.1, v0.2, …** series, following Phase 48.
Phases 44–46 instead numbered versions *of the agreement*, so their boundary
agreement files occupy the low numbers. See `tools/check_record_integrity.py`.

---

# SECTION A — PURPOSE

## What this phase is

Phase 49 **forms and pre-registers a hypothesis.** Its deliverable is a
document, not a verdict.

It produces no evaluation of any strategy, consumes no holdout, and issues no
finding about market behaviour. If Phase 49 ends with a pre-registered
hypothesis and nothing else, it has succeeded.

## What this phase is not

**Phase 49 does not spend D2.** The decision to consume the holdout, and the
single evaluation itself, belong to **Phase 50** under its own agreement.

This separation is deliberate and is the structural choice this phase rests on.
D2 is single-use and cannot be rebuilt without another acquisition phase and
another ninety days of waiting. A phase that both develops a hypothesis and
evaluates it decides whether to spend the holdout at the worst possible moment —
after weeks of investment in the hypothesis, by the people most committed to it.
Phase 50 asks that question cold.

Phase 49 is also **not** a search for a strategy in the data. See the
interpretive resolution below.

## Interpretive resolution — the D1 seal conflict

**Two clauses inherited from Phase 48 conflict, and Phase 49 is the first phase
where the conflict bites. It is recorded here rather than resolved silently.**

`docs/PHASE_48_BOUNDARY_AGREEMENT.md` Section E states:

> The sealed data files are not opened after acquisition until a hypothesis is
> pre-registered. Only the summaries are readable.

The same document's Section B describes D1 as:

> Body available immediately; in-sample material for a future phase

Read together these are ambiguous for any phase that must both form a
hypothesis and use D1. One clause seals D1 until a hypothesis exists; the other
describes it as immediately available material.

**RATIFIED INTERPRETATION — binding on Phase 49:**

1. **Both D1 and D2 remain sealed against exploratory examination.** The Phase
   48 forbidden-statistics list applies to both: return autocorrelation at any
   lag, volatility clustering measures, ATR or any indicator series,
   compression-episode or signal counts, drawdown or trend statistics, plotting
   the price series, and any backtest, exploratory or otherwise.
2. **D1's designation as in-sample material does not authorise hypothesis
   discovery.**
3. **Hypotheses must originate independently of both sealed datasets.**
4. **Permitted origins** are market-structure reasoning, published academic or
   empirical research, and previously established procedural knowledge from this
   project. Section C governs.
5. **D1 becomes available for implementation and development only after the
   hypothesis and its testing protocol have been formally pre-registered.**
6. **D2 remains reserved for a single independent evaluation** under its
   existing restrictions, in Phase 50.

**The reasoning.** There is a distinction between *hypothesis generation* —
deciding what might constitute a genuine edge — and *hypothesis testing* —
determining whether that edge exists in the data. If D1 is examined to discover
which strategy looks promising, it has already influenced the hypothesis.
Calling the subsequent work in-sample development does not undo that influence.
D2 would then be testing a hypothesis that D1 had already chosen, and the
holdout would be measuring something other than what it appears to measure.

Protecting D2's independence is one of the central purposes of Phase 48.
Between two readings of its own text, the one that preserves that purpose
governs.

**What this resolution does not do.** It does **not** amend Phase 48, which is
closed. It does not assert that Phase 48's wording was clear, or that the
conflict was foreseen. The wording was ambiguous; this is Phase 49's reading of
an inherited document, recorded so that a later reader can see that the conflict
existed, which interpretation was chosen, and why. The precedent is Phase 48's
own treatment of the Phase 47 legitimacy test, which was resolved the same way
and for the same reason.

**Acknowledged cost.** This reading is the more restrictive one. It forecloses
the most natural way to find a strategy — looking at a year of data and noticing
something — and it accepts that the phase may end with no viable hypothesis at
all. That outcome is permitted and is not a failure of the phase. The priority
is preserving the independence of the evidence, even where that means finding
nothing.

## Relationship to the Phase 47 legitimacy test

`docs/PHASE_47_CLOSE.md` binds successor phases:

> does the proposal originate in a REASON stated independently of this result,
> or in the RESULT itself?

**Phase 48 satisfied this test by construction**, proposing no hypothesis at
all. **Phase 49 cannot.** It proposes a hypothesis, so it must argue the test
explicitly rather than cite a close document as authorisation — a requirement
Phase 47's close states directly for the direction closest to the line.

Section C carries that burden. Every candidate hypothesis states its origin in
writing and defends it against this test before it is admissible.

## What Phase 49 does not establish

Nothing about market behaviour. No result of Phase 49 can support, weaken, or
bear on any hypothesis, including the one it pre-registers. A pre-registration
is a statement of intent and a commitment to criteria; it is not evidence.

---

# SECTION C — LEGITIMATE HYPOTHESIS ORIGINS

*Section B (holdout protocol and dataset handling) is outstanding. Section C is
drafted first because it is the section that must exist before anyone thinks
about a hypothesis, and because its content is independent of B.*

## Permitted origins — exhaustive

A hypothesis admitted to Phase 49 originates in exactly one of:

1. **Market-structure reasoning.** An argument from how the market or the
   instrument mechanically works — session boundaries, liquidity provision,
   participant behaviour, settlement or rollover mechanics, the five-day trading
   week. The argument must be statable without reference to any price series
   this project holds.
2. **Published academic or empirical research.** Cited specifically, with the
   claim it makes and the conditions under which it was established. A citation
   is not a licence: the hypothesis must argue why the published effect should
   transfer to `frxGBPJPY` at 15-minute granularity.
3. **Previously established procedural knowledge from this project.** Permitted
   by Phase 48's interpretive resolution, which distinguishes acting on
   procedural knowledge — such as knowing a holdout is spent, or that a
   measurement apparatus is defective — from selecting *content* to route around
   a negative outcome.

**Anything else is inadmissible.** In particular, a hypothesis is inadmissible
if it was chosen because it resembles what examined data appeared to favour,
whether that data is D1, D2, a prior phase's dataset, or a chart seen elsewhere.

## Inadmissible, stated explicitly

- Any hypothesis discovered by examining D1 or D2, in whole or in part.
- Any re-tuning of a previously rejected hypothesis. **EmaCross stays 9/21.**
  Changing parameters on a failed strategy is not a new hypothesis; it is the
  same hypothesis with the failure sanded off.
- Any hypothesis selected because prior phases failed, where the selection
  reasoning is "the previous thing didn't work, so try the adjacent thing."
  That originates in the result, not in a reason independent of it.
- Any hypothesis whose stated origin cannot be written down before the data is
  touched.

## Required hypothesis statement — all seven elements

A hypothesis is admissible only with a written statement containing **every**
element below. An incomplete statement is not admissible, and the omission is
recorded rather than waived.

1. **Origin.** Which permitted category, and specifically what — the mechanism,
   the citation, or the procedural fact.
2. **Theoretical reasoning.** Why this should be true, argued from the origin.
3. **Why it should have predictive value.** Distinct from (2): a mechanism can
   be real and still carry no forecastable signal. This element argues that the
   effect is exploitable in advance, not merely visible afterwards.
4. **Why it is distinct from previously rejected hypotheses.** Phases 45 and 46
   rejected crossover signals on two instruments; Phase 47 rejected a
   volatility-compression breakout out of sample. Distinctness is argued on
   mechanism, not on parameters or instrument.
5. **Proposed primary configuration.** The specific rule, stated precisely
   enough that two implementers would produce the same signals.
6. **Falsification criteria.** What result would establish that the hypothesis
   is wrong — stated before any data is seen, and stated as something that can
   actually occur.
7. **Expected trade density.** *(Advisor addition — accept or strike.)* An
   estimate, with its basis, of how many trades the configuration should produce
   over D2's 88.708 forward days. Phase 48 Section F criterion 5 and the n ≥ 50
   evaluable tier both depend on this, and an estimate made after seeing the
   holdout is worthless. A hypothesis that cannot estimate its own trade density
   in advance is not specified precisely enough to test.

## Admissibility review

The hypothesis statement is reviewed against this section **before** any
pre-registration is written and **before** D1 is opened for implementation.

The reviewer's question is not "is this likely to work." It is: **would this
statement have been written in exactly this form if the data did not exist?**

A hypothesis that fails review is recorded with the reason, in the same manner
Phase 48 recorded every screened instrument including the rejections. A phase
that admits only its eventual winner has a defective record.

## No-survivors rule

**If no hypothesis survives Section C, Phase 49 closes with that finding.** It
does not proceed by relaxing an origin category, by admitting a hypothesis with
an incomplete statement, or by reclassifying a data-derived idea as
market-structure reasoning.

Closing with "no admissible hypothesis was found" is a legitimate and complete
outcome. D2 remains unspent and available to a later phase that has one.

---

# OUTSTANDING — not yet drafted

- **Section B** — holdout protocol, dataset handling, the `epoch <= 1787193000`
  exclusion, the clipped first bar of each dataset, commit-before-read, hash
  citation, and the D1/D2 firewall during Phase 49.
- **Section D** — in-sample discipline on D1 once pre-registration is complete:
  what fitting is permitted, what is forbidden, and how parameter bounds are
  declared in advance.
- **Section E** — acceptance criteria, sample sufficiency, the n ≥ 50 evaluable
  tier, and the pass bar. Fixed before Phase 50 opens.
- **Section F** — forbidden responses to a result, carried from Phase 46.
- **Section G** — operational preconditions and work items.

**This agreement must not be ratified until B, D, E and F exist.**
