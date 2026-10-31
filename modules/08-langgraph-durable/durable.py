"""Module 08: what a graph buys you that a loop doesn't: pausing, resuming and tracing.

Three things production agents need that a `while` loop doesn't give you for free:
  1. a human can approve a risky action, hours later, from another process
  2. a crash at step 4 doesn't re-run (and re-bill, and re-send) steps 1-3
  3. you can see exactly which nodes ran, which is what you assert on in evals

All of them rest on one idea: a **checkpointer** saves the state after every node, keyed by a
`thread_id`. Tests use `InMemorySaver`; production uses SQLite/Postgres with the same API.

    uv run pytest modules/08-langgraph-durable -x
    uv run python modules/08-langgraph-durable/demo.py

Docs: https://docs.langchain.com/oss/python/langgraph/interrupts
      https://docs.langchain.com/oss/python/langgraph/persistence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from lab.llm import LLM


def ask(llm: LLM, system: str, prompt: str, max_tokens: int = 1024) -> str:
    return llm.complete(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens).text


def thread(thread_id: str) -> dict:
    """The `config` that ties a run to a saved conversation. Same id = same saved state."""
    return {"configurable": {"thread_id": thread_id}}


# ---------------------------------------------------------------- 1. human approval

DRAFT_SYSTEM = "Draft a short, polite reply to the customer's ticket. Return only the reply."


class ApprovalState(TypedDict, total=False):
    ticket: str
    draft: str
    decision: dict   # what the human answered: {"approved": bool, "edited": str | None}
    outcome: str     # "sent" | "rejected"


def build_approval_graph(llm: LLM, send_fn: Callable[[str], None], checkpointer):
    """draft -> review (pause for a human) -> send or reject.

    Nodes, named exactly like this (the tests and traces use the names):
      - "draft":  state["draft"] = ask(llm, DRAFT_SYSTEM, state["ticket"])
      - "review": decision = interrupt({"draft": state["draft"]}); return {"decision": decision}
                  interrupt() pauses the whole graph. When someone later calls
                  graph.invoke(Command(resume=<answer>), config), interrupt() returns <answer>.
      - "send":   send_fn(decision["edited"] if the human edited, else the draft); outcome = "sent"
      - "reject": outcome = "rejected"
    After "review": go to "send" ONLY if decision["approved"] is exactly True. Anything else
    (missing key, "yes", None) is a rejection: fail closed on a risky action.
    Compile with graph.compile(checkpointer=checkpointer).

    The trap this module is built around: when you resume, the node that contains interrupt()
    restarts from its first line. So anything before the interrupt() call runs twice. Which of
    the nodes above must therefore NOT contain the model call or the send?
    Initial state: {"ticket": ...}.
    """
    # TODO(08-a)
    raise NotImplementedError


# ---------------------------------------------------------------- 2. crash recovery

class PipelineState(TypedDict):
    value: str


def build_pipeline(steps: list[tuple[str, Callable[[str], str]]], checkpointer):
    """A straight line of nodes. Node `name` runs fn(state["value"]) and stores the result in
    state["value"]. Chain them START -> first -> ... -> last -> END, and compile with the checkpointer.

    If a node raises, the checkpoint from the previous node survives. get_state(config).next then
    names the node that failed, and graph.invoke(None, config) continues from there.
    """
    # TODO(08-b)
    raise NotImplementedError


def run_with_resume(graph, initial: dict, thread_id: str, max_attempts: int = 3,
                    retry_on: tuple[type[Exception], ...] = (Exception,)) -> dict:
    """Run the graph, and if it raises one of `retry_on`, RESUME it rather than restarting it.

    - attempt 1: graph.invoke(initial, thread(thread_id))
    - later attempts: graph.invoke(None, thread(thread_id))   # None = continue from the checkpoint
    - after max_attempts failures, re-raise the last error.
    - an exception NOT in retry_on propagates immediately (a bug or bad input won't fix itself).
    """
    # TODO(08-b)
    raise NotImplementedError


# ---------------------------------------------------------------- 3. traceability

@dataclass
class RunTrace:
    nodes: list[str] = field(default_factory=list)   # nodes that ran during THIS call, in order
    interrupted: bool = False                         # True if the run stopped at an interrupt()
    state: dict = field(default_factory=dict)         # the saved state after the call


def trace_run(graph, graph_input, thread_id: str) -> RunTrace:
    """Run the graph with graph.stream(..., stream_mode="updates") and record what happened.

    Each streamed chunk is a dict {node_name: update}. An interrupt shows up as a chunk with the
    key "__interrupt__": that is not a node, so don't list it, but do set interrupted=True.
    Afterwards read the saved state with graph.get_state(config).values.

    This is the bridge to Module 04: an eval can now assert on the *trajectory*
    ("the refund path never reached `send` without a `review`"), not just the final text.
    """
    # TODO(08-c)
    raise NotImplementedError
