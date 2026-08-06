# APEX ULTRA — PHASE 46 CLOSE ASSESSMENT

**Verdict: FAIL — edge not demonstrated.**

_Assessed 2026-08-05 against docs/PHASE_46_BOUNDARY_AGREEMENT.md (v0.1,
commit ecbf230) as amended by v0.2 (commit 780aef2). Verify with
`py -m tools.expectancy_candles` against the committed resolutions file._

## The question this phase asked

Phase 45 established that EmaCross 9/21 has no edge on R_100, a random
number generator — a structurally predetermined result. Phase 46 asked
the question that is not predetermined:

**Does the same strategy, unchanged, have positive expectancy on a real
market with genuine order flow?**

One variable changed: the instrument. EmaCross stayed 9/21. The bracket
was rescaled to the instrument's volatility (0.2%/0.4%, ratio preserved),
a design decision recorded before any data was evaluated.

## Answer

No — but the failure is of a different kind from Phase 45's, and the
distinction is the most important finding of this phase.

| Measure | Primary (decisive) | Secondary (indicative) |
|---|---|---|
| Trades | 1,314 | 255 |
| Wins / Losses | 449 / 865 | 86 / 169 |
| Win rate | **34.17%** | 33.73% |
| Naive 95% CI | 31.61% – 36.73% | 27.92% – 39.53% |
| Block-based 95% CI | 31.83% – 37.38% | 29.12% – 40.94% |
| Expectancy per trade | **−0.005%** | −0.0076% |
| Total return | −6.54% | −1.95% |

Reference points:
- **33.33%** — driftless random walk with barriers at −0.2%/+0.4%
- **35.00%** — break-even after the measured 0.01% spread
- **38.00%** — the pass bar, locked before any EUR/USD data existed

## Pre-committed criteria

| Criterion | Required | Actual | Met |
|---|---|---|---|
| Resolved signals | ≥ 1,000 | 1,314 | YES |
| Independent windows | ≥ 150 | 672.2 | YES |
| Win rate (primary) | ≥ 38% | 34.17% | **NO** |

Sample requirements comfortably met. The decisive criterion is not.

## The critical distinction: indeterminate, not disproven

Phase 45's confidence interval on R_100 was **[31.21%, 32.35%]** against
a 34.5% break-even — the entire range below, with margin. That was a
decisive negative: no edge exists, and the reason was structural.

Phase 46's interval is **[31.61%, 36.73%]** against a 35.0% break-even.
**It straddles break-even.** Expectancy of −0.005% per trade is
statistically indistinguishable from zero.

This data is consistent with a small positive edge, no edge, or a small
negative edge. It cannot distinguish between them. The phase fails
because 38% was the pre-committed bar and 34.17% is not 38% — but
"failed to demonstrate an edge" is a weaker claim than "demonstrated no
edge", and the record should not conflate them.

What the result rules out is a LARGE edge. A strategy with genuine
predictive power on a year of data would not sit on break-even.

## Disclosures (both push the true figure downward)

1. **Gap-throughs: 33 signals (2.51% of resolved).** Weekend gaps that
   opened past a barrier were resolved at the BARRIER price to keep the
   arithmetic fixed. In reality a stop gapped through fills worse than
   −0.2%. Measured expectancy is therefore OPTIMISTIC relative to live
   fills. The agreement required this disclosure above a 2% threshold.
2. **Swap/rollover costs are not modelled.** Cross-weekend resolution
   assumes a position can be held through the close; 236 weekend
   crossings occurred. Real overnight financing would reduce returns
   further.
3. **Spread assumed constant at 0.01%.** Measured samples ranged
   0.0069%–0.0087% during a thin Asian session. Real spreads widen
   during news and illiquid periods.

Adjusting for these, the honest reading is that the strategy is
approximately break-even before frictions and negative after them.

## The mid-phase amendment (disclosed in full)

