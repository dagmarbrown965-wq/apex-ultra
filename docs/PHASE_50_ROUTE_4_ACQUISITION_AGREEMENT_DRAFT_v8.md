# PHASE 50 — ROUTE 4 — ACQUISITION BOUNDARY AGREEMENT AND INSTRUMENT-SELECTION RULE

## DRAFT v8 — NOT AGREED, NOT AUTHORISED

Revised 2026-11-24 local and UTC (§0.1) under the CEO's G0 review of v7.
Supersedes v7. Safety-argument notes v1–v5 are retained as the reasoning
record.

**v8 is v7 with only the clauses listed below changed.** Every other clause is
byte-identical to the v7 text already reviewed, so a diff of v7 against v8
shows the complete set of changes and nothing else. The G0 review of v7
accepted §§5–10 and confirmed §16 step 1; v8 changes nothing that review
accepted on its merits, and reopens nothing settled.

### Maturity statement — read before the rest

v8 reconciles three places that still described C9 as wholly static or
preventive. **It does not advance the project by one step.**

- **No candidate acquisition path identified.** None assessed.
- **No replacement tooling designed, planned, approved or written.**
- **No probe run. No fixture built. No gate passed.**
- **The displacement threat model remains provisional.**
- **Containment still has zero technical controls** and rests on policy (§7.1).
- Nothing has been tested.

Route 4 is approved in principle. This agreement is **not approved**. Nothing
below authorises connector assessment, provider selection, tooling,
acquisition, D1/D2 access, or hypothesis generation. `tools/fetch_candles.py`
is frozen. Phase 49's result ("No admissible hypothesis found") is unchanged.

### Changes in v8

The G0 review of v7 raised **one** issue: §7.6's Classification paragraph
still called C9 a *preventive containment control*, contradicting the
composite classification established in §5, §5.1 and §7.6's own
component-typing clause. A sweep of all nineteen C9 references found **two
further instances of the same defect** in places the review did not reach.
All three are corrected; nothing else is touched.

| # | Clause | Change |
|---|---|---|
| 1 | §7.6 Classification | **As ruled.** C9 is now described as a **composite** information-exposure-boundary control, naming which components are preventive ((i), (ii), (iv)) and which is one-way detection ((iii)). The existing limitations are retained and now attach to **both** functions. |
| 2 | **§8.7** | *Found in the sweep.* Required C9 to be "**statically gated**", which asserts the same preventive-only reading the review rejected — test (iii) is dynamic. Corrected. |
| 3 | **§12, gate G6** | *Found in the sweep.* Listed "C9 **static gate**" as the thing G6 tests, which would have scoped the gate to three of its four tests and silently dropped the write-set audit from the sequence. Corrected. |

**Why the sweep mattered.** Items 2 and 3 are the same error as item 1, in
documents' usual hiding places: a requirement clause and a gate row. Item 3
was the more consequential — left as written, G6 would have tested a "static
gate" and the dynamic audit would have had no gate that called for it.

Unchanged and accepted at the v7 G0 review: §5 and §5.1's register and
counts, §6 in full incl. probe v and C6's seven requirements, §6.5's
fixtures, §7.6's isolation default, two-channel allowlist and type-based
safety argument, §8.1–§8.10 incl. the E2 dispositions, §9, §10, §14.13's
resumption principle, §14.14's scope/mechanism split, and §0.1's dating
convention.

---

## §0. STATUS TAGS

| Tag | Meaning |
|---|---|
| **[V]** | **Verified fact** — read from the repository or an authoritative `docs/` file. |
| **[R]** | **Accepted requirement** — ruled. Binding once the agreement is approved. |
| **[C]** | **Conditional control** — holds only under an assumption named in the clause. |
| **[A]** | **Declared unvalidated assumption** — disclosed, not established. |
| **[O]** | **Open** — unresolved. Nothing may depend on it. |
| **[G]** | **Gate not yet passed.** |

Standing rules: *conversation history is a lead for inspection, not evidence*;
*the filesystem is the source of truth over any document, including this one*.

### §0.1 [R] Dating convention — and a defect corrected

v5 was dated **2026-11-22** and dated its standing checks the same way, with
**no convention stated**, while the CEO's local date was **2026-11-21**. The
discrepancy was raised on review and is resolved, not papered over:

**[V]** The working container runs **UTC**. At the time of v5's revision it
was **2026-11-22 02:42 UTC**, which is **2026-11-21 21:42 Saturday** in
**America/Jamaica (UTC−05:00)**. Neither date was wrong; the document carried
no convention, so the two readings could not be reconciled from the text.

**[R] The convention, from v6 onward.**
1. **Epochs and data boundaries are UTC**, always, since D1 and D2 are epoch
   series (§2.1–§2.2). No local time appears in any boundary, interval or
   record.
2. **Document and event datelines carry their zone explicitly.** A bare date
   is not used. Where an event happened on the CEO's machine, the **local**
   date is given first and the UTC date second.
3. **§7.8's "wall-clock time of inspection" is UTC**, consistent with (1).
4. **Day-granularity deadlines are local to the CEO** unless stated
   otherwise, being commitments on his calendar rather than data boundaries.
   §13's **4 December 2026** is therefore local (America/Jamaica).

**[A] Why this is worth a clause rather than an edit.** §4.1 lists **timezone
interpretation** as a displacement hazard worth up to 14 hours, and §6.2 sizes
C2's margin partly against it. A document that sizes a margin against timezone
error while carrying an undated-convention dateline of its own was
demonstrating the hazard it describes. The defect is recorded here so the
convention is not quietly reintroduced.

---

## §1. GOVERNING PRINCIPLES

**P1 [R]** — **A detection mechanism must never be presented as a prevention
mechanism.** Request-side enforcement, provider compliance, response
inspection, artifact integrity and containment are separate controls with
separate failure modes. They are not combined into a single statement of
safety anywhere in this agreement, and a later revision that does so is in
breach of it.

**P2 [R]** — **The self-testability standard.** The admissibility test
includes whether we can independently test our own controls. A control that
cannot be independently tested is not an established control merely because
its implementation appears convincing. **Retained even if it reduces the
admissible provider set to zero.**

---

## §2. VERIFIED FACTS

**2.1 [V] D1.** Granularity 900 s; first epoch `1755657580`; last epoch
`1787193000`; span 364.993 days. `1787193000` a clean multiple of 900
(Amendment v0.11 line 46). Exclusion recorded as `epoch <= 1787193000` (v0.11
line 147; Phase 49 boundary agreement line 162).

**2.2 [V] D2.** Granularity 900 s; first epoch `1786039197` (2026-08-06
17:59:57 UTC); last epoch `1794857400` (2026-11-16 19:30:00 UTC); span 102.063
days. First epoch **897 s off the 900-second boundary** (D2 seal lines
100–101); last epoch a clean multiple of 900.

**2.3 [V] Overlap.** D2's first epoch precedes D1's last by 13.354 days. D1
and D2 are **not disjoint in calendar time** — why §10 states intervals in
epochs, not dates.

