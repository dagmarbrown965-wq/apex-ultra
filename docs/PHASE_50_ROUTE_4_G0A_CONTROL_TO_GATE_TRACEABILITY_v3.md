# PHASE 50 — ROUTE 4 — G0a CONTROL-TO-GATE TRACEABILITY REGISTER, v3

## G0a ARTIFACT — findings only, not an agreement revision

Revised 2026-11-24 under the CEO's four further points. Supersedes v2.
**Agreement v8 is untouched and remains approved at G0.**

Authorises nothing. No candidate assessed, no tooling designed or authorised,
no acquisition, no D1/D2 access. **No first X acquisition until C1, C2, C5 and
C6 have passed implementation verification** — G9 is an operational deployment
gate, not the first occasion those controls are exercised.

### What changed in v3

| # | Change |
|---|---|
| 1 | **§4.1 — F5a's oracle.** Its expected count is now a literal declared when the fixture is authored, never computed at run time, so the test cannot reproduce the implementation's own truncation error in its reference. |
| 2 | **§4.2 — F8's criterion is baseline-relative.** "No artifact exists" could pass or fail for the wrong reason. Replaced with *creates, modifies or leaves behind no prohibited durable artifact*, measured against a pre-run snapshot — **plus** write-set evidence, because a partial write followed by cleanup leaves no filesystem trace yet still put rejected data on disk. |
| 3 | **§4.3 — shared mechanism, unshared scope.** C9's audit observes the *inspector*; F8 concerns the *acquisition and validation pipeline*. One mechanism may serve both, but coverage is per process and per write path and must be evidenced separately. **This produces an ordering requirement: the process set must be enumerated before the mechanism is chosen** (§5.7). |
| 4 | **Two corrections** — C1's provider row now reads *disconfirmation only*; §5.6's dangling reference to a non-existent "§0" is corrected to §1.2. |

Carried from v2 and accepted: the decomposed invariant (§1.2), the **AC**
category and its sub-distinction (§2), the narrowed C9 wording (§3), the
ten-fixture suite (§4), G5a (§5.2), G7 probes i–v (§5.3), the five-field
register and the standing sweep (§5.5, §5.6).

---

## 1. THE ROOT CAUSE, AND WHAT THE INVARIANT ACTUALLY RESTS ON

**1.1 Active is not tested.** Gate G9 reads *"First X acquisition … with C5,
C6, C9 active"*. That is **deployment**, not verification, but it occupies the
position where a test would sit, so C5 and C6 scan as mapped while nothing
tests them. Same class as the G6/C9 omission corrected in v8, better hidden,
because the control's name does appear in a gate row.

**1.2 What §10.5's invariant depends on — corrected.** Not C6 alone:

| Component | Role in the invariant |
|---|---|
| **C6** | The **runtime payload-validation and rejection mechanism**. Checks every returned timestamp against the permitted bound and rejects the response whole. Its implementation is **unverified** and must be tested before acquisition. |
| **C2** | The **boundary margin** against the displacement and labelling risks inside its model — including the labelling error that C6 cannot see, because C6 checks timestamps *as returned*. |
| **§4's threat model** | The enumeration both of the above are sized against. |
| **C9** | Containment of what a breach exposes, after the fact. |

So the invariant depends on the **combined boundary design and its stated
assumptions**. This makes the C6 orphan finding more precise rather than
weaker: **C6 is the critical unverified runtime enforcement component**, and
the invariant has several dependencies of which it is one.

**1.3 Proposed remedy.** §12's gate table gains a **tests / operates /
decides** column. A control named only under *operates* is untested by
construction.

---

## 2. CATEGORIES

v1 used four. A fifth is needed, because v1 forced two different things into
one box.

| Code | Meaning | Established by |
|---|---|---|
| **IV** | Implementation verification | A gate, against fixtures through the production path |
| **OT** | Operational testing | A probe against a real provider; one-way only |
| **AC** | **Analytical claim** | **Review of a derivation against its stated assumptions** |
| **EA** | External assumption | **Nothing.** Declared, never established |
| **RL** | Residual limitation | Declared; no procedure removes it |

**Why AC is not EA.** Whether a provider will comply is genuinely external —
no procedure available to this project establishes it. Whether `38h + 2P`
follows from §4.1's components is a model claim with a derivation, and that
derivation can be reviewed. A gate cannot prove it; analytical review can
establish whether it follows from the stated premises. Collapsing the two
understated what is checkable.

**[A] One honest sub-distinction inside AC.** The envelope has a derivation
available. **§4's completeness does not** — no derivation establishes that a
threat enumeration is exhaustive. Both are AC, but only the first is reviewable
to a conclusion; the second stays a declared premise however long it survives.

---

