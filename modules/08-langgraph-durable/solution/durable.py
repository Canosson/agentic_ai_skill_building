"""Reference solution: human-in-the-loop, crash recovery and traceability with LangGraph."""

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
    decision: dict
    outcome: str  # "sent" | "rejected"


def build_approval_graph(llm: LLM, send_fn: Callable[[str], None], checkpointer):
    def draft(state: ApprovalState) -> dict:
        return {"draft": ask(llm, DRAFT_SYSTEM, state["ticket"])}

    def review(state: ApprovalState) -> dict:
        # Pauses here. On resume this node restarts, and interrupt() returns the human's answer.
        decision = interrupt({"draft": state["draft"]})
        return {"decision": decision}

    def send(state: ApprovalState) -> dict:
        decision = state["decision"]
        send_fn(decision.get("edited") or state["draft"])
        return {"outcome": "sent"}

    def reject(state: ApprovalState) -> dict:
        return {"outcome": "rejected"}

    graph = StateGraph(ApprovalState)
    graph.add_node("draft", draft)
    graph.add_node("review", review)
    graph.add_node("send", send)
    graph.add_node("reject", reject)
    graph.add_edge(START, "draft")
    graph.add_edge("draft", "review")
    graph.add_conditional_edges(
        "review", lambda s: "send" if s["decision"].get("approved") is True else "reject", ["send", "reject"]
    )
    graph.add_edge("send", END)
    graph.add_edge("reject", END)
    return graph.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------- 2. crash recovery

class PipelineState(TypedDict):
    value: str


def build_pipeline(steps: list[tuple[str, Callable[[str], str]]], checkpointer):
    def make_node(fn):
        return lambda state: {"value": fn(state["value"])}

    graph = StateGraph(PipelineState)
    for name, fn in steps:
        graph.add_node(name, make_node(fn))
    graph.add_edge(START, steps[0][0])
    for (a, _), (b, _) in zip(steps, steps[1:]):
        graph.add_edge(a, b)
    graph.add_edge(steps[-1][0], END)
    return graph.compile(checkpointer=checkpointer)


def run_with_resume(graph, initial: dict, thread_id: str, max_attempts: int = 3,
                    retry_on: tuple[type[Exception], ...] = (Exception,)) -> dict:
    config = thread(thread_id)
    payload: dict | None = initial
    for attempt in range(1, max_attempts + 1):
        try:
            return graph.invoke(payload, config)
        except retry_on:
            if attempt == max_attempts:
                raise
            payload = None  # None = "continue from the last checkpoint"
    raise AssertionError("unreachable")


# ---------------------------------------------------------------- 3. traceability

@dataclass
class RunTrace:
    nodes: list[str] = field(default_factory=list)
    interrupted: bool = False
    state: dict = field(default_factory=dict)


def trace_run(graph, graph_input, thread_id: str) -> RunTrace:
    config = thread(thread_id)
    trace = RunTrace()
    for chunk in graph.stream(graph_input, config, stream_mode="updates"):
        for key in chunk:
            if key == "__interrupt__":
                trace.interrupted = True
            else:
                trace.nodes.append(key)
    trace.state = dict(graph.get_state(config).values)
    return trace
