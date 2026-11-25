# PHASE 50 — ROUTE 4 — STAGED ACQUISITION: THE SAFETY ARGUMENT, v5

## WORKING NOTE — NOT CLOSED, NOT AUTHORISED

Revised 2026-11-22 under the CEO's four rulings. Supersedes v4. **Acquisition
agreement DRAFT v1 remains untouched**; everything here reaches it only as the
consolidated amendments in §12.

Authorises nothing. No provider selection, no connector assessment, no
replacement tooling, no acquisition, no D1/D2 access, no hypothesis
generation. Route 4 approved in principle; acquisition path unapproved.

**New in v5.** The four rulings are written in. Three consequences follow that
were not visible before them: the displacement model and the containment model
are **two different models** and v4 ran them together (§2); "architecturally
incapable" is a claim of the same kind as this project's execution-impossibility
guarantee and therefore needs a **verifying gate**, not an assertion (§7.6,
control **C9**); and the exposure record's own field list opens a retention
route that the ruling it serves prohibits (§7.8).

---

## 1. GOVERNING PRINCIPLES

> **P1 — A detection mechanism must never be presented as a prevention
> mechanism.** Request-side enforcement, provider compliance, response
> inspection and artifact integrity are separate controls with separate
> failure modes.

> **P2 — The self-testability standard.** The admissibility test includes
> whether we can independently test our own controls. That is a stronger
> standard than asking whether a provider offers historical data over a
> specified interval. **It is retained even if it reduces the number of
> possible providers to zero.**

P2 is recorded as a principle rather than a preference because it is the
clause most exposed to deadline pressure, and §10.2 makes the pressure
foreseeable.

### Control register

| # | Control | Type | Addresses | Does **not** do | Failure mode |
|---|---|---|---|---|---|
| **C1** | Request-side granularity declaration **G** | **Prevention**, *conditional* | Bounds `P ≤ G` a priori | Does not prevent coarser data arriving | Silent, if the provider ignores G |
| **C2** | Margin **M = 14 days** | **Prevention** | Displacement Category 3.1 **only** | Does not address substitution, non-compliance, or any unbounded class | A component unbounded or unenumerated |
| **C3** | Granularity-fidelity probe | Detection, one-way | Provider non-compliance, tested conditions | Does not establish compliance for X, other endpoints, or later | Instrument/endpoint/tier/time specificity |
| **C4** | Substitution probes | Detection, one-way | Category 3.3, tested conditions | As C3 | As C3 |
| **C5** | Response-side spacing check | **Detection only** | A cap violation already arrived | Cannot prevent arrival; costs restricted-tier exposure | **Blind to substitution** |
| **C6** | Payload-derived coverage check | **Detection only** | Category 3.3 at acquisition time | Cannot prevent arrival; does **not** establish C7 | Blind if the artifact is built from the echo |
| **C7** | Artifact-integrity fixtures | Detection, one-way | Category 3.4b, the evidence mechanism | Does not establish provider truthfulness or immunity to future change | Production path not genuinely exercised |
| **C8** | Freshness re-probe | Detection, one-way, time-bounded | Provider drift between test and acquisition | Establishes recency only | Change after the re-probe |
| **C9** | **Static gate on the inspector's interface** (§7.6) | **Prevention**, *unconditional* | **Containment**: deferred metadata reaching analytical use | Does not prevent deferred data arriving, nor detect a breach | Gate not run, or scoped too narrowly |

**1.1 What the register now shows.** Nine controls; **three preventive**, of
which **two are unconditional** (C2, C9) and one conditional (C1). C9 is
preventive for a *different hazard* than C1 and C2 — see §2 — and the register
must not be read as C9 improving boundary protection. It does not. It protects
containment, and containment was previously carried by a policy statement.

**1.2** Residual risk is still not zero. It is a **bounded and disclosed
position**, conditional on the threat model being sufficiently complete and
the stated assumptions being defensible.

---

## 2. TWO MODELS, SEPARATED

v4 ran these together and the governing principle P1 forbids exactly that kind
of merge.

| Model | Question | Covered by |
|---|---|---|
| **Displacement model** (§3) | *How does deferred-region data come to cross into a response?* | C1–C4, C6–C8 |
| **Containment model** (§7.2) | *What may happen to deferred-region data that has already crossed?* | The three tiers, C5's narrow permission, **C9** |

They have different hazards, different failure modes and different controls. A
perfect displacement model with no containment leaks through analysis; perfect
containment with a broken displacement model simply receives more to contain.
Neither substitutes for the other, and the agreement should carry them as
separate sections.

