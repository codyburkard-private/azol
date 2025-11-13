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

### `get_tenants()`
Get user's tenants.

**Returns:** List of dictionaries containing tenant information

**Raises:** `ArmRequestFailedException`

**Example:**
```python
tenants = arm_client.get_tenants()
for tenant in tenants:
    print(tenant["defaultDomain"])
```

### `get_management_groups(expand=False)`
Get all management groups.

**Parameters:**
- `expand` - Return full API output or abbreviated version

**Returns:** List of management group dictionaries or IDs

**Example:**
```python
mgroups = arm_client.get_management_groups()
```

### `get_subscriptions(expand=False)`
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

### `get_resource_groups(subscriptions=None)`
Get all resource groups.

**Parameters:**
- `subscriptions` - Optional list of subscription IDs to enumerate

**Returns:** List of resource group IDs

**Example:**
```python
rgs = arm_client.get_resource_groups()
```

### `get_providers()`
Get ARM providers and API versions.

**Returns:** Dictionary mapping provider namespaces to API versions

**Example:**
```python
providers = arm_client.get_providers()
```

### `get_resource(resource_id, api_version=None)`
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

### `get_resources(resource_type=None, subscriptions=None, ignore_subscriptions=None)`
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


## Exceptions

All clients may raise the following exceptions:

- `ArmRequestFailedException` - ARM API request failed
