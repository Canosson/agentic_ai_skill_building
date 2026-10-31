"""Reference solution: the Module 05 patterns as LangGraph state graphs."""

from __future__ import annotations

import json
import operator
import re
from typing import Annotated, Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from lab.llm import LLM


def ask(llm: LLM, system: str, prompt: str, max_tokens: int = 1024) -> str:
    return llm.complete(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens).text


def extract_json(s: str):
    m = re.search(r"(\{.*\}|\[.*\])", s, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON found in: {s[:200]!r}")
    return json.loads(m.group(1))


# ---------------------------------------------------------------- 1. chain

class ChainState(TypedDict):
    current: str
    outputs: list[str]
    error: str | None


def build_chain_graph(llm: LLM, steps: list[tuple[str, Callable[[str], bool] | None]]):
    def make_node(i: int, instruction: str, gate):
        def node(state: ChainState) -> dict:
            out = ask(llm, instruction, state["current"])
            failed = gate is not None and not gate(out)
            return {
                "current": out,
                "outputs": [*state["outputs"], out],
                "error": f"gate failed after step {i}" if failed else None,
            }
        return node

    def after(next_name: str):
        return lambda state: END if state["error"] else next_name

    graph = StateGraph(ChainState)
    names = [f"step_{i}" for i in range(len(steps))]
    for i, (instruction, gate) in enumerate(steps):
        graph.add_node(names[i], make_node(i, instruction, gate))
    graph.add_edge(START, names[0])
    for i, name in enumerate(names):
        nxt = names[i + 1] if i + 1 < len(names) else END
        graph.add_conditional_edges(name, after(nxt), [nxt, END] if nxt != END else [END])
    return graph.compile()


# ---------------------------------------------------------------- 2. router

ROUTER_SYSTEM = ("Classify the user's request into exactly one category. "
                 "Reply with ONLY the category name, nothing else.")


class RouterState(TypedDict):
    query: str
    category: str
    answer: str


def build_router_graph(llm: LLM, handlers: dict[str, Callable[[str], str]], fallback: str):
    def classify(state: RouterState) -> dict:
        options = "\n".join(f"- {name}" for name in handlers)
        label = ask(llm, ROUTER_SYSTEM, f"Categories:\n{options}\n\nRequest: {state['query']}", max_tokens=20)
        label = label.strip().strip(".").strip("`'\"").lower()
        return {"category": next((n for n in handlers if n.lower() == label), fallback)}

    def make_handler(name: str):
        return lambda state: {"answer": handlers[name](state["query"])}

    graph = StateGraph(RouterState)
    graph.add_node("classify", classify)
    for name in handlers:
        graph.add_node(f"handle_{name}", make_handler(name))
        graph.add_edge(f"handle_{name}", END)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify", lambda state: state["category"], {name: f"handle_{name}" for name in handlers}
    )
    return graph.compile()


# ---------------------------------------------------------------- 3. orchestrator-workers

PLANNER_SYSTEM = ("Break the task into independent subtasks that can be done in parallel. "
                  'Reply with ONLY a JSON list of strings, e.g. ["subtask 1", "subtask 2"].')
SYNTH_SYSTEM = "Combine the workers' results into one coherent answer to the original task."


class OrchestratorState(TypedDict):
    task: str
    subtasks: list[str]
    results: Annotated[list[tuple[int, str]], operator.add]
    errors: Annotated[list[str], operator.add]
    final: str


def build_orchestrator_graph(llm: LLM, worker: Callable[[str], str], max_subtasks: int = 5):
    def plan(state: OrchestratorState) -> dict:
        subtasks = extract_json(ask(llm, PLANNER_SYSTEM, state["task"]))
        if not isinstance(subtasks, list) or not subtasks or not all(isinstance(s, str) for s in subtasks):
            raise ValueError(f"planner returned an invalid plan: {subtasks!r}")
        return {"subtasks": subtasks[:max_subtasks]}

    def fan_out(state: OrchestratorState) -> list[Send]:
        return [Send("work", {"index": i, "subtask": s}) for i, s in enumerate(state["subtasks"])]

    def work(payload: dict) -> dict:
        i, sub = payload["index"], payload["subtask"]
        try:
            return {"results": [(i, worker(sub))]}
        except Exception as e:
            return {"results": [(i, f"[worker failed: {type(e).__name__}: {e}]")], "errors": [f"{sub}: {e}"]}

    def synthesise(state: OrchestratorState) -> dict:
        ordered = [out for _, out in sorted(state["results"])]
        joined = "\n\n".join(
            f"## Subtask {i + 1}: {s}\n{o}" for i, (s, o) in enumerate(zip(state["subtasks"], ordered))
        )
        return {"final": ask(llm, SYNTH_SYSTEM, f"Original task: {state['task']}\n\nWorker results:\n{joined}")}

    graph = StateGraph(OrchestratorState)
    graph.add_node("plan", plan)
    graph.add_node("work", work)
    graph.add_node("synthesise", synthesise)
    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", fan_out, ["work"])
    graph.add_edge("work", "synthesise")
    graph.add_edge("synthesise", END)
    return graph.compile()


# ---------------------------------------------------------------- 4. evaluator-optimizer

CRITIC_SYSTEM = ("You review drafts against the criteria. Reply with ONLY JSON: "
                 '{"approved": true|false, "feedback": "<specific changes needed>"}')


class RefineState(TypedDict):
    task: str
    criteria: str
    draft: str
    feedback: str
    approved: bool
    round: int
    history: list[tuple[str, str]]


def build_refine_graph(llm: LLM, max_rounds: int = 3):
    def draft(state: RefineState) -> dict:
        return {"draft": ask(llm, "Complete the task.", state["task"]), "round": 0, "history": []}

    def critique(state: RefineState) -> dict:
        try:
            verdict = extract_json(
                ask(llm, CRITIC_SYSTEM, f"Criteria:\n{state['criteria']}\n\nDraft:\n{state['draft']}")
            )
            approved, feedback = verdict.get("approved") is True, str(verdict.get("feedback", ""))
        except (ValueError, json.JSONDecodeError, AttributeError):
            approved, feedback = False, "Critic output unreadable; improve clarity and re-check the criteria."
        return {
            "approved": approved,
            "feedback": feedback,
            "round": state["round"] + 1,
            "history": [*state["history"], (state["draft"], feedback)],
        }

    def revise(state: RefineState) -> dict:
        return {"draft": ask(
            llm, "Revise the draft using the feedback. Return only the revised draft.",
            f"Task: {state['task']}\n\nDraft:\n{state['draft']}\n\nFeedback:\n{state['feedback']}",
        )}

    def next_step(state: RefineState) -> str:
        return END if state["approved"] or state["round"] >= max_rounds else "revise"

    graph = StateGraph(RefineState)
    graph.add_node("draft", draft)
    graph.add_node("critique", critique)
    graph.add_node("revise", revise)
    graph.add_edge(START, "draft")
    graph.add_edge("draft", "critique")
    graph.add_conditional_edges("critique", next_step, ["revise", END])
    graph.add_edge("revise", "critique")
    return graph.compile()
