---
title: Arm Client
nav_order: 2
parent: Clients
---

# ArmClient

An HTTP client for interacting with the Azure Resource Manager API.

## Constructor

```python
ArmClient(tenant, cred, principal_lookup_table=None, ignore_providers=False, **kwargs)
```

**Parameters:**
- `tenant` - Tenant ID or domain name
- `cred` - Credential object
- `principal_lookup_table` - Optional lookup table for principals
- `ignore_providers` - Skip fetching providers on init (default: False)

## Methods

An HTTP client for interacting with the Azure Resource Manager API.

**Constructor Parameters:**
- `cred`: Credential object
- `tenant` (str): Tenant ID or domain name
- `principal_lookup_table` (dict, optional): Mapping of principal IDs to names
- `ignore_providers` (bool, optional): Skip loading providers on initialization

**Methods:**

### `get_tenants()`
Get all tenants the credential has access to.

**Example:**
```python
from azol import User, ArmClient

cred = User(username="user@domain.com")
client = ArmClient(tenant="tenant.com", cred=cred)
tenants = client.get_tenants()
for tenant in tenants:
    print(tenant['tenantId'])
```

### `get_subscriptions(expand=False)`
Get all subscriptions.

**Example:**
```python
subscriptions = client.get_subscriptions()
for sub_id in subscriptions:
    print(sub_id)
```

### `get_management_groups(expand=False)`
Get all management groups.

**Example:**
```python
mg_groups = client.get_management_groups()
```

### `get_resource_groups(subscriptions=None)`
Get all resource groups.

**Example:**
```python
resource_groups = client.get_resource_groups()
for rg_id in resource_groups:
    print(rg_id)
```

### `get_resources(resource_type=None, subscriptions=None, ignore_subscriptions=None)`
Get all resources with optional filtering.

**Example:**
```python
# Get all virtual networks
vnets = client.get_resources(
    resource_type='Microsoft.Network/virtualNetworks'
)
for vnet in vnets:
    print(vnet.name, vnet.location)
```

### `get_resource(resource_id, api_version=None)`
Get a specific resource by its ID.

**Example:**
```python
resource = client.get_resource(
    "/subscriptions/sub-id/resourceGroups/rg-name/providers/Microsoft.Compute/virtualMachines/vm-name"
)
print(resource.properties)
```

### `get_rbac_role_assignments()`
Get all RBAC role assignments.

**Example:**
```python
assignments = client.get_rbac_role_assignments()
for assignment in assignments:
    print(assignment.id)
```

### `get_rbac_assignments_at_scope(scope)`
Get RBAC assignments at a specific scope.

**Example:**
```python
assignments = client.get_rbac_assignments_at_scope(
    "/subscriptions/00000000-0000-0000-0000-000000000000"
)
```

### `get_own_rbac_role_assignments()`
Get RBAC assignments of the current identity.

**Example:**
```python
my_assignments = client.get_own_rbac_role_assignments()
```

### `elevate_access_as_global_admin()`
Elevate access as a Global Administrator.

**Example:**
```python
response = client.elevate_access_as_global_admin()
```

### `get_app_services()`
Get all app services with configurations.

**Example:**
```python
app_services = client.get_app_services()
for app in app_services:
    print(app.name, app.properties['config'])
```

### `get_app_service(resource_id)`
Get a specific app service.

**Example:**
```python
app = client.get_app_service(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Web/sites/myapp"
)
```

### `get_app_services_with_easy_auth()`
Get app services that have Easy Auth enabled.

**Example:**
```python
easy_auth_apps = client.get_app_services_with_easy_auth()
```

### `get_functions()`
Get all Azure Functions with configurations.

**Example:**
```python
functions = client.get_functions()
```

### `get_functions_with_easy_auth()`
Get functions with Easy Auth enabled.

**Example:**
```python
easy_auth_funcs = client.get_functions_with_easy_auth()
```

### `get_app_settings(resource_id)`
Get app settings for an app service or function.

**Example:**
```python
settings = client.get_app_settings(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Web/sites/myapp"
)
```

### `get_app_service_environment_variables(resource_id)`
Get environment variables for an app service (Windows only).

**Example:**
```python
env_vars = client.get_app_service_environment_variables(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Web/sites/myapp"
)
```

### `get_runbooks(automation_account_id)`
Get runbooks in an automation account.

**Example:**
```python
runbooks = client.get_runbooks(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Automation/automationAccounts/myaccount"
)
```

### `get_runbook_content(automation_account_runbook_id)`
Get the content of a runbook.

**Example:**
```python
content = client.get_runbook_content(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Automation/automationAccounts/myaccount/runbooks/myrunbook"
)
print(content.text)
```

### `get_automation_variables(automation_account_id)`
Get variables in an automation account.

**Example:**
```python
variables = client.get_automation_variables(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Automation/automationAccounts/myaccount"
)
```

### `get_logic_app(logic_app_resource_id)`
Get a logic app resource.

**Example:**
```python
logic_app = client.get_logic_app(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Logic/workflows/myworkflow"
)
```

### `get_deployment_history(scope)`
Get deployment history at a scope.

**Example:**
```python
deployments = client.get_deployment_history(
    "/subscriptions/00000000-0000-0000-0000-000000000000"
)
```

### `get(path, api_version=None)`
Make a raw GET request to ARM.

**Example:**
```python
response = client.get("/subscriptions")
```

### `post(path, api_version, data)`
Make a raw POST request to ARM.

**Example:**
```python
response = client.post(
    "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Resources/deployments/deploy1",
    "2021-04-01",
    {"properties": {...}}
)
```

### `put(path, api_version, data)`
Make a raw PUT request to ARM.

### `patch(path, api_version, data)`
Make a raw PATCH request to ARM.

### `delete(path)`
Make a raw DELETE request to ARM.

**Example:**
```python
response = client.delete("/subscriptions/sub-id/resourceGroups/rg")
```


## Exceptions

All clients may raise the following exceptions:

- `ArmRequestFailedException` - ARM API request failed
