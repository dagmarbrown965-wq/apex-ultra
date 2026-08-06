# PHASE 46 BOUNDARY AGREEMENT (v0.1 — LOCKED 2026-08-05)

_Status: authoritative once committed to docs/ on main. Level 2 document
under the AI Company Constitution v1.1. Consistent with, and no weaker
than, the Phase 44 and Phase 45 agreements. The filesystem is the source
of truth._

## Purpose

Phase 45 established that EmaCross 9/21 has no demonstrable edge on
R_100 (win rate 31.78%, CI 31.21–32.35%, entirely below the 34.5%
break-even). R_100 is a random number generator; a trend-following rule
has no persistence to extract from one, so that result was structurally
predetermined.

Phase 46 asks the question that is NOT predetermined:

**Does the same strategy, unchanged, have positive expectancy on a real
market with genuine order flow?**

One variable changes: the instrument. EmaCross stays 9/21. The crossing-
moment logic, the 1:2 risk-reward ratio, both position policies, and the
entire verification discipline stay identical. The bracket is rescaled to
match the new instrument's volatility — see "Bracket" below — and that
rescaling is a design decision made BEFORE any data was evaluated, not a
response to a result.

## Established facts (measured 2026-08-05, before this agreement)

All probed via the existing read-only transport. None assumed.

| Parameter | Value | How established |
|---|---|---|
| Instrument | `frxEURUSD` | `active_symbols` — forex market confirmed available |
| Timeframe | 15-minute candles (`granularity: 900`) | probed |
| History depth | ≥ 300 days, boundary between 300–365 | weekday-corrected probe |
| Per-request cap | 1,000 candles | observed |
| Candle rate | ~76 bars/day of trading time (762 bars / 10.1 days) | measured |
| Per-bar volatility | 0.0353% stdev | measured over 762 bars |
| Time to move 0.2% | ~32 bars ≈ 8.0 hours | derived, matches theory |
| Spread | 0.0069% – 0.0087% of price (0.8–1.0 pips) | 12 live bid/ask samples |
| pip_size | 5 | `active_symbols` |

Two API behaviours that MUST be defended against in code:

1. **Weekend responses are empty by design.** Forex closes Friday
   evening and reopens Sunday evening. `ticks_history` returns
   `{"candles": []}` for weekend timestamps. This is NOT an error and
   NOT history exhaustion. The Phase 45 fetch tool's stop condition
   ("no usable data") would misread it and halt at the first weekend.
2. **Past the history boundary, Deriv SILENTLY RETURNS CURRENT DATA.**
   Requests for 365+ days back returned candles dated ~0.1 days old
   while echoing the requested `end` correctly. A naive paging loop
   would collect thousands of duplicate current bars and believe it had
   years of history. **Every fetched batch must have its returned epochs
   verified against the requested range, and any substituted batch
   discarded and treated as the boundary.**

## Bracket (fixed, declared, NOT tuned)

- Stop: **0.2%** from entry
- Target: **0.4%** from entry
- Ratio: 1:2, identical to Phase 45

Rationale, recorded before testing: R_100's 1%/2% bracket was sized to
an instrument with ~100% annualised volatility. EUR/USD moves ~0.0353%
per 15-minute bar; a 1% stop would take days to resolve. 0.2%/0.4%
preserves the ratio while resolving in ~8 hours, giving comparable trade
frequency and comparable independent-window counts. The bracket is fixed
for the entire phase.

## Cost model

Spread observed between 0.0069% and 0.0087% round-trip. The agreement
adopts **0.01% round-trip** as a conservative stated assumption — above
the worst observed value, biasing against the strategy deliberately.

Net outcomes:
- WIN: +0.4% − 0.01% = **+0.39%**
- LOSS: −0.2% − 0.01% = **−0.21%**
- **Break-even win rate = 0.21 / (0.39 + 0.21) = 35.0%**

Note: samples were taken at ~01:00 UTC (thin Asian session). Spreads
typically tighten during London/New York overlap and widen around news
and rollover. The 0.01% assumption is treated as representative; it is
not claimed to bound every moment.

## Falsification criteria (SET BEFORE ANY DATA IS EVALUATED)

The strategy is judged to have an edge ONLY if ALL hold:

1. **≥ 1,000 resolved signals.**
2. **≥ 150 independent resolution windows**, where windows =
   (total contiguous trading-time span) / (8 hours).
3. **Win rate ≥ 38%** under the PRIMARY policy — clearly above the 35.0%
   break-even rather than within noise of it.

