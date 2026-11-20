# Prop firm requirement specification

**2026-11-17.** Written *before* shopping, so a firm is judged against criteria
rather than against its own marketing.

**Purpose: feasibility, not apparatus.** This is a form to fill in per firm, not
a project. If it grows past one page of actual answers it has failed its job.

**Why it exists:** `docs/PHASE_49_BOUNDARY_AGREEMENT.md` §E.5 fixes the
confirming test's conditions in advance, and those conditions are the firm's
rules. The firm is therefore a **design input to the pass criteria**, not a
procurement decision taken afterwards.

---

## The five questions that decide go / no-go

Everything else is secondary. If these five don't clear, stop.

| # | Question | Disqualifying answer |
|---|---|---|
| 1 | **Automation permitted at all three levels — see 1a.** Confirmed in writing by support, not inferred from a rules page. | No, or unclear, at any one of the three |
| 2 | **Is the maximum drawdown static or trailing?** | Trailing is not disqualifying but is materially harder — see note below |
| 3 | **What is the daily loss limit, and what is it calculated from?** Starting balance, previous close, or equity high | A limit tight enough that normal variance at 0.5% risk breaches it |
| 4 | **Profit split, and cost per attempt** | — |
| 5 | **Is there a verifiable payout record?** | No evidence of payouts to real traders |

**Question 1 is the hard disqualifier.** Equity Edge — the firm currently held
— **fails it, confirmed by support in writing on 2026-11-18**: *"Using an EA is
strictly prohibited."* Their published rules say the same, and support further
confirmed that *"The prohibited strategies rules apply to all account types"*,
so funded and Qualified Trader accounts are covered by the prohibition.
**Equity Edge is disqualified for an EA-based strategy.**

Whether a program used **only to generate signals**, with every trade reviewed
and placed manually, counts as EA use was asked directly and **answered on
2026-11-19**: *"Please be advised that the use of EAs is not permitted, even if
the trades are executed manually."* The manual-execution fallback is therefore
**not permitted**, and the enquiry is closed. An earlier draft of this document
asserted that
manual execution remained permitted there; that assertion was never verified
and has been withdrawn.

### 1a — Automation has three levels, and a firm can pass one while failing another

| Level | What to confirm in writing |
|---|---|
| **Tool** | Are Expert Advisors permitted? Are **custom-built** EAs permitted? |
| **Behaviour** | Are automated entries and exits permitted? Restrictions on trade frequency, holding time or strategy type? Any **minimum average trade duration**? |
| **Payout** | Can profits generated **by that specific behaviour** qualify for withdrawal? |

**Permission to use the tool is not permission for what the tool does.** Equity
Edge's prohibited-practice list — high-frequency trading, tick scalping,
latency arbitrage, toxic flow — would bite a strategy at the frequency the
economics keep pointing toward, even at a firm that welcomes automation. The
written confirmation must name the prohibited practices, any minimum trade
duration, frequency limits and payout eligibility explicitly.

**A firm that permits EAs but reserves the right to void payouts for particular
EA behaviour is not a suitable counterparty.**

**On trailing drawdown:** a floor that follows the equity high-water mark means
early profit raises the level you can be stopped out at. The simulations in
`docs/PHASE_49_ECONOMIC_FLOOR.md` assumed **static**, which is the generous
case. Any firm offering trailing requires those pass-probability figures to be
recomputed before E.5's position size is fixed.

---

## A — Rules compatibility

**The answers below are Equity Edge's, recorded 2026-11-18.** For any other
firm, copy this file and clear the answer column; do not overwrite these.

| Item | Answer | Notes |
|---|---|---|
| **1. Tool** — EA / automated execution permitted | **NO.** *"Using an EA is strictly prohibited"* (2026-11-18), and *"the use of EAs is not permitted, even if the trades are executed manually"* (2026-11-19). **Both automated execution and EA-generated signals followed by manual execution are prohibited.** | **In writing. Keep the email.** |
| **2. Behaviour** — proposed strategy's behaviours permitted | **Declined** — no advance review available | Describe frequency, holding time, entries and exits. See the HFT and tick-scalping rows below, which feed this answer |
| **3. Payout** — profits from this EA-generated strategy payout-eligible | **Declined** — reviews occur only after a challenge is passed or a payout requested | **Explicit** written confirmation, not inferred from 1 or 2 |
| Applicable rule clauses named by support | **None.** No clause was cited for any answer | **Ask support to cite the clauses.** A representative's reassurance does not override contradictory contractual terms |
| Drawdown type | not reached | Static / trailing |
| Maximum drawdown % | not reached | |
| Daily loss limit % | not reached | |
| Daily limit basis | not reached | Starting balance / previous close / equity high |
| Daily limit reset time | not reached | |
| Phase 1 profit target % | not reached | |
| Phase 2 profit target %, if any | not reached | |
| Minimum trading days | not reached | |
| Time limit on evaluation | not reached | Unlimited is a genuine advantage |
| High-frequency trading restrictions | prohibited, Trading Rules §3 | Relevant if a candidate needs density |
| Tick scalping / minimum trade duration | prohibited; **2-minute average** trade duration rule applies to all phases of Swift, Legacy and Instant; Flagship evaluation exempt | |
| News trading windows | 2 min either side (Legacy/Swift funded), 5 min (Flagship funded), 8 min (Instant); profits deducted | Width, and whether profits are clawed back |
| Hedging permitted | **No** — *"payout rejection and may also results in account termination"* | |
| Consistency rule | not reached | e.g. best day capped at X% of total profit |
| Copy trading rules | max two Challenge accounts; prohibited on Instant | |
| Weekend / overnight holding permitted | gap-trading restriction applies in the final two hours before close | Relevant if a candidate holds positions |

