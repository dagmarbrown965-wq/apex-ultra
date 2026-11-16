# APEX ULTRA — deferred fixes and open record-integrity items

**Created on the filesystem 2026-11-16.** A version of this list has existed in
the Claude project mirror since 2026-08-24 but **was never committed to the
repo** — so under filesystem-is-source-of-truth it was not recorded at all. That
is itself an instance of the problem this list tracks, and is why it now lives
in `docs/`.

Every item below is marked with its verification state. Items verified
2026-11-16 were checked against the filesystem in the W48.4/W48.5 session, not
inherited from the record.

---

# CLOSED

## C1. D2's content span (~71 days, not 75) — **CLOSED 2026-11-16**

Raised 2026-08-25. Resolved by **Amendment v0.11** (`d8f0f73`) and the **D2 seal**
(`f7a69cf`), neither by the route anticipated here.

The interval was anchored to lock on 2026-09-10, which would have delivered
71.44 forward days. The fetch then slipped 17 days. The delivered dataset
carries **88.708 days** of forward data over a **92-day interval of record** —
more than the 75 days originally specified, not less. The shortfall this item
worried about inverted.

Both options recorded here on 2026-08-25 were overtaken. The decision that
mattered was made before the fetch, in writing, which is what this item asked
for.

---

# DEFERRAL EXPIRING

## D1. False docstring in `tools/fetch_candles.py` line 17

**Verified present 2026-11-16.** The docstring states the per-request cap is
1000 candles. It is not a candle cap: `count` is a **time window**, and
`count=1000` at 900 s spans 900,000 s = **10.42 days**.

**The deferral's condition is now satisfied in substance.** It was deferred
because Section D.1 pins the tool as reused **verbatim**, and editing it between
the two fetches would mean D1 and D2 were not produced by a byte-identical
tool. Both fetches have now run against the identical file — D1 on 2026-08-19,
D2 on 2026-11-16. The verbatim requirement is fully discharged.

**Fix at the W48.5 phase close.** Nothing further blocks it.

The operational risk it created was real and nearly bit: the D2 run sheet had to
carry the correction explicitly, and sizing was computed from the time-window
reading rather than the docstring.

---

# CONFIRMED ABSENT — the record asserts these exist

Both verified by `Test-Path` on 2026-11-16. Both returned **False**.

## A1. `tools/rest403_probe.py`

Referenced in the record; not in the repo. Either never written, or written and
lost. Note that `testing/diagnostics/deriv_rest_auth_probe.py` **does** exist and
proved to be the right instrument for credential diagnosis on 2026-11-16 — it
may be that the probe was built there and the record names a path that never
existed.

## A2. `docs/PHASE_42_1_BOUNDARY_AGREEMENT.md`

**The more serious of the two.** A boundary agreement is the load-bearing
artifact of a phase, and Phase 42.1 is the phase whose handoff this project's
session context is built on. Establish whether Phase 42.1 ever had a written
agreement or whether the record overstates it. If it never existed, say so in
the record rather than leaving a citation pointing at nothing.

---

# NEW — raised in the 2026-11-16 session

## N1. The fetcher does not emit the Amendment v0.10 identity fields

v0.10 requires a bounded instrument-identity check (first/last/min/max close,
first and last raw records). `tools/fetch_candles.py` writes none of them into
its summary, so every phase must compute them by hand — and **after a seal that
requires a committed script**, because the commit-before-read rule then binds.
Done by console command for D2 at acquisition time, before the seal existed.

Fix with the D1 docstring fix, once the tool is unfrozen.

## N2. Section G.1's "failure mode is silence" is wrong for the fetch path

`tools/fetch_candles.py` authorizes explicitly and exits 1 with `AUTH FAILED`.
Confirmed empirically 2026-11-16: an invalid token produced a loud failure and
wrote nothing. The silent mode belongs to the **live-observation** path
(`feed/live_readonly.py` → the allowlisted lazy `rest_shadow_adapter` import),
which may never call `authorize`.

v0.11 Clause 6 records the correction, but **Section G.1 itself is unamended**
and still states the generalisation. Narrow its wording to name the path at the
phase close.

This claim had been load-bearing since August: it drove the renewal urgency,
both scheduled reminders, and one of the three reasons in the 2026-09-10 anchor
decision.

## N3. The Deriv dashboard's "Last used" column no longer exists

`docs/TOKEN_RENEWAL_2026-08-19.md` names it *"the check that matters"* and builds
the verification standard on it. Verified 2026-11-16: the API token page exposes
only Name, Status, Token key, Permissions, Expiry date, Actions — in both card
and list view.

Replacement standard recorded in `docs/TOKEN_RENEWAL_2026-11-16.md`:
`py -m testing.diagnostics.deriv_rest_auth_probe`. **The August document still
asserts the old procedure** and should carry a pointer forward.

## N4. `DERIV_APP_ID` has no fallback on the fetch path

`infrastructure/broker/deriv/rest_transport.py:123` —
`self.app_id = app_id or _os.environ.get("DERIV_APP_ID", "")`, no default.
`config_loader.py:70` defaults to `"1089"`, but `fetch_candles.py` builds a
`DerivRestOtpTransport` directly and never passes through it.

**An unset app id returns HTTP 401 — indistinguishable from an expired token.**
Two faults, one error message. Cost the 2026-11-16 session its first diagnostic
round. Not documented in `PREFLIGHT.md` or `SHADOW_RUNBOOK.md`; both should name
it.