Amendment v0.2 was made AFTER seeing a result, which is the pattern this
project's discipline exists to guard against. It is recorded here in full
because a reader must be able to judge it.

- **Trigger:** the W46.2 run returned **17.84% unresolved**, exceeding
  the 10% threshold that v0.1 itself defined as a compromised sample.
  The trigger was not the win rate.
- **Cause:** v0.1 forbade resolution crossing a contiguous block, a rule
  inherited from Phase 45 where blocks were collection gaps in a 24/7
  synthetic. Applied to a market that closes, it truncated every trade
  still open at a Friday close.
- **Change:** resolution now crosses weekend closures, as a real held
  position would.
- **Effect on the result:** unresolved 17.84% → 0.68%; win rate
  **32.29% → 34.17%** (+1.88 points).
- **Why the number moved:** the 227 previously-truncated signals resolved
  at roughly 43%. This is structural, not noise — trades still open at a
  week's end are the slow ones, and with a target twice as far as the
  stop, slow trades skew toward the target. Truncation was systematically
  discarding winners. The correction moved the result in the honest
  direction.
- **It did not change the verdict.** 34.17% remains below both the 35.0%
  break-even and the 38% bar.

The pre-amendment figures are committed at d78bc8f and restated in the
amendment document so the change remains auditable in perpetuity.

## What was built

- **W46.0** (`tools/fetch_candles.py`, 7e76db5) — paged `ticks_history`
  in candle mode. Two API behaviours were discovered by probing and
  defended against in code: weekend responses are empty by design, and
  **past the history boundary Deriv silently returns current data while
  echoing the requested `end`**. The substitution defence fired correctly
  at request 37, establishing the boundary at exactly 365 days. Without
  it the dataset would have been silently poisoned with duplicate current
  bars. Result: 24,257 candles, 364.99 days — the complete year available.
- **W46.1** (`tools/replay_candles.py`, db5e23f) — drove the real
  `EmaCross` / `SimpleRegime` / `DescriptiveBracket` / `build_signal`
  chain over OHLC closes. Bracket percentages supplied through the
  class's existing constructor parameters; no engine file modified.
  1,323 signals across 56 blocks. Bracket arithmetic verified by hand on
  both a long and a short.
- **W46.2 v2** (`tools/resolve_candles_v2.py`, 8917fed) — cross-weekend
  resolution using intra-bar highs and lows, more accurate than Phase
  45's tick sampling. 1,314 resolved, 9 unresolved, 0 same-bar ambiguous.
- **W46.3** (`tools/expectancy_candles.py`, 088a358) — costs applied,
  both policies, naive and block-based intervals, mechanical verdict.

## What this phase does NOT conclude

- It does not conclude that EUR/USD is unbeatable, or that EMA crossovers
  never work. It tested one strategy, one parameter set, one bracket, one
  timeframe, one year, one pair.
- It does not conclude the strategy has negative expectancy. The interval
  straddles break-even; the honest statement is that no edge was
  demonstrated.
- A single backtest on one instrument over one period would be weak
  evidence even had it passed. It would justify further investigation,
  not capital.

## Forbidden responses (v0.1, unchanged and binding)

Not permitted in response to this result: changing EMA periods, changing
the bracket ratio, changing the timeframe, switching currency pair, or
filtering signals post hoc. Each is curve-fitting. Any such work requires
a new phase, a new agreement, and explicit CEO approval recorded in
writing.

The 15-minute timeframe was chosen before any EUR/USD result existed,
because hourly would have yielded only ~260 signals. That was design.
Choosing differently now would not be.

## Status

Phase 46 is CLOSED with a negative finding.

Two instruments have now been tested to the same standard. R_100 returned
a decisive negative for structural reasons. EUR/USD returned an
indeterminate result sitting on break-even. In neither case did EmaCross
9/21 demonstrate an edge that would justify risking capital.

Cost of learning this across Phases 45 and 46: approximately five weeks,
zero capital.
