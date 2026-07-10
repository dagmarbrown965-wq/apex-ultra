# APEX ULTRA — Pre-Demo Preflight (Phase 39.4)

One command proves every safety gate is satisfied before any Deriv demo
execution is allowed. It is a **verification gate only** — it adds no trading
functionality and starts no strategy, signal, or order flow on its own.

## Command

```bash
python -m testing.preflight.apex_demo_ready            # auto: real if able, else dry-run
python -m testing.preflight.apex_demo_ready --dry-run  # simulated flow check
python -m testing.preflight.apex_demo_ready --real     # live Deriv gate
python -m testing.preflight.apex_demo_ready --verbose  # also print sub-phase returns
```

For a real run:

```bash
pip install websocket-client
export DERIV_APP_ID=<your app_id>
export DERIV_API_TOKEN=<your VIRTUAL/demo account token>
export DERIV_SYMBOL=R_100        # optional
# LIVE_TRADING must remain unset/false — see Hard Rules
```

## What it executes

| Phase | Checks |
|-------|--------|
| 35    | broker lifecycle tests, failure recovery tests |
| 36    | burn-in validation, risk-guard checks |
| 37    | adapter safety checks |
| 38    | Deriv adapter checks |
| 39    | smoke-test validation |
| 39.1  | execution mapping validation |
| 39.2  | contract verification |
| 39.3  | live contract gate |

## READY criteria (all ten must hold)

1. Deriv connection successful
2. Account is virtual/demo
3. `contracts_for` confirmed
4. Contract type confirmed
5. Execution mapping confirmed
6. SL/TP compatibility confirmed
7. Shadow mode enabled
8. No live trading capability
9. Broker lifecycle tests pass
10. Failure recovery tests pass

## Possible outcomes

| Status            | Meaning |
|-------------------|---------|
| `READY`           | All ten criteria hold **and** verification ran against a live Deriv virtual account. Demo execution may proceed. |
| `DRY-RUN PASSED`  | All offline-checkable gates pass, but verification used simulated data. **NOT demo ready.** |
| `BLOCKED`         | One or more gates failed (or a hard rule was violated). Exact blockers are listed. |

## Hard rules

- **DEMO ONLY.** If `LIVE_TRADING=true`, the preflight fails with `BLOCKED`
  regardless of every other result. This phase never permits live trading.
- **No simulated data may produce READY.** READY requires a real
  `DerivWebSocketTransport` connection to a virtual account. Simulation can only
  yield `DRY-RUN PASSED`.
- Real (non-virtual) account logins are refused, and a non-virtual `loginid`
  blocks readiness.

## Do not proceed to burn-in / demo execution until a `--real` run prints `READY`.
