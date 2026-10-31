"""Module 03 tests. The server is tested over a real MCP connection, in-process."""

import asyncio
import json
from types import SimpleNamespace as NS

import pytest
from mcp import Client

from lab.testing import load

srv = load(__file__, "server")
bridge = load(__file__, "bridge")


def run(coro):
    return asyncio.run(coro)


async def with_client(fn, store=None):
    store = store or srv.NoteStore()
    async with Client(srv.build_server(store)) as c:
        return await fn(c)


async def tools_by_name(c):
    return {t.name: t for t in (await c.list_tools()).tools}


# ---------------------------------------------------------------- server


def test_server_exposes_four_tools():
    names = run(with_client(lambda c: tools_by_name(c)))
    assert set(names) == {"search_notes", "read_note", "add_note", "delete_note"}


def test_tool_schemas_have_right_required_params():
    tools = run(with_client(tools_by_name))
    assert tools["add_note"].input_schema["required"] == ["title", "body"]
    assert tools["read_note"].input_schema["required"] == ["title"]
    assert tools["delete_note"].input_schema["required"] == ["title"]


def test_tool_annotations():
    tools = run(with_client(tools_by_name))
    assert tools["read_note"].annotations.read_only_hint is True
    assert tools["add_note"].annotations.destructive_hint is False
    assert tools["delete_note"].annotations.destructive_hint is True


def test_add_then_search_then_read():
    async def flow(c):
        r = await c.call_tool("add_note", {"title": "MCP", "body": "Model Context Protocol", "tags": ["AI"]})
        assert not r.is_error and "Saved note 'MCP'" in r.content[0].text
        hits = json.loads((await c.call_tool("search_notes", {"tag": "ai"})).content[0].text)
        assert [h["title"] for h in hits] == ["MCP"]
        note = json.loads((await c.call_tool("read_note", {"title": "mcp"})).content[0].text)
        assert note == {"title": "MCP", "body": "Model Context Protocol", "tags": ["ai"]}
    run(with_client(flow))


def test_duplicate_add_is_a_clear_error():
    async def flow(c):
        await c.call_tool("add_note", {"title": "A", "body": "1"})
        r = await c.call_tool("add_note", {"title": "a", "body": "2"})
        assert r.is_error and "already exists" in r.content[0].text
    run(with_client(flow))


def test_read_unknown_note_tells_model_how_to_recover():
    async def flow(c):
        r = await c.call_tool("read_note", {"title": "nope"})
        assert r.is_error and "search_notes" in r.content[0].text
    run(with_client(flow))


def test_delete():
    store = srv.NoteStore()
    store.add("Old", "x")

    async def flow(c):
        r = await c.call_tool("delete_note", {"title": "old"})
        assert not r.is_error and "Deleted note 'Old'" in r.content[0].text
        r = await c.call_tool("delete_note", {"title": "old"})
        assert r.is_error and "no note" in r.content[0].text
    run(with_client(flow, store))
    assert store.notes == {}


def test_store_persists_to_disk(tmp_path):
    p = tmp_path / "notes.json"
    srv.NoteStore(p).add("Keep", "me")
    assert srv.NoteStore(p).get("keep").body == "me"


# ---------------------------------------------------------------- bridge


def test_mcp_tools_to_anthropic_from_live_server():
    tools = run(with_client(lambda c: c.list_tools())).tools
    defs = {d["name"]: d for d in bridge.mcp_tools_to_anthropic(tools)}
    assert set(defs["add_note"]) == {"name", "description", "input_schema"}
    assert defs["add_note"]["input_schema"]["type"] == "object"
    assert "unique" in defs["add_note"]["description"]


def test_mcp_tools_to_anthropic_handles_missing_description():
    tool = NS(name="x", description=None, input_schema={"type": "object", "properties": {}})
    assert bridge.mcp_tools_to_anthropic([tool])[0]["description"] == ""


def test_result_to_text():
    ok = NS(is_error=False, content=[NS(type="text", text="a"), NS(type="text", text="b")])
    assert bridge.result_to_text(ok) == ("a\nb", False)
    mixed = NS(is_error=None, content=[NS(type="text", text="see chart"), NS(type="image")])
    assert bridge.result_to_text(mixed) == ("see chart\n[1 non-text block(s) omitted: image]", False)
    err = NS(is_error=True, content=[NS(type="text", text="boom")])
    assert bridge.result_to_text(err) == ("boom", True)


@pytest.mark.parametrize("annotations, expected", [
    (None, True),
    (NS(read_only_hint=True, destructive_hint=None), False),
    (NS(read_only_hint=None, destructive_hint=False), False),
    (NS(read_only_hint=None, destructive_hint=True), True),
    (NS(read_only_hint=None, destructive_hint=None), True),
])
def test_needs_approval(annotations, expected):
    assert bridge.needs_approval(NS(annotations=annotations)) is expected