Rows marked *not reached* were never asked: Question 1 disqualified the firm
before the economic terms mattered. They are not unanswered, they are moot.

### Verification record — Equity Edge

| | |
|---|---|
| Enquiry sent | 2026-11-17, `support@equityedge.io`, four numbered questions |
| Reply received | 2026-11-18 05:41 UTC, Hillary, Customer Support Representative |
| Confirmed, verbatim | *"Using an EA is strictly prohibited."* |
| Confirmed, verbatim | *"The prohibited strategies rules apply to all account types."* |
| Confirmed, verbatim, 2026-11-19 | *"Please be advised that the use of EAs is not permitted, even if the trades are executed manually."* |
| Declined | Advance review of any strategy, trade or account — see Section B |
| Not answered | Q2 payout eligibility for signal-only use; Q3 whether the stated profile engages any prohibited practice |
| Clauses cited | **None**, for any answer |
| Outstanding | **None — enquiry closed 2026-11-19** |

**One-firm reference point — NOT an industry standard.** From the Equity Edge
survey only: targets 8–10%, daily limits 3–5%, maximum drawdown 5–10%, splits
80–90%, 2–3 minimum trading days, evaluation time limits often unlimited.

This is a single firm's terms, surveyed once. It is useful for judging whether
another firm's offer is better or worse *than Equity Edge's*, and for nothing
more. It has not been checked against any sample of the sector and must not be
cited as what the industry typically offers.

## B — Counterparty risk

**A firm with perfect rules that does not pay is worse than one with tight rules
that does.**

| Item | Answer |
|---|---|
| Legal entity and jurisdiction | Equity Edge Ltd, Saint Lucia |
| Years operating under that entity | not established |
| Verifiable payout evidence — not testimonials | not established; marketing claims only |
| Who holds the money | not established |
| Is the execution broker regulated, and where | not established |
| What happens to funded accounts if the firm fails | not established |
| Any regulatory action against the firm or its principals | not established |
| **Advance clearance available before an attempt** | **No.** Support, 2026-11-18: *"we are unable to review trades or accounts directly. Reviews are conducted exclusively by the Trade Review Team after a challenge has been passed or a payout request has been submitted."* |

**The advance-clearance finding is a counterparty finding, not a rules
finding.** Compliance judgement is applied only after the fee is paid, the work
is done and the money is requested. No strategy question can be settled before
committing. Combined with Terms §6 — payouts *"may be declined in cases of
suspected rule breaches, location discrepancies, or strategy manipulation"* —
and §10's *"Decisions are final"*, the trader carries the whole interpretive
risk. **Ask every future firm whether advance clearance exists; treat its
absence as a material defect, not an administrative detail.**

This section exists because the prop sector has a documented history of firms
closing or being restricted by regulators, sometimes with traders' balances
unpaid. A strategy that works is worth nothing against a counterparty that
doesn't.

## C — Economic terms

| Item | Answer |
|---|---|
| Profit split % | not reached |
| Cost per attempt | not reached |
| Is the fee refunded on passing | not reached |
| Account sizes offered | not reached |
| Payout frequency and minimum | not reached |
| Scaling terms | not reached |
| Maximum allocation | not reached |

Feeds the economic floor: `docs/PHASE_49_ECONOMIC_FLOOR.md` values a funded
account at roughly 12 months of split profit, which is the figure that decides
whether an attempt is rational.

---

## Decision rule

**Hard disqualifiers — any one ends consideration:**

1. EAs not permitted, or the firm will not answer the question in writing.
2. No verifiable evidence of payouts.
3. A prohibited-practice list that forbids the frequency a candidate requires.

**Preference order among firms that clear those:**

1. Static drawdown over trailing.
2. Wider gap between profit target and maximum drawdown.
3. No time limit on the evaluation.
4. Higher split, then lower cost per attempt — **in that order**, because the
   split compounds across every payout while the attempt fee is paid once.

**Record the chosen firm's actual numbers into the Phase 50 pre-registration
before any attempt**, per E.5. Rules discovered after a strategy is frozen
cannot be used to adjust it.

**Equity Edge fails disqualifier 1 on both limbs** — EAs are not permitted, and
the firm declined to answer the behaviour and payout questions in writing.
Consideration ends there.

---

## What this spec is not

It is not a recommendation of any firm. It is not an endorsement of prop
funding as a route. It fixes what must be true for the funded evaluation
described in E.5 to be a valid confirming test — and if no accessible firm
clears the hard disqualifiers, that is a finding about the route, not about the
strategy.
