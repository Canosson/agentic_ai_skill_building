"""An agent that answers questions about THIS repo, using your ToolRegistry.

    uv run python modules/02-tools-and-context/demo.py "Which module covers evals, and what do I build there?"

Note the sandbox check in _safe(): any tool that touches files or the network is an
attack surface. A prompt-injected document can ask the model to read ~/.ssh/id_rsa.
"""

import sys
from pathlib import Path

from lab.llm import AnthropicLLM
from lab.loop import run_agent
from lab.testing import load

tools_mod = load(__file__, "tools")
ROOT = Path(__file__).resolve().parents[2]
reg = tools_mod.ToolRegistry(max_output_chars=3000)


def _safe(rel: str) -> Path:
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        raise PermissionError(f"{rel!r} is outside the repo")
    return p


@reg.register
def list_files(subdir: str = ".") -> list[str]:
    """List files under a directory of the repo (recursively, max 200).

    Args:
        subdir: Path relative to the repo root, e.g. "modules/04-evals".
    """
    base = _safe(subdir)
    files = [str(p.relative_to(ROOT)) for p in sorted(base.rglob("*"))
             if p.is_file() and ".venv" not in p.parts and "__pycache__" not in p.parts]
    return files[:200]


@reg.register
def read_file(path: str, max_lines: int = 120) -> str:
    """Read a text file from the repo.

    Args:
        path: Path relative to the repo root.
        max_lines: Only return this many lines from the top.
    """
    lines = _safe(path).read_text().splitlines()
    more = f"\n...[{len(lines) - max_lines} more lines]" if len(lines) > max_lines else ""
    return "\n".join(lines[:max_lines]) + more


@reg.register
def grep(pattern: str, subdir: str = ".") -> list[str]:
    """Find lines containing a case-insensitive substring. Returns 'path:line: text' (max 50).

    Args:
        pattern: Plain text to search for (not a regex).
        subdir: Limit the search to this directory.
    """
    hits = []
    for p in sorted(_safe(subdir).rglob("*.md")) + sorted(_safe(subdir).rglob("*.py")):
        if ".venv" in p.parts:
            continue
        for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if pattern.lower() in line.lower():
                hits.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:160]}")
    return hits[:50]


def trace(kind, data):
    if kind == "tool":
        flag = " [ERROR]" if data["is_error"] else ""
        print(f"  {data['name']}({data['input']}) -> {len(data['output'])} chars{flag}")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which module covers evals, and what exactly do I build there?"
    llm = AnthropicLLM()
    print(f"\nQ: {q}\n")
    r = run_agent(llm, q, reg.definitions(), reg.impls(), on_event=trace,
                  system="You answer questions about a code repo. Explore with tools before answering. Cite file paths.")
    print(f"\nA: {r.final_text}\n\nturns={r.turns} tokens={llm.usage}")
