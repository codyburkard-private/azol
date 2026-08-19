"""Unit tests for azol.http request builder and error mapping."""
import unittest
from unittest.mock import MagicMock

import requests

from azol.http import (
    AzolAuthError,
    AzolClientError,
    AzolHTTPError,
    AzolNotFoundError,
    AzolServerError,
    AzolThrottledError,
    HTTPRequest,
    HTTPRequestBuilder,
    OAuthHTTPRequest,
    OAuthRequestBuilder,
    create_session,
    exception_from_response,
)


class SampleServiceError(AzolHTTPError):
    """Stand-in for a service-specific ``AzolHTTPError`` subclass."""


def _mock_response(
    status_code=200,
    url="https://example.com/resource",
    method="GET",
    text="{}",
    headers=None,
):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.url = url
    response.text = text
    response.content = text.encode("utf-8")
    response.headers = headers or {}
    response.request = MagicMock()
    response.request.method = method
    return response


class ExceptionMappingTests(unittest.TestCase):
    def test_status_mapping(self):
        cases = [
            (401, AzolAuthError),
            (404, AzolNotFoundError),
            (429, AzolThrottledError),
            (400, AzolClientError),
            (500, AzolServerError),
        ]
        for status, expected in cases:
            with self.subTest(status=status):
                err = exception_from_response(_mock_response(status_code=status))
                self.assertIsInstance(err, expected)
                self.assertEqual(err.status_code, status)
                self.assertIn(str(status), str(err))

    def test_throttled_retry_after(self):
        err = exception_from_response(
            _mock_response(status_code=429, headers={"Retry-After": "12"})
        )
        self.assertIsInstance(err, AzolThrottledError)
        self.assertEqual(err.retry_after, 12.0)

    def test_service_exception_cls_preserved(self):
        err = exception_from_response(
            _mock_response(status_code=403, text="denied"),
            exception_cls=SampleServiceError,
        )
        self.assertIsInstance(err, SampleServiceError)
        self.assertIsInstance(err, AzolHTTPError)
        self.assertEqual(err.status_code, 403)
        self.assertEqual(err.body_snippet, "denied")

    def test_legacy_empty_service_exception_still_constructible(self):
        err = SampleServiceError()
        self.assertIsInstance(err, AzolHTTPError)


