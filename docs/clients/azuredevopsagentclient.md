---
title: Azure DevOps Agent Client
nav_order: 7
parent: Clients
---

# AzureDevOpsAgentClient

An HTTP client for interacting with Azure DevOps agents.

## Constructor

```python
AzureDevOpsAgentClient(org_name, pool_id, agent_id, rsa_parameters, message_callback=None)
```

**Parameters:**
- `org_name` - Organization name
- `pool_id` - Agent pool ID
- `agent_id` - Agent ID
- `rsa_parameters` - RSA parameters for authentication
- `message_callback` - Optional callback for processing messages

## Methods

### `connect()`
Connect to the agent service.

**Example:**
```python
agent_client.connect()
```

### `disconnect()`
Disconnect from the agent service.

**Example:**
```python
agent_client.disconnect()
```

