# PHASE 48 AMENDMENT v0.9 (2026-08-19)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as already
amended by v0.1–v0.8 (`5ea4066`). Authoritative once committed to `docs/` on
`main`.*

**Made after W48.0b closed and BEFORE the W48.1 D1 fetch has been run.** No D1
bar count exists. The instrument is selected (`frxGBPJPY`, `578231b`) but no
acceptance measurement has been taken against it.

---

## Defect in Section F criterion 3

As written:

> | 3 | Completeness | Bar count **≥ 97%** of arithmetic expectation for the
> span; no single gap > 6h on a 24/7 instrument |

For a five-day market the arithmetic expectation over 365 days is 480
fifteen-minute bars per FX week (Sunday 17:00 ET to Friday 17:00 ET = 120 hours)
× 52.14 weeks ≈ **25,029 bars**.

**The project's own validated forex year fails that test.** Phase 46's
`candles_frxEURUSD_900_1754473235_1786008600.jsonl` holds **24,257 bars over
364.99 days** — the dataset on which an entire phase was conducted and closed.
24,257 / 25,029 = **96.9%**, below the 97% threshold.

The arithmetic expectation is the faulty part, not the data. It ignores public
holidays, early closes, and the fact that the tradable FX week is not five
24-hour days. A criterion that rejects a known-good year is mis-calibrated.

This was found before D1 was fetched. Had it been found after, any adjustment
would have been indistinguishable from moving a threshold to admit a result.

---

## Correction — completeness for a five-day instrument

Section F criterion 3 is replaced, for **five-day (forex) instruments**, by:

> | 3 | Completeness | Bar count **≥ 97% of 24,257**, i.e. **≥ 23,529 bars**
> for a ~365-day span, where 24,257 is the observed bar count of the validated
> Phase 46 `frxEURUSD` 365-day series. All gaps inventoried. Weekend gaps are
> expected and are not defects; intra-session gaps are reported and counted. |

The benchmark is an **observed** forex year from this project's own verified
data, not an arithmetic idealisation. For a span materially shorter or longer
than 365 days, the benchmark scales pro rata by span in days.

**For 24/7 instruments the original clause stands unchanged**, including the
6-hour single-gap rule. That rule does not apply to a five-day instrument,
where a ~48-hour weekend gap is normal and expected — as Section D.3 already
states.

### Why 97% of an observed year rather than a looser figure

97% of 24,257 permits a shortfall of 728 bars, about 7.6 trading days'
worth, which is ample room for holidays and short feed outages while still
rejecting a materially truncated series. Tightening it further would risk
rejecting a good year over a holiday calendar; loosening it would let a
genuinely incomplete fetch through.

---

## Unchanged

Provenance floor r ≥ 0.95 at n ≥ 500. Independence ceiling |r| < 0.30 at
n ≥ 2500. Integrity: substitution defence must fire and the boundary be
measured. Sufficiency: bar count must support a future n ≥ 50 holdout.
Contiguity for D2. Seal requirements. Selection rule per v0.8. Section C's
no-survivors rule.

The acceptance hierarchy and the rule that no later criterion may rescue an
earlier failure both stand.

---

## Decision log

* 2026-08-19 — W48.0b closed with `frxGBPJPY` selected. Advisor computed the
  arithmetic expectation implied by criterion 3 for a five-day market and found
  it would reject Phase 46's own validated EUR/USD year at 96.9%. Raised and
  corrected before the D1 fetch, so that no D1 bar count existed at the time
  the threshold was set. Benchmark re-grounded on observed data from this
  project rather than an idealised week.