## 3. CONTROL → GATE, EVERY COMPONENT

| Control | Component | Cat. | Gate | Status |
|---|---|---|---|---|
| **C1** | Emitted request carries explicit G, start and end | IV | **G5a** proposed | **ORPHAN** |
| **C1** | Provider honours the declared G | EA | C3 — **disconfirmation only** | assumption; C3 can **refute** it, never establish it |
| **C2** | First request's end bound = `boundary − M` | IV | **G5a** proposed | **ORPHAN** |
| **C2** | `38h + 2P` follows from §4.1 | **AC** | analytical review | **not a gate item** — see §2 |
| **C3** | Granularity fidelity (probe iv) | OT | **G7** | mapped |
| **C4** | Substitution (probes ii, iii) | OT | **G7** | mapped |
| **probe v** | Error specificity, where E2 asserted | OT | **G7**, after §5.3 | **ORPHAN** — G7 reads "i–iv" |
| **C5** | Spacing-check implementation | IV | **G5a** proposed | **ORPHAN** |
| **C5** | Blind to substitution | RL | — | declared in §5 |
| **C6** | The seven §6.4 requirements | IV | **G5a** proposed | **ORPHAN — critical** |
| **C6** | Labelling errors pass C6 | RL | — | declared; margin carried by C2 |
| **C7** | Fixtures 1 and 2, production path | IV | **G6** | mapped |
| **C8** | Freshness re-probe | OT | **G8** | mapped |
| **C9** | Static tests (i), (ii), (iv) | IV | **G6** | mapped (v8) |
| **C9** | Dynamic write-set audit (iii) | IV | **G6** | mapped (v8) |
| **§4** | Threat-model completeness | **AC** | — | declared premise; no derivation available |

**[R] C9 wording, narrowed as ruled.** C9's **acceptance procedure is
incorporated into G6**. That does **not** mean runtime controls named in later
operational gates have had their implementations verified — which is precisely
why naming C9 in G6 closed its gap, while C5's and C6's gaps need a separate
fixture gate.

---

## 4. THE C6 FIXTURE SUITE — MAPPED, AND v1'S SET WAS INCOMPLETE

The CEO's requirement: map fixtures to all seven §6.4 requirements, so a suite
is not declared complete merely because it contains several adversarial
examples. Applying it to v1's six scenarios shows they covered **four of
seven**.

| §6.4 req. | Requirement | v1 coverage | Fixture |
|---|---|---|---|
| **1** | Predicate over **every** element | **MISSING** | **F1** — out-of-bounds entry positioned **mid-payload**, neither first nor last. The core universality test, and v1 had no fixture that forced it |
| **2** | No reliance on ordering | covered | **F2** — compliant payload delivered unordered |
| **3** | Check **before** transform | **MISSING** | **F3** — out-of-bounds entry positioned so a sort-and-trim or dedup step would remove it; the check must still reject. v1's "duplicate entry" scenario did not test this |
| **4** | Malformed entries fail, never skipped | covered | **F4** — unparseable epoch |
| **5** | Independent count reconciliation | partial | **F5a** — payload where a truncated iteration would still reconcile against a loop-accumulated count. **Expected count is a literal declared in the fixture** — see §4.1 |
| **5** | **Exactly one** timestamp per entry | **MISSING** | **F5b** — an entry yielding **zero** extractable timestamps; **F5c** — an entry yielding **two** |
| **6** | Empty return is not a pass | covered | **F6** — empty payload; must report "no data", never "boundary respected" |
| **7** | Off-grid entries halt | covered | **F7** — `t % G != 0`; must halt pending §14.13 re-derivation |
| — | **Rejection must not reach durable artifacts** | **MISSING** | **F8** — after any rejection above, assert the rejected response **creates, modifies or leaves behind no prohibited durable artifact**, measured against a pre-run baseline — see §4.2. A correct verdict with a downstream path that writes anyway is the live hazard |

**Ten fixtures, not six.** F1, F3, F5b, F5c and F8 are new. The three
requirements v1 under-covered — universality, check-before-transform, and the
one-timestamp-per-entry clause — are the three where a plausible-looking
implementation most easily passes a weak suite.

**[R] F8 matters more than the others.** Proving the validator returns a
failure verdict is insufficient; the evidence must be that **rejected data
cannot reach durable artifact creation.**

### 4.1 [R] F5a's oracle must be independent of the iteration under test

§6.4 requirement 5 already forbids a count accumulated by the checking loop,
and F5a tests that. But the **fixture's** expected count must also be
independent, or the test can reproduce the same truncation error in both the
implementation **and** its supposed reference, and agree with itself. **The
expected count is therefore a literal declared when the fixture is authored**,
never computed at run time by code sharing a path with the implementation.