**2.4 [V] Standing checks, 2026-11-21 local (America/Jamaica, UTC−05:00) =
2026-11-22 UTC, commit `370b14b`.** Run on the CEO's machine, so the local
date is given first per §0.1(2). Clean tree with the
17 known untracked artifacts under `engine/output/`; M0 PASS 3/3; CP3 PASS
(single allowlisted lazy read-data import at `feed\live_readonly.py:77`);
`_last_sign` at five sites in `engine\strategy\ema_cross.py`.

**2.5 [V] `tools/fetch_candles.py`, 307 lines, read 2026-11-21 local /
2026-11-22 UTC.** Pasted from the CEO's machine, so the local date is first
per §0.1(2).
- **No caller-settable window.** `end_param` initialises unconditionally to
  `"latest"` and only decreases. `main()` exposes `--days` and `--symbol`.
  Every fetch anchors at the present and walks backwards until accumulated
  *span* reaches `--days`. Neither end is addressable.
- **This explains §2.3** — the overlap is what a backward walk from
  2026-11-16 UTC does when asked for 102 days.
- **The substitution defence discards**; inert on request 1 while `end_param`
  is `"latest"`; the `break` leaves the run exiting **0** with files written.
- **The summary covers the whole accepted set** and cannot disagree with the
  data file.
- **Guards intact**: `LIVE_TRADING` refusal, `is_virtual != 1` refusal, only
  `authorize` and `ticks_history` sent, writes confined to `engine/output/`.

**2.6 [R] Consequence.** The tool **cannot express** a bounded historical
request and is therefore not the acquisition path. **Frozen.** "Fetch then
discard" does not rescue it: §10.2's reason for deferral concerns what has
been **seen**, not what is on disk.

---

## §3. THE TWO MODELS

**[R]** Separated throughout, because P1 forbids merging controls with
different hazards.

| Model | Question | Boundary |
|---|---|---|
| **Displacement** (§4) | How can deferred-region data enter a response that was supposed to exclude it? | **Acquisition boundary (AB)** |
| **Containment** (§7) | Once information has entered a response, what may the system inspect, retain, expose or transmit? | **Information-exposure boundary (IEB)** |

A sound displacement model with no containment leaks through analysis. Sound
containment with a broken displacement model simply receives more to contain.

---

## §4. DISPLACEMENT THREAT MODEL

**[A] Provisional, not exhaustive.**

**4.1 Bounded displacement.** Timestamp labelling (open vs close), timezone
interpretation, daylight saving, date-vs-datetime truncation,
inclusive-vs-exclusive endpoint semantics, bar-period effects.

**4.2 Granularity.** Unexpected aggregation; a period coarser than requested.
Sits *underneath* 4.1's bound, because it determines whether P is finite.

**4.3 Substitution.** Correct-looking request metadata paired with data from a
different interval. Reference case **[V]**: the documented Deriv behaviour.
**Unbounded.**

**4.4a Coverage calculation.** What interval the returned data represents.

**4.4b Artifact integrity.** Whether the artifact accurately records that
calculation. **[R] 4.4a passing does not establish 4.4b.** The interlock: the
Deriv substitution signature *is* an evidence failure, because echoing the
request correctly is what defeats an artifact built on the echo.

**4.5 Provider-specific behaviour.** Differences between instruments,
endpoints, account tiers and permissions, and request conditions. The standing
reason C3, C4, C7 and C8 are one-way.

---

## §5. CONTROL REGISTER

**5.0 [R] Every function below is prospective.** No control is implemented.
"Preventive" describes what a control **would** do once built, tested and
gated — **not a protection that currently exists**. Read with §5.3.

| # | Control | Function | Boundary | Does **not** do | Failure mode | State |
|---|---|---|---|---|---|---|
| **C1** | Request-side granularity declaration **G** | Prevention **[C]**, prospective | AB | Does not prevent coarser data arriving | Silent, if provider ignores G | **[G]** |
| **C2** | Margin **M = 14 days** | Prevention **[C]**, prospective | AB | Does not address 4.2, 4.3, or any unbounded class | A component unbounded or unenumerated | **[G]** |
| **C3** | Granularity-fidelity probe | Detection, one-way | AB | Does not establish compliance for X, other endpoints, or later | 4.5 specificity | **[G]** |
| **C4** | Substitution probes | Detection, one-way | AB | As C3 | As C3 | **[G]** |
| **C5** | Response-side spacing check | Detection only | AB — **spends IEB** | Cannot prevent arrival; **blind to substitution** | Substituted data carries self-consistent spacing | **[G]** |
| **C6** | Payload-derived coverage check | Detection only | AB | Cannot prevent arrival; does **not** establish C7 | Blind if the artifact is built from the echo | **[G]** |
| **C7** | Artifact-integrity fixtures | Detection, one-way | AB (evidence) | Does not establish provider truthfulness or immunity to future change | Production path not genuinely exercised | **[G]** |
| **C8** | Freshness re-probe | Detection, one-way | AB | Establishes recency only | Change after the re-probe | **[G]** |
| **C9** | Gate on the inspector's interface **and** write set | **Composite** — prevention (structural and state tests (i), (ii), (iv)) **and** detection, one-way (dynamic audit (iii)); prospective, **conditional on implementation and gate passage**. See §7.6 | **IEB** | **Does not** prevent deferred data entering a response; **does not** validate provider compliance; **does not** establish that acquisition boundaries were respected; its audit component **does not** establish the absence of writes on unexercised paths | Gate not run, scoped too narrowly, examining only the declared type, missing an indirect route, or an audit mechanism lacking fidelity for memory-mapped or child-process writes | **[G]** |

**5.1 [R] Nine controls — counted by control, then by function.** The two
counts differ, because **C9 is composite** (§7.6) and counting only by control
would conceal one of its functions.

| | Count | Which |
|---|---|---|
| Controls | **9** | C1–C9 |
| Carrying a **preventive** function | **3** | C1 and C2, both assumption-conditional; **C9**, which is *not* assumption-conditional but operates only after implementation and successful gate passage |
| Carrying a **detection** function | **7** | C3–C8, **and C9's dynamic write-set audit** |
| Serving the **acquisition boundary** | **8** | C1–C8 |
| Serving the **information-exposure boundary** | **1** | C9 |

**[R]** C9 appears in **both** function rows; that is what composite means.
The six acquisition-boundary detectors are therefore **not** the only
detection functions in the architecture, and no summary of this register may
imply otherwise.
Containment is far thinner than displacement, and its single control is
unimplemented.

**5.2 [R] C5 is the coupling point** — the only control that spends one
boundary to serve the other. If C5 is removed under §7.9, the two models
decouple entirely and the stronger provider-side standard applies instead.

**5.3 [R] Every control is at state [G].** None implemented, run or passed.
The register describes an architecture, **not a defence in place**. "Three
preventive controls" must never be read as three protections now operating.

