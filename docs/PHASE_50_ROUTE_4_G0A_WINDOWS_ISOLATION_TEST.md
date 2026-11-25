# PHASE 50 — ROUTE 4 — G0a STEP 2: THE WINDOWS ISOLATION TEST

## Test design — unrun. Nothing here is a result.

Produced 2026-11-25 as G0a step 2 under the CEO's ordering. **Authorises
nothing**: no tooling, no provider assessment, no acquisition, no D1/D2
access, no hypothesis generation. The probe script touches no project data,
no Deriv endpoint and no credentials.

**The question this answers, and it is falsifiable:**

> On this machine, under the intended execution configuration, can P1 be made
> **unable** to write to durable storage while P2 **retains** the ability —
> and can P1 still do its own job?

A negative result is a real outcome. It returns Route 4 to the two-process
baseline with its full dynamic-audit burden, and that is far cheaper to learn
now than at implementation.

---

## 1. THREE LEGS, NOT TWO

The CEO's framing names two: P1 denied, P2 retained. **A third is needed or a
passing result is worthless.**

| Leg | Must establish | Why |
|---|---|---|
| **L1** | P1 is **denied** durable write | The structural claim |
| **L2** | P2 **retains** durable write | Otherwise nothing can be persisted |
| **L3** | **P1 can still fetch** | A boundary that breaks the transport is not a solution — it is a broken acquisition path wearing a safety argument |

L3 is the one most easily forgotten. A restricted token that denies writes may
also deny the certificate store, the proxy configuration or the network stack,
in which case P1 cannot perform the only job it exists to do. The probe tests
it explicitly.

---

## 2. THE PASS CRITERION, AND WHY IT IS DEMANDING

**[R] L1 passes only if P1 is denied at *every* probed location, temp
included.**

This is stricter than it may look, and the reason matters. §7.8's prohibition
is on **rejected data reaching durable storage at all** — not on it reaching
`docs\`. A rejected payload written to `%TEMP%` is bytes on disk. If P1 can
write to temp, the capability boundary is **not** achieved, and the three-
process design's advantage over the baseline evaporates.

The alternative — declaring temp a controlled quarantine with its own purge
and audit — reintroduces exactly the problem the architecture exists to
remove, so it is not a way around the criterion.

**[A] This criterion may well be what fails.** Several isolation mechanisms
deny writes to the user profile while leaving `C:\Windows\Temp` writable
through a group ACE. That would be a partial boundary, and a partial boundary
is not one.

---

## 3. LOCATIONS AND VECTORS

**Locations probed:** repo root, `docs\`, `engine\output\`, user `%TEMP%`,
`%LOCALAPPDATA%`, profile root, `C:\Windows\Temp`, `C:\`.

**[R] Five write vectors per location**, because a mechanism that blocks one
API is not a capability boundary: `Set-Content`,
`[System.IO.File]::WriteAllText`, `New-Item -ItemType File`, `Out-File`, and
directory creation. A result is only "denied" when all five are.

**[R] Read is probed separately from write.** "Denied write" and "cannot see
the directory at all" are different findings with different consequences — the
second would also prevent P1 reading its own configuration, which is an L3
failure in disguise.

**Safety, given incident I1:** the probe creates only uniquely named
`_apexprobe_<hex>.*` files and removes each **by explicit path**. No wildcard
delete appears anywhere in it. A leftover check runs at the end and reports
anything that survived.

---

## 4. THE MECHANISM LADDER — CHEAPEST FALSIFICATION FIRST

| # | Mechanism | Admin? | Credentials? | Why in this order |
|---|---|---|---|---|
| **T1** | **Restricted token** via `runas /trustlevel:0x20000` | no | **no** | Built in, no account to create, no password to handle. If it works, the whole question is settled cheaply |
| **T2** | Low integrity level | varies | no | OS-enforced regardless of ACLs; needs a launcher |
| **T3** | Separate local account | **yes** | **yes** | Most reliable distinct SID; introduces an account and credential handling |
| — | Job object | — | — | **Excluded.** Not a filesystem access-control boundary; does not address the shared-SID problem |

**T1 first** also respects the project's credential discipline: it needs no
password, so nothing is typed or stored.

### Running T1

The restricted window closes on exit and may be unable to write a log, so keep
it open and read from it:

```
runas /trustlevel:0x20000 "cmd /k powershell -NoProfile -ExecutionPolicy Bypass -File C:\Windows\Temp\apex_g0a_write_probe.ps1 -Label RESTRICTED"
```

The script is placed in `C:\Windows\Temp` for this run because a restricted
token may be unable to **read** the profile — if the script sat in the repo,
the test would fail for the wrong reason.

### Running the baseline

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apex_g0a_write_probe.ps1 -Label NORMAL
```

