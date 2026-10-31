"""Module 03a: your own MCP server.

MCP (Model Context Protocol) is a standard way to expose tools to ANY agent host:
Claude Desktop, Claude Code, Cowork, and other MCP-capable clients. You write the tools once;
every host can use them.

    uv run pytest modules/03-mcp -x
    uv run python modules/03-mcp/server.py          # runs over stdio (waits for a client)

NoteStore is given (plain Python, no MCP). Your job is build_server().
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations


@dataclass
class Note:
    title: str
    body: str
    tags: list[str] = field(default_factory=list)


class NoteStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.notes: dict[str, Note] = {}
        if self.path and self.path.exists():
            for d in json.loads(self.path.read_text()):
                self.notes[d["title"].lower()] = Note(**d)

    def _save(self) -> None:
        if self.path:
            self.path.write_text(json.dumps([asdict(n) for n in self.notes.values()], indent=2))

    def add(self, title: str, body: str, tags: list[str] | None = None) -> Note:
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
        key = title.lower()
        if key in self.notes:
            raise ValueError(f"a note titled {title!r} already exists")
        note = Note(title, body, sorted({t.lower() for t in tags or []}))
        self.notes[key] = note
        self._save()
        return note

    def get(self, title: str) -> Note:
        try:
            return self.notes[title.strip().lower()]
        except KeyError:
            raise KeyError(f"no note titled {title!r}") from None

    def search(self, query: str = "", tag: str | None = None) -> list[Note]:
        q = query.lower()
        return [
            n for n in self.notes.values()
            if (q in n.title.lower() or q in n.body.lower()) and (tag is None or tag.lower() in n.tags)
        ]

    def delete(self, title: str) -> Note:
        note = self.get(title)
        del self.notes[note.title.lower()]
        self._save()
        return note


def build_server(store: NoteStore) -> MCPServer:
    """Expose the NoteStore as four MCP tools. search_notes is done as an example.

    TODO(03-a) read_note(title) -> str
        JSON of the full note. Unknown title -> raise ToolError with a message that
        tells the model how to recover (hint: mention search_notes).
    TODO(03-b) add_note(title, body, tags: list[str] | None = None) -> str
        Returns "Saved note '<title>'." Duplicate/empty title -> ToolError with the reason.
    TODO(03-c) delete_note(title) -> str
        Returns "Deleted note '<title>'." Unknown title -> ToolError.

    Annotations tell hosts how risky a tool is (hosts may ask a human before risky calls):
        read_note   -> read_only_hint=True
        add_note    -> destructive_hint=False   (adds, never destroys)
        delete_note -> destructive_hint=True

    Why ToolError? MCP hides the message of unexpected exceptions (it could leak internals).
    A ToolError is a deliberate, model-facing message.
    """
    server = MCPServer("notes", instructions="A personal notebook. Search before adding to avoid duplicates.")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True))
    def search_notes(query: str = "", tag: str | None = None) -> str:
        """Search notes by text in the title or body, optionally filtered by tag.

        Returns a JSON list of {title, tags, preview}. Use read_note for the full body.
        An empty query with no tag lists every note.
        """
        hits = store.search(query, tag)
        return json.dumps([{"title": n.title, "tags": n.tags, "preview": n.body[:100]} for n in hits])

    # your three tools here

    return server


if __name__ == "__main__":
    default = Path(__file__).resolve().parent / "notes.json"
    build_server(NoteStore(os.environ.get("NOTES_PATH", default))).run()
