"""Environment and path configuration for the live Graph harness."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TENANT = "azoltest.onmicrosoft.com"
STATE_PREFIX = "azol-state-"
EPHEMERAL_PREFIX = "azol-ephemeral-"
GRAPH_V1 = "https://graph.microsoft.com/v1.0"
GRAPH_BETA = "https://graph.microsoft.com/beta"
MICROSOFT_GRAPH_APP_ID = "00000003-0000-0000-c000-000000000000"
DIRECTORY_READERS_DISPLAY_NAME = "Directory Readers"
GRAPH_APP_ROLE_VALUE = "User.Read.All"

LIVE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = LIVE_DIR / ".state.json"


@dataclass(frozen=True)
class LiveConfig:
    tenant: str
    tenant_id: str | None
    client_id: str | None
    allow_any_tenant: bool
    auto_ensure: bool
    capabilities: frozenset[str]

    @property
    def upn_domain(self) -> str:
        return self.tenant

    def has_cap(self, name: str) -> bool:
        return name.lower() in self.capabilities


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip() == "1"


def load_config() -> LiveConfig:
    caps = set()
    for key, value in os.environ.items():
        if key.startswith("AZOL_LIVE_CAP_") and value.strip() == "1":
            caps.add(key.removeprefix("AZOL_LIVE_CAP_").lower())
    return LiveConfig(
        tenant=os.environ.get("AZOL_LIVE_TENANT", DEFAULT_TENANT).strip(),
        tenant_id=(os.environ.get("AZOL_LIVE_TENANT_ID") or "").strip() or None,
        client_id=(os.environ.get("AZOL_LIVE_CLIENT_ID") or "").strip() or None,
        allow_any_tenant=_truthy("AZOL_LIVE_ALLOW_ANY_TENANT"),
        auto_ensure=_truthy("AZOL_LIVE_AUTO_ENSURE"),
        capabilities=frozenset(caps),
    )


def assert_tenant_allowed(config: LiveConfig) -> None:
    if config.tenant == DEFAULT_TENANT:
        return
    if config.allow_any_tenant:
        return
    raise SystemExit(
        f"Refusing tenant {config.tenant!r}; expected {DEFAULT_TENANT!r} "
        "or set AZOL_LIVE_ALLOW_ANY_TENANT=1"
    )


def prefixed_name(suffix: str) -> str:
    if not suffix.startswith(STATE_PREFIX):
        return f"{STATE_PREFIX}{suffix}"
    return suffix


def assert_safe_display_name(name: str) -> None:
    if not (name.startswith(STATE_PREFIX) or name.startswith(EPHEMERAL_PREFIX)):
        raise ValueError(
            f"Refusing non-harness name {name!r}; must start with "
            f"{STATE_PREFIX!r} or {EPHEMERAL_PREFIX!r}"
        )
