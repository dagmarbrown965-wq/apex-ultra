# PHASE 47 BOUNDARY AGREEMENT (v1.0 — LOCKED 2026-08-06)

*Status: authoritative once committed to docs/ on main. Level 2 document
under the AI Company Constitution v1.1. This is a PRE-REGISTRATION
document: every value in Sections C, D, E and F was fixed before any
backtest was run. The filesystem is the source of truth.*

\---

# SECTION A — PURPOSE

## The question

Phases 45 and 46 tested EmaCross 9/21 — a moving-average crossover — on a
synthetic index and on EUR/USD. Both failed. R\_100 failed decisively
(31.78%, CI entirely below break-even) for structural reasons: it is a
random number generator. EUR/USD failed indeterminately (34.17%, CI
straddling break-even), consistent with a simple public rule capturing
nothing after costs in a highly efficient market.

Phase 47 tests a conceptually different hypothesis on a different market.

## Hypothesis (stated before any test)

**Short-term volatility expansion following compression exhibits more
directional persistence than moving-average crossover signals in crypto
markets.**

Reasoning:

* Crypto trades 24/7 and spends extended periods in low-volatility
consolidation.
* Large directional moves frequently originate from volatility breakouts
rather than from moving-average crossings.
* The edge, if any, comes from participating in a regime transition
(compression → expansion), not from predicting reversals.

## The hypothesis's known weak point, stated in advance

Volatility clustering is among the most robust empirical regularities in
finance: low-volatility periods are followed by low-volatility periods,
and compressions do resolve into expansions. **That established fact
concerns magnitude, not direction.** This strategy additionally assumes
the direction of the initial break persists — a substantially weaker
claim with far less empirical support.

The edge, if it exists, lives entirely in that directional persistence.
The well-supported volatility half of the hypothesis must not be allowed
to lend credibility to the unsupported directional half.

## What a positive result would and would not mean

A pass would mean the configuration below produced positive expectancy on
one year of one instrument under stated cost assumptions, with the most
recent quarter held out. It would justify further investigation on other
instruments and periods. **It would not justify capital.**

\---

# SECTION B — DATA \& COST MODEL

## Instrument provenance (W47.0 gate — PASSED before this agreement)

`cryBTCUSD` on Deriv was validated against Binance BTCUSDT before any
strategy work began, to establish it reflects real market dynamics rather
than a synthetic construction:

|Measure|Result|
|-|-|
|Matched 15m timestamps|500|
|**Bar-to-bar return correlation**|**0.9979**|
|Deriv return stdev|0.1654%|
|Binance return stdev|0.1658%|
|Level difference (median)|−0.0425% (Deriv below Binance)|
|Level difference (range)|−0.1580% to −0.0123%|

Conclusion: Deriv reproduces real BTC dynamics. The persistent \~0.043%
level discount is a constant pricing offset and does not affect a
strategy trading changes. Volatility clustering present in BTC will be
present in this data.

## Data

|Parameter|Value|Source|
|-|-|-|
|Instrument|`cryBTCUSD`|active\_symbols|
|Timeframe|15-minute candles (`granularity: 900`)|—|
|History available|365 days (hard boundary)|probed|
|Expected candles|\~35,000 (24/7 market)|arithmetic|
|15m return volatility|\~0.165% per bar|measured, 500 bars|

**API behaviours defended against in code** (established in Phase 46 and
re-confirmed for BTC): past the 365-day boundary Deriv silently returns
CURRENT candles while echoing the requested `end`. Every fetched batch
must have returned epochs verified against the requested range; any
substituted batch is discarded and treated as the boundary.

Unlike EUR/USD, BTC trades continuously — no weekend gaps are expected.
Any gap found is a data anomaly and must be reported, not smoothed.

## Cost model — FROZEN

Measured 2026-08-06 from 6 live bid/ask samples: 0.0019%–0.0048%
round-trip, mean \~0.0034%.

**The agreement adopts 0.01% round-trip** — approximately triple the
observed mean and double the worst observation. Deliberately
conservative, and **frozen**: it may not be revised during the phase for
any reason, including to make a result clear a threshold.

