"""Module 02a: tools as an interface for the model.

What MCP SDKs and frameworks do "magically" with @tool decorators, you build here:
turn a normal Python function into a tool definition, then call it safely.

    uv run pytest modules/02-tools-and-context/test_tools.py -x
"""

from __future__ import annotations

import inspect
import json
import re
import types
import typing
from typing import Any, Callable, Literal, get_args, get_origin


def type_to_schema(tp: Any) -> dict:
    """Python type hint -> JSON Schema fragment.

    str -> {"type": "string"}    int -> "integer"    float -> "number"
    bool -> "boolean"            dict / dict[str, X] -> {"type": "object"}
    list[X] -> {"type": "array", "items": <schema of X>}
    Literal["a", "b"] -> {"type": "string", "enum": ["a", "b"]}
    X | None  or  Optional[X] -> schema of X
    anything else -> raise TypeError

    Hints: typing.get_origin / get_args; X | None has origin types.UnionType,
    Optional[X] has origin typing.Union.
    """
    # TODO(02-a)
    raise NotImplementedError("type_to_schema")


def parse_docstring(doc: str | None) -> tuple[str, dict[str, str]]:
    """Google-style docstring -> (summary, {param: description}).

        '''Search the notes.

        Longer explanation here.

        Args:
            query: Words to look for.
            limit: Max results. Keep it small,
                the model reads every one.
        '''
    -> ("Search the notes.\\n\\nLonger explanation here.",
        {"query": "Words to look for.", "limit": "Max results. Keep it small, the model reads every one."})

    Everything before "Args:" is the summary. A deeper-indented line continues the previous
    param. A line indented less than the params (e.g. "Returns:") ends the Args section.
    """
    # TODO(02-b)
    raise NotImplementedError("parse_docstring")


def function_to_tool(fn: Callable) -> dict:
    """Build an Anthropic tool definition from a function:

    {"name": fn.__name__,
     "description": <docstring summary>,
     "input_schema": {"type": "object", "properties": {...}, "required": [...]}}

    - Each parameter becomes a property (use typing.get_type_hints for the types).
    - Add "description" to a property if the docstring documents it.
    - A parameter is required iff it has no default.
    """
    # TODO(02-c)
    raise NotImplementedError("function_to_tool")


class ToolCallError(Exception):
    pass


class ToolRegistry:
    """Holds tools and calls them defensively. The model makes mistakes; the registry
    turns every mistake into a clear message the model can act on."""

    def __init__(self, max_output_chars: int = 4000):
        self.max_output_chars = max_output_chars
        self._fns: dict[str, Callable] = {}
        self._defs: dict[str, dict] = {}

    def register(self, fn: Callable) -> Callable:
        """Usable as a decorator. Stores fn and its function_to_tool definition."""
        self._fns[fn.__name__] = fn
        self._defs[fn.__name__] = function_to_tool(fn)
        return fn

    def definitions(self) -> list[dict]:
        return list(self._defs.values())

    def call(self, name: str, args: dict) -> tuple[str, bool]:
        """Returns (content, is_error). Never raises. In this order:

        1. Unknown tool         -> error listing available tools
        2. Missing required arg -> error naming the missing arg(s)
        3. Unexpected arg       -> error naming it AND listing the valid ones
        4. Tool raises          -> "ExceptionType: message"
        5. Non-string output    -> json.dumps
        6. Output longer than max_output_chars -> keep the first max_output_chars and append
           "\\n...[truncated N chars]" where N is how many were cut
        """
        # TODO(02-d)
        raise NotImplementedError("ToolRegistry.call")

    def impls(self) -> dict[str, Callable[..., str]]:
        """Adapter for run_agent (given, not an exercise): every call goes through call(),
        and errors are raised so run_agent flags them is_error."""
        def make(n):
            def impl(**kw):
                out, err = self.call(n, kw)
                if err:
                    raise ToolCallError(out)
                return out
            return impl
        return {n: make(n) for n in self._fns}
