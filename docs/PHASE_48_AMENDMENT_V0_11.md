# PHASE 48 AMENDMENT v0.11 — D2 interval of record and acquisition mechanism

*Status: authoritative once committed to `docs/` on `main`, per the v1.0 status
convention. Level 2 document under the AI Company Constitution v1.1. Drafted and
ratified 2026-11-16, **before the D2 fetch was run** — no D2 bar count, span, or
`stop_reason` was in existence when any value below was fixed.*

*Every claim was verified by reading `tools/fetch_candles.py`,
`docs/PHASE_48_BOUNDARY_AGREEMENT.md` and `.gitignore` on the filesystem at HEAD
`1a7848e`, not from any mirror or chat history.*

---

## Why this amendment is required

Two independent reasons. The second is not discretionary.

**1. The delivered interval is outside both options the pre-registration
weighed.** Section B ratified 75 days and records at lines 118–121 that a 90-day
interval *"was considered and rejected on token arithmetic: Deriv caps token
lifetime at 90 days, so a token renewed on the lock date expires ~2026-11-14,
and a 90-day interval would land the D2 fetch with effectively zero margin. 75
days leaves roughly two weeks."* The fetch is taking place at lock + 92 days,
and the ~2026-11-14 expiry that reasoning turned on has already passed. Section
B's `~2026-10-30` cannot be read to carry 17 days of slip and an interval
outside both options considered at lock.

**2. Section D.5 describes a fetch the frozen tool cannot perform.** D.5 states
*"D2's fetch requests the interval from D1's last epoch forward."*
`tools/fetch_candles.py` exposes only `--days` (float, default 300.0) and
`--symbol`. It begins at `end_param = "latest"` and walks **backward**
(`end_param = batch_oldest - 1`, line 196), terminating when `(newest_epoch -
oldest_epoch) >= target_seconds` (line 192). There is no start-epoch parameter.
Section D.1 requires the tool be reused **verbatim**, so it cannot be given one.
Section D's preamble governs: *"Exhaustive. Anything not stated is a defect in
this agreement, to be resolved by amendment before fetching, never by
implementer discretion."* Selecting a `--days` value is exactly such a
resolution and is therefore made here, in advance, rather than at the keyboard.

---

## Clause 1 — Interval of record

The D2 interval of record is **92 days from lock (2026-08-16 → 2026-11-16)**,
delivering approximately **88.4 days of forward data** measured from D1's last
epoch 1787193000 (2026-08-20 02:30:00 UTC, confirmed a clean multiple of 900).

The D2 seal states this figure and cites this clause.

The 2026-09-10 anchor decision's instruction that the seal disclose "71.44 days,
not 75" is **superseded and must not be carried forward**: the delivered span
exceeds 75 days rather than falling short of it.

Section B's trade-count justification is unaffected in direction. 88.4 days at
the density that justified 75 days yields more trades, not fewer. Section F
criterion 5 remains the backstop.

## Clause 2 — Acquisition mechanism

D2 is acquired by a **backward walk from `latest`**, not a forward fetch:

```
py -m tools.fetch_candles --symbol frxGBPJPY --days 92
```

`--days 92` is selected so the walk reaches past D1's last epoch and yields a
**provable overlap** rather than a boundary required to land exactly. At a run
time of 18:00–21:00 UTC on 2026-11-16 the oldest bar lands near 2026-08-16,
giving roughly **3.2–3.4 days of overlap**. `--days 90` would leave only
~1.2–1.4 days of margin, and the D1 seal records the first bar clipped **320
seconds off-boundary**, systematic across all three project fetches. In a
backward walk the clipped bar is the **oldest** one — precisely where Section F
criterion 6 is measured. The overlap absorbs that defect instead of colliding
with it.

Overlap is **recorded, not trimmed**, per D.5 unchanged. Within the fetch,
overlapping epochs are deduplicated by the tool's own `candles` dict (line 90),
which is keyed by epoch.

Expected request count is approximately 9. `MAX_REQUESTS = 100`, so the cap is
not in play. `MAX_CONSECUTIVE_EMPTY = 4` with a one-day step back on an empty
response, so a two-day forex weekend cannot terminate the walk prematurely.

## Clause 3 — Completeness computation

Section F criterion 3 is computed from **D2's own first and last epochs**, not
from the D2 interval, because the file spans the overlap as well:

```
span_days = (last_epoch - first_epoch) / 86400
benchmark = 66.4588 * span_days          # Amendment v0.9, observed forex year
floor     = 0.97 * benchmark
```

Expected figures:

| Span | Expected bars | **97% floor** |
|---|---|---|
| 88.4 d (interval only) | ~5,875 | ≥ 5,699 |
| 90 d | ~5,981 | ≥ 5,802 |
| **92 d** | **~6,114** | **≥ 5,931** |

The figures carried by the 2026-09-10 anchor decision and the 2026-10-30
fetch-day run sheet (4,748 expected / ≥ 4,605 floor) assume a 2026-10-30 fetch
and are **void**.

Secondary cross-check, not the criterion: an independent Alpha Vantage GBP/JPY
daily series shows 62 trading days between 2026-08-20 and 2026-11-13. At 96 bars
per trading day a 92-day file should hold roughly 6,000–6,300 bars. A result far
below the floor indicates a failed acquisition, not a market gap.

## Clause 4 — Substitution defence: disposition (a), established by code

Section D.2 requires the substitution defence to fire and treats a fetch in
which it does not as *"anomalous and must be reported."* **On D2 it cannot fire,
and this is a property of the code rather than an assumption.**

Line 166 reads:

```python
if isinstance(end_param, int) and batch_newest > end_param + GRANULARITY:
```

