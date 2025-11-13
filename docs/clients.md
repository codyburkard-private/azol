---
title: Clients
---

# API Clients

Azol provides several HTTP clients for interacting with Azure services. All clients inherit from `OAuthHTTPClient` and handle authentication automatically.

## OAuthHTTPClient

Base class for all OAuth HTTP clients. Provides token management and OAuth flow handling.

### Constructor Parameters

- `cred` - Credential object (User, ServicePrincipal, etc.)
- `oauth_resource` - OAuth resource identifier (e.g., `OAuthResourceIDs.Arm`)
- `base_url` - Base URL for API requests
- `tenant` - Tenant ID or domain name
- `oauth_flow` - OAuth flow to use (defaults to credential's default flow)
- `scopes` - List of OAuth scopes to request
- `use_persistent_cache` - Whether to use persistent token cache (default: True)
- `auto_refresh` - Automatically refresh expired tokens (default: True)

### Methods

#### `fetch_token()`
Fetch a new access token and cache it.

**Example:**
```python
client.fetch_token()
```

#### `get_current_token()`
Get the currently cached access token.

**Returns:** Raw JWT token string or None

**Example:**
```python
token = client.get_current_token()
```

#### `get_current_refresh_token()`
Get the current refresh token.

**Returns:** Refresh token string or None

**Example:**
```python
refresh = client.get_current_refresh_token()
```

#### `refresh_token()`
Force refresh using the refresh token.

**Example:**
```python
client.refresh_token()
```

#### `get_token_claims()`
Get claims from the current token.

**Returns:** Dictionary containing token claims

**Example:**
```python
claims = client.get_token_claims()
print(claims['upn'])
print(claims['tid'])
```

#### `switch_tenant(tenant)`
Switch to a different tenant.

**Parameters:**
- `tenant` - Tenant ID or domain name

**Example:**
```python
client.switch_tenant("another-tenant.com")
```

#### `switch_scope(scopes, default, profile, offline_access, openid)`
Change the OAuth scope.

**Parameters:**
- `scopes` - List of scope strings
- `default` - Use default scope for resource
- `profile` - Include profile scope
- `offline_access` - Include offline_access scope
- `openid` - Include openid scope

**Example:**
```python
client.switch_scope(
    scopes=["User.Read", "Mail.Read"],
    default=False,
    profile=True,
    offline_access=True,
    openid=True
)
```

#### `switch_client(client_id)`
Switch to a different OAuth client (FOCI abuse).

**Parameters:**
- `client_id` - Client ID to switch to

**Example:**
```python
client.switch_client("00000000-0000-0000-0000-000000000000")
```

#### `refresh_to_new_resource(oauth_http_client_class)`
Create a new client for a different resource using the same refresh token.

**Parameters:**
- `oauth_http_client_class` - Client class to create (e.g., `ArmClient`, `GraphClient`)

**Returns:** New client instance

**Example:**
```python
# Switch from Graph to ARM
arm_client = graph_client.refresh_to_new_resource(ArmClient)
```

#### `from_client(client, *args, **kwargs)` (Class Method)
Create a new client from an existing client.

**Example:**
```python
# Create ARM client from Graph client
arm_client = ArmClient.from_client(graph_client)
```

---

## ArmClient

An HTTP client for interacting with the Azure Resource Manager API.

### Constructor

```python
ArmClient(tenant, cred, principal_lookup_table=None, ignore_providers=False, **kwargs)
```

**Parameters:**
- `tenant` - Tenant ID or domain name
- `cred` - Credential object
- `principal_lookup_table` - Optional lookup table for principals
- `ignore_providers` - Skip fetching providers on init (default: False)

### Methods

#### `get_tenants()`
Get user's tenants.

**Returns:** List of dictionaries containing tenant information

**Raises:** `ArmRequestFailedException`

**Example:**
```python
tenants = arm_client.get_tenants()
for tenant in tenants:
    print(tenant["defaultDomain"])
```

#### `get_management_groups(expand=False)`
Get all management groups.

**Parameters:**
- `expand` - Return full API output or abbreviated version

**Returns:** List of management group dictionaries or IDs

**Example:**
```python
mgroups = arm_client.get_management_groups()
```

#### `get_subscriptions(expand=False)`
Get all subscriptions.

**Parameters:**
- `expand` - Return full API output or abbreviated version

**Returns:** List of subscription dictionaries or subscription IDs

**Example:**
```python
subscriptions = arm_client.get_subscriptions()
for sub_id in subscriptions:
    print(sub_id)
```

#### `get_resource_groups(subscriptions=None)`
Get all resource groups.

**Parameters:**
- `subscriptions` - Optional list of subscription IDs to enumerate

**Returns:** List of resource group IDs

**Example:**
```python
rgs = arm_client.get_resource_groups()
```

#### `get_providers()`
Get ARM providers and API versions.

**Returns:** Dictionary mapping provider namespaces to API versions

**Example:**
```python
providers = arm_client.get_providers()
```

#### `get_resource(resource_id, api_version=None)`
Get an individual resource.

**Parameters:**
- `resource_id` - ARM resource ID
- `api_version` - Optional API version (auto-resolved if None)

**Returns:** `GenericResource` object

**Example:**
```python
resource = arm_client.get_resource("/subscriptions/.../resourceGroups/.../providers/...")
print(resource.name)
```

#### `get_resources(resource_type=None, subscriptions=None, ignore_subscriptions=None)`
Get all resources.

**Parameters:**
- `resource_type` - Optional resource type filter (e.g., "Microsoft.Compute/virtualMachines")
- `subscriptions` - Optional list of subscription IDs
- `ignore_subscriptions` - Optional list of subscription IDs to ignore

**Returns:** List of `GenericResource` objects

**Example:**
```python
# Get all resources
resources = arm_client.get_resources()

# Get only VMs
vms = arm_client.get_resources(resource_type="Microsoft.Compute/virtualMachines")
```

---

## GraphClient

An HTTP client for interacting with the Microsoft Graph API.

### Constructor

```python
GraphClient(tenant, cred, base_url=GRAPHBETAURL, **kwargs)
```

### Methods

#### `get_all_users(select=None)`
Get all users in the directory.

**Parameters:**
- `select` - Optional list of properties to select

**Returns:** List of user dictionaries

**Example:**
```python
users = graph_client.get_all_users(select=['userPrincipalName', 'mail', 'displayName'])
```

#### `get_all_groups(owners=False)`
Get all groups.

**Parameters:**
- `owners` - Include group owners in response

**Returns:** List of group dictionaries

**Example:**
```python
groups = graph_client.get_all_groups(owners=True)
```

#### `get_all_groups_and_owners()`
Get all groups with their owners.

**Returns:** List of group dictionaries with owner information

**Example:**
```python
groups = graph_client.get_all_groups_and_owners()
```

#### `get_directory_role_definitions()`
Get all directory role definitions.

**Returns:** List of role definition dictionaries

**Example:**
```python
roles = graph_client.get_directory_role_definitions()
```

#### `get_directory_role_assignments()`
Get all directory role assignments.

**Returns:** List of role assignment dictionaries

**Example:**
```python
assignments = graph_client.get_directory_role_assignments()
```

#### `add_directory_role_assignment(role_definition_id, principal_id)`
Assign a directory role to a principal.

**Parameters:**
- `role_definition_id` - Role definition ID
- `principal_id` - Principal (user/SP) object ID

**Returns:** Assignment dictionary

**Example:**
```python
assignment = graph_client.add_directory_role_assignment(
    role_definition_id="role-id",
    principal_id="principal-id"
)
```

#### `create_new_local_service_principal(name)`
Create a new service principal.

**Parameters:**
- `name` - Display name for the service principal

**Returns:** Dictionary with `clientId`, `spSecret`, and `spId`

**Example:**
```python
sp = graph_client.create_new_local_service_principal("MyApp")
print(f"Client ID: {sp['clientId']}")
print(f"Secret: {sp['spSecret']}")
```

---

## KeyVaultClient

An HTTP client for interacting with Azure Key Vaults.

### Constructor

```python
KeyVaultClient(key_vault_name, cred, tenant, **kwargs)
```

**Parameters:**
- `key_vault_name` - Name of the key vault
- `cred` - Credential object
- `tenant` - Tenant ID or domain name

### Methods

#### `get_secrets()`
Get all secrets in the key vault.

**Returns:** List of secret metadata dictionaries

**Example:**
```python
secrets = kv_client.get_secrets()
for secret in secrets:
    print(secret['name'])
```

#### `get_secret(secret_name, secret_version=None)`
Get a secret value.

**Parameters:**
- `secret_name` - Name of the secret
- `secret_version` - Optional version (defaults to latest)

**Returns:** Secret value string

**Example:**
```python
secret_value = kv_client.get_secret("my-secret")
```

#### `get_keys()`
Get all keys in the key vault.

**Returns:** List of key metadata dictionaries

**Example:**
```python
keys = kv_client.get_keys()
```

#### `get_certificates()`
Get all certificates in the key vault.

**Returns:** List of certificate metadata dictionaries

**Example:**
```python
certs = kv_client.get_certificates()
```

---

## AzureDevOpsClient

An HTTP client for interacting with the Azure DevOps API.

### Constructor

```python
AzureDevOpsClient(cred, tenant, **kwargs)
```

### Methods

#### `get_organizations()`
Get all organizations accessible to the credential.

**Returns:** List of organization dictionaries

**Example:**
```python
orgs = devops_client.get_organizations()
```

#### `get_projects(org_name)`
Get all projects in an organization.

**Parameters:**
- `org_name` - Organization name

**Returns:** List of project dictionaries

**Example:**
```python
projects = devops_client.get_projects("myorg")
```

#### `get_service_connections(org_name, project_name)`
Get all service connections in a project.

**Parameters:**
- `org_name` - Organization name
- `project_name` - Project name

**Returns:** List of service connection dictionaries

**Example:**
```python
connections = devops_client.get_service_connections("myorg", "myproject")
```

#### `get_agent_pools(org_name)`
Get all agent pools in an organization.

**Parameters:**
- `org_name` - Organization name

**Returns:** List of agent pool dictionaries

**Example:**
```python
pools = devops_client.get_agent_pools("myorg")
```

#### `create_agent(org_name, pool_id, name)`
Create a new DevOps agent.

**Parameters:**
- `org_name` - Organization name
- `pool_id` - Agent pool ID
- `name` - Agent name

**Returns:** Tuple of (agent_data, rsa_parameters)

**Example:**
```python
agent_data, rsa_params = devops_client.create_agent("myorg", pool_id, "myagent")
```

---

## DataFactoryClient

An HTTP client for the internal Data Factory API.

### Constructor

```python
DataFactoryClient(authentication_key, ir_node_id=None, spoofed_ir_name="Default")
```

**Parameters:**
- `authentication_key` - Data Factory IR authentication key
- `ir_node_id` - Optional existing IR node ID
- `spoofed_ir_name` - Name for spoofed IR node

### Methods

#### `get_managed_identity_token(oauth_resource)`
Get a managed identity token.

**Parameters:**
- `oauth_resource` - OAuth resource (e.g., "https://management.azure.com/")

**Returns:** Access token string

**Example:**
```python
token = df_client.get_managed_identity_token("https://management.azure.com/")
```

#### `spoof_shir(poll_interval=3, job_callback=None)`
Register a spoofed self-hosted integration runtime and poll for jobs.

**Parameters:**
- `poll_interval` - Polling interval in seconds
- `job_callback` - Optional callback function for processing jobs

**Example:**
```python
def process_job(job):
    print(f"Got job: {job}")

df_client.spoof_shir(poll_interval=5, job_callback=process_job)
```

---

## KuduClient

An HTTP client for interacting with Kudu/SCM APIs.

### Constructor

```python
KuduClient(site_name, cred, tenant, **kwargs)
```

**Parameters:**
- `site_name` - App Service site name
- `cred` - Credential object
- `tenant` - Tenant ID or domain name

### Methods

#### `get_scm_env_vars()`
Get SCM environment variables.

**Returns:** Dictionary of environment variables

**Example:**
```python
env_vars = kudu_client.get_scm_env_vars()
```

---

## AzureDevOpsAgentClient

An HTTP client for interacting with Azure DevOps agents.

### Constructor

```python
AzureDevOpsAgentClient(org_name, pool_id, agent_id, rsa_parameters, message_callback=None)
```

**Parameters:**
- `org_name` - Organization name
- `pool_id` - Agent pool ID
- `agent_id` - Agent ID
- `rsa_parameters` - RSA parameters for authentication
- `message_callback` - Optional callback for processing messages

### Methods

#### `connect()`
Connect to the agent service.

**Example:**
```python
agent_client.connect()
```

#### `disconnect()`
Disconnect from the agent service.

**Example:**
```python
agent_client.disconnect()
```

---

## Exceptions

All clients may raise the following exceptions:

- `ArmRequestFailedException` - ARM API request failed
- `GraphRequestFailedException` - Graph API request failed
- `ScmRequestFailedException` - Kudu/SCM API request failed
- `DevOpsAgentAuthenticationException` - DevOps agent authentication failed
- `DevOpsAgentSessionExistsAzolException` - Agent session already exists
- `DevOpsAgentSessionCreationException` - Failed to create agent session

