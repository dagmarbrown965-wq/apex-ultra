# PHASE 50 — ROUTE 4 — G0a PROCESS ENUMERATION OF THE ACQUISITION PATH

## G0a ARTIFACT — evaluation candidate, not an approved architecture

Produced 2026-11-25 under the CEO's direction to enumerate three processes
first, with the two-process design retained as the baseline alternative.

**Authorises nothing.** No gate passes by choosing a design. G0a remains in
progress. No tooling, no provider assessment, no acquisition, no D1/D2
access, no hypothesis generation. Agreement v8 remains G0-approved and
unapproved as a whole.

**Why this document exists.** Register v3 §5.7 requires the acquisition
path's processes to be enumerated **before** the §14.14 Windows write-set
mechanism can be assessed, because coverage is per process and per write
path. Enumerating them turned out to do more than fix the mechanism's scope —
**the split itself changes how much the mechanism has to prove.**

### Two findings the CEO should see before the detail

1. **§4 — the three-process design breaks agreement v8 §7.6's exhaustive
   two-channel declaration.** A third channel appears, carrying raw validated
   payload between processes. Adopting this architecture therefore requires an
   **amendment to a G0-approved agreement**, not merely a G0a design note.
2. **§6 — OS-enforced write denial between processes of the same Windows user
   is not achievable with file ACLs**, because they share a SID. This is the
   most likely route to the three-process design proving impractical, and it
   should be tested early rather than discovered at implementation.

---

## 1. WHAT THE SPLIT DECIDES

| | Two processes | Three processes |
|---|---|---|
| P1 durable write capability | **Present** | **Absent by design** |
| F8 rejection assurance | Observe **absence of writes** on every reject path | Verify a **permission and capability boundary** |
| Windows mechanism burden | Must establish P1 did not write, on all paths | Narrowed; still required for indirect writes |
| Rejected payload reaching persistence | Prevented by P1 behaving correctly | Prevented by process and interface separation |
| Inter-process complexity | Lower | **Higher** |
| Principal residual risk | Audit fidelity and reject-path coverage | IPC boundary, permission configuration, OS-mediated indirect writes |

**[A] The burden the two-process design carries, quantified.** Register v3
§4.2 lists seven execution paths the audit must exercise — pass, C5 failure,
C6 failure, malformed-entry rejection, empty return, transport error and an
uncaught-exception path. Under two processes, **six of those are reject paths
on which F8 rests entirely on observing an absence**, with every fidelity
question about the Windows mechanism attached to each. Under three processes
the structural boundary carries most of that, and the audit covers the
residue.

**[R] This is the same move §7.6 already makes once.** That clause converts
*"no code dereferences this object"* — which no gate can check — into *"no
module imports this"*, which one can. The three-way split applies the same
conversion to **writes**: from *"no code writes rejected data"*, unverifiable
across future edits, to *"this process cannot write there"*, enforceable and
checkable.

---

## 2. THREE-PROCESS ENUMERATION — PREFERRED FOR EVALUATION

**[O] Preferred candidate. Not approved, and not assumed feasible until §6
and §7 are settled against Windows evidence.**

### P1 — acquisition and validation

| Property | Value |
|---|---|
| Transport access | **Yes** — the only process that has it |
| Holds raw provider payload | **Yes** — the only process that does |
| Runs | C5 (spacing), C6 (coverage, all seven §6.4 requirements) |
| Durable write capability | **None.** Not "does not write" — *cannot* |
| Emits on pass | the closed result **and** the validated payload |
| Emits on rejection | the closed result **only**, plus permitted non-sensitive diagnostics per §7.8's magnitude-only record |
| Never emits | raw or partial payload on any rejection or error path |

### P2 — persistence

| Property | Value |
|---|---|
| Transport access | **None** |
| Receives | a passing closed result and its validated payload, only |
| Can receive a rejected payload | **No** — not through any defined interface |
| Writes | the permitted dataset and summary (§10.5) |
| Durable write capability | **Yes** — the only process that has it |

### P3 — hypothesis-generation consumer

| Property | Value |
|---|---|
| Transport access | **None** |
| Receives | persisted, admitted exploratory data |
| Route to rejected payloads | **None** |
| Subject to | the existing generation-phase restrictions and approvals |
| C9 test (i)/(ii) applies to | **this process** — module graph and channel allowlist |

