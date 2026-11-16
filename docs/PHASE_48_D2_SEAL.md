# PHASE 48 — D2 SEAL (W48.4 / W48.5)

**Sealed 2026-11-16.** Establishes the D2 dataset under
`docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0, `7415aa4`) as amended v0.1–v0.10
(`d678e97`) and **v0.11 (`d8f0f73`)**.

Every acceptance value below was fixed in v0.11 and committed to `origin/main`
**before this fetch was run**. No criterion was chosen in light of a result.

---

## 1. Dataset identity

| Field | Value |
|---|---|
| Instrument | `frxGBPJPY` |
| Granularity | 900 s (15-minute bars) |
| File | `engine/output/candles_frxGBPJPY_900_1786039197_1794857400.jsonl` |
| Byte size | 611,160 |
| **SHA-256** | **`99A22CFC24061C00591B0E8C63E1F99B8B5DDBBEBDAC7B8C1D588FA66952E49E`** |
| Bars | 6,748 |
| First epoch | 1786039197 — 2026-08-06 17:59:57 UTC |
| Last epoch | 1794857400 — 2026-11-16 19:30:00 UTC |
| Span | 8,818,203 s = 102.063 days |
| Forward data beyond D1 | **88.708 days** |
| Fetched | 2026-11-16, `tools/fetch_candles.py` reused verbatim per Section D.1 |
| Invocation | `py -m tools.fetch_candles --symbol frxGBPJPY --days 92` (v0.11 Clause 2) |
| Summary | `engine/output/candles_frxGBPJPY_900_1786039197_1794857400_summary.json` |
| Token | `apex_trade_demo_6`, Trade scope, key suffix `c9de`, created 2026-11-16 |
| Account | `DOT93163679`, `is_virtual: 1`, confirmed on the fetch banner |

`line_count` on the data file is 6,748, matching `candle_count` in the summary.

**Record-shape corroboration.** 611,160 bytes over 6,748 candles is 90.57
bytes/candle. Sealed D1 is 2,196,813 over 24,257 = 90.56. Identical record
shape, independent of any content claim.

## 2. Acceptance against Section F

Criteria evaluated per v0.11: **3, 4, 6 and 7 binding; 5 satisfied by
construction; 1 and 2 are instrument-selection gates discharged at D1.**

| # | Criterion | Requirement | Measured | Result |
|---|---|---|---|---|
| 1 | Provenance | r ≥ 0.95, n ≥ 500 | Discharged at D1: **+0.99224**, n = 1990, `578231b` | **inherited** |
| 2 | Independence | \|r\| < 0.30, n ≥ 2500 | Discharged at D1: **0.0548** | **inherited** |
| 3 | Completeness | ≥ 97% of 66.4588 × span (v0.9, v0.11 Clause 3) | **6,748** vs benchmark 6,783.0, floor **≥ 6,579.5** — **99.48%** | **PASS** |
| 4 | Integrity | Defence disposition per v0.11 Clause 4; gaps inventoried | Did not fire, as pre-registered; 15 gaps inventoried; 0 empty responses | **PASS** |
| 5 | Sufficiency | Supports a future n ≥ 50 holdout | 6,748 bars; 88.708 forward days | **PASS** |
| 6 | Contiguity | D2 continues D1; overlap recorded | First epoch 1786039197 **precedes** D1's last 1787193000 by **13.354 days** | **PASS** |
| 7 | Seal | SHA-256 recorded; commit trail clean; no forbidden statistic | This document | **established** |

Criteria evaluated in order. None was reached by rescuing an earlier failure.

Completeness recomputed from the file's own first and last epochs, per v0.11
Clause 3, not from the D2 interval:

```
span_days = (1794857400 - 1786039197) / 86400 = 102.0625
benchmark = 66.4588 * 102.0625                = 6,783.0
floor     = 0.97 * 6,783.0                    = 6,579.5
actual    = 6,748                             = 99.48% of benchmark
```

## 3. Integrity detail

**The substitution defence did NOT fire**, and `substitution_note` is `null`.

This is the disposition pre-registered in v0.11 Clause 4, established by reading
the code before the fetch rather than inferred afterwards. Line 166 tests
`isinstance(end_param, int) and batch_newest > end_param + GRANULARITY`. On
request 1 `end_param` is the string `"latest"`, so the branch is not evaluated.
On every later request `end_param = batch_oldest - 1`, and the newest candle in
existence is the present, so returned data can never be materially newer than
requested. The condition that fired at request 37 on both prior fetches is a
365-day walk running off the start of Deriv's served history; this walk spans
102 days and never approaches it.

**Section D.2 is therefore satisfied by reporting that the defence did not fire,
with this reason.** It is not assumed benign.

| Field | Value |
|---|---|
| `stop_reason` | **`target_reached`** — matches the v0.11 Clause 4 pre-registration |
| `requests_made` | 10 |
| `empty_responses` | 0 |
| `substitution_note` | `null` |

**Gaps: 15 over granularity.** Largest 184,500 s (51.25 h) after epoch
1786135500 (2026-08-07 20:45:00 UTC) — a weekend closure. Weekend gaps are
expected for a five-day instrument under Section D.3 and are reported, never
smoothed or backfilled.

**Independent check on the gap count.** Sealed D1 inventories 55 gaps over
364.993 days. At that density a 102.063-day span predicts **15.4**. Fifteen were
observed. The span contains 14.58 weeks, so essentially every gap is a weekend
closure and no intra-session gaps are present — the signature D.3 describes for
a correctly acquired five-day series.

**Clipped first bar.** First epoch 1786039197 is **897 s off the 900-second
boundary**; the last epoch 1794857400 is a clean multiple of 900. The clipped
first bar is now observed on all four project fetches. D1's offset was 320 s;
this one is 897 s (equivalently 3 s short of the next boundary). Systematic in
occurrence, variable in magnitude. **Any future use excludes the first bar.**

## 4. Contiguity and the overlap (Section F.6, v0.11 Clause 5)

D2's first epoch **precedes** D1's last epoch. There is no gap to explain; there
is an overlap of **1,153,803 s = 13.354 days**.

Per Section D.5 the overlap is **recorded, not trimmed**. Within the fetch,
duplicate epochs were deduplicated by the tool's own epoch-keyed `candles` dict.

**Binding on any future use, carried from v0.11 Clause 5:**

> **A future phase using D2 as a holdout excludes all bars with
> `epoch <= 1787193000`.**

Without this exclusion the overlap silently reintroduces 13.354 days of sealed
D1 in-sample material into the holdout D2 exists to provide. A future
pre-registration citing the SHA-256 above inherits this boundary with it.

## 5. Instrument identity check (Amendment v0.10)

| Measure | Value |
|---|---|
| First record | `{"epoch": 1786039197, "open": 213.151, "high": 213.153, "low": 213.151, "close": 213.153}` |
| Last record | `{"epoch": 1794857400, "open": 210.314, "high": 210.324, "low": 210.257, "close": 210.27}` |
| First close | 213.153 |
| Last close | 210.270 |
| Minimum close | **206.947** |
| Maximum close | **217.461** |

Bounded exactly to what v0.10 permits. Nothing is derived from these values.

**External reference, recorded before this file existed.** An Alpha Vantage
GBP/JPY daily series over the file's span (2026-08-06 → 2026-11-16, 72 trading
days) gives closes **207.555 – 217.237** and low/high **206.344 – 217.840**. The
band for the D2 *interval* (2026-08-20 onward) was recorded earlier the same day,
before the fetch; the figures above are the same source and method over the
file's actual span, which proved wider than predicted (section 6).

**The relationship between the two is the confirmation.** D2's 15-minute closes
(206.947 – 217.461) sit *wider* than the daily close range and *inside* the
daily low/high range, on both ends. That is the only correct relationship
between intraday closes and daily OHLC from an independent venue: a dataset
failing it either side would not be this instrument. D2's first close of 213.153
is 0.031 from Alpha Vantage's 2026-08-06 close of 213.122.

Confirms GBP/JPY and excludes any pair quoted near unity.

## 6. Disclosure: a prediction in v0.11 Clause 2 was wrong

v0.11 Clause 2 estimated that `--days 92` would place the oldest bar near
2026-08-16, giving **~3.2–3.4 days** of overlap. The actual overlap is **13.354
days** and the file spans **102.063 days**, not 92.

**Cause.** The fetch loop tests `(newest_epoch - oldest_epoch) >=
target_seconds` *after* appending each batch, so it overshoots by up to one full
request window (10.4167 days). At request 9 the span stood at 91.65 days, below
the 92-day target, so request 10 ran and carried the total to 102.06 days. The
advisor's estimate failed to account for the post-append test when selecting 92.

**Consequences, all absorbed:**

- Clause 3 computes completeness from the file's own epochs, so the floor moved
  with the span and the criterion was applied correctly at 102.063 days.
- Clause 5's exclusion rule operates unchanged; it now protects 13.354 days of
  sealed material rather than 3.3.
- Clause 1's forward-data figure, ~88.4 days, is accurate: 88.708 observed.
- Section D.5's "any overlap is recorded, not trimmed" governs, as written.

Recorded here rather than corrected silently. A smaller `--days` value would
have produced a shorter file; nothing about the result was improved by the
error, and no criterion was adjusted after the fact.

## 7. Seal enforcement — enforced unread

**SEALED.** Not to be opened until a hypothesis is pre-registered. Only the
summary is readable.

1. Any script that reads
   `candles_frxGBPJPY_900_1786039197_1794857400.jsonl` **must be committed to
   `main` before it is executed.** Git history is the complete log of everything
   that has touched the sealed data.
2. A future phase pre-registering against this dataset cites the SHA-256 in
   section 1, states the commit range within which no reading script was
   committed, and applies the section 4 exclusion.
3. **If the hash cannot be reproduced, this dataset's provenance is void and it
   may not serve as a holdout.**

**Seal established at the commit adding this document.** The only read performed
on this file before the seal was the Section E structural allowlist plus the
Amendment v0.10 bounded identity check in section 5, both at acquisition time,
by console command, before the seal existed.

Forbidden until pre-registration, unchanged: return autocorrelation at any lag;
volatility clustering measures; ATR or any indicator series; compression-episode
or signal counts; drawdown or trend statistics; plotting the price series; and
any backtest, exploratory or otherwise.

**No forbidden statistic has been computed on this dataset.**

## 8. Operational record

**Credentials.** The fetch path requires `DERIV_APP_ID` to be set explicitly.
`infrastructure/broker/deriv/rest_transport.py:123` has **no fallback**, while
`config_loader.py:70` defaults to `1089` — but `fetch_candles.py` builds a
`DerivRestOtpTransport` directly and never passes through `config_loader`. With
the variable unset, the REST accounts listing returns **HTTP 401, indistinguishable
from an expired token**. App id in use: `33wXCuqL07IJ4XTrihUHm`. Nothing in
`docs/` recorded this before today.

**`testing/diagnostics/deriv_rest_auth_probe.py` is the correct instrument for
credential verification**, not a fetch. It prints the exact API payload, the
`loginid`, `is_virtual`, and a balance read. It resolved today's failure in one
run after the fetch had produced only a single ambiguous line.

**Demo-account guard observed.** `loginid DOT93163679`, `is_virtual: 1`. The
2026-08-19 renewal recorded the DOT..79-over-ROT..99 selection guard as
"unchanged in code; not re-observed." It is now observed on the live path.

**Execution guards verified green at `1a7848e`, immediately before the fetch:**
M0 regression PASS (3/3); CP3 PASS with a single allowlisted lazy read-data
import and no execution-capable imports under `engine/`; `_last_sign` content
probe HIT; `LIVE_TRADING` observed empty. **No guard was altered.**

**Section G.1 is wrong for this path** — see v0.11 Clause 6. The fetch path
authorizes explicitly and fails with `AUTH FAILED`, exit 1. This was confirmed
empirically today: an invalid token produced a loud failure and wrote nothing.

## 9. Outstanding at phase close

- **W48.5 phase close assessment** — this seal completes D2 acquisition.
- **`docs/APEX_DEFERRED_FIXES.md` does not exist on the filesystem.** The
  deferred-fixes list exists only in the Claude project mirror and is therefore
  unrecorded under filesystem-is-source-of-truth. Create it, carrying: the false
  per-request-cap docstring in `fetch_candles.py` (line 17); the absent
  `tools/rest403_probe.py`; the missing `docs/PHASE_42_1_BOUNDARY_AGREEMENT.md`;
  the repository still living under `Downloads` (Section G.2); the
  `ticks_rejected < ticks_seen` assertion carried forward from `b7379a3`; and
  the two items below.
- **The fetcher does not emit the v0.10 identity fields.** Amendment v0.10
  requires a bounded identity check; nothing in the tooling produces
  first/last/min/max close, so every phase must perform it by hand, and after a
  seal that requires a committed script.
- **Section G.1 wording** should be narrowed to name the live-observation path.
- **`engine/output/live_signals_2026-07-12_session001.jsonl` has no summary.**
  Under the journal-lazy / summary-unconditional mechanism documented in
  `b7379a3`, that implies a session which emitted at least one signal and never
  reached session end — the inverse of the benign 07-22 case, and unexplained.
  Outside Phase 48 scope.
- **Token hygiene** — recorded separately in `docs/TOKEN_RENEWAL_2026-11-16.md`.
