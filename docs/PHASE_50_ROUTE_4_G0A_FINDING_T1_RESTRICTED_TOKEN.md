# PHASE 50 — ROUTE 4 — G0a FINDING: T1 (RESTRICTED TOKEN) FAILS

## Result record — a negative, evidenced as such

Recorded 2026-11-25 local (America/Jamaica, UTC−05:00) / 2026-11-25 UTC,
per §0.1's dating convention. **Authorises nothing.** No tooling, no provider
assessment, no acquisition, no D1/D2 access, no hypothesis generation.

**Finding, in one line:** `runas /trustlevel:0x20000` restricts privileges and
administrative group membership but **leaves the user SID present and
enabled**, so every ACL-granted write still succeeds. T1 is rejected.

---

## 1. WHAT WAS RUN

| Run | Label | Local time | Token |
|---|---|---|---|
| Control | `NORMAL-v2` | 13:28:54 (18:28:54 UTC) | ordinary, non-elevated |
| Candidate | `RESTRICTED` | 13:30:38 (18:30:38 UTC) | `runas /trustlevel:0x20000` |

Probe: `apex_g0a_write_probe_v2.ps1`, 128 lines, reviewed before execution.
Ten locations, six write vectors each, plus a read leg, an HTTPS leg and a
leftover check. The probe establishes **effective access by writing**, not by
reading ACL entries.

---

## 2. THE RESULT — IDENTICAL, LOCATION BY LOCATION

