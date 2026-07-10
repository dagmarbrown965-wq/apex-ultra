"""APEX ULTRA — Deriv DEMO broker integration (Phase 38)."""

from .deriv_adapter import (
    DerivConfig,
    DerivDemoAdapter,
    DerivRealAccountBlocked,
    live_trading_enabled,
)
from .deriv_transport import (
    DEFAULT_WS_URL,
    DerivConnectionError,
    DerivSimulatedTransport,
    DerivTimeout,
    DerivTransport,
    DerivTransportError,
    DerivWebSocketTransport,
)

__all__ = [
    "DerivConfig",
    "DerivDemoAdapter",
    "DerivRealAccountBlocked",
    "live_trading_enabled",
    "DEFAULT_WS_URL",
    "DerivConnectionError",
    "DerivSimulatedTransport",
    "DerivTimeout",
    "DerivTransport",
    "DerivTransportError",
    "DerivWebSocketTransport",
]

from .config_loader import (
    DerivConfigError,
    DerivSmokeConfig,
    is_virtual_login,
    load_deriv_config,
    verify_virtual_account,
)

__all__ += [
    "DerivConfigError",
    "DerivSmokeConfig",
    "is_virtual_login",
    "load_deriv_config",
    "verify_virtual_account",
]

from .execution_mapping import (
    ApexOrderIntent,
    DerivContractSpec,
    describe_mapping,
    map_intent_to_proposal,
    validate_mapping,
)
from .config_loader import load_contract_spec

__all__ += [
    "ApexOrderIntent",
    "DerivContractSpec",
    "describe_mapping",
    "map_intent_to_proposal",
    "validate_mapping",
    "load_contract_spec",
]

from .contract_verification import (
    ContractVerification,
    confirm_apex_mapping,
    verify_contracts_for,
)

__all__ += [
    "ContractVerification",
    "confirm_apex_mapping",
    "verify_contracts_for",
]

from .contract_selection import ContractSelection, select_contract

__all__ += ["ContractSelection", "select_contract"]

from .shadow import (
    ShadowBrokerView,
    ShadowEvent,
    ShadowRecorder,
    ShadowSignal,
    ShadowViolation,
)

__all__ += [
    "ShadowBrokerView",
    "ShadowEvent",
    "ShadowRecorder",
    "ShadowSignal",
    "ShadowViolation",
]
