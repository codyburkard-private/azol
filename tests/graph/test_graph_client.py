"""Offline contract tests for GraphClient public methods."""
import unittest
from unittest.mock import MagicMock, patch

import requests

from graph._helpers import (
    last_json,
    last_method,
    last_params,
    last_url,
    make_graph_client,
    mock_response,
)


class GraphClientContractTests(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock(spec=requests.Session)
        self.session.request.return_value = mock_response(payload={"value": []})
        self.client = make_graph_client(self.session)

    def _set_payload(self, payload, status_code=200):
        self.session.request.return_value = mock_response(
            status_code=status_code, payload=payload
        )

    # --- Escape hatches --------------------------------------------------------

    def test_call_and_odata(self):
        self.assertIs(type(self.client.call("/users")), type(self.client.odata("/users")))

    def test_get_plain_path(self):
        self._set_payload({"id": "1"})
        body = self.client.get("/users/1")
        self.assertEqual(body["id"], "1")
        self.assertEqual(last_method(self.session), "GET")
        self.assertTrue(last_url(self.session).endswith("/users/1"))

    def test_get_with_query_string(self):
        self._set_payload({"value": []})
        self.client.get("/users?$select=id&$top=1")
        self.assertTrue(last_url(self.session).endswith("/users"))
        self.assertEqual(last_params(self.session)["$select"], "id")
        self.assertEqual(last_params(self.session)["$top"], "1")

    def test_post_put_patch_delete(self):
        self._set_payload({"ok": True})
        self.client.post("/x", {"a": 1})
        self.assertEqual(last_method(self.session), "POST")
        self.assertEqual(last_json(self.session), {"a": 1})

        self.client.put("/x", {"a": 2})
        self.assertEqual(last_method(self.session), "PUT")

        self.client.patch("/x", {"a": 3})
        self.assertEqual(last_method(self.session), "PATCH")

        self.session.request.return_value = mock_response(status_code=204, payload=None)
        self.assertIsNone(self.client.delete("/x"))
        self.assertEqual(last_method(self.session), "DELETE")

    # --- Single-object getters -------------------------------------------------

    def test_get_me(self):
        self._set_payload({"id": "me"})
        self.assertEqual(self.client.get_me()["id"], "me")
        self.assertTrue(last_url(self.session).endswith("/me"))

    def test_get_user_by_id_and_upn(self):
        self._set_payload({"id": "u1"})
        self.client.get_user(object_id="u1")
        self.assertTrue(last_url(self.session).endswith("/users/u1"))
        self.client.get_user(upn="a@b.com")
        self.assertTrue(last_url(self.session).endswith("/users/a@b.com"))
        with self.assertRaises(ValueError):
            self.client.get_user()
        with self.assertRaises(ValueError):
            self.client.get_user(object_id="u1", upn="a@b.com")

    def test_get_group_application_organization(self):
        self._set_payload({"id": "g1"})
        self.client.get_group("g1")
        self.assertTrue(last_url(self.session).endswith("/groups/g1"))

        self._set_payload({"id": "a1"})
        self.client.get_application(object_id="a1")
        self.assertTrue(last_url(self.session).endswith("/applications/a1"))
        self.client.get_application(app_id="app-guid")
        self.assertIn("applications(appId='app-guid')", last_url(self.session))

        self._set_payload({"value": [{"id": "org"}]})
        orgs = self.client.get_organization()
        self.assertEqual(orgs[0]["id"], "org")
        self.assertTrue(last_url(self.session).endswith("/organization"))

    def test_get_directory_roles_admin_units_ca(self):
        self.client.get_directory_roles()
        self.assertTrue(last_url(self.session).endswith("/directoryRoles"))
        self.client.get_administrative_units()
        self.assertTrue(last_url(self.session).endswith("/directory/administrativeUnits"))
        self.client.get_conditional_access_policies()
        self.assertTrue(
            last_url(self.session).endswith("/identity/conditionalAccess/policies")
        )

    # --- Directory roles -------------------------------------------------------

    def test_get_directory_role_definitions(self):
        self.client.get_directory_role_definitions()
        self.assertIn("/roleManagement/directory/roleDefinitions", last_url(self.session))
        self.assertEqual(last_params(self.session)["$select"], "displayName,id,isBuiltIn")

    def test_get_directory_role_assignments_filter(self):
        self.client.get_directory_role_assignments(principal_id="p1")
        self.assertEqual(
            last_params(self.session)["$filter"], "principalId eq 'p1'"
        )
        self.assertEqual(last_params(self.session)["$count"], "true")

    def test_add_and_delete_directory_role_assignment(self):
        self._set_payload({"id": "asg"}, status_code=201)
        self.client.add_directory_role_assignment("role", "principal")
        self.assertEqual(last_method(self.session), "POST")
        self.assertEqual(last_json(self.session)["roleDefinitionId"], "role")

        self.session.request.return_value = mock_response(status_code=204, payload=None)
        self.assertIsNone(self.client.delete_directory_role_assignments("asg"))
        self.assertEqual(last_method(self.session), "DELETE")

    # --- Entitlement management ------------------------------------------------

    def test_entitlement_reads_and_creates(self):
        self.client.get_entitlement_management_catalogs()
        self.assertIn("accessPackageCatalogs", last_url(self.session))

        self.client.get_access_packages()
        self.assertIn("accessPackages", last_url(self.session))
        self.assertIn("accessPackageCatalog", last_params(self.session)["$expand"])

        self._set_payload(
            {"value": [{"roleDefinitionId": "missing-role-id"}]},
        )
        roles = self.client.get_access_catalogs_roles("cat1")
        self.assertEqual(roles[0]["azolAnnotations"]["roleName"], "unknown")

        self._set_payload({"id": "new"}, status_code=201)
        self.client.create_entitlement_management_catalog({"displayName": "c"})
        self.client.create_entitlement_management_package({"displayName": "p"})
        self.client.create_package_policy({"displayName": "pol"})
        self.assertEqual(last_method(self.session), "POST")

    # --- PIM -------------------------------------------------------------------

    def test_pim_reads(self):
        self.client.get_current_pim_eligibility()
        self.assertIn("roleEligibilitySchedules/filterByCurrentUser", last_url(self.session))
        self.client.get_current_pim_activations()
        self.assertIn("roleAssignmentSchedules/filterByCurrentUser", last_url(self.session))
        self.client.get_active_pim_assignments()
        self.assertTrue(last_url(self.session).endswith("/roleAssignmentSchedules"))
        self.client.get_eligible_pim_assignments()
        self.assertTrue(last_url(self.session).endswith("/roleEligibilitySchedules"))

    def test_activate_deactivate_pim_role(self):
        self.session.request.side_effect = [
            mock_response(payload={"id": "me-id"}),
            mock_response(status_code=201, payload={"id": "req"}),
        ]
        body = self.client.activate_pim_role("role-def")
        self.assertEqual(body["id"], "req")
        self.assertEqual(last_json(self.session)["action"], "selfActivate")
        self.assertEqual(last_json(self.session)["principalId"], "me-id")

        self.session.request.side_effect = None
        self._set_payload({"id": "req2"}, status_code=201)
        self.client.deactivate_pim_role("role-def", principal_id="p1")
        self.assertEqual(last_json(self.session)["action"], "selfDeactivate")
        self.assertEqual(last_json(self.session)["principalId"], "p1")

    # --- Users / groups --------------------------------------------------------

    def test_get_all_users_default_select(self):
        self.client.get_all_users()
        self.assertEqual(
            last_params(self.session)["$select"],
            "id,displayName,userPrincipalName",
        )

    def test_get_all_users_filter(self):
        self.client.get_all_users(odata_filter="startswith(displayName,'A')")
        self.assertEqual(
            last_params(self.session)["$filter"], "startswith(displayName,'A')"
        )

    def test_get_all_groups_and_membership_helpers(self):
        self.client.get_all_groups()
        self.assertTrue(last_url(self.session).endswith("/groups"))
        self.client.get_all_groups_and_owners()
        self.assertIn("owners", last_params(self.session)["$expand"])
        self.client.get_all_groups_and_memberships()
        self.assertIn("memberOf", last_params(self.session)["$expand"])
        self.client.get_transitive_group_memberships("g1")
        self.assertTrue(last_url(self.session).endswith("/groups/g1/transitiveMembers"))
        self.client.get_transitive_member_of("o1")
        self.assertTrue(
            last_url(self.session).endswith("/directoryObjects/o1/transitiveMemberOf")
        )

    def test_group_member_and_owner_mutations(self):
        self.session.request.return_value = mock_response(status_code=204, payload=None)
        self.assertIsNone(self.client.add_group_member("g1", "p1"))
        self.assertTrue(last_url(self.session).endswith("/groups/g1/members/$ref"))
        self.assertIn("directoryObjects/p1", last_json(self.session)["@odata.id"])

        self.assertIsNone(self.client.remove_group_member("g1", "p1"))
        self.assertTrue(last_url(self.session).endswith("/groups/g1/members/p1/$ref"))

        self.assertIsNone(self.client.add_group_owner("g1", "p1"))
        self.assertTrue(last_url(self.session).endswith("/groups/g1/owners/$ref"))
        self.assertIsNone(self.client.remove_group_owner("g1", "p1"))

    def test_get_directory_object_and_type(self):
        self._set_payload({"id": "o1", "@odata.type": "#microsoft.graph.user"})
        self.assertEqual(self.client.get_directory_object("o1")["id"], "o1")
        self.assertEqual(self.client.try_get_object_type("o1"), "#microsoft.graph.user")

    def test_get_all_principals(self):
        self.session.request.side_effect = [
            mock_response(payload={"value": [{"id": "u1", "displayName": "User"}]}),
            mock_response(payload={"value": [{"id": "s1", "displayName": "SP"}]}),
            mock_response(payload={"value": [{"id": "g1", "displayName": "Group"}]}),
        ]
        principals = self.client.get_all_principals()
        self.assertEqual(principals["u1"]["principalType"], "User")
        self.assertEqual(principals["s1"]["principalType"], "ServicePrincipal")
        self.assertEqual(principals["g1"]["principalType"], "Group")

    # --- Apps / SPs ------------------------------------------------------------

    def test_get_service_principal_validation(self):
        with self.assertRaises(ValueError):
            self.client.get_service_principal()
        with self.assertRaises(ValueError):
            self.client.get_service_principal(object_id="a", client_id="b")
        self._set_payload({"id": "sp"})
        self.client.get_service_principal(object_id="sp1")
        self.assertTrue(last_url(self.session).endswith("/servicePrincipals/sp1"))
        self.client.get_service_principal(client_id="app1")
        self.assertIn("servicePrincipals(appId='app1')", last_url(self.session))

    def test_get_all_applications_and_sps(self):
        self.client.get_all_applications()
        self.assertTrue(last_url(self.session).endswith("/applications"))
        self.client.get_all_service_principals()
        self.assertTrue(last_url(self.session).endswith("/servicePrincipals"))
        self.client.get_all_application_owners()
        self.client.get_all_service_principals_owners()
        self.client.get_all_sp_reply_urls()
        self.assertEqual(last_params(self.session)["$select"], "replyUrls,id,displayName")

    def test_federated_identities(self):
        self.client.get_all_application_federated_identities()
        headers = self.session.request.call_args.kwargs.get("headers") or {}
        self.assertEqual(headers.get("ConsistencyLevel"), "eventual")
        self.assertIn(
            "not(federatedIdentityCredentials/$count eq 0)",
            last_params(self.session)["$filter"],
        )
        self.client.get_all_service_principal_federated_identities()
        headers = self.session.request.call_args.kwargs.get("headers") or {}
        self.assertEqual(headers.get("ConsistencyLevel"), "eventual")

    def test_app_and_sp_owner_mutations(self):
        self.session.request.return_value = mock_response(status_code=204, payload=None)
        self.assertIsNone(self.client.add_app_owner("app", "p1"))
        self.assertTrue(last_url(self.session).endswith("/applications/app/owners/$ref"))
        self.assertIsNone(self.client.remove_app_owner("app", "p1"))
        self.assertIsNone(self.client.add_sp_owner("sp", "p1"))
        self.assertTrue(last_url(self.session).endswith("/servicePrincipals/sp/owners/$ref"))
        self.assertIsNone(self.client.remove_sp_owner("sp", "p1"))

    def test_secrets(self):
        self._set_payload({"secretText": "s", "keyId": "k"})
        self.assertEqual(self.client.add_app_secret("app")["secretText"], "s")
        self.assertTrue(last_url(self.session).endswith("/applications/app/addPassword"))
        self.assertEqual(self.client.add_sp_secret("sp")["secretText"], "s")
        self.session.request.return_value = mock_response(status_code=204, payload=None)
        self.assertIsNone(self.client.remove_app_secret("app", "k"))
        self.assertTrue(last_url(self.session).endswith("/applications/app/removePassword"))
        self.assertIsNone(self.client.remove_sp_secret("sp", "k"))

    def test_create_local_and_remote_sp(self):
        self.session.request.side_effect = [
            mock_response(status_code=201, payload={"id": "app-obj", "appId": "app-id"}),
            mock_response(status_code=201, payload={"id": "sp-id"}),
            mock_response(payload={"secretText": "secret"}),
        ]
        out = self.client.create_new_local_service_principal("azol-live-test")
        self.assertEqual(
            out,
            {
                "clientId": "app-id",
                "appObjectId": "app-obj",
                "spId": "sp-id",
                "spSecret": "secret",
            },
        )
        self.assertEqual(self.session.request.call_count, 3)

        self.session.request.side_effect = None
        self._set_payload({"id": "sp2"}, status_code=201)
        remote = self.client.create_new_remote_service_principal("remote-app")
        self.assertEqual(remote, {"clientId": "remote-app", "spId": "sp2"})

    # --- Permissions -----------------------------------------------------------

    def test_get_api_permissions_unknown_safe(self):
        self._set_payload({"value": [{"appRoleId": "not-a-real-role"}]})
        perms = self.client.get_api_permissions("sp1")
        self.assertEqual(perms[0]["azolAnnotations"]["permissionName"], "unknown")

    def test_get_graph_role_assignments_annotation(self):
        self._set_payload({"value": [{"appRoleId": "not-a-real-role"}]})
        roles = self.client.get_graph_role_assignments()
        self.assertEqual(roles[0]["azolAnnotations"]["roleName"], "unknown")
        self.assertIn("00000003-0000-0000-c000-000000000000", last_url(self.session))

    def test_get_all_sp_api_permissions_annotation_key(self):
        self._set_payload(
            {
                "value": [
                    {
                        "id": "sp",
                        "appId": "a",
                        "displayName": "n",
                        "appRoleAssignments": [{"appRoleId": "missing"}],
                    }
                ]
            }
        )
        sps = self.client.get_all_sp_api_permissions()
        self.assertIn("azolAnnotations", sps[0]["appRoleAssignments"][0])
        self.assertNotIn("azolannotations", sps[0]["appRoleAssignments"][0])

    def test_delegated_permissions(self):
        self.session.request.side_effect = [
            mock_response(
                payload={
                    "value": [
                        {"consentType": "AllPrincipals", "principalId": None},
                        {"consentType": "Principal", "principalId": "u1"},
                    ]
                }
            ),
            mock_response(payload={"userPrincipalName": "user@contoso.com"}),
        ]
        grants = self.client.get_delegated_permissions("sp1")
        self.assertEqual(grants[0]["principalName"], "all")
        self.assertEqual(grants[1]["principalName"], "user@contoso.com")

    def test_get_all_sp_delegated_permissions_and_oauth2(self):
        self.client.get_all_sp_delegated_permissions()
        self.assertTrue(last_url(self.session).endswith("/oauth2PermissionGrants"))
        self.client.get_oauth2_permission_grants("sp1")
        self.assertTrue(
            last_url(self.session).endswith("/servicePrincipals/sp1/oauth2PermissionGrants")
        )

    def test_assign_and_remove_app_role(self):
        self._set_payload({"id": "asg"}, status_code=201)
        self.client.assign_app_role("sp", "res", "role")
        self.assertEqual(last_json(self.session)["appRoleId"], "role")
        self.session.request.return_value = mock_response(status_code=204, payload=None)
        self.assertIsNone(self.client.remove_app_role_assignment("sp", "asg"))

    def test_get_app_role_assigned_to(self):
        self.client.get_app_role_assigned_to("res-sp")
        self.assertTrue(
            last_url(self.session).endswith("/servicePrincipals/res-sp/appRoleAssignedTo")
        )


if __name__ == "__main__":
    unittest.main()