At a 1.5×ATR stop of roughly 0.15–0.18% of price, costs are \~6% of the
risk per trade under the frozen assumption, \~2% under observed values.

Not modelled, and disclosed as limitations: overnight funding on held
positions, slippage on stop fills, and spread widening during volatile
expansion — the exact conditions this strategy trades into. **Measured
expectancy is therefore optimistic relative to live execution.**

\---

# SECTION C — PRIMARY CONFIGURATION (verdict-producing)

**This section defines the single configuration whose result constitutes
the verdict of Phase 47. Nothing in Appendix X can produce a pass.**

|Element|Value|
|-|-|
|Instrument|cryBTCUSD|
|Timeframe|15-minute (primary)|
|Compression metric|ATR(14) percentile|
|Lookback|96 bars (24 hours)|
|Compression threshold|ATR percentile < 20th|
|Entry trigger|First close beyond frozen compression range|
|Setup expiry|4 bars after episode ends|
|Initial stop|1.5 × ATR(14) at entry|
|Trail|3 × ATR(14), activating at +1R|
|Position policy|One at a time, no pyramiding|

## Justification of each choice (theoretical, not empirical)

**ATR over Bollinger bandwidth.** Bandwidth is the standard deviation of
closes; ATR incorporates each bar's high, low, and prior close. In 24/7
crypto a bar can travel 0.5% and close flat — bandwidth records that as
quiet, ATR as active. The hypothesis concerns volatility; ATR measures
volatility, bandwidth measures a correlate. Secondary: ATR is the unit of
stop placement, so entry and risk share dimensions.

**ATR(14).** Wilder's original period. Chosen because it is the field
default; deviating would require a justification not available before
testing, and inventing one would be the first step toward fitting.

**96-bar lookback (24 hours).** Crypto has genuine diurnal structure —
Asian, European and US sessions differ in participation. A shorter
lookback would flag routine session quiet as compression; a longer one
would blur regime changes. One full day is the shortest window containing
a complete cycle.

**20th percentile.** Must be tight enough to identify genuine compression
and loose enough to yield a testable sample. At 10th, episodes become
rare and the sample collapses; at 30th, "compression" describes ordinary
conditions. 20% is the standard convention for unusually-low-but-not-
extreme, and the roundest defensible value in the usable range.

*Acknowledged open question, raised in protocol review and NOT resolved
here:* whether expectancy increases monotonically with compression
extremity. Testing 10/15/20/25/30 to find out would be mining on a sample
too small to distinguish discovery from noise. 20% is locked; monotonicity
is a question for a future phase with its own data.

**Close beyond the consolidation range, not beyond a band.** A Bollinger
band is a statistical construct — exceeding 2σ says something about a
distribution. A consolidation range is structural: it marks where orders
accumulated during the quiet period. If regime transitions have
directional persistence, it is because supply at that level was
exhausted, not because a standard-deviation threshold was crossed.
**Close, not touch**, filters wicks; on 15-minute bars a wick is often a
single large order rather than a regime change.

**1.5 × ATR initial stop.** The stop must sit beyond ordinary noise and
inside the move being captured. 1.0 ATR is inside a single average bar's
range. Beyond 2.0 ATR, more of the anticipated expansion is consumed
proving the entry wrong. A move of 1.5 ATR against the entry is evidence
the breakout failed — which is what a stop should encode.

*Counter-argument recorded, from protocol review:* successful breakouts
frequently retest the range by 1–2 pre-compression ATR before continuing,
so 1.5 ATR may systematically convert valid retests into losses. This is
the strongest objection to the configuration. It is not resolved by
widening the stop here — a wider stop mechanically raises win rate while
lowering R-multiples, and which dominates cannot be known without the
test we cannot run first. The objection is carried into Appendix X as a
labelled hypothesis.

