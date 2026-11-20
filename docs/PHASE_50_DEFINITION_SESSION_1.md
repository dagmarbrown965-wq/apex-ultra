# Phase 50 — definition session 1

**2026-11-20.** A **session record**, not an agreement. Nothing here is
ratified, and no part of it authorises anything.

**Outcome: a framework for evaluating the Phase 50 architecture was
developed. No trustworthy numerical operating characteristics were
established and no architecture was selected. Step 2 is paused.**

---

## Compliance

| | Status |
|---|---|
| D1-A opened | **NO** |
| D1-B exposed | **NO** |
| D2 accessed | **NO** |
| Any sealed dataset read | **NO** |
| Phase 48 seal amended or reinterpreted | **NO** |
| Phase 49 result altered | **NO** — stands closed at `0af9555` |
| Phase 50 agreement drafted | **NO** |
| Execution authorised | **NO** |

Every figure in this document comes from simulation over assumed parameters or
from arithmetic over published summary values. No project data was used.

## Provenance — what is verified, and by whom

**This matters more than usual here, because most of this session's numbers
have been neither independently reproduced nor audited.**

| Tier | Artefact | Status |
|---|---|---|
| **Independently reproduced** | `d1b_mc_v2.py` | CEO ran it on a different OS and numpy version and obtained an **exact line-for-line match**, including interval values |
| **Source audited, not run** | `d1b_mc_v5_1.py`, `phase50_economics.py`, `phase50_sel.py` | CEO read the source and found defects recorded below. CEO stated explicitly: *"I am assessing the numerical results and methodology you supplied, not claiming to have independently reproduced the simulations."* |
| **Neither audited nor reproduced** | `d1b_mc_v3/v4/v5/v5_2/v6/v7/v8/v9.py` | Advisor-run only. Figures are unverified |
| **Not committed** | all of the above | None of these scripts exists in the repository. The figures are not reproducible project evidence |

**No script from this session is in `docs/` or `tools/`.** A future reader
cannot re-derive any number below.

---

# STEP 1 — the seven requirements

Accepted by the CEO as the working specification, with two corrections applied.
**These are the advisor's rendering of CEO rulings, not verbatim quotation**,
a distinction the CEO required be preserved.

**Architecture these govern:** D1-A discovery → freeze one candidate → D1-B
internal out-of-sample → D2 independent overfit detection (single use) → E.5
live evaluation at ≤0.5% risk.

**R1.** D1-B and D2 are **rejection filters, not two confirmations.** Both sit
below the sample size needed to confirm the reference effect. Neither may be
reported as establishing an edge, and passing both is not "confirmed twice".

**R2.** Combined false-survival and genuine-edge survival rates **must be
evaluated by Monte Carlo** before any threshold is approved. Joint survival is
simulated directly; multiplying marginals is not an acceptable substitute.

**R3.** D1-B's verdict **depends on its realised sample size.** The minimum
realised trade count for a conclusive verdict is fixed in advance. Below it the
verdict is inconclusive — not a pass, not a failure — with no extending the
period, substituting the candidate, or adjusting parameters.

**R4.** D1 and D2 are **permanently consumed** by Phase 50, whatever the
outcomes.

**R5.** Phase 50 leaves **no clean historical test data.** Fresh forward data
must accumulate before another test can be run, subject to the collection
interval established by Phase 48 Section B (**75 days from lock**).

> *Correction applied.* An earlier draft said "75–90 days". The 90 was
> introduced by the advisor and is not supported by the record; the D1 seal
> states only *"75-day interval from lock per Section B"*. The range was
> removed rather than left as a ruling.

**R6.** The **epoch-boundary tooling must be built and independently verified
before D1-A is opened.** Declared split epoch; tool and its read-boundary tests
committed to `main` before execution; verification that it cannot read, plot,
compute from or otherwise expose D1-B; permitted and prohibited ranges
recorded; any D1-B exposure during discovery permanently spends D1-B. The CEO
further required that the fixture test **actual information boundaries**, not
merely that a particular query returns no rows.

**R7.** The D1-B and D2 **testing procedure must address** serial dependence
and episode clustering. Its false-pass rate must be **evaluated by simulation**
across the declared dependence mechanisms and parameter ranges before any
threshold is approved.

> *Correction applied.* The advisor's original wording called the statistic
> "robust". The CEO required the weaker and more accurate formulation, on the
> grounds that calling a statistic robust before demonstrating its operating
> characteristics implies a property not established.

Gate 7 sub-requirements, as specified by the CEO and unchanged:

- **7a** a declared set of dependence-generating mechanisms;
- **7b** explicit parameter ranges and justification for those ranges;
- **7c** calibration results for each procedure under those mechanisms;
- **7d** a distinction between empirically supported dependence assumptions and
  deliberately adverse stress scenarios;
- **7e** no claim of nominal 10% error control where simulation demonstrates
  otherwise;
- **7f** an explicit inconclusive or uncalibrated outcome where dependence
  cannot be bounded sufficiently.

**On K**, ruled but not numerically set: K is the total number of candidate
hypotheses examined during D1-A, including rejected candidates and variations
sufficiently similar to constitute additional tests; the counting rule is
defined before exploration begins; the count may not be reset; and the operator
may not decide afterwards that several tested candidates were really one
hypothesis.

**On scenarios:** no declared dependence scenario may be dropped or softened
because a procedure performs badly in it.

---

# STEP 2 — gate 7's circularity

## The problem

Gate 7 requires the procedure's false-pass rate to be evaluated before any
threshold is approved. The dependence structure of `frxGBPJPY` trade outcomes
is unknown. Estimating it requires trade outcomes, which require a frozen
strategy, which requires D1-A to be open — and at ~210 trades the dependence
that materially inflates the variance is below the noise floor of estimating
it. Read literally, the gate could not be discharged before the thing it
protects.

## The resolution developed

1. **Declare a bound, do not estimate the dependence.** The declared
   dependence range is organised by a bound `V_max` on the variance inflation
   factor of the sample mean.
2. **Set the threshold by simulation over the declared domain**, not by a
   normal approximation, which ran optimistic throughout.
3. **Publish the operating characteristics before any data exists.**
4. The D1-A measurement becomes a **one-way falsification tripwire**, never an
   input to the threshold.
5. **State the asymmetry** rather than claim symmetry.

The claim this licenses is conditional and demonstrable: *provided dependence
does not exceed `V_max` on the declared grid, the false-pass rate is at most
the declared tolerance.* It does **not** claim that `V_max` holds.

**CEO wording, to be preserved verbatim in any eventual agreement:**

> A declared VIF bound is an assumption defining the conditional calibration
> claim. It is not an empirically established property of the strategy. D1-A
> can falsify that assumption but cannot validate it merely by failing to
> detect a violation.

## Two designs were specified and a third emerged

| | Design A | Design B | Design C |
|---|---|---|---|
| | minimax | conditional | single-stage |
| Cutoff basis | calibrated at `V_max` | calibrated at i.i.d. | calibrated at i.i.d. |
| Stages | D1-B + D2 | D1-B + D2 | D1-B only |
| Size claim | ≤ tolerance across the grid | disclosed per VIF | disclosed per VIF |

Design C emerged from the advisor challenging its own two-stage proposal after
the joint simulation showed the chain discards most genuine candidates. The CEO
required that C be evaluated on its merits rather than rejected for departing
from the original architecture, and that R1 not be silently treated as
optional if C were adopted.

**CEO wording for Design B, to be preserved if B is adopted:**

> Design B does not provide uniform 10% false-pass control across the declared
> dependence domain. It uses an IID-calibrated integer cutoff and reports the
> simulated false-pass probability at each declared VIF and dependence
> mechanism. The increased false-pass probability under dependence is an
> accepted limitation, not a calibration success. No result may be described as
> having 10% error control unless the applicable dependence assumptions support
> that claim.

---

# FINDINGS — established

These survive the defect register. Each is either analytic, verifiable by
inspection, or reproduced across independent runs.

**F1. The incumbent test is miscalibrated under dependence, and the magnitude
follows an analytic formula.** For a two-state latent regime on the win
probability with conditional independence given the state:

```
Var(r_t) = 4 p(1-p)
Cov(r_t, r_{t-k}) = 4 a^2 phi^k        phi = 2*persist - 1
rho(k) = lambda phi^k                  lambda = a^2 / [p(1-p)]
VIF_n  = 1 + 2 sum_{k=1}^{n-1} (1 - k/n) lambda phi^k
```

**The CEO derived the finite-sample form independently** and corrected the
advisor's asymptotic version. At persist 0.98, a 0.10, n 210: VIF = 2.696, and
the predicted false-pass rate of 21.8% was matched by simulation.

**F2. The dependence is in the latent win probability, not in the outcomes.**
Outcomes are conditionally independent given the state. This models persistent
variation in the probability of winning and does **not** represent
outcome-to-outcome mechanisms such as overlapping positions. The CEO
identified this distinction; it is a limitation of the model, not a property of
the market.

