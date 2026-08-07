"""Unified fluent Graph call facade for GET (OData) and mutations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, List, Mapping, Optional, Set

from azol.clients.odata.request import ODataHTTPRequest
from azol.clients.odata.result import GraphResult

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


class GraphCall:
    """Fluent Graph request configurator.

    Configure OData options and/or a JSON body, then terminate with a verb
    (``get`` / ``post`` / ``put`` / ``patch`` / ``delete``) to execute.
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
        self._json: Any = None
        self._data: Any = None

    def select(self, *fields: str) -> "GraphCall":
        if fields:
            self._params["$select"] = ",".join(fields)
        return self

    def expand(self, nav: str, select: Optional[Iterable[str]] = None) -> "GraphCall":
        if select:
            part = f"{nav}($select={','.join(select)})"
        else:
            part = nav
        self._expand_parts.append(part)
        self._params["$expand"] = ",".join(self._expand_parts)
        return self

    def filter(self, expr: str) -> "GraphCall":
        self._params["$filter"] = expr
        return self

    def top(self, n: int) -> "GraphCall":
        self._params["$top"] = str(n)
        return self

    def skip(self, n: int) -> "GraphCall":
        self._params["$skip"] = str(n)
        return self

    def orderby(self, *fields: str) -> "GraphCall":
        if fields:
            self._params["$orderby"] = ",".join(fields)
        return self

    def count(self, enabled: bool = True) -> "GraphCall":
        if enabled:
            self._params["$count"] = "true"
            self._headers["ConsistencyLevel"] = "eventual"
        else:
            self._params.pop("$count", None)
            self._headers.pop("ConsistencyLevel", None)
        return self

    def search(self, text: str) -> "GraphCall":
        self._params["$search"] = text
        return self

    def header(self, key: str, value: str) -> "GraphCall":
        self._headers[key] = value
        return self

    def headers(self, headers: Optional[Mapping[str, str]]) -> "GraphCall":
        if headers:
            self._headers.update(headers)
        return self

    def params(self, params: Optional[Mapping[str, Any]]) -> "GraphCall":
        if params:
            self._params.update(params)
        return self

    def body(self, payload: Any) -> "GraphCall":
        """Set a JSON request body (alias of ``json``)."""
        return self.json(payload)

    def json(self, payload: Any) -> "GraphCall":
        self._json = payload
        return self

    def data(self, data: Any) -> "GraphCall":
        self._data = data
        return self

    def expect(self, *status_codes: int) -> "GraphCall":
        if not status_codes:
            raise ValueError("expect() requires at least one status code")
        self._expected_status = set(status_codes)
        return self

    def get(self) -> GraphResult:
        expected = self._expected_status or frozenset({200})
        request = ODataHTTPRequest(
            client=self._client,
            path=self._path,
            params=dict(self._params),
            headers=dict(self._headers),
            expected_status=frozenset(expected),
            exception_cls=self._exception_cls,
        )
        odata_response = request.execute()
        return GraphResult(
            odata_response.response,
            client=self._client,
            exception_cls=self._exception_cls,
            expected_status=frozenset(expected),
            headers=dict(self._headers),
        )

    def post(self) -> GraphResult:
        return self._mutate("POST")

    def put(self) -> GraphResult:
        return self._mutate("PUT")

    def patch(self) -> GraphResult:
        return self._mutate("PATCH")

    def delete(self) -> GraphResult:
        return self._mutate("DELETE")

    _DEFAULT_MUTATE_STATUS = {
        "POST": frozenset({200, 201, 204}),
        "PUT": frozenset({200, 201, 204}),
        "PATCH": frozenset({200, 204}),
        "DELETE": frozenset({200, 204}),
    }

    def _mutate(self, method: str) -> GraphResult:
        expected = self._expected_status or self._DEFAULT_MUTATE_STATUS[method]
        builder = (
            self._client.request(exception_cls=self._exception_cls)
            .path(self._path)
            .params(dict(self._params) if self._params else None)
            .headers(dict(self._headers))
            .expect(*expected)
        )
        if self._json is not None:
            builder.json(self._json)
        if self._data is not None:
            builder.data(self._data)
        verb = getattr(builder, method.lower())
        http_request = verb()
        response = http_request.execute()
        return GraphResult(
            response,
            client=self._client,
            exception_cls=self._exception_cls,
            expected_status=frozenset(expected),
            headers=dict(self._headers),
        )
