---
title: Providers
---

# Secret Providers

Azol provides secret providers for retrieving secrets from various sources. Providers are used by the token service to retrieve credentials securely.

## KeyVaultProvider

A secret provider that retrieves secrets from Azure Key Vault.

### Constructor

```python
KeyVaultProvider(username, key_vault_name, tenant_id, client_id=None, azol_id=None, 
                 credential=None, cache_refresh_token=True)
```

**Parameters:**
- `username` - Username for authentication (required if credential not provided)
- `key_vault_name` - Name of the Azure Key Vault
- `tenant_id` - Tenant ID
- `client_id` - Optional OAuth client ID
- `azol_id` - Optional azol ID (auto-generated if not provided)
- `credential` - Optional credential object (defaults to User if not provided)
- `cache_refresh_token` - Cache refresh token (default: True)

### Methods

#### `get_id()`
Get the azol ID of the provider.

**Returns:** String containing the azol ID

**Example:**
```python
provider_id = provider.get_id()
```

#### `get_secret(secret_reference)`
Get a secret from the key vault.

**Parameters:**
- `secret_reference` - String containing the secret name

**Returns:** Secret value string or None if not found

**Example:**
```python
from azol.providers import KeyVaultProvider

provider = KeyVaultProvider(
    username="user@domain.com",
    key_vault_name="myvault",
    tenant_id="tenant-id"
)

secret = provider.get_secret("my-secret")
if secret:
    print(f"Secret value: {secret}")
```

### Example Usage

```python
from azol.providers import KeyVaultProvider
from azol.credentials import ServicePrincipal

# Using default User credential
provider = KeyVaultProvider(
    username="user@domain.com",
    key_vault_name="myvault",
    tenant_id="tenant-id"
)

# Using custom credential
cred = ServicePrincipal(
    client_id="client-id",
    client_secret="secret"
)

provider = KeyVaultProvider(
    key_vault_name="myvault",
    tenant_id="tenant-id",
    credential=cred
)

# Get secret
secret_value = provider.get_secret("secret-name")
```

---

## FileSecretProvider

A secret provider that retrieves secrets from a local JSON file.

### Constructor

```python
FileSecretProvider(file=None, directory=None)
```

**Parameters:**
- `file` - Optional file name (defaults to "secrets.json")
- `directory` - Optional directory path (defaults to current directory)

### Methods

#### `get_secret(secret_reference)`
Get a secret from the file.

**Parameters:**
- `secret_reference` - Key name in the JSON file

**Returns:** Secret value string or None if not found

**Example:**
```python
from azol.providers import FileSecretProvider

# File should be JSON: {"secret1": "value1", "secret2": "value2"}
provider = FileSecretProvider(file="secrets.json")
secret = provider.get_secret("secret1")
print(secret)
```

### File Format

The secret file should be a JSON object with key-value pairs:

```json
{
    "secret1": "value1",
    "secret2": "value2",
    "client_secret": "my-secret-value"
}
```

### Example Usage

```python
from azol.providers import FileSecretProvider

# Default file (secrets.json in current directory)
provider = FileSecretProvider()
secret = provider.get_secret("my-secret")

# Custom file path
provider = FileSecretProvider(
    file="my-secrets.json",
    directory="/path/to/secrets"
)
secret = provider.get_secret("my-secret")
```

---

## Using Providers with Token Service

Providers are typically used internally by the token service, but can also be used directly:

```python
from azol.providers import KeyVaultProvider
from azol.credentials import User
from azol.clients import ArmClient

# Create provider
provider = KeyVaultProvider(
    username="user@domain.com",
    key_vault_name="myvault",
    tenant_id="tenant-id"
)

# Provider is used automatically when creating clients with secrets_provider parameter
cred = User(username="user@domain.com")
client = ArmClient(
    tenant="tenant.com",
    cred=cred,
    secrets_provider=provider
)
```

---

## Best Practices

1. **Security**: Never commit secret files to version control
2. **Key Vault**: Use Key Vault for production environments
3. **File Provider**: Use file provider only for development/testing
4. **Credentials**: Prefer using service principals with Key Vault for automation
5. **Caching**: Enable refresh token caching for better performance

