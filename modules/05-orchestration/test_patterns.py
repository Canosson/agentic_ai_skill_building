import threading
import time

import pytest

from lab.llm import FakeLLM, text
from lab.testing import load

p = load(__file__, "patterns")


# ---------------------------------------------------------------- chain

def test_chain_feeds_each_output_into_next_step():
    llm = FakeLLM([text("outline"), text("draft"), text("final")])
    out = p.chain(llm, [("Outline it.", None), ("Draft it.", None), ("Polish it.", None)], "topic")
    assert out == ["outline", "draft", "final"]
    assert [r["system"] for r in llm.requests] == ["Outline it.", "Draft it.", "Polish it."]
    assert [r["messages"][0]["content"] for r in llm.requests] == ["topic", "outline", "draft"]


def test_chain_gate_stops_early_and_saves_cost():
    llm = FakeLLM([text("too short"), text("never reached")])
    with pytest.raises(ValueError, match="0"):
        p.chain(llm, [("Step A", lambda s: len(s) > 50), ("Step B", None)], "x")
    assert llm.calls == 1


# ---------------------------------------------------------------- route

HANDLERS = {"billing": lambda q: f"billing:{q}", "technical": lambda q: f"tech:{q}", "general": lambda q: f"gen:{q}"}


@pytest.mark.parametrize("label, expected", [
    ("billing", "billing"), (" Technical.\n", "technical"), ("`BILLING`", "billing"), ("refunds", "general"),
])
def test_route(label, expected):
    llm = FakeLLM([text(label)])
    chosen, out = p.route(llm, "my card was charged twice", HANDLERS, fallback="general")
    assert chosen == expected
    assert out == HANDLERS[expected]("my card was charged twice")
    prompt = llm.requests[0]["messages"][0]["content"]
    assert all(name in prompt for name in HANDLERS) and "charged twice" in prompt
    assert llm.requests[0]["system"] == p.ROUTER_SYSTEM
    assert llm.calls == 1


# ---------------------------------------------------------------- orchestrate

def test_orchestrate_plans_runs_workers_and_synthesises():
    llm = FakeLLM([text('Plan:\n["research A", "research B"]'), text("combined answer")])
    r = p.orchestrate(llm, "compare A and B", worker=lambda s: f"done({s})")
    assert r.subtasks == ["research A", "research B"]
    assert r.worker_outputs == ["done(research A)", "done(research B)"]
    assert r.final == "combined answer"
    synth_prompt = llm.requests[1]["messages"][0]["content"]
    assert "compare A and B" in synth_prompt and "done(research B)" in synth_prompt
    assert llm.requests[1]["system"] == p.SYNTH_SYSTEM


def test_orchestrate_runs_workers_in_parallel_and_keeps_order():
    running, peak, lock = 0, 0, threading.Lock()

    def worker(s):
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.05 if s == "a" else 0.01)
        with lock:
            running -= 1
        return s.upper()

    llm = FakeLLM([text('["a", "b", "c"]'), text("ok")])
    r = p.orchestrate(llm, "t", worker, max_workers=3)
    assert peak >= 2, "workers ran one at a time"
    assert r.worker_outputs == ["A", "B", "C"]


def test_orchestrate_caps_subtasks():
    llm = FakeLLM([text('["1","2","3","4","5","6","7"]'), text("ok")])
    assert len(p.orchestrate(llm, "t", str, max_subtasks=3).subtasks) == 3


def test_orchestrate_survives_a_failing_worker():
    def worker(s):
        if s == "bad":
            raise RuntimeError("rate limited")
        return "fine"

    llm = FakeLLM([text('["good", "bad"]'), text("partial answer")])
    r = p.orchestrate(llm, "t", worker)
    assert r.worker_outputs[0] == "fine"
    assert r.worker_outputs[1] == "[worker failed: RuntimeError: rate limited]"
    assert r.errors == ["bad: rate limited"]
    assert r.final == "partial answer"


@pytest.mark.parametrize("plan", ['{"tasks": ["a"]}', "[]", "[1, 2]", "no json here"])
def test_orchestrate_rejects_bad_plans(plan):
    with pytest.raises(ValueError):
        p.orchestrate(FakeLLM([text(plan)]), "t", str)


# ---------------------------------------------------------------- evaluate_optimize

def test_refine_approved_first_round():
    llm = FakeLLM([text("draft 1"), text('{"approved": true, "feedback": ""}')])
    r = p.evaluate_optimize(llm, "write a haiku", "5-7-5 syllables")
    assert (r.final, r.rounds, r.approved) == ("draft 1", 1, True)
    assert llm.calls == 2
    assert llm.requests[1]["system"] == p.CRITIC_SYSTEM
    assert "5-7-5" in llm.requests[1]["messages"][0]["content"]


def test_refine_revises_with_feedback_until_approved():
    llm = FakeLLM([
        text("draft 1"), text('{"approved": false, "feedback": "too long"}'),
        text("draft 2"), text('{"approved": true, "feedback": "good"}'),
    ])
    r = p.evaluate_optimize(llm, "task", "criteria")
    assert (r.final, r.rounds, r.approved) == ("draft 2", 2, True)
    revise_prompt = llm.requests[2]["messages"][0]["content"]
    assert "too long" in revise_prompt and "draft 1" in revise_prompt
    assert r.history == [("draft 1", "too long"), ("draft 2", "good")]


def test_refine_gives_up_after_max_rounds_without_a_wasted_revision():
    no = text('{"approved": false, "feedback": "meh"}')
    llm = FakeLLM([text("d1"), no, text("d2"), no])
    r = p.evaluate_optimize(llm, "task", "criteria", max_rounds=2)
    assert (r.final, r.rounds, r.approved) == ("d2", 2, False)
    assert llm.calls == 4


def test_refine_unreadable_critic_is_not_approval():
    llm = FakeLLM([text("d1"), text("Looks great to me!")])
    r = p.evaluate_optimize(llm, "task", "criteria", max_rounds=1)
    assert r.approved is False
