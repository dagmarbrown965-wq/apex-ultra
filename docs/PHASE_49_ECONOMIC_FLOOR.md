# Phase 49 — the economic floor

**Analysis of 2026-11-17.** Establishes what an edge must be *worth* before any
hypothesis is named, so that Section E's pass bar is set against economics
rather than against statistical detectability alone.

**No sealed data was used.** Every figure below is arithmetic over published
summary values, standard statistical formulae, or Monte Carlo simulation.
Neither D1 nor D2 was opened. Nothing here breaches the Section E quarantine.

**Several inputs are placeholders**, marked as such. They are replaced with
real account figures before Section E is ratified.

---

## 1. Break-even win rate

Cost per round trip, expressed in R (units of the stop), is `spread / stop`.
At 1:1 reward:risk, break-even win rate is `(1 + cost) / 2`.

| Venue | Cost assumption | Cost in R | Break-even |
|---|---|---|---|
| Deriv retail CFD *(placeholder)* | 3 pip spread, 25 pip stop | 0.120 | **56.0%** |
| MT5 raw spread *(placeholder)* | 1.5 pip all-in, 25 pip stop | 0.060 | **53.0%** |
| MT5 raw, tight stop | 1.5 pip all-in, 10 pip stop | 0.150 | 57.5% |
| MT5 raw, wide stop | 1.5 pip all-in, 40 pip stop | 0.038 | 51.9% |

Binary options, where break-even is `1 / (1 + payout)`:

| Payout | Break-even win rate |
|---|---|
| 95% | 51.3% |
| 90% | 52.6% |
| 85% | 54.1% |
| 80% | 55.6% |

**MT5 raw-spread execution is materially cheaper than Deriv retail pricing**,
and the difference — roughly three percentage points of required win rate — is
larger than most strategies' entire edge.

## 2. D2 cannot confirm a modest edge

**This is the most consequential finding here and it needs no venue data.**

At Phase 47's observed density (106 trades over ~91 days), D2's 88.708 forward
days yield approximately **103 trades**.

| | |
|---|---|
| Standard error of win rate at n = 103 | **4.9 pp** |
| 95% confidence interval | **± 9.6 pp** |

A strategy that truly wins 57.5% will, 95% of the time, show an observed rate
between **47.9% and 67.1%**. That interval contains 50%. **It cannot be
distinguished from a coin.**

Trades required to establish an edge at 80% power, 5% two-sided:

| True win rate | Edge | Trades needed |
|---|---|---|
| 52.0% | 2.0 pp | 4,892 |
| 55.0% | 5.0 pp | 776 |
| 57.5% | 7.5 pp | **341** |
| 60.0% | 10.0 pp | 188 |
| 65.0% | 15.0 pp | 79 |

**D2 holds roughly a third of what is needed to confirm a 57.5% edge.** It can
only establish something winning about 65% or better — a rate that should
itself be treated as evidence of a bug on 15-minute FX.

### What D2 is actually for

**Rejection, not confirmation.** Phase 47 is the proof: a strategy showing
+37.66R at PF 1.15 in-sample, correctly killed by 106 holdout trades, because
badly overfit results collapse obviously and do not need a large sample to
expose.

A small holdout is an excellent detector of self-deception and a weak validator
of a real but modest edge. **Phase 50 must be built on that understanding.**
Surviving D2 means "not obviously fake", not "established".

## 3. Income arithmetic

Monthly return = `trades × risk_per_trade × (2p − 1 − cost)`.
At Phase 47 density: **~35 trades per month**.

| True win rate | Edge/trade | Monthly @1% risk | Capital for £1,000/mo |
|---|---|---|---|
| 55.0% | −0.020R | −0.71% | never |
| 56.0% | 0.000R | 0.00% | break-even |
| 57.5% | +0.030R | **1.06%** | **£94,000** |
| 60.0% | +0.080R | 2.83% | £35,300 |
| 65.0% | +0.180R | 6.37% | £15,700 |

*(Deriv-cost placeholder, 0.12R. MT5 costs improve each row.)*

**At 35 trades a month a good strategy returns about 1% monthly.** Unfunded,
that requires substantial capital to produce meaningful income.

## 4. Frequency — what it does and does not fix

Raising trade frequency:

