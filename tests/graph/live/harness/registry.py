"""State registry and dependency ordering."""
from __future__ import annotations

from graph.live.harness.states.app_role_graph import GraphAppRoleState
from graph.live.harness.states.directory_role import DirectoryRoleState
from graph.live.harness.states.federated_credential import FederatedCredentialState
from graph.live.harness.states.gated import (
    ConditionalAccessState,
    EntitlementCatalogState,
    PimActiveState,
    PimEligibleState,
)
from graph.live.harness.states.organization import OrganizationState
from graph.live.harness.states.subject_principal import SubjectPrincipalState
from graph.live.harness.states.test_application import TestApplicationState
from graph.live.harness.states.test_group import TestGroupState
from graph.live.harness.states.test_user import TestUserState

_STATE_CLASSES = [
    OrganizationState,
    SubjectPrincipalState,
    TestUserState,
    TestGroupState,
    TestApplicationState,
    DirectoryRoleState,
    GraphAppRoleState,
    FederatedCredentialState,
    PimEligibleState,
    PimActiveState,
    EntitlementCatalogState,
    ConditionalAccessState,
]

STATES = {cls().name: cls() for cls in _STATE_CLASSES}


def get_state(name: str):
    if name not in STATES:
        raise KeyError(f"unknown state: {name}")
    return STATES[name]


def all_state_names() -> list[str]:
    return list(STATES.keys())


def topological_order(names: list[str] | None = None) -> list[str]:
    selected = set(names) if names is not None else set(STATES.keys())
    unknown = selected - set(STATES.keys())
    if unknown:
        raise KeyError(f"unknown states: {sorted(unknown)}")

    # include dependencies transitively
    needed: set[str] = set()

    def add(name: str) -> None:
        if name in needed:
            return
        state = STATES[name]
        for req in state.requires:
            add(req)
        needed.add(name)

    for name in selected:
        add(name)

    ordered: list[str] = []
    remaining = set(needed)
    while remaining:
        ready = [
            n
            for n in remaining
            if all(r in ordered for r in STATES[n].requires)
        ]
        if not ready:
            raise RuntimeError(f"cyclic state dependencies among {sorted(remaining)}")
        # stable: registry declaration order
        ready.sort(key=lambda n: list(STATES.keys()).index(n))
        for name in ready:
            ordered.append(name)
            remaining.remove(name)
    return ordered


def destroy_order(names: list[str] | None = None) -> list[str]:
    return list(reversed(topological_order(names)))
