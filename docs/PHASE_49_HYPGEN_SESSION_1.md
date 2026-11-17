# Phase 49 — hypothesis generation, session 1 of 3

**2026-11-17.** Conducted under `docs/PHASE_49_BOUNDARY_AGREEMENT.md` §G.2.

**Outcome: three candidates considered, three rejected. No admissible
hypothesis produced.**

---

## Compliance

| Requirement (G.2) | Status |
|---|---|
| Session 1 of 3 | ✔ |
| Duration ≤ 2 hours | ✔ |
| **D1 opened** | **NO** |
| **D2 opened** | **NO** |
| Statistical exploration performed | **NO** |
| Implementation or backtesting | **NO** |
| Every candidate recorded including rejections | ✔ |

**No dataset was opened and no statistic was computed on any project data at
any point in this session.** Every rejection below rests on reasoning and
published literature, not on measurement. The session preconditions (G.1) were
run and passed at `8f875e1`.

## Methodological note — proposer and reviewer were not independent

All three candidates were proposed by the advisor and reviewed by the CEO. The
Section C admissibility test asks whether a statement would have been written in
the same form if the data did not exist; when one party proposes and the other
ratifies, that test is weaker than it appears.

It was partly mitigated by the CEO applying a uniform three-question standard to
every candidate — mechanism independently supported, prediction observable in
the available data, falsifiable after realistic costs — which caught an
asymmetry in the advisor's reasoning (see A below). The concentration is
recorded rather than resolved.

## Filter applied before any candidate was considered

Derived from `docs/PHASE_49_ECONOMIC_FLOOR.md` and Sections C and E:

- **Density:** ≥ 0.56 trades/day to reach n ≥ 50 on D2's 88.708 days. This
  eliminated every calendar-event mechanism before examination — month-end
  rebalancing (~12/year), quarter-end (4), weekend gaps (52), scheduled central
  bank meetings (8).
- **Cost:** ≥ 0.052R at a 25-pip stop on the observed 1.3-pip spread; the ratio
  worsens sharply for shorter stops.
- **Distinctness (element 4):** not a crossover rule, not a compression
  breakout. Phases 45–47 and F.0.
- **Origin (element 1):** statable without reference to any price series this
  project holds.

---

## Candidate A — Round-number order clustering

**Origin claimed:** published research. Osler (2003), order clustering at round
numbers. *Citation produced from the advisor's general knowledge and NOT
verified against the source in this session.*

**Mechanism:** take-profit orders cluster at round numbers producing reversal;
stop-loss orders cluster just beyond them producing continuation.

### Rejected — Section C element 6 (falsification criteria)

**The mechanism predicts both directions and nothing publicly observable
selects between them in advance.** Reversal at the level and continuation
through it are opposite behaviours. Osler had dealer order-book data and could
see which order type dominated; this project has candles. A hypothesis that
cannot state its direction before the event is not falsifiable.

### Correction recorded — the advisor's first rejection was wrong

The advisor initially rejected A on the grounds that the order-clustering
*mechanism* is unobservable in candle data. **The CEO rejected that reasoning**,
correctly: candle data can test a narrowly defined round-number price-response
hypothesis even though it cannot establish the mechanism behind it. The
mechanism justifies the prediction; the test measures the prediction.

**This correction mattered beyond A.** Applied consistently, the observability
standard would have killed candidate B more severely — B's chain is time-of-day
→ liquidity → inventory-driven flow, two proxy layers against A's one. The
advisor had applied a stricter standard to A than to the candidate it preferred.

**The standard adopted:** Q2 asks whether the data observes what the hypothesis
*predicts*, not whether it observes the mechanism.

### What is NOT established

That round-number effects have been disproven, or that competition has
eliminated them. The age of the source is a plausibility argument, not a
measurement. **A is rejected as specified, not refuted as a class.**

---

## Candidate C — Fixing-window flows

**Origin claimed:** market structure plus published research on the WM/Reuters
16:00 London fix. *The 2015 widening of the fixing window from one to five
minutes is cited from the advisor's general knowledge and NOT verified against
a source in this session.*

**Mechanism:** real-money hedging demand concentrates at a publicly known time,
producing transient price pressure.

### Rejected — on density and weakened predictability

- The daily version faces the most intense institutional competition of any
  moment in the FX day, and the fixing-window reform was *intended* to reduce
  exactly the predictability the hypothesis depends on.
- The version with the strongest mechanical basis — month-end hedging
  rebalancing, directionally forecastable from the month's equity returns — is
  **~12 events per year** and fails the density filter outright. It cannot
  populate a D2 sample under Section E.

### What is NOT established

