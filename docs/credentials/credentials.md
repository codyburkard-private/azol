---
title: Credentials
nav_order: 1
---

# Credentials

Azol provides several credential types for authentication. All credentials inherit from the base `Credential` class.

## Credential

Base class for all credential types.

### Methods

#### `get_id()`
Get the azol ID of the credential object.

**Returns:** String containing the azol ID

**Example:**
```python
cred_id = cred.get_id()
```

---

## EntraIdCredential

Base class for Entra ID credentials (inherits from `Credential`).

### Methods

#### `get_default_oauth_flow()`
Get the default OAuth flow for this credential type.

**Returns:** OAuth flow string

---

## User

A credential object for user authentication. Supports refresh tokens, device code flow, and authorization code flow.

### Constructor

```python
User(username=None, refresh_token=None, ests=None, ests_persistent=None, 
     client_id=FOCIClients.MicrosoftAzurePowershell, **kwargs)
```

**Parameters:**
- `username` - User's email address
- `refresh_token` - Optional refresh token
- `ests` - Optional ESTS cookie
- `ests_persistent` - Optional persistent ESTS cookie
- `client_id` - OAuth client ID (defaults to Azure PowerShell client)

**Supported OAuth Flows:**
- `refresh_token`
- `device_code` (default)
- `authorization_code`

### Methods

#### `get_username()`
Get the username of the user object.

**Returns:** Username string or None

**Example:**
```python
username = user.get_username()
```

#### `set_username(username)`
Set the username of the user object.

**Parameters:**
- `username` - Username to set

**Example:**
```python
user.set_username("user@domain.com")
```

#### `username_is_known()`
Check if the username is set.

**Returns:** Boolean

**Example:**
```python
if user.username_is_known():
    print(f"Username: {user.get_username()}")
```

#### `get_refresh_token()`
Get the current refresh token.

**Returns:** Refresh token string or None

**Example:**
```python
refresh = user.get_refresh_token()
```

#### `has_refresh_token()`
Check if a refresh token is available.

**Returns:** Boolean

**Example:**
```python
if user.has_refresh_token():
    print("Refresh token available")
```

#### `get_ests()`
Get the user's ESTS cookies.

**Returns:** `ESTS` object containing ests and ests_persistent cookies

**Example:**
```python
ests = user.get_ests()
print(ests.ests)
```

#### `has_ests()`
Check if ESTS cookies are available.

**Returns:** Boolean

**Example:**
```python
if user.has_ests():
    print("ESTS cookies available")
```

#### `get_client_id()`
Get the OAuth client ID.

**Returns:** Client ID string

**Example:**
```python
client_id = user.get_client_id()
```

### Example Usage

```python
from azol.credentials import User
from azol.clients import ArmClient

# Create user credential
cred = User(username="user@domain.com")

# Use with client
arm_client = ArmClient(tenant="tenant.com", cred=cred)

# Or with refresh token
cred = User(username="user@domain.com", refresh_token="refresh-token")
arm_client = ArmClient(tenant="tenant.com", cred=cred)
```

---

## ServicePrincipal

A credential for service principal authentication. Supports client secret or X.509 certificate authentication.

### Constructor

```python
ServicePrincipal(client_id, client_secret=None, pfx_path=None, b64_cert=None, 
                 cert_password=None, **kwargs)
```

**Parameters:**
- `client_id` - Service principal client ID (required)
- `client_secret` - Client secret (optional, if using secret auth)
- `pfx_path` - Path to PFX certificate file (optional, if using cert auth)
- `b64_cert` - Base64-encoded PFX certificate (optional, if using cert auth)
- `cert_password` - Certificate password (required if using cert auth)

**Supported OAuth Flows:**
- `client_credentials`

**Note:** You must provide either `client_secret`, `pfx_path`, or `b64_cert`.

### Methods

#### `get_credential_type()`
Get the credential type (secret or x509).

**Returns:** String ("secret" or "x509")

**Example:**
```python
cred_type = sp.get_credential_type()
print(f"Auth type: {cred_type}")
```

#### `get_client_secret()`
Get the client secret (if using secret auth).

**Returns:** Client secret string or None

**Example:**
```python
secret = sp.get_client_secret()
```

#### `get_certificate()`
Get the certificate object (if using cert auth).

**Returns:** Cryptography PKCS12KeyAndCertificates object or None

**Example:**
```python
cert = sp.get_certificate()
```

### Example Usage

```python
from azol.credentials import ServicePrincipal
from azol.clients import GraphClient

# Using client secret
cred = ServicePrincipal(
    client_id="00000000-0000-0000-0000-000000000000",
    client_secret="your-secret"
)

# Using certificate
cred = ServicePrincipal(
    client_id="00000000-0000-0000-0000-000000000000",
    pfx_path="/path/to/cert.pfx",
    cert_password="cert-password"
)

# Use with client
graph_client = GraphClient(tenant="tenant.com", cred=cred)
```

---

## AccessToken

A credential object for using a raw access token.

### Constructor

```python
AccessToken(token, **kwargs)
```

**Parameters:**
- `token` - Raw JWT access token string

**Supported OAuth Flows:**
- `raw_token`

### Example Usage

```python
from azol.credentials import AccessToken
from azol.clients import ArmClient

# Create credential from token
cred = AccessToken(token="eyJ0eXAi...")

# Use with client
arm_client = ArmClient(tenant="tenant.com", cred=cred)
```

---

## ApplicationObject

A credential for application object authentication.

### Constructor

```python
ApplicationObject(**kwargs)
```

**Example Usage**

```python
from azol.credentials import ApplicationObject
from azol.clients import GraphClient

cred = ApplicationObject()
graph_client = GraphClient(tenant="tenant.com", cred=cred)
```

---

## DevOpsAgentCredential

A credential for Azure DevOps agent authentication.

### Constructor

```python
DevOpsAgentCredential(agent_key, **kwargs)
```

**Parameters:**
- `agent_key` - DevOps agent authentication key

**Example Usage**

```python
from azol.credentials import DevOpsAgentCredential
from azol.clients import AzureDevOpsAgentClient

cred = DevOpsAgentCredential(agent_key="agent-key")
```

---

## ADOWorkloadFederationCredential

A credential for Azure DevOps pipeline workload federation.

### Constructor

```python
ADOWorkloadFederationCredential(**kwargs)
```

**Example Usage**

```python
from azol.credentials import ADOWorkloadFederationCredential
from azol.clients import GraphClient

cred = ADOWorkloadFederationCredential()
graph_client = GraphClient(tenant="tenant.com", cred=cred)
```

---

## Choosing a Credential Type

- **User**: Use when you have user credentials (username/password, refresh token, or ESTS cookies)
- **ServicePrincipal**: Use when you have a service principal with client secret or certificate
- **AccessToken**: Use when you already have a valid access token
- **ApplicationObject**: Use for application-only authentication
- **DevOpsAgentCredential**: Use for Azure DevOps agent authentication
- **ADOWorkloadFederationCredential**: Use for Azure DevOps pipeline workload federation

