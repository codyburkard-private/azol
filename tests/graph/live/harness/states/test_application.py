"""Seeded application with SP, password credential, and subject owner."""
from __future__ import annotations

from typing import Any

from graph.live.harness.config import prefixed_name
from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class TestApplicationState(BaseState):
    name = "test_application"
    requires = ["subject_principal"]
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        ids = ctx.ensure_app(prefixed_name("app"))
        subject_sp = ctx.state("subject_principal")["spId"]
        ctx.ensure_app_owner(ids["appObjectId"], subject_sp)
        ctx.ensure_password_credential(ids["appObjectId"])
        data = {
            **ids,
            "ownerIds": [subject_sp],
            "hasPasswordCredential": True,
        }
        return ctx.set_state(self.name, data)

    def destroy(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name) or {}
        sp_id = data.get("spId")
        app_object_id = data.get("appObjectId")
        if not app_object_id:
            found = ctx.graph.find_by_display_name("applications", prefixed_name("app"))
            if found:
                app_object_id = found["id"]
                sp = ctx.graph.find_sp_by_app_id(found["appId"])
                sp_id = sp["id"] if sp else sp_id
        if sp_id:
            ctx.graph.delete_best_effort(f"/servicePrincipals/{sp_id}")
        if app_object_id:
            ctx.graph.delete_best_effort(f"/applications/{app_object_id}")

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        data = ctx.state(self.name)
        app = ctx.graph.graph("GET", f"/applications/{data['appObjectId']}")
        if not app:
            raise AssertionError("test_application missing")
