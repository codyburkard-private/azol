"""Unified fluent ARM call facade for GET and mutations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional, Set

from azol.clients.arm.result import ArmResult

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


class ArmCall:
    """Fluent ARM request configurator.

    Configure ``api-version``, filters, and body, then terminate with a verb
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
        if path and not path.startswith("/"):
            path = f"/{path}"
        self._path = path
        self._exception_cls = exception_cls
        self._params: dict = {}
        self._headers: dict = {}
        self._expected_status: Optional[Set[int]] = None
        self._json: Any = None
        self._data: Any = None

    def api_version(self, version: str) -> "ArmCall":
        self._params["api-version"] = version
        return self

    def filter(self, expr: str) -> "ArmCall":
        self._params["$filter"] = expr
        return self

    def param(self, key: str, value: Any) -> "ArmCall":
        self._params[key] = value
        return self

    def params(self, params: Optional[Mapping[str, Any]]) -> "ArmCall":
        if params:
            self._params.update(params)
        return self

    def header(self, key: str, value: str) -> "ArmCall":
        self._headers[key] = value
        return self

    def headers(self, headers: Optional[Mapping[str, str]]) -> "ArmCall":
        if headers:
            self._headers.update(headers)
        return self

    def body(self, payload: Any) -> "ArmCall":
        return self.json(payload)

    def json(self, payload: Any) -> "ArmCall":
        self._json = payload
        return self

    def data(self, data: Any) -> "ArmCall":
        self._data = data
        return self

    def expect(self, *status_codes: int) -> "ArmCall":
        if not status_codes:
            raise ValueError("expect() requires at least one status code")
        self._expected_status = set(status_codes)
        return self

    def get(self) -> ArmResult:
        return self._execute("GET")

    def post(self) -> ArmResult:
        return self._execute("POST")

    def put(self) -> ArmResult:
        return self._execute("PUT")

    def patch(self) -> ArmResult:
        return self._execute("PATCH")

    def delete(self) -> ArmResult:
        return self._execute("DELETE")

    def _execute(self, method: str) -> ArmResult:
        expected = self._expected_status or frozenset({200})
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
        response = verb().execute()
        return ArmResult(
            response,
            client=self._client,
            exception_cls=self._exception_cls,
            expected_status=frozenset(expected),
            headers=dict(self._headers),
        )
