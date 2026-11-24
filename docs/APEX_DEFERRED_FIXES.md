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

# CLOSED — fixed 2026-11-16, after the phase close

## D1. False docstring in `tools/fetch_candles.py` — **FIXED**

The docstring claimed the per-request cap was 1000 candles. It is not a candle
cap: `count` is a **time window**, and `count=1000` at 900 s spans 900,000 s =
**10.4167 days**.

Deferred since 2026-08-24 because Section D.1 pinned the tool as reused
**verbatim**, and editing it between the two fetches would have meant D1 and D2
were not produced by a byte-identical file. Both fetches ran against the
identical tool — D1 on 2026-08-19, D2 on 2026-11-16 — so the verbatim
requirement was fully discharged at the phase close, and the line was corrected
the same day.

The operational risk was real and nearly bit: the D2 run sheet had to carry the
correction explicitly, and the fetch was sized from the time-window reading
rather than from the docstring.

**Demonstrated live during verification.** A smoke fetch at `--days 1` returned
a **10.413-day** span from a single request — one request window is the minimum
fetch granularity, which is precisely what the old line obscured.

**Partially discharged only — see N13 (2026-11-24).** The docstring was
corrected, but three instances of the superseded 1000-candle claim survive
elsewhere in the same file, one of them in an artifact that outlives the run.
D1 should not be read as closed.

---

# CONFIRMED ABSENT — both investigated and resolved 2026-11-16

## A1. `tools/rest403_probe.py` — **LOST. Record was accurate; the action was never taken.**

Not in the repo (`Test-Path` False), and **nothing matching `rest403*` anywhere
under the old `Downloads\APEX_ULTRA` tree** (recursive search, 2026-11-16).

**The record did not overstate this** — an earlier version of this entry said it
did, and that was wrong. `docs/APEX_HANDOFF_PHASE_42_1.md` states plainly:
*"rest403_probe.py — standalone diagnostic (stdlib only, engine-free), currently
ONLY in ~/Downloads. RECOMMENDED: copy into tools/ and commit; it proved its
worth today."* The handoff was accurate and the recommendation was simply never
carried out. The file has since been lost.

**Consequence.** This probe is the evidence base for the claim that Deriv offers
no read-only scope and that the live token is therefore **trade-scoped by
necessity** — the premise under which this project accepts a Trade-scoped
credential at all, compensated by code guards. Its *finding* survives, quoted
verbatim in the handoff: `403 "Insufficient scopes"` on
`GET /trading/v1/options/accounts`. The means to reproduce it does not. If
Deriv's scope behaviour ever changes, the check that established the premise
cannot be re-run.

`testing/diagnostics/deriv_rest_auth_probe.py` exists and is excellent for
credential diagnosis, but it tests authorization, not scope refusal. It is not a
substitute.

**Recommended:** rewrite the scope probe and commit it, next time the token
behaviour is being examined anyway.

## A2. `docs/PHASE_42_1_BOUNDARY_AGREEMENT.md` — **NEVER EXISTED. Not recoverable.**

Investigated 2026-11-16, four ways, all negative:

| Check | Result |
|---|---|
| `Test-Path .\docs\PHASE_42_1_BOUNDARY_AGREEMENT.md` | False |
| `git log --all -- docs/PHASE_42_1_BOUNDARY_AGREEMENT.md` | **empty** — never committed on any branch |
| `git log --all --diff-filter=D -- "*PHASE_42_1*"` | **empty** — never deleted |
| `Downloads\APEX_ULTRA\docs\` | Only `APP_COMPLETION_PLAN.md` and `ENGINE_MANIFEST.md`, both unrelated and months older |

`docs/APEX_HANDOFF_PHASE_42_1.md:55` lists it under "What this phase added /
changed" as *"locked five-point agreement."* **The handoff does not record what
the five points were.** The substance is not preserved anywhere.

**Telling detail:** `docs/PHASE_42_1_ADDENDUM.md`, listed two lines below it in
the same section, **is** in the repo. One of the two was committed and the other
left no trace in git, on disk, or in the old working directory. The likeliest
reading is that the agreement was never written as a file and the handoff listed
it aspirationally.

**What this means.** Phase 42.1 has **no pre-registration document**. Its code is
sound and independently verified — `_last_sign` probed HIT at `1a7848e`, CP3
passes every session, the guards hold — but 42.1's *claims* are not checkable
against a locked agreement the way Phases 46, 47 and 48's are. This is the phase
whose handoff is this project's standing session context.

**Not reconstructable, and should not be.** Writing a "boundary agreement" for
Phase 42.1 now, from memory and after the fact, would be a pre-registration
authored in full knowledge of the results — precisely the thing these documents
exist to prevent. **The correct action is to amend the handoff to state that no
agreement was committed**, and leave it at that.

---

# NEW — raised in the 2026-11-16 session

## N1. The fetcher did not emit the Amendment v0.10 identity fields — **FIXED 2026-11-16**

v0.10 requires a bounded instrument-identity check (first/last/min/max close,
first and last raw records). The tool wrote none of them, so every phase had to
compute them by hand — and **after a seal, that requires a committed script**,
because the commit-before-read rule binds. For D2 it was done by console command
at acquisition time, before the seal existed.

**Now emitted by the tool.** The summary gains `first_close`, `last_close`,
`min_close`, `max_close`, `first_record`, `last_record` and an
`identity_check_note`. Values are derived from the epoch-keyed `candles` dict
already in memory — no additional requests, and no change to pagination, the
substitution defence, gap handling, stop conditions, or the `.jsonl` output.

**Why the raw records are included despite duplicating the `.jsonl`:** once a
dataset is sealed, the summary is the only readable artifact. Holding the first
and last records there lets a future phase re-verify instrument identity without
opening sealed data at all.

**Verified** by a throwaway `--days 1` fetch on `frxEURUSD` (deliberately not
`frxGBPJPY`, so the artifact could not be mistaken for sealed data; both files
deleted afterwards). The fields were emitted correctly, with closes of
**1.09924–1.12504** — a pair quoted near unity, which is exactly the case the
v0.10 check exists to exclude.

**Known and intended consequence:** the D1 and D2 summaries predate this change
and do not carry the fields. They are **not** regenerated — their identity
checks live in their seals. Future summaries therefore differ in shape from the
two sealed ones.

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

## N10. Loose duplicates of repo files in the former parent directory

**Observed 2026-11-16** while moving the repo out of `Downloads`. The old parent
`C:\Users\dagma\Downloads\APEX_ULTRA\` holds ~47 entries, including:

- **`deriv_rest_auth_probe.py`** and **`rest_transport.py`** loose at the top
  level — the exact filenames of `testing/diagnostics/deriv_rest_auth_probe.py`
  and `infrastructure/broker/deriv/rest_transport.py`, the two files this
  session relied on to diagnose the token failure and to establish the
  `DERIV_APP_ID` trap. Today's commands ran from inside the repo, so Python
  resolved the real modules — that was working-directory luck, not a guard.
- A **browser re-download family**: `ApexV5_COMPLETE_1.jsx`, `_4`,
  `..._TradeReview_1/_2/_3.jsx`, `..._HeatEngine_1.ts`,
  `..._AdaptiveSizing_1.ts`, `APEX_ULTRA_EMA_RSI_1.xml`.
- A **second `docs\` directory** at that level. This project's standard install
  step is `Copy-Item $HOME\Downloads\<file> .\docs\<file>`, which lands
  somewhere different depending on the working directory.

**Same family as Section G.3**, the standing rule since the session002 incident
that required deleting `Downloads\trading bot\files (80)\ema_cross.py` — G.3 is
verified met, but the rule it encodes is not being applied generally. The
deferred-fixes list already records this project being bitten once by a
browser-saved duplicate (`screen_candidates (1).py`) being picked up instead of
the intended file.

**Not acted on.** Nothing was deleted; the repo was moved out instead, which
removes the adjacency. Resolve by deciding what in that directory is still
wanted, rather than by bulk deletion. Note `APEX_V6_demo_review_2026-11-16.md`
there is dated the same day and its provenance is unestablished.

## N11. Summaries carry no SHA-256, though Section D.4 requires it

**Section D.4** of the boundary agreement: *"SHA-256 of each completed data file
computed and recorded in its summary at acquisition time, before any analysis
exists."*

**The tool has never done this.** Verified 2026-11-16 by reading the summaries
of all three datasets — Phase 46 `frxEURUSD`, and Phase 48 D1 and D2. None
contains a hash field.

For D1 and D2 the hashes were computed by hand and recorded in the seal
documents, so **D.4 is satisfied in substance but not literally**: the hash does
exist, before any analysis, in a committed artifact. For the Phase 46 dataset no
hash was ever recorded anywhere.

**Fix:** hash the data file between writing it and writing the summary — the
file is closed at that point, so this is a few lines and no behavioural change.
Deliberately **not** bundled into the 2026-11-16 D1/N1 patch: that change had an
agreed two-item scope, and expanding scope mid-session is how the second mistake
happens. Needs its own short plan.

Note this is the same family as N1 — a tool not emitting what an agreement
requires, with the gap covered by hand each time and nobody noticing the tool
never changed.

## N12. The Claude project mirror produces documents that never become real

**Three instances found on 2026-11-16**, which makes it a mechanism rather than
an accident:

| Document | Status |
|---|---|
| `APEX_DEFERRED_FIXES.md` | Mirror-only since 2026-08-24. Committed 2026-11-16 (`3a811b5`). |
| `PHASE_48_AMENDMENT_V0_6.md` | Mirror-only since 2026-08-20, while `v0.7` cited it and both seals claimed "v0.1–v0.10/v0.11". Committed 2026-11-16 (`d48991f`). |
| `PHASE_42_1_BOUNDARY_AGREEMENT.md` | Never existed anywhere. Cited by the Phase 42.1 handoff as a "locked five-point agreement". **Not reconstructable** — see A2. |

The first two are repaired. **The mechanism is not.** Writing a document in the
project mirror feels like producing it, and nothing checks the mirror against
`docs/`. Under filesystem-is-source-of-truth a mirror-only document does not
exist, however complete it looks and however many other documents cite it.

**Proposed standing check**, in the same family as N5: any session that writes a
durable document compares the mirror's Phase-48-era document list against
`docs/` before closing, and treats a mirror-only document as a finding. Cheap,
and it would have caught v0.6 in August.

---

# NEW — raised in the 2026-11-24 session

Raised while reading `tools/fetch_candles.py` in full for the first time,
during Phase 50 Route 4 Session 1. All three are **documentation or validation
findings only.** The tool is **frozen** under the Route 4 acquisition
agreement and none of these authorises a change to it.

## N13. D1 is recorded as FIXED, but only the docstring was corrected

The docstring now states correctly that `count` is a time window. Three
instances of the superseded claim remain in the same file:

| Instance | Location | Outlives the run? |
|---|---|---|
| `CANDLES_PER_REQUEST = 1000` with the comment `# observed server cap` | the constant | no |
| `per request   : 1000 candles` | the run banner | printed only |
| `"candles_per_request": 1000` | the summary JSON | **yes** |

