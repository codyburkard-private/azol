"""Session factory helpers for azol HTTP clients."""
from __future__ import annotations

from typing import Optional

import requests


DEFAULT_TIMEOUT = 10


def create_session(
    user_agent: Optional[str] = None,
    *,
    extra_headers: Optional[dict] = None,
) -> requests.Session:
    """Create a ``requests.Session`` with library defaults.

    Args:
        user_agent: Optional default User-Agent header for all requests.
        extra_headers: Optional additional default headers.

    Returns:
        A configured ``requests.Session``.
    """
    session = requests.Session()
    if user_agent:
        session.headers["User-Agent"] = user_agent
    if extra_headers:
        session.headers.update(extra_headers)
    return session
