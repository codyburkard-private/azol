"""Prepared HTTP request objects produced by builders."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Set, Union

import requests

from azol.http.errors import exception_from_response
from azol.http.session import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HTTPRequest:
    """An immutable description of an HTTP call, ready to ``execute()``."""

    session: requests.Session
    method: str
    url: str
    params: Optional[Mapping[str, Any]] = None
    data: Any = None
    json: Any = None
    headers: Mapping[str, str] = field(default_factory=dict)
    cookies: Optional[Mapping[str, str]] = None
    timeout: Union[float, tuple] = DEFAULT_TIMEOUT
    allow_redirects: bool = True
    expected_status: Optional[Set[int]] = None
    raise_on_error: bool = True
    exception_cls: Optional[type] = None

    def execute(self) -> requests.Response:
        """Send this request via its bound session and apply error policy."""
        headers = dict(self.headers)
        response = self.session.request(
            self.method,
            self.url,
            params=self.params,
            data=self.data,
            json=self.json,
            headers=headers,
            cookies=self.cookies,
            timeout=self.timeout,
            allow_redirects=self.allow_redirects,
        )
        return self._apply_error_policy(response)

    def _apply_error_policy(self, response: requests.Response) -> requests.Response:
        if not self.raise_on_error:
            return response

        expected = self.expected_status
        if expected is None:
            if 200 <= response.status_code < 300:
                return response
            expected = set()

        if response.status_code in expected:
            return response

        error = exception_from_response(
            response, exception_cls=self.exception_cls
        )
        logger.error(
            "HTTP request failed: %s %s -> %s. Body: %s",
            self.method,
            self.url,
            response.status_code,
            getattr(error, "body_snippet", None),
        )
        raise error


@dataclass(frozen=True)
class OAuthHTTPRequest(HTTPRequest):
    """HTTP request that injects a bearer token (and optional UA) on execute."""

    ensure_token: Optional[Callable[[], str]] = None
    user_agent: Optional[str] = None
    skip_auth: bool = False

    def execute(self) -> requests.Response:
        headers = dict(self.headers)
        if not self.skip_auth:
            if self.ensure_token is None:
                raise ValueError("OAuthHTTPRequest requires ensure_token unless skip_auth=True")
            headers["Authorization"] = f"Bearer {self.ensure_token()}"
        if self.user_agent:
            headers["User-Agent"] = self.user_agent

        response = self.session.request(
            self.method,
            self.url,
            params=self.params,
            data=self.data,
            json=self.json,
            headers=headers,
            cookies=self.cookies,
            timeout=self.timeout,
            allow_redirects=self.allow_redirects,
        )
        return self._apply_error_policy(response)
