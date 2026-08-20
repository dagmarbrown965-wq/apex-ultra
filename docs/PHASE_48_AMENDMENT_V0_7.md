# PHASE 48 AMENDMENT v0.7 (2026-08-19)

*Amends `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as already
amended by v0.1 (`bf90beb`), v0.2, v0.3, v0.4 (`74e0401`), v0.5 and v0.6
(`fb46cf5`). Authoritative once committed to `docs/` on `main`.*

**Made before any provenance correlation has been computed.** The reference
file has been characterised structurally; no candidate has been measured
against it. Every rule below was fixed before a single correlation existed.

---

## Reference source — established

| Field | Value |
|---|---|
| Source | HistData.com, Generic ASCII, M1 (1-minute bars) |
| Series | `GBPJPY`, July 2026 |
| Archive | `HISTDATA_COM_ASCII_GBPJPY_M1202607.zip` (334,726 B) |
| Data file | `DAT_ASCII_GBPJPY_M1_202607.csv` (2,025,354 B, 32,667 rows) |
| SHA-256 | `70009d82358c9e79869e8a0d1df81675e8b5d1427b717bfa5ad8d76de3ab0f34` |
| Retrieved | 2026-08-19 |
| Companion | `DAT_ASCII_GBPJPY_M1_202607.txt` (4,999 B) — a **gap report**, retained as part of the provenance record |

Format: semicolon-delimited, `YYYYMMDD HHMMSS;open;high;low;close;volume`.
Volume is `0` on every row and is ignored. No bid/ask columns, so v0.4's
mid-price clause does not apply to this source.

**All seven surviving candidates are available from this source** (GBP/JPY,
AUD/JPY, AUD/NZD, AUD/CHF, NZD/JPY, GBP/AUD, GBP/NZD), so none will be
rejected as unverifiable for the reason the four `OTC_` index products were.

---

## Finding 1 — the source file is not time-ordered

60 strictly-backwards timestamp steps across 10 dates. 109 timestamps appear
more than once (99 twice, 10 three times), 119 surplus rows in total, and
**every one of the 109 collisions carries conflicting OHLC.** No collision is
adjacent; they occur as spliced blocks.

### Rule 1 — sort

Source rows are sorted by timestamp before any other processing. Arrival order
in the file carries no meaning and must not be relied on.

### Rule 2 — drop every duplicated minute

**Any minute whose timestamp appears more than once is dropped in its
entirety.** No row is preferred over another on price, range, or position.

Cost, measured on this file: 228 of 32,667 rows, **0.70%**. 41 of 2,179
fifteen-minute buckets are touched; the worst single bucket loses 7 minutes.
After the rule, 32,439 rows remain and the series is strictly increasing.

**Observation recorded but deliberately not acted on.** 90 of the 109
collisions have a recognisable structure: a degenerate bar with
`open == high == low == close` is spliced beside a genuinely-ranged bar, in
reversed pairs. A rule preferring the ranged bar would recover 90 of them. It
is rejected because it requires judging which bar is "real", and the cost of
refusing that judgment is 0.70% of rows against 4× the required sample. The
remaining 19 collisions are ranged-versus-ranged and admit no structural tell
at all — any rule that resolved them would be picking a price.

A future phase needing finer treatment may revisit this with its own
pre-registration. It may not be revisited to rescue a failing correlation.

---

## Finding 2 — the source does not document its timezone

The companion `.txt` contains no reference to `time`, `zone`, `EST`, `EDT`,
`GMT`, `UTC`, `DST` or `offset`. It is a gap report, not a specification.

Indirect evidence, recorded as evidence and not as a conclusion: the gap report
lists gaps beginning at exactly `170000` on consecutive dates
(`20260701`, `20260706`, `20260707`), and the file's final bar is `20260731
165900` — a Friday. Both are consistent with 17:00 in file-time being the New
York daily rollover and weekly close. That narrows the offset to New York time
but does not settle whether DST is applied.

### Rule 3 — the offset is IDENTIFIED, never fitted

Alignment is resolved as a declared step, separate from and prior to
measurement.

1. The candidate set is fixed in advance: whole-hour offsets **UTC+0, UTC−4,
   UTC−5**, each combined with a bar shift of **−1, 0, +1** fifteen-minute
   bars. Nine combinations. UTC+0 is included as a control expected to fail.
2. Correlation is computed at **every** combination and **the full table is
   printed**, not just the winner.
3. The offset is **identified** only if the best combination yields
   **r ≥ 0.90** and the second-best yields **r ≤ 0.60**. A single sharp peak
   against a flat field identifies an alignment; a graded field does not.
4. If no combination meets that test, the tool **halts**. It does not select
   the maximum. A best-of-nine chosen from a graded field is fitting, and
   fitting is what this project's rules exist to prevent.
5. The identified offset is recorded, and every candidate thereafter is
   measured at that same offset. The identification is performed **once**, on
   one pair, and is a property of the source rather than of any candidate.

Thresholds 0.90 and 0.60 are fixed here, before any correlation is computed.
The provenance floor itself remains r ≥ 0.95 at n ≥ 500, unchanged.

---

## Finding 3 — bucket completeness

Resampled to 15 minutes on the file-local clock, July yields 2,179 buckets:
2,092 with all 15 minutes present, 87 partial (4.0%), the smallest holding 10.

### Rule 4 — complete buckets only

**Only 15-minute buckets containing all 15 source minutes are used.** A partial
bucket's close may be materially stale relative to the bucket boundary, and
2,092 complete buckets against a 500-bar requirement means excluding partials
costs nothing.

**Disclosed bias:** partial buckets cluster at the 17:00 rollover and at the
gaps enumerated in the companion report — systematically the thinnest-liquidity
minutes of the day. Provenance is therefore measured on normal-liquidity
periods. This is defensible for the question being asked, since stale quotes on
either side would depress correlation for reasons unrelated to instrument
fidelity, but it is a stated limitation rather than a neutral choice.

---

## Unchanged

Provenance floor r ≥ 0.95 at n ≥ 500 matched bars. Independence ceiling
|r| < 0.30 at n ≥ 2500. Bar `E` covers the half-open interval
`[E, E+900)` per v0.5, with Deriv's `epoch` marking bar open. Two-stage gate
order per v0.2. No interpolation of missing bars, ever. Section C's
no-survivors rule: if no candidate clears 0.95, the phase closes with that
finding and no threshold is relaxed.

---

## Decision log

* 2026-08-19 — HistData confirmed to cover all seven surviving candidates.
  GBPJPY July 2026 retrieved and hashed. Structural characterisation found the
  file unordered with 109 conflicting duplicate timestamps and no documented
  timezone. Advisor measured the cost of the maximally conservative duplicate
  rule (0.70% of rows) before proposing it, and rejected the
  degenerate-bar heuristic that would recover 90 of 109 on the grounds that its
  benefit is immaterial and its cost is a judgment about which price is real.
  Offset identification specified with pre-declared thresholds and a mandatory
  halt, to prevent a best-of-nine search being reported as an alignment. No
  correlation had been computed when this amendment was written.
