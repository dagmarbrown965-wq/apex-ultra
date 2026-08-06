# APEX ULTRA — CEILING CHECK RECORD: BTC mean-reversion after large moves

**Result: not distinguishable from zero. Closed without a phase.**

_Recorded 2026-08-06. A ceiling check is a cheap descriptive screen run
BEFORE designing a pre-registered phase, to establish whether the
available magnitude could plausibly clear costs. It is not a phase, does
not produce a verdict on an edge, and cannot pass anything. Reproduce
with `py -m tools.ceiling_btc_reversion`._

## Hypothesis

Large short-term moves in crypto overshoot fair value because of
cascading liquidations of leveraged positions, then partially revert as
the forced flow exhausts.

**Structural origin, stated independently of any prior result:** crypto
markets carry high retail leverage with clustered stop levels. Forced
liquidation is a mechanical, non-discretionary flow — it is not a
prediction about trader intent. This mechanism is distinct from the
volatility-compression breakout tested in Phase 47, which assumed
directional *persistence*; this assumes the opposite, *reversion*. The
hypothesis would have been worth stating whether or not Phase 47 had
passed, which is what the Phase 47 legitimacy test requires.

## Method

Descriptive measurement only. No strategy, entries, stops, or expectancy.

- Data: 35,023 committed 15-minute `cryBTCUSD` candles, 364.996 days
  (fetched W47.1, provenance validated against Binance at 0.9979
  return correlation).
- Threshold: |log return| ≥ 2σ, σ measured over the full sample.
- Measured: signed forward return over the next 1, 2 and 3 bars, where
  POSITIVE means price moved back against the original move.
- Split by direction, to test the liquidation-asymmetry prediction.

## Findings

σ = 0.2370%; threshold = 0.4741%. **1,759 qualifying bars** (5.02%),
848 up and 911 down.

| Lookahead | n | Mean | Median | Win rate | mean/se |
|---|---|---|---|---|---|
| 1 bar | 1,759 | +0.0107% | +0.0520% | 56.9% | **+0.97** |
| 2 bars | 1,759 | +0.0091% | +0.0398% | 53.4% | +0.61 |
| 3 bars | 1,759 | +0.0080% | +0.0311% | 51.8% | +0.46 |

By direction, at 1 bar: after UP moves +0.0159% (mean/se +1.11); after
DOWN moves +0.0058% (mean/se +0.35).

Distribution at 1 bar: p25 −0.2056%, p75 +0.2560%, min −4.1659%,
max +2.4696%.

## Interpretation

**The headline number fails the significance screen.** Mean/se of +0.97
is within one standard error of zero. With n = 1,759 the sample is not
underpowered — a small real effect would have registered. The mean is
consistent with noise.

**Two features of the data are nonetheless coherent and worth recording.**

1. **Median is five times the mean** (+0.0520% vs +0.0107%), with a
   56.9% win rate. Most large moves are followed by a small reversion,
   while a minority are followed by large continuations that drag the
   mean down. The left tail is nearly twice the right (−4.17% vs
   +2.47%). That is the shape a cascade-that-keeps-cascading would
   produce.
2. **Win rate decays monotonically with horizon** — 56.9% → 53.4% →
   51.8% — which is what a short-lived real effect looks like. Pure
   noise would show no ordering.

**Neither observation rescues the hypothesis, for a reason that is
arithmetic rather than statistical: a strategy captures the mean, not
the median.** Individual trades are drawn from the full distribution
including its left tail. The mean is +0.0107%, roughly 2% of the
original move, against a 0.0048% spread measured in CALM conditions —
and these signals fire immediately after a 0.47% move, when spreads
widen and slippage is at its worst. Realistic entry cost plausibly
exceeds the entire gross figure.

**The structural prediction was not confirmed.** Liquidation cascades
were expected to produce asymmetry, with stronger reversion after
down-moves. The data shows the opposite ordering (up-moves reverting
more), and neither direction is significant. The mechanism proposed as
the reason for the edge did not show up in the measurement.

## Why this closes without a phase

A positive mean within one standard error of zero, of a magnitude
comparable to unmodelled costs, is precisely the profile that has
convinced generations of traders to build systems on noise. Phase 47
already demonstrated on this project what happens when a marginal
in-sample result meets fresh data: the sign flipped.

**A recognised temptation, explicitly declined.** A stop-based variant
that truncated the left tail could in principle convert the median into
capturable expectancy. Designing that variant *now* would originate in
this output rather than independently of it, which the Phase 47
legitimacy test forbids. If such a design is ever pursued, its reason
must be statable without reference to this measurement.

## Cost to the dataset

**This check read the entire BTC year.** σ, the threshold, and every
forward return were computed across the full series. No portion of this
dataset is unseen, so it can no longer supply a clean holdout.

Any future phase on this hypothesis would require one of:
1. **Forward-collected data.** Deriv serves a rolling 365 days; waiting
   three months yields ~8,600 fresh 15m bars this screen never saw.
2. **A different instrument.** The cascade mechanism is not BTC-specific,
   so testing ETH or another pair under the same pre-registered rules is
   legitimate rather than a workaround.
3. Running on this data with the contamination disclosed — **rejected**.
   It looks reasonable and quietly degrades the standard.

## Methodological note: the ceiling-check pattern

This is the second hypothesis closed by cheap arithmetic rather than a
built phase. The first was BTC perpetual funding carry, killed in ten
minutes when measured funding of ~3.1% annualised gross proved negative
after retail costs — below a pre-registered "not worth further work"
threshold.

The pattern substantially increases search throughput: most hypotheses
can be screened in minutes rather than weeks, so many more can be tested
per unit of effort. In a search with a low expected hit rate, that
matters more than the quality of any individual test.

**Standing practice: run the ceiling check first.** Build a phase only
for hypotheses that survive it.

## Status

Closed. Hypothesis not supported; no phase designed; no capital at risk.

Running total: five hypotheses tested to an honest standard, no
validated edge. Three closed by full pre-registered phases (45, 46, 47),
two closed by ceiling check (funding carry, mean-reversion).