**5.4 [R]** Residual risk is not zero and cannot be made zero here. It is a
**bounded and disclosed position**, conditional on §4 being sufficiently
complete and on the assumptions named in each [C] and [A] clause.

---

## §6. DISPLACEMENT CONTROLS

**6.1 [R] C1 — request-side granularity declaration.** The request declares
**G ≤ daily**, supplying `P ≤ G`. The provider **must honour** it. C5 can
detect non-compliance but cannot prevent it; compliance is **[A]**, probed by
C3. A mechanism without an explicit granularity parameter cannot supply C1 and
is inadmissible.

**6.2 [R] C2 — the margin.**

*Combination rule.* §4.1's components are combined by **addition**, giving a
worst-case **directional** bound — not because they are independent
(independence would argue root-sum-square, which is *smaller*) but because
their effects may align in the dangerous direction and are positively coupled
through one wrong model of one provider. **A worst-case bound, not a
statistical confidence statement.**

*Envelope* `38h + 2P`. **[V]** Internally consistent: a coherent joint
scenario reaches `≈36h + 2P` — an instant sent as `D 00:00Z`, truncated to
date `D`, resolved end-of-day at UTC−12 = `D+1 11:59:59Z`, plus close
labelling and inclusive endpoints — within two hours of the envelope.

| Granularity | P | Worst case | M = 14 d factor |
|---|---|---|---|
| Hourly | 1 h | 40 h = 1.67 d | 8.40 |
| **Daily** | 24 h | **86 h = 3.58 d** | **3.91** |
| Weekly | 168 h | 374 h = 15.58 d | **0.90 — fails** |
| Monthly (30 d) | 720 h | 1478 h = 61.58 d | 0.23 — fails |

**[C] M = 14 days is not independently safe.** It holds only under: margin ≥
14 days **and** G honoured. **M must never be described as protecting against
provider non-compliance.** C3 is the only test of that assumption, and C3 is
one-way.

**[A] The envelope is only as strong as the bounds assigned to its
components.** §4 is provisional; if a component's bound is wrong or a sixth
mechanism exists, the envelope fails.

**[R] Residual, retained.** Under M = 14 d a weekly-bar response displaces up
to 15.58 days, leaving a **1.58-day** crossing window — kept to show what
removing the cap reopens.

**[R] The cap is structural.** Margin alone needs M ≈ 61 d for weekly and is
defeated by monthly; the regress has no stopping point.

**6.3 [R] C3 and C4 — the sacrificial-instrument tripwire.** Instrument **S**
named with its reason and **committed and pushed before any probe** (explicit
paths; never `git add -A`). S **permanently ineligible as X**, struck from the
§9 list; designation precedes or is disjoint from list construction. S
assessed on specification pages only. **No X data requested, viewed or exposed
during the test.** Probes use the **actual** mechanism, endpoint and request
form.

| # | Probe | Reads on |
|---|---|---|
| i | In-range request | Baseline |
| ii | Out-of-range future | 4.3 |
| iii | Out-of-range past, before S's history begins | 4.3 |
| iv | Granularity fidelity: declare G, inspect the period returned | 4.2 |
| v | **Error specificity** — required **only** where E2 is asserted under §8.5 case 3 | Whether an out-of-range error is specific to the range condition |

| Result | Consequence |
|---|---|
| Substitution observed | **Path disqualified** |
| Granularity non-compliance observed | **Path disqualified** |
| Clean failure observed | Recorded. **No validation.** |
| Ambiguous | **No validation.** Investigate without exposing X |

Disqualification scopes to the **path** — provider, endpoint and request form;
changing any requires fresh probes.

**[R] Probe v, and when it is required.** An error returned for an
unsatisfiable range is evidence of rejection **only if the error is specific
to the range condition**. A generic failure that happens to coincide with an
out-of-range request establishes nothing. Probe v therefore issues other
failing requests on S — unknown symbol, invalid granularity, malformed
parameters — and confirms that the range error is **distinguishable** from
them. Probe v is **not** required for admissibility, because E2 is not
required (§8.9); it is required **whenever E2 is asserted** under §8.5.

**[R] Two things kept distinct, and no wording may blur them:** *testing the
provider/endpoint/request combination*, and *assuming its behaviour
generalises to X*. **[A]** A clean result leaves the declared uniformity
assumption unvalidated. The sacrificial instrument never establishes universal
provider reliability.

**6.4 [R] C6 — payload-derived coverage, under quarantine.**

> Coverage is calculated from the **received** response payload **under
> quarantine**, never from the request or echoed response parameters. The
> payload is **not admitted into the accepted exploratory dataset** until the
> applicable checks pass.

**[V]** The frozen tool models the calculation correctly, deriving
`first_epoch`/`last_epoch` from its accepted set; the quarantine sequencing
above is additional to it.

**[R] C6's test is universal, not extremal.** §10.5's invariant claims that a
passing response contains no deferred-region timestamp. **That claim can be no
stronger than the test**, so the test covers **every** returned timestamp. C6
must not rest on the first timestamp, the last timestamp, echoed interval
metadata, or an assumption that the payload is ordered and well-formed.

| # | Requirement |
|---|---|
| 1 | The predicate is evaluated over **every element** of the returned timestamp set: each `t` satisfies `start_bound <= t < end_bound`. |
| 2 | **No reliance on ordering.** The check must not assume the provider returned the payload sorted. |
| 3 | **Check before transform.** The boundary check runs on the **raw returned set**, before deduplication, sorting, resampling or any other transformation. |
| 4 | **Malformed entries fail the response**, and are never skipped. An entry that cannot be parsed into an integer epoch has an unknown value, and skipping it would let an unknown value pass. |
| 5 | **Count reconciliation against an independently established count** — see the clause below. A count accumulated by the checking iteration itself is not acceptable. |
| 6 | **An empty return is its own outcome, not a pass.** A universal predicate over an empty set is vacuously true; an empty payload is reported as "no data", never as "boundary respected". |
| 7 | **Off-grid entries do not pass silently.** Any `t` with `t % G != 0` is reported and halts the acquisition pending convention re-derivation under §8.8. Per §15.2 the frozen tool never checked this, and D2's first epoch entered the sealed record off-grid as a result. |

**[R] Requirement 5 in full — the count must be independent of the check.**
If the implementation counts entries using the same truncated or filtered
iteration that performs the timestamp checks, **both counts agree despite an
incomplete inspection** and the reconciliation confirms itself. Therefore:

1. The raw payload's entry count is **determined independently** — from the
   parsed structure's own cardinality, not accumulated by the checking loop.
2. **Exactly one** valid timestamp is extracted and checked **for every
   entry** — not zero, not several.
3. The checked count **equals** that independent raw-entry count, asserted.
4. **Any extraction failure rejects the response** (requirement 4), and is
   never recorded as an entry checked.

**[A] What C6 still does not cover.** C6 checks timestamps **as returned**. If
the provider labels a bar with a timestamp that misrepresents the interval the
bar actually covers — §4.1's labelling error — C6 passes a bar whose true
market time lies outside the bound. That half of the hazard is carried by
**C2's margin**, not by C6. Neither control covers both halves, and per **P1**
neither is described as though it did.

