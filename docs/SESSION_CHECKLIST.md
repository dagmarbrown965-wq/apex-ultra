# APEX ULTRA — standing session checklist

**Created 2026-11-16.** Consolidates checks that already existed but were
scattered — several of them only in the Claude project instructions, which is
to say only in a mirror and not on the filesystem. That is the failure this
document also exists to stop (deferred-fixes N12).

Nothing here is new policy. Each item cites where it came from.

---

## 1. Session open — always

```powershell
git status                                      # clean tree, up to date with origin
py -m engine.validation.test_m0_regression      # PASS (3/3)
py -m engine.validation.check_cp3_imports       # CP3: PASS
Select-String -Path .\engine\strategy\ema_cross.py -Pattern "_last_sign"   # must HIT
```

Expect a clean tree apart from the known untracked artifacts in
`engine/output/` — roughly seventeen rejected Phase 44 session journals and
summaries, deliberately untracked. Their exclusion encodes a validity decision,
which is why Section D.7 forbids `git add -A`.

CP3 PASS is the compensating control for a Trade-scoped token. It is verified,
never weakened.

## 2. Record integrity — before closing, and before relying on any citation

```powershell
py -m tools.check_record_integrity
```

Reports cited-but-absent paths and gaps in amendment chains. Exit 0 clean, 1 on
findings. Known-absent paths live in `tools/known_absent.txt` with reasons;
adding a line there should be deliberate, not a way to silence the tool.

It also covers `engine/output/`, so a sealed dataset going missing is reported.

## 3. Mirror versus filesystem — the check no tool can do

**Compare the Claude project's document list against `docs/` before closing a
session.** A document written in the project mirror is not real. Under
filesystem-is-source-of-truth it does not exist, however complete it looks and
however many other documents cite it.

Three instances were found on 2026-11-16 alone:

- `APEX_DEFERRED_FIXES.md` — mirror-only since 2026-08-24.
- `PHASE_48_AMENDMENT_V0_6.md` — mirror-only since 2026-08-20, while `v0.7`
  cited it and both Phase 48 seals claimed the chain was complete.
- `PHASE_42_1_BOUNDARY_AGREEMENT.md` — never existed anywhere, and deliberately
  not reconstructed.

`tools/check_record_integrity.py` cannot see the mirror. This step is manual
and has no substitute.

## 4. Deriv credentials — whenever a session touches them

**Read the dashboard first and compare it against the current
`docs/TOKEN_RENEWAL_*.md`.** A token on the dashboard that no document accounts
for is a finding. This has happened twice: `apex_trade_demo_4` unrecorded for
weeks in August, `apex_demo_test` unrecorded for two months until 2026-11-16.
Nothing enforces the one-active-token rule between renewals except this look.

Setting credentials — `Read-Host` then `cls`, never pasted into chat:

```powershell
$env:DERIV_API_TOKEN = Read-Host "pat_ token"
$env:DERIV_APP_ID = Read-Host "alphanumeric app id ONLY, not the token"
cls
"now using suffix=" + $env:DERIV_API_TOKEN.Substring($env:DERIV_API_TOKEN.Length-4)
```

**Check that printed suffix against the dashboard before trusting any result.**
A `Read-Host` that silently fails to take produced a misleading repeat failure
on 2026-11-16.

Verify with:

```powershell
py -m testing.diagnostics.deriv_rest_auth_probe
```

Expect `REST AUTH READY`, `is_virtual: 1`, and the expected `loginid`. **Do not
look for the dashboard's "Last used" column** — it no longer exists, though
`docs/TOKEN_RENEWAL_2026-08-19.md` still names it as the check that matters.

`DERIV_APP_ID` has no fallback on the fetch path. Unset, it returns HTTP 401,
indistinguishable from an expired token.

Renewal order is **create → verify → record → delete**, never create → record →
delete. Deleting the incumbent before the successor is proven leaves zero
working tokens.

## 5. Installing any file into the repo

**Every file install ends with a content probe.** Line count plus
`Select-String` for distinctive strings that must be present. A ratified
document was committed un-probed on 2026-11-16 and had to be verified after the
fact; a stale download was copied over a newer one twice because the probe was
skipped or run before the download landed.

Commit with explicit paths. Never `git add -A`.

## 6. Deleting anything under `engine/output/`

**Never use a wildcard.** Name files explicitly, one by one.

That directory holds sealed datasets whose seals state that an unreproducible
hash voids provenance. On 2026-11-16 a wildcard intended to clear two
smoke-test artifacts also matched the Phase 46 dataset, which is not
re-fetchable. See incident I1.

## 7. Sealed data

D1 `candles_frxGBPJPY_900_1755657580_1787193000.jsonl` — `E9DF6A4E…EFEE39`
D2 `candles_frxGBPJPY_900_1786039197_1794857400.jsonl` — `99A22CFC…52E49E`

Both gitignored, so **git is not a backup of them**. Copies at
`%USERPROFILE%\OneDrive\Documentos\APEX_SEALED_DATA\`, hashes verified
2026-11-16.

Not to be opened until a hypothesis is pre-registered. Any script that reads
either file must be committed to `main` **before** it runs — git history is the
audit log. A future phase using D2 as a holdout excludes `epoch <= 1787193000`
and the clipped first bar of each dataset.

**D2 is single-use.** One hypothesis spends it.

---

## Sources

Items 1 and 5 are the standing session rules carried since Phase 42.1. Item 4
draws on `docs/TOKEN_RENEWAL_2026-11-16.md` and Amendment v0.6. Items 2, 3 and 6
come from `docs/APEX_DEFERRED_FIXES.md` (N5, N12, I1). Item 7 restates the D1
and D2 seals and `docs/PHASE_48_CLOSE.md`.

Where this checklist and a boundary agreement disagree, **the agreement
governs** — this is a convenience index, not a source of authority.
