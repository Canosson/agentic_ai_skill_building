"""Module 04: an eval harness. The skill that separates people who demo agents from people who ship them.

    uv run pytest modules/04-evals -x
    uv run python modules/04-evals/run.py --save baseline
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from lab.llm import LLM

# ---------------------------------------------------------------- data (given)


@dataclass
class Case:
    """One test case. `expect` keys: contains, not_contains, tool_called, max_turns, rubric."""
    id: str
    input: str
    expect: dict


@dataclass
class Trial:
    """What the agent did on one run of one case."""
    output: str
    tool_calls: list[str] = field(default_factory=list)  # tool names, in order
    turns: int = 1
    tokens: int = 0


@dataclass
class CaseResult:
    case_id: str
    passed: bool              # True only if EVERY trial passed
    checks: dict[str, bool]   # check name -> passed (from the first failing trial, else the last)
    trials_passed: int
    trials: int
    notes: list[str] = field(default_factory=list)


@dataclass
class Report:
    results: list[CaseResult]
    mean_turns: float
    total_tokens: int

    @property
    def pass_rate(self) -> float:
        return sum(r.passed for r in self.results) / len(self.results) if self.results else 0.0

    def failures(self) -> list[CaseResult]:
        return [r for r in self.results if not r.passed]

    def to_dict(self) -> dict:
        return {"pass_rate": self.pass_rate, "mean_turns": self.mean_turns,
                "total_tokens": self.total_tokens, "results": [asdict(r) for r in self.results]}

    @classmethod
    def from_dict(cls, d: dict) -> "Report":
        return cls([CaseResult(**r) for r in d["results"]], d["mean_turns"], d["total_tokens"])


def load_cases(path: str | Path) -> list[Case]:
    return [Case(**json.loads(line)) for line in Path(path).read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------- 04-a: deterministic checks
# Cheap, fast, no model needed. Use these wherever you can.

def check_contains(trial: Trial, expected: str | list[str]) -> bool:
    """True if EVERY expected string appears in trial.output. Case-insensitive, and ignore
    commas on both sides so "7,006,652" matches "7006652"."""
    # TODO(04-a)
    raise NotImplementedError


def check_not_contains(trial: Trial, forbidden: str | list[str]) -> bool:
    """True if NONE of the forbidden strings appear (case-insensitive)."""
    # TODO(04-a)
    raise NotImplementedError


def check_tool_called(trial: Trial, name: str) -> bool:
    # TODO(04-a)
    raise NotImplementedError


def check_max_turns(trial: Trial, n: int) -> bool:
    # TODO(04-a)
    raise NotImplementedError


# ---------------------------------------------------------------- 04-b: model-graded check

JUDGE_SYSTEM = (
    "You are a strict evaluator. Given a question, an answer and a rubric, decide whether the "
    'answer satisfies the rubric. Reply with ONLY a JSON object: {"pass": true|false, "reason": "<one sentence>"}'
)


def llm_judge(llm: LLM, question: str, answer: str, rubric: str) -> tuple[bool, str]:
    """Ask a model to grade an answer against a rubric. Returns (passed, reason).

    - One llm.complete call with system=JUDGE_SYSTEM and a single user message that contains the
      question, the answer and the rubric (wrap each in XML-style tags, e.g. <answer>...</answer>).
    - Judges often wrap the JSON in prose or ```json fences. Extract the first {...} and parse it.
    - Anything you can't parse into {"pass": <bool>, ...} -> (False, "judge output unparseable: ...").
      An eval must fail CLOSED: an unreadable verdict is never a pass.
    """
    # TODO(04-b)
    raise NotImplementedError


# ---------------------------------------------------------------- 04-c: grading one trial

CHECKS: dict[str, Callable[[Trial, object], bool]] = {
    "contains": check_contains,
    "not_contains": check_not_contains,
    "tool_called": check_tool_called,
    "max_turns": check_max_turns,
}


def grade(case: Case, trial: Trial, judge_llm: LLM | None = None) -> tuple[dict[str, bool], list[str]]:
    """Run every expectation in case.expect. Returns (checks, notes).

    - Keys in CHECKS -> call the check with the expectation's value.
    - "rubric"       -> llm_judge(judge_llm, case.input, trial.output, rubric); add "judge: <reason>" to notes.
                        No judge_llm -> raise ValueError (silently skipping would inflate your score).
    - Unknown key    -> raise ValueError (a typo in your dataset must not silently pass).
    """
    # TODO(04-c)
    raise NotImplementedError


# ---------------------------------------------------------------- 04-d: the runner

def run_eval(agent_fn: Callable[[str], Trial], cases: list[Case], judge_llm: LLM | None = None,
             trials: int = 1) -> Report:
    """Run every case `trials` times.

    - A case passes only if ALL its trials pass. Agents aren't deterministic; one lucky pass
      proves little.
    - If agent_fn raises, that trial fails with checks={"no_crash": False} and a note starting
      "agent crashed:". The eval itself must keep going.
    - CaseResult.checks = checks of the first failing trial, or of the last trial if all passed.
    - mean_turns over all non-crashed trials (0.0 if none); total_tokens summed.
    """
    # TODO(04-d)
    raise NotImplementedError


# ---------------------------------------------------------------- 04-e: regression check

def compare(baseline: Report, candidate: Report) -> dict:
    """{"regressions": [ids that passed before and fail now] (sorted),
        "fixes":       [ids that failed before and pass now] (sorted),
        "pass_rate_delta": candidate.pass_rate - baseline.pass_rate, rounded to 4 places}
    Only compare case ids present in both reports."""
    # TODO(04-e)
    raise NotImplementedError