**6.5 [R] C7 — artifact integrity, by adversarial fixture.** Both fixtures run
through the **actual production processing and artifact-generation path**.

| Source | Fixture 1 | Fixture 2 |
|---|---|---|
| Request states | **A** | **A** |
| Echoed metadata states | **A** | **B** |
| Returned payload represents | **B** | **C** |
| **Expected artifact coverage** | **B** | **C** |

Fixture 1 establishes that the artifact derives coverage from the payload
rather than from the agreeing request-and-echo. Fixture 2 makes all three
sources distinguishable, so a generator reading the **echo** cannot pass by
coincidence — which Fixture 1 alone cannot detect, because there request and
echo agree.

**[R] Failure condition, stated exactly.**

> A mismatch between the **independently computed payload coverage** and the
> **generated artifact** disqualifies the path.

A discrepancy between the requested and returned intervals is **not** a C7
failure. It is the test stimulus — precisely what the fixture exists to
create, and what the artifact is required to report faithfully.

**[R] No simplified substitute.** If the production path cannot accept a
fixture without changing production behaviour, **that limitation is
documented**; a simplified test implementation is never substituted and
claimed as the production path passing.

**[A] Scope of a pass.** Establishes that C7 is correctly implemented. Does
**not** establish that a real provider produces every failure mode, that the
provider's raw response is truthful, or that the artifact is immune to future
implementation changes.

**6.6 [R] C8 — freshness.** Probes ii–iv re-run immediately before the first X
acquisition, same session, both artifact sets committed, using the **same**
endpoint, request structure, granularity declaration and relevant
account/access conditions. Any **material provider-side change** invalidates
the result and requires reassessment. Establishes **recency**, never
reliability.

---

## §7. CONTAINMENT CONTROLS

**7.1 [R] Current state.** The three tiers are **policy**. Policy is not a
control. Until C9 is implemented and gated, **containment rests entirely on
policy**.

**7.2 [R] The three tiers.**

| Tier | Content | Treatment |
|---|---|---|
| **Price/data** | Deferred OHLC, volume, indicators, charts, derived market information | **Prohibited** |
| **Restricted metadata** | Timestamps and spacing, solely for boundary-integrity and granularity checks | **Conditionally permitted** |
| **Analytical** | Any use of deferred information for instrument selection, hypothesis generation, comparison or refinement | **Prohibited** |

**7.3 [R] Conditions on the restricted tier.** Minimum timestamp information
only; no deferred prices or price-derived fields displayed, retained for
analysis, or passed to hypothesis-generation processes; the check automated
and narrowly scoped; **immediate abort** on a detected breach, not
investigation; the exposure **recorded explicitly** and **never** described as
zero exposure or as preservation of an entirely untouched dataset.

**7.4 [R] Automation is load-bearing but not sufficient.** A program that
computes modal spacing, compares it to G and discards cannot form a hypothesis
from what it read; a person reading the same timestamps can. But instructing a
process is no stronger than instructing a person unless the process is
constrained in what it can **retain and emit**.

**7.5 [R] Interface constraints.** Automated timestamp and spacing inspection;
**no interactive display** of deferred timestamps; **no per-bar output**
reachable by hypothesis-generation processes; **only narrowly defined
results** — pass/fail and a breach indication; **immediate abort** on breach.
The standard: the process must be **architecturally incapable** of exposing
the underlying observations for analytical use through its permitted
interface. Not forbidden from it — incapable of it.

**7.6 [R] C9.** Precedent **[V]**: this project's only other incapability
claim — that execution is impossible — rests not on intent but on verified
code guards and a static import gate (`check_cp3_imports`), re-run every
session.

1. The inspector returns a **closed result type**.
2. Containing only: verdict; breach indication; permitted scalars (§7.8).
3. **No per-bar records or timestamp-valued members** exposed through that
   interface.
4. The hypothesis-generation path **cannot import** the inspector or access
   its underlying observations.
5. A **static gate** verifies these restrictions.
6. The gate runs as a **standing check** alongside M0 and CP3.
7. **The gate examines the actual production interface and dependency path**,
   not merely the declared result-type definition — otherwise an
   implementation could satisfy the type declaration while exposing raw
   observations by another route.
