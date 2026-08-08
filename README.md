# APEX ULTRA

A Python research pipeline for testing trading hypotheses against real
market data — built with reproducibility, data-quality validation, and
pre-registered evaluation criteria.

**Status:** research complete on five hypotheses. No validated trading
edge found. The pipeline, tooling, and methodology are the deliverable.

---

## What this project is

Most backtesting code answers "did this strategy make money on past
data?" That question is easy to answer and easy to answer wrongly. This
project was built to answer a harder one: **"would I know if my result
were spurious?"**

Everything here — the provenance gates, the frozen cost models, the
deterministic replay, the single-use holdouts — exists to make a false
positive detectable. In one phase it worked: a strategy returning +37.66R
over nine months of in-sample data reversed sign on a holdout that had
been sealed before testing began. Without that holdout it would have
looked like a success.

---

## Engineering highlights

### Silent API failure detection

Deriv's `ticks_history` endpoint, when asked for data beyond its 365-day
retention boundary, **returns current data while echoing the requested
timestamp back correctly**. There is no error, no flag, and no
indication in the response that substitution occurred.

A naive paging loop would accumulate thousands of duplicate current
candles and report success. The fetch tool verifies every returned batch
against the requested range and halts on mismatch:

```python
if isinstance(end_param, int) and batch_newest > end_param + GRANULARITY:
    stop_reason = "history_boundary_substitution"
    # batch discarded; boundary reached
```

This fired correctly on the production fetch at request 37, establishing
the retention boundary at exactly 365 days and preventing a silently
corrupted dataset.

**Related finding:** empty responses at weekends are normal for forex
(the market is closed) and must not be treated as exhaustion. The tool
distinguishes "no data because closed" from "no data because boundary"
from "no response frame" — three cases that look similar and mean
different things.

### Deterministic, hash-verified pipelines

Every processing stage records SHA-256 of its inputs and outputs.
Repeated runs over identical data produce byte-identical results,
verified as a gate rather than assumed:

```
run 1: trades_sha256 d9445e0db7aedcca6606c5c8d3286d2bedf25532...
run 2: trades_sha256 d9445e0db7aedcca6606c5c8d3286d2bedf25532...
DETERMINISM: PASS
```

This gives a reproducibility chain that survives future code changes —
any later run can be verified against a committed result.

### Data provenance validation

Before any strategy work on a new instrument, the data source is
validated against an independent reference. Deriv's `cryBTCUSD` was
checked against Binance BTCUSDT across 500 matched 15-minute bars:

| Measure | Result |
|---|---|
| Bar-to-bar return correlation | **0.9979** |
| Return stdev (Deriv / Binance) | 0.1654% / 0.1658% |
| Median level difference | −0.0425% (constant offset) |

Confirming the instrument reflects real market dynamics rather than a
synthetic construction was made a blocking gate — if it had failed, weeks
of downstream work would have been meaningless.

### Automated validation gates

- **Regression suite** — positive, negative (drift detection), and
  determinism tests, run before every commit.
- **Static import gate** — verifies no execution-capable code is
  reachable from the engine package, enforced by AST inspection with an
  explicit allowlist.
- **Structural integrity checks** — schema validation, strictly
  increasing timestamps, single-symbol/strategy per session, filename
  convention enforcement.

### Frozen execution boundary

Execution is architecturally impossible, not merely avoided:

- demo account only, verified at connection
- `LIVE_TRADING=true` refuses to run
- every order-placing method raises `ExecutionForbiddenError`
- the static import gate prevents execution code from being reachable

Across 14 days of live observation and all subsequent work,
`live_orders_sent: 0` in every session artifact.

---

## Architecture

```
engine/            frozen core - feed, strategy, regime, risk, assembly
  feed/            read-only market data contracts
  strategy/        Strategy interface + implementations
  risk/            descriptive bracket generation (no position sizing)
  validation/      regression and static import gates
infrastructure/    broker transport (read-only surfaces only)
tools/             research code - fetch, replay, resolve, evaluate
docs/              boundary agreements, phase closes, handovers
```

Research code lives in `tools/` and imports the engine's real strategy
classes verbatim — never reimplementing them, so the thing being tested
is the thing that would run. The engine itself stays frozen; promoting
research code into it would require its own phase and gates.

---

## Methodology

Each research phase locks a written agreement **before any data is
seen**, specifying:

- the hypothesis and its known weak point
- the cost model (frozen — may not be revised to make a result pass)
- falsification criteria and minimum sample size
- a chronological holdout, single-use
- an explicit list of forbidden responses to a negative result

Two principles emerged from the work:

> Pre-registration protects against changing the answers after seeing the
> data. Adversarial review protects against asking the wrong question,
> implementing it ambiguously, or reasoning incorrectly before seeing the
> data. Neither is sufficient alone.

> The test is not whether criticism is present; it is whether the
> protocol becomes stricter each time it is touched.

---

## Research findings

Five hypotheses tested, none producing a validated edge:

| Hypothesis | Instrument | Result |
|---|---|---|
| EMA crossover 9/21 | R_100 (synthetic) | Decisive negative — 31.78% win rate vs 34.5% break-even, CI entirely below |
| EMA crossover 9/21 | EUR/USD 15m | Indeterminate — 34.17% vs 35.0% break-even, CI straddles |
| Volatility compression breakout | BTC 15m | In-sample +0.1307R / PF 1.15; **holdout −0.2119R / PF 0.77** |
| Perpetual funding carry | BTC | Killed at ceiling check — ~3.1% gross annualised, negative after retail costs |
| Mean-reversion after large moves | BTC 15m | Not distinguishable from zero — mean +0.0107%, mean/se +0.97 |

The third is the most instructive: the strategy looked profitable across
288 in-sample trades and reversed on 106 holdout trades. The
pre-registered holdout is what caught it.

Two hypotheses were closed by arithmetic in minutes rather than by
building a full phase — a "ceiling check" pattern that substantially
increases how many ideas can be screened per unit of effort.

---

## Running it

```bash
# credentials via environment (never committed, never in arguments)
export DERIV_API_TOKEN=...
export DERIV_APP_ID=...

python -m engine.validation.test_m0_regression   # regression gate
python -m engine.validation.check_cp3_imports    # static import gate

python -m tools.fetch_candles --symbol cryBTCUSD --days 400
python -m tools.backtest_compression_breakout
python -m tools.evaluate_phase47
```

Python 3.12+. Standard library only for the research tools; no numpy or
pandas dependency.

---

## What this project does not claim

- No validated trading edge was found.
- No capital has ever been at risk. Every result is offline analysis.
- Backtested results are not evidence of live profitability, and the
  phase documents state their own limitations explicitly — unmodelled
  slippage, spread widening during volatility, and execution-model
  biases in both directions.

---

## License

MIT
