"""
APEX ULTRA — Deriv Execution Mapping (Phase 39.1)

Maps an APEX order intent (side, size, stop-loss, take-profit, close) onto a
Deriv contract request, WITHOUT assuming a contract type. The contract type and
its proposal parameters live in DerivContractSpec and must be CONFIRMED against
Deriv's `contracts_for` for a symbol before the readiness gate can pass.

This module lives entirely under infrastructure/broker/deriv so the shared Order
model and risk/sizing layers are not touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..broker_interface import OrderSide


@dataclass
class ApexOrderIntent:
    """The engine-side order, expressed independently of any broker."""
    side: OrderSide
    size: float                       # APEX size (mapped to stake or units per spec.basis)
    symbol: str
    stop_loss: Optional[float] = None     # absolute amount (per Deriv limit_order)
    take_profit: Optional[float] = None   # absolute amount (per Deriv limit_order)
    comment: str = ""


@dataclass
class DerivContractSpec:
    """Candidate Deriv contract configuration. `confirmed` must be set true only
    after confirming the contract_type is available via contracts_for."""
    contract_type_buy: str = "MULTUP"        # CANDIDATE — must be confirmed
    contract_type_sell: str = "MULTDOWN"     # CANDIDATE — must be confirmed
    basis: str = "stake"                     # 'stake' or 'payout'
    multiplier: Optional[int] = 100          # for multiplier contracts
    duration: Optional[int] = None           # for option contracts
    duration_unit: Optional[str] = None      # 's','m','h','d','t'
    supports_limit_order: bool = True        # multipliers support SL/TP
    confirmed: bool = False
    candidate_note: str = ("candidate multiplier mapping — NOT confirmed; "
                           "verify against Deriv contracts_for")

    @property
    def is_multiplier(self) -> bool:
        return self.multiplier is not None and self.duration is None

    @property
    def is_option(self) -> bool:
        return self.duration is not None


def map_intent_to_proposal(intent: ApexOrderIntent, spec: DerivContractSpec,
                           currency: str) -> dict:
    """Build a Deriv `proposal` request from an APEX intent + contract spec."""
    contract_type = (spec.contract_type_buy if intent.side == OrderSide.BUY
                     else spec.contract_type_sell)
    req: dict = {
        "proposal": 1,
        "amount": intent.size,
        "basis": spec.basis,
        "contract_type": contract_type,
        "currency": currency,
        "symbol": intent.symbol,
    }
    if spec.multiplier is not None:
        req["multiplier"] = spec.multiplier
    if spec.duration is not None:
        req["duration"] = spec.duration
        req["duration_unit"] = spec.duration_unit or "m"

    limit_order: dict = {}
    if intent.stop_loss is not None:
        limit_order["stop_loss"] = intent.stop_loss
    if intent.take_profit is not None:
        limit_order["take_profit"] = intent.take_profit
    if limit_order:
        req["limit_order"] = limit_order
    return req


def validate_mapping(intent: ApexOrderIntent,
                     spec: DerivContractSpec) -> tuple[bool, list[str]]:
    """Structural validation of the APEX->Deriv mapping. Returns (ok, issues)."""
    issues: list[str] = []
    if intent.size <= 0:
        issues.append("size must be > 0")
    if not spec.contract_type_buy or not spec.contract_type_sell:
        issues.append("contract_type_buy/sell must be set")
    if spec.multiplier is None and spec.duration is None:
        issues.append("neither multiplier nor duration set — proposal cannot price")
    if (intent.stop_loss is not None or intent.take_profit is not None) \
            and not spec.supports_limit_order:
        issues.append("stop_loss/take_profit set but contract has no limit_order")
    if spec.is_option and (intent.stop_loss is not None
                           or intent.take_profit is not None):
        issues.append("option contracts do not support stop_loss/take_profit")
    return (len(issues) == 0, issues)


def describe_mapping(intent: ApexOrderIntent, spec: DerivContractSpec,
                     currency: str) -> list[tuple[str, str, str]]:
    """Human-readable mapping table: (APEX field, Deriv field, value)."""
    buy_ct, sell_ct = spec.contract_type_buy, spec.contract_type_sell
    rows = [
        ("side=BUY", "contract_type", buy_ct),
        ("side=SELL", "contract_type", sell_ct),
        ("size", f"amount (basis={spec.basis})", f"{intent.size}"),
    ]
    if spec.multiplier is not None:
        rows.append(("(contract)", "multiplier", str(spec.multiplier)))
    if spec.duration is not None:
        rows.append(("(contract)", "duration",
                     f"{spec.duration}{spec.duration_unit or 'm'}"))
    rows += [
        ("stop_loss", "limit_order.stop_loss",
         str(intent.stop_loss) if intent.stop_loss is not None else "(none)"),
        ("take_profit", "limit_order.take_profit",
         str(intent.take_profit) if intent.take_profit is not None else "(none)"),
        ("close", "sell(contract_id, price=0)", "market close"),
    ]
    return rows
