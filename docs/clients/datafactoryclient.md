---
title: Data Factory Client
nav_order: 5
parent: Clients
---

# DataFactoryClient

An HTTP client for the internal Data Factory API.

## Constructor

```python
DataFactoryClient(authentication_key, ir_node_id=None, spoofed_ir_name="Default")
```

**Parameters:**
- `authentication_key` - Data Factory IR authentication key
- `ir_node_id` - Optional existing IR node ID
- `spoofed_ir_name` - Name for spoofed IR node

## Methods

### `get_managed_identity_token(oauth_resource)`
Get a managed identity token.

**Parameters:**
- `oauth_resource` - OAuth resource (e.g., "https://management.azure.com/")

**Returns:** Access token string

**Example:**
```python
token = df_client.get_managed_identity_token("https://management.azure.com/")
```

### `spoof_shir(poll_interval=3, job_callback=None)`
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

