"""Live-tenant GraphClient tests against harness-seeded fixtures.

Always attempts to run. Skips with a clear reason when Azure CLI / token /
manifest fixtures are not ready, or when a capability API is unavailable.
Opt out with ``AZOL_LIVE_GRAPH=0``.
"""
from __future__ import annotations

import unittest

from graph.live.live_helpers import (
    LiveGraphTestCase,
    eventually,
    probe_or_skip,
    require_manifest_state,
)


class GraphLiveCoreTests(LiveGraphTestCase):
    def test_organization(self):
        org_state = require_manifest_state(self, "organization")
        orgs = self.client.get_organization()
        self.assertIsInstance(orgs, list)
        self.assertTrue(orgs)
        if org_state.get("id"):
            self.assertEqual(orgs[0]["id"], org_state["id"])

    def test_get_user_seed(self):
        user = require_manifest_state(self, "test_user")
        got = self.client.get_user(upn=user["upn"])
        self.assertEqual(got["id"], user["id"])
        self.assertEqual(got["userPrincipalName"].lower(), user["upn"].lower())

    def test_directory_object_seed(self):
        user = require_manifest_state(self, "test_user")
        obj = self.client.get_directory_object(user["id"])
        self.assertEqual(obj["id"], user["id"])
        otype = self.client.try_get_object_type(user["id"])
        self.assertTrue(otype is None or otype.startswith("#microsoft.graph."))

    def test_subject_service_principal(self):
        subject = require_manifest_state(self, "subject_principal")
        sp = self.client.get_service_principal(object_id=subject["spId"])
        self.assertEqual(sp["id"], subject["spId"])
        self.assertEqual(sp["appId"], subject["appId"])
        app = self.client.get_application(object_id=subject["appObjectId"])
        self.assertEqual(app["id"], subject["appObjectId"])

    def test_test_group_membership(self):
        group = require_manifest_state(self, "test_group")
        user = require_manifest_state(self, "test_user")
        got = self.client.get_group(object_id=group["id"])
        self.assertEqual(got["id"], group["id"])
        members = self.client.get_transitive_group_memberships(group["id"])
        member_ids = {m["id"] for m in members}
        self.assertIn(user["id"], member_ids)

    def test_test_application(self):
        app_state = require_manifest_state(self, "test_application")
        app = self.client.get_application(object_id=app_state["appObjectId"])
        self.assertEqual(app["id"], app_state["appObjectId"])
        sp = self.client.get_service_principal(object_id=app_state["spId"])
        self.assertEqual(sp["id"], app_state["spId"])

    def test_directory_role_assignment_present(self):
        role = require_manifest_state(self, "directory_role")
        subject = require_manifest_state(self, "subject_principal")
        assignments = self.client.get_directory_role_assignments(
            principal_id=subject["spId"]
        )
        ids = {a.get("id") for a in assignments}
        self.assertIn(role["assignmentId"], ids)

    def test_graph_app_role_annotated(self):
        app_role = require_manifest_state(self, "graph_app_role")
        subject = require_manifest_state(self, "subject_principal")

        def _find():
            perms = self.client.get_api_permissions(subject["spId"])
            return next(
                (
                    p
                    for p in perms
                    if p.get("id") == app_role["assignmentId"]
                    or p.get("appRoleId") == app_role["appRoleId"]
                ),
                None,
            )

        match = eventually(_find, label="graph app role assignment")
        self.assertIsNotNone(
            match,
            f"app role assignment not visible on subject SP; state={app_role}",
        )
        self.assertIn("azolAnnotations", match)
        self.assertEqual(match.get("appRoleId"), app_role["appRoleId"])
        self.assertTrue(match["azolAnnotations"].get("permissionName"))

    def test_federated_credential_seed(self):
        fic = require_manifest_state(self, "federated_credential")

        def _found():
            apps = self.client.get_all_application_federated_identities()
            return any(
                a.get("id") == fic["appObjectId"]
                and any(
                    c.get("id") == fic["id"]
                    for c in (a.get("federatedIdentityCredentials") or [])
                )
                for a in apps
            )

        self.assertTrue(
            eventually(_found, label="federated credential in application list"),
            f"seeded FIC not returned by get_all_application_federated_identities; state={fic}",
        )

    def test_directory_role_definitions(self):
        roles = self.client.get_directory_role_definitions()
        self.assertIsInstance(roles, list)
        self.assertTrue(any(r.get("displayName") for r in roles))

    def test_list_collections_nonempty_or_list(self):
        self.assertIsInstance(self.client.get_all_users(), list)
        self.assertIsInstance(self.client.get_all_groups(), list)
        self.assertIsInstance(self.client.get_all_applications(), list)
        self.assertIsInstance(self.client.get_all_service_principals(), list)

    def test_get_all_principals(self):
        principals = self.client.get_all_principals()
        self.assertIsInstance(principals, dict)

    def test_directory_roles_and_admin_units(self):
        self.assertIsInstance(self.client.get_directory_roles(), list)
        self.assertIsInstance(self.client.get_administrative_units(), list)


class GraphLivePimTests(LiveGraphTestCase):
    def test_pim_reads(self):
        def _probe():
            self.assertIsInstance(self.client.get_eligible_pim_assignments(), list)
            self.assertIsInstance(self.client.get_active_pim_assignments(), list)
            self.assertIsInstance(self.client.get_current_pim_eligibility(), list)
            self.assertIsInstance(self.client.get_current_pim_activations(), list)

        probe_or_skip(self, _probe)


class GraphLiveEntitlementTests(LiveGraphTestCase):
    def test_catalogs_and_packages(self):
        def _probe():
            catalogs = self.client.get_entitlement_management_catalogs()
            self.assertIsInstance(catalogs, list)
            packages = self.client.get_access_packages()
            self.assertIsInstance(packages, list)

        probe_or_skip(self, _probe)


class GraphLiveConditionalAccessTests(LiveGraphTestCase):
    def test_conditional_access_policies(self):
        def _probe():
            policies = self.client.get_conditional_access_policies()
            self.assertIsInstance(policies, list)

        probe_or_skip(self, _probe)


if __name__ == "__main__":
    unittest.main()
