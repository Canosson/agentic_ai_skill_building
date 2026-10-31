"""Your agent loop + your MCP server, talking over stdio like a real host.

    uv run python modules/03-mcp/demo.py "Save a note called 'MCP' explaining what it is, tagged ai"
    uv run python modules/03-mcp/demo.py "What notes do I have about ai?"
    uv run python modules/03-mcp/demo.py "Delete the MCP note"        # asks for your approval

How the pieces fit:
  main thread (asyncio)  : owns the MCP connection to the server subprocess
  worker thread          : runs the synchronous run_agent loop
  tool impls             : hop from the worker thread back onto the event loop
"""

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.llm import AnthropicLLM
from lab.loop import run_agent
from lab.testing import load, using_solution

bridge = load(__file__, "bridge")
HERE = Path(__file__).resolve().parent
SERVER = HERE / ("solution" if using_solution() else "") / "server.py"


def trace(kind, data):
    if kind == "tool":
        flag = " [ERROR]" if data["is_error"] else ""
        print(f"  {data['name']}({data['input']}) -> {data['output'][:150]}{flag}")


async def main(question: str) -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)],
                                   env={"NOTES_PATH": str(HERE / "notes.json")})
    async with Client(params) as client:
        mcp_tools = (await client.list_tools()).tools
        risky = {t.name for t in mcp_tools if bridge.needs_approval(t)}
        loop = asyncio.get_running_loop()

        def make_impl(name):
            def impl(**args):
                if name in risky:
                    ok = input(f"\n  ⚠ approve {name}({args})? [y/N] ").strip().lower() == "y"
                    if not ok:
                        raise PermissionError("The user declined this action.")
                fut = asyncio.run_coroutine_threadsafe(client.call_tool(name, args), loop)
                text, is_error = bridge.result_to_text(fut.result(timeout=30))
                if is_error:
                    raise RuntimeError(text)
                return text
            return impl

        llm = AnthropicLLM()
        print(f"\nQ: {question}\n   (tools: {[t.name for t in mcp_tools]}, needs approval: {sorted(risky)})\n")
        result = await asyncio.to_thread(
            run_agent, llm, question, bridge.mcp_tools_to_anthropic(mcp_tools),
            {t.name: make_impl(t.name) for t in mcp_tools}, on_event=trace,
            system="You manage the user's notes with the tools provided. Be concise.",
        )
        print(f"\nA: {result.final_text}\n\nturns={result.turns} tokens={llm.usage}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "What notes do I have?"))
