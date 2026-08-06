# Live Graph harness (azoltest)

Dedicated lab tenant: **azoltest.onmicrosoft.com**.

Provisioning uses **Azure CLI** (`az rest`) only — not azol. Live tests exercise **azol `GraphClient`** with a Graph access token from `az account get-access-token`.

The live suite **always attempts to run**. If Azure CLI is not logged in, Graph token minting fails, or harness fixtures are missing, tests **skip** with a clear reason (not a hard failure). Opt out with `AZOL_LIVE_GRAPH=0`.

## 1. Create the provisioner app

In Entra ID, create an application (no client secret). Admin-consent these **application** permissions:

| Permission | Why |
| --- | --- |
| `RoleManagement.ReadWrite.Directory` | Directory role assignment states |
| `Application.ReadWrite.All` | Apps, SPs, secrets, owners, FICs |
| `AppRoleAssignment.ReadWrite.All` | Graph app role assignment state |
| `Group.ReadWrite.All` | Groups, members, owners |
| `User.ReadWrite.All` | Seed test user |
| `Directory.Read.All` | Enumerations / directoryObjects |
| `Organization.Read.All` | Org smoke tests |

## 2. Federated credential (GitHub Actions)

On the provisioner app, add a federated identity credential:

- Issuer: `https://token.actions.githubusercontent.com`
- Subject: scoped to this repo + environment or branch
- Audience: `api://AzureADTokenExchange`

## 3. Environment

```text
AZOL_LIVE_TENANT=azoltest.onmicrosoft.com
AZOL_LIVE_CLIENT_ID=<provisioner app (client) id>   # for azure/login / ensure
AZOL_LIVE_TENANT_ID=<directory tenant guid>
# AZOL_LIVE_GRAPH=0   # optional: force-skip the entire live suite
```

PIM / Entitlement / CA / mutate tests always attempt when auth works; they skip if Graph returns auth/license errors. Harness `ensure` still respects `AZOL_LIVE_CAP_*` for optional seeding stubs.

Safety:

- Provisioner refuses non-`azoltest.onmicrosoft.com` unless `AZOL_LIVE_ALLOW_ANY_TENANT=1`
- Create/delete only `azol-state-*` / `azol-ephemeral-*`
- Manifest: `tests/graph/live/.state.json` (gitignored; ids only, no secrets)

Do **not** use `AZOL_LIVE_CLIENT_SECRET` for the provisioner.

## 4. Authenticate with Azure CLI

GitHub Actions:

```yaml
permissions:
  id-token: write
  contents: read
steps:
  - uses: azure/login@v2
    with:
      client-id: ${{ vars.AZOL_LIVE_CLIENT_ID }}
      tenant-id: ${{ vars.AZOL_LIVE_TENANT_ID }}
      allow-no-subscriptions: true
```

Local: obtain an Azure CLI session the provisioner accepts (federated / workload identity). No long-lived client secret in `.env`.

## 5. Ensure / status / reset

From repo root with `tests` on `PYTHONPATH` (and azol installed):

```bash
set PYTHONPATH=tests
python -m graph.live.harness.cli ensure
python -m graph.live.harness.cli status
python -m graph.live.harness.cli reset
```

`ensure` creates idempotent fixtures (`azol-state-subject`, `azol-state-user@…`, group, app, Directory Readers on subject, Graph `User.Read.All` on subject, FIC on test app).

## 6. Run live tests

Same Azure CLI session (token for azol comes from `az account get-access-token`):

```bash
set AZOL_LIVE_TENANT=azoltest.onmicrosoft.com
set PYTHONPATH=tests
python -m unittest discover -s tests/graph/live
```

Missing `.state.json` / states → skip (`run harness ensure`). No `az login` → skip (`live Graph not ready`).

## Sample workflow

See [`.github/workflows/liveGraph.yml`](../../../.github/workflows/liveGraph.yml).