8. **[R] Indirect access routes are in scope.** A direct-import restriction
   can pass while another route still exposes the data. The gate therefore
   also covers:
   - **shared storage, files and shared memory** — a static check that no
     hypothesis-path module *references* the quarantine location does **not**
     establish that the process *cannot read it*: a generic filesystem call,
     an environment-derived path or another indirect mechanism bypasses the
     check. The architecture must therefore establish an **enforceable access
     boundary**, and the gate must test the **actual restriction** rather than
     the absence of a known reference.

     **[R] Non-persistence is necessary but insufficient.** Keeping the
     quarantined payload out of the filesystem until the checks pass prevents
     a failed payload reaching disk. It does **not** prevent another function
     in the same process obtaining a reference to the payload and exposing its
     timestamps to the hypothesis-generation path, with no filesystem
     involved. Non-persistence addresses one half of the hazard only.

     **[R] The requirement.** The quarantine boundary must prevent the
     hypothesis-generation path from accessing raw observations **whether
     those observations are held in memory or on disk**.

     **[R] Default architecture: process-level isolation.** The inspector
     process holds the transport and the raw response and exposes **only its
     closed result type** to the hypothesis-generation process. The only
     channels across the boundary are the serialised closed result and, on a
     pass, the accepted exploratory dataset.

     *Why this is enforceable where same-process is not:* in a same-process
     design the raw payload is reachable by any code in the process, so the
     only barrier is "no code dereferences this object" — a statement about
     every future edit, and one a static gate cannot verify, because it cannot
     tell what a held reference will be used for. Process separation converts
     that unverifiable property into a verifiable one: **no module imports
     these modules or opens these resources.** That is exactly the shape of
     `check_cp3_imports`, which the project already relies on for its
     execution-impossibility claim.

     **[R] The two permitted channels, declared exhaustively.** A consumer
     process must have *some* means of receiving the closed result, so a
     prohibition on all inter-process communication would reject the intended
     architecture. Gate test (ii) therefore prohibits **undeclared** channels,
     not communication as such. Exactly two channels cross the boundary:

     | # | Channel | Direction | Content | Schema |
     |---|---|---|---|---|
     | 1 | **Result channel** | inspector → consumer, unidirectional | the closed result type only | §7.8's permitted fields |
     | 2 | **Accepted dataset** | inspector writes, consumer reads | only a payload that passed C5 and C6 | §10.5's summary and dataset |

     **[R] Channel 1 is safe because of the type, not because of the
     transport.** The closed result type has no member capable of carrying a
     raw observation, so nothing raw can traverse channel 1 **even if its
     transport were a shared memory segment**. The guarantee therefore sits
     where C9 items 1–3 and 7 already verify it, and the gate's job reduces to
     two checkable questions: **is the result type closed**, and **is the
     transport the declared one**. The transport is named in the architecture
     so that an undeclared one is distinguishable from it.

     **[R] What the G0a gate tests — the actual restriction, not the design
     intent.**

     | # | Test | Kind |
     |---|---|---|
     | (i) | The consumer's module graph excludes the inspector, the transport and the raw-response type | static — **preventive** |
     | (ii) | The consumer's external channel and resource references are **enumerated**, and **every one maps to a declared channel** (1 or 2) with its declared direction and schema. Any unmatched reference **fails the gate**. | static — **preventive** |
     | (iii) | The inspector's **observed** write set is confined to the declared allowlist, audited at the filesystem-call level | dynamic — **detection, one-way** |
     | (iv) | Where the quarantine touches disk at all, the **actual** permission state is asserted | state assertion — **preventive** |

     **[R] Test (ii) is an allowlist, not a blocklist — and that is
     substantive, not stylistic.** An earlier draft enumerated forbidden
     transports (IPC, shared memory, memory mapping, debugger facilities) with
     an exception for channel 1. That formulation had two defects: it would
     **pass any mechanism nobody had thought of**, and it needed an exception
     for the very channel the architecture depends on. The allowlist form
     **fails unknown mechanisms by default** and needs no exception, because
     channel 1 is *matched* rather than excused. It is also the same
     discipline as test (iii)'s independently declared write allowlist, so the
     two tests no longer reason in opposite directions.

     **[R] C9 is a composite, and P1 applies inside it.** Its tests are not of
     one kind: (i), (ii) and (iv) verify structural or state properties and are
     preventive; **(iii) is a dynamic observation and is therefore detection,
     one-way** — an unexpected write disqualifies, while a clean audit does not
     establish that no write occurs under an unexercised condition. C9 must
     never be summarised as four verifications.

     **[R] Scope of the write-set audit — to be specified at G0a.**
     - **Operations observed:** file creation, open-for-write, write, rename
       or move, truncate, delete, directory creation, and memory-mapped
       writes. Not open-for-write alone.
     - **Execution paths exercised:** at minimum pass, C5 failure, C6 failure,
       malformed-entry rejection, empty return, transport error, **and an
       uncaught-exception path**. The hazard is precisely a write on a failure
       path — a diagnostic dump in an exception handler — which is the
       filesystem counterpart of the traceback route named above.
     - **Child processes:** writes by any child are attributed to the
       inspector. Either the audit follows children, or the architecture
       **prohibits the inspector spawning them**, which is simpler and
       statically checkable.
     - **Comparison:** observed paths are **canonicalised** — symlinks and
       relative paths resolved — before an exact-set comparison against the
       allowlist. Any path outside it fails the gate.
     - **[R] The allowlist is declared independently, never inferred from what
       was observed.** An allowlist derived from the audit's own output would
       confirm itself, which is §6.4 requirement 5's defect in another place.
     - **[A] Mechanism fidelity is a separate question from scope**, and is
       where this is most likely to be hard. **A complete specification of
       what must be observed is not a demonstration that the chosen mechanism
       can observe it.** Candidate mechanism classes on the target platform
       differ materially in coverage and in the privilege they require, and
       they differ **precisely at the two scope items most likely to matter**:
       **memory-mapped writes** and **writes by child processes**. The
       mechanism decision is therefore made against those two items, not
       against the easy cases. §14.14 carries it as a **G0a** decision in its
       own right, separate from the scope above.

     The static reference check is retained as a **supplementary** check,
     never as the mechanism.

     **[O] A same-process design** is permitted only on demonstration of an
     equivalent enforceable mechanism. The burden is on the proposal, and
     keeping the payload in memory does not discharge it.

     **[A] Declared threat model, so the boundary is not overclaimed.** This
     boundary is against **architectural and accidental exposure by our own
     code, present or future**. It is **not** against adversarial same-user
     process inspection: a debugger attached under the same OS account defeats
     all of the above, and on Windows under a single user account separate
     processes give no mutual memory protection. The hazard being managed is
     **a code path existing**, not an attacker.

     **[A] Residual — process memory can reach disk outside the inspector's
     own write set.** Core dumps, crash reporters, and swap or pagefile writes
     are not filesystem calls the inspector makes, so test (iii) does not
     catch them. An in-memory quarantine is therefore **not** a guarantee of
     non-persistence. **[O]** Mitigation to settle at G0a: disable core dumps
     and crash reporting for the inspector process, or declare the exposure;
   - **caches and serialised intermediates**, including any on-disk or
     in-process cache holding raw observations;
   - **logs and standard output** — no raw observation is written to any log
     or stream;
   - **[R] exception messages and tracebacks** — a naive implementation leaks
     a timestamp array in a traceback, and an uncaught exception is an
     unreviewed output channel. Raw observations must not appear in any
     exception payload.

**[R] Classification.** C9 is a **composite information-exposure-boundary
control**, prospective and conditional on implementation and gate passage. Its
structural and state components — tests (i), (ii) and (iv) — provide
**preventive** containment; its dynamic write-set audit — test (iii) —
provides **one-way detection**.

**Neither function** prevents deferred data entering a response, validates
provider compliance, or establishes that acquisition boundaries were
respected. C9 restricts what happens to information **after it has arrived**.
It must not be counted as reducing displacement probability or strengthening
the margin, and the detection component must not be counted as prevention
(**P1**). **Its failure — in either component — means the metadata inspector
cannot be accepted for use under the restricted tier.**

**7.7 [R] C5 remains a detector.** It cannot undo the fact that a response
containing deferred data has arrived. **The primary protection remains
request-side enforcement.** C9 contains what arrived; it does not reduce what
arrives.

**7.8 [R] Operational inspection versus durable record.**

*Operational inspection.* The transient process may access the minimum
timestamps required for its check. **That information must not become a
durable analytical artifact**, must not be displayed interactively, and must
not pass into hypothesis-generation workflows.

*Durable inspection record.* The committed record contains only:

| Field | Permitted representation |
|---|---|
| Control | `C5` |
| Run identifier | Opaque identifier |
| Inspection time | **Wall-clock** time (not market time) |
| Inspection scope | Fixed categorical value |
| Verdict | Pass / fail |
| Breach indication | Yes / no |
| Breach type | Closed category |
| Breach magnitude | Seconds **relative to the requested bound** |
| Breach count | Bars **relative to the requested bound** |
| Abort status | Yes / no |

**Prohibited representations:** first or last market timestamps; calendar
dates or date ranges; market-time descriptions of the breach; deferred price
or price-derived values; raw response excerpts.

Worked distinction — permitted: *"Exceeded requested bound by 3 bars."*
Prohibited: *"Returned data through 7 November."* The first records the
magnitude of a control failure; the second describes the deferred dataset's
temporal coverage.

**[R] The record format is locked before acquisition, not improvised after an
incident.**