---

## 3–6, 9. SETTLED MATERIAL, CARRIED FORWARD

**§3 Displacement threat model** — provisional, not exhaustive. 3.1 bounded
displacement; 3.2 granularity; 3.3 substitution; **3.4a coverage calculation**
and **3.4b artifact integrity** (C6 passing does **not** establish C7); 3.5
provider-specific behaviour. v4 and v5 added no category — weak evidence of
convergence, **not** proof of completeness.

**§4 Compound bound.** Worst-case **directional** envelope `38h + 2P` — added
because effects may align and are positively coupled, not because they are
independent (which would argue root-sum-square and a *smaller* figure). A
coherent joint scenario reaches `≈36h + 2P`, within two hours of the envelope.
Daily cap → `86 h = 3.58 d`, factor **3.91** at M = 14 d. Weekly → 15.58 d,
fails; monthly → 61.58 d, fails. **M is conditional on C1 and must never be
described as protecting against non-compliance.** Residual with weekly bars
under M = 14 d: a **1.58-day** crossing window. The cap is **structural** —
margin alone needs M ≈ 61 d for weekly and is defeated by monthly.

**§5 C1.** Request declares **G ≤ daily**, supplying `P ≤ G`. Compliance is an
assumption, probed by C3. A mechanism without an explicit granularity
parameter cannot supply C1 and is inadmissible.

**§6 C3/C4.** Sacrificial instrument **S**, designated and sealed by commit
before any probe, permanently ineligible as X, assessed on specification pages
only. Four probes on the **actual** mechanism, endpoint and request form:
in-range baseline; out-of-range future; out-of-range past; granularity
fidelity. Substitution **or** non-compliance → **path disqualified**. Clean
failure → recorded, **no validation**. Disqualification scopes to provider +
endpoint + request form.

**§9 C8 freshness.** Probes re-run immediately before the first X acquisition,
same session, both artifact sets committed, using the **same** endpoint,
request structure, granularity declaration and account/access conditions. Any
**material provider-side change** invalidates and requires reassessment.
Establishes **recency**, never reliability.

---

## 7. CONTAINMENT: C5, THE TIERS, C9 AND THE RECORD

**7.1 Ruling.** C5 is **retained**, subject to a strict metadata-only
exception. Dropping it would leave the request-side declaration dependent on
provider behaviour with no check that returned spacing is consistent with it.

**7.2 The three tiers.**

| Tier | Content | Treatment |
|---|---|---|
| **Price/data** | Deferred OHLC, volume, indicators, charts, derived market information | **Prohibited** |
| **Restricted metadata** | Timestamps and spacing information, solely for boundary-integrity and granularity checks | **Conditionally permitted** |
| **Analytical** | Any use of deferred information for instrument selection, hypothesis generation, comparison or refinement | **Prohibited** |

**7.3 Conditions on the restricted tier.** Minimum timestamp information only;
no deferred prices or price-derived fields displayed, retained for analysis or
passed to hypothesis-generation processes; the check automated and narrowly
scoped; immediate abort on a detected breach, not investigation; the exposure
recorded explicitly and **never** described as zero exposure or as
preservation of an entirely untouched dataset.

**7.4 Automation is load-bearing but not sufficient — as ruled.** Automation
is what separates the restricted tier from the analytical one in practice: a
program that computes modal spacing, compares it to G and discards cannot form
a hypothesis from what it read, where a person reading the same timestamps
can. But instructing a process is no stronger than instructing a person unless
the process is *constrained in what it can retain and emit*.

**7.5 Interface constraints, as ruled.** The inspector must provide:
automated timestamp and spacing inspection; **no interactive display** of
deferred timestamps; **no per-bar output** available to hypothesis-generation
processes; **only narrowly defined results** — pass/fail and a boundary-breach
indication; **immediate abort** on a detected breach.

The operative standard, in your words: the process must be **architecturally
incapable** of exposing the underlying observations for analytical use through
its permitted interface. Not forbidden from it — incapable of it.

**7.6 PROPOSED — C9, because "architecturally incapable" is a claim of a kind
this project already knows how to verify.** The project makes exactly one
other incapability claim: execution is impossible. That claim does not rest on
intent — it rests on **verified code guards** and a **static import gate**
(`check_cp3_imports`: no execution-capable imports, no `adapters.*` or
`testing.*` imports anywhere under `engine/`), re-run as a standing check
every session. The precedent is unambiguous: an incapability claim in this
project carries a gate that fails loudly when the claim stops being true.

Proposed by analogy:

1. The inspector returns a **closed result type** carrying only the §7.5
   fields — verdict, breach indication, and the §7.8 scalars. No sequence, no
   per-bar structure, no timestamp field.
2. A **static gate** verifies (a) that the inspector's public interface
   exposes no per-bar or timestamp-valued member, and (b) that no module on
   the hypothesis-generation path imports the inspector or its raw-response
   type.
3. The gate runs as a standing check, alongside M0 and CP3.

Without C9, "architecturally incapable" is an assertion, and P1's whole
discipline is that assertions are classified by type rather than accepted by
tone. With it, containment has its first unconditional preventive control.

**7.7 C5 remains a detector.** It cannot undo the fact that a response
containing deferred data has arrived. **The primary protection remains
request-side enforcement.** C9 does not change this: C9 contains what arrived;
it does not reduce what arrives.

**7.8 The exposure record — and the gap its own field list opens.** Your field
list is adopted. But two of its fields are routes to exactly what the ruling
prohibits, and the ruling says so itself: *the record must not become a route
for retaining or analysing deferred market information.*

- **"Scope of metadata inspected"** — if this resolves to first and last
  timestamps, deferred-region timestamps are written into a durable, committed
  document that a person then reads. That is retention, and it crosses into
  the analytical tier at the moment someone reads the file.
- **"Boundary-breach classification"** — if it carries the breach's extent as
  a calendar position, it describes coverage of the deferred window.

PROPOSED resolution — **magnitude, never content**:

| Permitted in the record | Prohibited in the record |
|---|---|
| Control identifier; run identifier | Any raw deferred-region timestamp |
| Wall-clock time of the inspection (**not** market time) | Any value indexed by calendar position inside the deferred region |
| Count of timestamps inspected | Any price or price-derived field |
| Inferred spacing (a grid property, not a market property) | Any per-bar sequence or distribution |
| Verdict; abort flag | Anything from which the deferred window's coverage could be reconstructed |
| Breach magnitude as **seconds and bar-count relative to the requested bound** | The breach's absolute position in calendar time |
| Breach classification by **type** | Breach classification by **date** |
| Explicit confirmation that no deferred price fields were exposed | — |

The reasoning for the permitted column: each entry is a property of the
*request-response relationship* or of the *grid*, not of the market. "Crossed
the requested bound by 3 bars" cannot seed a hypothesis about X. "Crossed into
2026-11-04 through 2026-11-07" begins to describe the deferred window, and is
prohibited for that reason even though it looks like the same fact.

**7.9 Escape clause, retained.** If the project later decides that even
timestamp-only deferred metadata is impermissible, C5 must be **removed** and
the path must meet the stronger provider-side enforcement and
independent-evidence standard. **That change requires a fresh agreement
decision** — not available by interpretation.

---

## 8. C7 AND FIXTURE-INJECTABILITY

**8.1 The admissibility criterion, as ruled, verbatim.**

> An acquisition path is admissible only if its proposed tooling architecture
> supports adversarial fixture injection through the same production
> processing and artifact-generation path used for real acquisition, without
> requiring a separate simplified implementation to establish C7.

This does **not** require the provider to supply fixture support. It requires
the proposed **acquisition architecture** to make the evidence test possible.
**G1 must not begin until this criterion is accepted and incorporated into the
selection rule.**

**8.2 Fixture 1 — payload against echo.** Request specifies interval **A**;
echoed response metadata reports **A**; the returned payload actually
represents **B**; the fixture runs through the production path; coverage
recomputed independently from the returned timestamps is compared against the
generated artifact. Establishes that the artifact derives coverage from the
**returned data**.

**8.3 Fixture 2 — request against echo.** Request and echoed metadata
deliberately disagree with each other, establishing which source the generator
actually trusts. Fixture 1 alone cannot distinguish a generator reading the
request from one reading the echo, because there the two agree.

**8.4 Scope of a pass.** Establishes that C7 is **correctly implemented**.
Does **not** establish that a real provider produces every failure mode; that
the provider's raw response is truthful; or that the artifact is immune to
future implementation changes. A mismatch **disqualifies the path**.

**8.5 No simplified substitute.** If the production path cannot accept a
fixture without changing production behaviour, **that limitation is
documented** and a simplified test implementation is **not** substituted and
claimed as the production path passing.

---

## 10. THE GATE SEQUENCE AND 4 DECEMBER

**10.1 Sequence, as ruled.** Plan-locking and approval are separated.

