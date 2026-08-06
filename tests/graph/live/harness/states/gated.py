"""Capability-gated state stubs (no seeding in v1)."""
from __future__ import annotations

from typing import Any

from graph.live.harness.context import HarnessContext
from graph.live.harness.states.base import BaseState


class _GatedStub(BaseState):
    requires: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        # v1: no Graph objects to seed; record capability acknowledgement
        return ctx.set_state(self.name, {"seeded": False, "stub": True})

    def destroy(self, ctx: HarnessContext) -> None:
        return None

    def verify(self, ctx: HarnessContext) -> None:
        return None


class PimEligibleState(_GatedStub):
    name = "pim_eligible"
    capabilities = ["pim"]


class PimActiveState(_GatedStub):
    name = "pim_active"
    capabilities = ["pim"]


class EntitlementCatalogState(_GatedStub):
    name = "entitlement_catalog"
    capabilities = ["entitlement"]


class ConditionalAccessState(_GatedStub):
    name = "conditional_access"
    capabilities = ["ca"]
