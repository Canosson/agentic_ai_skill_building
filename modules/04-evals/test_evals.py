from pathlib import Path

import pytest

from lab.llm import FakeLLM, text
from lab.testing import load

ev = load(__file__, "evals")
T = ev.Trial


# ---------------------------------------------------------------- 04-a

def test_check_contains():
    t = T("The answer is 7,006,652.")
    assert ev.check_contains(t, "7006652")
    assert ev.check_contains(t, ["answer", "7006652"])
    assert not ev.check_contains(t, ["answer", "42"])
    assert ev.check_contains(T("HELLO"), "hello")


def test_check_not_contains():
    assert ev.check_not_contains(T("It is 81."), ["82", "eighty-two"])
    assert not ev.check_not_contains(T("Sure, 82!"), "82")


def test_check_tool_called_and_turns():
    t = T("x", tool_calls=["calculator", "today"], turns=3)
    assert ev.check_tool_called(t, "today")
    assert not ev.check_tool_called(t, "weather")
    assert ev.check_max_turns(t, 3)
    assert not ev.check_max_turns(t, 2)


# ---------------------------------------------------------------- 04-b

def test_judge_parses_json_and_sends_everything():
    judge = FakeLLM([text('{"pass": true, "reason": "correct"}')])
    assert ev.llm_judge(judge, "Q?", "A.", "Must be A") == (True, "correct")
    sent = judge.requests[0]
    assert sent["system"] == ev.JUDGE_SYSTEM
    body = sent["messages"][0]["content"]
    assert "Q?" in body and "A." in body and "Must be A" in body


def test_judge_handles_fenced_json_with_prose():
    judge = FakeLLM([text('Here is my verdict:\n```json\n{"pass": false, "reason": "made up a number"}\n```')])
    assert ev.llm_judge(judge, "q", "a", "r") == (False, "made up a number")


@pytest.mark.parametrize("raw", ["I think it passes!", '{"pass": "yes"}', "{not json}", ""])
def test_judge_fails_closed(raw):
    ok, reason = ev.llm_judge(FakeLLM([text(raw)]), "q", "a", "r")
    assert ok is False and "unparseable" in reason


# ---------------------------------------------------------------- 04-c

def test_grade_runs_each_expectation():
    case = ev.Case("c1", "17*23?", {"contains": "391", "tool_called": "calculator", "max_turns": 2})
    checks, _ = ev.grade(case, T("391", ["calculator"], turns=3))
    assert checks == {"contains": True, "tool_called": True, "max_turns": False}


def test_grade_rubric_uses_judge_and_records_reason():
    case = ev.Case("c2", "weather?", {"rubric": "admits it cannot know"})
    checks, notes = ev.grade(case, T("I can't check live weather."), FakeLLM([text('{"pass": true, "reason": "honest"}')]))
    assert checks == {"rubric": True}
    assert notes == ["judge: honest"]


def test_grade_rubric_without_judge_raises():
    with pytest.raises(ValueError):
        ev.grade(ev.Case("c", "q", {"rubric": "x"}), T("a"))


def test_grade_unknown_expectation_raises():
    with pytest.raises(ValueError, match="contians"):
        ev.grade(ev.Case("c", "q", {"contians": "typo"}), T("a"))


# ---------------------------------------------------------------- 04-d

CASES = [
    ev.Case("math", "2+2", {"contains": "4"}),
    ev.Case("hello", "hi", {"contains": "hello"}),
]


def test_run_eval_basic_report():
    def agent(q):
        return T("4" if q == "2+2" else "go away", turns=2, tokens=10)

    r = ev.run_eval(agent, CASES)
    assert [x.passed for x in r.results] == [True, False]
    assert r.pass_rate == 0.5
    assert r.mean_turns == 2
    assert r.total_tokens == 20
    assert [f.case_id for f in r.failures()] == ["hello"]


def test_run_eval_requires_all_trials_to_pass():
    outputs = iter(["4", "5", "4"])
    r = ev.run_eval(lambda q: T(next(outputs)), CASES[:1], trials=3)
    res = r.results[0]
    assert res.passed is False
    assert res.trials_passed == 2 and res.trials == 3
    assert res.checks == {"contains": False}  # from the failing trial


def test_run_eval_survives_a_crashing_agent():
    def agent(q):
        if q == "hi":
            raise TimeoutError("api down")
        return T("4")

    r = ev.run_eval(agent, CASES)
    crashed = r.results[1]
    assert crashed.passed is False
    assert crashed.checks == {"no_crash": False}
    assert any(n.startswith("agent crashed:") for n in crashed.notes)
    assert r.mean_turns == 1


# ---------------------------------------------------------------- 04-e

def _report(passes: dict) -> "ev.Report":
    return ev.Report([ev.CaseResult(k, v, {}, int(v), 1) for k, v in passes.items()], 1.0, 0)


def test_compare_finds_regressions_and_fixes():
    base = _report({"a": True, "b": False, "c": True, "old": True})
    cand = _report({"a": True, "b": True, "c": False, "new": False})
    assert ev.compare(base, cand) == {"regressions": ["c"], "fixes": ["b"], "pass_rate_delta": -0.25}


# ---------------------------------------------------------------- dataset sanity (given)

def test_dataset_is_valid():
    cases = ev.load_cases(Path(__file__).parent / "cases.jsonl")
    assert len(cases) >= 10
    assert len({c.id for c in cases}) == len(cases), "duplicate ids"
    allowed = {"contains", "not_contains", "tool_called", "max_turns", "rubric"}
    for c in cases:
        assert c.expect and set(c.expect) <= allowed, c.id