**F3. The economic floor's 341-trade figure and Section E.2 answer different
questions.** The floor asks whether a 57.5% rate can be distinguished from a
coin (null 50%, two-sided 5%) — 341 trades, confirmed by simulation at 79.5%
power and closed form at 349. E.2 asks whether it can be distinguished from
**zero net expectancy after costs** (null 52.6%, one-sided) — **470 trades**,
closed form and simulation agreeing. Both figures are correct for their own
question. **Any Phase 50 sizing against E.2 must cite 470, not 341.**

**F4. The test reduces exactly to an integer win-count cutoff.** For p̂ ≥ 0.5
the statistic is strictly increasing in the win count, so `t ≥ crit` is
equivalent to `wins ≥ W`. Verified at both n = 210 (106 attainable values) and
n = 103 (52). This removes the discrete-threshold problem by construction
rather than by interpolation, and is verifiable by inspection.

**F5. A long HAC bandwidth is self-defeating.** At n = 210 with L = 100,
HAC sized at ~19% on i.i.d. data. L/n ≈ 0.48 is far outside the regime where
HAC is valid, so "use a longer bandwidth" cannot be the correction.

**F6. The floor's funded-pass figures were cited against the wrong row.** The
advisor used 11.3% as the probability a worthless candidate passes E.5. That
figure is the floor's rate for a **losing** strategy at a 50% win rate. For a
**zero-expectancy** candidate at break-even the floor's own figure is 45.5%,
which the session's E.5 simulation reproduced independently (~45%). The cause
is structural: an 8% profit target against a 10% drawdown means a driftless
walk reaches the target first roughly 56% of the time before costs. **The
evaluation's barriers favour a zero-expectancy strategy.**

**F7. Conditional and unconditional false-funded probabilities are different
quantities and both are required.** The CEO identified that the advisor's
tables reported the unconditional quantity under a conditional-sounding label.
The conditional figure is the stable property of an architecture; the
unconditional one mixes in the prior.

---

# FINDINGS — provisional, NOT established

**The figures in this section are illustrative of the framework's behaviour.
They are not operating characteristics and must not be cited as such.** Every
one is subject to the defect register below.

- The incumbent test sized at roughly 10% under independence and roughly 23%
  under the strongest simulated dependence. Direction and rough magnitude are
  consistent across versions; the specific numbers are unverified.
- Neither HAC, a bootstrap standard error, nor a HAC-studentized bootstrap-t
  held nominal size across the full declared domain at n = 210. A
  HAC-studentized bootstrap-t at a longer block length was the best of those
  examined, and remained oversized under the strongest dependence.
- A model-based long-run variance estimator held size only by being
  conservative, at a severe cost in power.
- Simulated size appeared **monotone in VIF** at a fixed cutoff, with no
  violations across four mechanisms and eleven grid points on the verification
  replicate. **This is a grid result; no continuity between grid points is
  claimed.**
- Across four mechanisms matched to the same VIF, sizes agreed closely at low
  VIF and spread by roughly one to one-and-a-half points at the highest. **VIF
  is the principal organising variable and is NOT established as a sufficient
  statistic** — the CEO's formulation, adopted.
- The two-stage chain appeared to discard most genuine candidates at the
  reference effect size; the single-stage alternative retained substantially
  more power at a substantially higher false-pass rate.
- The D1-A dependence tripwire appeared **near-inert**: at a true VIF equal to
  the declared bound it fired in roughly 0% to 2% of runs depending on
  mechanism, and worst against the longest-correlation mechanism, where a
  batch-means estimator with batch size 21 reads far below a correlation time
  of about 50. **The one-way falsification requirement is formally satisfied
  and practically close to empty.** The CEO required this limitation appear in
  any agreement rather than be glossed.
- Simulated selection on D1-A appeared to **enrich** the frozen candidate for
  genuineness, with the post-freeze probability several times the per-candidate
  base rate. **This result depends on a candidate population the CEO judged
  too restrictive** (see D16) and should not be relied on.

---

# THE FOUR EV BIASES

All four were found during the session, three by the advisor auditing its own
code and one by the CEO. **All four run in the same direction — they understate
the cost of a high-power architecture, and therefore flatter Design C.** The
economic rankings produced during the session are **withdrawn**, not retained
as provisional.

