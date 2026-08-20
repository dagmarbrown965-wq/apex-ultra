# PHASE 48 — D1 SEAL (W48.2)

**Sealed 2026-08-19.** Establishes the D1 dataset under
`docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as amended v0.1–v0.10
(`d678e97`).

---

## 1. Dataset identity

| Field | Value |
|---|---|
| Instrument | `frxGBPJPY` |
| Granularity | 900 s (15-minute bars) |
| File | `engine/output/candles_frxGBPJPY_900_1755657580_1787193000.jsonl` |
| Byte size | 2,196,813 |
| **SHA-256** | **`E9DF6A4E2CDBBAAC8C9B738314E288E2AB006075768B9F0FA8904A521DEFEE39`** |
| Bars | 24,257 |
| First epoch | 1755657580 |
| Last epoch | 1787193000 |
| Span | 31,535,420 s = 364.993 days |
| Fetched | 2026-08-19, `tools/fetch_candles.py` reused verbatim per Section D.1 |
| Summary | `engine/output/candles_frxGBPJPY_900_1755657580_1787193000_summary.json` |

Selection provenance: instrument chosen by rule at `578231b` under Amendment
v0.8 — lowest independence max|r| among candidates clearing the provenance
floor.

## 2. Acceptance against Section F

| # | Criterion | Requirement | Measured | Result |
|---|---|---|---|---|
| 1 | Provenance | r ≥ 0.95, n ≥ 500 | **+0.99224**, n = 1990 | **PASS** |
| 2 | Independence | \|r\| < 0.30, n ≥ 2500 | **0.0548** (max vs frxEURUSD / cryBTCUSD), n = 2766/2768 | **PASS** |
| 3 | Completeness | ≥ 23,529 bars (v0.9) | **24,257** — 100.0% of the 24,257-bar benchmark | **PASS** |
| 4 | Integrity | Substitution defence fired, boundary measured, gaps inventoried | Fired at request 37; 55 gaps inventoried | **PASS** |
| 5 | Sufficiency | Supports a future n ≥ 50 holdout | 24,257 bars over a full year | **PASS** |
| 6 | Contiguity | D2 only | not applicable to D1 | — |
| 7 | Seal | This document | — | **established** |

Criteria evaluated in order; none was reached by rescuing an earlier failure.

## 3. Integrity detail

**Substitution defence fired**, as Section D.2 requires it must:

```
request 37: requested_end 1755657579, returned_newest 1787193000,
            excess_seconds 31535421  (365.0 days newer)
            batch discarded; history boundary reached
```

Request 37 is the same request number at which the defence fired in W47.1 and
in the Phase 46 fetch — consistent boundary behaviour across three fetches.

**Gaps:** 55 over granularity; largest 184,500 s (51.25 h) after epoch
1755895500. Weekend closures for a five-day instrument, expected under
Section D.3 and reported, never smoothed or backfilled. Empty responses: 0.

## 4. Instrument identity check (Amendment v0.10)

| Measure | Value |
|---|---|
| First close | 198.692 |
| Last close | 215.530 |
| Minimum close | 197.528 |
| Maximum close | 219.602 |

Confirms GBP/JPY. Corroborated against the July 2026 HistData reference range
(213.08–219.59) and an independent Alpha Vantage daily envelope
(210.54–220.64). Excludes any pair quoted near unity.

This check was prompted by D1's bar count and span being **identical** to Phase
46's `frxEURUSD` series (24,257 bars, 364.99 days). The match is benign — all
`frx` pairs share one trading calendar and one 365-day boundary — but the
substitution defence validates epochs, not content, and could not have
distinguished the two.

**Disclosure, per Amendment v0.10:** these statistics were computed **before**
v0.10 added them to the Section E allowlist. At the moment of computation they
were outside an allowlist stated to be exhaustive. The breach, the harm
assessment, and the corrective amendment are recorded in
`docs/PHASE_48_AMENDMENT_V0_10.md`. Nothing has been derived from them.

## 5. Known artifact — clipped first bar

`first_epoch` 1755657580 is **not** a multiple of 900. Every subsequent bar is
boundary-aligned; the second bar is 1755657900, only **320 seconds** later.
The first bar is a partial, clipped at the edge of available history.

**Systematic, not specific to D1.** Phase 46's `frxEURUSD` begins at 1754473235
(635 s off-boundary) and Phase 47's `cryBTCUSD` at 1754498185 (385 s
off-boundary). All three of this project's candle fetches carry a clipped first
bar. The record contains no prior mention of it.

**Binding on any future use of this dataset:** the first bar must be excluded,
or any calculation crossing it must account for a 320-second step labelled as a
900-second one. The W48.0b tooling is unaffected — its matched-returns logic
requires exactly 900 s spacing and therefore skips the pair automatically — but
a backtest assuming uniform spacing would not.

Effect on Phase 46 and 47 conclusions: one bar in 24,257 and one in 35,023
respectively. Immaterial to those verdicts. Recorded for completeness, not as a
challenge to them.

## 6. Seal

The data file is **not opened again** until a hypothesis is pre-registered
against it. Only this document and the fetch summary are readable.

Enforcement is by audit trail, per Section E as amended:

1. Any script that reads
   `candles_frxGBPJPY_900_1755657580_1787193000.jsonl` **must be committed to
   `main` before it is executed.** Git history is the complete log of
   everything that has touched the sealed data.
2. A future phase pre-registering against this dataset cites the SHA-256 above
   and states the commit range within which no reading script was committed.
3. **If the hash cannot be reproduced, this dataset's provenance is void and it
   may not serve as a holdout.**

**Seal established at the commit adding this document.** No forbidden statistic
has been computed on this dataset, subject in full to the disclosure in
section 4.

Forbidden until pre-registration, unchanged: return autocorrelation at any lag,
volatility clustering measures, ATR or any indicator series,
compression-episode or signal counts, drawdown or trend statistics, plotting
the price series, and any backtest, exploratory or otherwise.

## 7. Outstanding for Phase 48

- **W48.4 — D2 fetch**, scheduled ~2026-10-30 (75-day interval from lock per
  Section B). Same instrument, continuing forward from D1's last epoch.
  Contiguity is Section F criterion 6.
- **W48.5 — D2 seal and phase close assessment.**
- Token `apex_trade_demo_5` expires 2026-11-17, clearing the D2 fetch by 18
  days. Scheduled check 2026-11-05.
