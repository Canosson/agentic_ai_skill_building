"""Module 03b: the client side. Turn any MCP server's tools into tools for your own loop.

This is what Claude Desktop, Claude Code and every agent framework's "MCP adapter" do.
"""

from __future__ import annotations

from typing import Any


def mcp_tools_to_anthropic(tools: list[Any]) -> list[dict]:
    """MCP Tool objects (from `(await client.list_tools()).tools`) -> Anthropic tool dicts.

    Each MCP tool has .name, .description (may be None) and .input_schema (already JSON Schema).
    Return [{"name": ..., "description": ... or "", "input_schema": ...}, ...]
    """
    # TODO(03-d)
    raise NotImplementedError("mcp_tools_to_anthropic")


def result_to_text(result: Any) -> tuple[str, bool]:
    """An MCP CallToolResult -> (text, is_error) for a tool_result block.

    result.content is a list of blocks; text blocks have .type == "text" and .text.
    - Join the text blocks with "\\n".
    - If there are non-text blocks (images, resources...), append one line:
      "[N non-text block(s) omitted: image, resource]"
    - is_error comes from result.is_error (make it a real bool).
    """
    # TODO(03-e)
    raise NotImplementedError("result_to_text")


def needs_approval(tool: Any) -> bool:
    """Should a human approve calls to this MCP tool? Follow the MCP spec's defaults:

    - No annotations at all              -> True  (unknown = assume risky)
    - read_only_hint is True             -> False
    - destructive_hint is False          -> False
    - otherwise (destructive True/None)  -> True  (the spec's default for destructive is True)
    """
    # TODO(03-f)
    raise NotImplementedError("needs_approval")
