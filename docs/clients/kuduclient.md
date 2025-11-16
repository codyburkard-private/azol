---
title: Kudu Client
nav_order: 6
parent: Clients
---

# KuduClient

An HTTP client for interacting with Kudu/SCM APIs.

## Constructor

```python
KuduClient(site_name, cred, tenant, **kwargs)
```

**Parameters:**
- `site_name` - App Service site name
- `cred` - Credential object
- `tenant` - Tenant ID or domain name

## Methods

### `get_scm_env_vars()`
Get SCM environment variables.

**Returns:** Dictionary of environment variables

**Example:**
```python
env_vars = kudu_client.get_scm_env_vars()
```

