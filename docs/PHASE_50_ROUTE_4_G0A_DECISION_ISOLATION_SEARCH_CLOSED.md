# PHASE 50 — ROUTE 4 — G0a DECISION: ISOLATION SEARCH CLOSED

## Three-process architecture rejected. Two-process baseline adopted for review.

Decided 2026-11-25 local (America/Jamaica, UTC−05:00) by the CEO, on the
bounded-scope rule set before the search began.

**Authorises nothing.** The agreement and every remaining gate still apply. No
tooling, no provider assessment, no acquisition, no D1/D2 access, no
hypothesis generation. Adopting a fallback design is not progress through a
gate.

---

## 1. THE DISPOSITION, STATED PRECISELY

**[R] The three-process architecture is rejected on the available evidence
and the bounded-scope decision.**

**[R] T3 was not run. It is therefore not a failed test.** The distinction is
deliberate: this record contains one experimental result (T1) and one
*predicted* failure mode (T3), and they carry different weight. Nothing below
should be cited as "T3 failed".

**[R] No claim is made that every possible Windows isolation mechanism is
impossible.** One family was tested and rejected with a reason; one candidate
was predicted to fail on stated grounds and not pursued; one (low integrity,
T2) remains untested and outside the agreed bound. The search was **stopped at
a bounded cost**, which is a decision, not a proof.

---

## 2. THE EXPERIMENTAL RESULT — T1

Recorded in full at `docs/PHASE_50_ROUTE_4_G0A_FINDING_T1_RESTRICTED_TOKEN.md`
(committed `5000201`), with its probe at
`testing/diagnostics/apex_g0a_write_probe_v2.ps1` (committed `5267a09`,
sha256 `85162694B0D9976D…`).

| Leg | Result |
|---|---|
| **L1** — P1 denied durable write | **FAILED totally.** Ten locations, six vectors, byte-identical to the control |
| **L2** — P2 retains writes | Passed **vacuously** — nothing was denied to anyone, so the leg was established by the control, not the candidate |
| **L3** — P1 can still fetch | Passed. `HTTPS GET : OK status 200` |

The restriction demonstrably applied — five privileges reduced to one — so
this is an evidenced negative rather than an inconclusive run. It failed
because the restricted token leaves the **user SID present and enabled**,
while ACLs key on identity. That reasoning rejects the whole restricted-token
family, not one trust level.

---

## 3. THE PREDICTED FAILURE — T3, NOT RUN

**[V] The four observations**, all from the T1 run's own output:

| # | Observation | Source |
|---|---|---|
| 1 | `BUILTIN\Users` was **enabled** in the restricted token | `whoami /groups`, RESTRICTED |
| 2 | `C:\Users\Public` — 6 / 6 vectors wrote | probe, both runs |
| 3 | `C:\ProgramData` — 6 / 6 vectors wrote | probe, both runs |
| 4 | `C:\Windows\Temp` — 6 / 6 vectors wrote, and `C:\` root wrote via `MkDir` + `InDir` | probe, both runs |

**[A] The inference, declared as an inference.** Those four locations grant
write to the **Users group**, not to a specific user. A separate local account
changes the SID and therefore defeats ACLs granted to the existing user — the
repository, the profile, `%TEMP%`, `%LOCALAPPDATA%`. It does **not** remove
the new account from `BUILTIN\Users`, because new local accounts join that
group by default. T3 as scoped would therefore be expected to fail L1 at those
four locations.

**[A] The second half of that inference is not verified on this machine.**
That new local accounts join `BUILTIN\Users` is a documented Windows default,
not something this session tested. The prediction rests on it.

**[R] What T3 would additionally require to pass:** explicit Deny-Write ACEs
for the new account on `C:\Users\Public`, `C:\ProgramData`, `C:\Windows\Temp`
and `C:\` — **machine-wide ACL modification outside the repository**, with
effects on software unrelated to APEX, on top of administrator rights and a
password in the workflow.

**[R] That is a materially larger intervention than the bound contemplated
when it was set.** The purpose was to establish a practical isolation
boundary, not to undertake progressively more invasive Windows security
modification. The benefit does not justify the expansion.

---

## 4. CONSEQUENCES

**4.1 [R] Amendment A1 is WITHDRAWN**, not shelved — per A1's own §5. The
three-process channel enumeration it proposed has no architecture to serve.
Agreement v8 §7.6's **global two-channel declaration therefore stands
unamended**, and no change to the G0-approved agreement is required by this
decision.

**4.2 [R] The two-process architecture is adopted as the design for review** —
process enumeration §9 — subject to its own requirements and its own review.
Adoption is not approval.

**4.3 [R] Falling back does not make the open problems disappear.** The
two-process design never depended on a capability boundary, so nothing it
needs has been lost; but equally nothing it owes has been discharged:

- **F8 now rests entirely on observing the absence of writes** across the six
  reject paths of register v3 §4.2, with no structural boundary behind it.
- **§14.14's Windows write-set mechanism question reverts to full weight.**
  The three-process design would have *narrowed* what that mechanism had to
  prove. With it rejected, the mechanism carries the whole load again, and it
  remains the item most likely to return negative.
- Register v3's core-dump residual (14.12), the IPC-spill question and the
  rejection-path coverage requirements are all unchanged.

**4.4 [R] Evidence retained.** The T1 finding and the probe stay in the
repository. The probe's hash ties the finding to the exact script that
produced it — the link deferred-fixes **A1** lost for `rest403_probe.py`.

**4.5 [R] This decision does not advance any gate.** G0a remains in progress.
G1 has not started. No provider has been assessed.

---

## 5. THE STANDING SWEEP THIS TRIGGERS

Register v3 §5.6 requires a two-way sweep after **every** change to a
classification, a control, a gate or an approval criterion. This decision
changes an architecture, so the sweep is owed. **It is not performed in this
document** — listed here so it is not quietly skipped.

| Target | What must be checked |
|---|---|
| `AMENDMENT_A1…` | Mark **WITHDRAWN** on its face, so the committed file does not read as live. Same defect class as D1 reading "FIXED" |
| `…PROCESS_ENUMERATION` §2–§8 | Now describe a **rejected** candidate. Needs a status banner, not deletion — the reasoning is the record of why |
| `…PROCESS_ENUMERATION` §9 | Two-process is now **adopted for review**, not "retained as fallback" |
| `…WINDOWS_ISOLATION_TEST` | Record its outcome: T1 run and failed, T3 not run, search closed |
| Register v3 §3 | F8's gate mapping — acceptance evidence now rests wholly on the dynamic audit |
| Register v3 §14.14 | Note that the mechanism question has reverted to full weight (§4.3) |
| Agreement v8 | **No change required.** §7.6 stands as approved; recorded so the absence of a change is deliberate rather than overlooked |

---

## 6. THE 4 DECEMBER DECISION IS SEPARATE

**[R]** Kept apart deliberately. On that date the question is whether **Route 4
is worth proceeding through its remaining gates** — not whether a three-process
boundary could be made to work on Windows.

**[R] Nine days remaining is not a reason to expand technical scope.** It is a
reason to decide, on what is known, whether the gate sequence is worth
running.
