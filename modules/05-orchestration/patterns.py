"""Module 05: workflow and multi-agent patterns, built from plain model calls.

These four patterns (from Anthropic's "Building effective agents") cover most of what
"multi-agent frameworks" sell. Each one is ~20 lines once you have the loop and evals.

    uv run pytest modules/05-orchestration -x
    uv run python modules/05-orchestration/demo.py
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from lab.llm import LLM


def ask(llm: LLM, system: str, prompt: str, max_tokens: int = 1024) -> str:
    return llm.complete(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens).text


def extract_json(s: str):
    m = re.search(r"(\{.*\}|\[.*\])", s, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON found in: {s[:200]!r}")
    return json.loads(m.group(1))


# ---------------------------------------------------------------- 1. prompt chaining

def chain(llm: LLM, steps: list[tuple[str, Callable[[str], bool] | None]], initial: str) -> list[str]:
    """Run steps in sequence; each step's output is the next step's input.

    Each step is (system_instruction, gate). Call ask(llm, instruction, current_input).
    If gate is not None and gate(output) is False -> raise ValueError mentioning the step index.
    (Gates are cheap programmatic checks that stop a bad chain early, before you pay for later steps.)
    Return the list of all step outputs.
    """
    # TODO(05-a)
    raise NotImplementedError


# ---------------------------------------------------------------- 2. routing

ROUTER_SYSTEM = ("Classify the user's request into exactly one category. "
                 "Reply with ONLY the category name, nothing else.")


def route(llm: LLM, query: str, handlers: dict[str, Callable[[str], str]], fallback: str) -> tuple[str, str]:
    """Classify the query with ONE cheap model call, then hand it to the matching handler.

    - System prompt: ROUTER_SYSTEM. The user prompt lists the category names and the request.
    - Normalise the label: strip whitespace, a trailing ".", quotes/backticks; compare case-insensitively.
    - Unknown label -> use `fallback`. Never crash on a bad classification.
    Returns (chosen_category_name, handler_output).
    """
    # TODO(05-b)
    raise NotImplementedError


# ---------------------------------------------------------------- 3. orchestrator-workers

PLANNER_SYSTEM = ("Break the task into independent subtasks that can be done in parallel. "
                  'Reply with ONLY a JSON list of strings, e.g. ["subtask 1", "subtask 2"].')
SYNTH_SYSTEM = "Combine the workers' results into one coherent answer to the original task."


@dataclass
class OrchestrationResult:
    subtasks: list[str]
    worker_outputs: list[str]
    final: str
    errors: list[str] = field(default_factory=list)


def orchestrate(llm: LLM, task: str, worker: Callable[[str], str], max_subtasks: int = 5,
                max_workers: int = 4) -> OrchestrationResult:
    """Planner -> parallel workers -> synthesiser.

    1. ask(llm, PLANNER_SYSTEM, task) and extract_json -> must be a non-empty list of strings,
       else raise ValueError. Keep at most max_subtasks.
    2. Run worker(subtask) for each subtask IN PARALLEL (ThreadPoolExecutor, max_workers).
       Outputs must stay in subtask order. A worker that raises must not sink the job: its output
       becomes "[worker failed: ExceptionType: message]" and "<subtask>: <message>" goes in errors.
    3. ask(llm, SYNTH_SYSTEM, ...) with the original task and every subtask + output.
    Return OrchestrationResult(subtasks, worker_outputs, final, errors).
    """
    # TODO(05-c)
    raise NotImplementedError


# ---------------------------------------------------------------- 4. evaluator-optimizer

CRITIC_SYSTEM = ("You review drafts against the criteria. Reply with ONLY JSON: "
                 '{"approved": true|false, "feedback": "<specific changes needed>"}')


@dataclass
class RefineResult:
    final: str
    rounds: int
    approved: bool
    history: list[tuple[str, str]] = field(default_factory=list)  # (draft, feedback)


def evaluate_optimize(llm: LLM, task: str, criteria: str, max_rounds: int = 3) -> RefineResult:
    """Draft -> critique -> revise, until approved or max_rounds.

    Model calls, in order:
      1. draft   = ask(llm, "Complete the task.", task)
      then for each round 1..max_rounds:
      2. verdict = extract_json(ask(llm, CRITIC_SYSTEM, <criteria + draft>))
         -> {"approved": bool, "feedback": str}. Unparseable -> treat as NOT approved.
         Append (draft, feedback) to history.
      3. approved -> return RefineResult(draft, round, True, history)
      4. not approved and rounds remain -> draft = ask(llm, <revise instruction>, <task + draft + feedback>)
    If never approved: RefineResult(last_draft, max_rounds, False, history).
    Note: no revision after the final critique (you'd be paying for a draft nobody reviews).
    """
    # TODO(05-d)
    raise NotImplementedError
