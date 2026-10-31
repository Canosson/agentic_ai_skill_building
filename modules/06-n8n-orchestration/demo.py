"""Build the ticket router, lint it, list its paths with their model cost, and export the JSON.

    uv run python modules/06-n8n-orchestration/demo.py

Then import `out/ticket-router.json` into n8n (README: "See it on a canvas").
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.testing import load

w = load(__file__, "workflows")

OUT = Path(__file__).resolve().parent / "out" / "ticket-router.json"


def main():
    wf = w.ticket_router_workflow()
    problems = w.validate(wf)
    print("LINT:", "clean" if not problems else "")
    for p in problems:
        print("  -", p)

    print("\nPATHS (model calls per route):")
    for path in w.paths(wf):
        print(f"  {w.llm_calls(wf, path)} LLM  {' → '.join(path)}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(wf, indent=2))
    print(f"\nWrote {OUT.relative_to(Path.cwd()) if OUT.is_relative_to(Path.cwd()) else OUT}")


if __name__ == "__main__":
    main()