**7.9 [R] Escape clause.** If the project later decides that even
timestamp-only deferred metadata is impermissible, C5 is **removed** and the
path must meet the stronger provider-side enforcement and independent-evidence
standard. **A fresh agreement decision**, not available by interpretation. See
§5.2 for the structural consequence.

---

## §8. ADMISSIBILITY OF AN ACQUISITION PATH

**8.1 [R] Native range restriction.** Explicit start and end boundary in the
request. A mechanism accepting only a duration, a count, or an
anchor-plus-span is inadmissible — the shape of the frozen tool.

**8.2 [R] Explicit granularity.** Must supply C1 (§6.1).

**8.3 [R] No unrestricted historical download.** Full-history or
to-the-present download followed by filtering, truncation or deletion is not
acceptable, whatever the retention policy afterwards.

**8.4 [R] No deferred-range exposure during assessment.** Extends past data
files to previews, charts, summaries, metadata, aggregate statistics and
cached responses. **Consequence:** this disqualifies interactive data portals
whose instrument pages render a current price chart, because opening the page
to assess the provider is itself exposure. Candidate assessment therefore
begins and stays with non-price-history evidence — provider documentation, API
specifications, endpoint capabilities, request formats, logging arrangements.

**8.5 [R] The three evidence components.** A request log proves what was
**requested**. Echoed response parameters prove what the provider
**reported**. C6 and C7 establish what the payload **represents** and whether
the artifact records it faithfully. **None of these establishes that the
provider enforced the requested bounds before producing the response.** The
evidence is therefore separated and never conflated:

| # | Component | Establishes | Supplied by |
|---|---|---|---|
| **E1** | **Request evidence** | The exact interval and granularity requested | Request artifact, captured before acquisition |
| **E2** | **Provider-enforcement evidence** | The mechanism by which those restrictions were applied **before the response was produced** | The provider, if at all |
| **E3** | **Returned-payload evidence** | The interval and granularity the received data actually represents | C6, under quarantine (§6.4) |

**[R] E1 and E3 must never be promoted into proof of E2.**

**[A] E2 is expected to be absent, and is never directly observable.** E2
concerns the provider's internal behaviour, which can only ever be inferred
from its outputs. **Every E2 claim is therefore an inference whose basis must
be stated.** Few market-data providers supply any means of making it: a
contractual statement is documentation, not evidence; an echo reports the
request, not the enforcement.

| Candidate E2 | Disposition |
|---|---|
| A reported **applied range** that is merely another echoed parameter | **Not E2.** It reports what the provider says, which is the conflation §8.5 exists to prevent. |
| A reported applied range with **credible semantics** establishing that it represents the actual applied restriction, **corroborated against the returned payload** | **Potentially E2**, on a stated inferential basis. |
| An **explicit error** for an unsatisfiable range | **Potentially E2**, provided the error semantics genuinely establish rejection rather than an unrelated or generic failure — which requires **probe v** (§6.3). |

**[R] Corroboration in case 2 is informative only where the applied range
*differs* from the requested range.** If the two never diverge, a match tells
nothing, because a plain echo would match equally well. Case-2 corroboration
is therefore gathered by C4's out-of-range probes on S, never by in-range
requests.

**[R] Disposition.** Where E2 is unobtainable, **the limitation is recorded**
as a declared unvalidated assumption. Its absence is **not** by itself
disqualifying — see §8.9 and §8.10. What compensates for it is C4's probes
(one-way, disqualifying only), C6's post-hoc detection, C2's bound on
displacement, and C5/C9's containment. What does **not** compensate for it is
a clean probe result, which per §6.3 validates nothing.

**8.6 [R] Fixture-injectability.**

> An acquisition path is admissible only if its proposed tooling architecture
> supports adversarial fixture injection through the same production
> processing and artifact-generation path used for real acquisition, without
> requiring a separate simplified implementation to establish C7.

Does **not** require the provider to supply fixture support. Requires the
proposed **acquisition architecture** to make the evidence test possible.

**8.7 [R] Containment capability.** The architecture must support C9 (§7.6) —
closed result type, no per-bar exposure, enforced dependency separation
including indirect routes, and **gated: statically for tests (i), (ii) and
(iv), and by the dynamic write-set audit for test (iii)**. A policy promise is
insufficient, and a static gate alone does not discharge this clause.

**8.8 [R] Timestamp and grid verification from permitted data only.** X's
granularity and open/close convention established from exploratory-region
data. The 900-second grid is **not** assumed. **[V]** D2's first epoch sitting
897 s off the boundary, having entered the sealed record silently, is the
standing evidence that this is not a formality.

**8.9 [R] Disposition — three cases, not two.**

| Case | Disposition |
|---|---|
| **Demonstrated failure** — a probe shows substitution, granularity non-compliance, or a C7 artifact mismatch | **Reject the path.** |
| **E1 or E3 absent, contradicted or insufficient** | **Do not admit the path.** |
| **E2 absent, with E1 and E3 sound and no demonstrated failure** | **Admissible, with the limitation recorded as a declared unvalidated assumption** (§8.5). |

**[R]** Nothing here may imply that the tripwire alone establishes
reliability. A clean sacrificial test does not establish reliable enforcement
for X (§6.3).

**[R] Scope of the rejection default.** Rejection remains the default where
**E1 or E3** is doubtful, contradicted or insufficient, or where a
**demonstrated failure** exists. **The absence of E2 alone is governed by the
third case above and is not grounds for rejection.**

**[R] P2 is unaffected by this narrowing.** P2 concerns whether *our own*
controls can be independently tested — §8.6 and §8.7 — not whether the
provider's enforcement can be evidenced. Narrowing §8.9 does not relax P2,
and P2 continues to stand even if it leaves no admissible provider.

**8.10 [R] RULED — the permissive reading governs.** Read literally, "a path
is inadmissible whenever the required enforcement evidence is absent" would
have collided with §8.5's instruction to **record the limitation** where the
provider offers no credible means of establishing E2: together they would have
made **every** path inadmissible, since E2 is expected to be absent.

**Ruled 2026-11-21 local / 2026-11-22 UTC: E2's absence, by itself, is not a
disqualifier where E1
and E3 are sound and no demonstrated failure exists.** The three dispositions
in §8.9 are the governing rule. The stricter reading — which would have closed
Route 4 immediately — is **not** intended.

**[R] What the ruling does not do.** It does not convert a missing E2 into
verified provider enforcement. C2, C4, C5, C6 and C9 supply bounded-risk,
probing, detection and containment measures; they do **not** collectively
establish that the provider enforced the requested boundary before producing
the response. A clean C4 probe is not proof of future provider behaviour, and
C6 is post-response detection, not prevention.

**[R] How such a decision must be phrased.** An admission under the third case
of §8.9 is a **conditional acceptance with a declared enforcement-evidence
limitation and a stated residual risk**. It must never be phrased, summarised
or carried forward as though the boundary were guaranteed. This clause and
**P1** together are the centre of this agreement.

---

## §9. INSTRUMENT-SELECTION RULE

