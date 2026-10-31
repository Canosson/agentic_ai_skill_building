"""Reference solution: connect MCP tools to your agent loop."""

from __future__ import annotations

from typing import Any


def mcp_tools_to_anthropic(tools: list[Any]) -> list[dict]:
    return [
        {"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
        for t in tools
    ]


def result_to_text(result: Any) -> tuple[str, bool]:
    parts = [b.text for b in result.content if getattr(b, "type", None) == "text"]
    other = [b.type for b in result.content if getattr(b, "type", None) != "text"]
    if other:
        parts.append(f"[{len(other)} non-text block(s) omitted: {', '.join(other)}]")
    return "\n".join(parts), bool(result.is_error)


def needs_approval(tool: Any) -> bool:
    a = getattr(tool, "annotations", None)
    if a is None:
        return True
    if a.read_only_hint:
        return False
    return a.destructive_hint is not False
