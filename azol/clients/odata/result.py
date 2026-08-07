"""Result of a Graph API call with paging helpers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Set

import requests

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


class GraphResult:
    """Wraps a Graph ``requests.Response`` and can follow ``@odata.nextLink``."""

    def __init__(
        self,
        response: requests.Response,
        *,
        client: "OAuthHTTPClient",
        exception_cls: Optional[type] = None,
        expected_status: Optional[Set[int]] = None,
        headers: Optional[dict] = None,
    ):
        self.response = response
        self._client = client
        self._exception_cls = exception_cls
        self._expected_status = expected_status
        self._headers = dict(headers) if headers else {}

    def json(self) -> Any:
        """Return the deserialized JSON body, or ``None`` for empty/204 responses."""
        if getattr(self.response, "status_code", None) == 204:
            return None
        content = getattr(self.response, "content", None)
        if content is not None and len(content) == 0:
            return None
        return self.response.json()

    def values(self) -> List[Any]:
        """Return all ``value`` items, following ``@odata.nextLink`` until exhausted."""
        all_objects: List[Any] = []
        response = self.response
        while True:
            body = response.json()
            all_objects.extend(body.get("value", []))
            next_link = body.get("@odata.nextLink")
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


# Backward-compatible alias used by earlier OData helpers/tests.
ODataResponse = GraphResult
