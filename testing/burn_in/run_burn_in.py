"""
APEX ULTRA — Burn-In Runner (Phase 36)

Entry point. Runs the burn-in and prints the required report block:

  SESSION / TRADES / WIN RATE / PROFIT FACTOR / MAX DD / SLIPPAGE /
  EXECUTION QUALITY / DRIFT / STATUS (PASS / FAIL)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from testing.broker_validation.demo_report import _execution_quality  # noqa: E402
from testing.burn_in.burn_in_controller import BurnInController  # noqa: E402


def _fmt_pf(pf: float) -> str:
    return "inf" if pf == float("inf") else f"{pf:.2f}"


def run(n_trades: int = 520, sim_days: float = 32.0, seed: int = 36) -> dict:
    controller = BurnInController(seed=seed)
    result = controller.run(n_trades=n_trades, sim_days=sim_days)

    s = result.session.stats()
    d = result.drift
    exec_quality = _execution_quality(result.metrics)
    ev = result.evaluation

    print("=" * 60)
    print("APEX ULTRA — PHASE 36 DEMO BURN-IN REPORT")
    print("=" * 60)
    print(f"SESSION:           {result.session.broker_name}  "
          f"({result.session.duration_days:.1f} simulated days)")
    print(f"                   balance "
          f"{result.session.starting_balance:,.0f} -> {s.balance:,.0f}  "
          f"(net {s.net_pnl:+,.0f})")
    print(f"TRADES:            {s.trade_count}  "
          f"(W:{s.winning_trades} / L:{s.losing_trades})  "
          f"attempts={controller._attempts}")
    print(f"WIN RATE:          {s.win_rate*100:.1f}%")
    print(f"PROFIT FACTOR:     {_fmt_pf(s.profit_factor)}")
    print(f"MAX DD:            {s.max_drawdown_pct:.2f}%")
    print(f"SLIPPAGE:          {result.collector.avg_slippage_bps:.3f} bps avg  "
          f"(spread avg {result.collector.avg_spread:.4f})")
    print(f"EXECUTION QUALITY: {exec_quality}/100   "
          f"latency {result.collector.avg_latency_ms:.2f}ms   "
          f"fail_rate {result.exec_failure_rate*100:.2f}%")
    print("-" * 60)
    print("BACKTEST vs DEMO:")
    print(f"  Win rate : backtest {d.backtest_wr:.0f}%  "
          f"demo {d.demo_wr:.0f}%  drift {d.wr_drift_pp:+.1f}pp")
    print(f"  Avg R:R  : backtest {d.backtest_rr:.2f}  "
          f"demo {d.demo_rr:.2f}  drift {d.rr_drift_pct:+.1f}%")
    print(f"  Max DD   : backtest {d.backtest_dd:.1f}%  "
          f"demo {d.demo_dd:.1f}%  drift {d.dd_drift_pp:+.1f}pp")
    print(f"DRIFT:             {d.overall_drift_pct:.2f}%  "
          f"(within tolerance: {d.within_tolerance})")
    print("-" * 60)
    print("BURN-IN GATES:")
    print(f"  >=500 trades     : {'OK' if ev.min_trades_met else 'NOT MET'} "
          f"({s.trade_count})")
    print(f"  >=30 days        : {'OK' if ev.min_duration_met else 'NOT MET'} "
          f"({result.session.duration_days:.1f}d)")
    print(f"  drawdown <=10%    : {'OK' if s.max_drawdown_pct <= 10 else 'BREACH'} "
          f"({s.max_drawdown_pct:.2f}%)")
    print(f"  exec failure <=5% : {'OK' if result.exec_failure_rate <= 0.05 else 'BREACH'} "
          f"({result.exec_failure_rate*100:.2f}%)")
    print(f"  risk guard        : {'OK' if result.risk_guard_ok else 'MALFUNCTION'}")
    if ev.stop_reasons:
        print(f"  STOP TRIGGERED   : {[r.value for r in ev.stop_reasons]}")
    print("-" * 60)
    print(f"STATUS:            {'PASS' if result.passed else 'FAIL'}")
    print("=" * 60)

    return {"result": result}


if __name__ == "__main__":
    run()
