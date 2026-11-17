# PHASE 49 BOUNDARY AGREEMENT — v1.0 DRAFT

**STATUS: DRAFT. NOT RATIFIED. NOT AUTHORITATIVE.**

*Becomes authoritative only when committed to `docs/` on `main`, per the Phase
48 v1.0 convention. Until then no dataset may be opened, no statistic computed,
and no implementation begun.*

*Sections A and C drafted 2026-11-16; Sections B, D, E, F and G drafted
2026-11-17. **All sections are now present.** One item remains before
ratification: the Phase 46 forbidden-response list must be read and merged into
Section F.*

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

# SECTION B — DATASETS AND THE HOLDOUT PROTOCOL

Carried forward from the Phase 48 seals and Amendment v0.11. Nothing here is
new policy; it is collected so that Phase 49 and Phase 50 operate from one
statement rather than three documents.

## The two datasets

| | D1 | D2 |
|---|---|---|
| Role | In-sample | **Single-use holdout** |
| File | `engine/output/candles_frxGBPJPY_900_1755657580_1787193000.jsonl` | `engine/output/candles_frxGBPJPY_900_1786039197_1794857400.jsonl` |
| Bars | 24,257 | 6,748 |
| Span | 364.993 d | 102.063 d |
| SHA-256 | `E9DF6A4E2CDBBAAC8C9B738314E288E2AB006075768B9F0FA8904A521DEFEE39` | `99A22CFC24061C00591B0E8C63E1F99B8B5DDBBEBDAC7B8C1D588FA66952E49E` |
| Seal | `docs/PHASE_48_D1_SEAL.md`, `1a7848e` | `docs/PHASE_48_D2_SEAL.md`, `f7a69cf` |