The hazard: choosing X *because* it looked promising, then reporting the
result as though X had been chosen blind. Undetectable afterwards from
artifacts.

**9.1 [R] Selection precedes acquisition and is sealed.** Candidate list,
criteria, ordering and tie-break committed and pushed **before any request is
issued**. Explicit paths; never `git add -A`. The commit hash is the proof of
ordering.

**9.2 [R] Criteria must be ex ante** — evaluable **without reference to any
property of X's own price history**. Admissible: contract specification,
venue, quoted granularity, span coverage, cost, existing credentials, firm
permission, **and whether the acquisition path satisfies §8**. Inadmissible:
realised volatility, correlation with the existing series, backtest
performance, anything computed from a sample fetch.

**9.3 [R] §8 capability is an admissibility criterion**, struck at selection
time before any data exists. Assessing it must itself respect §8.4.

**9.4 [R] The list is fixed and ordered in advance**, with a deterministic
tie-break. Acquisition proceeds down the list. The order is not revisited.

**9.5 [R] One-way exit only.** A candidate may be dropped only for a reason on
a closed, pre-stated list — span not covered, granularity mismatch,
unavailable, prohibited by the firm, acquisition path inadmissible under §8.
**Never** for a reason discovered by looking at the data. "That one didn't
work, try the next" is the prohibited move, and dropping on a data-discovered
ground is that move wearing a procedural hat.

**9.6 [R] K is bounded before the first fetch.** A multiplicity parameter, not
a budget to be spent until something appears. A larger K buys more hypotheses
to test later and more multiplicity when they are tested; it does not buy
evidence.

**9.7 [O] The candidate list and K are deferred to the selection stage**,
after the architecture requirements are settled. Not drafted now, and they do
not block G0a.

---

## §10. THE ACQUISITION BOUNDARY

**10.1 [C] The two intervals**, in epochs, **conditional on §8.8** — if X's
timestamps are close-times, or X's granularity is not 900 s, both bounds move
and must be re-derived before use.

| Region | Interval | Status |
|---|---|---|
| **Exploratory** | `t < 1787193900` | Usable for hypothesis generation |
| **Deferred** | `1787193900 <= t < 1794858300` | **Not acquired. Not exposed. Not usable.** |

Derivation, checkable: `1787193900 = 1787193000 + 900` — the exploratory
region ends with D1's last bar inclusive. `1794858300 = 1794857400 + 900` —
the deferred region ends with D2's last bar inclusive. **[A]** Both assume
epoch denotes bar-open on a 900-second grid, the assumption §8.8 exists to
test.

**10.2 [R] Why deferred.** Acquiring or viewing X over D2's span during
generation destroys D2 as a holdout for any cross-series hypothesis. D2 is
unspent and is **the only remaining clean historical test sample**. Not a
scheduling preference; not relaxable for convenience or for §13.

**10.3 [R] The deferral is one-way.** X over the deferred region may be
acquired only under a **separate written agreement**, after the generation
phase has closed and a candidate has been frozen. Not unlocked by this
agreement, by elapsed time, or by a null result in the exploratory region.

**10.4 [R] Staged first acquisition — both bounds explicit.** Per §8.1 the
request carries a start **and** an end.

- **End bound:** no later than `1787193900 − M`.
- **Start bound:** `end − W`, where **W** is declared in advance and committed
  with the selection record.
- **[R] W is sized for the inference it must support**, not for convenience:
  it must yield enough bars at the declared G for modal-spacing inference to
  be robust against gaps and holidays, while remaining inside the exploratory
  region.
- **[O] PROPOSED: W such that the window yields at least 500 bars at declared
  G** — at G = 900 s that is ≈5.2 days, comfortably inside the region. W and G
  interact, so the figure is settled together with G, not before it.

Then X's granularity and convention are established from that result; then
§10.1 is re-derived; only then may an acquisition approach the boundary.

**10.5 [R] Acquisition sequencing — corrected.** The v2 wording required a
summary containing first epoch, last epoch, count and inferred granularity to
be committed *before the data is read*, which is impossible: those fields are
derived from the response. The sequence is:

1. **Capture the request artifact (E1) and commit it — before acquisition.**
2. **Receive the response into quarantine** (§6.4). It is not an accepted
   dataset.
3. **Run the automated checks** — C5 spacing, C6 coverage — on the quarantined
   payload.
4. **Derive coverage and granularity from the received payload.**
5. **Produce the permitted operational result.**
6. **Commit only the allowed durable artifacts.**

**[R] The containment invariant, which resolves the conflict with §7.8.**
There is no need for two conflicting schemas, because the two artifacts never
describe the same data:

> **No durable artifact ever contains a deferred-region timestamp.** A
> response that passes C5 and C6 lies wholly within the exploratory region
> **as labelled** (§6.4), so its acquisition summary may carry its own first
> and last epochs freely — they are permitted data. A response that fails is
> **rejected whole** and no acquisition summary is produced for it; the only
> durable output is the magnitude-only inspection record of §7.8.

**[A] Residual.** With C6 specified universally (§6.4) the invariant is now
**exactly as strong as its test**, for timestamps **as returned**. Two gaps
remain, both declared rather than resolved: C6 is detection, not prevention
(§5), so a crossing it cannot see would still reach a summary; and a labelling
error (§4.1) can place a correctly-labelled bar's true market time outside the
bound, which is **C2's** province and not C6's.

---

## §11. X IS EXPLORATORY ONLY

**[R]** X is **not a holdout**. Nothing computed on X confirms anything. X can
generate a hypothesis; it cannot test one. A result found on X and reported as
evidence is a false positive by construction, however it was found. The
generation-phase agreement carries this as an explicit prohibition rather than
relying on anyone remembering it.

---

## §12. GATE SEQUENCE

**[G] None passed.** No implementation begins because the architecture has
been discussed or because a provider appears promising. The fixture seam is
designed in, never retrofitted once implementation has become difficult to
test.

| Gate | Work | Depends on |
|---|---|---|
| **G0** | Rule on this document, incl. **§8.10** | — |
| **G0a** | Architecture requirements: §8.6 fixture-injectability, §8.7/C9 containment incl. indirect routes, §7.6 process-level isolation with its four gate tests and two declared channels, §7.6 write-set audit **scope**, **§14.14 audit mechanism and its fidelity at memory-mapped and child-process writes — a decision distinct from the scope**, §7.6 core-dump mitigation, §6.4 C6 universal coverage with independent count reconciliation, §14.13 off-grid resumption evidence standard, §7.8 record format, §10.5 sequencing | G0 |
| **G1** | Identify a candidate path; assess against §8 under §8.4 discipline | G0a |
| **G2** | Design the replacement tooling with the fixture seam and closed result type | G1 |
| **G3** | Produce and review a **locked implementation plan** | G2 |
| **G4** | **Explicit approval to implement** — a separate gate | G3 |
| **G5** | Implement | G4 |
| **G6** | Test the controls: C7 fixtures 1 and 2; C9 in full — the static tests (i), (ii), (iv) **and** the dynamic write-set audit (iii) | G5 |
| **G7** | Designate S by commit; run C3/C4 probes i–iv | G1, G5 |
| **G8** | C8 freshness re-probe | G6, G7 |
| **G9** | First X acquisition per §10.4 and §10.5, with C5, C6, C9 active | G8 |
| **G10** | Establish X's convention; re-derive §10.1 | G9 |

