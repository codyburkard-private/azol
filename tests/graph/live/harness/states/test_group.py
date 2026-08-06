"""Seeded security group with member=user and owner=subject."""
from __future__ import annotations

from typing import Any

from graph.live.harness.config import prefixed_name
from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class TestGroupState(BaseState):
    name = "test_group"
    requires = ["test_user", "subject_principal"]
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        group = ctx.ensure_group(prefixed_name("group"))
        user_id = ctx.state("test_user")["id"]
        subject_sp = ctx.state("subject_principal")["spId"]
        ctx.ensure_group_member(group["id"], user_id)
        ctx.ensure_group_owner(group["id"], subject_sp)
        data = {
            "id": group["id"],
            "displayName": group["displayName"],
            "memberIds": [user_id],
            "ownerIds": [subject_sp],
        }
        return ctx.set_state(self.name, data)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        group_id = data.get("id")
        if not group_id:
            found = ctx.graph.find_by_display_name("groups", prefixed_name("group"))
            group_id = found["id"] if found else None
        if group_id:
            ctx.graph.delete_best_effort(f"/groups/{group_id}")

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        group = ctx.graph.graph("GET", f"/groups/{data['id']}")
        if not group:
            raise AssertionError("test_group missing")
        members = ctx.graph.graph_list(f"/groups/{data['id']}/members")
        member_ids = {m.get("id") for m in members}
        for mid in data.get("memberIds", []):
            if mid not in member_ids:
                raise AssertionError(f"group missing member {mid}")
