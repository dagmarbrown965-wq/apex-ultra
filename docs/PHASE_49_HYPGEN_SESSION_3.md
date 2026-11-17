# Phase 49 — hypothesis generation, session 3 of 3

**2026-11-17.** Conducted under `docs/PHASE_49_BOUNDARY_AGREEMENT.md` §G.2.

**Outcome: five candidate classes proposed, none admitted. No admissible
hypothesis produced. Phase 49 closes under G.4 — see
`docs/PHASE_49_CLOSE.md`.**

---

## Compliance

| Requirement (G.2) | Status |
|---|---|
| Session 3 of 3 | ✔ |
| Duration ≤ 2 hours | ✔ — closed early, see below |
| **D1 opened** | **NO** |
| **D2 opened** | **NO** |
| Statistical exploration performed | **NO** |
| Implementation or backtesting | **NO** |
| Section C relaxed | **NO** |
| Every candidate recorded including rejections | ✔ |

Session preconditions (G.1) run and passed at `6b59137`: clean tree apart from
the seventeen known untracked `engine/output/` artifacts, M0 regression PASS
(3/3), CP3 PASS, `_last_sign` HIT, `RECORD INTEGRITY: PASS` over 45 documents
and 52 cited paths.

**Closed with time remaining, deliberately.** Approximately 27 minutes of the
two hours were used, measured against a **nominal** 12:45 start (Jamaica local
time); approximately 93 minutes went unused. The session was closed because its
shortlist was exhausted, not because the clock expired. *Searching for a sixth class simply
because time remained was considered and rejected: that is the mechanism by
which a manufactured candidate gets made.*

**Spacing limitation, same as session 2.** This session began immediately after
an extended block of prop-firm rules verification rather than from anywhere
new. Session 2 recorded the same defect about itself. G.2 caps duration, not
spacing, so this is compliant — and it is recorded as a limitation on the
session's independence rather than excused.

**Proposer and reviewer again not independent.** The advisor proposed all five
classes; the CEO reviewed. This is the third consecutive session with that
concentration.

## Brief

Set at the close of session 2 and narrowed in this session before any class was
examined:

> **An obligation to transact that is not publicly scheduled, has a defensible
> directional implication, and leaves an observable opportunity in GBP/JPY
> 15-minute OHLC data.**

The narrowing came from the pattern of the seven prior rejections. Five died on
behavioural or liquidity grounds; the two with a **procedural** origin — the
WM/Reuters fix and weekend gaps — died on *density*, not on theory. The target
was therefore obligation-driven flow: a counterparty compelled to transact
regardless of price, since compelled flow should survive competition where
mistake-driven flow is arbitraged away.

**The "not publicly scheduled" qualifier is load-bearing and was added for
cause.** The 16:00 London fix *is* obligation-driven flow and it died precisely
because its timing is public, which is what permits anticipation. Obligation
alone is insufficient.

---

## Classes proposed

| # | Class | Obligation | Disposition |
|---|---|---|---|
| 1 | Volatility-triggered deleveraging of carry positions | Risk limits force exposure cuts as volatility rises | **Not established** — see below |
| 2 | Margin-call cascades / crash risk | Forced liquidation | Rejected on **density**, on grounds established in sessions 1–2 |
| 3 | Option dealer gamma hedging | Delta-hedging is mechanical | Rejected on **element 2** and **constraint 4** |
| 4 | Swap / rollover financing at 17:00 NY | Financing is charged | Rejected — **publicly scheduled** |
| 5 | Sovereign reserve / SWF rebalancing | Mandate-driven | Rejected — unobservable, insufficient density |

**Classes 2–5 were rejected without reopening their grounds.** Each dies on a
constraint already established and recorded in sessions 1 or 2 — density for 2
and 5, directional unobservability plus external-data dependence for 3, public
scheduling for 4. Re-deriving a known rejection is not what the final session
is for. They are recorded as considered so that the record is not a list of
survivors.

---

## Class 1 — volatility-triggered deleveraging of carry positions

