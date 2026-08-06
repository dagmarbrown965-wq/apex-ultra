# APEX ULTRA — PHASE 47 CLOSE ASSESSMENT

**Verdict: FAIL — hypothesis not supported.**

_Assessed 2026-08-06 against docs/PHASE_47_BOUNDARY_AGREEMENT.md (v1.0,
commit 121f285), a pre-registration document whose criteria were locked
before any BTC candle was fetched. Verify with
`py -m tools.evaluate_phase47`._

## The hypothesis tested

**Short-term volatility expansion following compression exhibits more
directional persistence than moving-average crossover signals in crypto
markets.**

Proposed after Phases 45 and 46 failed on crossover signals, on the
reasoning that large directional moves frequently begin with volatility
breakouts rather than moving-average crossings, and that the edge — if
any — would come from participating in regime transitions rather than
predicting reversals.

## Result

| Measure | In-sample (75%) | Holdout (25%) |
|---|---|---|
| Trades | 288 | **106** |
| Win rate | 30.21% | 26.42% |
| **Expectancy** | **+0.1307R** | **−0.2119R** |
| **Profit factor** | **1.1496** | **0.7696** |
| Total R | +37.66 | −22.46 |
| Max drawdown | −28.69R | −29.61R |
| Mean bars held | 20.6 | 19.7 |
| Exits: stop / trail | 151 / 137 | 55 / 51 |

Verdict evaluated strictly in order, stopping at first failure:

| # | Criterion | Required | Actual | Result |
|---|---|---|---|---|
| 1 | Holdout sample validity | n ≥ 50 | 106 | **PASS** |
| 2 | Holdout expectancy | > 0.15R | **−0.2119R** | **FAIL** |
| 3 | Profit factor | > 1.25 | not evaluated | — |
| 4 | Stability | ≥ 75% of in-sample | not evaluated | — |

Criteria 3 and 4 were not evaluated. Per Section F, later criteria may
not rescue an earlier failure.

## The central finding: the sign flipped out of sample

**This is the most important result the APEX project has produced, and it
is not about volatility breakouts.**

In-sample, across 288 trades and nine months, the strategy returned
**+37.66R with a profit factor of 1.15**. On its face that is a working
strategy. A researcher without a pre-registered holdout would have
stopped there, concluded the hypothesis was supported, and deployed it.

The holdout returned **−22.46R with a profit factor of 0.77**. The sign
of the edge reversed.

Two readings are consistent with the data and cannot be distinguished
from it:

1. The in-sample result was noise. With a 26–30% win rate and a
   heavy-tailed R distribution (holdout max +9.80R, in-sample max
   +14.59R), a handful of large winners can produce an apparent edge
   that does not persist.
2. A real edge existed in the earlier regime and decayed.

**For the purpose of risking capital, the two readings are equivalent.**

The pre-registered, single-use holdout is what caught this. That
mechanism was specified on 2026-08-06 before any data was fetched,
precisely so this outcome would be detectable rather than flattering.

## The strategy behaved as designed; the prediction was wrong

Worth separating mechanism from result. The trade profile matched the
intended shape closely:

- Low win rate (26.42% holdout), as expected for a trend-following
  breakout system with a 1:2 stop-to-trail structure.
- Median loss −1.09R, clustering tightly at the intended risk unit.
- Winners running far beyond losers: holdout MFE median +1.31R, p75
  +3.22R, max +12.92R.
- Trail activated on 51 of 106 holdout trades, doing its intended job of
  letting favourable moves continue.

The asymmetric payoff structure worked. There simply was not enough
directional persistence after compression to make it profitable.

**This is the hypothesis's known weak point, identified in Section A of
the agreement before testing:** volatility clustering is well established
and concerns MAGNITUDE, not direction. The strategy additionally required
that the direction of the initial break persists — a substantially weaker
claim. The result is consistent with the volatility half being true and
the directional half being false.

## Disclosures and uncertainties

**Close-only execution, both bias directions.** The pre-registration
mandated evaluating stops and trails on bar close only.

- *Favourable:* a bar piercing the stop intrabar but closing back inside
  does not exit, whereas a resting stop order would have filled.
- *Unfavourable:* a bar closing well beyond the stop exits at that close,
  not at the stop. **215 of 394 trades (54.6%) exited worse than −1.05R.**

The unfavourable effect is large and plausibly accounts for a meaningful
share of the negative expectancy. This is a stated uncertainty, NOT a
rescue: the execution model was locked in advance, and revising it after
seeing a result is precisely what the agreement forbids. A future phase
could pre-register intrabar stop simulation and test it honestly on
fresh data.

An earlier advisor claim that close-only "likely biases expectancy
upward" was **retracted during implementation** when synthetic testing
revealed the opposing effect. The net direction is an empirical question
and is not claimed here.

**Other limitations:** cost model frozen at 0.01% round-trip against
~0.0034% observed (conservative by ~3x); overnight funding and stop-fill
slippage unmodelled; spread widening during volatile expansion — the
exact condition this strategy trades into — unmodelled; 165 breakout
signals suppressed by the one-position-at-a-time rule, so the result
describes that constrained strategy rather than the unconstrained signal;
single instrument, single year, single parameter set.

## Data provenance and reproducibility

- **W47.0 gate (passed before any strategy work):** Deriv `cryBTCUSD`
  validated against Binance BTCUSDT — bar-to-bar return correlation
  **0.9979** across 500 matched 15-minute bars, return stdev 0.1654% vs
  0.1658%. The instrument reflects real BTC dynamics, not a synthetic
  construction. Making this the first gate was a CEO instruction and it
  was the right call: had it failed, the phase would have ended in twenty
  minutes.
- **W47.1:** 35,023 candles, 364.996 days. The substitution defence
  (Deriv silently returns current data past the 365-day boundary) fired
  correctly at request 37. Five sub-hour gaps, four on Saturdays —
  maintenance windows, 0.07% of the series.
- **W47.2:** determinism verified by repeated runs producing identical
  `trades_sha256` (`d9445e0d...`). Candle file SHA-256 recorded alongside,
  giving a reproducibility chain that survives future code changes.
- Pre-registered prediction of 360–730 trades: **actual 394** — inside
  the range. 711 episodes started, 559 broke out, 152 expired, 165
  signals suppressed.

## Forbidden responses (binding)

Not permitted in response to this result: changing the compression
threshold, lookback, ATR period, stop or trail multiples, expiry window,
timeframe, or instrument and re-running; or filtering trades post hoc.

**The holdout is spent.** It was single-use by design and has been used.
No further evaluation of this dataset can produce a verdict.

Appendix X variants (2.5 ATR stop, 1-hour timeframe, 5 ATR trail) may be
run on IN-SAMPLE data only and cannot produce a pass, a partial pass, or
any claim about the hypothesis. Their sole output is candidate hypotheses
for future phases requiring fresh data and their own pre-registration.

## Status

Phase 47 is CLOSED. The hypothesis is not supported.

Three strategies have now been tested to pre-registered standards:
crossover on a synthetic index (decisive negative), crossover on EUR/USD
(indeterminate, on break-even), and volatility-compression breakout on
BTC (positive in-sample, negative out-of-sample).

None demonstrated an edge sufficient to justify capital. The cost of
establishing this across Phases 45–47: approximately six weeks, zero
capital risked.

The methodology itself is now demonstrably load-bearing. Phase 47 shows
it can distinguish a strategy that looks profitable from one that is —
which is the distinction that separates disciplined research from
expensive self-deception.