The third is the one that matters: it is written into every summary artifact,
including any future sealed dataset, under a key whose name asserts a cap that
does not exist.

**This is also a record finding.** D1's entry above reads **FIXED**, and was
closed on the strength of the docstring alone. Same family as N12 — a document
asserting more than the filesystem supports.

**Fix:** documentation and a field rename, no behavioural change. Needs its
own short plan, deliberately not bundled with anything else, per N11's
reasoning.

## N14. Nothing validates epoch alignment to the granularity grid

`tools/fetch_candles.py` computes `gaps_over_granularity_count` — intervals
**larger** than the granularity — but nothing tests `epoch % GRANULARITY`. An
off-grid timestamp passes through silently into both the `.jsonl` and the
summary.

**This has already happened, in sealed data.** D2's first epoch is
`1786039197`, three seconds short of `1786039200` — **897 s off the
900-second boundary**. It entered the D2 seal without the tool noticing. The
seal records the offset at lines 100–101, so the fact is preserved, but it was
caught by hand rather than by the tool.

**Consequence beyond the record.** Phase 50's Route 4 agreement requires X's
grid and open/close timestamp convention to be **established from data rather
than assumed**, and both of its acquisition-boundary intervals are explicitly
conditional on that convention. This item is the evidential basis for that
conditionality: a tool that never validated the grid for the instrument it was
built for will not validate it for a new one.

**Not a fix to the frozen tool.** Recorded so that any replacement acquisition
tooling carries the check from the start.

## N15. `MAX_CONSECUTIVE_EMPTY = 4` is a thin margin against a holiday closure

On an empty response the loop steps back `WEEKEND_STEP_SECONDS = 86400` — one
day — and aborts after four consecutive empties as
`history_exhausted_consecutive_empty`.

A normal forex weekend costs two or three empties. A long holiday closure can
reach four, at which point the run stops with a `stop_reason` that **reads
like a history boundary but would be a calendar artifact**. The delivered span
would be short and the cause misattributed.

**Recorded as a risk, not a change.** The retry policy is not to be adjusted
without separate justification and review: altering it changes fetch
behaviour, and the tool is frozen.

---

# INCIDENT

## I1. Phase 46 dataset deleted by a wildcard, 2026-11-16

**The advisor wrote a `Remove-Item` glob over `engine/output/`, a directory
holding sealed and historical evidence, when the fetch had just printed the two
exact filenames that needed removing.**

```powershell
Remove-Item .\engine\output\candles_frxEURUSD_900_*.jsonl, .\engine\output\candles_frxEURUSD_900_*_summary.json
```