---

## 3. DATA FLOW, AND WHERE RAW DATA CAN EXIST

| Location | Raw payload | Validated payload | Closed result | Accepted dataset |
|---|---|---|---|---|
| Provider → P1 | **yes** | — | — | — |
| P1 memory | **yes** | yes | yes | — |
| P1 → P2, channel 2 | **no** | yes, on pass only | — | — |
| P1 → P2/record, channel 1 | no | no | yes | — |
| P2 memory | **no** | yes | yes | yes |
| Durable storage | **no** | — | magnitude-only record | yes |
| P3 | **no** | — | yes | yes |

**[R] The invariant this table encodes:** raw provider payload exists in
exactly one process and never crosses a boundary. What crosses on a pass is a
payload that has already satisfied C5 and C6.

---

## 4. FINDING — THE CHANNEL COUNT CHANGES, AND THE AGREEMENT SAYS TWO

Agreement v8 §7.6 declares the permitted channels **exhaustively**: channel 1,
the closed result, inspector → consumer; channel 2, the accepted dataset,
inspector writes and consumer reads. Gate test (ii) then requires that every
external channel reference map to one of those two.

The three-process design has **three**:

| # | Channel | Carries | Opens when |
|---|---|---|---|
| 1 | P1 → P2 result | closed result type | always |
| **2 (new)** | **P1 → P2 validated payload** | **raw market data, post-validation** | **pass only** |
| 3 | P2 → P3 accepted dataset | the persisted dataset and summary | after persistence |

**[R] Consequence.** §7.6's declaration was written for a two-process world
and states a **global** count. It must be restated **per boundary** —
P1→P2 and P2→P3 have different permitted channels and different contents. The
allowlist logic of test (ii) survives intact and applies unchanged to P3; what
changes is the enumeration it checks against.

**[O] Process point, not a drafting point.** Agreement v8 is **G0-approved**.
Adopting the three-process architecture therefore requires an **amendment**,
with the amendment itself subject to the standing two-way sweep (register v3
§5.6) across descriptions, requirements, gate definitions and approval
criteria. It should not be absorbed silently into a G0a design note.

---

## 5. FINDING — VALIDATE FULLY BEFORE ANY BYTE CROSSES CHANNEL 2

The CEO's open item 4 asks that P2 cannot receive a rejected payload
*including through partial messages, stale buffers or error paths*. There is
one architectural decision that settles most of it.

**[R] PROPOSED rule: buffer and validate to completion, then transfer. Never
stream-and-validate.** If P1 streams the payload to P2 while validating — the
obvious performance choice — then a rejection discovered mid-stream leaves P2
holding a **partial rejected payload**, and the whole structural argument
collapses into the two-process case with extra steps.

Channel 2 therefore opens **only after** C5 and C6 have returned a pass over
the complete payload. Before that point the channel carries nothing.

**[A] The cost is memory.** P1 must hold the entire response before
transferring. At the scale in question — a single exploratory window at
900 s granularity — this is a few megabytes and not a constraint. It would
become one for a much larger acquisition, and that is a reason to bound the
window, not to relax the rule.

**[O] Residual for G0a:** stale buffers and error paths on channel 2 itself —
a transfer interrupted after a pass, leaving P2 with a partial *validated*
payload. Not a containment breach, since the data passed, but it is a
data-integrity case P2's acceptance logic must handle rather than ignore.

---

## 6. FINDING — OS ENFORCEMENT IS THE LIKELY FEASIBILITY WALL

The CEO's open item 5 requires boundaries enforced by the operating system
rather than asserted by application logic. This is where the design is most
likely to fail, and it should be tested first.

**[V] The problem.** If P1, P2 and P3 all run as the same Windows user, they
share a **SID**. File ACLs grant and deny by SID, so **no ACL can permit P2 to
write a directory while denying P1**, when both run as that user. "P1 cannot
write" is not achievable by permissions alone in the default single-account
arrangement.

**[O] The options, each with a real cost — G0a must pick one and evidence
it:**

