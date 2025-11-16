---
title: Azure DevOps Client
nav_order: 4
parent: Clients
---

# AzureDevOpsClient

An HTTP client for interacting with the Azure DevOps API.

## Constructor

```python
AzureDevOpsClient(cred, tenant, **kwargs)
```

## Methods

### `get_organizations()`
Get all organizations accessible to the credential.

**Returns:** List of organization dictionaries

**Example:**
```python
orgs = devops_client.get_organizations()
```

### `get_projects(org_name)`
Get all projects in an organization.

**Parameters:**
- `org_name` - Organization name

**Returns:** List of project dictionaries

**Example:**
```python
projects = devops_client.get_projects("myorg")
```

### `get_service_connections(org_name, project_name)`
Get all service connections in a project.

**Parameters:**
- `org_name` - Organization name
- `project_name` - Project name

**Returns:** List of service connection dictionaries

**Example:**
```python
connections = devops_client.get_service_connections("myorg", "myproject")
```

### `get_agent_pools(org_name)`
Get all agent pools in an organization.

**Parameters:**
- `org_name` - Organization name

**Returns:** List of agent pool dictionaries

**Example:**
```python
pools = devops_client.get_agent_pools("myorg")
```

### `create_agent(org_name, pool_id, name)`
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

