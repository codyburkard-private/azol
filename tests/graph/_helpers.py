"""Shared helpers for GraphClient offline tests."""
from unittest.mock import MagicMock

import requests

from azol.clients.graph_client import GraphClient
from azol.http.session import DEFAULT_TIMEOUT


def mock_response(status_code=200, payload=None, url="https://graph.microsoft.com/beta/x"):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.url = url
    response.headers = {}
    response.request = MagicMock()
    response.request.method = "GET"
    if payload is None and status_code == 204:
        response.content = b""
        response.text = ""
        response.json.side_effect = ValueError("No JSON")
    else:
        body = payload if payload is not None else {"value": []}
        response.json.return_value = body
        response.text = str(body)
        response.content = b"{}" if body is not None else b""
    return response


def make_graph_client(session=None):
    """Build a GraphClient without running OAuthHTTPClient.__init__."""
    client = GraphClient.__new__(GraphClient)
    client._session = session if session is not None else MagicMock(spec=requests.Session)
    client._baseurl = "https://graph.microsoft.com/beta"
    client._useragent = "azol-test"
    client._request_timeout = DEFAULT_TIMEOUT
    client._ensure_access_token = lambda: "access-token"
    client._owns_session = False
    return client


def last_call(session):
    return session.request.call_args


def last_method(session):
    return session.request.call_args.args[0]


def last_url(session):
    return session.request.call_args.args[1]


def last_params(session):
    return session.request.call_args.kwargs.get("params") or {}


def last_json(session):
    return session.request.call_args.kwargs.get("json")
