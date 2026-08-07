"""Microsoft Graph via Azure CLI `az rest` (no azol imports)."""
from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Callable
from typing import Any, TypeVar
from urllib.parse import quote

from graph.live.harness.az_auth import AzCliError, run_az
from graph.live.harness.config import GRAPH_V1

# Entra directory writes are eventually consistent across partitions.
_CONSISTENCY_ATTEMPTS = 10
_CONSISTENCY_SLEEP_S = 2.0

T = TypeVar("T")


def _odata_eq(field: str, value: str) -> str:
    escaped = value.replace("'", "''")
    return f"{field} eq '{escaped}'"


def is_consistency_error(exc: BaseException) -> bool:
    detail = str(exc)
    markers = (
        "Request_ResourceNotFound",
        "ResourceNotFound",
        "Not Found",
        "does not exist or one of its queried reference-property objects are not present",
        "NoBackingApplicationObject",
        "does not reference a valid application object",
    )
    return any(marker in detail for marker in markers)


def with_consistency_retry(
    operation: Callable[[], T],
    *,
    label: str,
    attempts: int = _CONSISTENCY_ATTEMPTS,
    sleep_s: float = _CONSISTENCY_SLEEP_S,
) -> T:
    """Retry Graph operations that fail due to Entra replication lag."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except AzCliError as exc:
            last_error = exc
            if not is_consistency_error(exc) or attempt >= attempts:
                raise
            time.sleep(sleep_s)
    raise AzCliError(f"{label} failed after {attempts} attempts: {last_error}")


def wait_for_get(path: str, *, label: str | None = None) -> dict[str, Any]:
    """Poll GET until the resource is readable."""
    resolved_label = label or f"wait for {path}"

    def _get() -> dict[str, Any]:
        payload = graph("GET", path)
        if not isinstance(payload, dict) or "id" not in payload:
            raise AzCliError(f"{resolved_label}: empty or invalid response")
        return payload

    return with_consistency_retry(_get, label=resolved_label)


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


def graph_list_consistent(
    path: str,
    *,
    filter_expr: str | None = None,
    label: str | None = None,
) -> list[dict[str, Any]]:
    """Like graph_list, but retries NotFound from parent-resource replication lag."""
    return with_consistency_retry(
        lambda: graph_list(path, filter_expr=filter_expr),
        label=label or f"list {path}",
    )


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

    def _ready() -> dict[str, Any]:
        fetched = graph("GET", f"/applications/{app_object_id}")
        if not isinstance(fetched, dict):
            raise AzCliError(f"application {app_object_id} not ready")
        if fetched.get("appId") != app_id:
            raise AzCliError(
                f"application {app_object_id} not ready "
                f"(expected appId={app_id}, got {fetched.get('appId')})"
            )
        by_app_id = graph_list(
            "/applications",
            filter_expr=_odata_eq("appId", app_id),
        )
        if not any(row.get("id") == app_object_id for row in by_app_id):
            raise AzCliError(
                f"application {app_object_id} not yet returned by appId filter"
            )
        return fetched

    with_consistency_retry(
        _ready,
        label=f"application {app_object_id} (appId={app_id}) visibility",
    )


def _create_service_principal(app_id: str, display_name: str) -> dict[str, Any]:
    """Create SP with retries for NoBackingApplicationObject replication lag."""

    def _create() -> dict[str, Any]:
        existing = find_sp_by_app_id(app_id)
        if existing is not None:
            return existing
        sp = graph("POST", "/servicePrincipals", {"appId": app_id})
        if isinstance(sp, dict) and "id" in sp:
            return sp
        raise AzCliError(f"failed to create service principal for {display_name}")

    return with_consistency_retry(
        _create,
        label=f"create service principal for {display_name}",
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
        fetched = wait_for_get(
            f"/applications/{app_object_id}",
            label=f"application {display_name}",
        )
        app_id = fetched.get("appId")
        if not app_id:
            raise AzCliError(f"application {display_name} missing appId")
    if created:
        _wait_for_application(app_object_id, app_id)
    else:
        wait_for_get(
            f"/applications/{app_object_id}",
            label=f"application {display_name}",
        )
    sp = find_sp_by_app_id(app_id)
    if sp is None:
        sp = _create_service_principal(app_id, display_name)
    wait_for_get(f"/servicePrincipals/{sp['id']}", label=f"service principal {display_name}")
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
