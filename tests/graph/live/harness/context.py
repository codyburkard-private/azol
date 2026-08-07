"""Harness context shared by state modules (Azure CLI Graph only)."""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from typing import Any

from graph.live.harness import az_graph
from graph.live.harness.az_auth import AzCliError
from graph.live.harness.config import (
    DIRECTORY_READERS_DISPLAY_NAME,
    GRAPH_APP_ROLE_VALUE,
    MICROSOFT_GRAPH_APP_ID,
    LiveConfig,
    assert_safe_display_name,
    prefixed_name,
)


def _password() -> str:
    alphabet = string.ascii_letters + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(24))
    return f"Aa1!{body}"


@dataclass
class HarnessContext:
    config: LiveConfig
    manifest: dict[str, Any]
    graph: Any = field(default=az_graph)

    def state(self, name: str) -> dict[str, Any]:
        return self.manifest.setdefault("states", {}).setdefault(name, {})

    def set_state(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        self.manifest.setdefault("states", {})[name] = data
        return data

    def ensure_app(self, display_name: str) -> dict[str, str]:
        return self.graph.ensure_application(display_name)

    def ensure_user(self, local_part: str = "user") -> dict[str, str]:
        display_name = prefixed_name(local_part)
        upn = f"{display_name}@{self.config.upn_domain}"
        assert_safe_display_name(display_name)
        existing = self.graph.find_live_user_by_upn(upn)
        if existing:
            return {"id": existing["id"], "upn": existing.get("userPrincipalName", upn)}

        created_ids: list[str] = []
        for round_idx in range(1, 4):
            existing = self.graph.find_live_user_by_upn(upn)
            if existing:
                return {
                    "id": existing["id"],
                    "upn": existing.get("userPrincipalName", upn),
                }
            created = self.graph.graph(
                "POST",
                "/users",
                {
                    "accountEnabled": True,
                    "displayName": display_name,
                    "mailNickname": display_name.replace(".", ""),
                    "userPrincipalName": upn,
                    "passwordProfile": {
                        "forceChangePasswordNextSignIn": False,
                        "password": _password(),
                    },
                },
            )
            if not isinstance(created, dict) or "id" not in created:
                raise AzCliError(f"failed to create user {upn} (round {round_idx})")
            created_ids.append(created["id"])
            try:
                live = self.graph.wait_until_readable(
                    f"/users/{created['id']}",
                    label=f"user {upn}",
                    fallback=lambda: self.graph.find_live_user_by_upn(upn),
                )
                return {
                    "id": live["id"],
                    "upn": live.get("userPrincipalName", upn),
                }
            except AzCliError:
                continue
        raise AzCliError(f"failed to create readable user {upn}; tried ids={created_ids}")

    def ensure_group(self, display_name: str) -> dict[str, str]:
        assert_safe_display_name(display_name)
        existing = self.graph.find_live_by_display_name("groups", display_name)
        if existing:
            return {"id": existing["id"], "displayName": display_name}

        created_ids: list[str] = []
        for round_idx in range(1, 4):
            existing = self.graph.find_live_by_display_name("groups", display_name)
            if existing:
                return {"id": existing["id"], "displayName": display_name}
            created = self.graph.graph(
                "POST",
                "/groups",
                {
                    "displayName": display_name,
                    "mailEnabled": False,
                    "mailNickname": display_name.replace("-", "")[:64],
                    "securityEnabled": True,
                },
            )
            if not isinstance(created, dict) or "id" not in created:
                raise AzCliError(
                    f"failed to create group {display_name} (round {round_idx})"
                )
            created_ids.append(created["id"])
            try:
                live = self.graph.wait_until_readable(
                    f"/groups/{created['id']}",
                    label=f"group {display_name}",
                    fallback=lambda: self.graph.find_live_by_display_name(
                        "groups", display_name
                    ),
                )
                return {"id": live["id"], "displayName": display_name}
            except AzCliError:
                continue
        raise AzCliError(
            f"failed to create readable group {display_name}; tried ids={created_ids}"
        )

    def ensure_group_member(self, group_id: str, member_id: str) -> None:
        self.graph.wait_for_get(f"/groups/{group_id}", label=f"group {group_id}")
        self.graph.wait_for_get(
            f"/directoryObjects/{member_id}",
            label=f"member {member_id}",
        )

        def _ensure() -> None:
            members = self.graph.graph_list(f"/groups/{group_id}/members")
            if any(m.get("id") == member_id for m in members):
                return
            self.graph.graph(
                "POST",
                f"/groups/{group_id}/members/$ref",
                {
                    "@odata.id": (
                        f"https://graph.microsoft.com/v1.0/directoryObjects/{member_id}"
                    )
                },
            )

        self.graph.with_consistency_retry(
            _ensure,
            label=f"ensure group member {member_id} on {group_id}",
        )

    def ensure_group_owner(self, group_id: str, owner_id: str) -> None:
        self.graph.wait_for_get(f"/groups/{group_id}", label=f"group {group_id}")
        self.graph.wait_for_get(
            f"/directoryObjects/{owner_id}",
            label=f"owner {owner_id}",
        )

        def _ensure() -> None:
            owners = self.graph.graph_list(f"/groups/{group_id}/owners")
            if any(o.get("id") == owner_id for o in owners):
                return
            self.graph.graph(
                "POST",
                f"/groups/{group_id}/owners/$ref",
                {
                    "@odata.id": (
                        f"https://graph.microsoft.com/v1.0/directoryObjects/{owner_id}"
                    )
                },
            )

        self.graph.with_consistency_retry(
            _ensure,
            label=f"ensure group owner {owner_id} on {group_id}",
        )

    def ensure_app_owner(self, app_object_id: str, owner_id: str) -> None:
        self.graph.wait_for_get(
            f"/applications/{app_object_id}",
            label=f"application {app_object_id}",
        )
        self.graph.wait_for_get(
            f"/directoryObjects/{owner_id}",
            label=f"owner {owner_id}",
        )

        def _ensure() -> None:
            owners = self.graph.graph_list(f"/applications/{app_object_id}/owners")
            if any(o.get("id") == owner_id for o in owners):
                return
            self.graph.graph(
                "POST",
                f"/applications/{app_object_id}/owners/$ref",
                {
                    "@odata.id": (
                        f"https://graph.microsoft.com/v1.0/directoryObjects/{owner_id}"
                    )
                },
            )

        self.graph.with_consistency_retry(
            _ensure,
            label=f"ensure app owner {owner_id} on {app_object_id}",
        )

    def ensure_directory_role_assignment(
        self,
        principal_id: str,
        role_display_name: str = DIRECTORY_READERS_DISPLAY_NAME,
    ) -> dict[str, str]:
        self.graph.wait_for_get(
            f"/directoryObjects/{principal_id}",
            label=f"principal {principal_id}",
        )
        roles = self.graph.graph_list(
            "/roleManagement/directory/roleDefinitions",
            filter_expr=f"displayName eq '{role_display_name.replace(chr(39), chr(39)+chr(39))}'",
        )
        role = next((r for r in roles if r.get("displayName") == role_display_name), None)
        if not role:
            raise AzCliError(f"role definition not found: {role_display_name}")
        role_definition_id = role["id"]

        def _ensure() -> dict[str, str]:
            assignments = self.graph.graph_list(
                "/roleManagement/directory/roleAssignments",
                filter_expr=f"principalId eq '{principal_id}'",
            )
            for assignment in assignments:
                if assignment.get("roleDefinitionId") == role_definition_id:
                    return {
                        "assignmentId": assignment["id"],
                        "roleDefinitionId": role_definition_id,
                        "principalId": principal_id,
                        "roleDisplayName": role_display_name,
                    }
            created = self.graph.graph(
                "POST",
                "/roleManagement/directory/roleAssignments",
                {
                    "principalId": principal_id,
                    "roleDefinitionId": role_definition_id,
                    "directoryScopeId": "/",
                },
            )
            if not isinstance(created, dict) or "id" not in created:
                raise AzCliError("failed to create directory role assignment")
            return {
                "assignmentId": created["id"],
                "roleDefinitionId": role_definition_id,
                "principalId": principal_id,
                "roleDisplayName": role_display_name,
            }

        return self.graph.with_consistency_retry(
            _ensure,
            label=f"directory role {role_display_name} for {principal_id}",
        )

    def ensure_graph_app_role(
        self,
        principal_sp_id: str,
        role_value: str = GRAPH_APP_ROLE_VALUE,
    ) -> dict[str, str]:
        self.graph.wait_for_get(
            f"/servicePrincipals/{principal_sp_id}",
            label=f"principal SP {principal_sp_id}",
        )
        graph_sp = self.graph.find_sp_by_app_id(MICROSOFT_GRAPH_APP_ID)
        if not graph_sp:
            raise AzCliError("Microsoft Graph service principal not found in tenant")
        resource_sp_id = graph_sp["id"]
        app_roles = graph_sp.get("appRoles") or self.graph.graph(
            "GET", f"/servicePrincipals/{resource_sp_id}?$select=appRoles"
        )
        if isinstance(app_roles, dict):
            app_roles = app_roles.get("appRoles") or []
        role = next(
            (
                r
                for r in app_roles
                if r.get("value") == role_value and r.get("isEnabled", True)
            ),
            None,
        )
        if not role:
            # refetch with expand if needed
            full = self.graph.graph("GET", f"/servicePrincipals/{resource_sp_id}")
            app_roles = (full or {}).get("appRoles") or []
            role = next(
                (r for r in app_roles if r.get("value") == role_value and r.get("isEnabled", True)),
                None,
            )
        if not role:
            raise AzCliError(f"Graph app role {role_value} not found")
        app_role_id = role["id"]

        def _ensure() -> dict[str, str]:
            existing = self.graph.graph_list(
                f"/servicePrincipals/{principal_sp_id}/appRoleAssignments"
            )
            for row in existing:
                if row.get("appRoleId") == app_role_id and row.get("resourceId") == resource_sp_id:
                    return {
                        "assignmentId": row["id"],
                        "appRoleId": app_role_id,
                        "resourceSpId": resource_sp_id,
                        "principalSpId": principal_sp_id,
                        "roleValue": role_value,
                    }
            created = self.graph.graph(
                "POST",
                f"/servicePrincipals/{principal_sp_id}/appRoleAssignments",
                {
                    "principalId": principal_sp_id,
                    "resourceId": resource_sp_id,
                    "appRoleId": app_role_id,
                },
            )
            if not isinstance(created, dict) or "id" not in created:
                raise AzCliError(f"failed to assign Graph app role {role_value}")
            return {
                "assignmentId": created["id"],
                "appRoleId": app_role_id,
                "resourceSpId": resource_sp_id,
                "principalSpId": principal_sp_id,
                "roleValue": role_value,
            }

        return self.graph.with_consistency_retry(
            _ensure,
            label=f"Graph app role {role_value} for {principal_sp_id}",
        )

    def ensure_password_credential(self, app_object_id: str) -> None:
        """Ensure the app has at least one password credential (secret value not stored)."""

        def _ensure() -> None:
            app = self.graph.graph("GET", f"/applications/{app_object_id}")
            if not isinstance(app, dict):
                raise AzCliError(f"application {app_object_id} not found")
            if app.get("passwordCredentials"):
                return
            self.graph.graph(
                "POST",
                f"/applications/{app_object_id}/addPassword",
                {"passwordCredential": {"displayName": "azol-state-seed"}},
            )

        self.graph.with_consistency_retry(
            _ensure,
            label=f"password credential for application {app_object_id}",
        )
