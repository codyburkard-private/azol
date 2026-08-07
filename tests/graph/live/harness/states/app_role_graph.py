"""Assign a Microsoft Graph application permission to the subject SP."""
from __future__ import annotations

from typing import Any

from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class GraphAppRoleState(BaseState):
    name = "graph_app_role"
    requires = ["subject_principal"]
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        principal_sp_id = ctx.state("subject_principal")["spId"]
        data = ctx.ensure_graph_app_role(principal_sp_id)
        return ctx.set_state(self.name, data)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        principal_sp_id = data.get("principalSpId") or (
            ctx.manifest.get("states", {}).get("subject_principal") or {}
        ).get("spId")
        assignment_id = data.get("assignmentId")
        if principal_sp_id and assignment_id:
            ctx.graph.delete_best_effort(
                f"/servicePrincipals/{principal_sp_id}/appRoleAssignments/{assignment_id}"
            )

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        rows = ctx.graph.graph_list(
            f"/servicePrincipals/{data['principalSpId']}/appRoleAssignments"
        )
        if not any(r.get("id") == data.get("assignmentId") for r in rows):
            raise AssertionError("graph app role assignment missing")
