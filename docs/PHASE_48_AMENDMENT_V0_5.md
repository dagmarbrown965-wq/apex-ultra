# PHASE 48 AMENDMENT v0.5 (2026-08-16)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as already
amended by v0.1 (`bf90beb`), v0.2, v0.3 and v0.4 (`74e0401`). Authoritative
once committed to `docs/` on `main`.*

**Made before any provenance measurement exists.** A clarification of a binding
rule, resolving an off-by-one ambiguity. No threshold or criterion changes.

---

## The established fact

Amendment v0.4 required the Deriv candle epoch convention to be established
before any provenance figure is trusted. It has been, by probe rather than
assumption:

`tools/probe_epoch_alignment.py`, run 2026-08-16 on `cryBTCUSD`, compared each
15-minute bar against the aggregate of the fifteen 1-minute bars covering the
same span. All 20 tested bars matched the open hypothesis; none matched the
close hypothesis; none were ambiguous or unexplained.

**`epoch` marks the bar's OPEN. A candle labelled E covers the half-open
interval [E, E+900).**

Record: `engine/output/probe_epoch_alignment_cryBTCUSD_1786908600.json`,
commit `d93dac1`.

Incidental confirmation: the 1-minute request asked for a 23,400-second window
and returned exactly 390 bars (23,400 ÷ 60), re-confirming at granularity 60
the finding that `count` specifies a time window rather than a candle cap.

---

## The ambiguity being fixed

Amendment v0.4's binding resample rule reads:

> The bar's close is the last observation at or before the bar's end.

With the open convention now established, bar E spans `[E, E+900)`. An
observation timestamped exactly `E+900` belongs to bar `E+900`, not to bar `E`.
"At or before the bar's end" would place it in both. One observation per bar
boundary is a small effect, but the rule is marked binding and Section D
forbids resolving ambiguity by implementer discretion.

---

## Amended text

Amendment v0.4, Correction 1, resampling rule, second clause is replaced by:

> - Each 15-minute reference bar labelled E aggregates exactly those
>   observations timestamped in the **half-open interval [E, E+900)** — that
>   is, `E <= t < E+900`. An observation at exactly `E+900` belongs to the next
>   bar and must not be included in bar E. The bar's close is the last
>   observation inside that interval.

All other clauses of the resample rule stand: UTC boundary alignment, mid
prices where bid and ask are supplied, and no interpolation of empty bars.

---

## Decision log

* 2026-08-16 — Epoch convention established by probe (unanimous, 20/20 open).
  Advisor noted that v0.4's "at or before the bar's end" wording double-counts
  the boundary observation under a half-open interval and proposed this
  clarification. No measurement existed at the time.
