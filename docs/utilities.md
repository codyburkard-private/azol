---
layout: default
title: Utilities
---

# Utilities

Azol provides various utility functions for working with tokens, certificates, Easy Auth, and more.

## Token Utilities

### `parse_jwt(token)`

Parse a JWT token and return its components.

**Parameters:**
- `token` - Raw JWT token string

**Returns:** Tuple of (header dict, body dict, signature string)

**Example:**
```python
from azol.utils import parse_jwt

header, body, signature = parse_jwt(token)
print(f"Tenant: {body['tid']}")
print(f"User: {body.get('upn')}")
print(f"App: {body['appid']}")
print(f"Expires: {body['exp']}")
```

---

### `is_token_expired(token, padding_time=0)`

Check if a JWT token is expired.

**Parameters:**
- `token` - JWT token string
- `padding_time` - Seconds before expiry to consider token expired (default: 0)

**Returns:** Boolean (True if expired or will expire within padding_time)

**Example:**
```python
from azol.utils import is_token_expired

if is_token_expired(token, padding_time=600):
    print("Token expires in less than 10 minutes")
```

---

### `get_tenant_id(tenant_name)`

Get tenant ID from a domain name by querying the OpenID configuration.

**Parameters:**
- `tenant_name` - Domain name or tenant name

**Returns:** Tenant ID string or None if domain is not registered

**Example:**
```python
from azol.utils import get_tenant_id

tenant_id = get_tenant_id("domain.com")
if tenant_id:
    print(f"Tenant ID: {tenant_id}")
else:
    print("Domain not registered as a tenant")
```

---

## Easy Auth Utilities

### `decrypt_easy_auth_token(encrypted_b64_data, hex_key)`

Decrypt an Easy Auth encrypted token.

**Parameters:**
- `encrypted_b64_data` - Base64-encoded encrypted token
- `hex_key` - Hexadecimal encryption key

**Returns:** Dictionary containing decrypted token data

**Example:**
```python
from azol.utils import decrypt_easy_auth_token

decrypted = decrypt_easy_auth_token(
    encrypted_b64_data="base64-encrypted-token",
    hex_key="hexadecimal-key"
)
print(decrypted)
```

---

### `get_easy_auth_user_tokens(zumo_token, site_url)`

Get user tokens from Easy Auth using X-ZUMO-TOKEN header.

**Parameters:**
- `zumo_token` - JWT token from X-ZUMO-AUTH header
- `site_url` - URL of the App Service or Function App

**Returns:** Dictionary containing user token information

**Raises:** `AzolEasyAuthUnauthorizedZumoTokenException` if token is invalid

**Example:**
```python
from azol.utils import get_easy_auth_user_tokens

tokens = get_easy_auth_user_tokens(
    zumo_token="jwt-token",
    site_url="https://myapp.azurewebsites.net"
)
print(tokens)
```

---

### `create_signed_easy_auth_token(site_url, signing_key_hex, user_object_id, user_principal_name, valid_days=7, idp="aad")`

Create a signed Easy Auth token for a user.

**Parameters:**
- `site_url` - URL of the App Service or Function App (must end with "/")
- `signing_key_hex` - Signing key in hexadecimal format (from environment variables)
- `user_object_id` - Object ID of the target user from Entra ID
- `user_principal_name` - UPN of the Entra user
- `valid_days` - Number of days the token should be valid (default: 7)
- `idp` - Identity provider (currently only "aad" is supported)

**Returns:** Signed JWT token string

**Raises:** `AzolEasyAuthIdpNotSupportedException` if idp is not supported

**Example:**
```python
from azol.utils import create_signed_easy_auth_token

token = create_signed_easy_auth_token(
    site_url="https://myapp.azurewebsites.net/",
    signing_key_hex="hex-signing-key",
    user_object_id="user-oid",
    user_principal_name="user@domain.com",
    valid_days=7
)
print(token)
```

---

### `create_easy_auth_subject(identifier)`

Create an Easy Auth subject identifier from a string.

**Parameters:**
- `identifier` - String identifier

**Returns:** Subject string

**Example:**
```python
from azol.utils import create_easy_auth_subject

subject = create_easy_auth_subject("user@domain.com")
```

---

## Certificate Utilities

### `create_x509_cert(common_name, password=None, country_name=None, state=None, locality=None, org_name=None, private_key_size=2048, subject_alternative_name=None, cert_name="azol_cert", private_key_public_exponent=65537, cert_valid_days=365)`

Create an X.509 certificate.

**Parameters:**
- `common_name` - Common name for the certificate (required)
- `password` - Optional password for the PFX file
- `country_name` - Country name (2-letter code)
- `state` - State or province name
- `locality` - Locality/city name
- `org_name` - Organization name
- `private_key_size` - Private key size in bits (default: 2048)
- `subject_alternative_name` - Subject alternative name (DNS)
- `cert_name` - Certificate name (default: "azol_cert")
- `private_key_public_exponent` - Public exponent (default: 65537)
- `cert_valid_days` - Certificate validity in days (default: 365)

