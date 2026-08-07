"""Ephemeral mutate live tests (does not destroy seeded harness states).

Always attempts when Azure CLI can mint a Graph token. Skips if not ready.
Uses ``azol-ephemeral-*`` names only.
"""
from __future__ import annotations

import uuid
import unittest

from azol.http.errors import AzolHTTPError
from azol.http.request import suppress_http_error_logging

from graph.live.harness.config import EPHEMERAL_PREFIX
from graph.live.live_helpers import (
    LiveGraphTestCase,
    eventually,
    skip_unavailable_graph,
)


class GraphLiveMutateTests(LiveGraphTestCase):
    def test_create_and_cleanup_ephemeral_sp(self):
        name = f"{EPHEMERAL_PREFIX}{uuid.uuid4().hex[:12]}"
        try:
            created = self.client.create_new_local_service_principal(name=name)
        except Exception as exc:
            skip_unavailable_graph(self, exc)
            return
        self.addCleanup(self._cleanup_sp, created)
        self.assertTrue(created["appObjectId"])

        def _sp():
            try:
                sp = self.client.get_service_principal(object_id=created["spId"])
            except AzolHTTPError as exc:
                if getattr(exc, "status_code", None) == 404:
                    return None
                raise
            if sp.get("id") != created["spId"]:
                return None
            if sp.get("displayName") != name:
                return None
            return sp

        def _app():
            try:
                app = self.client.get_application(object_id=created["appObjectId"])
            except AzolHTTPError as exc:
                if getattr(exc, "status_code", None) == 404:
                    return None
                raise
            if app.get("id") != created["appObjectId"]:
                return None
            if app.get("displayName") != name:
                return None
            return app

        with suppress_http_error_logging():
            sp = eventually(_sp, label="ephemeral service principal")
            app = eventually(_app, label="ephemeral application")
        self.assertIsNotNone(sp, f"service principal not readable; created={created}")
        self.assertIsNotNone(app, f"application not readable; created={created}")

    def _cleanup_sp(self, created):
        with suppress_http_error_logging():
            try:
                self.client.delete(f"/servicePrincipals/{created['spId']}")
            except Exception:
                pass
            try:
                self.client.delete(f"/applications/{created['appObjectId']}")
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
