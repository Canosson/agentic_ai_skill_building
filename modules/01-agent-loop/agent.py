"""Module 01: build the agent loop yourself. No framework.

Run the tests:   uv run pytest modules/01-agent-loop -x
Try it for real: uv run python modules/01-agent-loop/demo.py

The protocol (Anthropic Messages API, as plain dicts):

  you  -> model:  messages=[{"role": "user", "content": "What's 17*23?"}], tools=[...]
  model -> you:   Response(stop_reason="tool_use", content=[
                     {"type": "text", "text": "Let me calculate."},
                     {"type": "tool_use", "id": "toolu_1", "name": "calculator",
                      "input": {"expression": "17*23"}}])
  you:            append the assistant turn, run the tool, then append ONE user turn:
                  {"role": "user", "content": [
                     {"type": "tool_result", "tool_use_id": "toolu_1", "content": "391"}]}
  you  -> model:  call again with the longer history ... until stop_reason != "tool_use"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from lab.llm import LLM, Message

DEFAULT_SYSTEM = "You are a helpful assistant. Use tools when they help. Be concise."


@dataclass
class AgentResult:
    final_text: str
    messages: list[Message]
    turns: int  # number of model calls made
    tool_calls: list[tuple[str, dict]] = field(default_factory=list)  # (name, input) in call order
    stopped_reason: str = "end_turn"  # "end_turn" | "max_turns" | other model stop_reason


def execute_tool(name: str, args: dict, tool_impls: dict[str, Callable[..., Any]]) -> tuple[str, bool]:
    """Run one tool and return (content, is_error).

    Rules (each one has a test):
    - Unknown tool name  -> return a helpful message listing the available tools, is_error=True
    - Tool raises        -> return "ExceptionType: message", is_error=True. NEVER let it crash the loop.
    - Tool returns a str -> return it as-is
    - Anything else      -> return json.dumps(value)
    """
    # TODO(01-a): implement
    raise NotImplementedError("execute_tool")


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
    """The agent loop.

    1. Start messages with the user's message.
    2. Call llm.complete(system=..., messages=..., tools=tools or None).
    3. Append the assistant turn: {"role": "assistant", "content": resp.content}
    4. If resp.stop_reason != "tool_use": you're done. Return final_text=resp.text.
    5. Otherwise run EVERY tool_use block (there can be several in one response),
       collect one tool_result block per call (matching tool_use_id, add "is_error": True
       on failure), and append them all in ONE user message. Go to 2.
    6. Never call the model more than max_turns times. If you hit the limit,
       return stopped_reason="max_turns".

    on_event (optional) is for logging: call on_event("model", resp) after each model call
    and on_event("tool", {...}) after each tool run. Tests don't check it; your demo uses it.
    """
    # TODO(01-b): implement
    raise NotImplementedError("run_agent")
