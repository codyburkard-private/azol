"""Microsoft Graph via Azure CLI `az rest` (no azol imports)."""
from __future__ import annotations

import json
import os
import tempfile
import time
from typing import Any
from urllib.parse import quote

from graph.live.harness.az_auth import AzCliError, run_az
from graph.live.harness.config import GRAPH_V1

# Entra directory writes are eventually consistent; SP create often races app create.
_APP_VISIBLE_ATTEMPTS = 8
_APP_VISIBLE_SLEEP_S = 2.0
_SP_CREATE_ATTEMPTS = 8
_SP_CREATE_SLEEP_S = 2.0


def _odata_eq(field: str, value: str) -> str:
    escaped = value.replace("'", "''")
    return f"{field} eq '{escaped}'"


def graph(
    method: str,
    url: str,
    body: dict[str, Any] | list[Any] | None = None,
    *,
    allow_statuses: set[int] | None = None,
) -> Any:
    """Invoke Microsoft Graph through Azure CLI (`az rest`)."""
    if url.startswith("/"):
        url = f"{GRAPH_V1}{url}"

    args = ["rest", "--method", method.upper(), "--url", url]
    tmp_path: str | None = None
    try:
        if body is not None:
            fd, tmp_path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(body, handle)
            args.extend(["--body", f"@{tmp_path}"])
        args.extend(["--output", "json"])
        proc = run_az(args, check=False)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            # az rest sometimes embeds HTTP status in stderr
            if allow_statuses and any(str(code) in detail for code in allow_statuses):
                return None
            raise AzCliError(f"az rest {method.upper()} {url} failed: {detail}")
        text = (proc.stdout or "").strip()
        if not text:
            return None
        return json.loads(text)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def graph_list(path: str, *, filter_expr: str | None = None) -> list[dict[str, Any]]:
    url = path if path.startswith("http") else f"{GRAPH_V1}{path if path.startswith('/') else '/' + path}"
    if filter_expr:
        sep = "&" if "?" in url else "?"
        encoded = quote(filter_expr, safe="()$' ")
        url = f"{url}{sep}$filter={encoded}"
    payload = graph("GET", url)
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        value = payload.get("value")
        if isinstance(value, list):
            return value
        return [payload]
    return []


def find_by_display_name(collection: str, display_name: str) -> dict[str, Any] | None:
    rows = graph_list(f"/{collection}", filter_expr=_odata_eq("displayName", display_name))
    for row in rows:
        if row.get("displayName") == display_name:
            return row
    return None


def find_user_by_upn(upn: str) -> dict[str, Any] | None:
    rows = graph_list("/users", filter_expr=_odata_eq("userPrincipalName", upn))
    for row in rows:
        if row.get("userPrincipalName", "").lower() == upn.lower():
            return row
    return None


def find_sp_by_app_id(app_id: str) -> dict[str, Any] | None:
    rows = graph_list("/servicePrincipals", filter_expr=_odata_eq("appId", app_id))
    return rows[0] if rows else None


def _wait_for_application(app_object_id: str, app_id: str) -> None:
    """Poll until the application is readable by object id and appId filter."""
    last_error: Exception | None = None
    for attempt in range(1, _APP_VISIBLE_ATTEMPTS + 1):
        try:
            fetched = graph("GET", f"/applications/{app_object_id}")
            if isinstance(fetched, dict) and fetched.get("appId") == app_id:
                by_app_id = graph_list(
                    "/applications",
                    filter_expr=_odata_eq("appId", app_id),
                )
                if any(row.get("id") == app_object_id for row in by_app_id):
                    return
        except AzCliError as exc:
            last_error = exc
        if attempt < _APP_VISIBLE_ATTEMPTS:
            time.sleep(_APP_VISIBLE_SLEEP_S)
    detail = f" ({last_error})" if last_error else ""
    raise AzCliError(
        f"application {app_object_id} (appId={app_id}) not visible after "
        f"{_APP_VISIBLE_ATTEMPTS} attempts{detail}"
    )


def _create_service_principal(app_id: str, display_name: str) -> dict[str, Any]:
    """Create SP with retries for NoBackingApplicationObject replication lag."""
    last_error: Exception | None = None
    for attempt in range(1, _SP_CREATE_ATTEMPTS + 1):
        existing = find_sp_by_app_id(app_id)
        if existing is not None:
            return existing
        try:
            sp = graph("POST", "/servicePrincipals", {"appId": app_id})
            if isinstance(sp, dict) and "id" in sp:
                return sp
            raise AzCliError(f"failed to create service principal for {display_name}")
        except AzCliError as exc:
            last_error = exc
            detail = str(exc)
            retryable = (
                "NoBackingApplicationObject" in detail
                or "does not reference a valid application object" in detail
            )
            if not retryable or attempt >= _SP_CREATE_ATTEMPTS:
                raise
            time.sleep(_SP_CREATE_SLEEP_S)
    raise AzCliError(
        f"failed to create service principal for {display_name}: {last_error}"
    )


def ensure_application(display_name: str) -> dict[str, str]:
    from graph.live.harness.config import assert_safe_display_name

    assert_safe_display_name(display_name)
    app = find_by_display_name("applications", display_name)
    created = False
    if app is None:
        app = graph("POST", "/applications", {"displayName": display_name})
        if not isinstance(app, dict) or "id" not in app:
            raise AzCliError(f"failed to create application {display_name}")
        created = True
    app_object_id = app["id"]
    app_id = app.get("appId")
    if not app_id:
        fetched = graph("GET", f"/applications/{app_object_id}")
        if not isinstance(fetched, dict) or not fetched.get("appId"):
            raise AzCliError(f"application {display_name} missing appId")
        app_id = fetched["appId"]
    if created:
        _wait_for_application(app_object_id, app_id)
    sp = find_sp_by_app_id(app_id)
    if sp is None:
        sp = _create_service_principal(app_id, display_name)
    return {
        "appObjectId": app_object_id,
        "appId": app_id,
        "spId": sp["id"],
    }


def delete_best_effort(path: str) -> None:
    try:
        graph("DELETE", path)
    except AzCliError:
        pass
