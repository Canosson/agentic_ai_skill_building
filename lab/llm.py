"""The single seam between your code and a model.

Everything in this lab talks to a model through the `LLM` protocol below. That buys
you two things that real agent teams care about:

1. `FakeLLM` lets every test run offline, free and deterministically.
2. Swapping providers or models never touches your agent logic.

Messages and content blocks are plain dicts in the exact shape of the Anthropic
Messages API, so you see the raw protocol rather than a framework's abstraction.
"""

from __future__ import annotations

import copy
import itertools
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol, Union

Block = dict[str, Any]
Message = dict[str, Any]

# Cheap and fast default for learning. Override with LAB_MODEL in .env.
DEFAULT_MODEL = "claude-haiku-5-5"


@dataclass
class Response:
    content: list[Block]
    stop_reason: str  # "end_turn" | "tool_use" | "max_tokens" | ...
    usage: dict[str, int] = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})

    @property
    def text(self) -> str:
        return "".join(b.get("text", "") for b in self.content if b["type"] == "text")

    @property
    def tool_calls(self) -> list[Block]:
        return [b for b in self.content if b["type"] == "tool_use"]


class LLM(Protocol):
    def complete(
        self,
        *,
        system: str,
        messages: list[Message],
        tools: list[dict] | None = None,
        max_tokens: int = 1024,
    ) -> Response: ...


# --------------------------------------------------------------------------- real model


def load_env(path: str | Path | None = None) -> None:
    """Minimal .env loader (KEY=VALUE lines). Existing env vars win."""
    path = Path(path) if path else Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class AnthropicLLM:
    """Thin wrapper over the Anthropic SDK that also tracks calls and token usage."""

    def __init__(self, model: str | None = None):
        load_env()
        import anthropic  # imported lazily so tests never need an API key

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("LAB_MODEL", DEFAULT_MODEL)
        self.calls = 0
        self.usage = {"input_tokens": 0, "output_tokens": 0}

    def complete(self, *, system, messages, tools=None, max_tokens=1024) -> Response:
        kwargs: dict[str, Any] = dict(
            model=self.model, max_tokens=max_tokens, system=system, messages=messages
        )
        if tools:
            kwargs["tools"] = tools
        raw = self.client.messages.create(**kwargs)
        self.calls += 1
        usage = {"input_tokens": raw.usage.input_tokens, "output_tokens": raw.usage.output_tokens}
        for k, v in usage.items():
            self.usage[k] += v
        content = [b.model_dump(exclude_none=True) for b in raw.content]
        return Response(content=content, stop_reason=raw.stop_reason, usage=usage)


# --------------------------------------------------------------------------- fake model

Scripted = Union[Response, Callable[[list[Message]], Response]]
_ids = itertools.count(1)


def text(s: str) -> Response:
    """A scripted final answer."""
    return Response(content=[{"type": "text", "text": s}], stop_reason="end_turn")


def tool_call(name: str, input: dict | None = None, *, id: str | None = None, say: str = "") -> Response:
    """A scripted response that asks for one tool call."""
    return tool_calls([(name, input or {}, id)], say=say)


def tool_calls(calls: list[tuple], *, say: str = "") -> Response:
    """A scripted response that asks for several tool calls at once.

    `calls` is a list of (name, input) or (name, input, id) tuples.
    """
    content: list[Block] = [{"type": "text", "text": say}] if say else []
    for c in calls:
        name, inp = c[0], c[1]
        cid = (c[2] if len(c) > 2 else None) or f"toolu_{next(_ids):04d}"
        content.append({"type": "tool_use", "id": cid, "name": name, "input": inp})
    return Response(content=content, stop_reason="tool_use")


class FakeLLM:
    """A scripted model for tests.

    Give it a list of Responses (or callables that receive the messages and return a
    Response). Every request is recorded in `.requests` so tests can inspect exactly
    what your code sent to the model.
    """

    def __init__(self, script: list[Scripted] | None = None, *, default: Scripted | None = None):
        self.script = list(script or [])
        self.default = default
        self.requests: list[dict] = []

    def complete(self, *, system, messages, tools=None, max_tokens=1024) -> Response:
        self.requests.append(
            {"system": system, "messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)}
        )
        if self.script:
            nxt = self.script.pop(0)
        elif self.default is not None:
            nxt = self.default
        else:
            raise AssertionError(
                "FakeLLM ran out of scripted responses: your code called the model more "
                "times than the test expected."
            )
        return nxt(messages) if callable(nxt) else copy.deepcopy(nxt)

    @property
    def calls(self) -> int:
        return len(self.requests)