On request 1, `end_param` is the string `"latest"`, so the branch is not
evaluated at all. On every subsequent request `end_param = batch_oldest - 1`,
and the newest candle that exists is the present, so returned data can never be
materially newer than requested. The condition that fired at request 37 on both
prior fetches is a 365-day backward walk running off the start of Deriv's served
history; a 92-day walk never approaches it.

**Section D.2 is satisfied by reporting that the defence did not fire, with this
reason, and by recording the actual `stop_reason` verbatim in the seal.**

**Pre-registered expectation: `stop_reason == "target_reached"`.** Any other
value — `max_requests_hit`, `history_exhausted_consecutive_empty`,
`empty_at_latest`, `no_response_frame` — is the anomaly D.2 means and is
reported as such. This expectation is fixed here, before the fetch.

## Clause 5 — The overlap must be excluded by any future holdout use

New requirement, arising from Clause 2.

Because D2 now contains bars duplicating sealed D1 in-sample material, the D2
seal must state the overlap boundary explicitly:

**A future phase using D2 as a holdout excludes all bars with
`epoch <= 1787193000`.**

Without this clause the overlap silently contaminates the holdout that D2 exists
to provide. The exclusion is stated in the seal alongside the SHA-256, so that a
future pre-registration citing the hash also inherits the boundary.

## Clause 6 — Correction to the record: the fetch path fails loudly

Section G.1 states that *"the documented failure mode is silence, not an
error."* That claim has driven the renewal urgency, the scheduled reminders, and
one of the three reasons given in the 2026-09-10 anchor decision. **It is wrong
for the fetch path.**

`tools/fetch_candles.py` authorizes explicitly and checks the result:

```python
auth = t.call({"authorize": token}, timeout=20.0)
if "error" in auth:
    print("AUTH FAILED: " + str(auth["error"].get("message")))
    return 1
acct = auth.get("authorize", {})
if acct.get("is_virtual") != 1:
    print("BLOCKED: account is not virtual/demo.")
    return 1
```

An expired token on this path produces **`AUTH FAILED` and exit code 1**, not a
quietly truncated file. The silent failure mode belongs to the **live
observation** path (`feed/live_readonly.py` → the allowlisted lazy
`rest_shadow_adapter` import), which the 2026-08-19 token renewal record
correctly describes as possibly never calling `authorize` at all. The Phase 48
documents generalised that property to every path that uses a token.

Consequences recorded:

- The anchor decision's third reason — token margin "on a failure mode that is
  silent" — was unfounded. That decision stands on its other two reasons and is
  **not** reopened.
- An expired or misconfigured token cannot produce a plausible-looking corrupt
  D2. The dataset risk arising from token expiry is materially lower than every
  prior document in this phase assumes.
- The Deriv dashboard "Last used" check remains the verification standard for a
  **renewal**, because it is the live-observation path that cannot self-report.
  For the fetch path, the banner line `auth ok (virtual account confirmed)` is
  direct in-band evidence that the token authorized against a virtual account.
- Section G.1's wording should be narrowed to name the path it applies to. Noted
  for the phase close, not amended here.

Also newly observed and previously unrecorded: the fetch path carries a
**virtual-account assertion** (`is_virtual != 1` → BLOCKED). The 2026-08-19
renewal record left the demo-account selection guard as "unchanged in code; not
re-observed." It is now observed, in this path, at this HEAD.

## What this amendment does NOT change

- **No acceptance threshold.** F1–F7 and their ratified values stand.
- **No code guard.** CP3 verified PASS at this HEAD: a single allowlisted lazy
  read-data import at `feed\live_readonly.py:77`, no execution-capable imports
  anywhere under `engine/`. Nothing was weakened to accommodate a token change.
- **No tuning.** EmaCross stays 9/21. Nothing in this phase produces or
  evaluates a trading signal.
- **Not the instrument.** `frxGBPJPY`, selected by rule at `578231b`.
- **Not the Section E allowlist.**
- **Not `tools/fetch_candles.py`**, which remains reused verbatim — including its
  false per-request-cap docstring — until the phase closes.

## Verification state at ratification (HEAD `1a7848e`, 2026-11-16)

| Gate | Result |
|---|---|
| Working tree | Clean; up to date with `origin/main`; 17 known untracked artifacts in `engine/output/` |
| M0 engine regression | PASS (3/3) |
| CP3 static import gate | PASS — single allowlist entry, unchanged |
| `_last_sign` content probe | HIT (lines 83, 101, 102, 105, 109) — genuine 42.1a code |
| Section B wording probe | Repo text matches; anchor decision not reopened |
| `.gitignore` coverage | `engine/output/candles_*.jsonl` matches `candles_frxGBPJPY_900_*.jsonl`; `_summary.json` not ignored, per `46a2c12` |
| `engine/output/live_signals.jsonl` | Absent — the Section G.4 CP4 trap is defused; the M0 banner still names the path |

## Deferred, not resolved here

- `docs/APEX_DEFERRED_FIXES.md` **does not exist on the filesystem**; the
  deferred-fixes list lives only in the Claude project mirror. Under
  filesystem-is-source-of-truth it is therefore unrecorded, including the false
  `fetch_candles.py` docstring and the absent `tools/rest403_probe.py`. To be
  created at the phase close.
- Carry-forward from `b7379a3`: a summary-reading tool should assert
  `ticks_rejected < ticks_seen`.
- `engine/output/live_signals_2026-07-12_session001.jsonl` exists with no
  summary. Under the journal-lazy / summary-unconditional mechanism documented in
  `b7379a3`, that implies a session which emitted at least one signal and never
  reached session end — the inverse of the benign 07-22 case, and unexplained.
  Outside Phase 48 scope.
