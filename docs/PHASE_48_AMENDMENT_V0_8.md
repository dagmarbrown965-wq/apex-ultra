# PHASE 48 AMENDMENT v0.8 (2026-08-19)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as already
amended by v0.1–v0.7 (`0d972bd`). Authoritative once committed to `docs/` on
`main`.*

**Made before any provenance correlation has been computed for any candidate.**
The reference clock has been identified (`41601a5`); no candidate has been
measured against the 0.95 floor.

---

## Gap identified

Section C determines the instrument "by rule" and says selection returns to
Section C on a gate failure. It does **not** say what happens when **several**
candidates pass both gates. Seven crosses are in play. Choosing among multiple
passers after seeing their results is selection-after-the-fact, which is the
behaviour this phase exists to prevent.

## Rule — selection among multiple passers

Among all candidates that clear **both** gates — independence |r| < 0.30 at
n ≥ 2500, and provenance r ≥ 0.95 at n ≥ 500 — the dataset is the candidate
with the **lowest independence max|r|**.

Rationale: independence is the scarce property Phase 48 exists to secure.
Provenance is specified as a floor to clear, not a quantity to maximise;
ranking on it would optimise a pass/fail criterion and could select a
barely-independent instrument over a clearly independent one.

If no candidate clears both gates, Section C's no-survivors rule governs: the
phase closes with that finding and no threshold is relaxed.

## Disclosure — this rule is not outcome-blind

The independence figures were measured and committed on 2026-08-16, before this
amendment. They are therefore known, and this rule **currently favours
`frxGBPJPY` at max|r| = 0.0548**, the lowest of the seven.

The alternative considered was ranking on provenance r, which is genuinely
outcome-blind because no provenance figure yet exists. It was rejected on the
principle above, with the CEO informed of the trade-off before deciding.

This disclosure exists so that a reader encountering `frxGBPJPY` as the selected
instrument can see that the rule which selected it was written while its
advantage was already visible, and judge that for themselves.

## Standing order of precedence

1. Both gates are binding. A candidate failing either is not eligible,
   whatever its other figures.
2. Among eligible candidates, lowest independence max|r| wins.
3. The selected instrument and every rejected candidate's figures are recorded.

---

## Decision log

* 2026-08-19 — Advisor identified that the agreement specified no rule for
  multiple passers and raised it before the provenance measurement was written
  or run. Both candidate rules put to the CEO together with the disclosure that
  the independence-based rule was not outcome-blind. CEO selected lowest
  independence max|r|. No provenance correlation existed at the time of this
  amendment.
