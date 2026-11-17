# Phase 49 — close

**2026-11-17.** Closed under `docs/PHASE_49_BOUNDARY_AGREEMENT.md` §G.4.

## Finding

> **No admissible hypothesis found.**

Three bounded hypothesis-generation sessions were conducted under the ratified
agreement. Twelve candidate classes were considered. None satisfied Section C.

**This outcome was accepted in advance.** G.4, verbatim: *"This outcome is
accepted in advance. It is a complete and legitimate result, not a failure of
the phase, and the deadline is not extended because the process has not produced
the answer hoped for."*

No fourth session. No relaxed criteria. No candidate manufactured to avoid an
unsuccessful result.

---

## What this establishes, and what it does not

G.4 requires the claim be stated with its limits, and this section is the
operative statement of the finding.

**It establishes:** that this research process, under these origin constraints
and within this agreed effort, did not produce a defensible candidate.

**It does NOT establish:**

- that systematic trading cannot work;
- that no edge exists in `frxGBPJPY`;
- that the project's method is wrong;
- that any individual candidate class has been *refuted*. Each was rejected as
  specified, on recorded grounds, with the limits of those grounds recorded
  alongside them.

The claim is bounded to the process and its limits.

---

## Compliance across the three sessions

| Requirement (G.2) | S1 | S2 | S3 |
|---|---|---|---|
| Duration ≤ 2 hours | ✔ | ✔ | ✔ |
| **D1 opened** | **NO** | **NO** | **NO** |
| **D2 opened** | **NO** | **NO** | **NO** |
| Statistical exploration performed | **NO** | **NO** | **NO** |
| Implementation or backtesting | **NO** | **NO** | **NO** |
| Section C relaxed | **NO** | **NO** | **NO** |
| Every candidate recorded including rejections | ✔ | ✔ | ✔ |
| G.1 preconditions passed at | `8f875e1` | `2bb381f` | `6b59137` |

**No sealed dataset was opened and no statistic was computed on any project data
at any point in Phase 49.** Every rejection rests on reasoning and published
literature. **D2 remains unspent and available to a later phase that has a
candidate.**

## The twelve classes

| # | Class | Session | Rejected on |
|---|---|---|---|
| 1 | Round-number order clustering (candidate A) | 1 | Element 6 — direction not selectable in advance |
| 2 | Fixing-window flows (candidate C) | 1 | Density; weakened predictability after the 2015 reform |
| 3 | Liquidity-conditional mean reversion (candidate B) | 1 | Element 2 — Payne (2003) contradicts the predicted direction |
| 4 | Gap effects | 2 | Density — ~52 genuine weekend gaps per year |
| 5 | Short-horizon serial dependence | 2 | Element 4 — not distinct from a crossover rule |
| 6 | Session-transition continuation | 2 | Element 2 — no directional theory |
| 7 | Intraday directional seasonality | 2 | Element 3 — Breedon & Ranaldo report the strategies unprofitable after costs |
| 8 | Volatility-triggered carry deleveraging | 3 | Element 2 — mechanism established at monthly/weekly horizons; the bridge to a 15-minute instrument-specific signal is absent |
| 9 | Margin-call cascades / crash risk | 3 | Density |
| 10 | Option dealer gamma hedging | 3 | Element 2; constraint 4 — external data |
| 11 | Swap / rollover financing at 17:00 NY | 3 | Publicly scheduled — dies as the fix did |
| 12 | Sovereign reserve / SWF rebalancing | 3 | Unobservable; density |

**Volatility clustering** was raised in session 2 and withdrawn under challenge:
it fails element 2 before the instrument question arises, being a magnitude
hypothesis rather than a directional one. Recorded there, not counted here.

**The Osler round-number re-specification** is recorded in
`docs/PHASE_49_HYPGEN_SESSION_3.md` as a variant of class 1 and is not counted
as a thirteenth class. It is the one result of Phase 49 worth carrying to a
future phase, and it is deliberately preserved rather than discarded.

---

## Findings worth preserving

These are the durable products of Phase 49. They cost three sessions and are
more useful than a weak candidate would have been.

**1. Candle-only data cannot distinguish temporary liquidity-driven price
pressure from permanent information-driven price discovery.** (Session 1.) That
distinction is the load-bearing element of most market-structure mechanisms —
it is what separates "this will revert" from "this will continue". Where a
mechanism's directional prediction turns on it, element 2 cannot be satisfied
with what this project holds.

**2. Constraint 4 is heavier than it appears.** (Session 2.) Any hypothesis
conditioning on an external series — another pair, a rate differential, an
economic calendar — cannot be tested on D1 or D2 without acquiring aligned
external data, which would be a new acquisition requiring its own agreement.
Most of what market-structure reasoning reaches for is therefore out of range.

**3. A documented market effect is not necessarily a tradable market edge, and
the obituary is in the source rather than the headline finding.** Demonstrated
three times: Payne against candidate B's direction; Breedon & Ranaldo against
intraday seasonality's costs; Osler's own anticipation statement against
round-number exploitability. In every case the literature that would have
supplied the origin is also the literature that documents the effect as
unexploitable, and in every case the advisor would have carried the candidate
forward on recall alone.

