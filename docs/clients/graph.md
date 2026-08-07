# GraphClient usage

`GraphClient` talks to Microsoft Graph (beta by default) using the same OAuth credential model as other azol clients.

## Construct a client

```python
from azol.credentials import ServicePrincipal
from azol.clients import GraphClient

cred = ServicePrincipal(client_id="...", client_secret="...")
client = GraphClient(tenant="contoso.onmicrosoft.com", cred=cred)
```

User credentials work the same way with `azol.credentials.User`.

## Domain helpers vs fluent calls

Prefer named helpers when they exist (`get_all_groups`, `get_service_principal`, …).
For anything else, use the fluent builder:

```python
users = (
    client.call("/users")
    .select("id", "displayName")
    .filter("startswith(displayName,'A')")
    .get()
    .values()
)
```

`values()` follows `@odata.nextLink` until paging is exhausted. `json()` returns a single response body (or `None` for empty/204 responses).

## Annotations

Several helpers attach human-readable names under `azolAnnotations`:

```python
perms = client.get_api_permissions(sp_object_id)
print(perms[0]["azolAnnotations"]["permissionName"])
```

Unknown role or permission ids map to `"unknown"` instead of raising.

## Mutations

Creates typically expect HTTP 201. Deletes and `$ref` ownership/membership writes accept 200 or 204 and often return `None` when the body is empty.

## Live tests

Optional live-tenant tests live under `tests/graph/live/`. See that directory's README for environment variables and capability flags (PIM, Entitlement Management, Conditional Access, mutate).
