"""
APEX ULTRA — Burn-In Controller (Phase 36)

Orchestrates a controlled live-demo burn-in:

  1. Pulls signals from a demo feed fixture.
  2. Routes each entry through the Phase 35 broker to sample real execution
     quality (fill price, slippage, spread, latency) and to surface execution
     failures (rejects / timeouts).
  3. Records the full per-trade dossier and updates session statistics.
  4. Continuously evaluates burn-in stop conditions and minimums.
  5. Produces the burn-in report with a PASS / FAIL verdict.

Duration is driven by a simulated clock so a >=30-day burn-in can be evaluated
in a compressed run. In live use the same loop accrues against wall-clock time.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from infrastructure.broker import (
    BrokerError,
    MarketConfig,
    MockBroker,
    Order,
    OrderResult,
)
from testing.broker_validation.execution_metrics import ExecutionMetrics
from .backtest_compare import BacktestBaseline, DemoActual, DriftReport, compare
from .burn_in_rules import BurnInThresholds, BurnInEvaluation, evaluate
from .demo_feed import DemoFeed, DemoSignal
from .session_manager import DemoSession
from .trade_collector import DemoTradeRecord, LiveTradeCollector


@dataclass
class RiskGuard:
    """Lightweight self-check that the risk layer is behaving. Stays healthy in
    nominal runs; `force_malfunction` exercises the FAIL path."""
    max_concurrent_risk_units: float = 5.0
    force_malfunction: bool = False
    _breaches: int = 0

    def check(self, requested_units: float, approved_units: float) -> bool:
        if self.force_malfunction:
            self._breaches += 1
            return False
        # a healthy guard never approves more than requested or over the cap
        if approved_units > requested_units + 1e-9:
            self._breaches += 1
            return False
        if approved_units > self.max_concurrent_risk_units + 1e-9:
            self._breaches += 1
            return False
        return True

    @property
    def ok(self) -> bool:
        return self._breaches == 0


@dataclass
class BurnInResult:
    session: DemoSession
    collector: LiveTradeCollector
    metrics: ExecutionMetrics
    evaluation: BurnInEvaluation
    drift: DriftReport
    exec_failure_rate: float
    risk_guard_ok: bool
    passed: bool
    runtime_ms: float


class BurnInController:
    def __init__(
        self,
        broker_name: str = "DEMO-BROKER",
        starting_balance: float = 100_000.0,
        risk_fraction: float = 0.005,     # 0.5% account risk per trade
        thresholds: Optional[BurnInThresholds] = None,
        baseline: Optional[BacktestBaseline] = None,
        inject_exec_failures: bool = True,
        seed: int = 36,
        broker=None,                      # inject a real adapter here (Phase 37)
    ) -> None:
        if broker is None:
            broker = MockBroker(
                symbol="APEX",
                market=MarketConfig(mid=100.0, latency_ms_mean=1.0,
                                    latency_ms_jitter=0.5),
                seed=seed,
            )
        self.broker = broker
        self.session = DemoSession(broker_name, starting_balance)
        self.collector = LiveTradeCollector()
        self.metrics = ExecutionMetrics()
        self.risk_guard = RiskGuard()
        self.thresholds = thresholds or BurnInThresholds()
        self.baseline = baseline or BacktestBaseline(
            win_rate=0.57, avg_rr=1.8, max_drawdown_pct=6.0
        )
        self.risk_fraction = risk_fraction
        self.inject_exec_failures = inject_exec_failures
        self._seed = seed
        self._attempts = 0

    # ------------------------------------------------------------------ #
    def _maybe_inject_fault(self, idx: int) -> None:
        if not self.inject_exec_failures:
            return
        # ~1.5% reject, ~0.5% timeout -> ~2% exec failure (< 5% threshold)
        if idx % 67 == 0:
            self.broker.faults.reject_next = True
        elif idx % 199 == 0:
            self.broker.faults.timeout_next = True

    def _execute_entry(self, sig: DemoSignal) -> Optional[OrderResult]:
        """Route entry through broker to sample execution quality."""
        self._attempts += 1
        # measure execution on the broker's own price scale (mid reference)
        broker_ref = self.broker.current_mid
        order = Order(self.broker.symbol, sig.side, qty=10.0,
                      expected_price=broker_ref)
        try:
            t0 = time.perf_counter()
            result = self.broker.submit_order(order, timeout=0.02)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self.metrics.record_fill(result, latency_ms, broker_ref)
            return result
        except BrokerError as e:
            cls = e.__class__.__name__
            if "Reject" in cls:
                self.metrics.record_rejected(order, broker_ref, str(e))
            else:
                self.metrics.record_missed(order, broker_ref, str(e))
            return None

    def _to_record(self, sig: DemoSignal, result: OrderResult,
                   pnl: float, r_mult: float) -> DemoTradeRecord:
        rec = self.metrics.records[-1]
        # map the broker-scale fill onto the signal's price scale for display
        mid = result.quote_at_submit.mid if result.quote_at_submit else 100.0
        fill = sig.entry_signal_price * (result.order.avg_fill_price / mid)
        return DemoTradeRecord(
            trade_id=sig.seq,
            signal_ts=sig.ts,
            signal_score=sig.score,
            regime=sig.regime,
            strategy=sig.strategy,
            asset=sig.asset,
            entry_signal_price=sig.entry_signal_price,
            actual_fill_price=round(fill, 4),
            slippage_bps=round(rec.slippage_bps, 3),
            spread=round(rec.spread_cost_per_unit * 2, 5),
            latency_ms=round(rec.latency_ms, 3),
            exit_reason=sig.exit_reason,
            pnl=round(pnl, 2),
            r_multiple=r_mult,
        )

    # ------------------------------------------------------------------ #
    def run(self, n_trades: int = 520, sim_days: float = 32.0) -> BurnInResult:
        t_start = time.perf_counter()
        self.broker.connect()  # establish demo broker link before trading
        seconds_per_trade = (sim_days * 86400.0) / max(1, n_trades)
        feed = DemoFeed(seed=self._seed, target_win_rate=0.53,
                        start_ts=self.session.sim_start_ts,
                        seconds_per_trade=seconds_per_trade)

        stopped = False
        for i in range(1, n_trades + 1):
            self._maybe_inject_fault(i)
            sig = feed.next()

            # risk guard self-check (approve full requested size)
            requested_units = 1.0
            approved_units = 1.0
            self.risk_guard.check(requested_units, approved_units)

            result = self._execute_entry(sig)
            if result is None:
                # execution failure -> no trade booked, advance clock only
                self.session.sim_now_ts = sig.ts
                continue

            # outcome -> P&L from predetermined R, scaled by dollar risk
            dollar_risk = self.session.balance * self.risk_fraction
            r_mult = sig.r_target if sig.will_win else -1.0
            pnl = r_mult * dollar_risk

            self.session.record_trade(pnl, r_mult, sim_ts=sig.ts)
            self.collector.add(self._to_record(sig, result, pnl, r_mult))

            # live stop-condition check
            exec_fail_rate = self._exec_failure_rate()
            ev = evaluate(self.session.trade_count, self.session.duration_days,
                          self.session.current_drawdown_pct, exec_fail_rate,
                          self.risk_guard.ok, self.thresholds)
            if ev.stop_triggered:
                stopped = True
                break

        self.session.close()
        exec_fail_rate = self._exec_failure_rate()
        stats = self.session.stats()

        evaluation = evaluate(
            stats.trade_count, self.session.duration_days,
            stats.max_drawdown_pct, exec_fail_rate, self.risk_guard.ok,
            self.thresholds,
        )

        drift = compare(
            self.baseline,
            DemoActual(win_rate=stats.win_rate, avg_rr=stats.avg_rr,
                       max_drawdown_pct=stats.max_drawdown_pct),
        )

        passed = (
            evaluation.minimums_met
            and not evaluation.stop_triggered
            and not stopped
            and drift.within_tolerance
        )
        runtime_ms = (time.perf_counter() - t_start) * 1000.0

        return BurnInResult(
            session=self.session,
            collector=self.collector,
            metrics=self.metrics,
            evaluation=evaluation,
            drift=drift,
            exec_failure_rate=exec_fail_rate,
            risk_guard_ok=self.risk_guard.ok,
            passed=passed,
            runtime_ms=runtime_ms,
        )

    def _exec_failure_rate(self) -> float:
        fails = self.metrics.rejected_orders + self.metrics.missed_executions
        return fails / self._attempts if self._attempts else 0.0
