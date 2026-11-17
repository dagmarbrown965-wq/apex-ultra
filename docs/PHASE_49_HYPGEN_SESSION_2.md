# Phase 49 — hypothesis generation, session 2 of 3

**2026-11-17.** Conducted under `docs/PHASE_49_BOUNDARY_AGREEMENT.md` §G.2.

**Outcome: four candidate classes examined, four rejected. No admissible
hypothesis produced.**

---

## Compliance

| Requirement (G.2) | Status |
|---|---|
| Session 2 of 3 | ✔ |
| Duration ≤ 2 hours | ✔ |
| **D1 opened** | **NO** |
| **D2 opened** | **NO** |
| Statistical exploration performed | **NO** |
| Implementation or backtesting | **NO** |
| Section C relaxed | **NO** |
| Every candidate recorded including rejections | ✔ |

Session preconditions (G.1) run and passed at `2bb381f`.

**Session 2 ran immediately after session 1**, which G.2 permits — it caps
duration, not spacing — but which reduces what three separate sessions are
meant to buy, since the second began from where the first ended rather than
from anywhere new. Recorded as a limitation of this session's independence.

## Brief

Set by session 1: **not** an immediate search for another market-structure
mechanism, but an examination of whether legitimate hypothesis origins exist
that do not depend on identifying hidden order flow and do not turn on
distinguishing temporary from permanent price impact.

## The constraint stack, stated explicitly

Each constraint has a separate source; together they are tighter than any one
of them appears.

1. **Origin** — structural, published, or procedural, statable without the data.
2. **Direction** — theory must justify the predicted direction, not merely the
   existence of an effect. *(Element 2; this is what rejected candidate B.)*
3. **Impact type** — must not turn on separating transitory from permanent
   price impact. *(Session 1 structural finding.)*
4. **Observability** — observable in **15-minute OHLC of a single instrument**.
   D1 and D2 contain `frxGBPJPY` candles and nothing else.
5. **Distinctness** — not a crossover rule, not a compression breakout.
6. **Density** — ≥ 0.56 trades/day to reach n ≥ 50 on D2.
7. **Cost** — clears 0.052R at a 25-pip stop on the observed 1.3-pip spread.

**Constraint 4 is heavier than it first appears.** Any hypothesis conditioning
on an external series — another pair, a rate differential, an economic calendar
— cannot be tested on D1 or D2 without acquiring aligned external data. That is
a new acquisition and would arguably require its own agreement. Most of what
market-structure reasoning normally reaches for is therefore out of range.

---

## Rejections

| Candidate class | Decision | Reason |
|---|---|---|
| Gap effects | Rejected | Insufficient event density for continuously traded FX; genuine weekend gaps are too infrequent. |
| Short-horizon serial dependence | Rejected | Insufficient distinctness from existing crossover strategies; measurement is also restricted before pre-registration. |
| Session-transition continuation | Rejected | Participation changes do not establish a theoretically justified directional prediction. |
| Intraday directional seasonality | Rejected | Breedon & Ranaldo report that most time-of-day strategies are unprofitable after transaction costs. |

### Gap effects

FX trades continuously; the only genuine gaps are weekend reopenings at ~52 per
year. Fails constraint 6 outright.

### Short-horizon serial dependence

A moving-average crossover **is** a serial-dependence bet. Element 4
distinctness cannot be satisfied by relabelling. Separately, return
autocorrelation at any lag is on the Phase 48 forbidden-statistics list until a
hypothesis is pre-registered, so the effect cannot be measured first and then
hypothesised.

### Session-transition continuation

Participation and price-discovery conditions change at session boundaries. No
argument was found that establishes **which direction** should follow. Element 2
fails for want of a directional theory, not for want of an effect.

### Intraday directional seasonality — examined in detail

**The effect is real and published.** Sources retrieved and read in this
session:

- **Ranaldo (2009)**, *Segmentation and Time-of-Day Patterns in Foreign Exchange
  Markets*, J. Banking & Finance 33(12), 2199–2206.
  `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=960209`
  Abstract, verbatim: *"Domestic currencies appreciate (depreciate)
  systematically during foreign (domestic) working hours."*
- **Breedon & Ranaldo**, *Intraday patterns in FX returns and order flow*, SNB
  Working Paper 2011-4. **Full text retrieved.**
  `https://www.snb.ch/public/asset/en/www-snb-ch/publications/research/working-papers/2011/working_paper_2011_04/publications0_en/working_paper_2011_04.n.pdf`

**Mechanism:** order flow. International funds trade in their own hours and are
net purchasers of foreign exchange, producing sell-pressure on the domestic
currency during domestic hours.

The hypothesis under consideration was that GBP/JPY should fall during London
hours and rise during Tokyo hours — two non-overlapping daily windows, ~177
signals on D2, escaping constraint 3 entirely because it predicts a persistent
directional tilt rather than reversion-versus-continuation.