Also note `docs/APEX_HANDOFF_PHASE_42_1.md:100`: app ids are **alphanumeric** on
the new platform. `1089` is the legacy public value.

## N5. Nothing checks the dashboard against the record between renewals

The one-active-token rule did not fail on 2026-09-13 — **nothing was enforcing
it.** Each renewal records its own state; nothing compares the dashboard to
`docs/TOKEN_RENEWAL_*.md` in between. That is how `apex_trade_demo_4` went
unrecorded for weeks in August and how `apex_demo_test` went unrecorded for two
months.

**Proposed standing check:** any session touching Deriv credentials lists the
active tokens and treats a mismatch against the current record as a finding. One
page load.

## N6. `engine/output/live_signals_2026-07-12_session001.jsonl` has no summary

Commit `b7379a3` established the mechanism: the journal is created lazily on
first emit, the summary written unconditionally at session end. Summary without
journal is benign — it means nothing was emitted.

**This file is the inverse**: a journal with no summary, which under that same
mechanism implies a session that emitted at least one signal and then never
reached session end. Abnormal termination. Unexplained, and not covered by the
07-22 resolution. Outside Phase 48 scope.

## N7. Summary-reading tools should assert `ticks_rejected < ticks_seen`

Carried forward verbatim from `b7379a3`. The 07-22 session002 summary looks
healthy at a glance — full field set, clean exit, `live_orders_sent: 0` — and
the failure shows only in `ticks_rejected` against `ticks_seen` (36/36).

## N8. The M0 banner still names a file that no longer exists

`py -m engine.validation.test_m0_regression` prints a suggested CP4 command
against `.\engine\output\live_signals.jsonl`. Verified 2026-11-16: that file is
**absent** (removed at `77f58e6`).

Section G.4's trap is therefore half-closed — running the line verbatim now
errors instead of reporting PASS on nothing, which is better, but the banner
still points at nothing.

## N9. The fetch loop overshoots `--days` by up to one request window

Not a defect, but undocumented and it caused a wrong prediction. The loop tests
`(newest_epoch - oldest_epoch) >= target_seconds` **after** appending a batch,
so it can overrun the target by a full request window (10.4167 days at
`count=1000`, 900 s).

D2 requested 92 days and received **102.063**. v0.11 Clause 2 predicted ~3.3
days of overlap with D1; actual was **13.354**. Disclosed in the D2 seal §6.

Anyone sizing a future fetch should expect the delivered span to be
`--days` plus up to one request window, and compute acceptance from the file's
own epochs rather than from the requested interval.

---

# ESCALATED

## E1. The repo lives under `C:\Users\dagma\Downloads\APEX_ULTRA\apex_ultra`

Section G.2 required the move **"before this phase generates new primary
evidence."** Phase 48 has now generated the most important evidence this project
holds — two sealed datasets — while still under `Downloads`.

The exposure is specific: both `.jsonl` files are caught by `.gitignore`
(deliberately, per D.6), so **git is not a backup of them**. They existed in
exactly one directory, one that browsers write into and cleanup tools empty, and
if either were lost both seals are void by their own terms.

**Partially mitigated 2026-11-16.** Verified copies now exist at
`%USERPROFILE%\Documents\APEX_SEALED_DATA\`, with both hashes reproduced:

| File | Bytes | SHA-256 reproduced |
|---|---|---|
| `candles_frxGBPJPY_900_1755657580_1787193000.jsonl` | 2,196,813 | `E9DF6A4E…EFEE39` ✓ |
| `candles_frxGBPJPY_900_1786039197_1794857400.jsonl` | 611,160 | `99A22CFC…52E49E` ✓ |

D1's hash had not been recomputed since 2026-08-19; it reproduced after 89 days,
confirming D1's provenance is intact rather than assumed.

**The move itself remains outstanding**, and a second copy in the same user
profile is not off-machine redundancy.

---

# VERIFIED 2026-11-16 — no longer open questions

- **Lock commit date.** `7415aa403af505128f9acb4a6662226919ab3d11`, Sun Aug 16
  13:05:30 2026 −0500 = **2026-08-16T18:05:30Z**. Read from `git log`, not from a
  document. Every Phase 48 date rests on this: lock + 75 = 2026-10-30, lock + 90
  = 2026-11-14 (the rejected option), lock + 92 = 2026-11-16 (the delivered
  interval).
- **17 untracked artifacts in `engine/output/`.** Exactly 17, unchanged across
  the session. Expected; a future `git status` should not read as a dirty tree.
  D.7's prohibition on `git add -A` is what keeps them out of history.
- **`.gitignore` coverage.** `engine/output/candles_*.jsonl` matched the new D2
  filename; the `_summary.json` is not ignored, per `46a2c12`. Verified by
  staging inspection before the seal commit.

---

## Decision log

* **2026-08-24** — Advisor raised the Section D.1 conflict before editing
  anything. Dagmar chose to defer the docstring fix until Phase 48 closes. No
  file touched.
* **2026-08-25** — The W48.4 reminder misfired 66 days early, re-derived the
  fetch date as 2026-10-30, and surfaced the D1-last-epoch anchor discrepancy
  now closed as C1.
* **2026-11-16** — This list committed to the filesystem for the first time.
  C1 closed; D1's deferral condition satisfied; A1 and A2 confirmed absent by
  `Test-Path`; N1–N9 raised during the D2 acquisition session; E1 partially
  mitigated by verified copies; the lock commit date verified from `git log`
  rather than inherited from the record.