| Gate | Work | Depends on |
|---|---|---|
| **G0** | Rule on v5; agreement v2 | this note |
| **G0a** | Establish the acquisition **architecture requirements**, incl. §8.1 and C9 | G0 |
| **G1** | Identify a candidate path; assess against §4 admissibility incl. §8.1, under restricted-tier discipline | G0a |
| **G2** | Design the replacement tooling **with the fixture seam and the closed result type** | G1 |
| **G3** | Produce and review a **locked implementation plan** | G2 |
| **G4** | **Explicit approval to implement** — a separate gate | G3 |
| **G5** | Implement the tooling | G4 |
| **G6** | Test its controls: C7 fixtures, C9 static gate | G5 |
| **G7** | Designate S by commit; run C3/C4 probes | G1, G5 |
| **G8** | C8 freshness re-probe | G6, G7 |
| **G9** | First X acquisition: window ending `1787193900 − M`, G declared, C5/C6/C9 active | G8 |
| **G10** | Establish X's convention; re-derive the boundary | G9 |

No implementation begins because the architecture has been discussed or
because a provider appears promising. The seam is designed in, never
retrofitted once implementation has become difficult to test.

**10.2 The 4 December clause, as ruled.**

> **4 December determines whether Route 4 proceeds. It does not certify that
> Route 4 works.**

The legitimate decision on that date: is Route 4 worth proceeding through the
remaining gates; is its potential research value sufficient to justify the
tooling and validation work; or should Route 4 be closed as impractical under
the existing constraints. It is **not** legitimate to read the deadline as
requiring a functioning provider, completed tooling, or acquired X data.
Acquisition before 4 December is highly unlikely, and that is **not a reason
to compress the gates**.

---

## 11. STILL OPEN

**11.1** C9 (§7.6) is PROPOSED and unruled. It is an architecture requirement,
so it belongs at **G0a** and must be settled before G1 like §8.1.

**11.2** The record's permitted/prohibited split (§7.8) is PROPOSED and
unruled.

**11.3** The displacement threat model is provisional. No category added at v4
or v5 — weak evidence of convergence only.

**11.4** No candidate path identified. It remains live that none is found
before 4 December, and under **P2** that outcome is accepted rather than
worked around.

**11.5** Nothing here shows X can be acquired within the boundary. The
register constrains how a path may be **tested**; it does not show any path
**passes**.

---

## 12. CONSOLIDATED AMENDMENTS TO AGREEMENT v1

Supersedes v4's §12. v1 stands as delivered until ruled on.

| # | Target | Change |
|---|---|---|
| 12.1 | preamble | **P1** and **P2** (§1), and the control register, so detection and prevention cannot be recombined in later revisions. |
| 12.2 | new section | The **two models** (§2) as separate sections — displacement and containment. |
| 12.3 | §4.4 | Evidential wording; coverage from the accepted payload, never the echo; 3.4a / 3.4b as separate requirements. |
| 12.4 | §4.7 | C1, C2 sized against §4 and §2, C2 **conditional on C1**, cross-references to §6 and §8. |
| 12.5 | §4.6 | Discovery procedure — §6 and §8. |
| 12.6 | new §4.8 | C5 as ruled: detection only, blind to substitution. |
| 12.7 | new §4.9 | C3/C4 tripwire in full, probe iv, one-way disclosure. |
| 12.8 | new §4.10 | C7 in full: fixtures 1 and 2 through the production path, §8.4 scope limits, §8.5 no-substitute rule. |
| 12.9 | §4.3 | Three tiers (§7.2), five conditions (§7.3), interface constraints (§7.5), record format (§7.8), escape clause (§7.9). |
| 12.10 | new §4.11 | C8 freshness with both conditions. |
| 12.11 | new §4.12 | **Fixture-injectability** admissibility criterion, §8.1 verbatim. |
| 12.12 | **new §4.13** | **C9** static gate on the inspector's interface (§7.6), as a standing check beside M0 and CP3. |
| 12.13 | §8 (deadline) | §10.2 verbatim: 4 December determines whether Route 4 proceeds; it does not certify that Route 4 works. |
| 12.14 | new section | The **gate sequence** (§10.1), with G4 as a separate approval gate. |
| 12.15 | §9 | Carry §11.1–§11.5 into the agreement's open items. |

---

Nothing is authorised by this document. §11.1 and §11.2 require rulings, and
§11.1 belongs at **G0a** — before any candidate path is assessed.

**Note on form:** the amendment list has reached fifteen rows against a v1 that
predates every ruling in it. Once §11.1 and §11.2 are settled, agreement **v2**
is likely easier to review than v1-plus-amendments. Say the word and I will
fold them; I have not done so unasked.