| # | Bias | Found by | Effect |
|---|---|---|---|
| 1 | A post-selection prior was paired with **pre-selection** single-candidate false-pass rates | CEO | Understated loss. Repaired by simulating the selection process so the post-freeze prior became an output |
| 2 | The **epistemic cost was omitted entirely** from the EV model, not implicitly included | CEO asked; advisor confirmed omission | Understated loss by an unpriced amount |
| 3 | The **attempt fee was charged only to worthless candidates** | advisor | Understated loss. A genuine candidate that passes the filter and fails E.5 also pays the fee. Correct form: `EV = P(real & funded)·V − P(historical pass)·C_attempt` |
| 4 | The worthless candidate population was **homogeneous at exactly break-even** | CEO | Overstated the selection enrichment and understated selection damage |

**The epistemic cost is to be represented as a constraint, not a price** — a
declared maximum acceptable probability of a worthless candidate reaching
funded status. The CEO declined to price false confidence and declined to adopt
any particular limit, on the grounds that a limit chosen now would risk being
selected because it conveniently separates the architectures under
consideration.

---

# DEFECT REGISTER

Open unless marked. Defects in the advisor's own simulations, recorded so that
no figure is relied on without them.

| # | Defect | Status |
|---|---|---|
| D1 | A column labelled `iid-t` computed HAC at L=1, in two separate tables | found by CEO; figures withdrawn |
| D2 | A silent bandwidth cap meant a column labelled `L=100` used L=52 | found by advisor; table mislabelled |
| D3 | "effective independent blocks" conflated regime-run count, variance-equivalent effective sample size, and independent observations | found by CEO; three quantities now reported separately |
| D4 | Confidence intervals were dropped in one version, a regression from the previous one | repaired in later versions |
| D5 | An outcome-level dependence generator was not null-calibrated; its stationary win rate embedded a genuine edge of +0.65pp in a table reporting size | found by advisor; repaired and re-run |
| D6 | A bootstrap-t studentized each resample by its **marginal** standard deviation, applying an independence-assuming denominator to a dependence-preserving resample | found by CEO; repaired with a HAC studentizer, which **reversed** the earlier conclusion that the bootstrap added nothing |
| D7 | The advisor wrongly flagged a three-state generator as mis-initialised; its transition matrix is doubly stochastic and the uniform start is stationary | corrected by CEO; advisor's flag withdrawn |
| D8 | A supremum taken over many noisy cells is upward-biased, and one row consisted of four independent draws of the same process counted as four mechanisms | found by advisor; repaired by collapsing the row and adopting Bonferroni-simultaneous bounds |
| D9 | Critical values at n = 103 were non-monotone because the statistic's attainable values form a coarse lattice | found by CEO; resolved by the integer-cutoff reformulation (F4) |
| D10 | A dead variable held the wrong row of the floor's table (11.3% rather than 45.5%); it did not propagate only because it was never used | found by advisor; see F6 |
| D11 | Currency units were never stated in the economic model | open |
| D12 | An inert time-cost parameter was multiplied by zero throughout | open |
| D13 | False-funded probabilities were computed unconditionally and presented under a conditional-sounding heading | found by CEO; see F7 |
| D14 | No uncertainty bounds on any figure in the selection model, and Design A's headline false-funded figure rests on **one event in 15,000 paths** | found by advisor, endorsed by CEO as critical |
| D15 | Only one worthless-candidate population was simulated. The CEO requires at least three: exactly break-even; heterogeneous around break-even including losing strategies; and predominantly losing with a near-break-even component | open |
| D16 | Candidates were given independent dependence paths. Strategies explored on the same market data share exposure to the same episodes. The CEO requires at least four cross-candidate structures and warns that the independent case must **not** be assumed conservative | open |
| D17 | The dependence amplitude was calibrated on the break-even variance and applied unchanged to genuine candidates, whose realised VIF is therefore about 2% higher than labelled | found by CEO; open |
| D18 | The amplitude was calibrated on a 210-trade window and applied to a 600-trade E.5 segment, whose realised VIF is about 5% higher than labelled | found by CEO; open |
| D19 | Dead code: an `if False` leftover, three unused functions, one unused constant; and a helper named for a 95% bound used a one-sided multiplier | open |
| D20 | Rare-event probabilities were estimated by normal approximation. The CEO requires exact binomial methods and event counts where rare events drive the decision | open |
| D21 | E.5's assumed rules — 0.5% risk, 1:1, 0.052R cost, +8% target, −10% barrier, 600-trade cap — are **simulation assumptions, not verified firm rules** | open pending firm information |

## Overstatements withdrawn

Recorded because the pattern matters more than any single instance.

