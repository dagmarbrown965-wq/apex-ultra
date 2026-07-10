# APEX ULTRA — Phase 40 Deriv Demo Shadow Burn-In

Runs APEX ULTRA against a **real Deriv demo account in shadow mode**: observe
the market, consume the existing signals, record what *would* have happened —
**without ever sending an order.**

## Command

```bash
python -m testing.shadow.shadow_burn_in --real      # real Deriv demo shadow run
python -m testing.shadow.shadow_burn_in --dry-run   # offline flow check (synthetic)
```

A real run requires, in code, a live signal source wired in:

```python
from testing.shadow import shadow_burn_in
shadow_burn_in.run(["--real"], signal_source=<your live APEX signal stream>)
```

The shadow layer **consumes** signals from the existing strategy + risk
pipeline. It does not generate signals or compute risk. The dry-run uses a
clearly-labelled synthetic replay fixture that is never a substitute for real
signals.

## Precondition (hard)

Before a real burn-in starts, the preflight must pass:

```bash
python -m testing.preflight.apex_demo_ready --real   # must print READY
```

If the preflight is not READY, the burn-in **does not start** — it prints the
blockers and exits with `STATUS: FAIL (precondition not met)`.

## No live orders — by construction

The controller only ever holds a `ShadowBrokerView`, a read-only facade. The
order methods (`submitOrder`, `submit_intent`, `closePosition`, `buy`, `sell`)
do not exist on it; any attempt to reach them raises `ShadowViolation`. The
report's `Live orders sent: 0` is a structural invariant, not a flag.

## Duration

Minimum **14 calendar days AND 500 shadow opportunities** — both must be met
(whichever comes later). Until then the status is `EXTEND`.

## What every shadow event records

timestamp, symbol, strategy, signal direction, signal score, regime, expected
entry, market price, spread, latency, risk size, would-be order size, would-be
stop loss, would-be take profit, and the acceptance/rejection reason.

## Status

| Status   | Meaning |
|----------|---------|
| `PASS`   | Both minimums met, safety clean (0 live orders, connections recovered). |
| `EXTEND` | Minimums not yet met — keep the shadow burn-in running. |
| `FAIL`   | Precondition not met, a live order somehow occurred, or a safety violation. |

No live trading capability exists in this phase. `LIVE_TRADING=true` fails the
preflight and therefore the burn-in.

## Outcome resolution

Win/loss for each accepted shadow opportunity is resolved from **subsequent
market data** in a real run (did the would-be TP or SL come first). The dry-run
fixture supplies synthetic outcomes purely to exercise the metrics.
```
```
