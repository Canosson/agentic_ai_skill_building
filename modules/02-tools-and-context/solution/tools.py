"""Reference solution: tool schemas from Python functions + a registry."""

from __future__ import annotations

import inspect
import json
import re
import types
import typing
from typing import Any, Callable, Literal, get_args, get_origin

_SIMPLE = {str: "string", int: "integer", float: "number", bool: "boolean", dict: "object"}


def type_to_schema(tp: Any) -> dict:
    origin = get_origin(tp)
    if origin in (typing.Union, types.UnionType):
        non_none = [a for a in get_args(tp) if a is not type(None)]
        return type_to_schema(non_none[0])
    if origin is Literal:
        return {"type": "string", "enum": list(get_args(tp))}
    if origin is list:
        args = get_args(tp)
        return {"type": "array", "items": type_to_schema(args[0])} if args else {"type": "array"}
    if origin is dict:
        return {"type": "object"}
    if tp in _SIMPLE:
        return {"type": _SIMPLE[tp]}
    raise TypeError(f"unsupported parameter type: {tp!r}")


def parse_docstring(doc: str | None) -> tuple[str, dict[str, str]]:
    doc = inspect.cleandoc(doc or "")
    summary, _, rest = doc.partition("Args:")
    params: dict[str, str] = {}
    lines = [ln for ln in rest.splitlines() if ln.strip()]
    if not lines:
        return summary.strip(), params
    indent = len(lines[0]) - len(lines[0].lstrip())  # indentation of a parameter line
    current = None
    for line in lines:
        this_indent = len(line) - len(line.lstrip())
        m = re.match(r"^\s*(\w+)(?:\s*\([^)]*\))?:\s*(.*)$", line)
        if m and this_indent == indent:
            current = m.group(1)
            params[current] = m.group(2).strip()
        elif current and this_indent > indent:
            params[current] += " " + line.strip()
        else:
            break  # a new section (e.g. "Returns:") ends Args
    return summary.strip(), params


def function_to_tool(fn: Callable) -> dict:
    summary, param_docs = parse_docstring(fn.__doc__)
    hints = typing.get_type_hints(fn)
    props, required = {}, []
    for name, p in inspect.signature(fn).parameters.items():
        schema = type_to_schema(hints.get(name, str))
        if name in param_docs:
            schema["description"] = param_docs[name]
        props[name] = schema
        if p.default is inspect.Parameter.empty:
            required.append(name)
    return {
        "name": fn.__name__,
        "description": summary,
        "input_schema": {"type": "object", "properties": props, "required": required},
    }


class ToolRegistry:
    def __init__(self, max_output_chars: int = 4000):
        self.max_output_chars = max_output_chars
        self._fns: dict[str, Callable] = {}
        self._defs: dict[str, dict] = {}

    def register(self, fn: Callable) -> Callable:
        self._fns[fn.__name__] = fn
        self._defs[fn.__name__] = function_to_tool(fn)
        return fn

    def definitions(self) -> list[dict]:
        return list(self._defs.values())

    def call(self, name: str, args: dict) -> tuple[str, bool]:
        if name not in self._fns:
            return f"Unknown tool '{name}'. Available: {', '.join(sorted(self._fns))}", True
        schema = self._defs[name]["input_schema"]
        missing = [r for r in schema["required"] if r not in args]
        if missing:
            return f"Missing required argument(s): {', '.join(missing)}", True
        unexpected = [a for a in args if a not in schema["properties"]]
        if unexpected:
            return (f"Unexpected argument(s): {', '.join(unexpected)}. "
                    f"Valid: {', '.join(schema['properties'])}"), True
        try:
            out = self._fns[name](**args)
        except Exception as e:
            return f"{type(e).__name__}: {e}", True
        out = out if isinstance(out, str) else json.dumps(out, default=str)
        if len(out) > self.max_output_chars:
            cut = len(out) - self.max_output_chars
            out = out[: self.max_output_chars] + f"\n...[truncated {cut} chars]"
        return out, False

    def impls(self) -> dict[str, Callable[..., str]]:
        """Adapter for run_agent: each impl goes through call() so validation applies.

        Errors are raised (not returned) so run_agent's error path flags them is_error.
        """
        def make(n):
            def impl(**kw):
                out, err = self.call(n, kw)
                if err:
                    raise ToolCallError(out)
                return out
            return impl
        return {n: make(n) for n in self._fns}


class ToolCallError(Exception):
    pass
