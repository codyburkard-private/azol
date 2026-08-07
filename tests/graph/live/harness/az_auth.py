"""Azure CLI session helpers for the live harness (no azol imports)."""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from graph.live.harness.config import DEFAULT_TENANT, LiveConfig


class AzCliError(RuntimeError):
    """Raised when an Azure CLI invocation fails."""


def _az_bin() -> str:
    found = shutil.which("az")
    if not found:
        raise AzCliError("Azure CLI (`az`) not found on PATH")
    return found


def run_az(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [_az_bin(), *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise AzCliError(f"az {' '.join(args)} failed ({proc.returncode}): {detail}")
    return proc


def az_json(args: list[str]) -> Any:
    proc = run_az([*args, "--output", "json"])
    text = (proc.stdout or "").strip()
    if not text:
        return None
    return json.loads(text)


def get_account() -> dict[str, Any]:
    account = az_json(["account", "show"])
    if not isinstance(account, dict):
        raise AzCliError("az account show returned no account; run azure/login or az login")
    return account


def assert_logged_in_for_tenant(config: LiveConfig) -> dict[str, Any]:
    account = get_account()
    tenant_id = account.get("tenantId")
    user = account.get("user") or {}
    name = user.get("name") or ""

    if config.tenant_id and tenant_id and config.tenant_id.lower() != str(tenant_id).lower():
        raise AzCliError(
            f"az account tenantId {tenant_id} does not match AZOL_LIVE_TENANT_ID={config.tenant_id}"
        )

    # Domain check when tenant env is the default vanity domain
    if config.tenant == DEFAULT_TENANT and not config.allow_any_tenant:
        # Federated SP logins often lack vanity domain on account; tenantId check above is preferred.
        # Soft-check: if name looks like a UPN domain, require azoltest.
        if "@" in name and not name.lower().endswith(f"@{DEFAULT_TENANT}"):
            # App-only sessions use object id style names — ignore.
            if "." in name.split("@", 1)[-1]:
                raise AzCliError(
                    f"az account user {name!r} is not in {DEFAULT_TENANT}; "
                    "set AZOL_LIVE_ALLOW_ANY_TENANT=1 to override"
                )
    return account


def get_graph_access_token() -> str:
    """Return a Microsoft Graph access token from the current az session.

    Never log the return value.
    """
    token = az_json(
        [
            "account",
            "get-access-token",
            "--resource",
            "https://graph.microsoft.com",
        ]
    )
    if not isinstance(token, dict) or not token.get("accessToken"):
        raise AzCliError("az account get-access-token did not return accessToken")
    return str(token["accessToken"])
