"""A module containing a client for interacting with the Graph API"""
from __future__ import annotations

import asyncio
import string
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union
from urllib.parse import parse_qs, urlparse

from azol.clients.oauth_http_client import OAuthHTTPClient
from azol.clients.odata import GraphCall
from azol.constants import GRAPHBETAURL, OAuthResourceIDs, appPermissionNameMap, roleNameMap
from azol.http.errors import AzolHTTPError

SelectArg = Optional[Union[Sequence[str], Iterable[str]]]


class GraphClient(OAuthHTTPClient):
    """HTTP client for interacting with the Microsoft Graph API.

    Defaults to the Graph beta endpoint. Prefer domain helpers below, or use
    :meth:`call` / :meth:`odata` for arbitrary paths.

    Failures raise ``AzolHTTPError`` (or a status-specific subclass).
    """

    def __init__(self, *args, base_url=GRAPHBETAURL, **kwargs):
        super().__init__(oauth_resource=OAuthResourceIDs.Graph, base_url=base_url, *args, **kwargs)

    def call(self, path: str) -> GraphCall:
        """Return a fluent Graph call bound to this client.

        Args:
            path: Graph API path (leading slash optional).

        Returns:
            A configured :class:`~azol.clients.odata.GraphCall`.

        Raises:
            AzolHTTPError: Raised when the terminated call receives an unexpected status.
        """
        return GraphCall(self, path)

    def odata(self, path: str) -> GraphCall:
        """Alias of :meth:`call` for OData-style GETs.

        Args:
            path: Graph API path.

        Returns:
            A configured :class:`~azol.clients.odata.GraphCall`.

        Raises:
            AzolHTTPError: Raised when the terminated call receives an unexpected status.
        """
        return self.call(path)

    @staticmethod
    def _directory_object_ref(principal_id: str) -> Dict[str, str]:
        return {
            "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{principal_id}"
        }

    @staticmethod
    def _permission_name(app_role_id: str) -> str:
        return appPermissionNameMap.get(app_role_id, "unknown")

    @staticmethod
    def _role_name(role_definition_id: str) -> str:
        return roleNameMap.get(role_definition_id, "unknown")

    # --- Single-object getters -------------------------------------------------

    def get_me(self) -> dict[str, Any]:
        """Get the signed-in user or the app's service principal profile.

        Returns:
            A dictionary for ``/me``.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call("/me").get().json()

    def get_user(self, object_id: Optional[str] = None, upn: Optional[str] = None) -> dict[str, Any]:
        """Get a user by object id or user principal name.

        Args:
            object_id: User object id.
            upn: User principal name.

        Returns:
            A dictionary containing the user.

        Raises:
            ValueError: If neither or both identifiers are provided.
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if (object_id is None) == (upn is None):
            raise ValueError("Provide exactly one of object_id or upn")
        path = f"/users/{object_id if object_id is not None else upn}"
        return self.call(path).get().json()

    def get_group(self, object_id: str) -> dict[str, Any]:
        """Get a group by object id.

        Args:
            object_id: Group object id.

        Returns:
            A dictionary containing the group.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(f"/groups/{object_id}").get().json()

    def get_application(self, object_id: Optional[str] = None, app_id: Optional[str] = None) -> dict[str, Any]:
        """Get an application by object id or application (client) id.

        Args:
            object_id: Application object id.
            app_id: Application (client) id.

        Returns:
            A dictionary containing the application.

        Raises:
            ValueError: If neither or both identifiers are provided.
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if (object_id is None) == (app_id is None):
            raise ValueError("Provide exactly one of object_id or app_id")
        if app_id is not None:
            path = f"/applications(appId='{app_id}')"
        else:
            path = f"/applications/{object_id}"
        return self.call(path).get().json()

    def get_organization(self) -> list[Any]:
        """Get organization (tenant) objects.

        Returns:
            A list of organization dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call("/organization").get().values()

    def get_directory_roles(self) -> list[Any]:
        """Get activated directory role instances in the tenant.

        Returns:
            A list of directory role dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call("/directoryRoles").get().values()

    def get_administrative_units(self) -> list[Any]:
        """Get administrative units in the tenant.

        Returns:
            A list of administrative unit dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call("/directory/administrativeUnits").get().values()

    def get_conditional_access_policies(self) -> list[Any]:
        """Get Conditional Access policies.

        Notes:
            Requires an appropriate Entra ID license and Graph permissions.

        Returns:
            A list of Conditional Access policy dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call("/identity/conditionalAccess/policies").get().values()

    # --- Directory roles -------------------------------------------------------

    def get_directory_role_definitions(self) -> list[Any]:
        """Get all directory role definitions.

        Returns:
            A list of dictionaries containing the role definitions in the directory.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/roleManagement/directory/roleDefinitions")
            .select("displayName", "id", "isBuiltIn")
            .get()
            .values()
        )

    def get_directory_role_assignments(self, principal_id: Optional[str] = None) -> list[Any]:
        """Get directory role assignments (non-PIM).

        Args:
            principal_id: Optional principal id to filter assignments.

        Returns:
            A list of dictionaries containing role assignment metadata.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        builder = (
            self.call("/roleManagement/directory/roleAssignments")
            .expand("roleDefinition", select=("id", "displayName"))
            .select(
                "roleDefinition",
                "roleDefinitionId",
                "principalId",
                "resourceScope",
                "directoryScopeId",
                "principalOrganizationId",
            )
        )
        if principal_id is not None:
            builder = builder.filter(f"principalId eq '{principal_id}'").count(True)
        return builder.get().values()

    def delete_directory_role_assignments(self, assignment_id: str) -> Any | None:
        """Remove an Entra ID role assignment.

        Args:
            assignment_id: The ID of the role assignment to delete.

        Returns:
            ``None`` for a successful 204 response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/roleManagement/directory/roleAssignments/{assignment_id}")
            .delete()
            .json()
        )

    def add_directory_role_assignment(self, role_definition_id: str, principal_id: str) -> dict[str, Any]:
        """Assign an Entra ID role to a principal.

        Args:
            role_definition_id: The ID of the role to assign.
            principal_id: The principal to assign to the role.

        Returns:
            A dictionary containing the created assignment.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        body = {
            "@odata.type": "#microsoft.graph.unifiedRoleAssignment",
            "roleDefinitionId": role_definition_id,
            "principalId": principal_id,
            "directoryScopeId": "/",
        }
        return (
            self.call("/roleManagement/directory/roleAssignments")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

    # --- Entitlement management ------------------------------------------------

    def get_access_catalogs_roles(self, catalog_id: str) -> list[Any]:
        """Get roles assigned to a specific access catalog.

        Args:
            catalog_id: The ID of the catalog.

        Returns:
            A list of role assignment dictionaries annotated with ``azolAnnotations``.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        roles = (
            self.call("/roleManagement/entitlementManagement/roleAssignments")
            .filter(f"appScopeId eq '/AccessPackageCatalog/{catalog_id}'")
            .get()
            .values()
        )
        for role in roles:
            role["azolAnnotations"] = {
                "roleName": self._role_name(role["roleDefinitionId"])
            }
        return roles

    def create_package_policy(self, policy: Mapping[str, Any]) -> dict[str, Any]:
        """Create an Entitlement Management access package assignment policy.

        Args:
            policy: Dictionary containing the package policy.

        Returns:
            A dictionary containing the created policy.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageAssignmentPolicies")
            .body(policy)
            .expect(201)
            .post()
            .json()
        )

    def create_entitlement_management_package(self, package: Mapping[str, Any]) -> dict[str, Any]:
        """Create an Entitlement Management access package.

        Args:
            package: Dictionary containing package metadata.

        Returns:
            A dictionary containing the created package.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackages")
            .body(package)
            .expect(201)
            .post()
            .json()
        )

    def create_entitlement_management_catalog(self, catalog: Mapping[str, Any]) -> dict[str, Any]:
        """Create an Entitlement Management catalog.

        Args:
            catalog: Dictionary containing catalog metadata.

        Returns:
            A dictionary containing the created catalog.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageCatalogs")
            .body(catalog)
            .expect(201)
            .post()
            .json()
        )

    def get_access_packages(self) -> list[Any]:
        """Get Entitlement Management access packages.

        Returns:
            A list of access package dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackages")
            .expand("accessPackageCatalog", select=("displayName", "id", "description"))
            .get()
            .values()
        )

    def get_entitlement_management_catalogs(self) -> list[Any]:
        """Get Entitlement Management catalogs.

        Returns:
            A list of catalog dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageCatalogs")
            .get()
            .values()
        )

    # --- PIM -------------------------------------------------------------------

    def get_current_pim_eligibility(self) -> list[Any]:
        """Get PIM eligibility of the current principal.

        Returns:
            A list of eligibility schedule dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(
                "/roleManagement/directory/roleEligibilitySchedules/"
                "filterByCurrentUser(on='principal')"
            )
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select(
                "principal",
                "roleDefinition",
                "scheduleInfo",
                "memberType",
                "appScopeId",
                "directoryScopeId",
                "createdDateTime",
            )
            .get()
            .values()
        )

    def get_current_pim_activations(self) -> list[Any]:
        """Get PIM activations of the current principal.

        Returns:
            A list of assignment schedule dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(
                "/roleManagement/directory/roleAssignmentSchedules/"
                "filterByCurrentUser(on='principal')"
            )
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select(
                "principal",
                "roleDefinition",
                "scheduleInfo",
                "memberType",
                "appScopeId",
                "directoryScopeId",
                "createdDateTime",
            )
            .get()
            .values()
        )

    def get_active_pim_assignments(self) -> list[Any]:
        """Get all active PIM assignment schedules.

        Returns:
            A list of active PIM assignment dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/roleManagement/directory/roleAssignmentSchedules")
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select(
                "principal",
                "roleDefinition",
                "scheduleInfo",
                "memberType",
                "appScopeId",
                "directoryScopeId",
                "createdDateTime",
            )
            .get()
            .values()
        )

    def get_eligible_pim_assignments(self) -> list[Any]:
        """Get all eligible PIM assignments.

        Returns:
            A list of eligible PIM assignment dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/roleManagement/directory/roleEligibilitySchedules")
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select(
                "principal",
                "roleDefinition",
                "scheduleInfo",
                "memberType",
                "appScopeId",
                "directoryScopeId",
                "createdDateTime",
            )
            .get()
            .values()
        )

    def activate_pim_role(
        self,
        role_definition_id: str,
        principal_id: Optional[str] = None,
        directory_scope_id: str = "/",
        justification: str = "azol activation",
        duration: str = "PT1H",
    ) -> dict[str, Any]:
        """Activate an eligible PIM directory role for a principal.

        Args:
            role_definition_id: Role definition id to activate.
            principal_id: Principal to activate for. Defaults to ``/me``.
            directory_scope_id: Directory scope (default tenant root ``/``).
            justification: Activation justification text.
            duration: ISO 8601 duration (default one hour).

        Returns:
            A dictionary containing the schedule request.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if principal_id is None:
            principal_id = self.get_me()["id"]
        body = {
            "action": "selfActivate",
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
            "justification": justification,
            "scheduleInfo": {
                "startDateTime": None,
                "expiration": {
                    "type": "afterDuration",
                    "duration": duration,
                },
            },
        }
        return (
            self.call("/roleManagement/directory/roleAssignmentScheduleRequests")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

    def deactivate_pim_role(
        self,
        role_definition_id: str,
        principal_id: Optional[str] = None,
        directory_scope_id: str = "/",
        justification: str = "azol deactivation",
    ) -> dict[str, Any]:
        """Deactivate an active PIM directory role for a principal.

        Args:
            role_definition_id: Role definition id to deactivate.
            principal_id: Principal to deactivate for. Defaults to ``/me``.
            directory_scope_id: Directory scope (default tenant root ``/``).
            justification: Deactivation justification text.

        Returns:
            A dictionary containing the schedule request.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if principal_id is None:
            principal_id = self.get_me()["id"]
        body = {
            "action": "selfDeactivate",
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
            "justification": justification,
        }
        return (
            self.call("/roleManagement/directory/roleAssignmentScheduleRequests")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

    # --- Users / groups / principals -------------------------------------------

    def get_transitive_group_memberships(self, group_id: str) -> list[Any]:
        """Get transitive members of a group.

        Args:
            group_id: Object id of the group.

        Returns:
            A list of member directory objects.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(f"/groups/{group_id}/transitiveMembers").get().values()

    def get_transitive_member_of(self, object_id: str) -> list[Any]:
        """Get groups and roles a directory object is transitively a member of.

        Args:
            object_id: Directory object id (user, group, or service principal).

        Returns:
            A list of container directory objects.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(f"/directoryObjects/{object_id}/transitiveMemberOf").get().values()

    def add_group_member(self, group_id: str, principal_id: str) -> dict[str, Any]:
        """Add a member to a group.

        Args:
            group_id: Group object id.
            principal_id: Directory object id to add.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/groups/{group_id}/members/$ref")
            .body(self._directory_object_ref(principal_id))
            .post()
            .json()
        )

    def remove_group_member(self, group_id: str, principal_id: str) -> Any | None:
        """Remove a member from a group.

        Args:
            group_id: Group object id.
            principal_id: Directory object id to remove.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/groups/{group_id}/members/{principal_id}/$ref")
            .delete()
            .json()
        )

    def add_group_owner(self, group_id: str, principal_id: str) -> dict[str, Any]:
        """Add an owner to a group.

        Args:
            group_id: Group object id.
            principal_id: Directory object id to add as owner.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/groups/{group_id}/owners/$ref")
            .body(self._directory_object_ref(principal_id))
            .post()
            .json()
        )

    def remove_group_owner(self, group_id: str, principal_id: str) -> Any | None:
        """Remove an owner from a group.

        Args:
            group_id: Group object id.
            principal_id: Directory object id to remove as owner.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/groups/{group_id}/owners/{principal_id}/$ref")
            .delete()
            .json()
        )

    def _get_all_users(self, select: SelectArg = (), odata_filter: Optional[str] = None):
        builder = self.call("/users")
        if select is None:
            pass
        elif len(list(select)) == 0:
            builder = builder.select("id", "displayName", "userPrincipalName")
        else:
            builder = builder.select(*select)
        if odata_filter is not None:
            builder = builder.filter(odata_filter).count(True)
        return builder.get().values()

    def get_all_users(
        self,
        select: SelectArg = (),
        odata_filter: Optional[str] = None,
        fast: bool = False,
    ) -> list[Any]:
        """Get all users in the directory.

        Args:
            select: Fields to return. Empty (default) selects id, displayName,
                and userPrincipalName. Pass ``None`` to omit ``$select``.
            odata_filter: Optional raw OData filter expression.
            fast: If True, fan out parallel filtered requests by UPN prefix.
                Ignores ``odata_filter``. Not thread-safe with a shared client.

        Returns:
            A list of user dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if fast:
            return asyncio.run(self._get_all_users_async(select=select))
        return self._get_all_users(select=select, odata_filter=odata_filter)

    async def _get_all_users_async(self, select: SelectArg = ()):
        loop = asyncio.get_event_loop()
        buckets = list(string.digits) + list(string.ascii_lowercase) + ["-", ".", "_", "!", "^", "~"]
        tasks = [
            loop.run_in_executor(
                None,
                self._get_all_users,
                select,
                f"startsWith(userPrincipalName, '{bucket}')",
            )
            for bucket in buckets
        ]
        res_list = await asyncio.gather(*tasks)
        return sum(res_list, [])

    def _get_all_service_principals_fast(self, select_string: str, filter_string: str):
        builder = self.call("/servicePrincipals").filter(filter_string).count(True)
        if select_string:
            builder = builder.select(*select_string.split(","))
        return builder.get().values()

    async def _get_all_service_principals_async(self, select: SelectArg = (), *args, **kwargs):
        if select is None:
            select_string = ""
        elif len(list(select)) == 0:
            select_string = "id,displayName"
        else:
            select_string = ",".join(["id", "displayName", *select])
        loop = asyncio.get_event_loop()
        buckets = list("abcdef0123456789")
        tasks = [
            loop.run_in_executor(
                None,
                self._get_all_service_principals_fast,
                select_string,
                f"startsWith(appId,'{bucket}')",
            )
            for bucket in buckets
        ]
        res_list = await asyncio.gather(*tasks)
        return sum(res_list, [])

    def get_all_service_principals(
        self,
        select: SelectArg = (),
        owners: bool = False,
        fast: bool = False,
    ) -> list[Any]:
        """Get all service principals in the directory.

        Args:
            select: Extra fields beyond id/displayName. Empty (default) returns
                id and displayName. Pass ``None`` to omit ``$select``.
            owners: Expand owners. Ignored when ``fast`` is True (Graph limitation).
            fast: Parallelize with appId prefix filters. Incompatible with owners.

        Returns:
            A list of service principal dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if fast:
            return asyncio.run(self._get_all_service_principals_async(select=select))
        return self._get_all_service_principals(select=select, owners=owners)

    def _get_all_service_principals(self, select: SelectArg = (), owners: bool = False):
        builder = self.call("/servicePrincipals")
        if select is not None:
            attrs = ["id", "displayName", *select]
            if owners:
                attrs.append("owners")
            builder = builder.select(*attrs)
        if owners:
            builder = builder.expand("owners", select=("id", "displayName"))
        return builder.get().values()

    def get_all_applications(self, select: SelectArg = (), owners: bool = False) -> list[Any]:
        """Get all applications in the directory.

        Args:
            select: Extra fields beyond id/displayName. Empty (default) returns
                id and displayName. Pass ``None`` to omit ``$select``.
            owners: Expand owners when True.

        Returns:
            A list of application dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        builder = self.call("/applications")
        if select is not None:
            attrs = ["id", "displayName", *select]
            if owners:
                attrs.append("owners")
            builder = builder.select(*attrs)
        if owners:
            builder = builder.expand("owners", select=("id", "displayName"))
        return builder.get().values()

    def get_all_groups(self, select: SelectArg = (), owners: bool = False) -> list[Any]:
        """Get all groups in Entra ID.

        Args:
            select: Extra fields beyond id/displayName. Empty (default) returns
                id and displayName. Pass ``None`` to omit ``$select``.
            owners: Expand owners when True.

        Returns:
            A list of group dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        builder = self.call("/groups")
        if select is not None:
            attrs = ["id", "displayName", *select]
            if owners:
                attrs.append("owners")
            builder = builder.select(*attrs)
        if owners:
            builder = builder.expand("owners", select=("id", "displayName"))
        return builder.get().values()

    def get_all_groups_and_memberships(self) -> list[Any]:
        """Get all groups with nested ``memberOf`` relationships.

        Returns:
            A list of group dictionaries including ``memberOf``.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/groups")
            .expand("memberOf", select=("id", "displayName"))
            .select("memberOf", "id", "displayName")
            .get()
            .values()
        )

    def get_all_groups_and_owners(self) -> list[Any]:
        """Get all groups with owners.

        Returns:
            A list of group dictionaries including owners.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/groups")
            .expand("owners", select=("id", "displayName"))
            .select("owners", "id", "displayName")
            .get()
            .values()
        )

    def get_all_principals(self) -> dict[str, Any]:
        """Get all users, service principals, and groups as a principal map.

        Returns:
            A dictionary mapping object ids to displayName and principalType.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        principals = {}
        for directory_object in self.get_all_users():
            principals[directory_object["id"]] = {
                "displayName": directory_object["displayName"],
                "principalType": "User",
            }
        for directory_object in self.get_all_service_principals():
            principals[directory_object["id"]] = {
                "displayName": directory_object["displayName"],
                "principalType": "ServicePrincipal",
            }
        for directory_object in self.get_all_groups():
            principals[directory_object["id"]] = {
                "displayName": directory_object["displayName"],
                "principalType": "Group",
            }
        return principals

    def get_directory_object(self, object_id: str) -> dict[str, Any]:
        """Get a directory object by id.

        Args:
            object_id: Directory object id.

        Returns:
            A dictionary containing the directory object.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(f"/directoryObjects/{object_id}").get().json()

    def try_get_object_type(self, object_id: str) -> str | None:
        """Get a directory object's ``@odata.type`` by id.

        Args:
            object_id: Directory object id.

        Returns:
            The OData type string, or ``None`` if absent.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        body = self.call(f"/directoryObjects/{object_id}").get().json()
        return body.get("@odata.type")

    # --- Apps / service principals / owners / secrets --------------------------

    def get_service_principal(self, object_id: Optional[str] = None, client_id: Optional[str] = None) -> dict[str, Any]:
        """Get a service principal by object id or client (app) id.

        Args:
            object_id: Service principal object id.
            client_id: Application (client) id.

        Returns:
            A dictionary containing the service principal.

        Raises:
            ValueError: If neither or both identifiers are provided.
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if (object_id is None) == (client_id is None):
            raise ValueError("Provide exactly one of object_id or client_id")
        if client_id is not None:
            path = f"/servicePrincipals(appId='{client_id}')"
        else:
            path = f"/servicePrincipals/{object_id}"
        return self.call(path).get().json()

    def get_all_service_principals_owners(self) -> list[Any]:
        """Get all service principals with owners.

        Returns:
            A list of service principal dictionaries including owners.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/servicePrincipals")
            .expand("owners", select=("id", "displayName"))
            .select("owners", "id", "appId", "displayName")
            .get()
            .values()
        )

    def get_all_application_owners(self) -> list[Any]:
        """Get all applications with owners.

        Returns:
            A list of application dictionaries including owners.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/applications")
            .expand("owners", select=("id", "displayName"))
            .select("owners", "id", "appId", "displayName")
            .get()
            .values()
        )

    def add_app_owner(self, app_object_id: str, principal_id: str) -> dict[str, Any]:
        """Add an owner to an application object.

        Args:
            app_object_id: Application object id.
            principal_id: Directory object id to add as owner.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/applications/{app_object_id}/owners/$ref")
            .body(self._directory_object_ref(principal_id))
            .post()
            .json()
        )

    def remove_app_owner(self, app_object_id: str, principal_id: str) -> Any | None:
        """Remove an owner from an application object.

        Args:
            app_object_id: Application object id.
            principal_id: Directory object id to remove as owner.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/applications/{app_object_id}/owners/{principal_id}/$ref")
            .delete()
            .json()
        )

    def add_sp_owner(self, sp_object_id: str, principal_id: str) -> dict[str, Any]:
        """Add an owner to a service principal.

        Args:
            sp_object_id: Service principal object id.
            principal_id: Directory object id to add as owner.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/servicePrincipals/{sp_object_id}/owners/$ref")
            .body(self._directory_object_ref(principal_id))
            .post()
            .json()
        )

    def remove_sp_owner(self, sp_object_id: str, principal_id: str) -> Any | None:
        """Remove an owner from a service principal.

        Args:
            sp_object_id: Service principal object id.
            principal_id: Directory object id to remove as owner.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/servicePrincipals/{sp_object_id}/owners/{principal_id}/$ref")
            .delete()
            .json()
        )

    def add_app_secret(self, app_object_id: str, name: str = "inconspicuous") -> dict[str, Any]:
        """Add a password credential to an application object.

        Args:
            app_object_id: Application object id.
            name: Display name for the new secret.

        Returns:
            A dictionary containing the new password credential (includes secretText).

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        body = {"passwordCredential": {"displayName": name}}
        return self.call(f"/applications/{app_object_id}/addPassword").body(body).post().json()

    def remove_app_secret(self, app_object_id: str, key_id: str) -> Any | None:
        """Remove a password credential from an application object.

        Args:
            app_object_id: Application object id.
            key_id: Credential key id to remove.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/applications/{app_object_id}/removePassword")
            .body({"keyId": key_id})
            .post()
            .json()
        )

    def add_sp_secret(self, sp_object_id: str, name: str = "inconspicuous") -> dict[str, Any]:
        """Add a password credential to a service principal.

        Args:
            sp_object_id: Service principal object id.
            name: Display name for the new secret.

        Returns:
            A dictionary containing the new password credential (includes secretText).

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        body = {"passwordCredential": {"displayName": name}}
        return self.call(f"/servicePrincipals/{sp_object_id}/addPassword").body(body).post().json()

    def remove_sp_secret(self, sp_object_id: str, key_id: str) -> Any | None:
        """Remove a password credential from a service principal.

        Args:
            sp_object_id: Service principal object id.
            key_id: Credential key id to remove.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/servicePrincipals/{sp_object_id}/removePassword")
            .body({"keyId": key_id})
            .post()
            .json()
        )

    def get_all_sp_reply_urls(self) -> list[Any]:
        """Get reply URLs for all service principals.

        Returns:
            A list of service principal dictionaries including replyUrls.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/servicePrincipals")
            .select("replyUrls", "id", "displayName")
            .get()
            .values()
        )

    def get_all_service_principal_federated_identities(self) -> list[Any]:
        """Get service principals that have federated identity credentials.

        Returns:
            A list of service principal dictionaries with federatedIdentityCredentials.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/servicePrincipals")
            .expand("federatedIdentityCredentials")
            .select("federatedIdentityCredentials", "id", "appId", "displayName")
            .filter("not(federatedIdentityCredentials/$count eq 0)")
            .header("ConsistencyLevel", "eventual")
            .get()
            .values()
        )

    def get_all_application_federated_identities(self) -> list[Any]:
        """Get applications that have federated identity credentials.

        Returns:
            A list of application dictionaries with federatedIdentityCredentials.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/applications")
            .expand("federatedIdentityCredentials")
            .select("federatedIdentityCredentials", "id", "appId", "displayName")
            .filter("not(federatedIdentityCredentials/$count eq 0)")
            .header("ConsistencyLevel", "eventual")
            .get()
            .values()
        )

    def create_new_local_service_principal(self, name: str = "inconspicuous") -> dict[str, Any]:
        """Create an application, service principal, and password in this tenant.

        Args:
            name: Display name for the new application / service principal.

        Returns:
            A dictionary with clientId, appObjectId, spId, and spSecret.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        app = (
            self.call("/applications")
            .body({"displayName": name})
            .expect(201)
            .post()
            .json()
        )
        app_id = app["appId"]
        app_object_id = app["id"]
        # Directory replication can lag; SP create may fail with NoBackingApplicationObject.
        sp = None
        last_error: Exception | None = None
        for attempt in range(1, 9):
            try:
                sp = (
                    self.call("/servicePrincipals")
                    .body({"appId": app_id})
                    .expect(201)
                    .post()
                    .json()
                )
                break
            except AzolHTTPError as exc:
                last_error = exc
                detail = f"{exc}\n{getattr(exc, 'body_snippet', '') or ''}"
                retryable = (
                    "NoBackingApplicationObject" in detail
                    or "does not reference a valid application object" in detail
                )
                if not retryable or attempt >= 8:
                    raise
                time.sleep(2)
        if not isinstance(sp, dict) or "id" not in sp:
            raise last_error or AzolHTTPError(
                f"failed to create service principal for application {app_id}"
            )
        sp_id = sp["id"]
        secret = (
            self.call(f"/servicePrincipals/{sp_id}/addPassword")
            .body({"passwordCredential": {"displayName": "inconspicuous"}})
            .post()
            .json()
        )["secretText"]
        return {
            "clientId": app_id,
            "appObjectId": app_object_id,
            "spId": sp_id,
            "spSecret": secret,
        }

    def create_new_remote_service_principal(self, client_id: str) -> dict[str, Any]:
        """Create a service principal for an application in another tenant.

        Args:
            client_id: Application (client) id of the remote application.

        Returns:
            A dictionary with clientId and spId.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        sp = (
            self.call("/servicePrincipals")
            .body({"appId": client_id})
            .expect(201)
            .post()
            .json()
        )
        return {"clientId": client_id, "spId": sp["id"]}

    # --- Permissions -----------------------------------------------------------

    def get_graph_role_assignments(self) -> list[Any]:
        """Get app role assignments granted on the Microsoft Graph service principal.

        Returns:
            A list of assignment dictionaries annotated with ``azolAnnotations``.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        roles = (
            self.call("/servicePrincipals(appId='00000003-0000-0000-c000-000000000000')/appRoleAssignedTo")
            .get()
            .values()
        )
        for role in roles:
            role["azolAnnotations"] = {
                "roleName": self._permission_name(role["appRoleId"])
            }
        return roles

    def get_app_role_assigned_to(self, resource_sp_id: str) -> list[Any]:
        """Get principals assigned app roles on a resource service principal.

        Args:
            resource_sp_id: Object id of the resource service principal.

        Returns:
            A list of app role assignment dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(f"/servicePrincipals/{resource_sp_id}/appRoleAssignedTo").get().values()

    def get_all_sp_api_permissions(self) -> list[Any]:
        """Get app role assignments for all service principals.

        Returns:
            A list of service principal dictionaries with annotated assignments.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        sps = (
            self.call("/servicePrincipals")
            .expand(
                "appRoleAssignments",
                select=("resourceId", "resourceDisplayName", "principalType", "appRoleId"),
            )
            .select("appRoleAssignments", "id", "appId", "displayName")
            .get()
            .values()
        )
        for sp in sps:
            for ass in sp.get("appRoleAssignments", []):
                ass["azolAnnotations"] = {
                    "permissionName": self._permission_name(ass["appRoleId"])
                }
        return sps

    def get_all_sp_delegated_permissions(self) -> list[Any]:
        """Get all oauth2 permission grants in the tenant.

        Returns:
            A list of oauth2PermissionGrant dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call("/oauth2PermissionGrants")
            .select(
                "id",
                "clientId",
                "consentType",
                "principalId",
                "resourceId",
                "scope",
            )
            .get()
            .values()
        )

    def get_api_permissions(self, sp_object_id: str) -> list[Any]:
        """Get app role assignments for a service principal.

        Args:
            sp_object_id: Service principal object id.

        Returns:
            A list of app role assignment dictionaries with ``azolAnnotations``.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        api_permissions = (
            self.call(f"/servicePrincipals/{sp_object_id}/appRoleAssignments").get().values()
        )
        for permission in api_permissions:
            permission["azolAnnotations"] = {
                "permissionName": self._permission_name(permission["appRoleId"])
            }
        return api_permissions

    def get_delegated_permissions(self, sp_object_id: str) -> list[Any]:
        """Get delegated permission grants for a service principal.

        Args:
            sp_object_id: Service principal object id.

        Returns:
            A list of grant dictionaries with ``principalName`` annotations.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        delegated_permissions = (
            self.call(f"/servicePrincipals/{sp_object_id}/oauth2PermissionGrants").get().values()
        )
        annotated_permissions = []
        for grant in delegated_permissions:
            annotated = grant.copy()
            if grant.get("consentType") == "AllPrincipals":
                annotated["principalName"] = "all"
            else:
                obj = self.call(f"/directoryObjects/{grant['principalId']}").get().json()
                annotated["principalName"] = obj.get("userPrincipalName")
            annotated_permissions.append(annotated)
        return annotated_permissions

    def get_oauth2_permission_grants(self, sp_object_id: Optional[str] = None) -> list[Any]:
        """Get oauth2 permission grants, optionally for one client SP.

        Args:
            sp_object_id: Optional client service principal object id.

        Returns:
            A list of oauth2PermissionGrant dictionaries.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        if sp_object_id is not None:
            return (
                self.call(f"/servicePrincipals/{sp_object_id}/oauth2PermissionGrants")
                .get()
                .values()
            )
        return self.get_all_sp_delegated_permissions()

    def assign_app_role(self, sp_object_id: str, resource_sp_id: str, app_role_id: str) -> dict[str, Any]:
        """Assign an app role to a service principal.

        Args:
            sp_object_id: Principal (client) service principal object id.
            resource_sp_id: Resource service principal object id.
            app_role_id: App role id on the resource.

        Returns:
            A dictionary containing the created assignment.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        body = {
            "principalId": sp_object_id,
            "resourceId": resource_sp_id,
            "appRoleId": app_role_id,
        }
        return (
            self.call(f"/servicePrincipals/{sp_object_id}/appRoleAssignments")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

    def remove_app_role_assignment(self, sp_object_id: str, assignment_id: str) -> Any | None:
        """Remove an app role assignment from a service principal.

        Args:
            sp_object_id: Service principal object id.
            assignment_id: App role assignment id.

        Returns:
            ``None`` for a successful empty response, otherwise the JSON body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return (
            self.call(f"/servicePrincipals/{sp_object_id}/appRoleAssignments/{assignment_id}")
            .delete()
            .json()
        )

    # --- Raw HTTP escape hatches -----------------------------------------------

    def get(self, path: str, headers: Optional[Mapping[str, str]] = None) -> Any:
        """GET a Graph path and return deserialized JSON.

        Args:
            path: Graph API path, optionally including a query string.
            headers: Optional extra headers.

        Returns:
            Deserialized JSON (dict/list) or ``None`` for an empty body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        headers = dict(headers) if headers else {}
        if "?" in path:
            parsed = urlparse(path)
            rel = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
            query = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
            return self.call(rel).params(query).headers(headers).get().json()
        builder = self.call(path)
        for key, value in headers.items():
            builder = builder.header(key, value)
        return builder.get().json()

    def post(self, path: str, data: Any) -> Any:
        """POST JSON to a Graph path and return deserialized results.

        Args:
            path: Graph API path.
            data: JSON-serializable request body.

        Returns:
            Deserialized JSON or ``None`` for an empty body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(path).body(data).post().json()

    def put(self, path: str, data: Any) -> Any:
        """PUT JSON to a Graph path and return deserialized results.

        Args:
            path: Graph API path.
            data: JSON-serializable request body.

        Returns:
            Deserialized JSON or ``None`` for an empty body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(path).body(data).put().json()

    def patch(self, path: str, data: Any) -> Any:
        """PATCH JSON to a Graph path and return deserialized results.

        Args:
            path: Graph API path.
            data: JSON-serializable request body.

        Returns:
            Deserialized JSON or ``None`` for an empty body.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(path).body(data).patch().json()

    def delete(self, path: str) -> Any:
        """DELETE a Graph path and return deserialized results.

        Args:
            path: Graph API path.

        Returns:
            ``None`` for a successful empty/204 response, otherwise JSON.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API.
        """
        return self.call(path).delete().json()