Expected sample from ~300 days: ~22,600 candles, ~1,170 signals
(at the measured 51.8 signals per 1,000 candles), ~900 windows. The
signal count clears the floor by only ~17%; the fetch must therefore
take the FULL available history, not a convenient subset. If the
realised signal count falls below 1,000, the sample is insufficient and
the phase reports that rather than lowering the bar.

If the result is below the bar, the finding is: **EmaCross 9/21 does not
have a demonstrable edge on EUR/USD 15-minute data either.** That
finding is accepted and the phase closes.

## Forbidden responses to a negative result

Carried forward unchanged from Phase 45, and binding here:

- Changing the EMA periods and re-running.
- Changing the bracket ratio and re-running.
- Changing the timeframe and re-running.
- Switching to another currency pair and re-running.
- Filtering signals post hoc by score, regime, session, or time of day.

The 15-minute timeframe was chosen BEFORE any EUR/USD result existed,
because hourly bars would have produced only ~260 signals — a design
decision, not a reaction. Choosing a timeframe after seeing a result
would be curve-fitting. The distinction is whether a result has been
observed; none has.

Any future work in a forbidden direction requires a new phase, a new
agreement, and explicit CEO approval recorded in writing.

## Position policies (unchanged from Phase 45 Amendment v0.2)

- **PRIMARY (decisive):** every resolved signal counted independently.
  Measures whether the SIGNAL has predictive value.
- **SECONDARY (indicative):** one position at a time, chronological.
  Executability check only; carries no pass/fail weight.

If PRIMARY shows no edge, the strategy is dead regardless of execution.
A PRIMARY edge that SECONDARY cannot capture is a capacity finding and
still does not pass.

## Work items

**W46.0 — candle fetch tool.** New file `tools/fetch_candles.py`.
Read-only. Pages `ticks_history` backwards with `style: candles,
granularity: 900`. MUST: verify returned epochs against the requested
range and stop on substitution; treat empty weekend responses as normal
and continue paging past them; sleep between requests; write candles to
disk with a summary recording span, count, gaps, and stop reason.
Nothing under `engine/` is touched.

**W46.1 — signal generation.** Reuse `tools/replay_signals.py` where
possible, adapted for OHLC input (closes drive the strategy; highs and
lows are retained for resolution). The REAL `EmaCross`, `SimpleRegime`,
`DescriptiveBracket`, and `build_signal` are imported verbatim, never
reimplemented. Bracket percentages come from a parameter, not from
`DescriptiveBracket`'s R_100 defaults — the ONLY behavioural difference
from Phase 45, and it is declared here.

**W46.2 — resolution.** Walk forward through candles. Because OHLC gives
intra-bar extremes, barrier detection uses `high` and `low`, not just
`close` — MORE accurate than Phase 45's tick sampling. If a bar's range
spans both barriers, record LOSS (pessimistic; intra-bar path unknown),
and count these cases. Weekend gaps split contiguous blocks; resolution
never crosses a block boundary.

**W46.3 — expectancy.** Apply the 0.01% cost, both policies, naive and
block-based confidence intervals, and report the verdict mechanically
against the criteria above.

## Gates (each work item)

Micro-plan approved in prose before any code; 42.0C regression PASS
(3/3); CP3 PASS with allowlist unchanged; commit diff lists only the
intended files; content probe on a string unique to the new code.

## Standing rules (carried forward)

- No code before a locked micro-plan. Filesystem over chat history.
- Credentials via three separate Read-Host lines then `cls`, screen
  confirmed blank; pastes to chat begin at the `====` banner.
- `git add` with explicit paths, never `-A`.
- Every file install ends with a content probe.
- Scripted anchored edits over manual editing for multi-line changes;
  always re-read the edited region afterward.
- No execution surface is touched. `LIVE_TRADING` stays unset. Live
  orders sent must remain 0.
- Bulk data files are gitignored; summaries are committed.

## What this phase cannot conclude

A positive result would mean EmaCross showed an edge on ~300 days of
EUR/USD 15-minute data under stated cost assumptions. It would NOT
establish that the strategy is profitable in practice, that the result
persists out of sample or in future data, that execution would achieve
the modelled fills, or that the spread assumption holds during news and
illiquid periods. Those are separate questions for separate phases.

A single positive backtest on one instrument over one period is weak
evidence. It would justify further investigation, not capital.

## Decision log

- 2026-08-05: instrument frxEURUSD; timeframe 15-minute (chosen because
  hourly yields only ~260 signals, decided before any result); bracket
  0.2%/0.4% (volatility-matched, 8h resolution, verified); cost 0.01%
  (conservative, above worst of 12 observed samples); break-even 35.0%
  derived; pass bar 38% carried forward from Phase 45's logic of
  requiring clear separation from break-even. All values measured or
  derived before any evaluation data was fetched.