**4. A publicly observable conditioning variable is the weakest possible basis
for element 3.** (Session 3.) The easier an effect's trigger is to see, the
stronger the prior that it is already competed away. Candidates look *better* on
observability and *worse* on exploitability as the trigger becomes more public,
and exploitability should be assessed first because it is cheaper.

**5. Procedural origins die on density; behavioural origins die on direction.**
Of the twelve classes, the ones with a genuine institutional obligation behind
them (the fix, gaps, margin cascades, sovereign rebalancing) failed because the
obligation is infrequent; the ones with adequate frequency failed because theory
would not fix the sign. The intersection — frequent *and* directionally
determinate *and* observable in one instrument's candles — is where the
admissible space is narrow, and three sessions did not find a point in it.

**6. The economic floor matters more than statistical detectability.**
`docs/PHASE_49_ECONOMIC_FLOOR.md` established that D2 holds roughly a third of
the sample needed to confirm a 57.5% edge, that a break-even strategy passes a
funded evaluation 45.5% of the time, and that position size determines how much
passing means (8.3× evidence ratio at 0.5% risk versus 3.1× at 1%). Those
findings are independent of any hypothesis and survive this close.

## Standing practice carried forward

**No candidate proceeds on a citation produced from memory.** The source is
retrieved and read, including its cost, horizon and profitability sections,
before the candidate is considered admissible. Adopted in session 2 after two
near-misses; it was the operative discipline in session 3 and it is what killed
class 8 and the Osler sub-line.

**Proposer and reviewer were not independent in any of the three sessions.** The
advisor proposed; the CEO reviewed. Mitigated by a uniform standard applied to
every candidate, which caught advisor errors in all three sessions. Recorded,
not resolved. A future generation phase should separate the roles if it can.

---

## Work item disposition (G.3)

| ID | Work | Status |
|---|---|---|
| W49.0 | Ratify the agreement; E/F/G complete; Phase 46 forbidden-response list merged | **Complete** at `8f875e1` |
| W49.1 | Firm requirement spec: rules compatibility and counterparty risk | **Spec complete** at `6b59137`; **firm verification outstanding** |
| W49.2 | Hypothesis generation, 3 sessions | **Complete** — 3 of 3 used |
| W49.3 | Admissibility review of each candidate | **Complete** — 12 classes, 0 admitted |
| W49.4 | Pre-registration of the surviving hypothesis | **Not reached** — no surviving hypothesis |
| W49.5 | D1 opened; in-sample development | **Not reached** |
| W49.6 | Configuration frozen; phase closes | **Superseded by this close** |

**W49.1 is explicitly incomplete and this close does not imply otherwise.**
`docs/FIRM_REQUIREMENT_SPEC.md` is written and ratified, but no firm has been
verified against it. An enquiry was sent to Equity Edge on 2026-11-17 asking
whether a self-built program used only to generate signals, with manual
execution, constitutes EA use; whether such profits are payout-eligible;
whether the intended trade profile engages any prohibited practice; and which
clauses govern each answer and for which account types and phases. That
verification runs independently of Phase 49 and is governed by its own rulings.

G.4 is triggered by the three sessions, not by completion of the work items, so
W49.1's outstanding state does not block this close.

## What follows

A separate decision, taken outside this agreement — G.4's own words. The
options, stated without recommendation:

- run the generation process again under **different origin constraints**;
- decide, as a distinct and explicitly agreed acquisition, whether an aligned
  second data series is worth acquiring — **taken before any candidate is
  named**, never afterwards to rescue one, since changing the evidence boundary
  to accommodate an idea is curve-fitting one level up;
- pursue the funded-evaluation route on its own merits, which does not depend on
  a hypothesis existing;
- do none of these.

Nothing in this close recommends or forecloses any of them.

---

## Record integrity

`py -m tools.check_record_integrity` — **PASS** at `6b59137`: 45 documents
scanned, 52 paths cited, no dangling references, three known-absent paths
recorded with reasons (A2, G.4 stub, A1), amendment chains complete for phases
44, 45, 46 and 48.

Deferred items remain deferred and are unaffected by this close: A2, N6, N10,
N11, N12 and incident I1 stand as recorded in `docs/APEX_DEFERRED_FIXES.md`.

## Close

> Phase 49 set out to determine whether a defensible trading hypothesis could be
> generated from permitted origins, within a fixed research budget, without
> touching sealed data. It could not. The process ran to its agreed limit, every
> candidate and rejection was recorded with the grounds and the limits of those
> grounds, the sealed holdout was not spent, and no criterion was weakened to
> produce a result. That is the phase working as designed, and the negative
> finding is the product.

| | |
|---|---|
| Phase | 49 |
| Verdict | **No admissible hypothesis found** |
| Sessions used | 3 of 3 |
| Classes considered | 12 |
| Candidates admitted | **0** |
| D1 opened | **No** |
| D2 opened | **No** — unspent, available to a later phase |
| Section C relaxed | **No** |
| Closed under | §G.4 |
