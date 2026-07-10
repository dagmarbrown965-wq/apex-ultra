"""
APEX ULTRA — Deriv DEMO Config Loader (Phase 39)

Loads Deriv smoke-test configuration from the environment (or an explicit dict)
and provides virtual-account verification.

Environment variables:
  DERIV_APP_ID         (default 1089 — Deriv's public app id)
  DERIV_API_TOKEN      (required for a real run; demo/virtual token)
  DERIV_ACCOUNT_LOGIN  (optional; verified against the authorized loginid)
  DERIV_SYMBOL         (default R_100)
  DERIV_CURRENCY       (default USD)
  LIVE_TRADING         (default false — must be false for DEMO ONLY)
  DERIV_SHADOW_MODE    (default true — demo-only observation default)
  DERIV_WS_URL         (default wss://ws.derivws.com/websockets/v3)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

from .deriv_adapter import DerivConfig
from .deriv_transport import DEFAULT_WS_URL

VIRTUAL_PREFIXES = ("VRT", "VRTC")


class DerivConfigError(Exception):
    """Invalid or unsafe Deriv configuration."""


@dataclass
class DerivSmokeConfig:
    app_id: str = "1089"
    api_token: str = ""
    account_login: Optional[str] = None
    symbol: str = "R_100"
    currency: str = "USD"
    ws_url: str = DEFAULT_WS_URL
    live_trading: bool = False
    shadow_mode: bool = True
    warnings: list[str] = field(default_factory=list)

    def deriv_config(self) -> DerivConfig:
        return DerivConfig(
            app_id=self.app_id,
            api_token=self.api_token,
            ws_url=self.ws_url,
            symbol=self.symbol,
            currency=self.currency,
        )

    @property
    def token_present(self) -> bool:
        return bool(self.api_token) and self.api_token != "DEMO-TOKEN"


def _as_bool(val: Optional[str], default: bool) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def load_deriv_config(env: Optional[Mapping[str, str]] = None,
                      *, require_token: bool = False) -> DerivSmokeConfig:
    env = env if env is not None else os.environ
    cfg = DerivSmokeConfig(
        app_id=env.get("DERIV_APP_ID", "1089"),
        api_token=env.get("DERIV_API_TOKEN", ""),
        account_login=env.get("DERIV_ACCOUNT_LOGIN") or None,
        symbol=env.get("DERIV_SYMBOL", "R_100"),
        currency=env.get("DERIV_CURRENCY", "USD"),
        ws_url=env.get("DERIV_WS_URL", DEFAULT_WS_URL),
        live_trading=_as_bool(env.get("LIVE_TRADING"), False),
        shadow_mode=_as_bool(env.get("DERIV_SHADOW_MODE"), True),
    )

    # SAFETY: LIVE_TRADING must be false for DEMO ONLY operation.
    if cfg.live_trading:
        cfg.warnings.append(
            "LIVE_TRADING=true detected — DEMO ONLY enforced anyway; "
            "real trading capability is disabled.")
    if not cfg.shadow_mode:
        cfg.warnings.append(
            "DERIV_SHADOW_MODE=false requested — ignored; shadow (demo-only) "
            "mode remains the default in Phase 39.")
        cfg.shadow_mode = True  # shadow mode remains default

    if cfg.account_login and not is_virtual_login(cfg.account_login):
        raise DerivConfigError(
            f"DERIV_ACCOUNT_LOGIN '{cfg.account_login}' is not a virtual "
            "account (must start with VRT)")

    if require_token and not cfg.token_present:
        raise DerivConfigError(
            "DERIV_API_TOKEN is required for a real run; set it to a Deriv "
            "VIRTUAL account token")
    return cfg


def is_virtual_login(loginid: Optional[str]) -> bool:
    return bool(loginid) and loginid.upper().startswith(VIRTUAL_PREFIXES)


def load_contract_spec(env: Optional[Mapping[str, str]] = None):
    """Build a DerivContractSpec from env. `confirmed` defaults FALSE — the
    candidate contract type must be confirmed against contracts_for."""
    from .execution_mapping import DerivContractSpec
    env = env if env is not None else os.environ
    mult = env.get("DERIV_MULTIPLIER")
    dur = env.get("DERIV_DURATION")
    return DerivContractSpec(
        contract_type_buy=env.get("DERIV_CONTRACT_TYPE_BUY", "MULTUP"),
        contract_type_sell=env.get("DERIV_CONTRACT_TYPE_SELL", "MULTDOWN"),
        basis=env.get("DERIV_BASIS", "stake"),
        multiplier=int(mult) if mult else (None if dur else 100),
        duration=int(dur) if dur else None,
        duration_unit=env.get("DERIV_DURATION_UNIT"),
        supports_limit_order=_as_bool(env.get("DERIV_SUPPORTS_LIMIT_ORDER"), True),
        confirmed=_as_bool(env.get("DERIV_CONTRACT_CONFIRMED"), False),
    )


def verify_virtual_account(authorize_response: dict,
                           expected_login: Optional[str] = None) -> tuple[bool, str]:
    """Returns (ok, reason). Confirms is_virtual===true and (optionally) that the
    authorized loginid matches the configured account."""
    if "error" in authorize_response:
        return False, f"authorize error: {authorize_response['error'].get('message')}"
    acct = authorize_response.get("authorize", {})
    is_virtual = bool(acct.get("is_virtual", 0))
    loginid = acct.get("loginid", "")
    if not is_virtual:
        return False, f"account {loginid} is REAL (is_virtual=false)"
    if not is_virtual_login(loginid):
        return False, f"loginid {loginid} lacks a virtual prefix"
    if expected_login and loginid != expected_login:
        return False, f"loginid {loginid} != configured {expected_login}"
    return True, f"virtual account {loginid} verified"