#### Rejected — Section C element 3 (exploitable in advance)

**The originating paper tested it as a trading strategy and reports it
unprofitable.** Breedon & Ranaldo, verbatim:

> *"most of these simple time-of-day trading strategies are not profitable when
> trading costs are included"*

The sole exception is **EUR/USD**, with in-sample Sharpe ratios of 1.3 and 0.9
over 1997–2007.

Element 3 asks why an effect should be exploitable in advance rather than
merely visible afterwards. The literature that would have supplied the origin
answers that question directly and negatively.

#### Three limitations on this rejection — recorded, not resolved

**1. GBP/JPY was not in the tested sample.** The pairs studied are EUR/USD,
USD/JPY, GBP/USD, EUR/JPY, USD/CHF, AUD/USD. **This is an additional limitation
on the candidate, NOT proof that GBP/JPY cannot exhibit the effect.** The cost
result is strong evidence against admissibility; it is not a measurement of
this instrument.

**2. The EUR/JPY sign anomaly is UNRESOLVED and is not used as decisive
evidence.** Table 2 reportedly shows EUR/JPY JPY-session returns of −0.057,
which in pair terms means JPY *rose* during its own session — contrary to the
paper's general claim. The subagent that retrieved this **explicitly flagged its
own sign-mapping as unverified.** The observation is recorded because EUR/JPY is
the only cross in the sample and GBP/JPY is also a cross, so the composition of
two local sessions is the relevant structure. **It must be independently
verified against the full paper before being relied upon.**

**3. The data ends June 2007.** Nineteen years of algorithmic competition on a
publicly documented effect. This is a plausibility argument, not a measurement.

---

## Volatility clustering — considered and withdrawn

Raised in this session as possibly the strongest surviving mechanism, then
withdrawn under CEO challenge.

It satisfies constraints 1, 3, 4, 5 and 6 without strain: robust, supported by
clustered information arrival, observable in candles, high-density, distinct
from both failed strategies.

**It fails constraint 2 before the instrument question arises.** Volatility
clustering predicts that large movements follow large movements; it says
nothing about whether the next movement is up or down. It is a magnitude
hypothesis, not a directional one.

The advisor initially framed this as an *instrument* mismatch — that a
directional CFD cannot express a volatility view. That is true but downstream.
**The correction is recorded because the advisor reached a more interesting
conclusion than the evidence supported**, which is the second time in two
sessions that the CEO's uniform standard has caught the advisor arriving
somewhere early.

A separate point stands: **if a volatility view were ever pursued, the binary
alternative does not automatically solve it.** Deriv binaries carry an explicit
payout structure that places break-even above 54% before any edge is required.
That would need establishing, not assuming.

---

## Methodological lesson — now demonstrated twice

**A documented market effect is not necessarily a tradable market edge.**

| Session | Candidate | Killed by |
|---|---|---|
| 1 | Liquidity-conditional mean reversion | Payne (2003): low liquidity supply is associated with **larger permanent** price effects, contradicting the predicted direction |
| 2 | Intraday directional seasonality | Breedon & Ranaldo: time-of-day strategies **not profitable after trading costs**, except EUR/USD |

In both cases the literature that would have supplied the origin is also the
literature that documents the effect as unexploitable — and in both cases the
advisor would have carried the candidate forward on recall alone. **The
obituary is in the source; it is not in the headline finding.**

**Standing practice for session 3 and beyond:** no candidate proceeds on a
citation the advisor has produced from memory. The source is retrieved and read,
including its cost and profitability sections, before the candidate is
considered admissible.

---

## Session Two Conclusion

> Four candidate classes were examined under the existing Phase 49
> admissibility requirements. None satisfied all required elements. No sealed
> dataset was accessed, no statistical exploration was performed, and no testing
> criteria were relaxed. The admissible hypothesis space has not been
> demonstrated to be empty. However, the examination has identified substantial
> constraints arising from the available instrument, data structure, transaction
> costs and existing published evidence.

## Purpose of session 3

**Session 3 is not an obligation to produce a candidate.**

Its purpose is to determine whether any **materially different** admissible
hypothesis class remains unexplored — materially different meaning not a
variant of a class already rejected, and not the same mechanism under another
name.

If none does, Phase 49 closes under G.4 with *"No admissible hypothesis
found"*, which establishes what this process produced within its agreed limits
and **does not** establish that systematic trading cannot work, that no edge
exists in `frxGBPJPY`, or that the method is wrong.

**Three sessions are a research limit, not a promise that a trading strategy
will emerge.**

## Status

| | |
|---|---|
| Sessions used | **2 of 3** |
| Candidate classes considered, cumulative | 7 |
| Candidates admitted | **0** |
| D1 / D2 opened | **No** |
| Section C relaxed | **No** |
