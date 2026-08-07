"""One federated identity credential on the seeded test application."""
from __future__ import annotations

from typing import Any

from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState

FIC_NAME = "azol-state-fic"


class FederatedCredentialState(BaseState):
    name = "federated_credential"
    requires = ["test_application"]
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        app_object_id = ctx.state("test_application")["appObjectId"]
        ctx.graph.wait_for_get(
            f"/applications/{app_object_id}",
            label=f"application {app_object_id}",
        )

        def _ensure() -> dict[str, Any]:
            existing = ctx.graph.graph_list(
                f"/applications/{app_object_id}/federatedIdentityCredentials"
            )
            fic = next((f for f in existing if f.get("name") == FIC_NAME), None)
            if fic is None:
                tenant_id = ctx.config.tenant_id
                if not tenant_id:
                    # discover from organization
                    orgs = ctx.graph.graph_list("/organization")
                    tenant_id = (orgs[0] or {}).get("id") if orgs else None
                issuer = (
                    f"https://login.microsoftonline.com/{tenant_id}/v2.0"
                    if tenant_id
                    else "https://login.microsoftonline.com/common/v2.0"
                )
                fic = ctx.graph.graph(
                    "POST",
                    f"/applications/{app_object_id}/federatedIdentityCredentials",
                    {
                        "name": FIC_NAME,
                        "issuer": issuer,
                        "subject": "azol-state-fic-subject",
                        "audiences": ["api://AzureADTokenExchange"],
                        "description": "azol live harness seed FIC",
                    },
                )
            if not isinstance(fic, dict) or "id" not in fic:
                raise RuntimeError("failed to ensure federated credential")
            return fic

        fic = ctx.graph.with_consistency_retry(
            _ensure,
            label=f"federated credential on {app_object_id}",
        )
        data = {
            "id": fic["id"],
            "name": fic.get("name", FIC_NAME),
            "appObjectId": app_object_id,
        }
        return ctx.set_state(self.name, data)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        app_object_id = data.get("appObjectId") or (
            ctx.manifest.get("states", {}).get("test_application") or {}
        ).get("appObjectId")
        fic_id = data.get("id")
        if app_object_id and fic_id:
            ctx.graph.delete_best_effort(
                f"/applications/{app_object_id}/federatedIdentityCredentials/{fic_id}"
            )

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        rows = ctx.graph.graph_list(
            f"/applications/{data['appObjectId']}/federatedIdentityCredentials"
        )
        if not any(r.get("id") == data.get("id") for r in rows):
            raise AssertionError("federated credential missing")
