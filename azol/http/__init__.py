"""HTTP transport primitives for azol: Session, request builder, and errors."""
from azol.http.call import HttpCall
from azol.http.errors import (
    AzolAuthError,
    AzolClientError,
    AzolConflictError,
    AzolError,
    AzolForbiddenError,
    AzolHTTPError,
    AzolNotFoundError,
    AzolServerError,
    AzolThrottledError,
    exception_from_response,
)
from azol.http.request import HTTPRequest, OAuthHTTPRequest
from azol.http.request_builder import HTTPRequestBuilder, OAuthRequestBuilder
from azol.http.result import HttpResult
from azol.http.session import DEFAULT_TIMEOUT, create_session

__all__ = [
    "AzolError",
    "AzolHTTPError",
    "AzolAuthError",
    "AzolForbiddenError",
    "AzolNotFoundError",
    "AzolConflictError",
    "AzolThrottledError",
    "AzolClientError",
    "AzolServerError",
    "exception_from_response",
    "HTTPRequest",
    "OAuthHTTPRequest",
    "HTTPRequestBuilder",
    "OAuthRequestBuilder",
    "HttpCall",
    "HttpResult",
    "DEFAULT_TIMEOUT",
    "create_session",
]
