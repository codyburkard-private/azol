#!/usr/bin/env python3
"""Fail if public GraphClient methods lack Google-style docstring sections."""
from __future__ import annotations

import inspect
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from azol.clients.graph_client import GraphClient

# Thin aliases may omit Raises.
_RAISES_OPTIONAL = frozenset()


def _public_methods():
    for name, obj in GraphClient.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(obj, staticmethod):
            func = obj.__func__
        elif isinstance(obj, classmethod):
            func = obj.__func__
        elif inspect.isfunction(obj):
            func = obj
        else:
            continue
        yield name, func


def main() -> int:
    errors = []
    methods = list(_public_methods())
    for name, method in methods:
        doc = inspect.getdoc(method) or ""
        if not doc:
            errors.append(f"{name}: missing docstring")
            continue
        sig = inspect.signature(method)
        params = [p for p in sig.parameters if p != "self"]
        if params and "Args:" not in doc:
            errors.append(f"{name}: docstring missing Args section")
        if "Returns:" not in doc:
            errors.append(f"{name}: docstring missing Returns section")
        if name not in _RAISES_OPTIONAL and "Raises:" not in doc:
            errors.append(f"{name}: docstring missing Raises section")

    if errors:
        print("GraphClient docstring check failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK: checked {len(methods)} public GraphClient methods")
    return 0


if __name__ == "__main__":
    sys.exit(main())
