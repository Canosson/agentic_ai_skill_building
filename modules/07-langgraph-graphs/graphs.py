"""Module 07: the Module 05 patterns, rebuilt as LangGraph state graphs.

A graph is the same logic with the control flow made explicit: state is a typed dict,
steps are nodes (functions that return a *partial* state update), and decisions are
conditional edges. The payoff is that the shape of your agent becomes data you can
draw, test and checkpoint (Module 08).

    uv run pytest modules/07-langgraph-graphs -x
    uv run python modules/07-langgraph-graphs/demo.py

LangGraph essentials you need here:
    graph = StateGraph(MyState)
    graph.add_node("name", fn)                      # fn(state) -> dict of keys to update
    graph.add_edge(START, "name"); graph.add_edge("a", "b")
    graph.add_conditional_edges("a", router_fn, ["b", END])   # router_fn(state) -> next node name
    app = graph.compile(); app.invoke(initial_state)         # returns the final state
Docs: https://docs.langchain.com/oss/python/langgraph/graph-api
"""

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
    current: str          # the text the next step will read
    outputs: list[str]    # every step's output so far
    error: str | None     # set when a gate fails


def build_chain_graph(llm: LLM, steps: list[tuple[str, Callable[[str], bool] | None]]):
    """One node per step, named "step_0", "step_1", ... (the tests look for these names).

    Each node: out = ask(llm, instruction, state["current"]), then return the updated
    current/outputs, and error = "gate failed after step {i}" if the step's gate rejects
    the output (otherwise None). Don't mutate state["outputs"]: return a new list.

    After each node, a conditional edge goes to END if state["error"] is set, otherwise to
    the next step (or END after the last). Same behaviour as Module 05's `chain`.
    Initial state: {"current": <input>, "outputs": [], "error": None}.
    """
    # TODO(07-a)
    raise NotImplementedError


# ---------------------------------------------------------------- 2. router

ROUTER_SYSTEM = ("Classify the user's request into exactly one category. "
                 "Reply with ONLY the category name, nothing else.")


class RouterState(TypedDict):
    query: str
    category: str
    answer: str


def build_router_graph(llm: LLM, handlers: dict[str, Callable[[str], str]], fallback: str):
    """A "classify" node, then a conditional edge to exactly one handler node.

    - classify: ONE model call, with ROUTER_SYSTEM; the user prompt lists the category names
      and the request. Normalise the label (strip whitespace, ".", quotes/backticks; compare
      case-insensitively); an unknown label becomes `fallback`. Store it in state["category"].
    - one node per handler, named f"handle_{name}" (node names may not equal a state key,
      so a category called "answer" must still work), which sets state["answer"] = handler(query).
    - add_conditional_edges("classify", <read state["category"]>, {category: node_name, ...}).
    Initial state: {"query": ...}.
    """
    # TODO(07-b)
    raise NotImplementedError


# ---------------------------------------------------------------- 3. orchestrator-workers

PLANNER_SYSTEM = ("Break the task into independent subtasks that can be done in parallel. "
                  'Reply with ONLY a JSON list of strings, e.g. ["subtask 1", "subtask 2"].')
SYNTH_SYSTEM = "Combine the workers' results into one coherent answer to the original task."


class OrchestratorState(TypedDict):
    task: str
    subtasks: list[str]
    # `operator.add` is a *reducer*: when parallel workers each return {"results": [...]},
    # LangGraph concatenates the lists instead of letting one overwrite the others.
    results: Annotated[list[tuple[int, str]], operator.add]   # (subtask index, output)
    errors: Annotated[list[str], operator.add]
    final: str


def build_orchestrator_graph(llm: LLM, worker: Callable[[str], str], max_subtasks: int = 5):
    """plan -> parallel "work" nodes -> synthesise.

    - plan: ask(llm, PLANNER_SYSTEM, task) -> extract_json -> a non-empty list of strings,
      else raise ValueError. Keep at most max_subtasks. Store in state["subtasks"].
    - fan out with the Send API: add_conditional_edges("plan", fn, ["work"]) where fn returns
      [Send("work", {"index": i, "subtask": s}), ...]. Each Send runs one "work" node in parallel
      with its own small input (NOT the full state).
    - work: return {"results": [(index, worker(subtask))]}. A worker that raises must not sink
      the run: its output becomes "[worker failed: ExceptionType: message]" and
      "<subtask>: <message>" goes into {"errors": [...]}.
    - synthesise: results arrive in whatever order the workers finished, so SORT by index before
      writing the prompt. Then ask(llm, SYNTH_SYSTEM, ...) with the original task and every
      "## Subtask N: <subtask>\\n<output>" in order. Store in state["final"].
    Initial state: {"task": ...}.
    """
    # TODO(07-c)
    raise NotImplementedError


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
    history: list[tuple[str, str]]   # (draft, feedback) per critique


def build_refine_graph(llm: LLM, max_rounds: int = 3):
    """draft -> critique -> (revise -> critique)* until approved or max_rounds.

    - draft: ask(llm, "Complete the task.", task); also initialise round=0 and history=[].
    - critique: verdict = extract_json(ask(llm, CRITIC_SYSTEM, <criteria + draft>)). Unparseable
      or approved is not exactly True -> NOT approved. Return approved, feedback, round+1 and
      history with (draft, feedback) appended.
    - revise: ask(llm, <revise instruction>, <task + draft + feedback>) -> new draft.
    - a conditional edge after critique: END if approved or round >= max_rounds (no revision
      that nobody will review), otherwise "revise". Then revise -> critique closes the loop.
    Initial state: {"task": ..., "criteria": ...}.
    """
    # TODO(07-d)
    raise NotImplementedError
