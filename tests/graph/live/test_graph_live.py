"""Live-tenant GraphClient tests (env-gated)."""
import unittest

from graph.live.live_helpers import (
    make_live_client,
    optional_env,
    require_cap,
    require_live,
)


@require_live()
class GraphLiveCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = make_live_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_organization(self):
        orgs = self.client.get_organization()
        self.assertIsInstance(orgs, list)
        self.assertTrue(orgs)

    def test_list_users_groups_apps_sps(self):
        users = self.client.get_all_users()
        self.assertIsInstance(users, list)
        groups = self.client.get_all_groups()
        self.assertIsInstance(groups, list)
        apps = self.client.get_all_applications()
        self.assertIsInstance(apps, list)
        sps = self.client.get_all_service_principals()
        self.assertIsInstance(sps, list)

    def test_directory_role_definitions(self):
        roles = self.client.get_directory_role_definitions()
        self.assertIsInstance(roles, list)
        self.assertTrue(any(r.get("displayName") for r in roles))

    def test_directory_role_assignments(self):
        assignments = self.client.get_directory_role_assignments()
        self.assertIsInstance(assignments, list)

    def test_graph_role_assignments(self):
        roles = self.client.get_graph_role_assignments()
        self.assertIsInstance(roles, list)
        if roles:
            self.assertIn("azolAnnotations", roles[0])

    def test_directory_object_seed(self):
        object_id = optional_env("AZOL_LIVE_OBJECT_ID")
        if not object_id:
            self.skipTest("Set AZOL_LIVE_OBJECT_ID to exercise get_directory_object")
        obj = self.client.get_directory_object(object_id)
        self.assertEqual(obj["id"], object_id)
        otype = self.client.try_get_object_type(object_id)
        self.assertTrue(otype is None or otype.startswith("#microsoft.graph."))

    def test_service_principal_self(self):
        client_id = optional_env("AZOL_LIVE_CLIENT_ID")
        sp = self.client.get_service_principal(client_id=client_id)
        self.assertEqual(sp["appId"], client_id)
        perms = self.client.get_api_permissions(sp["id"])
        self.assertIsInstance(perms, list)

    def test_get_all_principals(self):
        principals = self.client.get_all_principals()
        self.assertIsInstance(principals, dict)

    def test_directory_roles_and_admin_units(self):
        self.assertIsInstance(self.client.get_directory_roles(), list)
        self.assertIsInstance(self.client.get_administrative_units(), list)

    def test_federated_identity_lists(self):
        self.assertIsInstance(
            self.client.get_all_application_federated_identities(), list
        )
        self.assertIsInstance(
            self.client.get_all_service_principal_federated_identities(), list
        )


@require_cap("mutate")
class GraphLiveMutateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = make_live_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_create_and_cleanup_local_sp(self):
        created = self.client.create_new_local_service_principal(name="azol-live-sp")
        self.addCleanup(self._cleanup_sp, created)
        sp = self.client.get_service_principal(object_id=created["spId"])
        self.assertEqual(sp["id"], created["spId"])
        app = self.client.get_application(object_id=created["appObjectId"])
        self.assertEqual(app["id"], created["appObjectId"])

    def _cleanup_sp(self, created):
        try:
            self.client.delete(f"/servicePrincipals/{created['spId']}")
        except Exception:
            pass
        try:
            self.client.delete(f"/applications/{created['appObjectId']}")
        except Exception:
            pass


@require_cap("pim")
class GraphLivePimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = make_live_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_pim_reads(self):
        self.assertIsInstance(self.client.get_eligible_pim_assignments(), list)
        self.assertIsInstance(self.client.get_active_pim_assignments(), list)
        # filterByCurrentUser often needs delegated auth; allow empty or success
        try:
            self.assertIsInstance(self.client.get_current_pim_eligibility(), list)
            self.assertIsInstance(self.client.get_current_pim_activations(), list)
        except Exception as exc:
            if "403" in str(exc) or "Authorization_RequestDenied" in str(exc):
                self.skipTest(f"PIM current-user APIs not available for this auth: {exc}")
            raise


@require_cap("entitlement")
class GraphLiveEntitlementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = make_live_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_catalogs_and_packages(self):
        catalogs = self.client.get_entitlement_management_catalogs()
        self.assertIsInstance(catalogs, list)
        packages = self.client.get_access_packages()
        self.assertIsInstance(packages, list)


@require_cap("ca")
class GraphLiveConditionalAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = make_live_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_conditional_access_policies(self):
        policies = self.client.get_conditional_access_policies()
        self.assertIsInstance(policies, list)


if __name__ == "__main__":
    unittest.main()
