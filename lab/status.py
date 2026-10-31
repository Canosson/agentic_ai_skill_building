"""Progress board: runs each module's tests against YOUR code and prints where you stand.

    uv run python -m lab.status
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    env = {**os.environ, "LAB_SOLUTION": ""}
    print(f"\n{'module':<26}{'passed':>8}{'total':>8}   status")
    print("-" * 56)
    for mod in sorted((ROOT / "modules").iterdir()):
        if not mod.is_dir() or not list(mod.glob("test_*.py")):
            continue
        out = subprocess.run(
            [sys.executable, "-m", "pytest", str(mod), "-q", "--no-header", "-p", "no:cacheprovider"],
            capture_output=True, text=True, env=env, cwd=ROOT,
        ).stdout
        passed = sum(int(n) for n in re.findall(r"(\d+) passed", out))
        failed = sum(int(n) for n in re.findall(r"(\d+) (?:failed|error)", out))
        total = passed + failed
        status = "DONE" if total and not failed else ("started" if passed else "todo")
        print(f"{mod.name:<26}{passed:>8}{total:>8}   {status}")
    print("\nNext: open the first module that isn't DONE and read its README.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
