"""Generic fluent HTTP call facade for OAuthHTTPClient subclasses."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional, Set

from azol.http.result import HttpResult

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


class HttpCall:
    """Fluent request configurator bound to an ``OAuthHTTPClient``.

    Configure query params / body / expected status, then terminate with a verb
    (``get`` / ``post`` / ``put`` / ``patch`` / ``delete``) to execute.
    """

    def __init__(
        self,
        client: "OAuthHTTPClient",
        path: Optional[str] = None,
        *,
        url: Optional[str] = None,
        exception_cls: Optional[type] = None,
        next_link_key: Optional[str] = "nextLink",
    ):
        self._client = client
        self._path: Optional[str] = None
        self._absolute_url: Optional[str] = url
        if path is not None:
            if path and not path.startswith("/"):
                path = f"/{path}"
            self._path = path
            self._absolute_url = None
        self._exception_cls = exception_cls
        self._next_link_key = next_link_key
        self._params: dict = {}
        self._headers: dict = {}
        self._expected_status: Optional[Set[int]] = None
        self._json: Any = None
        self._data: Any = None

    def path(self, path: str) -> "HttpCall":
        if path and not path.startswith("/"):
            path = f"/{path}"
        self._path = path
        self._absolute_url = None
        return self

    def url(self, url: str) -> "HttpCall":
        """Use an absolute URL (ignores the client's base URL)."""
        self._absolute_url = url
        self._path = None
        return self

    def api_version(self, version: str) -> "HttpCall":
        self._params["api-version"] = version
        return self

    def filter(self, expr: str) -> "HttpCall":
        self._params["$filter"] = expr
        return self

    def param(self, key: str, value: Any) -> "HttpCall":
        self._params[key] = value
        return self

    def params(self, params: Optional[Mapping[str, Any]]) -> "HttpCall":
        if params:
            self._params.update(params)
        return self

    def header(self, key: str, value: str) -> "HttpCall":
        self._headers[key] = value
        return self

    def headers(self, headers: Optional[Mapping[str, str]]) -> "HttpCall":
        if headers:
            self._headers.update(headers)
        return self

    def body(self, payload: Any) -> "HttpCall":
        return self.json(payload)

    def json(self, payload: Any) -> "HttpCall":
        self._json = payload
        return self

    def data(self, data: Any) -> "HttpCall":
        self._data = data
        return self

    def expect(self, *status_codes: int) -> "HttpCall":
        if not status_codes:
            raise ValueError("expect() requires at least one status code")
        self._expected_status = set(status_codes)
        return self

    def get(self) -> HttpResult:
        return self._execute("GET")

    def post(self) -> HttpResult:
        return self._execute("POST")

    def put(self) -> HttpResult:
        return self._execute("PUT")

    def patch(self) -> HttpResult:
        return self._execute("PATCH")

    def delete(self) -> HttpResult:
        return self._execute("DELETE")

    def _execute(self, method: str) -> HttpResult:
        if self._absolute_url is None and self._path is None:
            raise ValueError("Request URL is not set; call path() or url()")
        expected = self._expected_status or frozenset({200})
        builder = (
            self._client.request(exception_cls=self._exception_cls)
            .params(dict(self._params) if self._params else None)
            .headers(dict(self._headers))
            .expect(*expected)
        )
        if self._absolute_url is not None:
            builder.url(self._absolute_url)
        else:
            builder.path(self._path)
        if self._json is not None:
            builder.json(self._json)
        if self._data is not None:
            builder.data(self._data)
        verb = getattr(builder, method.lower())
        response = verb().execute()
        return HttpResult(
            response,
            client=self._client,
            exception_cls=self._exception_cls,
            expected_status=frozenset(expected),
            headers=dict(self._headers),
            next_link_key=self._next_link_key,
        )
