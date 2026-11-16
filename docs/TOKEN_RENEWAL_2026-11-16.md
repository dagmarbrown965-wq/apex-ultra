# Token renewal — 2026-11-16

Performed during the W48.4/W48.5 session that acquired and sealed D2
(`f7a69cf`). Supersedes `docs/TOKEN_RENEWAL_2026-08-19.md` as the active token
record; that document's *verification procedure* is corrected below.

## Active token

| Field | Value |
|---|---|
| Name | `apex_trade_demo_6` |
| Scope | **Trade only** |
| Created | 2026-11-16 |
| Expires | **2027-02-14** |
| Key suffix | `c9de` |
| Key prefix | `pat_3f` (new-platform PAT, 68 characters) |
| App id in use | `33wXCuqL07IJ4XTrihUHm` |
| Account | `DOT93163679`, `is_virtual: 1` |

90 days exactly, confirming Deriv's documented cap. **Next renewal deadline:
mid-February 2027.** Nothing in Phase 48 depends on it.

Supersedes `apex_trade_demo_5` (created 2026-08-19, expiry 2026-11-17, suffix
`5452`), deleted after this record was committed. `_5` was still active and
valid on 2026-11-16; it was replaced on schedule, not after a failure.

## Correction: the "Last used" verification no longer exists

`docs/TOKEN_RENEWAL_2026-08-19.md` states that the Deriv dashboard's **"Last
used"** column is *"the check that matters"*, on the correct reasoning that repo
output alone cannot distinguish a working new token from a stale environment
variable.

**That column is no longer present in the Deriv dashboard.** As of 2026-11-16
the API token page, in both card and list view, exposes only Name, Status, Token
key, Permissions, Expiry date and Actions. A session following the August
procedure would look for a column that does not exist.

**Replacement standard, used today and recommended going forward:**

```
py -m testing.diagnostics.deriv_rest_auth_probe
```

It reports the token prefix and suffix actually in use, the app id actually
sent, the resolved `loginid`, `is_virtual`, and a live balance read — and on
failure prints the exact API payload. Today it returned `REST AUTH READY`,
`loginid DOT93163679`, `is_virtual: 1`, balance read, on suffix `c9de`.
Corroborated minutes later by the fetch banner's `auth ok (virtual account
confirmed)` ahead of a 6,748-bar acquisition.

This is **stronger** than the column it replaces. The August standard existed
because the live-observation path may never call `authorize` and therefore
cannot self-report; the probe authorizes explicitly and names what it used. It
also closes the stale-variable hole directly, by printing the suffix of the
token actually in the environment rather than the one assumed to be.

**Operating rule:** after setting the variable, print the suffix and check it
against the dashboard before trusting any result.

```powershell
$env:DERIV_API_TOKEN = Read-Host "pat_ token"
cls
"now using suffix=" + $env:DERIV_API_TOKEN.Substring($env:DERIV_API_TOKEN.Length-4)
```

This caught a silent no-op today: a `Read-Host` that did not take, which
produced an identical probe result and was briefly mistaken for a repeated
failure.

## UNRESOLVED: a third active token this project does not account for

| Field | Value |
|---|---|
| Name | `apex_demo_test` |
| Scope | **Trade** |
| Key suffix | `4ec9` |
| Expires | 2026-12-12 |
| Implied creation | ~2026-09-13 (90-day cap) |
| Status | **Active** |

No Phase 48 document, and no document in `docs/`, mentions this token. It was
created roughly four weeks after the August renewal and never recorded.

**This is the failure the August correction was written about, recurring.** That
correction found that every Phase 48 document named `apex_trade_demo_2` while
the dashboard held an unrecorded `apex_trade_demo_4`. The one-active-token rule
exists to make that impossible, and on 2026-11-16 the dashboard held **three**
active Trade-scoped tokens.

**Pending CEO identification.** If unrecognised, it should be deleted: an
active Trade-scoped credential of unknown provenance is exactly what the demo
account's compensating code guards are not designed to excuse. If recognised,
it should be documented here with its purpose and owner.

Not deleted in this session, because deleting an unidentified credential
destroys the evidence of what it was.

## A credential of unknown origin was in the environment

The session's first fetch attempt failed with `AUTH FAILED: accounts listing
failed (HTTP 401)` and the payload `"Invalid or expired token"`. The token in
`DERIV_API_TOKEN` was a well-formed 68-character `pat_` credential with prefix
`pat_9f` and suffix `0f05`.

**`0f05` matches no token in this Deriv account** — the dashboard held only
`5452` and `4ec9` at that moment. It was not persisted at User or Machine scope,
so it had been set into the process by hand.

Its provenance is undetermined: a deleted token, a token from a different Deriv
account, or a credential from elsewhere. Recorded because an unexplained
credential in a shell that also runs trade-scoped tooling is worth a line in the
record, and because it cost the session its first diagnostic round by presenting
as an expiry failure when it was an identity failure.

## The `DERIV_APP_ID` trap

The fetch path **requires** `DERIV_APP_ID` to be set explicitly.

- `infrastructure/broker/deriv/rest_transport.py:123` —
  `self.app_id = app_id or _os.environ.get("DERIV_APP_ID", "")`. **No fallback.**
- `infrastructure/broker/deriv/config_loader.py:70` — defaults to `"1089"`, but
  `tools/fetch_candles.py` constructs a `DerivRestOtpTransport` directly and
  never passes through `config_loader`.

With the variable unset, the REST accounts listing returns **HTTP 401 —
indistinguishable from an expired token**. Two different faults, one error
message. Nothing in `docs/` warned about this before today.

`docs/APEX_HANDOFF_PHASE_42_1.md:100` separately records that app ids are
**alphanumeric** on the new platform, not numeric. Do not reach for `1089`.

## Scope and guards

Scope unchanged: **Trade only**. Deriv offers no read-only scope — the creation
form lists Trade, Account management, Application insights and Payments.
Trade-by-necessity holds.

**No guard was altered to accommodate this renewal.** Verified green at
`1a7848e` immediately before the fetch:

| Gate | Result |
|---|---|
| M0 engine regression | PASS (3/3) |
| CP3 static import gate | PASS — single allowlisted lazy read-data import at `feed\live_readonly.py:77`; no execution-capable imports under `engine/` |
| `_last_sign` content probe | HIT — genuine 42.1a code |
| `LIVE_TRADING` | Observed empty before the fetch |

**Demo-account guard now observed.** The 2026-08-19 record left the
DOT..79-over-ROT..99 selection guard as *"unchanged in code; not re-observed."*
The auth probe resolved `loginid DOT93163679` with `is_virtual: 1`, and
`tools/fetch_candles.py` carries its own assertion — `is_virtual != 1` →
`BLOCKED: account is not virtual/demo.` Observed, in this path, at this HEAD.

## Order

Create → verify → record → delete, as corrected in August. `_5` remained active
and untouched throughout the session, including as the designated control for an
A/B test that proved unnecessary once `_6` authorized on first attempt. Deleting
the incumbent before the successor is proven leaves zero working tokens; the
one-active-token rule governs the steady state, not every instant of the
transition.
