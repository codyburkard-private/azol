# Live GraphClient tests

These tests call a real Microsoft Graph tenant. They are **skipped by default**.

## Enable

```bash
set AZOL_LIVE_GRAPH=1
set AZOL_LIVE_TENANT=yourtenant.onmicrosoft.com
set AZOL_LIVE_CLIENT_ID=00000000-0000-0000-0000-000000000000
set AZOL_LIVE_CLIENT_SECRET=...
python -m unittest discover -s tests/graph/live
```

Optional seed ids:

- `AZOL_LIVE_OBJECT_ID` — any directory object id for resolve tests

## Capability flags

| Flag | Enables |
| --- | --- |
| `AZOL_LIVE_CAP_PIM=1` | PIM schedule reads (needs Entra ID P2 / PIM) |
| `AZOL_LIVE_CAP_ENTITLEMENT=1` | Entitlement Management catalogs/packages |
| `AZOL_LIVE_CAP_CA=1` | Conditional Access policies |
| `AZOL_LIVE_CAP_MUTATE=1` | Create/delete ephemeral `azol-live-*` objects |

If a flag is set but Graph returns 403/license errors, the test **fails** (claimed capability is broken).
If a flag is unset, those tests **skip**.

## Suggested app permissions (application)

Core reads:

- `Organization.Read.All`
- `User.Read.All`
- `Group.Read.All`
- `Application.Read.All`
- `Directory.Read.All`
- `RoleManagement.Read.Directory`
- `AppRoleAssignment.ReadWrite.All` (or read equivalents)

Mutate:

- `Application.ReadWrite.All`

PIM / EM / CA as required by the corresponding Graph docs for your license SKU.

## Secrets

Do not commit secrets. Prefer process env vars or a gitignored `.env.live` loaded by your shell.