| Location | NORMAL-v2 | RESTRICTED |
|---|---|---|
| repo root | 6 / 6 wrote | **6 / 6 wrote** |
| `docs\` | 6 / 6 wrote | **6 / 6 wrote** |
| `engine\output\` | 6 / 6 wrote | **6 / 6 wrote** |
| user `%TEMP%` | 6 / 6 wrote | **6 / 6 wrote** |
| `%LOCALAPPDATA%` | 6 / 6 wrote | **6 / 6 wrote** |
| profile root | 6 / 6 wrote | **6 / 6 wrote** |
| `C:\Windows\Temp` | 6 / 6 wrote | **6 / 6 wrote** |
| `C:\` root | 2 / 6 — `MkDir`, `InDir` | **2 / 6 — `MkDir`, `InDir`** |
| `C:\Users\Public` | 6 / 6 wrote | **6 / 6 wrote** |
| `C:\ProgramData` | 6 / 6 wrote | **6 / 6 wrote** |
| HTTPS GET | OK, 200 | **OK, 200** |
| Leftovers | none | **none** |

**Not one vector at one location differed.**

---

## 3. THE RESTRICTION DEMONSTRABLY APPLIED

Recorded because "no difference" is otherwise ambiguous between *the
restriction is ineffective* and *the restriction never ran*. This project does
not record an absence as a negative.

| Evidence | NORMAL | RESTRICTED |
|---|---|---|
| Privileges held | **5** — Shutdown, ChangeNotify, Undock, IncreaseWorkingSet, TimeZone | **1** — ChangeNotify only |
| `BUILTIN\Administrators` | deny-only (UAC filtering) | deny-only |
| User SID | enabled | **enabled** |
| Mandatory Label | Medium | **Medium** |

The privilege count is the discriminator. `BUILTIN\Administrators` showing
deny-only is **not** evidence of restriction on its own — ordinary UAC
filtering produces the same line on a non-elevated admin account. Four
privileges removed is unambiguous.

---

## 4. WHY IT FAILED, AND WHAT THAT RULES OUT

**[V] Mechanism.** The restricted token retains
`MicrosoftAccount\dagmarbrown965@gmail.com` as a **Mandatory group, Enabled**
entry. The repository, profile, Public and ProgramData ACLs grant write to
that SID. ACLs key on **identity**; the trust level restricts **privileges and
group membership**. Those are different things, and only the second was
touched.

**[R] This generalises beyond trust level `0x20000`.**

> Any isolation mechanism that leaves the same user SID present and enabled
> cannot produce a write-capability difference through ACLs.

The **entire restricted-token family is therefore rejected** for this purpose,
not merely the one trust level tested. A further restricted-token variant
would fail for the same reason.

**[A] It also splits the remaining candidates by mechanism rather than by
convenience:**

| Candidate | Changes the SID? | Orthogonal to ACLs? | Status |
|---|---|---|---|
| **T3 — separate local account** | **Yes** | — | Untested. Would work for the right reason. Costs admin rights and a password |
| **T2 — low integrity level** | No | **Yes** — integrity is checked separately from ACLs | **Untested, and mechanically distinct.** The `Medium Mandatory Level` above is direct evidence it was never applied |
| Further restricted tokens | No | No | **Rejected by §4** |
| Job object | No | No | Rejected earlier — not a filesystem access-control boundary |

---

## 5. A SECOND FINDING, INDEPENDENT OF T1

**[V] The `C:\` root escalation is demonstrated, not theorised.** Under both
tokens, file creation at `C:\` is denied on all four file vectors while
`MkDir` succeeds **and `InDir` succeeds** — a process that cannot create a
file at `C:\` can create a folder there and write inside it, because it owns
what it creates.

This was found only because probe v2 added the `InDir` vector. **Probe v1
would have reported `C:\` as "mostly denied" and a T1 pass would have been
read into it.**

**[R] Consequence that survives whatever happens to T1.** It confirms the
choice already made at register v3 §4.3: the write-set audit's allowlist must
be **declared independently**, with *any* write outside it failing. A
forbidden-location list would have missed `C:\<new folder>\inner.txt`
entirely, because nobody forbids a directory that does not yet exist. This
applies to the **two-process baseline as well**, so it is not contingent on
the architecture chosen.

---

## 6. WHAT THIS FINDING DOES **NOT** ESTABLISH

- It does **not** show that no isolation mechanism exists. It rejects one
  family, with a reason, and leaves two candidates untested.
- It does **not** settle the bound. Per the isolation test §6 the agreed bound
  was T1 then T3; §4 above is new evidence that T2 is mechanically distinct,
  which the CEO may or may not treat as grounds to revisit that ordering.
- It does **not** affect the two-process baseline's viability. That design
  never depended on a capability boundary.
- It does **not** approve or withdraw amendment A1. A1 remains **proposed and
  conditional**; it is withdrawn only if the isolation question closes
  negative overall.

---

## 7. PROVENANCE OF THIS FINDING

Captured **before** the probe was committed, not reconstructed afterwards.
Recorded because deferred-fixes **A1** is the standing example of the
alternative: `rest403_probe.py` was lost, its finding survives only as a
quotation, and the check that established the premise can no longer be re-run.

| | |
|---|---|
| Script | `apex_g0a_write_probe_v2.ps1`, 128 lines |
| SHA-256 | `85162694B0D9976D469A663E30A207BD5642D1AA24DD7617C628D7866207159D` |
| Hash verified | On both sides before installation — the file as transmitted and the file as executed are byte-identical |
| Committed to | `testing/diagnostics/apex_g0a_write_probe_v2.ps1`, alongside `deriv_rest_auth_probe.py` |
| PowerShell | 5.1.26100.9818 |
| Operating system | Microsoft Windows 11 Home, build 10.0.26300.0 |
| Control run | `NORMAL-v2`, from the Downloads copy |
| Candidate run | `RESTRICTED`, from a staged copy at `C:\Windows\Temp` — same file, same hash; staged because a restricted token may be unable to read the profile. The staged copy was removed by explicit path afterwards |

**[R] The result in §2 is the result of *this* script version.** Any future
re-run must verify the hash above before its output is compared with §2, and
a modified probe produces a new finding rather than a confirmation of this
one.

**[A] What the provenance does not cover.** It records the environment and the
script, not the machine state — other processes, pending updates and ACL
changes since the run are not captured. A re-run on a materially changed
machine is a new test.

---

## 8. DECISION PENDING

| Option | Cost | Consequence |
|---|---|---|
| **Run T3** — separate local account | Admin rights; a password in the workflow, against the project's credential discipline; repo read-grant without write | If it passes, three-process architecture is feasible and A1 proceeds |
| **Run T2 first** — low integrity | Needs a launcher; may break the transport (L3) | Mechanically the cheaper of the two if it works |
| **Stop now** — adopt the two-process baseline | None | A1 withdrawn; F8 rests entirely on the dynamic audit across six reject paths, as recorded in the process enumeration §9 |

**No option is taken by this document.**
