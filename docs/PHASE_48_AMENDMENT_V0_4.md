# PHASE 48 AMENDMENT v0.4 (2026-08-16)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as already
amended by v0.1 (`bf90beb`), v0.2 and v0.3. Authoritative once committed to
`docs/` on `main`.*

**Made after W48.0a completed and before any provenance measurement exists.**
No provenance result has been produced, so nothing in this amendment can have
been shaped by one. It resolves a question the agreement left open: Section
C.3 requires "an independent public reference in the manner of W47.0" but does
not say what qualifies as one, or what happens when none can be obtained.

---

## Finding that prompted this amendment

W47.0 validated `cryBTCUSD` against Binance BTCUSDT at r = 0.9979. That was
easy because crypto spot data is free, public, and available at matching
granularity. The W48.0a survivor set is not crypto.

Probed 2026-08-16 against the session's Alpha Vantage connector:

| Endpoint | Result |
|---|---|
| `FX_INTRADAY` (15min) | **Premium only.** Returns a subscription notice, not data. |
| `FX_DAILY` | Free. Clean daily OHLC, ~100 bars compact. |
| `INDEX_CATALOG` | US and Cboe indices only — DJI, SPX, NDX, VIX, RUT and Cboe strategy series. **No FTSE, CAC, SMI or Hang Seng at any granularity.** |

So the connector can verify the seven currency crosses only at daily
granularity, and cannot verify the four `OTC_` index products at all.

---

## Correction 1 — what qualifies as a provenance reference

Section C.3 is extended. An acceptable reference must satisfy all of:

1. **Independent of Deriv.** Not derived from, or redistributed by, the
   platform under test.
2. **Publicly documented and retrievable**, so a future reader can obtain the
   same series.
3. **Native granularity of 15 minutes or finer.** Tick or 1-minute data
   resampled to 15-minute bars is acceptable; coarser data is not, per
   Correction 2.
4. **Covering at least 500 matched 15-minute bars** inside the screening
   window.
5. **Retrieval recorded**: source, exact series identifier, retrieval date, and
   file SHA-256, written into the provenance record.

**Resampling rule — binding, to remove implementer discretion.** Where the
reference is finer than 15 minutes:

- Bars align to UTC 15-minute boundaries matching Deriv's candle epochs.
- The bar's close is the last observation at or before the bar's end.
- Where bid and ask are supplied, the mid is used: `(bid + ask) / 2`.
- Bars with no observations are omitted, never interpolated.
- **The alignment convention of Deriv's epoch field — bar-open versus
  bar-close — has NOT been probed and must be established before any
  provenance figure is trusted.** A one-bar misalignment would depress
  correlation and could cause a false rejection.

Candidate sources identified but **not yet probed**: HistData (free 1-minute
FX bars) and Dukascopy (free tick history). Neither has been tested by this
project. Whichever is used, its retrieval must satisfy the five requirements
above.

## Correction 2 — daily granularity is not acceptable

Provenance is verified at the granularity of the intended study. W47.0
established fidelity at 15 minutes because the strategy under test operated on
15-minute bars.

A daily-granularity check would confirm that an instrument's daily moves track
a real market while saying nothing about its 15-minute microstructure — which
is the behaviour any Phase 48 dataset exists to support. Deriv's own
`ticks_history` gaps, quote staleness during thin sessions, and synthetic
smoothing would all be invisible at daily resolution.

The free `FX_DAILY` endpoint is therefore **not** adopted as the provenance
source, and criterion 1's n ≥ 500 and r ≥ 0.95 stand unchanged at 15 minutes.

---

## Correction 3 — disposition of the four `OTC_` index survivors

`OTC_FCHI`, `OTC_FTSE`, `OTC_HSI` and `OTC_SSMI` passed W48.0a independence
but no reference satisfying Correction 1 could be obtained for any of them.

They are recorded as **NOT VERIFIABLE — rejected for Phase 48**, and
explicitly **not** as criterion-1 failures.

The distinction is deliberate. A criterion-1 failure means a correlation was
measured and came in below 0.95 — a statement about the instrument. What
occurred here is that the measurement could not be performed at all — a
statement about available data. Recording the second as the first would
overstate what is known and would wrongly foreclose a later phase that funds an
index data feed.

**Reopenable.** If a reference meeting Correction 1 becomes available for any
of these four, a future phase may screen it under its own pre-registration.
The W48.0a independence figures stand and need not be recomputed.

Ancillary observation, recorded but not relied upon: these are Deriv `OTC_`
products — proprietary constructions rather than exchange feeds — and the
absence of any independent series against which to check them is itself a
reason for caution about founding a year-long study on one.

---

## Resulting candidate pool

Seven currency crosses proceed to W48.0b provenance verification:

`frxGBPJPY`, `frxAUDJPY`, `frxAUDNZD`, `frxAUDCHF`, `frxNZDJPY`,
`frxGBPAUD`, `frxGBPNZD`

If none of the seven clears r ≥ 0.95, **Section C's no-survivors rule
governs**: the phase closes with the finding that no instrument on this
platform could be shown both independent of prior work and faithful to a real
market. No threshold is to be relaxed in response.

---

## What is not changed

Independence ceiling |r| < 0.30; provenance floor r ≥ 0.95; n ≥ 500 matched
bars for provenance and n ≥ 2500 for independence; the two-stage gate order;
the `R_100` exemption; the leg-overlap rule; and the completeness, integrity,
sufficiency, contiguity and seal criteria.

---

## Decision log

* 2026-08-16 — W48.0a closed with 11 survivors. Advisor probed the available
  reference sources and reported that 15-minute FX is paywalled, daily FX is
  free, and no non-US index series is available at all. CEO selected a free
  bulk 15-minute source for the crosses over daily granularity or paid data,
  and rejection over holding or ETF proxies for the indices. Advisor recorded
  the rejection as "not verifiable" rather than "criterion-1 failure", and
  flagged the unprobed Deriv epoch alignment convention as a precondition to
  trusting any provenance figure. No provenance measurement existed when this
  amendment was made.