**3 × ATR trail, activating at +1R.** The initial stop asks "was I wrong
immediately?"; the trail asks "has the expansion ended?" A trail as tight
as the entry stop would exit on the first pullback within a continuing
move — cutting exactly the trades the hypothesis says should run.
Activation at +1R prevents the trail from *widening* risk: without it,
governance would transfer to the 3 ATR trail the moment price moved 1.5
ATR favourably, loosening the effective stop from −1R to −1.5R at
precisely the wrong moment.

**15-minute primary.** Compression-expansion is a short-horizon
microstructure phenomenon: order-book depletion and repricing occur over
minutes to hours. On 1h bars a full compression-and-breakout would occupy
3–4 bars, too coarse to identify the transition. Arithmetic agrees: 1h
yields \~8,760 bars/year and too few episodes to test; 15m yields \~35,000.

**Note on a justification deliberately struck.** An earlier draft
justified the 1.5/3.0 structure partly by "comparability with Phases
45–46." That was decoration and has been removed: those phases both
*failed*, so their 1:2 structure carries no demonstrated merit, and
importing it would be researcher inertia rather than reasoning. The stop
and trail stand on the noise-versus-signal argument alone.

\---

# SECTION D — IMPLEMENTATION FREEZE

No ambiguity is permitted. These rules are exhaustive; anything not
stated here is a defect in this agreement, to be resolved by amendment
before testing, never by implementer discretion.

1. **Compression condition:** ATR(14) percentile over a rolling 96-bar
window < 20%.
2. **Episode start:** the first bar whose ATR percentile qualifies.
3. **Episode end:** the first bar whose ATR percentile does not qualify.
4. **Range:** `max(high)` and `min(low)` of the episode's qualifying bars
ONLY. Non-qualifying bars never extend the range.
5. **Entry:** the first bar that CLOSES beyond the frozen range — above
`max(high)` for a long, below `min(low)` for a short.
6. **Expiry:** if no breakout close occurs within 4 bars after the
compression episode ends, the setup expires and the range is
discarded.
7. **Position policy:** one position at a time. No pyramiding. Signals
arising while a position is open are ignored, not queued.
8. **Initial stop:** 1.5 × ATR(14) measured at entry, fixed for the life
of the trade unless superseded by the trail.
9. **Trail:** the 3 × ATR(14) trailing stop is **inactive until the
position reaches +1R (1.5 × ATR in unrealised profit). Once
activated, it ratchets only in the favourable direction and may not
widen risk.**
10. **Bar-close basis:** entries, trail updates and exits are all
evaluated on bar close. No intra-bar logic. This matches the entry
rule and avoids untestable path-dependence.
11. **ATR at entry is frozen** for that trade's stop and trail distances;
it is not recomputed as the trade progresses.
12. **Unresolved trades:** a position still open when the dataset ends is
recorded as UNRESOLVED, excluded from expectancy, and reported.

\---

# SECTION E — EVALUATION RULES

## Split

**75/25 chronological.** In-sample: days 1–274. Holdout: the most recent
\~91 days. Most-recent-as-holdout simulates having built the strategy in
the past and deployed it forward; a holdout placed earlier would let
later in-sample data leak knowledge of the holdout regime.

**The holdout is touched ONCE, by the primary configuration only. A
second look makes it in-sample and voids the phase.**

## Metrics (all reported for in-sample and holdout separately)

Because the strategy is deliberately low-win-rate and high-payoff, win
rate is descriptive only and carries no pass/fail weight. The Phase 45/46
38% bar does NOT transfer.

* Trade count
* Win rate (descriptive)
* **Expectancy in R** (mean R-multiple per trade)
* **Profit factor** (gross wins ÷ gross losses)
* Maximum drawdown (in R)
* **Maximum adverse excursion** (MAE) distribution
* **Maximum favourable excursion** (MFE) distribution
* **Full R-multiple distribution**
* &#x20;Unresolved trade count, \*\*and their unrealised R at the dataset
* &#x20; boundary\*\* (individually and as a distribution). Unresolved trades are
* &#x20; excluded from expectancy, but under a trailing exit they skew toward
* &#x20; winners still running, so their unrealised R must be reported for a
* &#x20; reader to assess exclusion bias.

## Predictions recorded in advance (falsifiable)