| Claim | Why withdrawn |
|---|---|
| "No estimator can recover a sum of terms each of which is invisible" | Too strong. A model-based estimator can use the joint pattern across lags. CEO's reformulation adopted |
| "A properly implemented bootstrap-t buys nothing" | An artefact of D6. Reversed after the studentizer was corrected |
| "VIF is a sufficient statistic for calibration" | Not established. VIF is the principal organising variable only |
| "Design A is economically dominated" | Not demonstrated. A pointwise test found A best in 11 of 48 cells, all at high attempt cost |
| "A coin that says fail regardless of whether an edge exists" | Imprecise. The rejection probability does differ between null and alternative; the discriminating power is merely very weak |
| "E.5 is worth 8.3:1, so a false positive is cheap" | The 8.3:1 came from the floor's i.i.d. Monte Carlo and is not dependence-robust. E.5 limits exposure; it does not establish genuineness |
| A joint probability obtained by multiplying marginals | R2 forbids it. Replaced by direct simulation on shared-dependence paths, which showed the error was real but modest here |

---

# OUTSTANDING WORK

Deferred by CEO decision, not abandoned.

1. **Three worthless-candidate populations** (D15) and **four cross-candidate
   dependence structures** (D16).
2. **Per-population VIF verification** (D17) and **E.5 dependence
   recalibration** (D18).
3. **Exact binomial bounds and event counts** on all rare-event estimates
   (D14, D20), with more paths where they drive the decision.
4. **EV reconstruction** with the fee attached to every historical pass (bias
   3) and the epistemic constraint reported alongside.
5. **Firm-specific E.5 rules and fee structure** (D21), including whether
   separate stage or reset fees exist.
6. **The D1-A estimator's decision rule**, which the CEO required be fixed
   before D1-A opens and which remains unsettled given the tripwire's measured
   weakness.
7. **An independent audit** of every script, none of which is committed.

## Why it was paused

Two reasons, both CEO-stated. The monetary inputs are unresolved, so the
economic comparison is exploring a hypothetical cost surface; and Phase 49
produced no admissible candidate, so the effort optimises the statistical
treatment of a candidate that does not exist. In the CEO's words, there is *"a
legitimate distinction between preparing an experiment and endlessly improving
its apparatus"*, and the full matrix should resume when there is a concrete
decision it can change.

---

# CANDIDATE GENERATION — the four routes

Assessed in this session and accepted by the CEO. **There is currently no
open, authorised route to finding a candidate.**

| Route | State |
|---|---|
| Phase 49 generation | **Closed** at `0af9555`. Three sessions spent, twelve classes rejected, no candidate. Cannot produce one |
| Phase 50 D1-A discovery | **Unauthorised**, and its apparatus is the work paused here |
| A fourth generation phase under different origin constraints | **Available under G.4** but needs a new agreement. Three sessions under armchair constraints produced nothing |
| Acquiring a second aligned data series | **Deferred** as a separate decision, never taken |

Choosing which to open is a strategic decision the CEO has deliberately left
for a fresh session rather than rushing into this closeout.

The firm-verification track continues independently. Equity Edge is
disqualified and closed (`fa18231`); an enquiry to a second firm is open.

---

# CLOSING STATUS

| | |
|---|---|
| Step 1 | Seven requirements accepted as the working specification |
| Step 2 | **PAUSED** |
| Numerical operating characteristics | **NONE ESTABLISHED** |
| Architecture | **NONE SELECTED** — A not demonstrated dominated, B and C unresolved |
| `V_max` | **NOT CHOSEN** |
| Epistemic limit | **NOT ADOPTED** |
| Agreement | **NOT DRAFTED, NOT APPROVED** |
| D1-A opening | **NOT AUTHORISED** |
| D1-B exposure | **NONE** |
| D2 access | **NONE** |
| Execution | **NOT AUTHORISED** |
| Phase 49 result | **UNCHANGED** — no admissible hypothesis found |
| Phase 48 seal | **UNCHANGED** |

> The current simulations have established a useful framework for evaluating
> selection, historical rejection filters, and false-funded outcomes. They have
> not established trustworthy numerical operating characteristics or selected
> an architecture. Further simulation is deferred pending resolution of the
> relevant economic inputs and a concrete candidate requiring evaluation.

**Standing caution, CEO-stated:** the firm enquiry must not become an
indefinite dependency. If a firm's response is negative or lacks contractual
clarity, another firm is evaluated under the same per-firm process. **The
strategy requirements are not weakened to accommodate a firm's rules.**

**And the sentence this session should be remembered by:** progress in
measuring an edge is not progress in finding one.
