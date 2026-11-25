# PHASE 50 — ROUTE 4 — PROPOSED AMENDMENT A1

## Per-boundary channel enumeration, replacing §7.6's global two-channel declaration

## STATUS: WITHDRAWN — 2026-11-25

**This amendment is withdrawn, not shelved**, per its own §5 and the decision
recorded in `PHASE_50_ROUTE_4_G0A_DECISION_ISOLATION_SEARCH_CLOSED.md`.

The three-process architecture it exists to serve was **rejected** on the
available evidence and the bounded-scope rule: T1 failed leg L1 completely,
and T3 was predicted to fail at four Users-group-granted locations without
machine-wide ACL changes that fall outside the agreed bound. **T3 was not
run.**

**Consequence: agreement v8 §7.6's global two-channel declaration stands
unamended.** No change to the G0-approved agreement is required. The text
below is retained as the record of what was proposed and why, and must not be
read as a live proposal.

---

**Status when raised: PROPOSED. Not adopted. Not approved.**
Raised 2026-11-25. Conditional on the §6 Windows isolation test returning
positive — if it fails, the two-process baseline stands and this amendment is
**withdrawn, not shelved**.

**Why this is an amendment and not a design note.** Agreement v8 is
**G0-approved as reviewed**. Its §7.6 declares the permitted channels
**exhaustively**, and gate test (ii) checks every external reference against
that enumeration. A three-process architecture introduces a channel that
enumeration does not contain. The existing G0 approval applies to v8 as
reviewed and does **not** extend to the changed architecture. Recording it
here keeps that distinction visible instead of letting G0a absorb it.

---

## 1. What v8 §7.6 currently says

> **The two permitted channels, declared exhaustively.** … Exactly two
> channels cross the boundary:
>
> | # | Channel | Direction | Content | Schema |
> | 1 | Result channel | inspector → consumer, unidirectional | the closed result type only | §7.8's permitted fields |
> | 2 | Accepted dataset | inspector writes, consumer reads | only a payload that passed C5 and C6 | §10.5's summary and dataset |

The count is **global** — "the boundary", singular — because the clause was
written for a two-process arrangement in which there is only one.

---

## 2. What the three-process architecture requires

Two boundaries, each with its own enumeration:

### Boundary B1 — P1 (acquisition and validation) → P2 (persistence)

| # | Channel | Direction | Content | Opens when |
|---|---|---|---|---|
| B1.1 | Result | P1 → P2, unidirectional | the closed result type only | always |
| B1.2 | **Validated payload** | P1 → P2, unidirectional | market data **that has already passed C5 and C6 in full** | **pass only** |

### Boundary B2 — P2 (persistence) → P3 (hypothesis-generation consumer)

| # | Channel | Direction | Content | Opens when |
|---|---|---|---|---|
| B2.1 | Accepted dataset | P2 writes, P3 reads | the persisted dataset and summary (§10.5) | after persistence |
| B2.2 | Result | P2 → P3, unidirectional | the closed result type only | always |

---

## 3. The amendment

**A1.1** Replace §7.6's global "exactly two channels cross the boundary" with
a **per-boundary enumeration**: each process boundary declares its own
exhaustive channel list, with direction, content and schema.

**A1.2** Gate test (ii)'s **logic is unchanged** — every external channel and
resource reference is enumerated and must map to a declared channel, with any
unmatched reference failing the gate. What changes is that the test is applied
**per boundary**, against that boundary's list. The allowlist form, and the
reason for it (an allowlist fails unknown mechanisms by default, a blocklist
passes them), survive intact.

**A1.3** Add the transfer invariant as a channel condition on **B1.2**:

> P1 must complete validation of the entire response before any payload bytes
> are made available to P2. Channel B1.2 carries nothing until C5 and C6 have
> returned a pass over the complete payload. **Streaming while validating is
> prohibited**, because a rejection discovered mid-stream would leave P2
> holding a partial rejected payload and collapse the structural separation
> into the two-process case.

**A1.4** Record that **B1.2 is the only channel in the architecture that
carries market data between processes**, and that it is therefore the surface
on which the §4 evaluation items concentrate.

---

## 4. What this amendment does **not** do

- It does **not** establish that the three-process architecture is feasible.
  That turns on the Windows isolation test, which is unrun.
- It does **not** weaken test (ii). The allowlist discipline is unchanged.
- It does **not** reduce the dynamic write-set audit's scope. Register v3
  §4.3 and the core-dump residual (14.12) survive unchanged.
- It does **not** claim that buffering in memory keeps bytes off durable
  storage. Paging, crash dumps and OS-managed diagnostics are separate
  concerns and remain open.

---

## 5. Procedure before adoption

1. The §6 Windows isolation test returns positive, for both legs — P1 denied,
   P2 retained.
2. The **standing two-way sweep** (register v3 §5.6) is run across
   descriptions, requirements, gate definitions and approval criteria, not
   only §7.6.
3. The affected clauses are re-reviewed: §5's register and counts, §7.6,
   §8.7's containment capability, §12's gate rows, and register v3's §3
   control-to-gate mapping.
4. Only then is A1 adopted, as part of an agreement revision carrying its own
   G0-style review.

**If the isolation test fails, A1 is withdrawn** and the two-process baseline
stands with its full F8 detection burden, per the process enumeration §9.

---

**Nothing in this document authorises tooling, acquisition, provider
assessment, D1/D2 access or hypothesis generation.**