class HTTPRequestBuilderTests(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock(spec=requests.Session)
        self.session.request.return_value = _mock_response(status_code=200)

    def test_verb_builds_request_without_io(self):
        request = (
            HTTPRequestBuilder(self.session, base_url="https://graph.microsoft.com/beta")
            .params({"$top": 1})
            .header("ConsistencyLevel", "eventual")
            .expect(200)
            .get("/users")
        )
        self.assertIsInstance(request, HTTPRequest)
        self.session.request.assert_not_called()
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url, "https://graph.microsoft.com/beta/users")
        self.assertEqual(request.params, {"$top": 1})

    def test_execute_sends_via_session(self):
        response = (
            HTTPRequestBuilder(self.session, base_url="https://graph.microsoft.com/beta")
            .params({"$top": 1})
            .header("ConsistencyLevel", "eventual")
            .expect(200)
            .get("/users")
            .execute()
        )
        self.assertEqual(response.status_code, 200)
        kwargs = self.session.request.call_args
        self.assertEqual(kwargs.args[0], "GET")
        self.assertEqual(kwargs.args[1], "https://graph.microsoft.com/beta/users")
        self.assertEqual(kwargs.kwargs["params"], {"$top": 1})
        self.assertEqual(kwargs.kwargs["headers"]["ConsistencyLevel"], "eventual")
        self.assertEqual(kwargs.kwargs["timeout"], 10)

    def test_absolute_url_overrides_base(self):
        request = (
            HTTPRequestBuilder(self.session, base_url="https://graph.microsoft.com/beta")
            .url("https://graph.microsoft.com/beta/users?$skiptoken=abc")
            .raise_on_error(False)
            .get()
        )
        self.assertEqual(
            request.url,
            "https://graph.microsoft.com/beta/users?$skiptoken=abc",
        )

    def test_path_with_absolute_url_is_not_joined_to_base(self):
        next_link = "https://graph.microsoft.com/beta/groups?$skiptoken=abc"
        request = (
            HTTPRequestBuilder(self.session, base_url="https://graph.microsoft.com/beta")
            .path(next_link)
            .raise_on_error(False)
            .get()
        )
        self.assertEqual(request.url, next_link)
        self.assertNotIn("betahttps:", request.url)

    def test_expect_raises_on_mismatch(self):
        self.session.request.return_value = _mock_response(
            status_code=404, text='{"error":"missing"}'
        )
        with self.assertRaises(AzolNotFoundError) as ctx:
            (
                HTTPRequestBuilder(self.session, base_url="https://example.com")
                .expect(200)
                .get("/missing")
                .execute()
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("missing", ctx.exception.body_snippet)

    def test_raise_on_error_false_returns_error_response(self):
        self.session.request.return_value = _mock_response(status_code=500)
        response = (
            HTTPRequestBuilder(self.session, base_url="https://example.com")
            .raise_on_error(False)
            .get("/boom")
            .execute()
        )
        self.assertEqual(response.status_code, 500)

    def test_headers_are_copied_not_mutated(self):
        original = {"X-Custom": "1"}
        request = (
            HTTPRequestBuilder(self.session, base_url="https://example.com")
            .headers(original)
            .auth_bearer("tok")
            .raise_on_error(False)
            .get("/x")
        )
        self.assertNotIn("Authorization", original)
        request.execute()
        sent_headers = self.session.request.call_args.kwargs["headers"]
        self.assertEqual(sent_headers["Authorization"], "Bearer tok")
        self.assertEqual(sent_headers["X-Custom"], "1")

    def test_default_2xx_accepted_without_expect(self):
        self.session.request.return_value = _mock_response(status_code=201)
        response = (
            HTTPRequestBuilder(self.session, base_url="https://example.com")
            .post("/created")
            .execute()
        )
        self.assertEqual(response.status_code, 201)

    def test_service_exception_cls_on_builder(self):
        self.session.request.return_value = _mock_response(status_code=400, text="bad")
        with self.assertRaises(SampleServiceError):
            (
                HTTPRequestBuilder(
                    self.session,
                    base_url="https://example.com",
                    exception_cls=SampleServiceError,
                )
                .expect(200)
                .get("/bad")
                .execute()
            )

    def test_method_plus_build_for_arbitrary_verbs(self):
        request = (
            HTTPRequestBuilder(self.session, base_url="https://example.com")
            .path("/x")
            .raise_on_error(False)
            .method("OPTIONS")
            .build()
        )
        self.assertEqual(request.method, "OPTIONS")
        request.execute()
        self.assertEqual(self.session.request.call_args.args[0], "OPTIONS")


class OAuthRequestBuilderTests(unittest.TestCase):
    def test_injects_bearer_and_user_agent_on_execute(self):
        session = MagicMock(spec=requests.Session)
        session.request.return_value = _mock_response(status_code=200)
        ensure = MagicMock(return_value="access-token")

        request = (
            OAuthRequestBuilder(
                session,
                ensure_token=ensure,
                user_agent="azol-test",
                base_url="https://example.com",
            )
            .raise_on_error(False)
            .get("/me")
        )
        self.assertIsInstance(request, OAuthHTTPRequest)
        ensure.assert_not_called()

        request.execute()
        ensure.assert_called_once()
        headers = session.request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer access-token")
        self.assertEqual(headers["User-Agent"], "azol-test")


class SessionFactoryTests(unittest.TestCase):
    def test_create_session_sets_user_agent(self):
        session = create_session(user_agent="azol-ua")
        try:
            self.assertEqual(session.headers["User-Agent"], "azol-ua")
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