**The hypothesis considered:** GBP/JPY is a carry pair funded in yen. Leveraged
holders operate under volatility-based risk limits, so rising realised
volatility *obliges* them to cut exposure, which means selling GBP/JPY. The
trigger is price-driven rather than calendar-driven; the direction is fixed by
which currency is the funding leg; realised volatility is computable from the
permitted candles.

### Sources retrieved and read

**Retrieved and read by the CEO in this session, not independently verified by
the advisor.** This is recorded because the standing practice adopted in
session 2 requires that a source be read before a candidate proceeds, and the
provenance of that reading belongs in the record.

- **Menkhoff, Sarno, Schmeling & Schrimpf (2012)**, *Carry Trades and Global
  Foreign Exchange Volatility*, Journal of Finance 67(2), 681–718.
  `https://openaccess.city.ac.uk/id/eprint/3391/1/CTVOL_R3_v4_paper.pdf`
  Monthly portfolio formation, monthly excess returns, sample Dec 1983 –
  Aug 2009. High-interest-rate currencies perform poorly when unexpected global
  FX volatility rises. **Costs are handled**: bid-ask deducted on portfolio
  entry and exit, ~30% monthly turnover, annualised excess returns above 5%
  after costs. Those are *monthly portfolio-level* costs.
- **Brunnermeier, Nagel & Pedersen (2009)**, *Carry Trades and Currency
  Crashes*, NBER Macroeconomics Annual 23.
  `https://www.nber.org/system/files/working_papers/w14473/w14473.pdf`
  Negative conditional skewness in investment currencies; carry losses coincide
  with reductions in speculative positions; funding constraints amplify moves
  through forced liquidation. Daily exchange-rate changes, quarterly skewness
  estimates, weekly and quarterly return distributions. **No cost-adjusted
  intraday trading strategy and no execution-cost analysis.**

### Rejected — the mechanism is established at the wrong horizon, and the bridge is missing

The sources establish:

> funding constraints + adverse conditions → carry-position reductions →
> potentially amplified currency movements

The hypothesis requires:

> rising realised **GBP/JPY** volatility → forced selling of GBP/JPY →
> persistent downward movement over a **15-minute** horizon

**Neither paper establishes the second relationship.** Specifically, neither
demonstrates that *instrument-specific realised volatility* substitutes for
global FX volatility, VIX, funding liquidity, or observed speculative
positioning. **That is a missing theoretical bridge, not a missing parameter**,
and element 2 cannot be satisfied by assuming it.

Not established either way: whether GBP/JPY currently carries an interest
differential wide enough for the mechanism to bite. The question became moot and
was not pursued.

### The retail forced-liquidation route — examined and separately unestablished

Pursued because Japanese retail margin traders are a documented population
under a genuine, price-triggered, unscheduled obligation.

- **BoJ Review 2016-E-5**, *Recent Trends in FX Margin Trading in Japan*
  (August 2016). `https://www.boj.or.jp/en/research/wps_rev/rev_2016/data/rev16e05.pdf`
- **BoJ Review 2023-E-7**, *Retail Foreign Exchange Margin Trading in Japan*
  (September 2023). `https://www.boj.or.jp/en/research/wps_rev/rev_2023/data/rev23e07.pdf`

The obligation is documented. 2016-E-5, verbatim: *"a yen rally has sometimes
been accelerated by a forced liquidation of positions under loss cutting
rules."* Loss-cut executes when *"the customer does not deposit the required
amount by the deadline."* Maximum leverage 25×; average leverage 6.3 in Q2 2014
falling to 4.6 in Q1 2016.

Three findings break it for this instrument:

1. **The direction is contested at source.** 2016-E-5: *"Japanese FX margin
   traders tend to take the contrarian trading strategy"* and are *"contrarians
   who contain FX rate fluctuations, except in cases of dramatic FX rate
   swings."* That is the opposite sign to a crowded-carry-unwind story outside
   stress episodes. The same paper separately describes structural
   *"short-yen/long-foreign currencies positions"* held for swap carry, so both
   signs are present and nothing selects between them in advance — the failure
   that killed candidate A in session 1.
