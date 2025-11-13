---
title: Models
---

# Data Models

Azol provides several data models for representing Azure resources and authentication data.

## GenericResource

A dataclass representing an Azure resource from ARM API.

### Attributes

- `id` (str) - Resource ID
- `name` (str) - Resource name
- `properties` (dict) - Resource properties
- `type` (str) - Resource type (e.g., "Microsoft.Compute/virtualMachines")
- `changedTime` (str, optional) - Last changed time
- `createdTime` (str, optional) - Creation time
- `identity` (dict, optional) - Managed identity information
- `kind` (str, optional) - Resource kind
- `location` (str, optional) - Azure region
- `tags` (dict, optional) - Resource tags
- `azolAnnotations` (dict, optional) - Custom annotations added by Azol

### Example Usage

```python
from azol import ArmClient, User

cred = User(username="user@domain.com")
client = ArmClient(tenant="tenant.com", cred=cred)

# Get resources
resources = client.get_resources()

for resource in resources:
    print(f"Name: {resource.name}")
    print(f"Type: {resource.type}")
    print(f"Location: {resource.location}")
    print(f"ID: {resource.id}")
    print(f"Properties: {resource.properties}")
    print(f"Tags: {resource.tags}")
    print("---")

# Get specific resource
resource = client.get_resource("/subscriptions/.../resourceGroups/.../providers/...")
print(f"Resource: {resource.name}")
```

### Accessing Properties

```python
# Access standard attributes
resource_id = resource.id
resource_name = resource.name
resource_type = resource.type

# Access properties dictionary
if 'osProfile' in resource.properties:
    os_profile = resource.properties['osProfile']
    print(f"Computer name: {os_profile.get('computerName')}")

# Access tags
if resource.tags:
    for key, value in resource.tags.items():
        print(f"Tag: {key} = {value}")

# Access managed identity
if resource.identity:
    print(f"Identity type: {resource.identity.get('type')}")
    if 'principalId' in resource.identity:
        print(f"Principal ID: {resource.identity['principalId']}")
```

---

## DevOpsRSAParameters

A dataclass containing RSA parameters for Azure DevOps agent authentication.

### Attributes

- `p` (bytes) - Prime p
- `q` (bytes) - Prime q
- `d` (bytes) - Private exponent
- `modulus` (bytes) - Modulus
- `dp` (bytes) - DP value
- `dq` (bytes) - DQ value
- `exponent` (bytes) - Public exponent
- `inverseq` (bytes) - Inverse Q

### Example Usage

```python
from azol.models import DevOpsRSAParameters
from azol.clients import AzureDevOpsClient

# RSA parameters are typically obtained from create_agent
cred = User(username="user@domain.com")
devops_client = AzureDevOpsClient(cred=cred, tenant="tenant.com")

agent_data, rsa_params = devops_client.create_agent(
    org_name="myorg",
    pool_id="pool-id",
    name="myagent"
)

# Access RSA parameters
print(f"Modulus: {rsa_params.modulus}")
print(f"Exponent: {rsa_params.exponent}")
print(f"Private key components: p, q, d")
```

### Converting to Base64

```python
import base64

# Convert to base64 for storage/transmission
modulus_b64 = base64.b64encode(rsa_params.modulus).decode()
exponent_b64 = base64.b64encode(rsa_params.exponent).decode()
```

---

## ESTS

A dataclass for ESTS (Entra ID Security Token Service) cookies.

### Attributes

- `ests` (str) - ESTS cookie value
- `ests_persistent` (str) - Persistent ESTS cookie value

### Example Usage

```python
from azol.models import ESTS
from azol.credentials import User

# Create ESTS object
ests = ESTS(
    ests="ests-cookie-value",
    ests_persistent="persistent-cookie-value"
)

# Use with User credential
user = User(
    username="user@domain.com",
    ests=ests.ests,
    ests_persistent=ests.ests_persistent
)

# Or get from existing user
user = User(username="user@domain.com")
if user.has_ests():
    ests_obj = user.get_ests()
    print(f"ESTS: {ests_obj.ests}")
    print(f"ESTS Persistent: {ests_obj.ests_persistent}")
```

### Storing ESTS Cookies

```python
import json
from azol.models import ESTS

# Save ESTS cookies
ests = ESTS(ests="...", ests_persistent="...")
with open("ests.json", "w") as f:
    json.dump({
        "ests": ests.ests,
        "ests_persistent": ests.ests_persistent
    }, f)

# Load ESTS cookies
with open("ests.json", "r") as f:
    data = json.load(f)
    ests = ESTS(
        ests=data["ests"],
        ests_persistent=data["ests_persistent"]
    )
```

---

## SPLoginModel

A model for service principal login initialization.

### Attributes

- Internal model used by authentication flows

### Example Usage

```python
# Typically used internally by token service
# Not directly instantiated by users
```

---

## Working with Models

### Converting to Dictionary

Most models can be converted to dictionaries:

```python
# GenericResource can be accessed as dict-like
resource_dict = {
    "id": resource.id,
    "name": resource.name,
    "type": resource.type,
    "properties": resource.properties
}
```

### Serialization

For JSON serialization:

```python
import json

# GenericResource
resource_dict = {
    "id": resource.id,
    "name": resource.name,
    "type": resource.type,
    "properties": resource.properties,
    "location": resource.location,
    "tags": resource.tags
}
json_str = json.dumps(resource_dict, indent=2)

# ESTS
ests_dict = {
    "ests": ests.ests,
    "ests_persistent": ests.ests_persistent
}
json_str = json.dumps(ests_dict)
```

### Filtering Resources

```python
# Filter resources by type
vms = [r for r in resources if r.type == "Microsoft.Compute/virtualMachines"]

# Filter by location
us_resources = [r for r in resources if r.location and "us" in r.location.lower()]

# Filter by tags
tagged_resources = [r for r in resources if r.tags]

# Filter by managed identity
mi_resources = [r for r in resources if r.identity]
```

---

## Model Annotations

Azol may add custom annotations to models for additional metadata:

```python
# GenericResource may have azolAnnotations
if resource.azolAnnotations:
    print(f"Annotations: {resource.azolAnnotations}")

# Example: Graph API resources may have roleName annotations
if 'roleName' in resource.azolAnnotations:
    print(f"Role: {resource.azolAnnotations['roleName']}")
```

---

## Best Practices

1. **Type Checking**: Use type hints when working with models
2. **Null Checks**: Always check for None/optional attributes
3. **Serialization**: Convert to dict for JSON serialization
4. **Filtering**: Use list comprehensions for efficient filtering
5. **Annotations**: Check azolAnnotations for additional metadata

