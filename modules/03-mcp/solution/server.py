"""Reference solution: a notes MCP server.

Run over stdio (what Claude Desktop / Claude Code do):
    uv run python modules/03-mcp/solution/server.py
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
    server = MCPServer("notes", instructions="A personal notebook. Search before adding to avoid duplicates.")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True))
    def search_notes(query: str = "", tag: str | None = None) -> str:
        """Search notes by text in the title or body, optionally filtered by tag.

        Returns a JSON list of {title, tags, preview}. Use read_note for the full body.
        An empty query with no tag lists every note.
        """
        hits = store.search(query, tag)
        return json.dumps([{"title": n.title, "tags": n.tags, "preview": n.body[:100]} for n in hits])

    @server.tool(annotations=ToolAnnotations(read_only_hint=True))
    def read_note(title: str) -> str:
        """Read the full body of a note by its exact title (case-insensitive)."""
        try:
            return json.dumps(asdict(store.get(title)))
        except KeyError as e:
            raise ToolError(f"{e.args[0]}. Use search_notes to find titles.") from None

    @server.tool(annotations=ToolAnnotations(destructive_hint=False))
    def add_note(title: str, body: str, tags: list[str] | None = None) -> str:
        """Create a new note. Titles must be unique (case-insensitive)."""
        try:
            n = store.add(title, body, tags)
        except ValueError as e:
            raise ToolError(str(e)) from None
        return f"Saved note {n.title!r}."

    @server.tool(annotations=ToolAnnotations(destructive_hint=True))
    def delete_note(title: str) -> str:
        """Permanently delete a note by its exact title."""
        try:
            n = store.delete(title)
        except KeyError as e:
            raise ToolError(e.args[0]) from None
        return f"Deleted note {n.title!r}."

    return server


if __name__ == "__main__":
    default = Path(__file__).resolve().parents[1] / "notes.json"
    build_server(NoteStore(os.environ.get("NOTES_PATH", default))).run()
