# PHASE 48 AMENDMENT v0.3 (2026-08-16)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, commit `7415aa4`) as
already amended by v0.1 (`bf90beb`) and v0.2. Authoritative once committed to
`docs/` on `main`.*

**Made AFTER the first W48.0a screen was run and its results seen.** This is
disclosed prominently because Phase 47's forbidden-responses section exists to
prevent exactly this move. The defence offered below is not that the timing is
innocent — it is that both corrections address defects in the criterion itself,
that the first is purely restrictive, and that the second is applied
symmetrically to every candidate rather than only to those that failed.

The superseded screen is retained at
`engine/output/screening_w48_0a_1786008600.json` and is not deleted. It records
41 candidates evaluated and 17 survivors under the original criterion.

---

## Correction 1 — structural leg overlap

### Defect

Section F criterion 2 measures linear correlation of returns. For currency
crosses this is not sufficient for the independence Section C describes
("a highly correlated instrument imports what is already known").

A cross quoted against a common currency is an **exact algebraic function** of
the reference series. In log returns:

    r(EUR/GBP) = r(EUR/USD) − r(GBP/USD)
    r(EUR/JPY) = r(EUR/USD) + r(USD/JPY)

Such a cross can show near-zero correlation with EUR/USD purely because the
common dollar factor cancels, while remaining fully determined by EUR/USD and
one other pair, and while sharing its entire EUR leg with the instrument
Phase 46 studied. The first screen produced exactly this: EUR/AUD passed at
r = +0.0195, EUR/GBP at +0.2025, EUR/JPY at −0.1907, EUR/NZD at −0.1178.

Low measured correlation was, in these four cases, evidence of cancellation
rather than of independence.

### Resolution

A candidate is ineligible if it shares a **currency leg** with any
previously-used instrument.

Excluded legs, derived from Section C.1:

| Previously used | Legs contributed |
|---|---|
| `frxEURUSD` | EUR, USD |
| `cryBTCUSD` | BTC, USD |
| `R_100` | none (synthetic; exempt per v0.1) |

**Excluded leg set: {EUR, USD, BTC}.**

Leg decomposition applies to symbols of the form `frx` + six characters and
`cry` + six characters, split into two three-character legs. Instruments with
no currency-pair structure — the `OTC_` index products — have no legs and are
unaffected by this criterion.

This criterion is **purely restrictive**: it can only remove candidates, never
admit one. Applied to the superseded screen it removes four survivors
(EUR/AUD, EUR/GBP, EUR/JPY, EUR/NZD), reducing 17 to 13.

### Cross-check

Every `frx*USD` and `frx USD*` pair failed criterion 2 numerically in the first
screen, and every one of them is also excluded structurally under this rule.
Where both criteria apply they agree, which is weak but real evidence the rule
is not arbitrary.

---

## Correction 2 — correlation estimation window

### Defect

Section F criterion 2 requires n ≥ 500 matched bars. That figure was imported
from the W47.0 provenance gate, where the correlation being measured was 0.9979
and any adequate sample sufficed.

The independence gate is a different measurement problem: it must distinguish
r = 0.25 from r = 0.35 near a 0.30 ceiling. At n = 500 the standard error of a
correlation coefficient is approximately 1/√500 ≈ 0.045. Differences of that
size around the ceiling are not resolvable.

At 15-minute granularity, 500 matched bars is roughly five days for a 24/7
instrument and ten days for forex. **The gate as run certified independence for
a year-long study on the basis of a fortnight in August.** Observed n values
ranged from 501 (OTC_SSMI, the bare minimum) to 999.

Consequences visible in the superseded screen: OTC_AEX passed at 0.2977 and
OTC_GDAXI at 0.2925, neither distinguishable from the 0.30 ceiling; OTC_AS51
failed at 0.3731 and Palladium at 0.3339, neither clearly distinguishable from
passing.

### Resolution

**Section F criterion 2's sample requirement is raised from n ≥ 500 to
n ≥ 2500 matched returns against each applicable reference.**

At n = 2500 the standard error falls to approximately 0.020, and the window
spans roughly 26 days of forex trading. The ceiling of 0.30 is unchanged.

### Symmetry requirement — binding

**The re-screen is applied to all 41 eligible candidates, not only to the 17
survivors.** A candidate that failed under the thin window may pass under the
wider one; that outcome is permitted and must be reported.

This is stated as a binding requirement because a re-measurement applied only
to survivors would be capable of confirming a preferred result and incapable of
overturning a rejection, which would make it a rescue rather than a correction.
Applying it to the whole field is what distinguishes the two.

Unlike Correction 1, this correction is **not** purely restrictive, and that is
disclosed rather than glossed.

---

## What is not changed

- The independence ceiling remains |r| < 0.30.
- The provenance floor remains r ≥ 0.95 (Section F criterion 1).
- The completeness, integrity, sufficiency, contiguity and seal criteria are
  untouched.
- The two-stage gate order from v0.2 stands.
- The `R_100` exemption from v0.1 stands.

---

## Record handling

The superseded screen is retained. The re-screen writes to a distinct filename
carrying its sample requirement, so the two records cannot be confused and the
change in the survivor set is auditable by comparing them.

---

## Decision log

* 2026-08-16 — First W48.0a screen completed: 41 candidates evaluated, 17
  survivors, no aborts. Advisor identified two defects in criterion 2 on
  inspecting the results: linear correlation does not capture structural
  entanglement in currency crosses, and the n ≥ 500 sample requirement was
  mis-imported from the provenance gate and yields a ten-day estimation
  window. Both raised with the CEO together with the observation that amending
  after seeing results is the move Phase 47 forbids, and that declining both
  was defensible. CEO adopted both. Advisor recorded that Correction 2 is not
  purely restrictive and imposed the whole-field symmetry requirement in
  response.
