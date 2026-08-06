"""Unit tests for Graph OData query builder."""
import unittest
from unittest.mock import MagicMock

import requests

from azol.clients.odata import ODataHTTPRequest, ODataQueryBuilder, ODataResponse
from azol.http import OAuthRequestBuilder


def _mock_response(status_code=200, payload=None, url="https://graph.microsoft.com/beta/users"):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.url = url
    response.headers = {}
    response.request = MagicMock()
    response.request.method = "GET"
    response.json.return_value = payload if payload is not None else {"value": []}
    response.text = str(payload)
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


class ODataQueryBuilderTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeGraphClient()

    def test_build_performs_no_io(self):
        request = (
            ODataQueryBuilder(self.client, "/servicePrincipals")
            .select("id", "displayName")
            .build()
        )
        self.assertIsInstance(request, ODataHTTPRequest)
        self.client._session.request.assert_not_called()

    def test_select_and_expand_params(self):
        request = (
            ODataQueryBuilder(self.client, "/servicePrincipals")
            .select("id", "displayName", "owners")
            .expand("owners", select=("id", "displayName"))
            .build()
        )
        self.assertEqual(request.path, "/servicePrincipals")
        self.assertEqual(request.params["$select"], "id,displayName,owners")
        self.assertEqual(
            request.params["$expand"], "owners($select=id,displayName)"
        )
        self.assertNotIn("?", request.path)

    def test_count_sets_consistency_level(self):
        request = (
            ODataQueryBuilder(self.client, "/users")
            .filter("startsWith(userPrincipalName, 'a')")
            .count(True)
            .build()
        )
        self.assertEqual(request.params["$count"], "true")
        self.assertEqual(request.params["$filter"], "startsWith(userPrincipalName, 'a')")
        self.assertEqual(request.headers["ConsistencyLevel"], "eventual")

    def test_filter_only_does_not_force_select(self):
        request = (
            ODataQueryBuilder(self.client, "/users")
            .filter("id eq 'x'")
            .build()
        )
        self.assertNotIn("$select", request.params)
        self.assertEqual(request.params["$filter"], "id eq 'x'")

    def test_execute_returns_odata_response(self):
        result = (
            ODataQueryBuilder(self.client, "/users")
            .select("id")
            .build()
            .execute()
        )
        self.assertIsInstance(result, ODataResponse)
        kwargs = self.client._session.request.call_args.kwargs
        self.assertEqual(kwargs["params"]["$select"], "id")
        self.assertEqual(
            self.client._session.request.call_args.args[1],
            "https://graph.microsoft.com/beta/users",
        )


class ODataResponsePagingTests(unittest.TestCase):
    def test_values_follows_next_link(self):
        client = FakeGraphClient()
        first = _mock_response(
            payload={
                "value": [{"id": "1"}],
                "@odata.nextLink": "https://graph.microsoft.com/beta/users?$skiptoken=abc",
            }
        )
        second = _mock_response(payload={"value": [{"id": "2"}]})
        client._session.request.side_effect = [first, second]

        result = ODataQueryBuilder(client, "/users").build().execute()
        items = result.values()

        self.assertEqual(items, [{"id": "1"}, {"id": "2"}])
        self.assertEqual(client._session.request.call_count, 2)
        second_url = client._session.request.call_args_list[1].args[1]
        self.assertEqual(
            second_url,
            "https://graph.microsoft.com/beta/users?$skiptoken=abc",
        )


if __name__ == "__main__":
    unittest.main()