---

## §13. DEADLINE

**[R] Route-decision deadline 4 December 2026.**

> **4 December determines whether Route 4 proceeds. It does not certify that
> Route 4 works.**

The legitimate decision: is Route 4 worth proceeding through the remaining
gates; is its potential research value sufficient to justify the tooling and
validation work; or should Route 4 be closed as impractical. It is **not**
legitimate to read the deadline as requiring a functioning provider, completed
tooling, or acquired X data. **Acquisition before 4 December is highly
unlikely, and that is not a reason to compress the gates.**

---

## §14. OPEN ITEMS

**14.1 [O]** No candidate path identified. Under **P2** it remains live that
none is found, and that outcome is accepted rather than worked around.

**14.2 [O]** Candidate list and K — deferred to the selection stage (§9.7).

**14.3 [O]** X's timestamp convention and granularity — deferred until
permitted exploratory acquisition. §10.1 is conditional on it.

**14.4 [O] Not assessed** — the workspace's attached market-data connector.
Admissibility under §8 **not** assessed; assessing it is §9 work requiring
§8.4 discipline. Recorded so its existence is not mistaken for 14.1 being
solved.

**14.5 [A]** The displacement threat model is provisional. No category added
at the last two revisions — weak evidence of convergence, **not** proof of
completeness.

**14.6 [O]** Whether C7's fixtures can be constructed against a real
candidate's architecture — correctly deferred to G1. G0a may accept
fixture-injectability as a mandatory requirement; G1 determines whether any
real candidate satisfies it.

**14.7 [A]** Nothing here shows X **can** be acquired within the boundary.

**14.8 [O]** The 21-item defect register in
`docs/PHASE_50_DEFINITION_SESSION_1.md` — carried forward undischarged.

**14.9 [O] The enforceable access boundary** (§7.6). **[R] Confirmed on
review: process isolation remains the default, and a same-process alternative
carries the burden of demonstrating an equivalent enforceable boundary.** What
remains open is the concrete design and whether any same-process proposal can
discharge that burden. A **G0a** architecture requirement. §8.10's reading,
which was 14.9 in v3, is **ruled** and closed.

**14.12 [O] The core-dump residual** (§7.6). **[R] Confirmed on review:
disabling core dumps and crash reporting is the cleaner containment position
where technically feasible. If the exposure is accepted instead it must be
documented explicitly as residual risk, and must never be described as
non-persistence.** What remains open is the technical feasibility on the
target platform. A **G0a** decision.

**14.13 [R] Off-grid resumption — the principle, settled.** An off-grid result
**rejects the current response and suspends acquisition**. Resumption
requires, cumulatively: (a) an **independently justified** timestamp and grid
convention; (b) **recalculation** of the applicable boundaries under it
(§10.1); and (c) a **recorded decision** that the acquisition path still
satisfies this agreement. **The offending response is never silently repaired,
filtered or admitted, and a halt is never cleared by changing a parameter or
by ignoring the offending entries.** **[O]** The exact evidence that
establishes the convention in (a) is a **G0a** decision.

**14.14 [O] The write-set audit — two decisions, not one.** G0a must settle
**both**:

1. **What the audit must observe** — the five-part scope in §7.6. *Stated.*
2. **Which mechanism can reliably observe that complete scope on the target
   platform** — *not stated, and not to be assumed.*

**[R] A complete specification of (1) is not a demonstration of (2).**
Candidate mechanism classes differ in coverage and in required privilege, and
differ most at **memory-mapped writes** and **child-process writes**, so (2)
is decided against those two items specifically.

**[R] If no available mechanism covers the full scope, the shortfall is
recorded as residual risk under §7.6 and is never closed by narrowing the
scope to what the mechanism happens to cover.** Trimming (1) to fit (2) would
make the audit self-certifying, which is the same defect as an allowlist
inferred from observation.

**14.10 [O] W in §10.4** — settled together with G. The 500-bar figure is a
proposal only and must not become a settled requirement without examining its
relationship to W, G and the inference it must support.

**14.11 [O] Probe v** (§6.3) — not required for admissibility; required
whenever E2 is asserted under §8.5.

---

## §15. APPENDIX — FINDINGS NOT IN ROUTE 4 SCOPE

Proposed destination `docs/APEX_DEFERRED_FIXES.md`.

**15.1 [V] Deferred item D1 partially discharged.** The docstring now
correctly states that `count` is a time window, not a candle cap. Three
instances of the superseded claim survive: the comment on
`CANDLES_PER_REQUEST = 1000` ("observed server cap"), the banner line
`per request : 1000 candles`, and the summary key `candles_per_request` — the
last two in artifacts that outlive the run. **Bounded documentation correction
only. Not an acquisition authorisation, not a behaviour change.**

**15.2 [V] Off-grid epochs pass unvalidated.**
`gaps_over_granularity_count` counts intervals larger than the granularity;
nothing tests `epoch % GRANULARITY`. D2's first epoch, three seconds short of
`1786039200`, entered the sealed record silently. The evidential basis for
§8.8 and §10.1's conditionality. **No change to the frozen tool is proposed.**

**15.3 [V] `MAX_CONSECUTIVE_EMPTY = 4` against `WEEKEND_STEP_SECONDS = 86400`
is a thin margin.** A normal weekend costs two or three empties; a long
holiday closure could reach four and abort as
`history_exhausted_consecutive_empty` — a stop reason that reads like a
history boundary but would be a calendar artifact. **Recorded as a risk. The
retry policy is not changed without separate justification and review.**

---

## §16. TO APPROVE THIS AGREEMENT

1. **§8.10 is ruled** (permissive reading), and the confirmation this step
   required is **satisfied**: the v7 G0 review confirmed that §8.5, §8.9 and
   §8.10 implement that ruling without further contradiction, and that no
   clause phrases a third-case admission as a guaranteed boundary.
2. **Performed at the v7 G0 review** — §§5–10 clause by clause, all accepted
   on their merits. v8's only change is the C9 wording reconciliation and its
   two swept siblings, so this step stands unless that change is rejected.
3. Settle the G0a architecture requirements in full — §7.6's isolation
   default with its four gate tests and two declared channels; §7.6's
   write-set audit **scope**; **§14.14's audit mechanism and its fidelity**,
   as a decision distinct from the scope; §7.6's core-dump mitigation;
   §6.4's universal C6 coverage with independent count reconciliation; and
   §14.13's evidence standard for a re-derived convention.
   **The next review's question is whether these are actually testable on the
   target Windows environment — not which provider to choose.**
4. Only then is there an agreement, and only then does G1 begin.

**Nothing is authorised by this document.**
