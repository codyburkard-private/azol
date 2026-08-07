"""Guard: provisioning harness must not import azol."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent / "harness"
FORBIDDEN_ROOTS = {
    HARNESS_ROOT / "az_graph.py",
    HARNESS_ROOT / "az_auth.py",
    HARNESS_ROOT / "cli.py",
    HARNESS_ROOT / "context.py",
    HARNESS_ROOT / "config.py",
    HARNESS_ROOT / "manifest.py",
    HARNESS_ROOT / "registry.py",
}


def _imports_azol(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "azol" or alias.name.startswith("azol."):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "azol" or mod.startswith("azol."):
                hits.append(mod)
    return hits


class HarnessNoAzolImportTests(unittest.TestCase):
    def test_states_and_az_graph_do_not_import_azol(self):
        paths = list(FORBIDDEN_ROOTS)
        paths.extend((HARNESS_ROOT / "states").rglob("*.py"))
        failures: list[str] = []
        for path in paths:
            if not path.is_file():
                continue
            hits = _imports_azol(path)
            if hits:
                failures.append(f"{path.relative_to(HARNESS_ROOT.parent)}: {hits}")
        self.assertEqual(failures, [], msg="azol imports forbidden in harness provisioning code")


if __name__ == "__main__":
    unittest.main()