- **Fixes income per unit time.** The same edge at 350 trades/month returns
  ~10× what it does at 35.
- **Fixes verifiability.** ~1,000 trades in D2 instead of ~103 resolves a 55%
  edge rather than only a 65% one.
- **Does NOT raise the probability of passing an evaluation.** Simulation
  confirms this: the equity path is the same random walk, only faster. Frequency
  buys time and information, not odds.

**The constraint:** more frequent trading means shorter stops, and cost is a
fraction of the stop. A 1.5 pip cost against a 25 pip stop is 0.06R; against a
5 pip stop it is 0.30R, putting break-even at 65% and out of reach.

**The hunt is therefore bounded on both sides:** frequent enough to earn and to
verify, with stops wide enough that spread does not consume the edge. This is a
much more specific target than "a pattern that predicts price", and it is why
Section C element 7 — expected trade density declared in advance — matters more
than it first appeared.

## 5. Funded-account evaluation

Monte Carlo, 8% profit target against 10% maximum drawdown, cost 0.06R, 1:1
reward:risk, fixed fractional sizing, 40,000–60,000 paths.

**Daily drawdown limits are NOT modelled.** Most evaluations impose ~5% daily,
which lowers every figure below. Real firm rules must replace these.

| True win rate | P(pass) @0.5% risk | P(pass) @1.0% risk |
|---|---|---|
| 50.0% — **no edge** | **11.3%** | 25.0% |
| 52.0% — losing | 31.3% | 38.7% |
| 53.0% — break-even | **45.5%** | 45.5% |
| 55.0% | 73.6% | 61.8% |
| 57.5% | **93.4%** | 78.2% |
| 60.0% | 98.9% | 89.4% |

### Two findings

**Passing an evaluation is weak evidence of an edge.** A break-even strategy
passes 45.5% of the time. A losing one passes a third of the time. This is the
Phase 47 failure mode in another costume: a result that looks like success and
is not. It is also, not coincidentally, the prop-firm business model.

**Position size determines how much passing means.**

| Risk/trade | No edge passes | Real 57.5% edge passes | Evidence ratio |
|---|---|---|---|
| 0.5% | 11.3% | 93.4% | **8.3×** |
| 1.0% | 25.0% | 78.2% | 3.1× |

**Trading smaller does not merely reduce risk — it converts the evaluation into
an actual test.** At 0.5% per trade a real edge nearly always passes and a fake
one nearly never does; at 1% the two blur. The common instinct to size up and
pass faster destroys the information value of passing.

Median time to pass at 35 trades/month, 0.5% risk: ~3.7 months at 57.5%, ~2.7
months at 60%. Check this against the firm's time limit.

## 6. What this implies for Section E

1. **The pass bar is economic, not statistical.** "Worth risking capital on",
   with costs in the model — not "distinguishable from zero".
2. **Trade density must clear an economic floor**, not merely the n ≥ 50
   evaluable tier. Fifty trades can measure an edge; fifty trades per quarter
   cannot pay anyone.
3. **A strategy that is real but trivial must fail.** Written before any
   hypothesis exists, so it cannot be argued away later when something squeaks
   over the line and nobody wants to kill it.
4. **D2's verdict is "not obviously fake", not "established".** Section E should
   say so, so that Phase 50's result is not over-read.
5. **A live evaluation at minimum position size is a second, independent test**,
   worth roughly 8:1 — and should be treated as part of the evidence chain
   rather than as a lap of honour.

## 7. The chain, and its weak link

hypothesis from reasoning → D1 for implementation → **D2 rejects overfit** →
low-risk evaluation gives ~8:1 → funded capital → income.

Each stage is cheap relative to the next and kills bad candidates early. The
structure is sound.

**Every stage assumes a real edge exists at the start.** Three attempts have not
produced one. Nothing in this analysis makes a fourth more likely to succeed; it
makes testing it cheaper, faster, and more informative, and it says in advance
what success would have to look like.

## 8. Placeholders to replace before Section E is ratified

- Actual MT5 spread **and commission** on `frxGBPJPY` / GBPJPY.
- Actual prop-firm rules: profit target, **daily** drawdown, maximum drawdown,
  time limit, profit split, cost per attempt.
- Swap/overnight financing, if any hypothesis holds positions across sessions.
- Realistic slippage, which is absent from every figure above.
