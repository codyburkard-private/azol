"""Environment gates and client factory for live Graph tests."""
from __future__ import annotations

import os
import unittest

from azol.clients import GraphClient
from azol.credentials import ServicePrincipal


def live_enabled() -> bool:
    return os.environ.get("AZOL_LIVE_GRAPH", "").strip() == "1"


def has_cap(name: str) -> bool:
    return os.environ.get(f"AZOL_LIVE_CAP_{name.upper()}", "").strip() == "1"


def require_live():
    return unittest.skipUnless(live_enabled(), "Set AZOL_LIVE_GRAPH=1 to run live Graph tests")


def require_cap(name: str):
    return unittest.skipUnless(
        live_enabled() and has_cap(name),
        f"Set AZOL_LIVE_GRAPH=1 and AZOL_LIVE_CAP_{name.upper()}=1",
    )


def live_tenant() -> str:
    return os.environ["AZOL_LIVE_TENANT"]


def make_live_client() -> GraphClient:
    tenant = live_tenant()
    client_id = os.environ["AZOL_LIVE_CLIENT_ID"]
    client_secret = os.environ["AZOL_LIVE_CLIENT_SECRET"]
    cred = ServicePrincipal(client_id=client_id, client_secret=client_secret)
    return GraphClient(
        tenant=tenant,
        cred=cred,
        use_persistent_cache=False,
    )


def optional_env(name: str):
    value = os.environ.get(name, "").strip()
    return value or None