Estimated \~2–4 compression episodes per day, roughly half producing a
range break → **\~1–2 trades/day → \~270–550 in-sample, \~90–180 holdout.**

*(Note: an earlier estimate of 35–60 holdout trades assumed EUR/USD-like
bar counts; BTC trades 24/7, roughly doubling available bars. The higher
figure follows from that correction.)*

If realised counts differ substantially from this range, that is itself
evidence about how well the mechanism is understood, and must be
reported.

\---

# SECTION F — SUCCESS / FAILURE / INCONCLUSIVE CRITERIA

## Sample validity tiers (holdout trade count)

|n|Status|
|-|-|
|n < 30|**Insufficient** — no verdict is issued|
|30 ≤ n < 50|**Exploratory only** — cannot pass|
|n ≥ 50|**Evaluable**|

## Success hierarchy — evaluated strictly in order

1. **Sample validity:** holdout n ≥ 50
2. **Positive expectancy:** holdout expectancy > 0.15R per trade
3. **Profit factor:** holdout profit factor > 1.25
4. **Stability:** holdout expectancy ≥ 75% of in-sample expectancy

**Failing any criterion ends the evaluation. Later criteria may not be
used to rescue a result that failed an earlier one.** A strong profit
factor does not excuse an insufficient sample; strong in-sample results
do not excuse holdout failure.

## Interpretation of a negative result

Given the expected sample size, a marginal negative must be reported as
**"not demonstrated"**, not "rejected." Only a result that is both
evaluable (n ≥ 50) and clearly negative supports rejecting the
hypothesis.

## Forbidden responses to a negative result

Carried forward from Phases 45 and 46 and binding here. Not permitted:
changing the compression threshold, lookback, ATR period, stop or trail
multiples, expiry window, timeframe, or instrument and re-running; or
filtering trades post hoc by time of day, session, direction, or any
other attribute.

Any such work requires a new phase, a new agreement, fresh data, and
explicit CEO approval recorded in writing.

## Acknowledged residual risk: researcher prior leakage

The values in Section C were chosen by an advisor with general knowledge
of what tends to appear in trading literature. That knowledge is not
neutral. The protection is not that the choices are unbiased — it is
that they are locked before data, the holdout is single-use, the cost
model is frozen, and the reasoning is written here where it can be
attacked. It was attacked during protocol review; the resulting
corrections (Section D in full, trail activation at +1R, the metric set,
the tiered sample rule, and the removal of the "comparability"
justification) are incorporated above.

\---

# APPENDIX X — EXPLORATORY GRID (non-verdict)

**Nothing in this appendix can produce a pass, a partial pass, or any
claim about the hypothesis. Its sole output is hypotheses for future
phases, each requiring fresh data and its own pre-registration.**

Exploratory runs execute on **in-sample data only**. They may never touch
the holdout.

|Variant|Change from primary|Purpose|
|-|-|-|
|X1|Initial stop 2.5 × ATR|Tests the retest-tolerance hypothesis raised during protocol review|
|X2|Timeframe 1 hour|Tests whether the effect is timeframe-specific|
|X3|Trail 5 × ATR|Tests whether the trail truncates continuing moves|

If a variant outperforms the primary configuration, that is **not a
result**. It is a candidate hypothesis for a subsequent phase, to be
pre-registered and tested on data not used here. Reporting an exploratory
variant as though it were a finding voids the phase.

\---

## Decision log

* 2026-08-06: W47.0 provenance gate passed (return correlation 0.9979
against Binance) before any strategy design. Hypothesis proposed by
CEO. Primary configuration proposed by advisor with theoretical
justification for each parameter. Protocol reviewed and criticised;
advisor conceded implementation under-specification (Section D adopted
as written from review), trail activation ambiguity (+1R rule),
incomplete pass criteria (metric set and tiered sample rule adopted),
and one weak justification struck. Advisor held on the 20th percentile,
recording monotonicity as an open question rather than testing it.
Structure separated into verdict-producing agreement and non-verdict
appendix at CEO direction. All values locked before implementation.

