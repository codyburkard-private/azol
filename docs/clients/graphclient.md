---
title: Graph Client
nav_order: 2
parent: Clients
---

# GraphClient

An HTTP client for interacting with the Microsoft Graph API.

## Constructor

```python
GraphClient(tenant, cred, base_url=GRAPHBETAURL, **kwargs)
```

## Methods

### `get_all_users(select=None)`
Get all users in the directory.

**Parameters:**
- `select` - Optional list of properties to select

**Returns:** List of user dictionaries

**Example:**
```python
users = graph_client.get_all_users(select=['userPrincipalName', 'mail', 'displayName'])
```

### `get_all_groups(owners=False)`
Get all groups.

**Parameters:**
- `owners` - Include group owners in response

**Returns:** List of group dictionaries

**Example:**
```python
groups = graph_client.get_all_groups(owners=True)
```

### `get_all_groups_and_owners()`
Get all groups with their owners.

**Returns:** List of group dictionaries with owner information

**Example:**
```python
groups = graph_client.get_all_groups_and_owners()
```

### `get_directory_role_definitions()`
Get all directory role definitions.

**Returns:** List of role definition dictionaries

**Example:**
```python
roles = graph_client.get_directory_role_definitions()
```

### `get_directory_role_assignments()`
Get all directory role assignments.

**Returns:** List of role assignment dictionaries

**Example:**
```python
assignments = graph_client.get_directory_role_assignments()
```

### `add_directory_role_assignment(role_definition_id, principal_id)`
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

### `create_new_local_service_principal(name)`
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

