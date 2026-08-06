"""Unit tests for ArmCall facade."""
import unittest
from unittest.mock import MagicMock

import requests

from azol.clients.arm import ArmCall, ArmResult
from azol.http import OAuthRequestBuilder


def _mock_response(status_code=200, payload=None, url="https://management.azure.com/x"):
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


class FakeArmClient:
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
            base_url="https://management.azure.com",
            exception_cls=exception_cls,
        )


class ArmCallTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeArmClient()

    def test_api_version_query_param(self):
        ArmCall(self.client, "/tenants").api_version("2020-01-01").get()
        kwargs = self.client._session.request.call_args.kwargs
        url = self.client._session.request.call_args.args[1]
        self.assertEqual(url, "https://management.azure.com/tenants")
        self.assertEqual(kwargs["params"]["api-version"], "2020-01-01")

    def test_filter_query_param(self):
        (
            ArmCall(self.client, "/subscriptions/sub/resources")
            .api_version("2019-03-01")
            .filter("resourceType eq 'Microsoft.Storage/storageAccounts'")
            .get()
        )
        kwargs = self.client._session.request.call_args.kwargs
        self.assertEqual(
            kwargs["params"]["$filter"],
            "resourceType eq 'Microsoft.Storage/storageAccounts'",
        )
        self.assertEqual(kwargs["params"]["api-version"], "2019-03-01")

    def test_get_values_pages_next_link(self):
        first = _mock_response(
            payload={
                "value": [{"id": "1"}],
                "nextLink": "https://management.azure.com/tenants?$skiptoken=abc",
            }
        )
        second = _mock_response(payload={"value": [{"id": "2"}]})
        self.client._session.request.side_effect = [first, second]

        items = (
            ArmCall(self.client, "/tenants")
            .api_version("2020-01-01")
            .get()
            .values()
        )
        self.assertEqual(items, [{"id": "1"}, {"id": "2"}])
        self.assertEqual(self.client._session.request.call_count, 2)
        second_url = self.client._session.request.call_args_list[1].args[1]
        self.assertEqual(
            second_url,
            "https://management.azure.com/tenants?$skiptoken=abc",
        )

    def test_get_json_single_entity(self):
        self.client._session.request.return_value = _mock_response(
            payload={"id": "/subscriptions/x", "name": "x"}
        )
        body = (
            ArmCall(self.client, "/subscriptions/x")
            .api_version("2019-03-01")
            .get()
            .json()
        )
        self.assertEqual(body["id"], "/subscriptions/x")

    def test_post_sends_json_and_expect(self):
        self.client._session.request.return_value = _mock_response(
            status_code=201, payload={"id": "new"}
        )
        body = (
            ArmCall(self.client, "/subscriptions/x/providers/Microsoft.Authorization/roleAssignments/y")
            .api_version("2022-04-01")
            .body({"properties": {}})
            .expect(201)
            .post()
            .json()
        )
        self.assertEqual(body["id"], "new")
        call = self.client._session.request.call_args
        self.assertEqual(call.args[0], "POST")
        self.assertEqual(call.kwargs["json"], {"properties": {}})

    def test_put_patch_delete_verbs(self):
        self.client._session.request.return_value = _mock_response(payload={})
        ArmCall(self.client, "/x").api_version("2022-04-01").body({"a": 1}).put()
        self.assertEqual(self.client._session.request.call_args.args[0], "PUT")

        ArmCall(self.client, "/x").api_version("2022-04-01").body({"a": 2}).patch()
        self.assertEqual(self.client._session.request.call_args.args[0], "PATCH")

        ArmCall(self.client, "/x").api_version("2022-04-01").delete()
        self.assertEqual(self.client._session.request.call_args.args[0], "DELETE")

    def test_result_type(self):
        result = ArmCall(self.client, "/tenants").api_version("2020-01-01").get()
        self.assertIsInstance(result, ArmResult)


if __name__ == "__main__":
    unittest.main()