Both are gitignored, so **git is not a backup of them.** Verified copies at
`%USERPROFILE%\OneDrive\Documentos\APEX_SEALED_DATA\`.

**If a hash cannot be reproduced, that dataset's provenance is void and it may
not serve as a holdout.** Verify both before relying on either.

## Mandatory exclusions

1. **D2: exclude every bar with `epoch <= 1787193000`.** Amendment v0.11 Clause
   5. D2 overlaps D1 by 13.354 days because the fetch tool walks backward from
   `latest` and overshoots by up to one request window. Without this exclusion
   the overlap silently reintroduces sealed in-sample material into the holdout.
2. **Exclude the first bar of each dataset.** Both are clipped off the
   900-second boundary — D1 by 320 s, D2 by 897 s — systematic across all four
   project fetches.

**Effective evaluable bars in D2 are therefore fewer than 6,748.** The exact
figure requires counting bars above the exclusion epoch, which requires opening
the file and therefore a committed script; it is determined and reported at
evaluation time in Phase 50. Arithmetic over published summary figures puts the
estimate near **5,860 bars over 88.708 forward days**. Sufficiency rests on
trade density, not bar count — see Section E.

## The D1/D2 firewall during Phase 49

**Phase 49 does not open D2 at all.** Not to count bars, not to check the
exclusion, not to confirm the hash beyond the file-level SHA-256 already
recorded. Only `docs/PHASE_48_D2_SEAL.md` and the committed summary are
readable.

**Phase 49 does not open D1 until the pre-registration is committed to `main`.**
Section A's interpretive resolution governs; Section D sets what happens after.

## What "spent" means

**D2 is evaluated once.** One hypothesis, one frozen configuration, one run, in
Phase 50. After that evaluation D2 is spent — **whatever the outcome.** A pass
does not earn a second look and a failure does not earn a retry.

**A run that produces any evaluable output is a use**, even if the
implementation is afterwards found defective. This is deliberate and is the
clause most likely to be resented later: without it, "the script had a bug, let
us fix it and re-run" becomes an unlimited number of attempts at the holdout,
each one looking principled.

**A run that fails before producing any statistic is not a use** — a crash, an
authentication failure, an empty read. The distinction is whether a number
about D2 was produced and seen, not whether anyone intended to see it.

If a defect is found after a use, the finding stands as recorded and the defect
is disclosed alongside it. D2 does not reset.

## Audit trail — enforced unread

1. **Any script that reads either sealed file must be committed to `main`
   before it is executed.** Git history is the complete log of everything that
   has touched the data.
2. The pre-registration **cites the SHA-256** of each dataset it will use and
   states the commit range within which no reading script was committed.
3. Only summaries are readable before a dataset is legitimately opened.

This cannot make cheating impossible on a single-operator machine. It makes
cheating require a deliberate, documented act of omission rather than a moment
of curiosity.

---

# SECTION C — LEGITIMATE HYPOTHESIS ORIGINS

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

# SECTION D — IN-SAMPLE DISCIPLINE ON D1

## When D1 opens

Only when **both** hold:

1. The hypothesis statement has passed Section C admissibility review, and
2. The pre-registration — hypothesis, frozen configuration rule, parameter
   bounds, falsification criteria — is **committed to `main`**.

Committed, not drafted. A pre-registration that exists only in a chat, or only
in the Claude project mirror, does not exist. Three documents were found in
exactly that state on 2026-11-16; see `docs/APEX_DEFERRED_FIXES.md` N12.

## What D1 is for

Implementation, parameter estimation within pre-registered bounds, sanity
checks, and debugging. This is what in-sample material is for and the
forbidden-statistics list no longer binds once pre-registration is complete —
backtesting D1 is the point.

## Parameter bounds are declared before D1 opens

If the hypothesis has free parameters, **their ranges and the rule for choosing
among them are written into the pre-registration**, before D1 is examined.
Selection within declared bounds is permitted on D1 and is disclosed. Selection
of the bounds themselves from D1 is not: that is hypothesis discovery wearing a
different hat, and Section A's resolution forbids it.

**EmaCross stays 9/21.** Standing project rule, unchanged. More generally, a
re-tuned rejected hypothesis is inadmissible under Section C regardless of what
D1 shows.

## Iteration is permitted and counted

There is **no limit** on how many configurations are tried on D1. Unlimited
iteration against in-sample data is legitimate — that is what makes it
in-sample — **provided the count is disclosed.**

The pre-registration handed to Phase 50 therefore records:

- how many distinct configurations were evaluated on D1,
- how many distinct hypotheses-in-spirit were explored, if more than one
  survived Section C,
- and the in-sample result of the configuration finally chosen.

The discipline is disclosure, not restraint. A configuration chosen from two
hundred attempts may still be real; a configuration chosen from two hundred
attempts and reported as though it were the first is not assessable at all.
Phase 47 is the precedent worth remembering: a strategy returning +37.66R at PF
1.15 in-sample that the holdout correctly rejected.

## The configuration is frozen before Phase 50

Whatever D1 work produces, the exact rule handed to Phase 50 is **frozen and
committed** — stated precisely enough that two implementers produce identical
signals, with every parameter fixed to a value.

**No parameter may be chosen, adjusted, or reinterpreted after D2 is opened.**
Any ambiguity discovered at evaluation time is resolved against the hypothesis,
not in its favour, and the ambiguity is recorded as a defect in the
pre-registration.

## D1's status afterwards

**D1 is spent as in-sample the moment it is opened.** It can never serve as a
holdout for any hypothesis, including a different one. This is not a new
restriction — it is what in-sample means — but it is stated so that a later
phase does not propose reusing D1 as clean data.

---

# SECTION E — ACCEPTANCE CRITERIA

**Fixed before any hypothesis exists.** This is the point of the section. A bar
written after a candidate is in mind bends to fit it, usually without anyone
intending it to.

## E.1 The division of labour

Two tests, with different jobs. Conflating them is the error this section
exists to prevent.

| | **D2 — screening** | **Funded evaluation — confirming** |
|---|---|---|
| Job | Reject strategies an edgeless process would rarely produce | Establish that an edge is real |
| Sample | ~103 trades expected | Hundreds, over months |
| Verdict on passing | **"not rejected"** | "evidence of an edge" |
| Evidence strength | ~2–5× likelihood ratio | ~8× at minimum position size |
| Cost of a wrong pass | Proceed to a paid evaluation | Lose a funded account |

**D2 cannot establish an edge and Section E does not ask it to.** At ~103
trades the standard error of the win rate is 4.9 pp; a true 57.5% strategy is
statistically indistinguishable from break-even. Establishing a 57.5% edge
requires ~341 trades. See `docs/PHASE_49_ECONOMIC_FLOOR.md`.

## E.2 The D2 bar

Expressed as expectancy rather than win rate, because reward:risk is not known
until a hypothesis exists and a win rate means nothing without it.

**Primary criterion.** Against a null hypothesis of **zero net expectancy after
modelled costs**:

```
t = mean(R_net) / ( sd(R_net) / sqrt(n) )     must be  >= 1.282
```

one-sided, i.e. **a false-pass rate of 10%** on an edgeless strategy. At n ≈ 103
this corresponds to an observed net expectancy of roughly **0.126R per trade**.

`R_net` is per-trade return in units of the pre-registered stop, **after**
subtracting modelled spread and commission. The cost model is declared in the
pre-registration and **may not be changed after D2 is opened.**

**Why 10% and not 5%.** A 5% bar demands ~0.16R and would reject roughly three
quarters of genuinely good strategies at this sample size. A 10% bar admits one
edgeless strategy in ten, which the confirming test is there to catch. The
screening test is tuned to avoid discarding real candidates; the confirming test
is tuned to avoid believing false ones.

## E.3 Secondary criteria — all must hold

1. **Evaluable trade count.** `n >= 50` closed trades on the permitted region
   of D2, carried forward from the Phase 47 sample-validity rule. Below ~100 the
   primary criterion becomes very demanding; a hypothesis expecting few trades
   should say so under Section C element 7 and accept that.
2. **Density consistent with pre-registration.** Observed trade count within
   **±50%** of the figure declared under Section C element 7. A strategy that
   predicted 100 trades and produced 12 is mis-specified, whatever its
   expectancy — the pre-registration did not describe the thing that ran.
3. **Survivable drawdown.** The D2 equity curve, at the position size intended
   for the funded evaluation, must not breach the intended firm's **daily** or
   **maximum** drawdown limits. A strategy that would have failed the evaluation
   on D2 does not proceed to pay for one.
4. **Net expectancy positive after costs.** Implied by the primary criterion,
   stated separately so it cannot be lost.

## E.4 What a pass means, and does not

**A D2 pass licenses one thing: proceeding to a funded evaluation at the
pre-registered position size.** It is not evidence of profitability, it is not a
result, and it may not be described as one in any document, commit message or
summary.

The permitted form of words is **"not rejected by D2"**. The forms
"validated", "confirmed", "proven" and "works" are forbidden, for the reason
Phase 47 demonstrated: a strategy showing +37.66R at PF 1.15 in-sample had no
edge whatsoever, and the language used about a result shapes what gets risked
against it.

## E.5 The confirming test — conditions fixed in advance

Fixed here so they cannot be loosened later to make a marginal candidate
proceed:

1. **Position size at the minimum the firm permits**, and no more than **0.5%
   of account per trade.** This is not caution — it is measurement. At 0.5% a
   real edge passes ~93% of the time and an edgeless one ~11%, an evidence ratio
   of **8.3×**; at 1.0% the ratio collapses to 3.1×. Sizing up to pass faster
   destroys the information the test exists to produce.
2. **The firm must permit automated execution**, confirmed in writing before any
   attempt. Equity Edge prohibits Expert Advisors and trade copiers outright;
   the firm used must not.
3. **Static drawdown preferred over trailing**, and the firm's actual target,
   daily limit and maximum limit recorded in the pre-registration before the
   attempt.
4. **The configuration is frozen.** Identical to the one evaluated on D2. No
   parameter is chosen, adjusted or reinterpreted between the two tests.

## E.6 Economic floor

A strategy that is statistically real but economically trivial **fails**.

Before the evaluation attempt, the pre-registration states expected monthly
return at the pre-registered position size and trade density, and the capital
required to produce income that matters. If that calculation shows the strategy
cannot pay at any accessible account size, Phase 50 does not proceed regardless
of the D2 result.

This is written now, before a candidate exists, precisely because it will be
unwelcome later when something squeaks over the statistical line and nobody
wants to kill it.

---

# SECTION F — FORBIDDEN RESPONSES TO A RESULT

Carried forward in spirit from Phase 46's forbidden-response list. **That list
is to be read and merged into this section before ratification**; what follows
is this phase's own additions and must not be treated as replacing it.

## Forbidden after D2 is opened

1. **Any second use of D2.** It is spent on first evaluable output, whatever the
   outcome. See Section B.
2. **Re-running with altered parameters.** Including parameters the
   pre-registration left ambiguous — ambiguity resolves **against** the
   hypothesis, per Section D.
3. **Changing the cost model.** Spread, commission and slippage assumptions are
   fixed in the pre-registration.
4. **Reporting a favourable subset.** By date range, session, volatility
   regime, or any other partition not pre-registered.
5. **Reclassifying a failure as inconclusive** in order to test again.
6. **Extending the dataset** to obtain more trades after seeing a near-miss.
7. **Attributing failure to regime** and re-testing on a different window. If
   regime-dependence is part of the hypothesis it is pre-registered as such.
8. **Proceeding to a funded evaluation on a failed D2.**
9. **Describing a D2 pass as validation.** See E.4.

## Permitted after a failure

- Record the result, the configuration, and the in-sample/out-of-sample gap.
- Close the hypothesis.
- Form a **genuinely new** hypothesis under Section C, for a future phase, on
  data that does not yet exist. A new hypothesis is not the old one with
  different parameters — Section C already forbids that.

## The standing precedent

Phase 47 recorded a strategy at **+37.66R, PF 1.15 in-sample**, rejected by
106 holdout trades. The record of that rejection is worth more to this project
than the strategy would have been. A failure correctly recorded is the normal
and successful output of this process.

---

# SECTION G — PRECONDITIONS, WORK ITEMS, STOPPING RULE

## G.1 Session preconditions

Every Phase 49 session opens with `docs/SESSION_CHECKLIST.md` items 1 and 2:
clean tree, M0 PASS (3/3), CP3 PASS, `_last_sign` HIT, and
`py -m tools.check_record_integrity` PASS.

## G.2 Hypothesis generation protocol

**Bounded in advance, and the bound is not extended because the process has not
yet produced the answer hoped for.**

| | |
|---|---|
| Sessions | **3**, dedicated |
| Duration | **2 hours** maximum each |
| Data access | **None.** No D1, no D2, no statistical exploration, no implementation, no backtesting |
| Output per candidate | The seven-element statement of Section C |
| Review | Section C admissibility, before any pre-registration is written |

Every candidate considered is recorded with its outcome, including rejections.
A record showing only an eventual winner is defective — the Phase 48 screening
precedent.

## G.3 Work items

| ID | Work | Gate |
|---|---|---|
| W49.0 | Ratify this agreement, E/F/G complete, Phase 46 forbidden-response list merged | — |
| W49.1 | Firm requirement spec: rules compatibility and counterparty risk | Section E.5 |
| W49.2 | Hypothesis generation, 3 sessions | Section C |
| W49.3 | Admissibility review of each candidate | Section C |
| W49.4 | Pre-registration of the surviving hypothesis, committed to `main` | Sections C, D, E |
| W49.5 | D1 opened; implementation and in-sample development; iteration count disclosed | Section D |
| W49.6 | Configuration frozen and committed; Phase 49 closes | Section D |

**D2 is not opened in Phase 49 under any circumstance.**

## G.4 Stopping rule

**If no candidate satisfies Section C within the three sessions, Phase 49 closes
with the finding "No admissible hypothesis found."**

This outcome is accepted in advance. It is a complete and legitimate result, not
a failure of the phase, and **the deadline is not extended because the process
has not produced the answer hoped for.** D2 remains unspent and available to a
later phase that has a candidate.

### What that outcome would and would not establish

**It would establish:** that this research process, under these origin
constraints and within this agreed effort, did not produce a defensible
candidate.

**It would NOT establish** that systematic trading cannot work, that no edge
exists in this instrument, or that the project's method is wrong. The claim is
bounded to the process and its limits, and must be stated that way in the close
document.

What follows such a close is a separate decision, taken outside this agreement:
whether to run the process again with different origin constraints, or whether
systematic trading is the right vehicle for the goal it is meant to serve.

---

# OUTSTANDING BEFORE RATIFICATION

- **Merge the Phase 46 forbidden-response list into Section F.**
  `docs/PHASE_46_BOUNDARY_AGREEMENT.md` and `docs/PHASE_46_CLOSE.md` carry it;
  Section F currently states this phase's own additions only and explicitly
  does not replace it.

**One item. Everything else is drafted.**