**Returns:** `AzolX509` dataclass with `public_cert` (PEM) and `private_cert` (base64 PFX)

**Example:**
```python
from azol.utils import create_x509_cert

cert = create_x509_cert(
    common_name="My Certificate",
    country_name="US",
    state="California",
    locality="San Francisco",
    org_name="My Company",
    password="certpass",
    cert_valid_days=365
)

print(cert.public_cert)  # PEM format
print(cert.private_cert)  # Base64 PFX
```

---

## String Utilities

### `get_strings_from_bytes(raw_bytes, min_length=3)`

Extract ASCII strings from binary data.

**Parameters:**
- `raw_bytes` - Raw bytes to search
- `min_length` - Minimum string length to extract (default: 3)

**Returns:** List of extracted strings

**Example:**
```python
from azol.utils import get_strings_from_bytes

# Read binary data
with open("memory.dump", "rb") as f:
    data = f.read()

# Extract strings
strings = get_strings_from_bytes(data, min_length=10)
for s in strings:
    if "password" in s.lower():
        print(s)
```

---

### `string_between(whole_string, start_string, end_string, include_start=False)`

Extract a substring between two delimiters.

**Parameters:**
- `whole_string` - String to search
- `start_string` - Start delimiter
- `end_string` - End delimiter
- `include_start` - Include start delimiter in result (default: False)

**Returns:** Extracted substring

**Example:**
```python
from azol.utils import string_between

text = "start:value:end"
result = string_between(text, "start:", ":end")
print(result)  # "value"
```

---

## Windows Utilities

### `decrypt_dpapi(encrypted_data)`

Decrypt DPAPI-encrypted data.

**Parameters:**
- `encrypted_data` - Encrypted bytes

**Returns:** Decrypted bytes

**Example:**
```python
from azol.utils.local.windows import decrypt_dpapi

decrypted = decrypt_dpapi(encrypted_bytes)
```

---

### `get_azure_cli_credential_file_contents()`

Get contents of Azure CLI credential file.

**Returns:** Dictionary containing credential file contents

**Example:**
```python
from azol.utils.local.windows import get_azure_cli_credential_file_contents

creds = get_azure_cli_credential_file_contents()
print(creds)
```

---

## Azure DevOps Utilities

### `is_self_hosted()`

Check if running on a self-hosted Azure DevOps agent.

**Returns:** Boolean

**Example:**
```python
from azol.utils.local.azuredevops import is_self_hosted

if is_self_hosted():
    print("Running on self-hosted agent")
```

---

### `get_agent_home_directory()`

Get the Azure DevOps agent home directory.

**Returns:** Path string

**Example:**
```python
from azol.utils.local.azuredevops import get_agent_home_directory

home = get_agent_home_directory()
print(home)
```

---

### `get_rsa_credentials_file()`

Get path to RSA credentials file.

**Returns:** Path string

**Example:**
```python
from azol.utils.local.azuredevops import get_rsa_credentials_file

creds_file = get_rsa_credentials_file()
```

---

### `load_rsa_credentials(credentials_dict)`

Load RSA credentials from a dictionary.

**Parameters:**
- `credentials_dict` - Dictionary containing RSA credential data

**Returns:** `DevOpsRSAParameters` object

**Example:**
```python
from azol.utils.local.azuredevops import load_rsa_credentials

rsa_params = load_rsa_credentials(creds_dict)
```

---

### `get_agent_id()`

Get the Azure DevOps agent ID.

**Returns:** Agent ID string

**Example:**
```python
from azol.utils.local.azuredevops import get_agent_id

agent_id = get_agent_id()
```

---

## Auth Utilities

### `start_azure_portal_login(*args)`

Start an Azure portal login flow.

**Example:**
```python
from azol.utils import start_azure_portal_login

start_azure_portal_login()
```

---

### `end_azure_portal_login(sp_init_args, code, state, id_token)`

Complete an Azure portal login flow.

**Parameters:**
- `sp_init_args` - Service principal initialization arguments
- `code` - Authorization code
- `state` - State parameter
- `id_token` - ID token

**Example:**
```python
from azol.utils import end_azure_portal_login

end_azure_portal_login(sp_init_args, code, state, id_token)
```

---

## Exceptions

### `AzolEasyAuthIdpNotSupportedException`

Raised when an unsupported Easy Auth identity provider is used.

### `AzolEasyAuthUnauthorizedZumoTokenException`

Raised when an invalid X-ZUMO-AUTH token is provided.

---

## Data Classes

### `AzolX509`

Dataclass containing X.509 certificate data.

**Attributes:**
- `public_cert` - Certificate in PEM format (string)
- `private_cert` - Certificate in base64-encoded PFX format (string)

**Example:**
```python
from azol.utils import create_x509_cert, AzolX509

cert: AzolX509 = create_x509_cert(common_name="Test")
print(cert.public_cert)
print(cert.private_cert)
```

