"""Prepared OData HTTP request for Microsoft Graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping, Optional, Set

from azol.clients.odata.result import GraphResult

if TYPE_CHECKING:
    from azol.clients.oauth_http_client import OAuthHTTPClient


@dataclass(frozen=True)
class ODataHTTPRequest:
    """Immutable OData GET ready to ``execute()`` into a ``GraphResult``."""

    client: "OAuthHTTPClient"
    path: str
    params: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    expected_status: Optional[Set[int]] = None
    exception_cls: Optional[type] = None

    def execute(self) -> GraphResult:
        """Send the request and wrap the first page as ``GraphResult``."""
        builder = (
            self.client.request(exception_cls=self.exception_cls)
            .path(self.path)
            .params(dict(self.params))
            .headers(dict(self.headers))
        )
        if self.expected_status is not None:
            builder.expect(*self.expected_status)
        else:
            builder.expect(200)
        response = builder.get().execute()
        return GraphResult(
            response,
            client=self.client,
            exception_cls=self.exception_cls,
            expected_status=self.expected_status or frozenset({200}),
            headers=dict(self.headers),
        )
