from typing import Literal, Optional

import pytest

from lab.testing import load

t = load(__file__, "tools")


# ---------------------------------------------------------------- type_to_schema

@pytest.mark.parametrize("tp, expected", [
    (str, {"type": "string"}),
    (int, {"type": "integer"}),
    (float, {"type": "number"}),
    (bool, {"type": "boolean"}),
    (dict, {"type": "object"}),
    (dict[str, int], {"type": "object"}),
    (list[str], {"type": "array", "items": {"type": "string"}}),
    (list[list[int]], {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}}),
    (Literal["asc", "desc"], {"type": "string", "enum": ["asc", "desc"]}),
    (Optional[int], {"type": "integer"}),
    (str | None, {"type": "string"}),
])
def test_type_to_schema(tp, expected):
    assert t.type_to_schema(tp) == expected


def test_type_to_schema_rejects_unknown_types():
    with pytest.raises(TypeError):
        t.type_to_schema(set)


# ---------------------------------------------------------------- docstrings

DOC = """Search the notes.

    Longer explanation here.

    Args:
        query: Words to look for.
        limit: Max results. Keep it small,
            the model reads every one.

    Returns:
        A list of notes.
    """


def test_parse_docstring_summary_and_params():
    summary, params = t.parse_docstring(DOC)
    assert summary == "Search the notes.\n\nLonger explanation here."
    assert params == {
        "query": "Words to look for.",
        "limit": "Max results. Keep it small, the model reads every one.",
    }


def test_parse_docstring_without_args():
    assert t.parse_docstring("Just a summary.") == ("Just a summary.", {})
    assert t.parse_docstring(None) == ("", {})


# ---------------------------------------------------------------- function_to_tool

def search_notes(query: str, limit: int = 5, tags: list[str] | None = None) -> str:
    """Search saved notes by keyword.

    Args:
        query: Words to look for.
        limit: Max results to return.
    """
    return "[]"


def test_function_to_tool():
    assert t.function_to_tool(search_notes) == {
        "name": "search_notes",
        "description": "Search saved notes by keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Words to look for."},
                "limit": {"type": "integer", "description": "Max results to return."},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query"],
        },
    }


# ---------------------------------------------------------------- registry

@pytest.fixture
def reg():
    r = t.ToolRegistry(max_output_chars=50)

    @r.register
    def greet(name: str, excited: bool = False) -> str:
        """Greet someone."""
        return f"Hello {name}" + ("!" if excited else ".")

    @r.register
    def stats() -> dict:
        """Numbers."""
        return {"n": 3}

    @r.register
    def dump() -> str:
        """Too much output."""
        return "x" * 120

    @r.register
    def fail(reason: str) -> str:
        """Always fails."""
        raise RuntimeError(reason)

    return r


def test_register_works_as_decorator_and_builds_definitions(reg):
    names = [d["name"] for d in reg.definitions()]
    assert names == ["greet", "stats", "dump", "fail"]


def test_call_happy_path(reg):
    assert reg.call("greet", {"name": "Ada", "excited": True}) == ("Hello Ada!", False)
    assert reg.call("stats", {}) == ('{"n": 3}', False)


def test_call_unknown_tool(reg):
    content, err = reg.call("wave", {})
    assert err and "greet" in content


def test_call_missing_argument(reg):
    content, err = reg.call("greet", {})
    assert err and "name" in content


def test_call_unexpected_argument_lists_valid_ones(reg):
    content, err = reg.call("greet", {"name": "Ada", "loud": True})
    assert err and "loud" in content and "name" in content and "excited" in content


def test_call_exception(reg):
    content, err = reg.call("fail", {"reason": "disk full"})
    assert err and content == "RuntimeError: disk full"


def test_call_truncates_long_output(reg):
    content, err = reg.call("dump", {})
    assert not err
    assert content == "x" * 50 + "\n...[truncated 70 chars]"
