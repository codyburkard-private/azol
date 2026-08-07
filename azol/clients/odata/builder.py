"""Fluent OData query builder for Microsoft Graph."""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Optional, Set

from azol.clients.odata.request import ODataHTTPRequest

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


class ODataQueryBuilder:
    """Accumulate OData query options and ``build()`` an ``ODataHTTPRequest``.

    The builder never performs I/O. Call ``build().execute()`` to send, then
    ``values()`` on the resulting ``ODataResponse`` to page through results.
    """

    def __init__(
        self,
        client: "OAuthHTTPClient",
        path: str,
        *,
        exception_cls: Optional[type] = None,
    ):
        self._client = client
        if not path.startswith("/"):
            path = f"/{path}"
        self._path = path
        self._exception_cls = exception_cls
        self._params: dict = {}
        self._headers: dict = {}
        self._expected_status: Optional[Set[int]] = None
        self._expand_parts: List[str] = []

    def select(self, *fields: str) -> "ODataQueryBuilder":
        if fields:
            self._params["$select"] = ",".join(fields)
        return self

    def expand(self, nav: str, select: Optional[Iterable[str]] = None) -> "ODataQueryBuilder":
        if select:
            part = f"{nav}($select={','.join(select)})"
        else:
            part = nav
        self._expand_parts.append(part)
        self._params["$expand"] = ",".join(self._expand_parts)
        return self

    def filter(self, expr: str) -> "ODataQueryBuilder":
        self._params["$filter"] = expr
        return self

    def top(self, n: int) -> "ODataQueryBuilder":
        self._params["$top"] = str(n)
        return self

    def skip(self, n: int) -> "ODataQueryBuilder":
        self._params["$skip"] = str(n)
        return self

    def orderby(self, *fields: str) -> "ODataQueryBuilder":
        if fields:
            self._params["$orderby"] = ",".join(fields)
        return self

    def count(self, enabled: bool = True) -> "ODataQueryBuilder":
        """Set ``$count`` and, when enabled, ``ConsistencyLevel: eventual``."""
        if enabled:
            self._params["$count"] = "true"
            self._headers["ConsistencyLevel"] = "eventual"
        else:
            self._params.pop("$count", None)
            self._headers.pop("ConsistencyLevel", None)
        return self

    def search(self, text: str) -> "ODataQueryBuilder":
        self._params["$search"] = text
        return self

    def header(self, key: str, value: str) -> "ODataQueryBuilder":
        self._headers[key] = value
        return self

    def expect(self, *status_codes: int) -> "ODataQueryBuilder":
        if not status_codes:
            raise ValueError("expect() requires at least one status code")
        self._expected_status = set(status_codes)
        return self

    def build(self) -> ODataHTTPRequest:
        """Freeze the current configuration into an ``ODataHTTPRequest``."""
        return ODataHTTPRequest(
            client=self._client,
            path=self._path,
            params=dict(self._params),
            headers=dict(self._headers),
            expected_status=(
                frozenset(self._expected_status)
                if self._expected_status is not None
                else None
            ),
            exception_cls=self._exception_cls,
        )
