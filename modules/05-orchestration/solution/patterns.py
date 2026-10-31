"""Reference solution: the core workflow and multi-agent patterns."""

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
    outputs, current = [], initial
    for i, (instruction, gate) in enumerate(steps):
        current = ask(llm, instruction, current)
        outputs.append(current)
        if gate is not None and not gate(current):
            raise ValueError(f"gate failed after step {i}: {current[:200]!r}")
    return outputs


# ---------------------------------------------------------------- 2. routing

ROUTER_SYSTEM = ("Classify the user's request into exactly one category. "
                 "Reply with ONLY the category name, nothing else.")


def route(llm: LLM, query: str, handlers: dict[str, Callable[[str], str]], fallback: str) -> tuple[str, str]:
    options = "\n".join(f"- {name}" for name in handlers)
    label = ask(llm, ROUTER_SYSTEM, f"Categories:\n{options}\n\nRequest: {query}", max_tokens=20)
    label = label.strip().strip(".").strip("`'\"").lower()
    chosen = next((n for n in handlers if n.lower() == label), fallback)
    return chosen, handlers[chosen](query)


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
    plan = extract_json(ask(llm, PLANNER_SYSTEM, task))
    if not isinstance(plan, list) or not all(isinstance(s, str) for s in plan) or not plan:
        raise ValueError(f"planner returned an invalid plan: {plan!r}")
    subtasks = plan[:max_subtasks]

    def safe(sub):
        try:
            return worker(sub), None
        except Exception as e:
            return f"[worker failed: {type(e).__name__}: {e}]", f"{sub}: {e}"

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pairs = list(pool.map(safe, subtasks))  # map preserves order
    outputs = [p[0] for p in pairs]
    errors = [p[1] for p in pairs if p[1]]
    joined = "\n\n".join(f"## Subtask {i + 1}: {s}\n{o}" for i, (s, o) in enumerate(zip(subtasks, outputs)))
    final = ask(llm, SYNTH_SYSTEM, f"Original task: {task}\n\nWorker results:\n{joined}")
    return OrchestrationResult(subtasks, outputs, final, errors)


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
    draft = ask(llm, "Complete the task.", task)
    history = []
    for rnd in range(1, max_rounds + 1):
        try:
            verdict = extract_json(ask(llm, CRITIC_SYSTEM, f"Criteria:\n{criteria}\n\nDraft:\n{draft}"))
            approved, feedback = bool(verdict.get("approved") is True), str(verdict.get("feedback", ""))
        except (ValueError, json.JSONDecodeError, AttributeError):
            approved, feedback = False, "Critic output unreadable; improve clarity and re-check the criteria."
        history.append((draft, feedback))
        if approved:
            return RefineResult(draft, rnd, True, history)
        if rnd == max_rounds:
            break
        draft = ask(llm, "Revise the draft using the feedback. Return only the revised draft.",
                    f"Task: {task}\n\nDraft:\n{draft}\n\nFeedback:\n{feedback}")
    return RefineResult(draft, max_rounds, False, history)
