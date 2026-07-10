"""
APEX ULTRA — Demo Session Manager (Phase 36)

Owns the state of a single controlled demo session and the running account
statistics. Pure bookkeeping over closed trades — it consumes trade outcomes,
it does not generate signals or place orders.

Tracks: session start/end, broker, account balance, equity, trade count,
winning/losing trades, drawdown, profit factor.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionStats:
    trade_count: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    net_pnl: float
    balance: float
    equity: float
    peak_equity: float
    max_drawdown_pct: float
    avg_win_r: float
    avg_loss_r: float
    avg_rr: float


class DemoSession:
    def __init__(self, broker_name: str, starting_balance: float = 100_000.0) -> None:
        self.broker_name = broker_name
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.equity = starting_balance

        self.session_start: float = time.time()
        self.session_end: Optional[float] = None
        # simulated clock for burn-in duration accounting
        self.sim_start_ts: float = self.session_start
        self.sim_now_ts: float = self.session_start

        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0          # stored as positive magnitude

        self._peak_equity = starting_balance
        self._max_dd_pct = 0.0
        self._win_r: list[float] = []
        self._loss_r: list[float] = []

    # ------------------------------------------------------------------ #
    def record_trade(self, pnl: float, r_multiple: float,
                     sim_ts: Optional[float] = None) -> None:
        self.trade_count += 1
        self.balance += pnl
        self.equity = self.balance
        if sim_ts is not None:
            self.sim_now_ts = sim_ts

        if pnl >= 0:
            self.winning_trades += 1
            self.gross_profit += pnl
            self._win_r.append(abs(r_multiple))
        else:
            self.losing_trades += 1
            self.gross_loss += abs(pnl)
            self._loss_r.append(abs(r_multiple))

        # drawdown tracking on realized equity curve
        if self.equity > self._peak_equity:
            self._peak_equity = self.equity
        dd = (self._peak_equity - self.equity) / self._peak_equity * 100.0
        self._max_dd_pct = max(self._max_dd_pct, dd)

    def close(self) -> None:
        self.session_end = time.time()

    # ------------------------------------------------------------------ #
    @property
    def current_drawdown_pct(self) -> float:
        if self._peak_equity <= 0:
            return 0.0
        return (self._peak_equity - self.equity) / self._peak_equity * 100.0

    @property
    def duration_days(self) -> float:
        return (self.sim_now_ts - self.sim_start_ts) / 86400.0

    @property
    def win_rate(self) -> float:
        return self.winning_trades / self.trade_count if self.trade_count else 0.0

    @property
    def profit_factor(self) -> float:
        if self.gross_loss == 0:
            return float("inf") if self.gross_profit > 0 else 0.0
        return self.gross_profit / self.gross_loss

    def stats(self) -> SessionStats:
        avg_win_r = sum(self._win_r) / len(self._win_r) if self._win_r else 0.0
        avg_loss_r = sum(self._loss_r) / len(self._loss_r) if self._loss_r else 0.0
        avg_rr = (avg_win_r / avg_loss_r) if avg_loss_r else 0.0
        return SessionStats(
            trade_count=self.trade_count,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            win_rate=self.win_rate,
            gross_profit=self.gross_profit,
            gross_loss=self.gross_loss,
            profit_factor=self.profit_factor,
            net_pnl=self.balance - self.starting_balance,
            balance=self.balance,
            equity=self.equity,
            peak_equity=self._peak_equity,
            max_drawdown_pct=self._max_dd_pct,
            avg_win_r=avg_win_r,
            avg_loss_r=avg_loss_r,
            avg_rr=avg_rr,
        )
