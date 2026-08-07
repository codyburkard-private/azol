"""Operator CLI: ensure / status / reset (Azure CLI provisioning only)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from graph.live.harness.az_auth import assert_logged_in_for_tenant
from graph.live.harness.config import (
    STATE_PREFIX,
    assert_tenant_allowed,
    load_config,
)
from graph.live.harness.context import HarnessContext
from graph.live.harness.manifest import empty_manifest, load_manifest, save_manifest
from graph.live.harness.registry import STATES, destroy_order, topological_order


def _build_ctx() -> HarnessContext:
    config = load_config()
    assert_tenant_allowed(config)
    assert_logged_in_for_tenant(config)
    manifest = load_manifest() or empty_manifest(config)
    manifest["tenant"] = config.tenant
    return HarnessContext(config=config, manifest=manifest)


def _caps_ok(ctx: HarnessContext, state) -> bool:
    if not state.capabilities:
        return True
    return all(ctx.config.has_cap(cap) for cap in state.capabilities)


def cmd_ensure(names: list[str] | None) -> int:
    ctx = _build_ctx()
    if names:
        order = topological_order(names)
    else:
        order = topological_order(
            [name for name, state in STATES.items() if _caps_ok(ctx, state)]
        )
    for name in order:
        state = STATES[name]
        if not _caps_ok(ctx, state):
            print(f"skip {name} (capabilities {state.capabilities} not enabled)")
            continue
        print(f"ensure {name}...")
        data = state.ensure(ctx)
        ctx.set_state(name, data)
        save_manifest(ctx.manifest)
        print(f"  ok: {json.dumps(data, sort_keys=True)}")
    print("manifest written")
    return 0


def cmd_status() -> int:
    ctx = _build_ctx()
    print(json.dumps(ctx.manifest, indent=2, sort_keys=True))
    failures = 0
    for name in topological_order():
        state = STATES[name]
        if name not in ctx.manifest.get("states", {}):
            if state.capabilities and not _caps_ok(ctx, state):
                print(f"verify {name}: skipped (cap off)")
                continue
            print(f"verify {name}: MISSING")
            failures += 1
            continue
        try:
            state.verify(ctx)
            print(f"verify {name}: ok")
        except Exception as exc:  # noqa: BLE001 - CLI status surface
            print(f"verify {name}: FAIL ({exc})")
            failures += 1
    return 1 if failures else 0


def _orphan_sweep(ctx: HarnessContext) -> None:
    """Best-effort delete azol-state-* users/groups/apps not necessarily in manifest."""
    scans: list[tuple[str, str, str]] = [
        ("users", f"startswith(displayName,'{STATE_PREFIX}')", "/users/{id}"),
        ("groups", f"startswith(displayName,'{STATE_PREFIX}')", "/groups/{id}"),
        (
            "applications",
            f"startswith(displayName,'{STATE_PREFIX}')",
            "/applications/{id}",
        ),
    ]
    for collection, filter_expr, delete_path in scans:
        try:
            rows = ctx.graph.graph_list(f"/{collection}", filter_expr=filter_expr)
        except Exception as exc:  # noqa: BLE001
            print(f"orphan scan {collection} failed: {exc}")
            continue
        for row in rows:
            display = row.get("displayName") or ""
            if not display.startswith(STATE_PREFIX):
                continue
            object_id = row.get("id")
            if not object_id:
                continue
            if collection == "applications":
                app_id = row.get("appId")
                if app_id:
                    sp = ctx.graph.find_sp_by_app_id(app_id)
                    if sp:
                        print(f"orphan delete servicePrincipal {sp['id']} ({display})")
                        ctx.graph.delete_best_effort(f"/servicePrincipals/{sp['id']}")
            path = delete_path.format(id=object_id)
            print(f"orphan delete {path} ({display})")
            ctx.graph.delete_best_effort(path)


def cmd_reset(names: list[str] | None) -> int:
    ctx = _build_ctx()
    order = destroy_order(names or None)
    for name in order:
        state = STATES[name]
        print(f"destroy {name}...")
        try:
            state.destroy(ctx)
        except Exception as exc:  # noqa: BLE001
            print(f"  warn: {exc}")
        ctx.manifest.get("states", {}).pop(name, None)
        save_manifest(ctx.manifest)
    if names is None:
        print("orphan sweep...")
        _orphan_sweep(ctx)
    ctx.manifest["states"] = {} if names is None else ctx.manifest.get("states", {})
    save_manifest(ctx.manifest)
    # Deletes are eventually consistent; give Graph time before a following ensure.
    print("waiting for directory deletes to settle...")
    time.sleep(15)
    print("reset complete")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="azoltest live Graph harness")
    sub = parser.add_subparsers(dest="command", required=True)

    ensure_p = sub.add_parser("ensure", help="idempotently create named states")
    ensure_p.add_argument("states", nargs="*", help="state names (default: all)")

    sub.add_parser("status", help="print manifest and verify states")

    reset_p = sub.add_parser("reset", help="destroy states and orphan-prefixed objects")
    reset_p.add_argument("states", nargs="*", help="state names (default: all)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "ensure":
        return cmd_ensure(args.states or None)
    if args.command == "status":
        return cmd_status()
    if args.command == "reset":
        return cmd_reset(args.states or None)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
