"""HTTP exception hierarchy for azol library clients."""
from __future__ import annotations

from typing import Optional

import requests


class AzolError(Exception):
    """Base exception for all azol library errors."""


class AzolHTTPError(AzolError):
    """Raised when an HTTP request fails unexpectedly.

    Attributes:
        status_code: HTTP status code, if available.
        method: HTTP method used for the request.
        url: Final request URL.
        response: The raw ``requests.Response``, if available.
        body_snippet: Truncated response body for debugging.
        request_id: Azure / Graph correlation id when present.
    """

    _BODY_LIMIT = 2000

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        status_code: Optional[int] = None,
        method: Optional[str] = None,
        url: Optional[str] = None,
        response: Optional[requests.Response] = None,
        body_snippet: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.status_code = status_code
        self.method = method
        self.url = url
        self.response = response
        self.body_snippet = body_snippet
        self.request_id = request_id
        if message is None:
            message = self._default_message()
        super().__init__(message)

    def _default_message(self) -> str:
        parts = ["HTTP request failed"]
        if self.status_code is not None:
            parts.append(f"with status {self.status_code}")
        if self.method and self.url:
            parts.append(f"for {self.method} {self.url}")
        elif self.url:
            parts.append(f"for {self.url}")
        if self.request_id:
            parts.append(f"(request-id={self.request_id})")
        return " ".join(parts)

    @classmethod
    def from_response(
        cls,
        response: requests.Response,
        message: Optional[str] = None,
    ) -> "AzolHTTPError":
        """Build an exception instance from a ``requests.Response``."""
        method = None
        if response.request is not None:
            method = response.request.method

        body_snippet = None
        try:
            text = response.text
            if text:
                body_snippet = text[: cls._BODY_LIMIT]
        except Exception:  # noqa: BLE001 - best-effort body capture
            body_snippet = None

        request_id = response.headers.get("request-id") or response.headers.get(
            "x-ms-request-id"
        )

        return cls(
            message,
            status_code=response.status_code,
            method=method,
            url=response.url,
            response=response,
            body_snippet=body_snippet,
            request_id=request_id,
        )


class AzolAuthError(AzolHTTPError):
    """HTTP 401 Unauthorized."""


class AzolForbiddenError(AzolHTTPError):
    """HTTP 403 Forbidden."""


class AzolNotFoundError(AzolHTTPError):
    """HTTP 404 Not Found."""


class AzolConflictError(AzolHTTPError):
    """HTTP 409 Conflict."""


class AzolThrottledError(AzolHTTPError):
    """HTTP 429 Too Many Requests.

    Attributes:
        retry_after: Seconds to wait before retrying, if provided by the server.
    """

    def __init__(self, *args, retry_after: Optional[float] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(*args, **kwargs)

    @classmethod
    def from_response(
        cls,
        response: requests.Response,
        message: Optional[str] = None,
    ) -> "AzolThrottledError":
        retry_after = _parse_retry_after(response)
        error = super().from_response(response, message=message)
        error.retry_after = retry_after
        return error


class AzolClientError(AzolHTTPError):
    """Other HTTP 4xx client errors."""


class AzolServerError(AzolHTTPError):
    """HTTP 5xx server errors."""


_STATUS_EXCEPTION_MAP = {
    401: AzolAuthError,
    403: AzolForbiddenError,
    404: AzolNotFoundError,
    409: AzolConflictError,
    429: AzolThrottledError,
}


def _parse_retry_after(response: requests.Response) -> Optional[float]:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def exception_from_response(
    response: requests.Response,
    exception_cls: Optional[type] = None,
    message: Optional[str] = None,
) -> AzolHTTPError:
    """Map a failed response to an ``AzolHTTPError`` (or subclass).

    If ``exception_cls`` is provided (a service-specific ``AzolHTTPError``
    subclass), that type is always used. Otherwise status codes are mapped
    to the generic hierarchy (401 → ``AzolAuthError``, 400 → ``AzolClientError``,
    500 → ``AzolServerError``, etc.).
    """
    if exception_cls is not None:
        if issubclass(exception_cls, AzolHTTPError):
            return exception_cls.from_response(response, message=message)
        # Legacy Exception subclasses without from_response support.
        return exception_cls(message) if message else exception_cls()

    status = response.status_code
    mapped = _STATUS_EXCEPTION_MAP.get(status)
    if mapped is not None:
        return mapped.from_response(response, message=message)
    if 400 <= status < 500:
        return AzolClientError.from_response(response, message=message)
    if status >= 500:
        return AzolServerError.from_response(response, message=message)
    return AzolHTTPError.from_response(response, message=message)
