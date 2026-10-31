"""SPOILER: reference agent loop (the solution to Module 01).

Don't open this until Module 01 is green on your own code. Modules 02+ import
`run_agent` from here so that a bug in your Module 01 can't block later modules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from lab.llm import LLM, Message

DEFAULT_SYSTEM = "You are a helpful assistant. Use tools when they help. Be concise."


@dataclass
class AgentResult:
    final_text: str
    messages: list[Message]
    turns: int  # number of model calls
    tool_calls: list[tuple[str, dict]] = field(default_factory=list)
    stopped_reason: str = "end_turn"  # "end_turn" | "max_turns" | other model stop_reason


def execute_tool(name: str, args: dict, tool_impls: dict[str, Callable[..., Any]]) -> tuple[str, bool]:
    """Run one tool. Returns (content, is_error). Never raises: errors go back to the model."""
    fn = tool_impls.get(name)
    if fn is None:
        return f"Unknown tool '{name}'. Available tools: {', '.join(sorted(tool_impls))}", True
    try:
        out = fn(**args)
    except Exception as e:  # the model can often recover if it sees the error
        return f"{type(e).__name__}: {e}", True
    return (out if isinstance(out, str) else json.dumps(out, default=str)), False


def run_agent(
    llm: LLM,
    user_message: str,
    tools: list[dict] | None = None,
    tool_impls: dict[str, Callable[..., Any]] | None = None,
    *,
    system: str = DEFAULT_SYSTEM,
    max_turns: int = 10,
    on_event: Callable[[str, Any], None] | None = None,
) -> AgentResult:
    tools, tool_impls = tools or [], tool_impls or {}
    emit = on_event or (lambda kind, data: None)
    messages: list[Message] = [{"role": "user", "content": user_message}]
    result = AgentResult(final_text="", messages=messages, turns=0)

    while result.turns < max_turns:
        resp = llm.complete(system=system, messages=messages, tools=tools or None)
        result.turns += 1
        messages.append({"role": "assistant", "content": resp.content})
        emit("model", resp)

        if resp.stop_reason != "tool_use":
            result.final_text = resp.text
            result.stopped_reason = resp.stop_reason
            return result

        tool_results = []
        for call in resp.tool_calls:
            result.tool_calls.append((call["name"], call["input"]))
            content, is_error = execute_tool(call["name"], call["input"], tool_impls)
            emit("tool", {"name": call["name"], "input": call["input"], "output": content, "is_error": is_error})
            block = {"type": "tool_result", "tool_use_id": call["id"], "content": content}
            if is_error:
                block["is_error"] = True
            tool_results.append(block)
        messages.append({"role": "user", "content": tool_results})

    result.stopped_reason = "max_turns"
    result.final_text = ""
    return result
