---
title: OAuthHTTPClient
nav_order: 0
parent: Clients
---

# OAuthHTTPClient

Base class for all OAuth HTTP clients. Provides token management and OAuth flow handling.

## Constructor Parameters

- `cred` - Credential object (User, ServicePrincipal, etc.)
- `oauth_resource` - OAuth resource identifier (e.g., `OAuthResourceIDs.Arm`)
- `base_url` - Base URL for API requests
- `tenant` - Tenant ID or domain name
- `oauth_flow` - OAuth flow to use (defaults to credential's default flow)
- `scopes` - List of OAuth scopes to request
- `use_persistent_cache` - Whether to use persistent token cache (default: True)
- `auto_refresh` - Automatically refresh expired tokens (default: True)

## Methods

### `fetch_token()`
Fetch a new access token and cache it.

**Example:**
```python
client.fetch_token()
```

### `get_current_token()`
Get the currently cached access token.

**Returns:** Raw JWT token string or None

**Example:**
```python
token = client.get_current_token()
```

### `get_current_refresh_token()`
Get the current refresh token.

**Returns:** Refresh token string or None

**Example:**
```python
refresh = client.get_current_refresh_token()
```

### `refresh_token()`
Force refresh using the refresh token.

**Example:**
```python
client.refresh_token()
```

### `get_token_claims()`
Get claims from the current token.

**Returns:** Dictionary containing token claims

**Example:**
```python
claims = client.get_token_claims()
print(claims['upn'])
print(claims['tid'])
```

### `switch_tenant(tenant)`
Switch to a different tenant.

**Parameters:**
- `tenant` - Tenant ID or domain name

**Example:**
```python
client.switch_tenant("another-tenant.com")
```

### `switch_scope(scopes, default, profile, offline_access, openid)`
Change the OAuth scope.

**Parameters:**
- `scopes` - List of scope strings
- `default` - Use default scope for resource
- `profile` - Include profile scope
- `offline_access` - Include offline_access scope
- `openid` - Include openid scope

**Example:**
```python
client.switch_scope(
    scopes=["User.Read", "Mail.Read"],
    default=False,
    profile=True,
    offline_access=True,
    openid=True
)
```

### `switch_client(client_id)`
Switch to a different OAuth client (FOCI abuse).

**Parameters:**
- `client_id` - Client ID to switch to

**Example:**
```python
client.switch_client("00000000-0000-0000-0000-000000000000")
```

### `refresh_to_new_resource(oauth_http_client_class)`
Create a new client for a different resource using the same refresh token.

**Parameters:**
- `oauth_http_client_class` - Client class to create (e.g., `ArmClient`, `GraphClient`)

**Returns:** New client instance

**Example:**
```python
# Switch from Graph to ARM
arm_client = graph_client.refresh_to_new_resource(ArmClient)
```

### `from_client(client, *args, **kwargs)` (Class Method)
Create a new client from an existing client.

**Example:**
```python
# Create ARM client from Graph client
arm_client = ArmClient.from_client(graph_client)
```

