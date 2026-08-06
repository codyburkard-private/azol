"""Unit tests for GraphCall facade."""
import unittest
from unittest.mock import MagicMock

import requests

from azol.clients.odata import GraphCall, GraphResult
from azol.http import OAuthRequestBuilder


def _mock_response(status_code=200, payload=None, url="https://graph.microsoft.com/beta/x"):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.url = url
    response.headers = {}
    response.request = MagicMock()
    response.request.method = "GET"
    response.json.return_value = payload if payload is not None else {"value": []}
    response.text = str(payload)
    response.content = b"{}"
    return response


class FakeGraphClient:
    def __init__(self):
        self._session = MagicMock(spec=requests.Session)
        self._session.request.return_value = _mock_response(
            payload={"value": [{"id": "1"}]}
        )

    def request(self, exception_cls=None):
        return OAuthRequestBuilder(
            self._session,
            ensure_token=lambda: "access-token",
            user_agent="azol-test",
            base_url="https://graph.microsoft.com/beta",
            exception_cls=exception_cls,
        )


class GraphCallTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeGraphClient()

    def test_get_values_pages_next_link(self):
        first = _mock_response(
            payload={
                "value": [{"id": "1"}],
                "@odata.nextLink": "https://graph.microsoft.com/beta/users?$skiptoken=abc",
            }
        )
        second = _mock_response(payload={"value": [{"id": "2"}]})
        self.client._session.request.side_effect = [first, second]

        items = (
            GraphCall(self.client, "/users")
            .select("id")
            .get()
            .values()
        )
        self.assertEqual(items, [{"id": "1"}, {"id": "2"}])
        self.assertEqual(self.client._session.request.call_count, 2)

    def test_get_json_single_entity(self):
        self.client._session.request.return_value = _mock_response(
            payload={"id": "abc", "displayName": "x"}
        )
        body = GraphCall(self.client, "/directoryObjects/abc").get().json()
        self.assertEqual(body["id"], "abc")

    def test_post_sends_json_and_expect(self):
        self.client._session.request.return_value = _mock_response(
            status_code=201, payload={"id": "new"}
        )
        body = (
            GraphCall(self.client, "/applications")
            .body({"displayName": "app"})
            .expect(201)
            .post()
            .json()
        )
        self.assertEqual(body["id"], "new")
        call = self.client._session.request.call_args
        self.assertEqual(call.args[0], "POST")
        self.assertEqual(call.kwargs["json"], {"displayName": "app"})

    def test_put_patch_delete_verbs(self):
        self.client._session.request.return_value = _mock_response(payload={})
        GraphCall(self.client, "/x").body({"a": 1}).put()
        self.assertEqual(self.client._session.request.call_args.args[0], "PUT")

        GraphCall(self.client, "/x").body({"a": 2}).patch()
        self.assertEqual(self.client._session.request.call_args.args[0], "PATCH")

        GraphCall(self.client, "/x").delete()
        self.assertEqual(self.client._session.request.call_args.args[0], "DELETE")

    def test_odata_params_not_in_path(self):
        GraphCall(self.client, "/users").select("id", "displayName").filter("id eq '1'").get()
        kwargs = self.client._session.request.call_args.kwargs
        url = self.client._session.request.call_args.args[1]
        self.assertEqual(url, "https://graph.microsoft.com/beta/users")
        self.assertEqual(kwargs["params"]["$select"], "id,displayName")
        self.assertEqual(kwargs["params"]["$filter"], "id eq '1'")

    def test_result_type(self):
        result = GraphCall(self.client, "/users").get()
        self.assertIsInstance(result, GraphResult)


if __name__ == "__main__":
    unittest.main()
