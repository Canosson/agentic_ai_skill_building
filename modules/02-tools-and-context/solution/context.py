"""Reference solution: keeping the context window under control."""

from __future__ import annotations

import copy
import json
from typing import Callable

from lab.llm import Message


def estimate_tokens(messages: list[Message]) -> int:
    return len(json.dumps(messages, default=str)) // 4


def trim_history(
    messages: list[Message], budget: int, count: Callable[[list[Message]], int] = estimate_tokens
) -> list[Message]:
    msgs = list(messages)
    # Drop (assistant, user) pairs right after the original task. Dropping in pairs keeps
    # roles alternating AND never orphans a tool_result from its tool_use.
    while count(msgs) > budget and len(msgs) > 3:
        del msgs[1:3]
    return msgs


def compact_tool_results(messages: list[Message], keep_last: int = 2, max_chars: int = 200) -> list[Message]:
    msgs = copy.deepcopy(messages)
    positions = [
        (i, j)
        for i, m in enumerate(msgs)
        if m["role"] == "user" and isinstance(m["content"], list)
        for j, b in enumerate(m["content"])
        if b.get("type") == "tool_result"
    ]
    old = positions[:-keep_last] if keep_last else positions
    for i, j in old:
        block = msgs[i]["content"][j]
        content = block.get("content", "")
        if isinstance(content, str) and len(content) > max_chars:
            block["content"] = content[:max_chars] + f"...[compacted, {len(content)} chars originally]"
    return msgs
