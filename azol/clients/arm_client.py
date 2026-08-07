"""A module containing a client for interacting with the ARM API.

Typical usage example:

    cred=User(username="username@domain.com")
    client=ArmClient(tenant="tenant.com", cred=cred)
    users=client.get_all_users()

"""
from typing import Any
import logging

from azol.clients.arm import ArmCall
from azol.clients.oauth_http_client import OAuthHTTPClient
from azol.constants import OAuthResourceIDs, ARMURL
from azol.http import AzolError
from azol.models.generic_resource import GenericResource
from azol.resources.rbac_roles import rbac_roles
from azol.utils import parse_jwt


class AzolArmUnsupportedException(AzolError):
    """
        Generic exception that is raised if something is not supported on the client
    """

class ArmClient( OAuthHTTPClient ):
    """
        An HTTP client for interacting with the Azure Resource Manager API
    """

    def __init__( self, *args, principal_lookup_table=None, ignore_providers=False, **kwargs ):
        super().__init__( oauth_resource=OAuthResourceIDs.Arm, base_url=ARMURL, *args, **kwargs)

        # get all providers immediately when logging in
        if not ignore_providers:
            self.providers=self.get_providers()
        self.principal_lookup_table=principal_lookup_table

    def call(self, path: str) -> ArmCall:
        """Return a fluent ARM call bound to this client.

        Failures raise ``AzolHTTPError`` (or a status-specific subclass such as
        ``AzolClientError`` / ``AzolServerError``).
        """
        return ArmCall(self, path)

    def get_tenants( self ) -> list[Any]:
        """Get user's tenants.
        
        Get tenants that the client's credential has access to.
        ARM only allows this API call with credential type is not "User".

        Returns:
            A dict containing the response from the ARM '/tenants' API.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return self.call("/tenants").api_version("2020-01-01").get().values()

    def get_management_groups( self, expand: bool=False ) -> list[Any]:
        """Get management groups
        
        Get all management groups that the current credentials have access to.
        
        Args:
            expand - (bool) Return the full ARM API output, or an abreviated version.

        Returns:
            A list of dicts containing management group metadata,
            or a list of management group ids if abreviated.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        management_group_raw_list = (
            self.call("/providers/Microsoft.Management/managementGroups")
            .api_version("2020-05-01")
            .get()
            .values()
        )

        if expand:
            return management_group_raw_list

        management_group_ids = [  mgroup[ "id" ] for mgroup in management_group_raw_list ]
        return management_group_ids

    def get_subscriptions( self, expand: bool=False ) -> list[Any]:
        """Get subscriptions
        
        Get all subscriptions that the current credentials have access to.
        
        Args:
            expand - (bool) Return the full ARM API output, or an abreviated version.

        Returns:
            A list of dicts containing subscription metadata, or a list of subscriptions ids
            if abreviated

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        subscriptions_raw_list = (
            self.call("/subscriptions").api_version("2019-03-01").get().values()
        )

        if expand:
            return subscriptions_raw_list

        subscription_ids = [ subDict[ 'subscriptionId' ] for subDict in subscriptions_raw_list ]
        return subscription_ids

    def get_resource_groups( self, subscriptions: Any | None=None ) -> list[Any]:
        """Get resource groups
        
        Get all resource groups that the current credentials have access to.
        
        Args:
            subscriptions - (list) Default None. A list of subscriptions to enumerate. If None, 
                            enumerate all subscriptions

        Returns:
            A list of resource group ids

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        if subscriptions is None:
            subscriptions_raw_list = (
                self.call("/subscriptions").api_version("2019-03-01").get().values()
            )
            subscriptions_abreviated_list = [ subDict[ 'subscriptionId' ]
                                             for subDict in subscriptions_raw_list ]
        else:
            subscriptions_abreviated_list = subscriptions
        resource_groups = []
        for subscription in subscriptions_abreviated_list:
            resource_groups += (
                self.call(f"/subscriptions/{subscription}/resourceGroups")
                .api_version("2019-03-01")
                .get()
                .values()
            )

        resource_group_ids = [ rgDict[ 'id' ] for rgDict in resource_groups ]
        return resource_group_ids

    def get_providers( self ) -> list[Any]:
        """Get azure providers
        
        Get ARM providers and api versions (/providers API).

        Returns:
            A dictionary containing the provider namespace mapped
            to a list of api versions

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        json_response = self.call("/providers").api_version("2023-07-01").get().json()
        try:
            providers={}
            for p in json_response["value"]:
                providers[p["namespace"].lower()] = {}
                for resource_type in p["resourceTypes"]:
                    rt=resource_type["resourceType"].lower()
                    ns=p["namespace"].lower()
                    providers[ns][rt] = resource_type["apiVersions"]

            return providers
        except Exception as e:
            logging.error("Unable to automatically fetch providers in the tenant."
                          " provider version auto-resolution will fail")     
            raise AzolArmUnsupportedException() from e

    def get_resource( self, resource_id: str, api_version: str | None=None ) -> dict[str, Any]:
        """Get an individual resource.
        
        Get the resource properties of a specific resource.
        
        
        Args:
            resource_id - (str) required. The ARM resource Id of the resource.

            api_version - (str) Default None. The API version of the provider to use in the ARM
                         request. If None, azol will attempt to auto-resolve the resource type and
                         use the latest known version of the provider from the last build.

        Returns:
            GenericResource object

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        # extract the resource provider name from the resource id
        namespace = resource_id.split('/providers/')[-1].split("/")[0].lower()
        provider = "/".join(resource_id.split('/providers/')[-1].split("/")[1:-1]).lower()

        provider_versions=self.providers[namespace][provider]
        latest=provider_versions[0]

        if api_version is None:
            api_version = latest
        json_response = self.call(resource_id).api_version(api_version).get().json()
        # sometimes value isnt actually required...
        if "value" in json_response.keys():
            resource = json_response[ "value" ]
        else:
            resource = json_response
        new_resource = self._deserialize_resource(resource)
        return new_resource

    def get_resources( self, resource_type: Any | None=None, subscriptions: Any | None=None, ignore_subscriptions: Any | None=None ) -> list[Any]:
        """Get all resources.
        
        Get all resources that the client's credential has access to.

        This will not return the resource's properties - this is not supported in a single ARM
        request.
        
        Args:
            resource_type - (str) Default None. Only get resources of this type.
                            Example: 'Microsoft.Network/virtualNetworks'

            subscriptions - (list) Default None. A list of subscription IDs
                            to enumerate.

            ignore_subscriptions - (list) Default None. A list of subscription IDs
                                   to ignore during enumeration of resources.

        Returns:
            A list of GenericResource objects

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        if subscriptions is None:
            subscriptions_raw_list = (
                self.call("/subscriptions").api_version("2019-03-01").get().values()
            )
            subscriptions_abreviated_list = [ subDict[ 'subscriptionId' ]
                                             for subDict in subscriptions_raw_list ]
        else:
            subscriptions_abreviated_list = subscriptions
        resources = []
        for subscription in subscriptions_abreviated_list:
            if ignore_subscriptions is not None and subscription in ignore_subscriptions:
                continue
            request = (
                self.call(f"/subscriptions/{subscription}/resources")
                .api_version("2019-03-01")
                .param(
                    "$expand",
                    "createdTime,changedTime,provisioningState,location,tags,type,properties",
                )
            )
            if resource_type is not None:
                request = request.filter(f"resourceType eq '{resource_type}'")
            for resource in request.get().values():
                new_resource = self._deserialize_resource(resource)
                resources.append(new_resource)

        return resources

    def get_resource_ids( self, resource_type: Any | None=None, subscriptions: Any | None=None, ignore_subscriptions: Any | None=None ) -> list[Any]:
        """Get all resource ids.
        
        Get the resource ids of all resources the client has access to
        
        Args:
            resource_type - (str) Default None. Only get resources of this type.
                            Example: 'Microsoft.Network/virtualNetworks'

            subscriptions - (list) Default None. A list of subscription IDs
                            to enumerate.

            ignore_subscriptions - (list) Default None. A list of subscription IDs
                                   to ignore during enumeration of resources.

        Returns:
            a list of resource ids

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        if subscriptions is None:
            subscriptions_raw_list = (
                self.call("/subscriptions").api_version("2019-03-01").get().values()
            )
            subscriptions_abreviated_list = [ subDict[ 'subscriptionId' ]
                                             for subDict in subscriptions_raw_list ]
        else:
            subscriptions_abreviated_list = subscriptions
        resources = []
        for subscription in subscriptions_abreviated_list:
            if ignore_subscriptions is not None and subscription in ignore_subscriptions:
                continue
            request = (
                self.call(f"/subscriptions/{subscription}/resources")
                .api_version("2019-03-01")
            )
            if resource_type is not None:
                request = request.filter(f"resourceType eq '{resource_type}'")
            resources += request.get().values()
        resources_abreviated_list = [ rDict[ 'id' ] for rDict in resources ]
        return resources_abreviated_list

    def get_rbac_role_definition_map( self ) -> list[Any]:
        """Get a dict of role definition ids mapped to names
        
        Enumerate all role definitions, and return a dictionary mapping all ids to names.

        This is helpful when performing data annotations of raw data gathered from a tenant.

        Returns:
            A dict mapping role definition ids to role definition names.
        """
        arm_roles_map = {}
        # enumerate management groups first
        management_group_permissions = True
        management_groups = self.get_management_groups( expand=False )
        if management_groups is None:
            management_group_permissions = False

        if management_group_permissions:
            for managementgroup in management_groups:
                definitions = (
                    self.call(
                        f"{managementgroup}/providers/"
                        "Microsoft.Authorization/roleDefinitions"
                    )
                    .api_version("2015-07-01")
                    .get()
                    .values()
                )
                temp_arm_roles_list = [ { "name": definition["properties"][ "roleName" ],
                                            "id": definition[ "id" ] } for definition
                                            in definitions ]
                for role_definition in temp_arm_roles_list:
                    if role_definition['id'] in arm_roles_map.keys():
                        pass
                    arm_roles_map[ role_definition['id'] ] = role_definition[ 'name' ]

        subscriptions = self.get_subscriptions( expand=False )
        for subscription in subscriptions:
            definitions = (
                self.call(
                    f"/subscriptions/{subscription}/providers/"
                    "Microsoft.Authorization/roleDefinitions"
                )
                .api_version("2015-07-01")
                .get()
                .values()
            )
            temp_arm_roles_list = [ { "name": definition["properties"][ "roleName" ],
                                        "id": definition[ "id" ] } for definition
                                        in definitions ]
            for role_definition in temp_arm_roles_list:
                if role_definition['id'] in arm_roles_map.keys():
                    pass
                arm_roles_map[ role_definition['id'] ] = role_definition[ 'name' ]

        return arm_roles_map

    def get_own_rbac_role_assignments(self) -> list[Any]:
        """
            Get all RBAC role assignments of the current identity

            Returns:
                A list of GenericResource ojects containing the RBAC assignments
        """
        user_id = parse_jwt(self.get_current_token())[1]["oid"]
        filter=f"principalId eq '{user_id}'"
        all_assignments = []
        subscriptions = self.get_subscriptions()
        for sub in subscriptions:
            new_assignments = (
                self.call(
                    f"/subscriptions/{sub}/providers/"
                    "Microsoft.Authorization/roleAssignments"
                )
                .api_version("2015-07-01")
                .filter(filter)
                .get()
                .values()
            )
            all_assignments += new_assignments
        known_ids = []
        final = []
        for i, ass in enumerate(all_assignments):
            if ass["id"] in known_ids:
                continue
            else:
                known_ids.append(ass["id"])
                final.append(ass)

        return final

    def get_rbac_role_assignments(self) -> list[Any]:
        """Get all RBAC role assignments
        
        Get all RBAC role assignments at all scopes in the tenant,
        with the client's current credential.
        
        If principal_lookup_table is populated in the client, it will be used to annotate the
        assignments with the displayNames of principal Ids.
        
        Returns:
            A list of GenericResource objects containing the RBAC assignments

        """
        role_assignments = []
        management_group_permissions = True
        management_groups = self.get_management_groups( expand=False )
        if management_groups is None:
            management_group_permissions = False

        if management_group_permissions:
            for managementgroup in management_groups:
                assignments = (
                    self.call(
                        f"{managementgroup}/providers/"
                        "Microsoft.Authorization/roleAssignments"
                    )
                    .api_version("2015-07-01")
                    .get()
                    .values()
                )
                for assignment in assignments:
                    if assignment[ "id" ] not in role_assignments:
                        role_assignments.append( assignment )

        resources = self.get_resource_ids()
        for resource in resources:
            assignments = (
                self.call(
                    f"{resource}/providers/"
                    "Microsoft.Authorization/roleAssignments"
                )
                .api_version("2015-07-01")
                .get()
                .values()
            )
            for assignment in assignments:
                if assignment[ "id" ] not in role_assignments:
                    role_assignments.append( assignment )

        #convert dictionaries to list of generic resources
        generic_resource_list=[]
        for resource in role_assignments:
            definition_id = resource[ "properties" ]["roleDefinitionId"]
            role_definition_name = rbac_roles[definition_id] if (
                    definition_id in rbac_roles.keys() ) else "unknown"
            annotations={
                "roleDefinitionName": role_definition_name
            }
            if self.principal_lookup_table:
                p_id = resource[ "properties" ]["principalId"]
                annotations[ "principalName" ] = self.principal_lookup_table[p_id]["displayName"]
            new_resource = self._deserialize_resource(resource)
            new_resource.azolAnnotations=annotations
            generic_resource_list.append(new_resource)

        return generic_resource_list

    def get_rbac_assignments_at_scope( self, scope: str ) -> list[Any]:
        """Get all RBAC role assignments at a given scope
        
        If principal_lookup_table is populated in the client, it will be used to annotate the
        assignments with the displayNames of principal Ids.
        
        Args:
            scope - (str) The id of a management group, subscription, resource group, or resource.

        Returns:
            A list of GenericResource objects containing rbac assignments

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        role_assignments = (
            self.call(f"{scope}/providers/Microsoft.Authorization/roleAssignments")
            .api_version("2022-04-01")
            .filter("atScope()")
            .get()
            .values()
        )
        #convert dictionaries to list of generic resources
        generic_resource_list=[]
        for resource in role_assignments:
            if resource["properties"]["scope"] != scope:
                continue
            definition_id = resource[ "properties" ]["roleDefinitionId"]
            role_definition_name = rbac_roles[definition_id] if (
                        definition_id in rbac_roles.keys() ) else "unknown"
            annotations={
                "roleDefinitionName": role_definition_name
            }
            if self.principal_lookup_table:
                principal_id = resource[ "properties" ]["principalId"]
                annotations[ "principalName" ] = self.principal_lookup_table[principal_id]["displayName"]
            new_resource = self._deserialize_resource(resource)
            new_resource.azolAnnotations=annotations
            generic_resource_list.append(new_resource)

        return generic_resource_list

    def elevate_access_as_global_admin( self ) -> Any:
        """Elevate access to Azure as Global Administrator.
        
        Toggle elevated access to Azure as a global administrator.
        This toggle sets the Global Administrator to User Access Administrator
        On the tenant scope of the directory.

        This only works if the current identity is a User, and is a Global Administrator
        
        Args:
            None

        Returns:
            dict containing raw ARM response 

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call("/providers/Microsoft.Authorization/elevateAccess")
            .api_version("2017-05-01")
            .post()
            .json()
        )

    def get_logic_app_runs( self, logic_app_resource_id: str ) -> list[Any]:
        """Get logic app run.
        
        Get metadata of logic app runs for a specific logic app
        
        Args:
            logic_app_resource_id - (str) The complete resource Id of the logic app

        Returns:
            A list of Generic Resource objects containing the logic app runs

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        resources = (
            self.call(f"{logic_app_resource_id}/runs")
            .api_version("2016-06-01")
            .get()
            .json()
        )
        deserialized_resource_list = []
        for resource in resources:
            new_resource = self._deserialize_resource(resource)
            deserialized_resource_list.append(new_resource)

        return deserialized_resource_list

    def get_logic_app_run_actions( self, logic_app_run_resource_id: str ) -> list[Any]:
        """Get logic app run actions.
        
        Get all run actions for a single logic app
        
        Args:
            logic_app_run_resource_id - (str) The complete resource Id of the logic app run

        Returns:
            Dictionary containing Logic App Actions

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{logic_app_run_resource_id}/actions")
            .api_version("2016-06-01")
            .get()
            .json()
        )

    def get_logic_app( self, logic_app_resource_id: str ) -> list[Any]:
        """Get a logic app.
        
        Get a logic app resource's properties
        
        Args:
            logic_app_resource_id - (str) The complete resource Id of the logic app

        Returns:
            GenericResource of the logic app

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        resource = (
            self.call(f"{logic_app_resource_id}")
            .api_version("2016-06-01")
            .get()
            .json()["value"]
        )
        new_resource = self._deserialize_resource(resource)
        return new_resource

    def get_logic_app_versions( self, logic_app_resource_id: str ) -> list[Any]:
        """Get a logic app's versions.
        
        Get a logic app resource's versions
        
        Args:
            logic_app_resource_id - (str) The complete resource Id of the logic app

        Returns:
            list of dictionaries containing all logic app versions

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{logic_app_resource_id}/versions")
            .api_version("2016-06-01")
            .get()
            .json()
        )

    def get_runbooks( self, automation_account_id: str ) -> list[Any]:
        """Get runbook metadata in an automation account.
        
        Get all runbook objects in an automation account.
        Calls the '/runbooks' endpoint.
        
        Args:
            automation_account_id - (str) The complete resource Id of the automation account

        Returns:
            dictionary containing a list of metadata for
            the runbooks in the automation account

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_id}/runbooks")
            .api_version("2019-06-01")
            .get()
            .values()
        )

    def get_runbook_content( self, automation_account_runbook_id: str ) -> list[Any]:
        """Get runbook content.
        
        Get the contents of a runbook.
        Calls the '/content' endpoint.
        
        Args:
            automation_account_runbook_id - (str) Complete resource Id of the automation account
                                            runbook

        Returns:
            (string) the raw contents of a runbook

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_runbook_id}/content")
            .api_version("2019-06-01")
            .get()
            .response
        )

    def get_runbook_draft_content( self, automation_account_runbook_id: str ) -> list[Any]:
        """Get runbook draft content.
        
        Get the draft contents of a runbook.
        Calls the '/draft/content' endpoint.
        
        Args:
            automation_account_runbook_id - (str) Complete resource Id of the automation account
                                            runbook

        Returns:
            (string) the raw contents of a runbook draft

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_runbook_id}/draft/content")
            .api_version("2019-06-01")
            .get()
            .response
        )

    def get_automation_webhooks( self, automation_account_id: str ) -> list[Any]:
        """Get automation account webhooks.
        
        Get the webhooks in an automation account.
        Calls the '/webhooks' endpoint.
        
        Args:
            automation_account_id - (str) Complete resource Id of the automation account

        Returns:
            List of dictionaries containing webhooks in the automation account

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_id}/webhooks")
            .api_version("2015-10-31")
            .get()
            .values()
        )

    def get_automation_variables( self, automation_account_id: str ) -> list[Any]:
        """Get automation account variables.
        
        Get the variables in an automation account.
        Calls the '/variables' endpoint.
        
        Args:
            automation_account_id - (str) Complete resource Id of the automation account

        Returns:
            List of dictionaries containing variables in the automation account

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_id}/variables")
            .api_version("2019-06-01")
            .get()
            .values()
        )

    def get_automation_jobs( self, automation_account_runbook_id: str ) -> list[Any]:
        """Get automation account runbook jobs.
        
        Get metadata on the jobs that have been run for an Automation Account runbook
        
        Args:
            automation_account_runbook_id - (str) Complete resource Id of the 
                                          automation account runbook

        Returns:
            A list of dictioaries containing metdata for automation account jobs.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_runbook_id}/jobs")
            .api_version("2019-06-01")
            .get()
            .values()
        )

    def get_automation_job_output( self, automation_account_job_id: str ) -> list[Any]:
        """Get automation account runbook job output.
        
        Get the job output of a specific automation account job

        
        Args:
            automation_account_job_id - (str) Complete resource Id of the
                                        automation account job

        Returns:
            string - raw ascii text of the job output

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{automation_account_job_id}/output")
            .api_version("2019-06-01")
            .get()
            .response
            .text
        )

    def get_deployment_history( self, scope: str ) -> list[Any]:
        """Get deployment history at a given scope
        
        Args:
            scope - (str) The resource ID of the scope for which to get deployment history

        Returns:
            A list of dictionaries containing the ARM deployments at the given scope

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(f"{scope}/providers/Microsoft.Resources/deployments/")
            .api_version("2021-04-01")
            .get()
            .json()
        )

    def get_current_user_pim_eligibility(self, scope: str) -> list[Any]:
        return (
            self.call(
                f"{scope}/providers/Microsoft.Authorization/"
                "roleEligibilityScheduleInstances"
            )
            .api_version("2020-10-01")
            .filter("asTarget()")
            .get()
            .json()
        )

    def get_descendants( self, management_group: str ) -> list[Any]:
        """Get direct descendants of a management group.

        This function will return subscriptions or management groups that are nested under
        the management group.
        
        Args:
            management_group - (str) the management group id to enumerate descendants

        Returns:
            A list of dictionaries containing the descendants of the management group

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(
                "/providers/Microsoft.Management/managementGroups"
                f"/{management_group}/descendants"
            )
            .api_version("2020-05-01")
            .get()
            .values()
        )
    
    def get_app_settings( self, resource_id: str ) -> list[Any]:
        """
            Get a dictionary containing key-values for all app service app settings.
        """
        settings = (
            self.call(f"{resource_id}/config/appsettings/list")
            .api_version("2024-04-01")
            .post()
            .json()["properties"]
        )
        return settings

    def get_app_service_processes(self, resource_id: str) -> list[Any]:
        """
           Get all processes running on the app service.
        """
        return (
            self.call(f"{resource_id}/processes")
            .api_version("2024-04-01")
            .get()
            .values()
        )

    def get_app_service_environment_variables(self, resource_id: str) -> list[Any]:
        """
           Get environment variales of the default process for an app service
           of function. Uses the ARM API. Only works for Windows as of may 2025 -
           alternatively, use kudu for linux with kuduClient

           resource_id: the resource id of an app service
        """
        app_svc=self.get_app_service(resource_id)
        if 'linux' in app_svc.kind:
            raise AzolArmUnsupportedException
        processes=self.get_app_service_processes(resource_id)
        default_process=None
        for proc in processes:
            if "user_name" in proc["properties"].keys() and "IIS APPPOOL" in proc["properties"]["user_name"]:
                default_process = proc["properties"]["id"]
        process=self.get_app_service_process(resource_id, default_process)
        environment_variables = process["properties"]["environment_variables"]
        return environment_variables        

    def get_app_service_process(self, resource_id: str, process_id: str) -> list[Any]:
        """
           Get details about the process running on the app service.

           resource_id: the resource id of an app service
           process_id: the process id to fetch
        """
        return (
            self.call(f"{resource_id}/processes/{process_id}")
            .api_version("2024-04-01")
            .get()
            .json()
        )

    def get_app_service_process_dump(self, resource_id: str, process_id: str) -> list[Any]:
        """
            Call the ARM API to dump the process memory on an app service

            resource_id: the resource id of an app service
            process_id: the process id to fetch
        """
        return (
            self.call(f"{resource_id}/processes/{process_id}/dump")
            .api_version("2024-04-01")
            .get()
            .response
            .content
        )

    def get_app_service(self, resource_id: str) -> list[Any]:
        """
            Get a specific app service, as well as its configurations and auth settings.
        """
        app_service = self.get_resource(resource_id)
        

        app_service.properties["config"] = {}
        configs = (
            self.call(f"{app_service.id}/config/web")
            .api_version("2024-04-01")
            .get()
            .json()["properties"]
        )
        app_service.properties["config"]["web"] = configs

        settings = (
            self.call(f"{app_service.id}/config/authSettingsV2")
            .api_version("2024-04-01")
            .get()
            .json()["properties"]
        )

        app_service.properties["config"]["authSettingsV2"] = settings
        return app_service

    def get_app_services_with_easy_auth(self) -> list[Any]:
        """
            Get all app services, as well as their configurations and auth settings. Only
            return the app services with easy auth
        """
        app_services = self.get_app_services()
        easy_auth_as=[]
        for app in app_services:
            if app.properties["config"]["authSettingsV2"]["platform"]["enabled"]:
                easy_auth_as.append(app)
        return easy_auth_as

    def get_functions_with_easy_auth(self) -> list[Any]:
        """
            Get all functions, as well as their configurations and auth settings. Only
            return the functions with easy auth
        """
        functions = self.get_functions()
        funcs=[]
        for func in functions:
            if func.properties["config"]["authSettingsV2"]["platform"]["enabled"]:
                funcs.append(func)
        return funcs

    def get_functions(self) -> list[Any]:
        """
            Get all functions, as well as their configurations and auth settings.
        """
        app_services_and_functions = self.get_resources(resource_type="Microsoft.Web/sites")
        app_services = []
        for res in app_services_and_functions:
            if "function" not in res.kind: continue
            if "workflow" in res.kind: continue
            app_services.append(res)

        for app_service in app_services:
            props = (
                self.call(f"{app_service.id}")
                .api_version("2024-04-01")
                .get()
                .json()["properties"]
            )
            app_service.properties = props

            app_service.properties["config"] = {}

            configs = (
                self.call(f"{app_service.id}/config/web")
                .api_version("2024-04-01")
                .get()
                .json()["properties"]
            )
            app_service.properties["config"]["web"] = configs

            settings = (
                self.call(f"{app_service.id}/config/authSettingsV2")
                .api_version("2024-04-01")
                .get()
                .json()["properties"]
            )

            app_service.properties["config"]["authSettingsV2"] = settings
        return app_services

    def get_app_services(self) -> list[Any]:
        """
            Get all app services, as well as their configurations and auth settings.
        """
        app_services_and_functions = self.get_resources(resource_type="Microsoft.Web/sites")
        app_services = []
        for res in app_services_and_functions:
            if "function" in res.kind: continue
            if "workflow" in res.kind: continue
            app_services.append(res)

        for app_service in app_services:
            props = (
                self.call(f"{app_service.id}")
                .api_version("2024-04-01")
                .get()
                .json()["properties"]
            )
            app_service.properties = props

            app_service.properties["config"] = {}

            configs = (
                self.call(f"{app_service.id}/config/web")
                .api_version("2024-04-01")
                .get()
                .json()["properties"]
            )
            app_service.properties["config"]["web"] = configs

            settings = (
                self.call(f"{app_service.id}/config/authSettingsV2")
                .api_version("2024-04-01")
                .get()
                .json()["properties"]
            )

            app_service.properties["config"]["authSettingsV2"] = settings
        return app_services

    def post( self, path: str, api_version: str, data: Any ) -> Any:
        """Send a POST request to ARM, and return the raw results

        Calls ARM at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on ARM
            api_version - (str) The api-version to call for the ARM API
            data - (dict) The JSON data to send to ARM in the API request body

        Returns:
            A dictionary containing the raw results from the ARM request.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(path).api_version(api_version).body(data).post().json()
        )

    def put( self, path: str, api_version: str, data: Any ) -> Any:
        """Send a PUT request to ARM, and return the raw results

        Calls ARM at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on ARM
            api_version - (str) The api-version to call for the ARM API
            data - (dict) The JSON data to send to ARM in the API request body

        Returns:
            A dictionary containing the raw results from the ARM request.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(path).api_version(api_version).body(data).put().json()
        )

    def patch( self, path: str, api_version: str, data: Any ) -> Any:
        """Send a PATCH request to ARM, and return the raw results

        Calls ARM at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on ARM
            api_version - (str) The api-version to call for the ARM API
            data - (dict) The JSON data to send to ARM in the API request body

        Returns:
            A dictionary containing the raw results from the ARM request.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        return (
            self.call(path).api_version(api_version).body(data).patch().json()
        )

    def get( self, path: str, api_version: str | None=None ) -> Any:
        """Send a GET request to ARM, and return the raw results

        Calls ARM at the path specified, and returns the raw deserialized results.
        
        Args:
            path - (str) The API path to call on ARM
            api_version - (str) The api-version to call for the ARM API

        Returns:
            A dictionary containing the raw results from the ARM request.

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API

        """
        if "/providers" not in path:
            namespace="microsoft.resources"
            provider=path.split("/")[1]
        else:    
            namespace_and_provider=path.split('/providers/')[-1]
            namespace_and_provider_list=namespace_and_provider.split("/")
            namespace = namespace_and_provider_list[0].lower()
            provider_and_resource = "/".join(namespace_and_provider_list[1:]).lower()
            matching_providers=[]
            for provider in self.providers[namespace].keys():
                if provider in provider_and_resource:
                    matching_providers.append(provider)
            provider=max(p for p in matching_providers)
            logging.info("Resolved namespace to ", namespace)
            logging.info("Resolved provider to ", provider)

        provider_versions=self.providers[namespace][provider]
        latest=provider_versions[0]
        logging.info("Resolved latest provider version to ", latest)
        api_version = latest
        return self.call(path).api_version(api_version).get().json()

    def delete( self, path: str ) -> Any:
        """Make a DELETE request to a specific API path within the ARM API.

        Args:
            - path - (string) The ARM API path.

        Returns:
           Request.Response object from the DELETE request

        Raises:
            AzolHTTPError: An error occurred accessing the ARM API
        """
        return self.call(path).delete().json()

    def _deserialize_resource( self, resource ):
        """Deserialize ARM output to a GenericResource

        Deserialize a raw JSON object from the ARM API resopnse into a generic resource
        in AZOL.

        Instantiates an object with all possible fields from ARM. If a property does not exist
        in the raw response, instantiate it to None
        
        Args:
            resource - (dict) dictionary containing the raw JSON from an ARM request

        Returns:
            GenericResource containing all deserialized properties.

        """
        r = GenericResource(
            id=resource[ "id" ],
            changedTime=resource[ "changedTime" ] if "changedTime" in resource.keys() else None,
            createdTime=resource[ "createdTime" ] if "createdTime" in resource.keys() else None,
            extendedLocation=resource[ "extendedLocation" ] if (
                "extendedLocation" in resource.keys() ) else None,
            identity=resource[ "identity" ] if "identity" in resource.keys() else None,
            kind=resource[ "kind" ] if "kind" in resource.keys() else None,
            location=resource[ "location" ] if 'location' in resource.keys() else None,
            managedBy=resource[ "managedBy" ] if "managedBy" in resource.keys() else None,
            name=resource[ "name" ],
            plan=resource[ "plan" ] if "plan" in resource.keys() else None,
            properties=resource[ "properties" ] if "properties" in resource.keys() else {},
            provisioningState=resource[ "provisioningState" ] if (
                "provisioningState" in resource.keys() ) else None,
            sku=resource[ "sku" ] if "sku" in resource.keys() else None,
            tags=resource[ "tags" ] if "tags" in resource.keys() else None,
            type=resource[ "type" ]
        )
        return r
