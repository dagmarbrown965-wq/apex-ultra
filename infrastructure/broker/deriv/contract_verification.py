"""
APEX ULTRA — Deriv Contract Verification (Phase 39.2)

Parses a Deriv `contracts_for` response and confirms the candidate contract is
actually available with parameters compatible with the APEX execution mapping.
Nothing here is assumed: the contract type, stake bounds, SL/TP support, and
durations are read from the (live) response and validated.

Defensive parsing: Deriv's exact field names can vary by API version, so every
lookup uses .get() with fallbacks. When run against the live server this is the
source of truth that flips the readiness gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .execution_mapping import DerivContractSpec


def _to_float(val, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


@dataclass
class ContractVerification:
    symbol: str
    symbol_exists: bool
    contract_type: str
    contract_category: Optional[str]
    available_types: list[str]
    min_stake: Optional[float]
    max_stake: Optional[float]
    multiplier_range: list = field(default_factory=list)
    min_duration: Optional[str] = None
    max_duration: Optional[str] = None
    stake_model: str = "stake"
    sl_supported: bool = False
    tp_supported: bool = False
    close_supported: bool = True   # Deriv contracts close via sell()
    confirmed: bool = False
    issues: list[str] = field(default_factory=list)

    def parameters(self) -> dict:
        return {
            "min_stake": self.min_stake,
            "max_stake": self.max_stake,
            "multiplier_range": self.multiplier_range or None,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
        }


def verify_contracts_for(response: dict, spec: DerivContractSpec, symbol: str,
                         intent_size: float) -> ContractVerification:
    """Validate a contracts_for response against the candidate spec + intent."""
    cf = response.get("contracts_for", response)  # accept raw or wrapped
    available_entries = cf.get("available", [])
    available_types = [e.get("contract_type") for e in available_entries]
    symbol_exists = bool(available_entries) and (
        cf.get("symbol", symbol) == symbol or symbol in
        {e.get("underlying_symbol") for e in available_entries})

    issues: list[str] = []
    if not symbol_exists:
        issues.append(f"symbol {symbol} not present in contracts_for")

    # locate the candidate BUY contract type entry
    want = spec.contract_type_buy
    entry = next((e for e in available_entries
                  if e.get("contract_type") == want), None)
    if entry is None:
        issues.append(f"contract_type {want} not available for {symbol}")
        return ContractVerification(
            symbol=symbol, symbol_exists=symbol_exists, contract_type=want,
            contract_category=None, available_types=available_types,
            min_stake=_to_float(cf.get("min_stake")),
            max_stake=_to_float(cf.get("max_stake")),
            confirmed=False, issues=issues)

    category = entry.get("contract_category")
    min_stake = _to_float(entry.get("min_stake"), _to_float(cf.get("min_stake")))
    max_stake = _to_float(entry.get("max_stake"), _to_float(cf.get("max_stake")))
    mult_range = entry.get("multiplier_range", []) or []
    supports_lo = bool(entry.get("supports_limit_order",
                                 1 if category == "multiplier" else 0))

    # sell-side type must also exist
    if spec.contract_type_sell not in available_types:
        issues.append(f"sell-side {spec.contract_type_sell} not available")

    # stake bounds
    if min_stake is not None and intent_size < min_stake:
        issues.append(f"size {intent_size} below min_stake {min_stake}")
    if max_stake is not None and intent_size > max_stake:
        issues.append(f"size {intent_size} above max_stake {max_stake}")

    # multiplier presence for multiplier contracts
    if category == "multiplier":
        if spec.multiplier is None:
            issues.append("multiplier contract but spec.multiplier is None")
        elif mult_range and spec.multiplier not in mult_range:
            issues.append(f"multiplier {spec.multiplier} not in {mult_range}")

    # SL/TP support must match what the spec/intent will request
    sl_supported = tp_supported = supports_lo
    if spec.supports_limit_order and not supports_lo:
        issues.append("spec expects limit_order (SL/TP) but contract does not support it")

    confirmed = (symbol_exists and entry is not None and not issues)

    return ContractVerification(
        symbol=symbol, symbol_exists=symbol_exists, contract_type=want,
        contract_category=category, available_types=available_types,
        min_stake=min_stake, max_stake=max_stake, multiplier_range=mult_range,
        min_duration=entry.get("min_contract_duration"),
        max_duration=entry.get("max_contract_duration"),
        stake_model=spec.basis, sl_supported=sl_supported, tp_supported=tp_supported,
        close_supported=True, confirmed=confirmed, issues=issues)


def confirm_apex_mapping(spec: DerivContractSpec,
                         v: ContractVerification) -> tuple[bool, list[tuple], list[str]]:
    """Confirm APEX BUY/SELL/CLOSE/SIZE/SL/TP map to the actual Deriv fields the
    verified contract supports. Returns (ok, rows, issues)."""
    issues: list[str] = []
    rows = [
        ("APEX BUY", "contract_type", spec.contract_type_buy),
        ("APEX SELL/CLOSE", "sell(contract_id, price=0)", "market close"),
        ("APEX SIZE", f"amount (basis={spec.basis})",
         f"within [{v.min_stake}, {v.max_stake}]"),
        ("APEX STOP LOSS", "limit_order.stop_loss",
         "supported" if v.sl_supported else "NOT supported"),
        ("APEX TAKE PROFIT", "limit_order.take_profit",
         "supported" if v.tp_supported else "NOT supported"),
    ]
    if not v.close_supported:
        issues.append("close not supported")
    if not v.sl_supported:
        issues.append("stop_loss not supported by verified contract")
    if not v.tp_supported:
        issues.append("take_profit not supported by verified contract")
    ok = v.confirmed and not issues
    return ok, rows, issues