| Option | Mechanism | Cost / risk |
|---|---|---|
| Separate local account for P1 | distinct SID, ordinary ACLs deny durable write | a second account, credential handling, scheduled-task or `runas` plumbing on a single-user machine |
| Restricted token | `CreateRestrictedToken` with deny-only SIDs or removed privileges | P1 must be launched through it; needs verification that the restriction actually covers the durable paths |
| AppContainer / low-integrity process | integrity levels deny writes to medium-integrity locations | strong, but affects everything P1 touches, including the transport and TLS stores |
| Job object with filesystem restrictions | kernel-enforced limits on the process | partial coverage; not a general filesystem deny |

**[A] Honest statement of where this leaves the architecture.** Until one of
these is demonstrated on the target machine, **"P1 cannot write durably" is a
design intention, not an enforced boundary** — and the three-process design's
advantage over the two-process baseline is unrealised. The advantage is
contingent on this, not delivered by the diagram.

**[R] Therefore this is the first thing G0a should test**, before the
§14.14 mechanism choice and before any tooling design. A negative result here
returns the project to the two-process baseline with its heavier audit burden,
and that is a decision better taken in week one than at implementation.

---

## 7. G0a EVALUATION ITEMS — THE CEO'S FIVE, AS TESTABLE QUESTIONS

| # | Must establish | Evidence type |
|---|---|---|
| 1 | P1's **actual effective** permissions, including inherited permissions and alternate write paths | structural |
| 2 | Whether **IPC can spill to disk** — temporary files, named-pipe buffering, memory-mapped backing | structural + dynamic |
| 3 | Whether **logging, exception handling, crash dumps, memory-mapped files, paging or child processes** can create prohibited durable artifacts | dynamic |
| 4 | That **P2 cannot receive a rejected payload**, including partial messages, stale buffers and error paths | structural (§5's rule) + dynamic |
| 5 | That the boundaries are **enforced by the OS**, not asserted by application logic | structural (§6) |

**[R] Item 3 is not narrowed by the three-process design.** Crash dumps,
paging and child processes are OS-mediated writes that a permission boundary
on P1 may or may not cover — a crash dump is written by the OS or a reporting
service, not by P1. Register v3's core-dump residual (14.12) survives this
architecture unchanged.

---

## 8. ACCEPTANCE CRITERIA — STRUCTURAL AND DYNAMIC, KEPT SEPARATE

Per **P1** of the agreement: these are different controls with different
failure modes and must not be reported as one result.

**8.1 Structural permission checks — preventive, if OS-enforced.**
- P1's effective token and the ACLs on every durable location, asserted
  against an **independently declared** allowlist (register v3 §4.3).
- P3's module graph excludes the transport, the inspector and the
  raw-response type.
- Each boundary's permitted channels enumerated, and every external reference
  mapped to one — per boundary, per §4 above.
- **Pass means the capability is absent.** Not that it was unused.

**8.2 Dynamic write-set audit — detection, one-way.**
- Still required, and still one-way: an unexpected write disqualifies, a clean
  audit does not establish absence under an unexercised path.
- Exercised over register v3 §4.2's seven execution paths, including the
  uncaught-exception path.
- Covers the OS-mediated routes of item 3, which the structural check cannot
  reach.

**[R] Neither result may be summarised into the other.** A passing structural
check does not make the audit unnecessary; a clean audit does not establish a
capability boundary.

---

## 9. TWO-PROCESS BASELINE — RETAINED

**[R] Retained as the fallback**, to be adopted only if the three-process
transfer boundary proves impractical or cannot be verified (§6).

Its burden is recorded so the fallback is not taken as equivalent: **F8 rests
entirely on observing the absence of writes across six reject paths**, with
the Windows mechanism's fidelity attached to each, and with no structural
boundary behind it. The design is simpler; the assurance is weaker, and the
weakness is concentrated exactly where register v3 §4.3 said a blind spot
would be invisible in the artifacts.

---

## 10. WHAT THIS DOES NOT CHANGE

- **No gate passes by choosing a design.** G0a remains in progress.
- **Three processes are preferred for evaluation, not approved**, and not
  assumed feasible until §6 is settled on the target machine.
- **The Windows write-set question is narrowed, not eliminated** (§7 item 3).
- **Agreement v8 would require amendment** if this architecture is adopted
  (§4), with the standing sweep applied.
- Nothing here authorises tooling, acquisition, provider assessment, D1/D2
  access or hypothesis generation.
