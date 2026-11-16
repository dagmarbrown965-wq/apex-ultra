# PHASE 48 — CLOSE ASSESSMENT (W48.5)

**Verdict: PASS.** The single-use holdout capability is restored.

*Assessed 2026-11-16 against `docs/PHASE_48_BOUNDARY_AGREEMENT.md` (v1.0,
`7415aa4`, verified from `git log` as dated 2026-08-16T18:05:30Z) as amended
v0.1–v0.11. Authoritative once committed to `docs/` on `main`, per the v1.0
status convention.*

---

## 1. What the phase set out to do

Phases 45, 46 and 47 tested three strategies to pre-registered standards and
none demonstrated an edge. The ceiling check at `a1ff0cf` recorded the dataset
as contaminated for holdout purposes, and Phase 47's holdout is separately and
explicitly spent by design.

The project's most load-bearing mechanism — the pre-registered, single-use
holdout — therefore had no clean data to operate on. Phase 48 existed to restore
that capability, and nothing else.

**It did.** Two datasets on one instrument, acquired and sealed, one of which
did not exist when any future hypothesis can be written.

## 2. Work items

| ID | Work | State |
|---|---|---|
| W48.0a | Independence screen | **COMPLETE** — 22 evaluated, 11 survivors, deterministic |
| W48.0b | Provenance gate | **COMPLETE** — 6 of 7 pass; `frxGBPJPY` selected by rule at `578231b` |
| W48.1 | D1 fetch | **COMPLETE** — 2026-08-19 |
| W48.2 | D1 seal | **COMPLETE** — `1a7848e` |
| W48.3 | Token renewal | **COMPLETE** — `apex_trade_demo_5`, then `_6` on 2026-11-16 |
| W48.4 | D2 fetch | **COMPLETE** — 2026-11-16 |
| W48.5 | D2 seal and close | **COMPLETE** — `f7a69cf` and this document |

## 3. The two datasets

| | D1 | D2 |
|---|---|---|
| Role | In-sample body | **Temporally clean holdout** |
| Instrument | `frxGBPJPY` 900 s | `frxGBPJPY` 900 s |
| Bars | 24,257 | 6,748 |
| First epoch | 1755657580 | 1786039197 |
| Last epoch | 1787193000 | 1794857400 |
| Span | 364.993 d | 102.063 d |
| Bytes | 2,196,813 | 611,160 |
| SHA-256 | `E9DF6A4E…EFEE39` | `99A22CFC…52E49E` |
| Seal | `1a7848e` | `f7a69cf` |

Same instrument, selected by rule before either fetch. D2 continues D1 forward
with **88.708 days** of data that did not exist when D1 was sealed, overlapping
D1 by **13.354 days**.

**Both hashes were reproduced on 2026-11-16**, D1's for the first time in 89
days. Provenance is confirmed, not assumed.

**Binding on any use of D2:** exclude all bars with `epoch <= 1787193000`
(Amendment v0.11 Clause 5). The overlap places sealed D1 in-sample material
inside D2; without the exclusion it contaminates the holdout it exists to
provide.

## 4. Section F

Every criterion that applies to each dataset passed, evaluated in order, with
none reached by rescuing an earlier failure.

D1 (`1a7848e`): provenance +0.99224 n=1990; independence 0.0548; completeness
24,257 vs 23,529 floor; substitution defence fired at request 37; 55 gaps
inventoried.

D2 (`f7a69cf`): completeness 6,748 vs 6,579.5 floor (99.48%); integrity with the
defence correctly **not** firing per v0.11 Clause 4; contiguity by recorded
overlap; 15 gaps against 15.4 predicted from D1's density; `stop_reason`
`target_reached` exactly as pre-registered.

**The acceptance values for D2 were committed at `d8f0f73`, before the fetch
ran.** The commit chain reads `1a7848e` → `d8f0f73` → `f7a69cf`: the
pre-registration sits physically between the two datasets in history. That
ordering is the mechanism this phase existed to restore, and it is auditable
without trusting anyone's account of it.

## 5. Section G preconditions — one breached

| | Precondition | State |
|---|---|---|
| G.1 | Token renewal before D2 | **Met.** `_5` in August, `_6` on 2026-11-16, expiring 2027-02-14. Its *wording* is wrong and is corrected by v0.11 Clause 6; G.1 itself remains unamended. |
| G.2 | Move the repo out of `Downloads` **before the phase generates new primary evidence** | **BREACHED.** |
| G.3 | Delete `Downloads\trading bot\files (80)\ema_cross.py` | **Met.** Verified absent 2026-11-16. |
| G.4 | CP4 trap | **Half-closed.** The stub is gone (`77f58e6`); the M0 banner still names it. |