That the fixing-window reform eliminated all exploitable fixing-related
effects. **It is evidence against the original rationale, not proof of
elimination.** The institutional-competition objection is likewise a
plausibility argument, not a measured result. Rejection is **provisional** on
these grounds and decisive only on density for the month-end variant.

---

## Candidate B — Liquidity-conditional mean reversion

**Origin claimed:** market-structure reasoning from inventory microstructure.

**Mechanism:** a dealer absorbing an order shades quotes to offload inventory,
producing transitory price impact that reverts — as distinct from
information-driven impact, which persists. The hypothesis conditioned on fixed
clock windows (Tokyo lunch, Tokyo–London handover, late New York) as a
pre-registerable proxy for thin liquidity.

**Survived Q2 and Q3's specifiability.** "A move of ≥X over window W during
clock-window T retraces ≥Z within V" is fully observable in 15-minute candles
and is falsifiable.

### Rejected — Section C element 2 (theoretical reasoning must support the predicted direction)

**The available literature points the opposite way in precisely B's
conditions.**

Sources supplied and linked by the CEO in this session:

- **Payne (2003)** — during periods of low liquidity supply, individual trades
  had **larger permanent** price effects.
  `https://www.sciencedirect.com/science/article/pii/S0022199603000035`
- **Bjønnes & Rime (2005)** — found **both** inventory-control and information
  effects in FX dealer transactions, and inventory control was not necessarily
  expressed through dealers' own prices as traditional models predict.
  `https://www.sciencedirect.com/science/article/abs/pii/S0304405X04001503`
- **Ranaldo & Santucci de Magistris (2022)** — FX price impact increases as
  market depth falls; illiquidity substantially greater during night hours.
  `https://doi.org/10.1016/j.jfineco.2022.09.004`

Element 2 requires the theoretical reasoning to support the **direction**
predicted. B predicts reversion in thin conditions; Payne reports larger
permanent impact in thin conditions. This is not theory being silent on which
mechanism dominates — it is the best available evidence contradicting the
predicted direction.

The Ranaldo finding compounds the economic objection independently: the
conditions proposed as the source of the opportunity are also the conditions of
widest spread, so edge and cost arise together.

### The inversion was considered and is not carried forward

Continuation on thin liquidity **is** supported by Payne, and inverting here
would be legitimate: F.0 forbids changing direction after observing a result,
and no result has been observed. Following the literature before any data is
hypothesis formation, not curve-fitting.

It is not carried forward because it is weak on two counts: the cost problem
doubles — entering at the widest spreads while chasing a move already made —
and distinctness from Phase 47 becomes strained, since compression-then-breakout
and thin-liquidity-then-continuation are different conditioning variables
producing the same trade shape. It would be expected to fail element 4.

**If proposed in a later session it is a distinct candidate requiring
independent review under Section C in full.** It does not inherit B's
groundwork, and it is not a relabelling of a rejected candidate.

---

## Structural finding

**Candle-only data cannot distinguish temporary liquidity-driven price pressure
from permanent information-driven price discovery.**

That distinction is the load-bearing element of most market-structure
mechanisms — it is precisely what separates "this will revert" from "this will
continue." Where a mechanism's directional prediction turns on it, the available
data cannot justify the direction, and Section C element 2 cannot be satisfied.

This restricts the range of market-structure hypotheses whose directional
predictions can be justified and evaluated with what this project holds.

**What this finding does NOT establish:**

- It does **not** establish that all market-structure hypotheses are
  inaccessible to this project.
- It does **not** justify weakening Section C, lowering the admissibility
  requirements, or relaxing any element.
- It does **not** establish that no edge exists in `frxGBPJPY`.

It is a constraint on a class of candidates, identified by reasoning, and it
should inform where session two looks rather than how strictly it judges.

---

## Direction for session 2

**Not** an immediate search for another market-structure mechanism.

First examine whether legitimate hypothesis origins exist that do **not**
depend on identifying hidden order flow, and do **not** turn on distinguishing
temporary from permanent price impact. If that class is empty, that is itself
the finding and it arrives two sessions earlier than it otherwise would.

The purpose is not to find something that passes. It is to establish whether
something genuinely defensible exists.

## Status

| | |
|---|---|
| Sessions used | **1 of 3** |
| Candidates considered | 3 |
| Candidates admitted | **0** |
| D1 / D2 opened | **No** |
| Section C relaxed | **No** |

Three reasoned rejections, each recorded with its grounds and with the limits
of what those grounds establish. Under G.4 the phase may close with "No
admissible hypothesis found" if sessions 2 and 3 produce the same outcome, and
that result is accepted in advance.
