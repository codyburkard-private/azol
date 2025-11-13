---
title: Caches
nav_order: 6
---

# Token Caches

Azol provides token caching mechanisms to avoid unnecessary authentication requests. All cache classes inherit from `AzolCache`.

## AzolCache

Base class for token caching. Provides methods for storing and retrieving tokens.

### Methods

#### `try_get_token(tenant_id, client_id, default_scope, scopes, oauth_resource, username=None)`

Attempt to get a cached token that matches the specified parameters.

**Parameters:**
- `tenant_id` - Tenant ID that issued the token
- `client_id` - OAuth client ID
- `default_scope` - Boolean indicating if default scope should be used
- `scopes` - List of OAuth scopes
- `oauth_resource` - OAuth resource identifier
- `username` - Optional username (for delegated tokens)

**Returns:** Dictionary containing token data (scope, username, access_token, refresh_token) or None

**Example:**
```python
from azol.caches import AzolCache

cache = AzolCache()
token_data = cache.try_get_token(
    tenant_id="tenant-id",
    client_id="client-id",
    default_scope=True,
    scopes=[],
    oauth_resource="https://management.azure.com",
    username="user@domain.com"
)

if token_data:
    print(f"Access token: {token_data['access_token']}")
    print(f"Refresh token: {token_data.get('refresh_token')}")
```

#### `cache_or_update(access_token, tenant_id, client_id, default_scope, scopes, oauth_resource, refresh_token=None, username=None, ests_cookie=None, ests_persistent_cookie=None)`

Save or update a token in the cache.

**Parameters:**
- `access_token` - OAuth2 access token to cache
- `tenant_id` - Tenant ID that issued the token
- `client_id` - OAuth client ID
- `default_scope` - Boolean indicating if default scope was used
- `scopes` - List of OAuth scopes
- `oauth_resource` - OAuth resource identifier
- `refresh_token` - Optional refresh token
- `username` - Optional username (for delegated tokens)
- `ests_cookie` - Optional ESTS cookie
- `ests_persistent_cookie` - Optional persistent ESTS cookie

**Returns:** None

**Example:**
```python
cache.cache_or_update(
    access_token="eyJ0eXAi...",
    tenant_id="tenant-id",
    client_id="client-id",
    default_scope=True,
    scopes=[],
    oauth_resource="https://management.azure.com",
    refresh_token="0.AX...",
    username="user@domain.com"
)
```

---

## InMemoryTokenCache

In-memory token cache. Tokens are stored in memory and lost when the process exits.

### Constructor

```python
InMemoryTokenCache()
```

### Example Usage

```python
from azol.caches import InMemoryTokenCache
from azol.credentials import User
from azol.clients import ArmClient

# Create in-memory cache
cache = InMemoryTokenCache()

# Cache is used automatically by clients
cred = User(username="user@domain.com")
client = ArmClient(
    tenant="tenant.com",
    cred=cred,
    use_persistent_cache=False  # Use in-memory cache
)
```

**Note:** In-memory cache is the default when `use_persistent_cache=False` is set on clients.

---

## LocalTokenCache

Token cache that persists tokens to the local filesystem. Tokens are saved to `~/.azol/tokencache/default`.

### Constructor

```python
LocalTokenCache()
```

### Example Usage

```python
from azol.caches import LocalTokenCache
from azol.credentials import User
from azol.clients import ArmClient

# Local cache is used automatically when use_persistent_cache=True (default)
cred = User(username="user@domain.com")
client = ArmClient(
    tenant="tenant.com",
    cred=cred,
    use_persistent_cache=True  # Default behavior
)
```

### Cache Location

Tokens are stored in:
- **Windows**: `%USERPROFILE%\.azol\tokencache\default`
- **Linux/Mac**: `~/.azol/tokencache/default`

### Security Considerations

- Tokens are stored in plain text JSON files
- Ensure proper file permissions on the cache directory
- Consider encrypting the cache directory for sensitive environments
- Clear cache when switching between different security contexts

---

## Cache Structure

The cache stores tokens in a nested dictionary structure:

```python
{
    "tenant-id": {
        "oauth-resource": {
            "client-id": [
                {
                    "type": "delegated" | "application",
                    "scopes": ["scope1", "scope2"],
                    "username": "user@domain.com",  # Only for delegated
                    "access_token": "eyJ0eXAi...",
                    "refresh_token": "0.AX...",  # Only for delegated
                    "ests_cookie": "...",  # Optional
                    "ests_persistent_cookie": "..."  # Optional
                }
            ]
        }
    }
}
```

---

## Using Custom Caches

You can implement custom cache classes by inheriting from `AzolCache`:

```python
from azol.caches import AzolCache

class CustomCache(AzolCache):
    def try_get_token(self, tenant_id, client_id, default_scope, scopes, 
                     oauth_resource, username=None):
        # Custom retrieval logic
        return super().try_get_token(...)
    
    def cache_or_update(self, access_token, tenant_id, client_id, default_scope, 
                       scopes, oauth_resource, refresh_token=None, username=None, 
                       ests_cookie=None, ests_persistent_cookie=None):
        # Custom storage logic
        super().cache_or_update(...)
```

---

## Cache Management

### Clearing Cache

To clear the local cache, delete the cache file:

```python
import os
from pathlib import Path
from azol.constants import AZOL_HOME

cache_file = Path(AZOL_HOME) / "tokencache" / "default"
if cache_file.exists():
    cache_file.unlink()
    print("Cache cleared")
```

### Inspecting Cache

You can read the cache file directly:

```python
import json
from pathlib import Path
from azol.constants import AZOL_HOME

cache_file = Path(AZOL_HOME) / "tokencache" / "default"
if cache_file.exists():
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    print(json.dumps(cache_data, indent=2))
```

---

## Best Practices

1. **Use Persistent Cache**: Enable persistent caching for better user experience
2. **Clear on Logout**: Clear cache when users log out
3. **Secure Storage**: Ensure cache directory has proper permissions
4. **Monitor Size**: Large caches may impact performance
5. **Token Expiry**: Cache automatically handles expired tokens, but manual cleanup may be needed

