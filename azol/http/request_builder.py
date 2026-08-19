"""Fluent builders that produce prepared ``HTTPRequest`` objects."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, Optional, Set, Union

import requests

from azol.http.request import HTTPRequest, OAuthHTTPRequest
from azol.http.session import DEFAULT_TIMEOUT


def is_absolute_http_url(value: str) -> bool:
    """Return True if *value* is an http(s) URL rather than a relative path."""
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def normalize_request_path(path: str) -> str:
    """Return a path (or absolute URL) suitable for :meth:`HTTPRequestBuilder.path`.

    Absolute http(s) URLs are left unchanged so callers can pass Graph
    ``@odata.nextLink`` values without joining them onto the client base URL.
    Relative paths get a leading slash.
    """
    if is_absolute_http_url(path):
        return path
    if not path.startswith("/"):
        return f"/{path}"
    return path


class HTTPRequestBuilder:
    """Accumulate request options and ``build()`` an ``HTTPRequest``.

    The builder never performs I/O. Terminal verb helpers (``get``, ``post``,
    …) set the method/path and return a prepared request; call ``execute()``
    on that object to send it::

        request = (
            HTTPRequestBuilder(session, base_url="https://example.com")
            .params({"top": 10})
            .expect(200)
            .get("/items")
        )
        response = request.execute()
    """

    def __init__(
        self,
        session: requests.Session,
        *,
        base_url: Optional[str] = None,
        default_timeout: Union[float, tuple] = DEFAULT_TIMEOUT,
        exception_cls: Optional[type] = None,
    ):
        self._session = session
        self._base_url = (base_url or "").rstrip("/")
        self._default_timeout = default_timeout
        self._exception_cls = exception_cls

        self._method: str = "GET"
        self._path: Optional[str] = None
        self._absolute_url: Optional[str] = None
        self._params: Optional[dict] = None
        self._json: Any = None
        self._data: Any = None
        self._headers: dict = {}
        self._cookies: Optional[dict] = None
        self._timeout: Optional[Union[float, tuple]] = None
        self._allow_redirects: bool = True
        self._expected_status: Optional[Set[int]] = None
        self._raise_on_error: bool = True

    def method(self, method: str) -> "HTTPRequestBuilder":
        self._method = method.upper()
        return self

    def get(self, path: Optional[str] = None) -> HTTPRequest:
        return self._verb("GET", path)

    def post(self, path: Optional[str] = None) -> HTTPRequest:
        return self._verb("POST", path)

    def put(self, path: Optional[str] = None) -> HTTPRequest:
        return self._verb("PUT", path)

    def patch(self, path: Optional[str] = None) -> HTTPRequest:
        return self._verb("PATCH", path)

    def delete(self, path: Optional[str] = None) -> HTTPRequest:
        return self._verb("DELETE", path)

    def _verb(self, method: str, path: Optional[str]) -> HTTPRequest:
        self._method = method
        if path is not None:
            self.path(path)
        return self.build()

    def path(self, path: str) -> "HTTPRequestBuilder":
        """Set a path relative to ``base_url``.

        Absolute ``http://`` / ``https://`` values are treated as complete URLs
        (same as :meth:`url`) so Graph ``@odata.nextLink`` is not joined onto
        ``https://graph.microsoft.com/beta``.
        """
        if is_absolute_http_url(path):
            return self.url(path)
        self._path = normalize_request_path(path)
        self._absolute_url = None
        return self

    def url(self, url: str) -> "HTTPRequestBuilder":
        """Set an absolute URL (ignores ``base_url``)."""
        self._absolute_url = url
        self._path = None
        return self

    def params(self, params: Optional[Mapping[str, Any]]) -> "HTTPRequestBuilder":
        self._params = dict(params) if params is not None else None
        return self

    def json(self, payload: Any) -> "HTTPRequestBuilder":
        self._json = payload
        return self

    def data(self, data: Any) -> "HTTPRequestBuilder":
        self._data = data
        return self

    def headers(self, headers: Optional[Mapping[str, str]]) -> "HTTPRequestBuilder":
        """Merge headers into the request (caller mapping is not mutated)."""
        if headers:
            self._headers.update(headers)
        return self

    def header(self, key: str, value: str) -> "HTTPRequestBuilder":
        self._headers[key] = value
        return self

    def cookies(self, cookies: Optional[Mapping[str, str]]) -> "HTTPRequestBuilder":
        self._cookies = dict(cookies) if cookies is not None else None
        return self

    def timeout(self, timeout: Union[float, tuple]) -> "HTTPRequestBuilder":
        self._timeout = timeout
        return self

    def allow_redirects(self, allow: bool = True) -> "HTTPRequestBuilder":
        self._allow_redirects = allow
        return self

    def auth_bearer(self, token: str) -> "HTTPRequestBuilder":
        self._headers["Authorization"] = f"Bearer {token}"
        return self

    def expect(self, *status_codes: int) -> "HTTPRequestBuilder":
        """Declare one or more successful status codes."""
        if not status_codes:
            raise ValueError("expect() requires at least one status code")
        self._expected_status = set(status_codes)
        self._raise_on_error = True
        return self

    def expect_any(self, status_codes: Iterable[int]) -> "HTTPRequestBuilder":
        return self.expect(*status_codes)

    def raise_on_error(self, enabled: bool = True) -> "HTTPRequestBuilder":
        """Control whether unexpected status codes raise on ``execute()``."""
        self._raise_on_error = enabled
        return self

    def with_exception_cls(self, exception_cls: type) -> "HTTPRequestBuilder":
        self._exception_cls = exception_cls
        return self

    def _build_url(self) -> str:
        if self._absolute_url is not None:
            return self._absolute_url
        if self._path is None:
            if self._base_url:
                return self._base_url
            raise ValueError("Request URL is not set; call path() or url()")
        if not self._base_url:
            raise ValueError("base_url is required when using path()")
        return f"{self._base_url}{self._path}"

    def _request_kwargs(self) -> dict:
        timeout = (
            self._default_timeout if self._timeout is None else self._timeout
        )
        expected = (
            frozenset(self._expected_status)
            if self._expected_status is not None
            else None
        )
        return {
            "session": self._session,
            "method": self._method,
            "url": self._build_url(),
            "params": dict(self._params) if self._params is not None else None,
            "data": self._data,
            "json": self._json,
            "headers": dict(self._headers),
            "cookies": dict(self._cookies) if self._cookies is not None else None,
            "timeout": timeout,
            "allow_redirects": self._allow_redirects,
            "expected_status": expected,
            "raise_on_error": self._raise_on_error,
            "exception_cls": self._exception_cls,
        }

    def build(self) -> HTTPRequest:
        """Freeze the current configuration into an ``HTTPRequest``."""
        return HTTPRequest(**self._request_kwargs())


class OAuthRequestBuilder(HTTPRequestBuilder):
    """Builder that produces ``OAuthHTTPRequest`` (token injected on execute)."""

    def __init__(
        self,
        session: requests.Session,
        *,
        ensure_token: Callable[[], str],
        user_agent: Optional[str] = None,
        base_url: Optional[str] = None,
        default_timeout: Union[float, tuple] = DEFAULT_TIMEOUT,
        exception_cls: Optional[type] = None,
    ):
        super().__init__(
            session,
            base_url=base_url,
            default_timeout=default_timeout,
            exception_cls=exception_cls,
        )
        self._ensure_token = ensure_token
        self._user_agent = user_agent
        self._skip_auth = False

    def without_auth(self) -> "OAuthRequestBuilder":
        """Skip bearer token injection when the request is executed."""
        self._skip_auth = True
        return self

    def get(self, path: Optional[str] = None) -> OAuthHTTPRequest:
        return self._verb("GET", path)

    def post(self, path: Optional[str] = None) -> OAuthHTTPRequest:
        return self._verb("POST", path)

    def put(self, path: Optional[str] = None) -> OAuthHTTPRequest:
        return self._verb("PUT", path)

    def patch(self, path: Optional[str] = None) -> OAuthHTTPRequest:
        return self._verb("PATCH", path)

    def delete(self, path: Optional[str] = None) -> OAuthHTTPRequest:
        return self._verb("DELETE", path)

    def _verb(self, method: str, path: Optional[str]) -> OAuthHTTPRequest:
        self._method = method
        if path is not None:
            self.path(path)
        return self.build()

    def build(self) -> OAuthHTTPRequest:
        """Freeze the current configuration into an ``OAuthHTTPRequest``."""
        return OAuthHTTPRequest(
            **self._request_kwargs(),
            ensure_token=self._ensure_token,
            user_agent=self._user_agent,
            skip_auth=self._skip_auth,
        )