Intended to clear the `--days 1` smoke-test artifacts
(`candles_frxEURUSD_900_1793964024_1794863700.*`). It also matched the **Phase
46 dataset**, `candles_frxEURUSD_900_1754473235_1786008600.*`.

**What was recovered.** The `_summary.json` is tracked and was restored
immediately with `git restore`. Its content is intact: 24,257 bars, 364.993
days, 55 gaps, substitution defence at request 37.

**What was lost, on the balance of evidence.** The `.jsonl` is gitignored, so
git cannot confirm whether it was present. It is absent now. Phase 47's
`candles_cryBTCUSD_900_*.jsonl` (3,485,479 bytes) is still in that directory
from August, and there is no reason Phase 46's would have been removed while
Phase 47's was kept. **Treat it as deleted by this command.** `Remove-Item`
bypasses the Recycle Bin and the repo is not synced, so there is no copy.

**It cannot be re-fetched.** The series begins at epoch 1754473235 —
2025-08-06, more than 365 days before 2026-11-16 — which is past Deriv's served
history wall.

**Assessed impact: real but not load-bearing.**

- **No SHA-256 was ever recorded** for this file (see N11), so it could never
  have served as verifiable provenance.
- Phase 46's strategy failed, and the ceiling check at `a1ff0cf` already
  recorded the dataset as contaminated for holdout purposes. It had no future
  evidentiary role.
- Amendment v0.9's completeness benchmark of **66.4588 bars/day** was derived
  from it and is independently recorded, as are all its structural statistics,
  in the restored summary. Nothing in D1's or D2's acceptance depends on the raw
  file still existing.

What is lost is the ability to re-derive that benchmark from source, or to
compute the hash that was never taken.

**Correct command, for the record:** the two literal paths the fetch printed.
Not a glob.

**Rule going forward:** never use a wildcard delete in `engine/output/`. That
directory holds sealed datasets whose seals state in terms that an
unreproducible hash voids provenance. Deletions there name files explicitly, one
by one.

**The sealed `frxGBPJPY` files were never at risk** — the glob was EUR/USD
specific — but that was a consequence of the smoke test's symbol choice, not of
care in writing the command.

---

# ESCALATED / RESOLVED

## E1. Repo location — **DISCHARGED 2026-11-16**

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

**Both halves completed later the same day.**

**Off-machine redundancy.** The first backup attempt went to
`$HOME\Documents\APEX_SEALED_DATA` — which resolves to the literal
`C:\Users\dagma\Documents`, a local folder that is **not** the user's real
Documents and is not synced. The real Documents is redirected to
`C:\Users\dagma\OneDrive\Documentos`. Copies were made there and both hashes
reproduced a third time. The sealed datasets now exist in three locations on two
machines. Note that OneDrive Files On-Demand may dehydrate them into
placeholders; they rehydrate on access and hash correctly, but a future check
may pause to download.

**Repo moved** to `C:\Users\dagma\APEX_ULTRA\apex_ultra`. Verified after the
move: tree clean, up to date with `origin/main`, HEAD `a003511`, D2 hash
`99A22CFC…52E49E` unchanged. Deliberately **not** inside `OneDrive\` — a sync
client managing a live `.git` directory is its own corruption risk. The split is
intentional: the backup benefits from sync, the repo does not.

**Only the repo was moved**, not its former parent — see N10.

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
* **2026-11-16, later** — D1 and N1 fixed in `tools/fetch_candles.py` and
  closed. A1 and A2 investigated and resolved: `rest403_probe.py` lost, the
  Phase 42.1 agreement never existed and is deliberately not reconstructed.
  N11 and N12 raised. Amendment v0.6 found mirror-only and committed verbatim
  with a dated preamble (`d48991f`), closing the v0.1–v0.11 chain. Incident I1
  recorded: the advisor's wildcard delete destroyed the Phase 46 dataset.
* **2026-11-16** — This list committed to the filesystem for the first time.
  C1 closed; D1's deferral condition satisfied; A1 and A2 confirmed absent by
  `Test-Path`; N1–N9 raised during the D2 acquisition session; E1 partially
  mitigated by verified copies; the lock commit date verified from `git log`
  rather than inherited from the record.
* **2026-11-24** — `tools/fetch_candles.py` read in full for the first time,
  during Phase 50 Route 4 Session 1. N13–N15 raised, and D1's closure found to
  be partial. The reading also established that the tool **cannot express a
  bounded historical request** — it anchors at `latest` and walks backwards,
  with no caller-settable window — which is why Route 4's acquisition path
  must be a different mechanism and the tool is now frozen. That finding lives
  in the Route 4 agreement, not here.
