"""State protocol for live harness provisioning."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from graph.live.harness.context import HarnessContext


@runtime_checkable
class State(Protocol):
    name: str
    requires: list[str]
    capabilities: list[str]

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]: ...

    def destroy(self, ctx: HarnessContext) -> None: ...

    def verify(self, ctx: HarnessContext) -> None: ...


class BaseState:
    name: str = ""
    requires: list[str] = []
    capabilities: list[str] = []

    def ensure(self, ctx: HarnessContext) -> dict[str, Any]:
        raise NotImplementedError

    def destroy(self, ctx: HarnessContext) -> None:
        return None

    def verify(self, ctx: HarnessContext) -> None:
        data = ctx.manifest.get("states", {}).get(self.name)
        if not data:
            raise AssertionError(f"state {self.name} missing from manifest")
