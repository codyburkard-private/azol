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

# Entra directory writes/deletes are eventually consistent across partitions.
_CONSISTENCY_ATTEMPTS = 30
_CONSISTENCY_SLEEP_S = 2.0
_CREATE_ROUNDS = 3

T = TypeVar("T")


class ConsistencyPending(AzCliError):
    """Resource exists but is not fully visible yet; safe to retry."""


def _odata_eq(field: str, value: str) -> str:
    escaped = value.replace("'", "''")
    return f"{field} eq '{escaped}'"


def is_consistency_error(exc: BaseException) -> bool:
    if isinstance(exc, ConsistencyPending):
        return True
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
                raise AzCliError(
                    f"{label} failed after {attempt} attempt(s): {exc}"
                ) from exc
            print(
                f"  directory not ready for {label} "
                f"(attempt {attempt}/{attempts}); retrying..."
            )
            time.sleep(sleep_s)
    raise AzCliError(f"{label} failed after {attempts} attempts: {last_error}")


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

    args = [
        "rest",
        "--method",
        method.upper(),
        "--url",
        url,
        "--headers",
        "Content-Type=application/json",
    ]
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


def get_if_exists(path: str) -> dict[str, Any] | None:
    """Single GET; return None on NotFound (no retry)."""
    try:
        payload = graph("GET", path)
    except AzCliError as exc:
        if is_consistency_error(exc):
            return None
        raise
    if isinstance(payload, dict) and payload.get("id"):
        return payload
    return None


def wait_for_get(path: str, *, label: str | None = None) -> dict[str, Any]:
    """Poll GET until the resource is readable."""
    resolved_label = label or f"wait for {path}"

    def _get() -> dict[str, Any]:
        payload = get_if_exists(path)
        if payload is None:
            raise ConsistencyPending(f"{resolved_label}: not visible yet")
        return payload

    return with_consistency_retry(_get, label=resolved_label)


def find_by_display_name(collection: str, display_name: str) -> dict[str, Any] | None:
    rows = graph_list(f"/{collection}", filter_expr=_odata_eq("displayName", display_name))
    for row in rows:
        if row.get("displayName") == display_name:
            return row
    return None


def find_live_by_display_name(
    collection: str,
    display_name: str,
) -> dict[str, Any] | None:
    """Find by displayName and confirm the object is GET-able (skip stale filter hits)."""
    found = find_by_display_name(collection, display_name)
    if not found or not found.get("id"):
        return None
    return get_if_exists(f"/{collection}/{found['id']}")


def find_user_by_upn(upn: str) -> dict[str, Any] | None:
    rows = graph_list("/users", filter_expr=_odata_eq("userPrincipalName", upn))
    for row in rows:
        if row.get("userPrincipalName", "").lower() == upn.lower():
            return row
    return None


def find_live_user_by_upn(upn: str) -> dict[str, Any] | None:
    found = find_user_by_upn(upn)
    if not found or not found.get("id"):
        return None
    return get_if_exists(f"/users/{found['id']}")


def find_sp_by_app_id(app_id: str) -> dict[str, Any] | None:
    rows = graph_list("/servicePrincipals", filter_expr=_odata_eq("appId", app_id))
    return rows[0] if rows else None


def find_live_sp_by_app_id(app_id: str) -> dict[str, Any] | None:
    found = find_sp_by_app_id(app_id)
    if not found or not found.get("id"):
        return None
    return get_if_exists(f"/servicePrincipals/{found['id']}")


def wait_until_readable(
    path: str,
    *,
    label: str,
    fallback: Callable[[], dict[str, Any] | None] | None = None,
    attempts: int = _CONSISTENCY_ATTEMPTS,
    sleep_s: float = _CONSISTENCY_SLEEP_S,
) -> dict[str, Any]:
    """Poll path (and optional fallback finder) until a live object appears."""
    last_detail = "not visible"
    for attempt in range(1, attempts + 1):
        got = get_if_exists(path)
        if got is not None:
            return got
        if fallback is not None:
            alt = fallback()
            if alt is not None:
                return alt
        last_detail = f"GET {path} not found"
        if attempt < attempts:
            print(
                f"  waiting for {label} to become readable "
                f"(attempt {attempt}/{attempts}); retrying..."
            )
            time.sleep(sleep_s)
    raise AzCliError(f"{label} not readable after {attempts} attempt(s): {last_detail}")


def _create_service_principal(app_id: str, display_name: str) -> dict[str, Any]:
    """Create SP with retries for NoBackingApplicationObject replication lag."""

    def _create() -> dict[str, Any]:
        existing = find_live_sp_by_app_id(app_id)
        if existing is not None:
            return existing
        sp = graph("POST", "/servicePrincipals", {"appId": app_id})
        if isinstance(sp, dict) and "id" in sp:
            live = wait_until_readable(
                f"/servicePrincipals/{sp['id']}",
                label=f"service principal {display_name}",
                fallback=lambda: find_live_sp_by_app_id(app_id),
                attempts=15,
            )
            return live
        raise ConsistencyPending(
            f"service principal create for {display_name} returned no id"
        )

    return with_consistency_retry(
        _create,
        label=f"create service principal for {display_name}",
    )


def ensure_application(display_name: str) -> dict[str, str]:
    from graph.live.harness.config import assert_safe_display_name

    assert_safe_display_name(display_name)

    app = find_live_by_display_name("applications", display_name)
    if app is None:
        app = _create_live_application(display_name)

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

    sp = find_live_sp_by_app_id(app_id)
    if sp is None:
        sp = _create_service_principal(app_id, display_name)

    return {
        "appObjectId": app_object_id,
        "appId": app_id,
        "spId": sp["id"],
    }


def _create_live_application(display_name: str) -> dict[str, Any]:
    """POST application and wait until Graph can GET it; recreate if id stays dead."""
    tried_ids: list[str] = []
    for round_idx in range(1, _CREATE_ROUNDS + 1):
        # A live app may have appeared while a prior create was settling.
        existing = find_live_by_display_name("applications", display_name)
        if existing is not None:
            return existing

        created = graph("POST", "/applications", {"displayName": display_name})
        if not isinstance(created, dict) or "id" not in created:
            raise AzCliError(
                f"failed to create application {display_name} (round {round_idx})"
            )
        app_object_id = created["id"]
        tried_ids.append(app_object_id)
        print(
            f"  created application {display_name} id={app_object_id} "
            f"(round {round_idx}); waiting until readable..."
        )
        try:
            return wait_until_readable(
                f"/applications/{app_object_id}",
                label=f"application {display_name}",
                fallback=lambda: find_live_by_display_name("applications", display_name),
                attempts=_CONSISTENCY_ATTEMPTS,
            )
        except AzCliError:
            print(
                f"  application id={app_object_id} still not readable; "
                f"retrying create (round {round_idx}/{_CREATE_ROUNDS})..."
            )
            continue
    raise AzCliError(
        f"failed to create readable application {display_name}; tried ids={tried_ids}"
    )


def delete_best_effort(path: str) -> None:
    try:
        graph("DELETE", path)
    except AzCliError:
        pass
