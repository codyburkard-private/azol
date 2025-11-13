---
title: Quick Start
---

# Quick Start Guide

This guide will help you get started with Azol quickly. We'll cover the most common use cases and patterns.

## Basic Authentication

### User Authentication

Authenticate as a user using device code flow (default):

```python
from azol.credentials import User
from azol.clients import ArmClient

cred = User(username="user@domain.com")
arm_client = ArmClient(tenant="tenant.com", cred=cred)

# Get all subscriptions
subscriptions = arm_client.get_subscriptions()
for sub_id in subscriptions:
    print(sub_id)
```

### Service Principal Authentication

Authenticate using a service principal:

```python
from azol.credentials import ServicePrincipal
from azol.clients import GraphClient

cred = ServicePrincipal(
    client_id="00000000-0000-0000-0000-000000000000",
    client_secret="your-secret"
)

graph_client = GraphClient(tenant="tenant.com", cred=cred)

# Get all groups with owners
groups = graph_client.get_all_groups_and_owners()
for group in groups:
    print(group)
```

### Interactive Authentication

Use authorization code flow for interactive browser login:

```python
from azol import User, ArmClient

cred = User("user@domain.com")
arm_client = ArmClient(
    cred=cred,
    oauth_flow="authorization_code"
)

# Get all tenants the user belongs to
tenants = arm_client.get_tenants()
for tenant in tenants:
    print(tenant["defaultDomain"])
```

## Common Operations

### Enumerate Azure Resources

```python
from azol import User, ArmClient

cred = User(username="user@domain.com")
client = ArmClient(tenant="tenant.com", cred=cred)

# Get all subscriptions
subscriptions = client.get_subscriptions()
print(f"Found {len(subscriptions)} subscriptions")

# Get all resources
resources = client.get_resources()
print(f"Found {len(resources)} total resources")

# Filter by resource type
vms = client.get_resources(resource_type="Microsoft.Compute/virtualMachines")
for vm in vms:
    print(f"VM: {vm.name} in {vm.location}")
```

### Enumerate Entra ID Users and Groups

```python
from azol import ServicePrincipal, GraphClient

cred = ServicePrincipal(
    client_id="00000000-0000-0000-0000-000000000000",
    client_secret="your-secret"
)
client = GraphClient(tenant="tenant.com", cred=cred)

# Get all users
users = client.get_all_users(select=['userPrincipalName', 'mail', 'displayName'])
print(f"Found {len(users)} users")

# Get all groups with owners
groups = client.get_all_groups(owners=True)
for group in groups:
    print(f"\nGroup: {group['displayName']}")
    if 'owners' in group:
        for owner in group['owners']:
            print(f"  Owner: {owner['displayName']}")
```

### Access Key Vault Secrets

```python
from azol import User, KeyVaultClient

cred = User(username="user@domain.com")

kv_client = KeyVaultClient(
    key_vault_name="myvault",
    cred=cred,
    tenant="tenant.com"
)

# List all secrets
secrets = kv_client.get_secrets()
for secret in secrets:
    secret_name = secret['name'].split('/')[-1]
    try:
        secret_value = kv_client.get_secret(secret_name)
        print(f"{secret_name}: {secret_value}")
    except:
        print(f"{secret_name}: [Access Denied]")
```

## Switching Between Resources

You can reuse refresh tokens to access different Azure resources:

```python
from azol import User, ArmClient, GraphClient

# Start with ARM client
cred = User(username="user@domain.com")
arm_client = ArmClient(tenant="tenant.com", cred=cred)

# Do ARM operations
subscriptions = arm_client.get_subscriptions()

# Switch to Graph using same refresh token
graph_client = arm_client.refresh_to_new_resource(GraphClient)
users = graph_client.get_all_users()
```

## Token Management

### Get Current Token

```python
token = client.get_current_token()
print(f"Token: {token[:50]}...")
```

### Get Token Claims

```python
claims = client.get_token_claims()
print(f"User: {claims.get('upn')}")
print(f"Tenant: {claims.get('tid')}")
print(f"App: {claims.get('appid')}")
```

### Force Token Refresh

```python
client.refresh_token()
```

## Error Handling

All clients raise specific exceptions for different error conditions:

```python
from azol import User, ArmClient
from azol.clients.arm_client import ArmRequestFailedException

cred = User(username="user@domain.com")
client = ArmClient(tenant="tenant.com", cred=cred)

try:
    resources = client.get_resources()
except ArmRequestFailedException as e:
    print(f"ARM request failed: {e}")
```

## Next Steps

- Explore the [Clients documentation](/clients) for detailed API reference
- Check out the [Credentials documentation](/credentials) for authentication options
- Review the [Utilities documentation](/utilities) for helper functions

