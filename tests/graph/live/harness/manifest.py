"""Load and save the live harness state manifest."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from graph.live.harness.config import MANIFEST_PATH, LiveConfig


def empty_manifest(config: LiveConfig) -> dict[str, Any]:
    return {
        "tenant": config.tenant,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "states": {},
    }


def load_manifest(path: Path | None = None) -> dict[str, Any] | None:
    target = path or MANIFEST_PATH
    if not target.is_file():
        return None
    with target.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid manifest at {target}")
    data.setdefault("states", {})
    return data


def save_manifest(manifest: dict[str, Any], path: Path | None = None) -> Path:
    target = path or MANIFEST_PATH
    manifest = dict(manifest)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return target


def require_state(manifest: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not manifest or name not in manifest.get("states", {}):
        raise KeyError(name)
    data = manifest["states"][name]
    if not isinstance(data, dict):
        raise KeyError(name)
    return data
