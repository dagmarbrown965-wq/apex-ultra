# PHASE 45 BOUNDARY AGREEMENT — AMENDMENT v0.2

_Amends the locked v0.1 (docs/PHASE_45_BOUNDARY_AGREEMENT.md, commits
efff0cc / ededecc). Where this amendment and v0.1 conflict, this
amendment governs. All other v0.1 provisions — including the
no-re-tuning rule and the scope limits — stand unchanged._

## Why this amendment exists

Two defects were found in v0.1 while sizing the data fetch, BEFORE any
code was written or any data collected.

**Defect 1 — the decisive test was the least powerful one.**
v0.1 made "one position at a time" the pass criterion at n >= 1,000.
Under that policy trades are strictly sequential, and with R_100 at
~100% annualised volatility (~0.0178%/s) the expected time for price to
travel to either the -1% stop or the +2% target is roughly
`a*b/sigma^2` ~= 105 minutes. 1,000 sequential trades would therefore
require ~73 days of continuous tick data. The easy-to-power policy was
relegated to "diagnostic" and the hard one made decisive.

**Defect 2 — overlapping signals are not independent observations.**
Under the every-signal policy, signals arrive roughly every 28 seconds
(observed: 1,046 signals across ~490 minutes of Phase 44 sessions)
while each takes ~105 minutes to resolve. That means ~225 positions are
open at once, all resolving against the SAME price path. A naive
binomial confidence interval on n signals would be badly overstated.
The effective independent sample is approximately
`total time span / expected resolution time`, NOT the signal count.

## Amendment 1 — policy roles swapped

- **PRIMARY (decisive): every signal evaluated independently.** This
  measures whether the SIGNAL has predictive value, which is the
  question the phase exists to answer.
- **SECONDARY (reported, not decisive): one position at a time.**
  Reported on whatever sample the data supports, as an executability
  check. If its sample is small it is described as indicative only and
  no pass/fail weight is placed on it.

The v0.1 interpretation rule is retained in amended form: if the
PRIMARY policy shows no edge, the strategy is dead regardless of
execution. A PRIMARY edge that the SECONDARY policy cannot capture is a
capacity finding and still does not pass this phase.

## Amendment 2 — sample requirements restated

The pass bar of **win rate >= 38%** (against a 34.5% break-even after
the 0.2-point spread) is UNCHANGED. What changes is what counts as an
adequate sample:

1. **>= 1,000 resolved signals**, AND
2. **>= 150 independent resolution windows**, where independent windows
   = (total span of tick data) / (105 minutes). This is the binding
   constraint and exists to prevent a precise-looking result built on a
   handful of correlated price paths.
3. Both the naive interval and a window-based estimate of uncertainty
   are reported. If they disagree materially, the wider one governs.

## Amendment 3 — data target

Fetch **>= 14 calendar days** of contiguous R_100 tick history
(~43,200 ticks/day at one tick per 2 seconds; ~605,000 ticks total;
~121 paged `ticks_history` requests at 5,000 per request). This yields
on the order of 43,000 signals and ~190 independent windows, satisfying
both sample requirements with margin.

If Deriv does not serve history that far back, the actual span
obtained is recorded as a stated limitation and the independent-window
count is computed from what was actually retrieved. A short sample
does not get reinterpreted as sufficient.

## Amendment 4 — resolution tail

Signals are generated only from the EARLIER portion of the fetched
series, leaving the later portion as resolution runway, so that late
signals are not systematically recorded as UNRESOLVED. The cut point is
chosen so the runway is at least several multiples of the ~105-minute
expected resolution time. Unresolved signals are excluded from the win
rate and reported as a separate count; if unresolved exceeds 10% of
signals the sample is treated as compromised and more data is fetched.

## Decision log

- 2026-07-24: policy roles swapped (CEO chose option 3 of three
  presented); independent-window requirement added after the advisor
  identified that overlapping positions on a shared price path inflate
  apparent precision; data target set at >= 14 days. All decided
  before any data existed and before W45.0 was planned.
