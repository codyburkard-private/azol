"""Seeded cloud-only test user."""
from __future__ import annotations

from typing import Any

from graph.live.harness.config import prefixed_name
from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class TestUserState(BaseState):
    name = "test_user"
    requires: list[str] = []
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        data = ctx.ensure_user("user")
        return ctx.set_state(self.name, data)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        user_id = data.get("id")
        upn = data.get("upn") or f"{prefixed_name('user')}@{ctx.config.upn_domain}"
        if not user_id:
            found = ctx.graph.find_user_by_upn(upn)
            user_id = found["id"] if found else None
        if user_id:
            ctx.graph.delete_best_effort(f"/users/{user_id}")

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        user = ctx.graph.graph("GET", f"/users/{data['id']}")
        if not user or user.get("userPrincipalName", "").lower() != data["upn"].lower():
            raise AssertionError("test_user missing or UPN mismatch")
