"""A module containing a client for interacting with the Graph API"""
from azol.clients.oauth_http_client import OAuthHTTPClient
from azol.clients.odata import GraphCall
from azol.constants import GRAPHBETAURL, OAuthResourceIDs, roleNameMap, appPermissionNameMap
import asyncio
import string

class GraphClient( OAuthHTTPClient ):
    """
        An HTTP client for interacting with the Microsoft Graph API
    """

    def __init__( self, *args, base_url=GRAPHBETAURL, **kwargs ):
        super().__init__(  oauth_resource=OAuthResourceIDs.Graph, base_url=base_url, *args, **kwargs )

    def call(self, path: str) -> GraphCall:
        """Return a fluent Graph call bound to this client.

        Failures raise ``AzolHTTPError`` (or a status-specific subclass such as
        ``AzolClientError`` / ``AzolServerError``).
        """
        return GraphCall(self, path)

    def odata(self, path: str) -> GraphCall:
        """Alias of ``call`` for OData-style GETs."""
        return self.call(path)

    def get_directory_role_definitions( self ):
        """Get all directory role definitions.
        
        Returns:
            A list of dictionaries containing the role definitions in the directory.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/roleManagement/directory/roleDefinitions")
            .select("displayName", "id", "isBuiltIn")
            .get().values()
        )

    def get_access_catalogs_roles( self, catalogId ):
        """
            Get all the roles assigned to a specific access catalog

            Args:
                catalogId - the ID of the catalog

            Returns:
                A list of dictionaries containing role assignments for the catalog

            Raises:
                AzolHTTPError: An error occurred accessing the Graph API

        """
        roles = (
            self.call("/roleManagement/entitlementManagement/roleAssignments")
            .filter(f"appScopeId eq '/AccessPackageCatalog/{catalogId}'")
            .get().values()
        )
        for role in roles:
            role["azolAnnotations"] = {
                "roleName" : roleNameMap[role["roleDefinitionId"]]
            }
        return roles


    def create_package_policy( self, policy ):
        """Create policy for Entitlement Management Pacakge

        Returns:
            A dictionary containing the entitlement management package policy.

        Args:
            policy - dictionary containing entitlement management package policy

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageAssignmentPolicies")
            .body(policy)
            .expect(201)
            .post()
            .json()
        )

    def create_entitlement_management_package( self, package ):
        """Create Entitlement Management Pacakge

        Returns:
            A dictionary containing the entitlement management package.

        Args:
            package - dictionary containing entitlement management package metadata

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackages")
            .body(package)
            .expect(201)
            .post()
            .json()
        )

    def create_entitlement_management_catalog( self, catalog ):
        """Create Entitlement Management Catalog

        Returns:
            A list of dictionaries containing the entitlement management catalog.

        Args:
            catalog - dictionary containing entitlement management catalog metadata

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageCatalogs")
            .body(catalog)
            .expect(201)
            .post()
            .json()
        )

    def get_access_packages( self ):
        """Get Entitlement Management Access Packages.

        Returns:
            A list of dictionaries containing all entitlement management access packages metadata.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """

        return (
            self.call("/identityGovernance/entitlementManagement/accessPackages")
            .expand("accessPackageCatalog", select=("displayName", "id", "description"))
            .get().values()
        )

    def get_entitlement_management_catalogs( self ):
        """Get Entitlement Management Catalogs.

        Returns:
            A list of dictionaries containing entitlement management catalog metadata.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """

        return self.call("/identityGovernance/entitlementManagement/accessPackageCatalogs").get().values()

    def create_package_policy( self, policy ):
        """Create policy for Entitlement Management Pacakge

        Returns:
            A dictionary containing the entitlement management package policy.

        Args:
            catalog - dictionary containing entitlement management package policy

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageAssignmentPolicies")
            .body(policy)
            .expect(201)
            .post()
            .json()
        )

    def create_entitlement_management_package( self, package ):
        """Create Entitlement Management Pacakge

        Returns:
            A dictionary containing the entitlement management package.

        Args:
            package - dictionary containing entitlement management package metadata

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackages")
            .body(package)
            .expect(201)
            .post()
            .json()
        )

    def create_entitlement_management_catalog( self, catalog ):
        """Create Entitlement Management Catalog

        Returns:
            A list of dictionaries containing the entitlement management catalog.

        Args:
            catalog - dictionary containing entitlement management catalog metadata

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/identityGovernance/entitlementManagement/accessPackageCatalogs")
            .body(catalog)
            .expect(201)
            .post()
            .json()
        )

    def get_access_packages( self ):
        """Get Entitlement Management Access Packages.

        Returns:
            A list of dictionaries containing all entitlement management access packages metadata.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """

        return (
            self.call("/identityGovernance/entitlementManagement/accessPackages")
            .expand("accessPackageCatalog", select=("displayName", "id", "description"))
            .get().values()
        )

    def get_entitlement_management_catalogs( self ):
        """Get Entitlement Management Catalogs.

        Returns:
            A list of dictionaries containing entitlement management catalog metadata.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """

        return self.call("/identityGovernance/entitlementManagement/accessPackageCatalogs").get().values()

    def get_current_pim_eligibility( self ):
        """Get pim eligibility of the current principal.

        Returns:
            A list of dictionaries containing the pim eligibility of the current principal.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/roleManagement/directory/roleEligibilitySchedules/filterByCurrentUser(on='principal')")
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select("principal", "roleDefinition", "scheduleInfo", "memberType", "appScopeId",
                    "directoryScopeId", "createdDateTime")
            .get().values()
        )

    def get_current_pim_activations( self ):
        """Get pim activations of the current principal.

        Returns:
            A list of dictionaries containing the pim activations of the current principal.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/roleManagement/directory/roleAssignmentSchedules/filterByCurrentUser(on='principal')")
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select("principal", "roleDefinition", "scheduleInfo", "memberType", "appScopeId",
                    "directoryScopeId", "createdDateTime")
            .get().values()
        )

    def get_active_pim_assignments( self ):
        """Get all active PIM sessions.
        
        Returns:
            A list of dictionaries containing the active PIM sessions in the directory.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/roleManagement/directory/roleAssignmentSchedules")
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select("principal", "roleDefinition", "scheduleInfo", "memberType", "appScopeId",
                    "directoryScopeId", "createdDateTime")
            .get().values()
        )

    def get_eligible_pim_assignments( self ):
        """Get all eligible PIM assignments.
        
        Returns:
            A list of dictionaries containing the eligible PIM assignments in the directory.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return (
            self.call("/roleManagement/directory/roleEligibilitySchedules")
            .expand("principal")
            .expand("roleDefinition", select=("displayName", "id", "templateId"))
            .select("principal", "roleDefinition", "scheduleInfo", "memberType", "appScopeId",
                    "directoryScopeId", "createdDateTime")
            .get().values()
        )

    def get_transitive_group_memberships( self, group_id ):
        """Get transitive group memberships of a specific group.
        
        Args:
            group_id - (str) object id of the group

        Returns:
            A list of objects containing members of the group.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API

        """
        return self.call(f"/groups/{group_id}/transitiveMembers").get().values()

    def _get_all_users( self, select=[], filter=None ):
        """Get all users in the directory.

        Args:
            select - (list) - a list of json attributes that should be returned from all group.
                    if this is None, the select query parameter will not be used in the request

            filter - (str) - a raw list containing a filter expression for the graph request

        Returns:
            A list of objects containing object id and displayName of all users

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        builder = self.call("/users")
        if select == []:
            builder = builder.select("id", "displayName", "appId")
        elif select is not None:
            builder = builder.select(*select)
        if filter is not None:
            builder = builder.filter(filter).count(True)
        return builder.get().values()

    def get_all_users(self, select=[], filter=None, fast=False):
        if fast:
            results=asyncio.run(self._get_all_users_async())
        else:
            results=self._get_all_users( select=select, filter=filter)
        return results


    async def _get_all_users_async(self):
        loop = asyncio.get_event_loop()
        numbers=list(string.digits)
        letters=list(string.ascii_lowercase)
        special=[ "-", ".", "_", "!", "^", "~" ]
        buckets=numbers+letters+special
        threads=[]
        for bucket in buckets:
            task=loop.run_in_executor(None, self._get_all_users, None, f"startsWith(userPrincipalName, '{bucket}')")
            threads.append(task)
        res_list=await asyncio.gather(*threads)
        res = sum(res_list, [])
        return res

    async def _get_all_service_principals_async(self, select=[], *args, **kwargs):
        '''
            Internal asynchronous method for fetching all service principals. 

            This method uses the "startsWith" odata filter to start 16 parallel request streams,
            each polling for service principals whose app IDs start with one of 0-f.

            Note that the graph api does not support both the $expand operation and $filter operation
            for service principals, so the "owners" argument is ignored if fast=true

        '''
        select = ",".join(select)
        loop = asyncio.get_event_loop()
        threads=[]
        buckets=["a", "b", "c", "d", "e", "f", "0", "1", "2", "3", "4", "5", "6","7","8","9"]
        for bucket in buckets:
            task=loop.run_in_executor(None, self._get_all_service_principals_fast, select, f"startsWith(appId,'{bucket}')")
            threads.append(task)
        res_list=await asyncio.gather(*threads)
        res = sum(res_list, [])
        return res

    def _get_all_service_principals_fast( self, select_string, filter_string ):
        builder = (
            self.call("/servicePrincipals")
            .filter(filter_string)
            .count(True)
        )
        if select_string:
            builder = builder.select(*select_string.split(","))
        return builder.get().values()

    def get_all_service_principals( self, select=[], owners=False, fast=False ):
        """Get all service principals in the directory

           By default, only get the id and displayName attributes. 
           Other attributes can be collected if explicitly requested using "select".
           Collect all attributes by setting select to None. Note that if owners
           is set to true and select is set to None, the full  owner
           objects will be returned due to limitiations in the Graph OData API.

           Note that the graph api does not support both the $expand operation and $filter operation
           for service principals, so the "owners" argument is ignored if fast=true

        Args:
            select - (list) - A list of json attributes that should be returned from all  service principals.
                    if this is None, the select query parameter will not be used in the request

            owners - (bool) - If set to True, the the owners of all  service principals will also be collected
                    in the graph API request. Defaults to False. Not compatible with the "fast" parameter due
                    to limitations in the graph API
            
            fast - (bool) - If True, speed up collection using multiple threads. Not compatible with the
                    "owners" parameter. If both are specified, the owners parameter will be ignored.
        Returns:
            A list of dictionaries, containing service principal information

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        if fast:
            results=asyncio.run(self._get_all_service_principals_async(select=select, owners=owners))
        else:
            results=self._get_all_service_principals( select=select, owners=owners)
        return results


    def _get_all_service_principals( self, select=[], owners=False ):
        builder = self.call("/servicePrincipals")
        if select is not None:
            attrs = ["id", "displayName", *select]
            if owners:
                attrs.append("owners")
            builder = builder.select(*attrs)
        if owners:
            builder = builder.expand("owners", select=("id", "displayName"))
        return builder.get().values()

    def _gets_all_service_principals( self, select=[], filter=None ):
        """Get all service principals in the directory.

        Args:
            select - (list) - a list of json attributes that should be returned from all group.
                    if this is None, the select query parameter will not be used in the request
        Returns:
            A list of objects containing object id and displayName of all service principals

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        pass

    def get_all_applications( self, select=[], owners=False ):
        """Get all applications in the directory

           By default, only get the id and displayName attributes. 
           Other attributes can be collected if explicitly requested using "select".
           Collect all attributes by setting select to None. Note that if owners
           is set to true and select is set to None, the full  owner
           objects will be returned due to limitiations in the Graph OData API.

        Args:
            select - (list) - A list of json attributes that should be returned from all applications.
                    if this is None, the select query parameter will not be used in the request

            owners - (bool) - If set to True, the the owners of all applications will also be collected
                    in the graph API request. Defaults to False
        Returns:
            A list of dictionaries, containing application information

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
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

    def get_directory_role_assignments( self, object=None ):
        """Get directory role assignments.

        Get all Entra ID role assignments in the directory, ignoring assignments through PIM

        Returns:
            A list of dictionaries containing role assignment metadata

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        builder = (
            self.call("/roleManagement/directory/roleAssignments")
            .expand("roleDefinition", select=("id", "displayName"))
            .select("roleDefinition", "roleDefinitionId", "principalId", "resourceScope",
                    "directoryScopeId", "principalOrganizationId")
        )
        if object is not None:
            builder = builder.filter(f"principalId eq '{object}'").count(True)
        return builder.get().values()

    def delete_directory_role_assignments( self, assignment_id ):
        """Remove an Entra ID role from a principal in the directory.

        Args:
            assignment_id - (str) - The ID of the role assignment to delete

        Returns:
            A list of dictionaries containing the graph response to the deletion

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call(f"/roleManagement/directory/roleAssignments/{assignment_id}")
            .delete()
            .json()
        )

    def add_directory_role_assignment( self, role_definition_id, principal_id ):
        """Assign an Entra ID role to a principal in the directory.

        Args:
            role_definition_id - (str) - The ID of the role to assign
            principal_id - (str) - the principal to assign to the role

        Returns:
            A dictionary containing the graph ressponse

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        body = {
            "@odata.type": "#microsoft.graph.unifiedRoleAssignment",
            "roleDefinitionId": role_definition_id,
            "principalId": principal_id,
            "directoryScopeId": "/"
        }
        return (
            self.call("/roleManagement/directory/roleAssignments")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

    def add_app_owner( self, app_object_id, principal_id ):
        """Add an owner to an application object.

        Args:
            app_object_id - (str) - The ID of the application
            principal_id - (str) - the principal to assign to owner

        Returns:
            A dictionary containing the graph ressponse

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        body = {
            "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{principal_id}"
        }
        # ERROR: this always errors out, even if it succeeds. its a requests library error
        return (
            self.call(f"/applications/{app_object_id}/owners/$ref")
            .body(body)
            .post()
            .json()
        )

    def remove_app_owner( self, app_object_id, principal_id ):
        """Remove an owner from an application object.

        Args:
            app_object_id - (str) - The ID of the application
            principal_id - (str) - the principal to assign to owner

        Returns:
            A dictionary containing the graph ressponse

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call(f"/applications/{app_object_id}/owners/{principal_id}/$ref")
            .delete()
            .json()
        )

    def get_all_service_principals_owners( self ):
        """Get all owners of all service principals.

        Calls the graph API get get all service prinicpals, as well as their
        owners.

        Returns:
            A list of dictionaries, containing service principal ids,
            names, and owners

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/servicePrincipals")
            .expand("owners", select=("id", "displayName"))
            .select("owners", "id", "appId", "displayName")
            .get().values()
        )

    def get_all_application_owners( self ):
        """Get all owners of all application objects.

        Calls the graph API get get all application objects, as well as their
        owners.

        Returns:
            A list of dictionaries, containing app object ids,
            names, and owners

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/applications")
            .expand("owners", select=("id", "displayName"))
            .select("owners", "id", "appId", "displayName")
            .get().values()
        )

    def get_all_groups_and_memberships( self ):
        """Get all groups and group memberships.

        Calls the graph API get get all groups, and nested memberships.

        Returns:
            A list of dictionaries, containing group ids, names, and nested relationships

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/groups")
            .expand("memberOf", select=("id", "displayName"))
            .select("memberOf", "id", "displayName")
            .get().values()
        )

    def get_all_groups( self, select=[], owners=False ):
        """Get all groups in Entra Id.

           By default, only get the id and displayName attributes. 
           Other attributes can be collected if explicitly requested using "select".
           Collect all attributes by setting select to None. Note that if owners
           is set to true and select is set to None, the full  owner
           objects will be returned due to limitiations in the Graph OData API.

        Args:
            select - (list) - A list of json attributes that should be returned from all group.
                    if this is None, the select query parameter will not be used in the request

            owners - (bool) - If set to True, the the owners of all groups will also be collected
                    in the graph API request. Defaults to False
        Returns:
            A list of dictionaries, containing group information

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
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

    def get_all_groups_and_owners( self ):
        """Get all group owners in all Entra ID groups.

        Calls the graph API get get all groups, and owners of those groups.

        Returns:
            A list of dictionaries, containing groupIds, groupNames, and owners

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/groups")
            .expand("owners", select=("id", "displayName"))
            .select("owners", "id", "displayName")
            .get().values()
        )

    def get_graph_role_assignments( self ):
        """
            Get all role assignments to the graph API
        """
        roles = (
            self.call("/servicePrincipals(appId='00000003-0000-0000-c000-000000000000')/appRoleAssignedTo")
            .get().values()
        )
        for role in roles:
            role_id=role["appRoleId"]
            if role_id in appPermissionNameMap.keys():
                role["roleName"] = appPermissionNameMap[role_id]
            else:
                role["roleName"] = "unknown"
        return roles

    def get_all_sp_api_permissions( self ):
        """Get all the API permissions assigned to all service principals.

        Returns:
           A list of dictionaries with API permissions assigned to all service principal

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        sps = (
            self.call("/servicePrincipals")
            .expand(
                "appRoleAssignments",
                select=("resourceId", "resourceDisplayName", "principalType", "appRoleId"),
            )
            .select("appRoleAssignments", "id", "appId", "displayName")
            .get().values()
        )
        for sp in sps:
            for ass in sp["appRoleAssignments"]:
                if ass["appRoleId"] in appPermissionNameMap.keys():
                    ass["azolannotations"] = {
                        "permissionName": appPermissionNameMap[ass["appRoleId"]]
                    }
                else:
                    ass["azolannotations"] = {
                        "permissionName": "unknown"
                    }
        return sps

    #def get_all_sp_delegated_permissions( self ): # TODO: currently errors
    #    """Get all the API permissions assigned to all service principals.
    #
    #    Returns:
    #       A list of dictionaries with API permissions assigned to all service principal
    #
    #    Raises:
    #        AzolHTTPError: An error occurred accessing the Graph API
    #    """
    #    response = self._send_request( "/servicePrincipals?&$select=oauth2PermissionGrants,"
    #                                   "id,displayName" )
    #    if response:
    #        return self._get_all_graph_objects(response)
    #    raise AzolHTTPError()

    def get_service_principal(self, object_id=None, client_id=None ):
        """Get service principals.

        Returns:
           A list of dictionaries containing service principal properties from Graph

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        if client_id is not None:
            path = f"/servicePrincipals(appId='{client_id}')"
        else:
            path = f"/servicePrincipals/{object_id}"
        return self.call(path).get().json()

    def get_all_sp_reply_urls( self ):
        """Get all the reply Urls for all service principals.

        Returns:
           A list of dictionaries containing service principals and
           their reply urls.

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/servicePrincipals")
            .select("replyUrls", "id", "displayName")
            .get().values()
        )

    def get_api_permissions( self, sp_object_id ):
        """Get all API permissions assigned to a service principal.

        Get all the API permissions assigned to a service principal. 

        Args:
            - sp_object_id - (string) The object ID of a service principal

        Returns:
           A dictionary containing the service principal and
           its API permissions 

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        api_permissions = (
            self.call(f"/servicePrincipals/{sp_object_id}/appRoleAssignments")
            .get().values()
        )
        for permission in api_permissions:
            permission["azolAnnotations"] = {
                    "permissionName": appPermissionNameMap[permission["appRoleId"]]
            }
        return api_permissions

    def get_delegated_permissions( self, sp_object_id ):
        """Get all the delegated permissions assigned to a service principal.

        Get all the API permissions assigned to a service principal. 

        Includes all users that have consented to the permission.
        Principal Id displayNames are annotated at runtime for human readability.

        Args:
            - sp_object_id - (string) The object ID of a service principal

        Returns:
           A dictionary containing the service principal and
           its consented delegated permissions 

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        delegated_permissions = (
            self.call(f"/servicePrincipals/{sp_object_id}/oauth2PermissionGrants")
            .get().values()
        )
        annotated_permissions=[]
        for p in delegated_permissions:
            annotated_permission = p.copy()
            if p["consentType"] == "AllPrincipals":
                annotated_permission["principalName"] = "all"
            else:
                obj = (
                    self.call(f"/directoryObjects/{p['principalId']}")
                    .get().json()
                )
                principal_name = obj["userPrincipalName"]
                annotated_permission[ "principalName" ] = principal_name
            annotated_permissions.append(annotated_permission)
        return annotated_permissions

    def get_all_principals( self ):
        """Get all principals in the directory.

        Get all users, service principals, and groups in the directory.

        These are the objects that may be assigned permissions in M365 and Azure. 

        Returns:
           A dictionary mapping object ids to users, groups and service principals

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        users=self.get_all_users()
        service_principals=self.get_all_service_principals()
        groups=self.get_all_groups()
        principals = {}
        for directory_object in users:
            val = {
                "displayName": directory_object["displayName"],
                "principalType": "User"
            }
            key = directory_object["id"]
            principals[key] = val

        for directory_object in service_principals:
            val = {
                "displayName": directory_object["displayName"],
                "principalType": "ServicePrincipal"
            }
            key = directory_object["id"]
            principals[key] = val

        for directory_object in groups:
            val = {
                "displayName": directory_object["displayName"],
                "principalType": "Group"
            }
            key = directory_object["id"]
            principals[key] = val

        return principals

    def add_app_secret( self, app_object_id, name="inconspicuous" ):
        """Add a secret to a service principal in Entra ID.

        Args:
            - app_object_id - (string) the object ID of the Entra ID
                                application for which to generate a new secret
            - name - (string) The name of the new secret.

        Returns:
           A dictionary containing the properties for the new app secret

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        body= {
            "passwordCredential": {
                "displayName": name
            }
        }
        return (
            self.call(f"/applications/{app_object_id}/addPassword")
            .body(body)
            .post()
            .json()
        )

    def add_sp_secret( self, sp_object_id, name="inconspicuous" ):
        """Add a secret to an application object in Entra ID.

        Args:
            - sp_object_id - (string) the object ID of the Entra ID
                            service principal for which to generate a new secret.
            - name - (string) The name of the new secret.

        Returns:
           A dictionary containing the properties for the new sp secret

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        body= {
            "passwordCredential": {
                "displayName": name
            }
        }
        return (
            self.call(f"/servicePrincipals/{sp_object_id}/addPassword")
            .body(body)
            .post()
            .json()
        )

    def get_directory_object( self, object_id ):
        """Get a directory object from its object id.

        Attempt to get a directory object from its object id. This could be any type
        of directory object. Useful when a guid is identified, and it is not clear what it is.

        Args:
            - object_id - (string) The directory object Id.

        Returns:
           A dictionary containing information from graph about the object

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call(f"/directoryObjects/{object_id}")
            .get().json()
        )

    def try_get_object_type( self, object_id ):
        """Get a directory object type from its object id.

        Attempt to get a directory object's type base on its object id. This could be any type
        of directory object. Useful when a guid is identified, and it is not clear what it is.

        Args:
            - object_id - (string) The directory object Id.

        Returns:
           (string) the type of the directory object, from Graph, or None if it is not a
                    directory object

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        body = (
            self.call(f"/directoryObjects/{object_id}")
            .get().json()
        )
        if "@odata.type" in body:
            return body["@odata.type"]
        return None

    def get_all_service_principal_federated_identities( self ):
        """Get all federated identities for service principals in the tenant.

        Returns:
           A list of federated identity objects for service principals with a federated identity

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/servicePrincipals")
            .expand("federatedIdentityCredentials")
            .select("federatedIdentityCredentials", "id", "appId", "displayName")
            .filter("not(federatedIdentityCredentials/$count eq 0)")
            .header("ConsistencyLevel", "eventual")
            .get().values()
        )

    def get_all_application_federated_identities( self ):
        """Get all federated identities for applications in the tenant.

        Returns:
           A list of federated identity objects for applications with a federated identity

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return (
            self.call("/applications")
            .expand("federatedIdentityCredentials")
            .select("federatedIdentityCredentials", "id", "appId", "displayName")
            .filter("not(federatedIdentityCredentials/$count eq 0)")
            .header("ConsistencyLevel", "eventual")
            .get().values()
        )

    def create_new_local_service_principal( self, name="inconspicuous" ):
        """Create a new service principal.

        Create an application object an service principal in the current tenant of the client.
        Requires a user with an Entra ID role or a service principal with a graph API
        permission capable of creating service principals.

        Also creates a secret for this new service principal.

        Args:
            - name - (string) The name of the new service principal.

        Returns:
           (string) A dictionary containing properties for the new service principal,
                    including the newly created secret

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        body = {
            "displayName": name
        }
        app = (
            self.call("/applications")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

        app_id = app[ "appId" ]
        app_object_id = app[ "id" ]

        # Create the logcal service principal
        body = {
            "appId": app_id
        }
        sp = (
            self.call("/servicePrincipals")
            .body(body)
            .expect(201)
            .post()
            .json()
        )

        sp_id = sp[ "id" ]

        # create a secret for the service principal
        body = {
            "passwordCredential": {
                "displayName": "inconspicuous"
            }
        }
        secret = (
            self.call(f"/servicePrincipals/{sp_id}/addPassword")
            .body(body)
            .post()
            .json()
        )[ "secretText" ]

        output = {
            "clientId": app_id,
            "appObjectId": app_object_id,
            "spId": sp_id,
            "spSecret": secret
        }

        return output

    def create_new_remote_service_principal( self, client_id ):
        """Create a new service principal referencing a remote application.

        Create avservice principal in the current tenant of the client.
        This service principall will reference an application in another directory.

        This means the application object in the other directory may be used to access
        the permissions of this principal

        Requires a user with an Entra ID role or a service principal with a graph API
        permission capable of creating service principals.

        Args:
            - client_id - (string) The client id of the service principal.

        Returns:
           (string) A dictionary containing properties for the new service principal

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        # Create the service principal
        body = {
            "appId": client_id
        }
        sp = (
            self.call("/servicePrincipals")
            .body(body)
            .expect(201)
            .post()
            .json()
        )
        sp_id = sp[ "id" ]

        output = {
            "clientId": client_id,
            "spId": sp_id
        }

        return output

    def get( self, path, headers={} ):
        """Make a get request to a specific API path within the Graph API.

        Args:
            - path - (string) The graph API path.

        Returns:
           Request.Response object from the GET request

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        if "?" in path:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(path)
            rel = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
            query = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
            return (
                self.call(rel)
                .params(query)
                .headers(headers)
                .get()
                .json()
            )
        builder = self.call(path)
        for key, value in headers.items():
            builder = builder.header(key, value)
        return builder.get().json()

    def post( self, path, data ):
        """Send a POST request to Graph, and return the raw results

        Calls Graph at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on Graph
            data - (dict) The JSON data to send to Graph in the API request body

        Returns:
            A dictionary containing the raw results from the ARM request.

        """
        return self.call(path).body(data).post().json()

    def put( self, path, data ):
        """Send a PUT request to Graph, and return the raw results

        Calls Graph at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on Graph
            data - (dict) The JSON data to send to Graph in the API request body

        Returns:
            A dictionary containing the raw results from the ARM request.

        """
        return self.call(path).body(data).put().json()

    def patch( self, path, data ):
        """Send a PATCH request to Graph, and return the raw results

        Calls Graph at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on Graph
            data - (dict) The JSON data to send to Graph in the API request body

        Returns:
            A dictionary containing the raw results from the ARM request.

        """
        return self.call(path).body(data).patch().json()

    def delete( self, path ):
        """Make a DELETE request to a specific API path within the Graph API.

        Args:
            - path - (string) The graph API path.

        Returns:
           Request.Response object from the DELETE request

        Raises:
            AzolHTTPError: An error occurred accessing the Graph API
        """
        return self.call(path).delete().json()
