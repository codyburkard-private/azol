---
title: Key Vault Client
nav_order: 3
parent: Clients
---

# KeyVaultClient

An HTTP client for interacting with Azure Key Vaults.

## Constructor

```python
KeyVaultClient(key_vault_name, cred, tenant, **kwargs)
```

**Parameters:**
- `key_vault_name` - Name of the key vault
- `cred` - Credential object
- `tenant` - Tenant ID or domain name

## Methods

### `get_secrets()`
Get all secrets in the key vault.

**Returns:** List of secret metadata dictionaries

**Example:**
```python
secrets = kv_client.get_secrets()
for secret in secrets:
    print(secret['name'])
```

### `get_secret(secret_name, secret_version=None)`
Get a secret value.

**Parameters:**
- `secret_name` - Name of the secret
- `secret_version` - Optional version (defaults to latest)

**Returns:** Secret value string

**Example:**
```python
secret_value = kv_client.get_secret("my-secret")
```

### `get_keys()`
Get all keys in the key vault.

**Returns:** List of key metadata dictionaries

**Example:**
```python
keys = kv_client.get_keys()
```

### `get_certificates()`
Get all certificates in the key vault.

**Returns:** List of certificate metadata dictionaries

**Example:**
```python
certs = kv_client.get_certificates()
```

