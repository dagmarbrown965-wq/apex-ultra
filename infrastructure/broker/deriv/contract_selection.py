"""
APEX ULTRA — Deriv Contract Selection (Phase 39.3)

Derives the confirmed contract from an ACTUAL contracts_for response. Nothing is
assumed: the contract type, its parameters, stake bounds, and SL/TP support are
all read from the response. A contract is selected only if it can represent the
APEX intent (directional up/down pair + SL/TP if the intent requires them).

If no available contract can represent the intent, selection is not confirmed
and the readiness gate must report BLOCKED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Known directional pairs in Deriv's taxonomy: (up_type, down_type, category).
# Only pairs actually present in the contracts_for response are ever used; this
# table just says which two types form a buy/sell pair — it does NOT assume any
# particular one is available for a given account/symbol.
DIRECTIONAL_PAIRS = [
    ("MULTUP", "MULTDOWN", "multiplier"),
    ("TURBOSLONG", "TURBOSSHORT", "turbos"),
    ("CALL", "PUT", "callput"),
    ("CALLE", "PUTE", "callputequal"),
]
# Preference order when several qualify: those that can carry SL/TP first.
CATEGORY_PREFERENCE = ["multiplier", "turbos", "callput", "callputequal"]


def _to_float(val, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


@dataclass
class ContractSelection:
    symbol: str
    confirmed: bool = False
    contract_type_buy: Optional[str] = None
    contract_type_sell: Optional[str] = None
    category: Optional[str] = None
    basis: str = "stake"
    min_stake: Optional[float] = None
    max_stake: Optional[float] = None
    multiplier: Optional[int] = None
    multiplier_range: list = field(default_factory=list)
    min_duration: Optional[str] = None
    max_duration: Optional[str] = None
    supports_limit_order: bool = False
    sl_representable: bool = False
    tp_representable: bool = False
    available_types: list = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def duration_model(self) -> str:
        if self.category in ("multiplier", "turbos"):
            return "open-ended (closed via sell)"
        if self.min_duration or self.max_duration:
            return f"{self.min_duration}..{self.max_duration}"
        return "n/a"

    def to_spec(self):
        """Build a confirmed DerivContractSpec from this selection."""
        from .execution_mapping import DerivContractSpec
        return DerivContractSpec(
            contract_type_buy=self.contract_type_buy or "",
            contract_type_sell=self.contract_type_sell or "",
            basis=self.basis,
            multiplier=self.multiplier if self.category in ("multiplier",) else None,
            duration=None,
            supports_limit_order=self.supports_limit_order,
            confirmed=self.confirmed,
            candidate_note=f"confirmed from contracts_for ({self.category})",
        )


def _supports_limit_order(entry: dict, category: Optional[str]) -> tuple[bool, bool]:
    """Returns (supported, inferred). Prefers the explicit flag; infers from
    category only when the flag is absent (and records that it was inferred)."""
    if "supports_limit_order" in entry:
        return bool(entry.get("supports_limit_order")), False
    # inference fallback — multipliers/turbos carry limit_order, callput does not
    return (category in ("multiplier", "turbos")), True


def select_contract(contracts_for_response: dict, symbol: str, *,
                    needs_sl: bool, needs_tp: bool, size: float,
                    preferred_multiplier: Optional[int] = None) -> ContractSelection:
    cf = contracts_for_response.get("contracts_for", contracts_for_response)
    entries = cf.get("available", [])
    by_type = {e.get("contract_type"): e for e in entries}
    available_types = list(by_type.keys())

    sel = ContractSelection(symbol=symbol, available_types=available_types)

    if not entries:
        sel.reasons.append(f"symbol {symbol} returned no contracts")
        return sel

    qualifying: list[ContractSelection] = []
    for up, down, category in DIRECTIONAL_PAIRS:
        if up not in by_type or down not in by_type:
            continue
        entry = by_type[up]
        supports_lo, inferred = _supports_limit_order(entry, category)
        min_stake = _to_float(entry.get("min_stake"), _to_float(cf.get("min_stake")))
        max_stake = _to_float(entry.get("max_stake"), _to_float(cf.get("max_stake")))
        mult_range = entry.get("multiplier_range", []) or []

        local_reasons = []
        if needs_sl and not supports_lo:
            local_reasons.append(f"{up}: stop_loss not representable (no limit_order)")
        if needs_tp and not supports_lo:
            local_reasons.append(f"{up}: take_profit not representable (no limit_order)")
        if min_stake is not None and size < min_stake:
            local_reasons.append(f"{up}: size {size} < min_stake {min_stake}")
        if max_stake is not None and size > max_stake:
            local_reasons.append(f"{up}: size {size} > max_stake {max_stake}")

        chosen_mult = None
        if category == "multiplier":
            if mult_range:
                if preferred_multiplier is not None:
                    if preferred_multiplier in mult_range:
                        chosen_mult = preferred_multiplier
                    else:
                        local_reasons.append(
                            f"{up}: multiplier {preferred_multiplier} not in {mult_range}")
                else:
                    chosen_mult = mult_range[len(mult_range) // 2]  # from response
            else:
                local_reasons.append(f"{up}: multiplier contract but no multiplier_range")

        candidate = ContractSelection(
            symbol=symbol, confirmed=(len(local_reasons) == 0),
            contract_type_buy=up, contract_type_sell=down, category=category,
            min_stake=min_stake, max_stake=max_stake,
            multiplier=chosen_mult, multiplier_range=mult_range,
            min_duration=entry.get("min_contract_duration"),
            max_duration=entry.get("max_contract_duration"),
            supports_limit_order=supports_lo,
            sl_representable=(supports_lo or not needs_sl),
            tp_representable=(supports_lo or not needs_tp),
            available_types=available_types,
            reasons=local_reasons + (["(limit_order support inferred from "
                                      "category — verify on live response)"]
                                     if inferred and supports_lo else []),
        )
        if candidate.confirmed:
            qualifying.append(candidate)
        else:
            sel.reasons += local_reasons

    if not qualifying:
        if not sel.reasons:
            sel.reasons.append("no directional contract pair available for symbol")
        return sel

    qualifying.sort(key=lambda c: CATEGORY_PREFERENCE.index(c.category)
                    if c.category in CATEGORY_PREFERENCE else 99)
    return qualifying[0]
