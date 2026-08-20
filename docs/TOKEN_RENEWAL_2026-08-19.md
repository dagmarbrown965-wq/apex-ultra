# Token renewal — 2026-08-19

## Active token (single)

| Field | Value |
|---|---|
| Name | apex_trade_demo_5 |
| Scope | Trade only |
| Created | 2026-08-19 |
| Expires | 2026-11-17 |
| Key suffix | 5452 |

Supersedes `apex_trade_demo_4` (created 2026-07-22, expiry 2026-10-20),
deleted 2026-08-19 after the successor was verified. One active token.

## Correction to the record

Every Phase 48 document named the active token `apex_trade_demo_2` expiring
~2026-10-08. Both wrong. The dashboard on 2026-08-19 showed a single active
token `apex_trade_demo_4`, created 2026-07-22, expiring 2026-10-20 — a
renewal performed after the 42.1 handoff and never written down. Names _3
and _4 were both already spent.

The deadline conclusion survived the correction: 2026-10-20 still preceded
the ~2026-10-30 D2 fetch, so renewal was required regardless.

Affected: APEX_STATE_2026-08-16.md item 5, PHASE_48_BOUNDARY_AGREEMENT.md
Section G.1 and W48.3, PHASE_48_W48_0A_CLOSE.md next-action 3.

The 75-day D2 interval needs no revision: its justification reasoned about a
hypothetical renewal on the lock date, not about the token then active.

## Margin

2026-11-17 clears the ~2026-10-30 D2 fetch by 18 days. If D2 slips beyond
mid-November a further renewal is required. Failure mode remains silence.

## Verification performed 2026-08-19 (HEAD 77f58e6)

- M0 engine regression: PASS (3/3)
- CP3 static import gate: PASS, single allowlisted lazy import unchanged
- Live observation, R_100, ema_cross, 1 signal: live_orders_sent 0
- Deriv dashboard "Last used": demo_5 moved to 2026-08-19; demo_4 remained
  2026-08-16. Confirms the new token was on the wire and the old one was not.

Not verified this session: the demo-account selection guard (DOT..79 over
ROT..99) is not printed on the live-observation banner. Unchanged in code;
not re-observed.

Scope unchanged. Deriv offers no read-only scope — the creation form lists
only Trade, Account management, Application insights, Payments. Trade-by-
necessity holds; no guard was altered to accommodate this renewal.

## Incidental findings

- session_summary_live_signals_2026-07-22_session002.json (617 B) exists with
  no journal on disk or in git. APEX_STATE accounts for seven rejected
  sessions; this is an eighth artifact it does not mention. Undetermined
  whether the journal was deleted or never written.
- HEAD 77f58e6 removed the 253-byte live_signals.jsonl CP4 stub. The Phase 48
  documents still list it as outstanding.
- live_signals_2026-08-19_session001.jsonl and its summary are artifacts of
  this token probe. Not Phase 44 window evidence, not Phase 48 evidence.
  Left untracked deliberately.