2. **GBP/JPY is undocumented.** USD/JPY is ~25% of retail volume in 2012 and
   ~75% in 2022. GBP/JPY appears in a chart legend in both papers with **no
   share stated anywhere in either**. The obligated population's activity in the
   only instrument this project can test is unquantified.
3. **No intraday evidence.** 2023-E-7 has none — monthly, quarterly and annual
   series only. 2016-E-5 has one three-hour window, 07:00–10:00 JST on
   11 January 2016.

Neither paper claims retail flows are predictable or exploitable. The nearest
statement is 2016-E-5 footnote 18 — *"It is said that there are yen-buying flows
that aim to induce loss-cut of Japanese FX margin traders"* — which the paper
presents as unsourced and does not test.

---

## The Osler finding — recorded, NOT carried forward

A sub-line of class 1 produced the only genuine research insight of the
session. It is recorded in full because it is a real result, and it is recorded
as **not carried forward** because it fails on two independent grounds.

**Source, retrieved and read in this session by the advisor:**

- **Osler, C. L. (2002)**, *Stop-Loss Orders and Price Cascades in Currency
  Markets*, Federal Reserve Bank of New York Staff Report 150; published in
  Journal of International Money and Finance.
  `https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf`
  Minute-by-minute Reuters quotes, January 1996 – April 1998, dollar-mark,
  dollar-yen and dollar-pound, New York hours 09:00–16:00. Order-cluster
  evidence from the Royal Bank of Scotland order book, August 1999 – April 2000,
  9,655 orders.

### What it establishes — the direction problem candidate A died on is soluble from public data

Verbatim:

> *"executed stop-loss sell orders cluster just below round numbers; stop-loss
> buy orders cluster just above round numbers"*

while take-profit orders *"cluster more strongly at the exact round numbers …
and have no tendency to cluster above or below such numbers."*

> *"The tendency to reverse course at round numbers remains statistically
> significant less than thirty minutes."*

> *"the average exchange-rate movement upon crossing a round number remains
> statistically significant for at least two hours."*

**Crossing versus reversing is observable in 15-minute candles.** Session 1
rejected candidate A because *"nothing publicly observable selects between"*
reversal and continuation. This selects between them with no order-book access.

Density is not the problem either: *"rates crossed round numbers on the order of
five times per day in the sample period"*, against the 0.56/day floor.

**And the cost arithmetic does not obviously fail.** The reported effect is
*"dollar-yen moves by 0.0130 percent more after crossing a round number than
after reversing course at a round number."* GBP/JPY was 210.576 at 17:55 UTC on
2026-11-17 (Alpha Vantage spot), so the project's observed 1.3-pip round-trip
cost is 0.013 ÷ 210.576 = **0.0062%**. The documented 15-minute differential of
**0.0130%** is roughly 2.1× that cost.

**This is recorded precisely because it is inconvenient.** The advisor expected
this class to die on cost as intraday seasonality did in session 2, and it does
not.

### Rejected — ground 1: Section C element 3 (exploitable in advance)

Osler's conclusions state the clusters *"can be rationally anticipated by market
participants."*

Round numbers are the most public conditioning variable available: identifying
them requires no feed, no data purchase and no inference. The effect was
documented in a Federal Reserve staff report in 2002 on 1996–98 data, and has
had twenty-eight years of exposure to anyone willing to code it. Sessions 1 and
2 treated source age as a plausibility argument rather than a measurement, and
that remains true here — **but the plausibility is materially worse for an
effect whose conditioning variable is free to observe than for one requiring
proprietary order flow.**

Three further weaknesses, each independent:

- **The measured quantity is not a tradable return.** 0.0130% is a difference in
  conditional means between two mutually exclusive event populations. No
  position earns a difference-in-means; the event type is known only after it
  has occurred, and the expected onward movement is a small fraction of the
  25-pip stop the cost assumption rests on. Converting the statistic into a
  per-trade expectancy requires assumptions the paper does not supply.
- **GBP/JPY is not in the sample** — dollar-mark, dollar-yen, dollar-pound. The
  pound was also the one pair where the reversal effect failed significance
  (marginal significance 0.179). This is the second time a candidate's
  supporting literature excludes the only instrument available.
