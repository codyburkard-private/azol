"""Assign Directory Readers to the subject principal."""
from __future__ import annotations

from typing import Any

from graph.live.harness.az_auth import AzCliError
from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class DirectoryRoleState(BaseState):
    name = "directory_role"
    requires = ["subject_principal"]
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        principal_id = ctx.state("subject_principal")["spId"]
        data = ctx.ensure_directory_role_assignment(principal_id)
        return ctx.set_state(self.name, data)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        assignment_id = data.get("assignmentId")
        if assignment_id:
            ctx.graph.delete_best_effort(
                f"/roleManagement/directory/roleAssignments/{assignment_id}"
            )

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        row = ctx.graph.graph(
            "GET", f"/roleManagement/directory/roleAssignments/{data['assignmentId']}"
        )
        if not row:
            raise AzCliError("directory role assignment missing")
