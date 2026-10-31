"""Module 02b: context management.

The loop re-sends the whole history on every turn. Long tasks get slow, expensive and
eventually fail on the context limit. Models also get worse at using information buried
in a huge context. These are two simple, widely used fixes.

    uv run pytest modules/02-tools-and-context/test_context.py -x
"""

from __future__ import annotations

import copy
import json
from typing import Callable

from lab.llm import Message


def estimate_tokens(messages: list[Message]) -> int:
    """Rough token count (given): ~4 characters per token. Good enough for budgeting;
    for exact counts the Anthropic API has a token-counting endpoint."""
    return len(json.dumps(messages, default=str)) // 4


def trim_history(
    messages: list[Message], budget: int, count: Callable[[list[Message]], int] = estimate_tokens
) -> list[Message]:
    """Drop the oldest turns until count(messages) <= budget.

    Rules:
    - ALWAYS keep messages[0]: it's the original task.
    - Never leave a tool_result whose tool_use was dropped (the API rejects that) and keep
      roles alternating user/assistant. (Hint: what happens if you always drop two
      messages at a time, starting at index 1?)
    - Never drop below 3 messages, even if still over budget.
    - Don't mutate the input list.
    """
    # TODO(02-e)
    raise NotImplementedError("trim_history")


def compact_tool_results(messages: list[Message], keep_last: int = 2, max_chars: int = 200) -> list[Message]:
    """Shrink OLD tool results; keep the most recent `keep_last` tool_result blocks intact.

    For each older tool_result whose string content is longer than max_chars, replace it with
    content[:max_chars] + f"...[compacted, {len(content)} chars originally]".
    The structure (ids, roles, number of blocks) must not change. Don't mutate the input.

    Why this works: once the model has acted on a tool result, it rarely needs the raw output again.
    """
    # TODO(02-f)
    raise NotImplementedError("compact_tool_results")