- **The author disclaims the causal step.** *"the statistical analysis is
  actually silent about the existence of any causal connection"*, and *"Because
  of data limitations — in particular, insufficient data on large, executed
  stop-loss orders — we cannot yet look directly at price cascades."* No trading
  strategy is tested, no profitability is reported, and the paper contains no
  transaction-cost analysis of any kind.

### Rejected — ground 2: out of scope for session 3

**This is candidate A re-specified, not a materially different class.** Session
3's purpose, as agreed, is to determine whether a class remains unexplored that
is *"not a variant of a class already rejected, and not the same mechanism under
another name."* The standing safeguard forbids candidate resurrection by
relabelling.

The argument against that reading was put and is recorded: session 1 logged A as
*"rejected as specified, not refuted as a class"*, A's rejection ground was
element 6, no project data has been observed, and re-specification from a source
not previously read is hypothesis formation rather than curve-fitting.

**The CEO ruled: record the finding, do not resurrect candidate A.** Both
grounds stand; either alone is sufficient.

### What this rejection does NOT establish

- It does **not** establish that round-number price response has been disproven,
  or that competition has eliminated it. Element 3 is answered here by a
  plausibility argument and the paper's own anticipation statement, not by
  measurement.
- It does **not** establish that the crossing-versus-reversing distinction is
  invalid. That distinction is a real published result and is the most useful
  thing this session produced.
- The finding is preserved here deliberately, so that a future phase operating
  under different origin constraints does not have to rediscover it.

---

## Methodological lesson — now demonstrated three times

**A documented market effect is not necessarily a tradable market edge, and the
obituary is in the source rather than in the headline finding.**

| Session | Candidate | Killed by |
|---|---|---|
| 1 | Liquidity-conditional mean reversion | Payne (2003): low liquidity supply is associated with **larger permanent** price effects, contradicting the predicted direction |
| 2 | Intraday directional seasonality | Breedon & Ranaldo: time-of-day strategies **not profitable after trading costs**, except EUR/USD |
| 3 | Round-number response, via Osler | The paper states the clusters *"can be rationally anticipated by market participants"*, tests no strategy, and analyses no costs |

**A new variant of the lesson, specific to this session:** a publicly observable
conditioning variable is the *weakest possible* basis for element 3. The easier
an effect's trigger is to see, the stronger the prior that it has already been
competed away. Candidates whose conditioning variable is free tend to look
*better* on observability (constraint 4) and *worse* on exploitability (element
3), and the second consideration should be applied first because it is cheaper
to evaluate.

---

## Session Three Conclusion

> Five candidate classes were proposed under the narrowed brief and examined
> under the existing Phase 49 admissibility requirements. Four were rejected on
> grounds already established in sessions one and two. The fifth was examined
> against its primary sources, which establish the proposed mechanism at
> monthly, weekly and daily horizons but do not establish it at the fifteen-
> minute horizon this project can test, and do not establish that
> instrument-specific realised volatility substitutes for the risk measures
> those sources actually use. A sub-line produced a genuine and previously
> unrecognised result — that crossing and reversing at round numbers have
> distinguishable subsequent price behaviour, observable without order-book
> access — which is recorded but not carried forward, being both outside this
> session's scope and independently deficient on element 3. No sealed dataset
> was accessed, no statistical exploration was performed, and no testing
> criteria were relaxed. The session was closed with time remaining because its
> shortlist was exhausted.

## Status

| | |
|---|---|
| Sessions used | **3 of 3** |
| Classes proposed this session | 5 |
| Previously-established rejections reused without reopening | 4 |
| Candidate classes considered, cumulative | **12** |
| Candidates admitted | **0** |
| D1 / D2 opened | **No** |
| Statistical exploration | **No** |
| Section C relaxed | **No** |
| Implementation or testing | **No** |
| Session time used | ~27 of 120, nominal 12:45 start; ~93 unused by decision |

The Osler round-number re-specification is recorded as a variant of candidate A
and is **not** counted as a new class in the cumulative figure.

Phase 49 closes under G.4. See `docs/PHASE_49_CLOSE.md`.
