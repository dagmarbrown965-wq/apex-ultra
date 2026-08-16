# PHASE 48 AMENDMENT v0.2 (2026-08-16)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, commit `7415aa4`) as
already amended by v0.1 (commit `bf90beb`). Authoritative once committed to
`docs/` on `main`.*

**Made before any candidate instrument was screened and before any data was
fetched.** No result exists that could have motivated it. This is a sequencing
correction, not a relaxation: **no threshold is changed and both gates remain
binding.**

---

## Ambiguity identified

Section C states:

> **The provenance gate runs first**, per the W47.0 precedent — a CEO
> instruction in Phase 47 that the close document credits as correct, since
> failure there ends the phase in twenty minutes rather than after a full
> fetch.

That instruction was issued in Phase 47 under a **single-candidate** design:
`cryBTCUSD` had already been chosen, one external reference (Binance BTCUSDT)
was obvious, and running provenance first genuinely could have ended the phase
in twenty minutes.

Phase 48 is a **multi-candidate sweep**. Section C determines the instrument by
rule from `active_symbols`, which on this platform is of order fifty to one
hundred eligible symbols. Applying provenance first at that scale requires
selecting an appropriate independent public reference for every candidate
before any is eliminated.

**Selecting an external reference is a discretionary act.** It requires judging
which public series genuinely corresponds to a given Deriv instrument, at
matching granularity and timestamps. Performing that judgement eighty times, on
symbols most of which will be discarded, is both expensive and an invitation to
exactly the carelessness the provenance gate exists to detect.

The independence gate has the opposite character: it is fully automatic,
requires no external data source and no judgement, and runs entirely against
series already on disk (`candles_frxEURUSD_900_*`, `candles_cryBTCUSD_900_*`).

---

## Resolution — two-stage screening

W48.0 is split into two stages, executed in this order:

| Stage | Work | Gate | Character |
|---|---|---|---|
| **W48.0a** | Independence screen across all eligible `active_symbols` | Section F criterion 2 | Automatic; no external data; no discretion |
| **W48.0b** | Provenance verification on stage-a survivors only | Section F criterion 1 | Requires a deliberately chosen reference per candidate |

**Both gates remain binding and unchanged.** A candidate must pass criterion 2
at |r| < 0.30 and criterion 1 at r ≥ 0.95 to be selected. Reordering affects
which gate eliminates a candidate first; it cannot allow a candidate to be
selected that either gate would have rejected.

Section F's rule that no later criterion may rescue an earlier failure is
unaffected: it governs the acceptance hierarchy applied to a chosen dataset,
not the order in which candidates are screened.

### Effect on the record

Section C requires every instrument screened to be recorded with its
correlations and outcome, including rejections.

Under two-stage screening, **candidates rejected at stage a will carry
independence correlations but no provenance figure.** This is intended and is
stated here so that a future reader does not read the absence as an omission.
Stage-b survivors carry both.

### Retained for the single-candidate case

Where a phase evaluates a single pre-identified instrument, the W47.0 ordering
stands: provenance first, on the fail-fast reasoning the Phase 47 close
document credits. This amendment applies only to multi-candidate sweeps.

---

## Amended text

Section C's ordering paragraph is replaced in full by:

> **Gate order.** For a multi-candidate sweep, the independence gate runs first
> across all eligible symbols (W48.0a), and the provenance gate runs on the
> survivors (W48.0b) — per Amendment v0.2, on the grounds that independence is
> automatic and provenance requires a discretionary per-candidate reference
> selection. Both gates are binding; neither may be waived. For a
> single-candidate evaluation the W47.0 ordering stands: provenance first.

Section H work items W48.0 is replaced by:

> | W48.0a | Independence screen across all eligible `active_symbols`; all
> candidates logged with correlations and outcome, including rejections |
> Section F criterion 2 |
> | W48.0b | Provenance verification on stage-a survivors; reference source
> named and recorded per candidate | Section F criterion 1 |

---

## Tooling constraint

The stage-a screening tool must compute **only** the statistics on the Section
E allowlist: matched-bar counts and return correlations. It must not compute or
report the candidate's own return standard deviation, autocorrelation, trend or
volatility measures, or any indicator series — a candidate examined that way is
contaminated before it is even selected.

Return standard deviation remains allowlisted at stage b, where it is computed
**against the external reference** as part of the provenance comparison, in the
manner of W47.0.

The tool is committed to `main` before it is executed.

---

## Decision log

* 2026-08-16 — Ambiguity identified by advisor during W48.0 preparation, after
  reading `tools/fetch_candles.py` and establishing that candidate enumeration
  would proceed from `active_symbols`. Raised before any candidate was screened
  and before any tool was run. Resolution proposed by advisor and ratified by
  CEO. No threshold altered; no gate waived.
