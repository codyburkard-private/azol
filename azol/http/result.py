"""Result of a fluent HTTP call with optional nextLink-style paging."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Set

import requests

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


class HttpResult:
    """Wraps a ``requests.Response`` and can follow a JSON next-link field."""

    def __init__(
        self,
        response: requests.Response,
        *,
        client: "OAuthHTTPClient",
        exception_cls: Optional[type] = None,
        expected_status: Optional[Set[int]] = None,
        headers: Optional[dict] = None,
        next_link_key: Optional[str] = "nextLink",
    ):
        self.response = response
        self._client = client
        self._exception_cls = exception_cls
        self._expected_status = expected_status
        self._headers = dict(headers) if headers else {}
        self._next_link_key = next_link_key

    def json(self) -> Any:
        """Return the deserialized JSON body of the first (or only) response."""
        return self.response.json()

    @property
    def content(self) -> bytes:
        return self.response.content

    @property
    def text(self) -> str:
        return self.response.text

    def values(self) -> List[Any]:
        """Return all ``value`` items, following ``next_link_key`` until exhausted.

        If ``next_link_key`` is ``None``, only the first page is returned.
        """
        all_objects: List[Any] = []
        response = self.response
        while True:
            body = response.json()
            all_objects.extend(body.get("value", []))
            if not self._next_link_key:
                break
            next_link = body.get(self._next_link_key)
            if not next_link:
                break
            response = self._fetch_next(next_link)
        return all_objects

    def _fetch_next(self, next_link: str) -> requests.Response:
        builder = (
            self._client.request(exception_cls=self._exception_cls)
            .url(next_link)
            .headers(self._headers)
        )
        if self._expected_status is not None:
            builder.expect(*self._expected_status)
        return builder.get().execute()
