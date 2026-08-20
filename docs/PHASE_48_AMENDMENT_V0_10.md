# PHASE 48 AMENDMENT v0.10 (2026-08-19)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as already
amended by v0.1–v0.9 (`065d326`). Authoritative once committed to `docs/` on
`main`.*

**Made after the W48.1 D1 fetch and BEFORE the W48.2 seal.** It corrects a gap
in the Section E allowlist and discloses a breach of that allowlist which has
already occurred.

---

## Disclosure first — the allowlist was breached

On 2026-08-19, immediately after the D1 fetch, the following were computed on
`candles_frxGBPJPY_900_1755657580_1787193000.jsonl`:

- `min(close)` = 197.528
- `max(close)` = 219.602
- the first two and last two records were printed in full

**None of these is on the Section E allowlist**, which is stated to be
exhaustive. They were computed at the advisor's instruction, one exchange after
the advisor described a seal asserting that no forbidden statistic had been
computed.

The breach is disclosed rather than absorbed. The seal for D1 must record it.

**Assessment of harm.** An annual price range and four boundary records are
about the weakest price statistics obtainable. They convey level and gross
amplitude and nothing about distribution, autocorrelation, volatility
clustering, or any temporal structure a strategy could be fitted to. The
advisor's judgement is that the dataset's usefulness as a clean holdout is not
materially impaired. That judgement is recorded so a future reader can
disagree with it rather than discover it.

---

## The gap this exposed

Section D.2's substitution defence verifies **epochs**, not **content**. It
establishes that the bars returned fall inside the requested range. It cannot
establish that the bars belong to the instrument requested.

That gap became concrete at D1: `frxGBPJPY` returned **24,257 bars over 364.993
days**, identical to the bar count and span of Phase 46's `frxEURUSD` series.
The match is benign — every `frx` pair shares one trading calendar and one
365-day boundary — but nothing on the allowlist could distinguish "the right
instrument" from "another instrument with the same session structure."

This project's standing rule is that every file install ends with a content
probe on a string only the correct version contains. Data files had no
equivalent.

---

## Correction — instrument identity check, added to the allowlist

The Section E allowlist gains one item, **bounded exhaustively**:

> - **Instrument identity check:** the first close, the last close, the minimum
>   close and the maximum close of the series, together with the first and last
>   raw records. These four numbers and two records may be computed and recorded
>   for the sole purpose of confirming that the served instrument is the
>   instrument requested, by comparison against the price level of an
>   independent reference. **Nothing further may be derived from them** — no
>   range-derived volatility measure, no drawdown, no comparison of ranges
>   across periods, no use in any hypothesis.

Rationale: an instrument-identity check is a **provenance** operation, not an
analytical one. It answers "is this the thing I asked for", which is the same
class of question as the substitution defence and the SHA-256, and it is the
only check capable of catching a served-wrong-instrument error. Excluding it
left the acquisition unable to verify its own subject.

The bound matters more than the addition. Four numbers and two records suffice
to distinguish GBP/JPY near 200 from EUR/USD near 1.10. Anything beyond that is
analysis and remains forbidden.

## Applied retrospectively to D1

The statistics already computed fall exactly within the item now added, and are
recorded in the D1 seal as an instrument identity check together with this
amendment's disclosure that they were computed before the amendment existed.

The check succeeded on its own terms: 197.528–219.602 against a July reference
range of 213.08–219.59 and an independent Alpha Vantage daily envelope of
210.54–220.64 confirms GBP/JPY and excludes any pair quoted near unity.

---

## Unchanged

Everything else on the allowlist, and the entire forbidden list — return
autocorrelation at any lag, volatility clustering measures, ATR or any
indicator series, compression-episode or signal counts, drawdown or trend
statistics, plotting the price series, and any backtest, exploratory or
otherwise. The enforced-unread seal, the commit-before-read audit rule, and all
Section F criteria stand.

---

## Decision log

* 2026-08-19 — D1 fetched (24,257 bars, 364.993 days, substitution defence
  fired at request 37). Advisor instructed a content probe to rule out a
  served-wrong-instrument error prompted by the exact bar-count match with
  Phase 46's EUR/USD series, then recognised the probe was outside the Section
  E allowlist. Breach disclosed, harm assessed, and the underlying gap —
  no allowlisted means of verifying instrument identity — corrected by a
  bounded addition rather than by widening the allowlist generally. Raised
  before the D1 seal was written.