**G.2 is recorded as a breach, not as an outstanding task.** The phase generated
the most important evidence this project holds — two sealed datasets whose
provenance depends on reproducible hashes — in a directory that browsers write
into and cleanup tools empty, after an agreement the CEO ratified said not to.
Both `.jsonl` files are caught by `.gitignore` per D.6, so the repository was
never a backup of them.

No evidence was lost. Verified copies now exist at
`%USERPROFILE%\Documents\APEX_SEALED_DATA\` with both hashes reproduced. The
move itself remains outstanding, and a second copy inside the same user profile
is not off-machine redundancy.

Recorded plainly because a precondition that is breached and then relabelled as
a to-do stops functioning as a precondition.

## 6. The Phase 47 legitimacy test

`PHASE_47_CLOSE.md` binds successor phases: *"does the proposal originate in a
REASON stated independently of this result, or in the RESULT itself?"*

**Phase 48 satisfies it by construction.** It proposed no hypothesis, so there
was nothing for a result to have originated in. The interpretive resolution
ratified 2026-08-16 — that the test prohibits selecting *content* to route
around a negative outcome, not acting on *procedural* knowledge such as knowing
a holdout is spent — was not relied upon beyond that.

## 7. What this phase does not establish

Nothing about market behaviour. No hypothesis was formed, no strategy tested,
no verdict issued about `frxGBPJPY` or any instrument. No result of Phase 48 can
support, weaken, or bear on the volatility-compression hypothesis or any other.

Phase 48 is not a successor to Phase 47 and must not be framed as fixing it.

## 8. Record-integrity findings — the method working

The phase's own documents were wrong in four places and asserted two files that
do not exist. Every one was caught by re-verifying against the filesystem rather
than trusting the record. These are findings *for* the method, not against it,
but they are recorded because a record nobody checks is the failure mode this
project has already suffered once.

1. **Section D.5 describes a fetch the frozen tool cannot perform.**
   `fetch_candles.py` has no start-epoch parameter and walks backward from
   `latest`. Found by reading the code before the fetch; resolved by Amendment
   v0.11 Clause 2 rather than by implementer discretion at the keyboard.
2. **Section G.1's "the documented failure mode is silence" is false for the
   fetch path**, which authorizes explicitly and exits 1 with `AUTH FAILED`.
   Confirmed empirically the same day. That claim had driven the renewal
   urgency, both scheduled reminders, and one of three reasons in the
   2026-09-10 anchor decision.
3. **The Deriv dashboard's "Last used" column no longer exists**, so the August
   verification standard — named there as "the check that matters" — is
   unperformable. Replaced by `testing/diagnostics/deriv_rest_auth_probe.py`,
   which is stronger.
4. **`DERIV_APP_ID` has no fallback on the fetch path**, and an unset app id
   returns HTTP 401 indistinguishable from an expired token.
5. **`tools/rest403_probe.py` does not exist.** Confirmed by `Test-Path`.
6. **`docs/PHASE_42_1_BOUNDARY_AGREEMENT.md` does not exist.** Confirmed by
   `Test-Path`. A boundary agreement is the load-bearing artifact of a phase,
   and Phase 42.1 is the phase this project's session context is built on.

A seventh, structural: **`docs/APEX_DEFERRED_FIXES.md` existed only in the
Claude project mirror** and had never been committed, so under
filesystem-is-source-of-truth the deferred-fixes list was not recorded at all.
Created on the filesystem at `3a811b5`.

Separately, an **unrecorded active Trade-scoped token** (`apex_demo_test`,
created ~2026-09-13) was found on the dashboard — the August failure recurring.
Deleted and recorded. The one-active-token rule did not fail; nothing was
enforcing it between renewals.

## 9. Disclosures carried into the record

- **Amendment v0.10** disclosed a Section E allowlist breach on D1: min/max
  close computed at advisor instruction, outside the exhaustive allowlist. The
  bounded identity check was added in response.
- **The D2 interval slipped 17 days** past the pre-registered `~2026-10-30`,
  delivering 92 days from lock against a pre-registration that weighed 75 and 90
  and chose 75. Resolved by Amendment v0.11 before the fetch, not after.
- **A prediction in v0.11 Clause 2 was wrong.** It estimated ~3.3 days of
  overlap; the actual was 13.354, because the fetch loop tests its stop
  condition after appending a batch and overshoots by up to one request window.
  Disclosed in the D2 seal §6. No criterion was adjusted in light of it.

## 10. What a successor phase inherits

**Binding, not advisory:**

1. **D2 is a single-use holdout.** Once a hypothesis is evaluated against it, it
   is spent, exactly as Phase 47's was. There is no second D2 without another
   acquisition phase and another 90-day wait.
2. **Exclude `epoch <= 1787193000` from D2** in any holdout use.
3. **Exclude the first bar of each dataset.** Both are clipped off the
   900-second boundary — D1 by 320 s, D2 by 897 s — systematic across all four
   project fetches.
4. **Commit before read.** Any script that opens either `.jsonl` must be
   committed to `main` before it is executed. Git history is the audit log.
5. **Cite the hash.** A pre-registration against either dataset states the
   SHA-256 and the commit range within which no reading script was committed.
   If a hash cannot be reproduced, that dataset's provenance is void.
6. **Forbidden until a hypothesis is pre-registered**, on both datasets: return
   autocorrelation at any lag; volatility clustering measures; ATR or any
   indicator series; compression-episode or signal counts; drawdown or trend
   statistics; plotting the price series; and any backtest, exploratory or
   otherwise. **None has been computed.**
7. **The Phase 47 legitimacy test still binds**, and any phase proposing the
   intrabar-stop-execution direction must argue the point explicitly rather than
   cite a close document as authorisation.

## 11. Recommended before a successor phase opens

- **Complete G.2.** Move the repository off `Downloads`, and put one copy of the
  sealed data somewhere off-machine.
- **Clear `docs/APEX_DEFERRED_FIXES.md` items D1 and N1** — the false docstring
  and the missing v0.10 identity fields. The Section D.1 verbatim requirement is
  now fully discharged: both fetches ran against the byte-identical tool, so the
  fix is unblocked.
- **Narrow Section G.1's wording** to name the live-observation path.
- **Adopt the standing credential check** (deferred-fixes N5): any session
  touching Deriv credentials lists the active tokens and treats a mismatch
  against `docs/TOKEN_RENEWAL_*.md` as a finding.
- **Establish whether Phase 42.1 ever had a boundary agreement**, and correct the
  record either way.

## 12. Carried forward, unresolved

- Signal density in the Phase 44 window varied by roughly two orders of
  magnitude between sessions (1 signal to 73 over a ~35-minute span). Any future
  hypothesis assuming a stable signal rate must establish that assumption rather
  than inherit it. Recorded 2026-08-16; still unaddressed.
- `engine/output/live_signals_2026-07-12_session001.jsonl` holds a journal with
  no summary, implying a session that emitted at least one signal and never
  reached session end. Unexplained.

---

## Post-close addendum — 2026-11-16, same day

**The verdict above is unchanged. This records what happened after it.**
Section 5's breach finding stands as written: G.2 *was* breached, and the phase
*did* generate its primary evidence under `Downloads`. That is a fact about the
phase and is not revised by remedying it afterwards.

**G.2 is now discharged.**

- The repository was moved to `C:\Users\dagma\APEX_ULTRA\apex_ultra`. Verified
  after the move: tree clean, up to date with `origin/main`, HEAD `a003511`, D2
  hash `99A22CFC…52E49E` unchanged. Deliberately not inside `OneDrive\`.
- Off-machine redundancy established at
  `C:\Users\dagma\OneDrive\Documentos\APEX_SEALED_DATA\`, both hashes reproduced
  a third time. An earlier copy to `$HOME\Documents` had landed in a local
  folder that is not the user's redirected Documents and is not synced.

Section 11's first recommendation is therefore complete. The rest stand.

**One finding arose from the move**, recorded as N10 in
`docs/APEX_DEFERRED_FIXES.md`: the former parent directory holds loose copies of
`deriv_rest_auth_probe.py` and `rest_transport.py` — the two files this session
depended on — plus a family of browser re-download duplicates and a second
`docs\` directory. Same class as the Section G.3 rule. Today's commands resolved
the correct modules only because they ran from inside the repo.

---

## Decision log

* **2026-11-16** — D2 fetched and sealed; Amendment v0.11 ratified before the
  fetch; token renewed to `apex_trade_demo_6`; an unrecorded third token found
  and deleted; the deferred-fixes list committed to the filesystem for the first
  time; both sealed hashes reproduced and backed up; the lock commit date
  verified from `git log`; G.3 verified met and G.2 recorded as breached. Phase
  48 assessed **PASS** on this document.
