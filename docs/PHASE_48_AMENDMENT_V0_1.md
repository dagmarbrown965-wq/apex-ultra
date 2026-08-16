# PHASE 48 AMENDMENT v0.1 (2026-08-16)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, commit `7415aa4`).
Authoritative once committed to `docs/` on `main`.*

**Made before any candidate instrument was screened and before any data was
fetched.** No result exists that could have motivated it. This is a defect
correction, not a mid-phase revision.

---

## Defect identified

Section F criterion 2 requires:

> Independence — |Return correlation| vs each previously-used instrument
> **< 0.30**, n ≥ 500 matched bars

Section C.1 names the previously-used instruments as `frxEURUSD`,
`cryBTCUSD`, and `R_100`.

**For `R_100` there are no bars.** All R_100 data held by the project is
tick-level (`engine/output/ticks_R_100_*`, collected 2026-07-24 to 2026-08-04
under Phase 45). Phases 46 and 47 produced 15-minute candle series for EUR/USD
and BTC; Phase 45 worked entirely in ticks. The criterion as written is
therefore unsatisfiable for one of the three instruments it names.

This is a drafting error in v1.0, which assumed comparable series across all
three prior instruments.

---

## Resolution — structural exemption

**`R_100` is exempt from the numeric independence gate.** The exemption is
recorded here with its justification rather than applied silently.

### Justification

Phase 45 established `R_100` as a random number generator, and closed FAIL for
that structural reason: `3b613a1` records no demonstrable edge at 31.78% against
a 34.5% break-even, with the confidence interval entirely below break-even.
The Phase 47 boundary agreement restates the finding plainly — *"it is a random
number generator."*

The independence gate exists to prevent a candidate instrument importing
structure the project has already examined. **An RNG contains no structure to
import.** Its true correlation to any real-market instrument is zero by
construction, and any measured value is sampling noise around zero. Computing
the number would produce a figure that looks like evidence while carrying none.

Resampling the tick series to 15-minute bars was considered and rejected: it
would satisfy the letter of the criterion at the cost of manufacturing a
meaningless statistic, and would additionally constrain candidate screening to
timestamps overlapping 2026-07-24 to 2026-08-04 for no analytical gain.

### What the exemption does not do

It does not weaken the gate. `frxEURUSD` and `cryBTCUSD` — the two instruments
that carry real market structure and that the project has genuinely
examined — remain subject to criterion 2 in full at the < 0.30 ceiling and the
n ≥ 500 matched-bar requirement.

---

## Amended text

Section F criterion 2 is replaced in full by:

> | 2 | Independence | \|Return correlation\| vs **`frxEURUSD` and
> `cryBTCUSD`** < **0.30**, n ≥ 500 matched bars each. **`R_100` is exempt
> per Amendment v0.1** — structurally an RNG, no importable structure, true
> correlation zero by construction. |

Section C.1 is unchanged: `R_100` remains a previously-used instrument and
remains ineligible for selection.

---

## Decision log

* 2026-08-16 — Defect identified by advisor during W48.0 preparation, before
  any candidate was screened. Three resolutions offered: structural exemption,
  tick resampling to satisfy the criterion literally, or removing `R_100` from
  the criterion. CEO selected the structural exemption. Removal was rejected on
  the grounds that it would erase the question from the record; a future reader
  would not know it had been considered. Amendment made with no data in hand.
