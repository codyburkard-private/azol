"""Subject app + service principal used as assignment target."""
from __future__ import annotations

from typing import Any

from graph.live.harness.config import prefixed_name
from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class SubjectPrincipalState(BaseState):
    name = "subject_principal"
    requires: list[str] = []
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        ids = ctx.ensure_app(prefixed_name("subject"))
        return ctx.set_state(self.name, ids)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        sp_id = data.get("spId")
        app_object_id = data.get("appObjectId")
        if sp_id:
            ctx.graph.delete_best_effort(f"/servicePrincipals/{sp_id}")
        if app_object_id:
            ctx.graph.delete_best_effort(f"/applications/{app_object_id}")
        # also find by name if manifest stale
        app = ctx.graph.find_by_display_name("applications", prefixed_name("subject"))
        if app:
            sp = ctx.graph.find_sp_by_app_id(app["appId"])
            if sp:
                ctx.graph.delete_best_effort(f"/servicePrincipals/{sp['id']}")
            ctx.graph.delete_best_effort(f"/applications/{app['id']}")

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        sp = ctx.graph.graph("GET", f"/servicePrincipals/{data['spId']}")
        if not sp or sp.get("appId") != data.get("appId"):
            raise AssertionError("subject service principal missing or mismatched")
