# PHASE 45 BOUNDARY AGREEMENT — AMENDMENT v0.3

_Amends the locked v0.1 (efff0cc / ededecc) as further amended by v0.2
(2131b26). Where this amendment and earlier versions conflict, this one
governs. The no-re-tuning rule, the 38% pass bar, the 34.5% break-even,
and the dual primary/secondary policy design all stand unchanged._

## Why this amendment exists

W45.0b (tool committed-pending) was built and run. A full-span fetch
attempt returned exactly 43,201 ticks spanning exactly 86,400 seconds
(1.000 day), then stopped on no-backward-progress. Finding, verified
from the fetch summary, not assumed:

**Deriv serves only ~24 hours of R_100 tick history.** Requests for
older data return no further ticks. The v0.2 target of >= 14 days of
history in a single pull is therefore NOT ACHIEVABLE from historical
data. The data within the 24h window is pristine (largest gap 2s, zero
gaps over expected).

A single 24h pull yields ~3,000 signals (clears the >= 1,000 bar) but
only ~13 independent resolution windows (86,400s / ~6,300s per
resolution), against the >= 150 required by v0.2 Amendment 2. That is
the binding shortfall.

## Amendment 1 — collection method: forward, not historical

The tick series is built FORWARD by repeated fetches over calendar
time, not by one deep historical pull. Each run of
`py -m tools.fetch_history --days 1` captures the most recent ~24h
before Deriv discards it. Files accumulate in engine/output/, one per
run, timestamped by epoch range. Overlap between runs is EXPECTED and
harmless; the evaluation step (W45.2) merges all tick files and
deduplicates by epoch (epochs are unique keys), producing one
contiguous series.

The W45.0b tool is NOT modified for this. It already does exactly what
is needed per run. Merge/dedupe is the reader's job at evaluation time.

## Amendment 2 — the binding rule is maximum gap, not frequency

Because only ~24h of history exists at any moment, data older than ~24h
at the time of a fetch is UNRECOVERABLE. Therefore:

- **A fetch MUST occur at least once every 24 hours.** This is the hard
  obligation. A gap longer than ~24h between successful fetches leaves a
  permanent hole in the series that cannot be backfilled.
- More frequent fetches (e.g. twice daily) are encouraged as insurance:
  they overlap harmlessly and shrink the risk that one missed fetch
  causes data loss.

Unlike the Phase 44 observation window, a missed collection day is NOT
covered by grace days — the data is simply gone. The collection period
is therefore LESS forgiving than the observation window, not more.

## Amendment 3 — collection target

Collect until the merged, deduplicated series contains **>= 150
independent resolution windows**, where independent windows =
(total contiguous span) / (105 minutes). At ~13 windows per clean 24h
day, this is approximately **12 days** of daily collection (12 x 13 ~=
156). If fetches are twice-daily and no day is missed, the calendar
duration is the same ~12 days but with safety margin against loss.

Holes matter: if a gap between fetches drops a block of time, the
"contiguous span" resets or fragments, and independent windows are
counted only within contiguous stretches. A fragmented series may need
more than 12 days to reach 150 windows. This is the cost of a missed
fetch, stated in advance.

## Amendment 4 — daily collection routine

Each collection run:
1. Credentials via the three-line ritual; cls; confirm blank.
2. `py -m tools.fetch_history --days 1`
3. Read the printed summary: confirm stop_reason is history_exhausted
   (expected — it means the full ~24h was retrieved) or target_reached,
   tick_count near 43,000, largest_gap_seconds small.
4. Commit the summary JSON for that run (the bulk .jsonl is gitignored
   per the pending W45.0 commit decision); the .jsonl stays on disk for
   the eventual merge.
5. Track progress: running count of independent windows toward 150.

## Decision log

- 2026-07-24: 24h platform limit discovered empirically from the fetch
  summary (not assumed). Method changed from single historical pull to
  forward daily collection. Binding rule set as max 24h gap between
  fetches (CEO chose "once daily obligatory, twice daily when time
  permits"). Target ~150 independent windows ~= 12 days. Missed-fetch
  data loss is explicitly NOT grace-covered. All decided before any
  evaluation code (W45.1+) was written.
