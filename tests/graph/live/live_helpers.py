"""Live Graph test helpers: always attempt; skip clearly when not ready."""
from __future__ import annotations

import os
import unittest
from typing import Any

from azol.clients import GraphClient
from azol.credentials import AccessToken

from graph.live.harness.az_auth import AzCliError, assert_logged_in_for_tenant, get_graph_access_token
from graph.live.harness.config import DEFAULT_TENANT, load_config
from graph.live.harness.manifest import load_manifest, require_state


class LiveSetupError(RuntimeError):
    """Live Graph prerequisites are missing or misconfigured."""


def live_explicitly_disabled() -> bool:
    """Opt out with AZOL_LIVE_GRAPH=0 (unset means try)."""
    return os.environ.get("AZOL_LIVE_GRAPH", "").strip() == "0"


def has_cap(name: str) -> bool:
    return os.environ.get(f"AZOL_LIVE_CAP_{name.upper()}", "").strip() == "1"


def live_tenant() -> str:
    return load_config().tenant


def live_unavailable_reason() -> str | None:
    """Return a skip reason if live tests cannot run, else None."""
    if live_explicitly_disabled():
        return "AZOL_LIVE_GRAPH=0 (live suite disabled)"
    config = load_config()
    if config.tenant != DEFAULT_TENANT and not config.allow_any_tenant:
        return (
            f"refusing tenant {config.tenant!r}; expected {DEFAULT_TENANT!r} "
            "or set AZOL_LIVE_ALLOW_ANY_TENANT=1"
        )
    try:
        assert_logged_in_for_tenant(config)
        get_graph_access_token()
    except AzCliError as exc:
        return f"live Graph not ready: {exc}"
    return None


def make_live_client() -> GraphClient:
    """Build GraphClient from the ambient Azure CLI Graph token."""
    reason = live_unavailable_reason()
    if reason:
        raise LiveSetupError(reason)
    config = load_config()
    token = get_graph_access_token()
    return GraphClient(
        tenant=config.tenant,
        cred=AccessToken(token),
        use_persistent_cache=False,
    )


def optional_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def load_live_manifest() -> dict[str, Any] | None:
    return load_manifest()


def require_manifest_state(test: unittest.TestCase, name: str) -> dict[str, Any]:
    manifest = load_live_manifest()
    try:
        return require_state(manifest, name)
    except KeyError:
        test.skipTest(
            f"state {name!r} missing; run: python -m graph.live.harness.cli ensure"
        )


def skip_unavailable_graph(test: unittest.TestCase, exc: BaseException) -> None:
    """Skip when Graph rejects the call for auth/license; otherwise re-raise.

    License errors often arrive as HTTP 400 with detail only in the response
    body (``AzolHTTPError.body_snippet``), not in ``str(exc)``.
    """
    text = str(exc)
    body = getattr(exc, "body_snippet", None) or ""
    status = getattr(exc, "status_code", None)
    haystack = f"{text}\n{body}".lower()

    license_markers = (
        "aadpremiumlicenserequired",
        "nolicense",
        "license requirement",
        "does not meet license",
        "not licensed",
        "premium license",
        "entra id p2",
        "entra id governance",
        "tenant does not meet license",
    )
    if any(marker in haystack for marker in license_markers):
        test.skipTest(f"Graph capability unavailable (license): {exc}")

    if status in (401, 403, 404):
        test.skipTest(f"Graph capability unavailable: {exc}")

    markers = (
        "authorization_requestdenied",
        "authorization_identitynotfound",
        "accessdenied",
        "aadsts",
        "insufficient privileges",
        "required scopes are missing",
        "request_resourcenotfound",
    )
    if any(marker in haystack for marker in markers):
        test.skipTest(f"Graph capability unavailable: {exc}")
    raise exc


class LiveGraphTestCase(unittest.TestCase):
    """Base class: always attempt live client setup; skip if not ready."""

    client: GraphClient

    @classmethod
    def setUpClass(cls):
        try:
            cls.client = make_live_client()
        except LiveSetupError as exc:
            raise unittest.SkipTest(str(exc)) from exc

    @classmethod
    def tearDownClass(cls):
        client = getattr(cls, "client", None)
        if client is not None:
            client.close()
