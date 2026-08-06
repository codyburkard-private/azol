"""Unit tests for generic HttpCall facade."""
import unittest
from unittest.mock import MagicMock

import requests

from azol.http import HttpCall, HttpResult, OAuthRequestBuilder


def _mock_response(status_code=200, payload=None, url="https://example.com/x"):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.url = url
    response.headers = {}
    response.request = MagicMock()
    response.request.method = "GET"
    response.json.return_value = payload if payload is not None else {"value": []}
    response.text = str(payload)
    response.content = b"raw-bytes"
    return response


class FakeClient:
    def __init__(self, base_url="https://example.com"):
        self._session = MagicMock(spec=requests.Session)
        self._session.request.return_value = _mock_response(
            payload={"value": [{"id": "1"}]}
        )
        self._base_url = base_url

    def request(self, exception_cls=None):
        return OAuthRequestBuilder(
            self._session,
            ensure_token=lambda: "access-token",
            user_agent="azol-test",
            base_url=self._base_url,
            exception_cls=exception_cls,
        )


class HttpCallTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()

    def test_api_version_and_filter(self):
        HttpCall(self.client, "/items").api_version("7.1").filter("a eq 1").get()
        kwargs = self.client._session.request.call_args.kwargs
        url = self.client._session.request.call_args.args[1]
        self.assertEqual(url, "https://example.com/items")
        self.assertEqual(kwargs["params"]["api-version"], "7.1")
        self.assertEqual(kwargs["params"]["$filter"], "a eq 1")

    def test_values_pages_next_link(self):
        first = _mock_response(
            payload={
                "value": [{"id": "1"}],
                "nextLink": "https://example.com/items?skip=1",
            }
        )
        second = _mock_response(payload={"value": [{"id": "2"}]})
        self.client._session.request.side_effect = [first, second]

        items = HttpCall(self.client, "/items").api_version("7.1").get().values()
        self.assertEqual(items, [{"id": "1"}, {"id": "2"}])
        self.assertEqual(self.client._session.request.call_count, 2)
        self.assertEqual(
            self.client._session.request.call_args_list[1].args[1],
            "https://example.com/items?skip=1",
        )

    def test_values_without_paging(self):
        first = _mock_response(
            payload={
                "value": [{"id": "1"}],
                "nextLink": "https://example.com/items?skip=1",
            }
        )
        self.client._session.request.return_value = first
        items = (
            HttpCall(self.client, "/items", next_link_key=None)
            .get()
            .values()
        )
        self.assertEqual(items, [{"id": "1"}])
        self.assertEqual(self.client._session.request.call_count, 1)

    def test_absolute_url(self):
        HttpCall(self.client).url("https://other.example/api").api_version("1").get()
        url = self.client._session.request.call_args.args[1]
        self.assertEqual(url, "https://other.example/api")

    def test_post_expect_and_body(self):
        self.client._session.request.return_value = _mock_response(
            status_code=202, payload={"ok": True}
        )
        body = (
            HttpCall(self.client, "/reports")
            .body({"a": 1})
            .expect(202)
            .post()
            .json()
        )
        self.assertEqual(body["ok"], True)
        call = self.client._session.request.call_args
        self.assertEqual(call.args[0], "POST")
        self.assertEqual(call.kwargs["json"], {"a": 1})

    def test_content_accessor(self):
        result = HttpCall(self.client, "/file").get()
        self.assertEqual(result.content, b"raw-bytes")
        self.assertIsInstance(result, HttpResult)

    def test_leading_slash_normalized(self):
        HttpCall(self.client, "org/_apis/projects").get()
        url = self.client._session.request.call_args.args[1]
        self.assertEqual(url, "https://example.com/org/_apis/projects")


if __name__ == "__main__":
    unittest.main()