### 4.2 [R] F8's criterion is baseline-relative, not existential

*"No summary and no dataset exists"* can pass or fail for the wrong reason — a
prior test's artifact already present, or a leftover from an earlier run. The
criterion is that the rejected response **creates, modifies or leaves behind
no prohibited durable artifact**, established by:

1. a **snapshot** of the durable artifact locations before the fixture runs;
2. after the run: **no new path, no modified path** (content hash and mtime),
   and **no partial or temporary file left behind**;
3. **and** write-set observation showing no write to a durable path at all —
   because a **partial write followed by cleanup** leaves no filesystem trace
   yet still put rejected data on disk. Only (3) catches that case, which is
   why F8 requires **both** the artifact comparison and the write-set
   evidence.

### 4.3 [R] F8 and C9's audit may share a mechanism; sharing a *scope* is not established

C9's audit (iii) observes the **inspector** process. F8 concerns the
**acquisition and validation pipeline** and whatever performs persistence. One
mechanism may well serve both, but **coverage is per process and per write
path**, so it must be evidenced for each scope separately. **A passing C9
audit can coexist with an F8 blind spot** — and because F8 establishes a
downstream safety property rather than another validation result, that blind
spot would be invisible in the artifacts.

**[R] The ordering requirement this produces, which lands *before* the
mechanism choice.** The architecture must first **enumerate every process in
the acquisition path**: §7.6's isolation default already implies at least two,
and persistence may add a third. A mechanism cannot be assessed for adequate
coverage until the set of things it must cover is fixed. Choosing the
mechanism and discovering the process set afterwards would repeat exactly the
error that §8.6 exists to prevent — deciding fixture-injectability only after
a path had been selected.

---

## 5. PROPOSED G0a ITEMS

As accepted, with the qualifications applied.

**5.1 [Accepted]** Add the **tests / operates / decides** column to §12.

**5.2 [Accepted in principle]** Add gate **G5a** between implementation (G5)
and the existing test gates. All fixtures run **through the production path**
under §8.6's fixture-injectability criterion — no simplified substitute, per
§6.5. Acceptance evidence, per control:

| Control | Acceptance evidence |
|---|---|
| **C1** | The **actual outbound request** contains explicit granularity, start and end — inspected on the emitted request, not on the configuration handed to the request builder |
| **C2** | The **production calculation** yields exactly `1785984300` for `boundary = 1787193900`, `M = 14 days` (2026-08-06 02:45:00 UTC, a clean multiple of 900) |
| **C5** | Fixtures demonstrate correct spacing **acceptance and rejection** |
| **C6** | F1–F8 of §4, mapped to all seven requirements, with **F5a's declared oracle** (§4.1) and **F8's baseline-relative criterion plus write-set evidence** (§4.2) |

**5.3 [Accepted]** G7 becomes **probes i–v**, probe v retaining its
conditional status — required only where E2 is asserted under §8.5 case 3.

**5.4 [Accepted, reworded]** Record that **C9's acceptance procedure is
incorporated into G6**, and that this does not imply verification of runtime
controls named in later operational gates.

**5.5 [Accepted]** Five-field register form — *control / component / gate
mapping / acceptance evidence / limitations* — carrying §2's category column
including **AC**. Two-way rule: every component has a gate **or** an
explicitly justified exception, and every gate has a defined control
requirement **and** acceptance criterion.

**5.6 [Accepted]** Standing two-way sweep after **every** change to a
classification, a control, a gate or an approval criterion. Sweep
descriptions, requirements, gate definitions and approval criteria — not only
the paragraph where an inconsistency surfaced. Every defect found in the last
two rounds — including the contradiction corrected at **§1.2** of this
register — was found by sweeping rather than by reading.

---

**5.7 [New, from §4.3]** **Before** the §14.14 mechanism decision, G0a
**enumerates every process in the acquisition path**, then requires the chosen
mechanism's coverage to be evidenced **per process and per write path** — for
C9's audit scope and F8's scope **separately**, not inferred from one to the
other.

---

## 6. WHAT THIS DOES NOT CHANGE

- **G0 remains approved.** Nothing here reopens v8's §§5–10, the E2
  dispositions, the fixture requirements, C6's seven requirements, or
  §14.13's resumption principle.
- **No control becomes stronger by being mapped.** An external assumption
  assigned a gate is still an assumption; §3's EA and AC rows keep that
  visible.
- **The sequencing rule, as ruled:** no first X acquisition until C1, C2, C5
  and C6 have passed G5a.
- **The substantive G0a question is unchanged** — whether §7.6's isolation and
  §14.14's audit mechanism can be implemented and tested on the target Windows
  environment, not which provider to choose. §4's F8 now depends on the same
  mechanism decision.
- **Nothing is authorised.**
