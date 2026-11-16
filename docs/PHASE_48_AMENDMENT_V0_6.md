# Phase 48 — Amendment v0.6

---

> ## COMMIT-TIME PREAMBLE — added 2026-11-16, not part of the original amendment
>
> **This amendment was authored 2026-08-19 and was never committed to the
> repository at that time.** It existed only in the Claude project mirror
> (created there 2026-08-20) until it was discovered missing on 2026-11-16,
> during the Phase 48 close-out, by listing `docs/` and noticing the sequence
> jumps from v0.5 to v0.7.
>
> `git log --all` confirms it was **never committed under this name and never
> deleted**. `docs/PHASE_48_AMENDMENT_V0_7.md:4` nonetheless cites it as part of
> the amendment chain, and both Phase 48 seals describe the boundary agreement
> as amended "v0.1–v0.10" and "v0.1–v0.11". The chain had a documented link with
> no file behind it.
>
> **The text below is committed verbatim from the mirror. Nothing in it has been
> altered, corrected, or updated.** Where it is now known to be wrong, it is
> left wrong and corrected elsewhere:
>
> - Its **credential-verification standard** — the Deriv dashboard's "Last used"
>   column — **no longer exists in Deriv's UI** as of 2026-11-16. Superseded by
>   `docs/TOKEN_RENEWAL_2026-11-16.md`, which substitutes
>   `testing/diagnostics/deriv_rest_auth_probe.py`.
> - `apex_trade_demo_5` was **deleted 2026-11-16** and superseded by
>   `apex_trade_demo_6` (expires 2027-02-14).
> - The D2 fetch did slip beyond mid-November, as this amendment anticipated.
>   It ran 2026-11-16 under Amendment v0.11.
>
> **Why committing it late is legitimate, where reconstructing it would not
> be.** The content is not written from memory — it exists unaltered in a
> timestamped artifact that predates every result it touches. It is operational
> (token record, renewal order, credential checks), not acceptance criteria, so
> no D1 or D2 threshold is affected by its late arrival. Contrast
> `docs/PHASE_42_1_BOUNDARY_AGREEMENT.md`, which never existed anywhere and
> which this project has decided **not** to reconstruct, precisely because
> writing one now would mean composing a pre-registration in full knowledge of
> the results.
>
> This is the third document found in 2026-11-16 to have been written in the
> Claude project mirror and never committed, alongside `APEX_DEFERRED_FIXES.md`
> (also committed that day) and the Phase 42.1 agreement (which never existed).
> Recorded as a pattern in `docs/APEX_DEFERRED_FIXES.md`.

---

**Subject:** Section G.1 (token renewal) — factual correction and closure of W48.3
**Date:** 2026-08-19
**Repo record:** `docs/TOKEN_RENEWAL_2026-08-19.md`, commit `fb46cf5`

The boundary agreement is LOCKED at `7415aa4` and is not edited in place. This
amendment corrects the factual premise of Section G.1 and records W48.3 as
complete, following the v0.1–v0.5 convention.

## What Section G.1 asserted

> `apex_trade_demo_2` expires ~2026-10-08; the D2 fetch is scheduled ~2026-10-30.

## What the Deriv dashboard showed on 2026-08-19

A single active token, `apex_trade_demo_4`, created 2026-07-22, Trade scope,
expiring **2026-10-20**. No token named `apex_trade_demo_2` existed. Names `_3`
and `_4` had both been used. A renewal performed on 2026-07-22 — after the 42.1
handoff — was never recorded anywhere, so every Phase 48 document was already
stale on the day it was written.

**The conclusion of G.1 survived; its figures did not.** 2026-10-20 still
preceded the ~2026-10-30 D2 fetch, so the renewal was required for exactly the
reason stated, twelve days later than believed.

**The 75-day D2 interval is unaffected.** Its justification in Section B
reasoned about a hypothetical renewal on the lock date, not about the token then
active, so no schedule arithmetic depends on the corrected figures.

## W48.3 — closed

| Field | Value |
|---|---|
| Name | `apex_trade_demo_5` |
| Scope | Trade only |
| Created | 2026-08-19 |
| Expires | **2026-11-17** |
| Key suffix | 5452 |

`apex_trade_demo_4` deleted 2026-08-19 after the successor was verified. One
active token, per the standing rule.

Margin over the ~2026-10-30 D2 fetch is **18 days**. A scheduled check is set
for 2026-11-05. If D2 slips beyond mid-November, a further renewal is required
before it, and should be taken close to the fetch date to maximise the 90-day
window rather than immediately.

## Procedural correction carried forward

Section G.1's implied order was create → record → delete. The order actually
used was **create → verify → record → delete**. Deleting the incumbent before
the successor is proven leaves zero working tokens and a rebuild under time
pressure. The one-active-token rule governs the steady state, not every instant
of the transition. Future renewals should follow the verified order.

## Verification standard for credentials — new, generalisable

A passing engine run proves nothing about the credential it appears to use. The
live read-only path may never call `authorize`, so a valid token, an expired
token, and a stale environment variable all produce identical green output.

The check that discriminates is **external to the system under test**: the Deriv
dashboard's "Last used" column must advance for the new token and must remain
unchanged for the old one. On 2026-08-19, `demo_5` moved from "Not used yet" to
2026-08-19 while `demo_4` stayed at 2026-08-16, which is what established that
the new token was genuinely on the wire.

A last-four-characters check on the loaded environment variable
(`5452`, matching the dashboard's own masked display) is the cheap precondition:
it catches the case where the old token is still loaded before any run is made.

## Scope — unchanged

Deriv's token creation form offers exactly four scopes: Trade, Account
management, Application insights, Payments. **No read-only scope exists**,
confirmed again 2026-08-19. Trade-by-necessity holds. No code guard was altered,
weakened, or re-examined to accommodate this renewal.

Not verified this session: the demo-account selection guard (DOT..79 over
ROT..99) is not printed on the live-observation banner. Unchanged in code; not
re-observed. Recorded as not-observed rather than confirmed.