**Both runs are required.** The normal run is L2 and the control: without it,
a denied result proves nothing, because the location might be unwritable for
everyone.

---

## 5. HOW TO READ THE RESULT

| Outcome | Reading |
|---|---|
| RESTRICTED denied **everywhere**, NORMAL writes everywhere, HTTPS **OK** under both | **L1, L2, L3 pass.** T1 is sufficient; three-process design is feasible at low cost |
| RESTRICTED denied in repo/profile but **writes `C:\Windows\Temp`** | **Partial boundary — L1 fails** (§2). Try T2/T3 before concluding |
| RESTRICTED denied everywhere but **HTTPS fails** | **L3 fails.** Not a solution; P1 could not fetch. Investigate what the token removed before discarding |
| RESTRICTED **cannot read** the repo | Expected under a strong restriction; not itself a failure, but P1's config and credential access must then be re-planned |
| RESTRICTED writes everywhere | T1 insufficient; go to T3 |

**[R] A single directory passing is not proof of a boundary.** The criterion
is the whole location set.

---

## 6. BOUNDING THE SEARCH — AS THE CEO REQUIRED

**[R] PROPOSED bound: test T1, then T3. If both fail, stop and adopt the
two-process baseline.**

T2 and AppContainer are not pursued unless T1 or T3 returns a result that
suggests a narrow, specific fix. The reason for the bound is that each further
mechanism costs more to implement, more to verify, and more to maintain, while
the baseline is already a working design — merely one with a heavier audit
burden that is documented and accepted.

**[A] A negative result for the tested configurations is not proof that no
isolation mechanism exists.** It is a decision to stop searching at a bounded
cost, recorded as such rather than as an impossibility claim.

---

## 7. WHAT A PASS WOULD *NOT* ESTABLISH

Listed so a positive result is not over-read, per **P1**.

- **It would not remove the dynamic write-set audit.** Register v3 §4.3 and
  the core-dump residual (14.12) survive. Crash dumps, paging and
  child-process writes are OS-mediated and are not writes P1 makes, so a
  permission boundary on P1 may not cover them.
- **It would not establish that buffering keeps bytes off disk** — paging and
  OS diagnostics are separate concerns, as the CEO noted on A1.3.
- **It would not approve amendment A1.** That still requires the standing
  two-way sweep and a fresh review of the affected clauses.
- **It would not establish IPC behaviour.** Whether channel B1.2 can spill to
  disk via named-pipe buffering or memory mapping is evaluation item 2 and is
  untested by this probe.
- **It would say nothing about P2's correctness**, only about its capability.

---

## 8. SEQUENCE

1. Standing checks.
2. Copy the probe to `C:\Windows\Temp\` and run the **NORMAL** baseline from
   the repo root.
3. Run the **RESTRICTED** T1 case.
4. Compare against §5. Record both outputs verbatim.
5. If T1 fails on §2's criterion, decide whether T3 is worth its cost before
   running it — that is a decision, not an automatic next step.
6. Record the result, positive or negative, as a G0a finding.

**Nothing is authorised by this document.**
