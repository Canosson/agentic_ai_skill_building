"""Test helper: load YOUR file or the reference solution.

    uv run pytest modules/01-agent-loop                 # tests your code
    LAB_SOLUTION=1 uv run pytest modules/01-agent-loop  # tests the reference solution
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


def using_solution() -> bool:
    return os.environ.get("LAB_SOLUTION", "") not in ("", "0", "false")


def load(test_file: str, name: str) -> ModuleType:
    here = Path(test_file).resolve().parent
    base = here / "solution" if using_solution() else here
    path = base / f"{name}.py"
    mod_name = f"_lab_{here.name.replace('-', '_')}_{name}_{'sol' if using_solution() else 'you'}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module
