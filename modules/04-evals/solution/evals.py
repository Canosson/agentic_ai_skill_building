"""Reference solution: a small, honest eval harness."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from lab.llm import LLM


@dataclass
class Case:
    id: str
    input: str
    expect: dict


@dataclass
class Trial:
    output: str
    tool_calls: list[str] = field(default_factory=list)
    turns: int = 1
    tokens: int = 0


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    checks: dict[str, bool]
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


# ---------------------------------------------------------------- checks

def _as_list(x) -> list[str]:
    return [x] if isinstance(x, str) else list(x)


def check_contains(trial: Trial, expected: str | list[str]) -> bool:
    out = trial.output.lower().replace(",", "")
    return all(e.lower().replace(",", "") in out for e in _as_list(expected))


def check_not_contains(trial: Trial, forbidden: str | list[str]) -> bool:
    out = trial.output.lower()
    return not any(f.lower() in out for f in _as_list(forbidden))


def check_tool_called(trial: Trial, name: str) -> bool:
    return name in trial.tool_calls


def check_max_turns(trial: Trial, n: int) -> bool:
    return trial.turns <= n


JUDGE_SYSTEM = (
    "You are a strict evaluator. Given a question, an answer and a rubric, decide whether the "
    'answer satisfies the rubric. Reply with ONLY a JSON object: {"pass": true|false, "reason": "<one sentence>"}'
)


def llm_judge(llm: LLM, question: str, answer: str, rubric: str) -> tuple[bool, str]:
    prompt = f"<question>\n{question}\n</question>\n<answer>\n{answer}\n</answer>\n<rubric>\n{rubric}\n</rubric>"
    resp = llm.complete(system=JUDGE_SYSTEM, messages=[{"role": "user", "content": prompt}], max_tokens=300)
    m = re.search(r"\{.*\}", resp.text, re.DOTALL)
    try:
        verdict = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        verdict = None
    if not isinstance(verdict, dict) or not isinstance(verdict.get("pass"), bool):
        return False, f"judge output unparseable: {resp.text[:200]!r}"
    return verdict["pass"], str(verdict.get("reason", ""))


CHECKS: dict[str, Callable[[Trial, object], bool]] = {
    "contains": check_contains,
    "not_contains": check_not_contains,
    "tool_called": check_tool_called,
    "max_turns": check_max_turns,
}


def grade(case: Case, trial: Trial, judge_llm: LLM | None = None) -> tuple[dict[str, bool], list[str]]:
    checks, notes = {}, []
    for key, value in case.expect.items():
        if key == "rubric":
            if judge_llm is None:
                raise ValueError(f"case {case.id} has a rubric but no judge_llm was given")
            ok, reason = llm_judge(judge_llm, case.input, trial.output, value)
            checks["rubric"] = ok
            notes.append(f"judge: {reason}")
        elif key in CHECKS:
            checks[key] = CHECKS[key](trial, value)
        else:
            raise ValueError(f"case {case.id}: unknown expectation {key!r}")
    return checks, notes


def run_eval(agent_fn: Callable[[str], Trial], cases: list[Case], judge_llm: LLM | None = None,
             trials: int = 1) -> Report:
    results, turns, tokens = [], [], 0
    for case in cases:
        passed_trials, first_fail, checks, notes = 0, None, {}, []
        for _ in range(trials):
            try:
                trial = agent_fn(case.input)
            except Exception as e:  # a crash is a failed trial, not a crashed eval
                checks = {"no_crash": False}
                notes.append(f"agent crashed: {type(e).__name__}: {e}")
            else:
                turns.append(trial.turns)
                tokens += trial.tokens
                checks, n = grade(case, trial, judge_llm)
                notes.extend(n)
            if all(checks.values()):
                passed_trials += 1
            elif first_fail is None:
                first_fail = checks
        shown = first_fail if first_fail is not None else checks
        results.append(CaseResult(case.id, passed_trials == trials, shown, passed_trials, trials, notes))
    return Report(results, sum(turns) / len(turns) if turns else 0.0, tokens)


def compare(baseline: Report, candidate: Report) -> dict:
    before = {r.case_id: r.passed for r in baseline.results}
    after = {r.case_id: r.passed for r in candidate.results}
    common = before.keys() & after.keys()
    return {
        "regressions": sorted(c for c in common if before[c] and not after[c]),
        "fixes": sorted(c for c in common if not before[c] and after[c]),
        "pass_rate_delta": round(candidate.pass_rate - baseline.pass_rate, 4),
    }
