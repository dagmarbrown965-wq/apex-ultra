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

**Question 1 is the hard disqualifier.** Equity Edge — the firm currently held —
**fails it**: its published rules state EA and trade-copier use *"is not
permitted and will lead to evaluation denial, payout denial, and account
closure."* That was read from their rules page by an agent, not confirmed by
their support, and should be put to them directly before the account is written
off. Manual execution of the bot's signals remains permitted there and at ~35
trades/month is feasible, so the account is not worthless.

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

| Item | Answer | Notes |
|---|---|---|
| EAs / automated trading permitted | | **In writing. Keep the email.** |
| Drawdown type | | Static / trailing |
| Maximum drawdown % | | |
| Daily loss limit % | | |
| Daily limit basis | | Starting balance / previous close / equity high |
| Daily limit reset time | | |
| Phase 1 profit target % | | |
| Phase 2 profit target %, if any | | |
| Minimum trading days | | |
| Time limit on evaluation | | Unlimited is a genuine advantage |
| High-frequency trading restrictions | | Relevant if a candidate needs density |
| Tick scalping / minimum trade duration | | |
| News trading windows | | Width, and whether profits are clawed back |
| Hedging permitted | | |
| Consistency rule | | e.g. best day capped at X% of total profit |
| Copy trading rules | | |
| Weekend / overnight holding permitted | | Relevant if a candidate holds positions |

**Industry baseline for judging answers**, from the Equity Edge survey: targets
8–10%, daily limits 3–5%, maximum drawdown 5–10%, splits 80–90%, 2–3 minimum
trading days, evaluation time limits often unlimited. Better or worse than that
is the useful comparison.

## B — Counterparty risk

**A firm with perfect rules that does not pay is worse than one with tight rules
that does.**

| Item | Answer |
|---|---|
| Legal entity and jurisdiction | |
| Years operating under that entity | |
| Verifiable payout evidence — not testimonials | |
| Who holds the money | |
| Is the execution broker regulated, and where | |
| What happens to funded accounts if the firm fails | |
| Any regulatory action against the firm or its principals | |

This section exists because the prop sector has a documented history of firms
closing or being restricted by regulators, sometimes with traders' balances
unpaid. A strategy that works is worth nothing against a counterparty that
doesn't.

## C — Economic terms

| Item | Answer |
|---|---|
| Profit split % | |
| Cost per attempt | |
| Is the fee refunded on passing | |
| Account sizes offered | |
| Payout frequency and minimum | |
| Scaling terms | |
| Maximum allocation | |

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

---

## What this spec is not

It is not a recommendation of any firm. It is not an endorsement of prop
funding as a route. It fixes what must be true for the funded evaluation
described in E.5 to be a valid confirming test — and if no accessible firm
clears the hard disqualifiers, that is a finding about the route, not about the
strategy.
