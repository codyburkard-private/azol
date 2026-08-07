"""Organization smoke state (no objects created)."""
from __future__ import annotations

from typing import Any

from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class OrganizationState(BaseState):
    name = "organization"
    requires: list[str] = []
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        orgs = ctx.graph.graph_list("/organization")
        if not orgs:
            raise RuntimeError("no organization returned from Graph")
        org = orgs[0]
        data = {
            "id": org.get("id"),
            "displayName": org.get("displayName"),
            "verifiedDomains": [
                d.get("name") for d in (org.get("verifiedDomains") or []) if d.get("name")
            ],
        }
        return ctx.set_state(self.name, data)

    def verify(self, ctx: HarnessContext) -> None:
        super().verify(ctx)
        orgs = ctx.graph.graph_list("/organization")
        if not orgs:
            raise AssertionError("organization empty")
        mid = ctx.state(self.name).get("id")
        if mid and orgs[0].get("id") != mid:
            raise AssertionError("organization id mismatch")
