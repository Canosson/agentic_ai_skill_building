import threading
import time

import pytest

from lab.llm import FakeLLM, text
from lab.testing import load

g = load(__file__, "graphs")


# ---------------------------------------------------------------- chain

def test_chain_feeds_each_output_into_next_step():
    llm = FakeLLM([text("outline"), text("draft"), text("final")])
    graph = g.build_chain_graph(llm, [("Outline it.", None), ("Draft it.", None), ("Polish it.", None)])
    out = graph.invoke({"current": "topic", "outputs": [], "error": None})
    assert out["outputs"] == ["outline", "draft", "final"]
    assert out["error"] is None
    assert [r["system"] for r in llm.requests] == ["Outline it.", "Draft it.", "Polish it."]
    assert [r["messages"][0]["content"] for r in llm.requests] == ["topic", "outline", "draft"]


def test_chain_gate_stops_the_graph_and_saves_cost():
    llm = FakeLLM([text("too short"), text("never reached")])
    graph = g.build_chain_graph(llm, [("Step A", lambda s: len(s) > 50), ("Step B", None)])
    out = graph.invoke({"current": "x", "outputs": [], "error": None})
    assert "step 0" in out["error"]
    assert out["outputs"] == ["too short"]
    assert llm.calls == 1


def test_chain_graph_has_one_node_per_step():
    graph = g.build_chain_graph(FakeLLM(), [("A", None), ("B", None)])
    nodes = set(graph.get_graph().nodes)
    assert {"step_0", "step_1"} <= nodes


# ---------------------------------------------------------------- router

HANDLERS = {"billing": lambda q: f"billing:{q}", "technical": lambda q: f"tech:{q}", "general": lambda q: f"gen:{q}"}


@pytest.mark.parametrize("label, expected", [
    ("billing", "billing"), (" Technical.\n", "technical"), ("`BILLING`", "billing"), ("refunds", "general"),
])
def test_router_graph(label, expected):
    llm = FakeLLM([text(label)])
    graph = g.build_router_graph(llm, HANDLERS, fallback="general")
    out = graph.invoke({"query": "my card was charged twice"})
    assert out["category"] == expected
    assert out["answer"] == HANDLERS[expected]("my card was charged twice")
    assert llm.requests[0]["system"] == g.ROUTER_SYSTEM
    assert llm.calls == 1


def test_router_only_runs_the_chosen_handler():
    ran = []
    handlers = {
        "a": lambda q: ran.append("a") or "A",
        "b": lambda q: ran.append("b") or "B",
    }
    g.build_router_graph(FakeLLM([text("b")]), handlers, fallback="a").invoke({"query": "q"})
    assert ran == ["b"]


def test_router_handler_named_like_a_state_key_still_works():
    handlers = {"answer": lambda q: "x", "query": lambda q: "y"}
    out = g.build_router_graph(FakeLLM([text("answer")]), handlers, fallback="query").invoke({"query": "q"})
    assert out["answer"] == "x"


# ---------------------------------------------------------------- orchestrator

def run_orchestrator(llm, worker, **kw):
    return g.build_orchestrator_graph(llm, worker, **kw).invoke({"task": "compare A and B"})


def test_orchestrator_plans_fans_out_and_synthesises():
    llm = FakeLLM([text('Plan:\n["research A", "research B"]'), text("combined answer")])
    out = run_orchestrator(llm, lambda s: f"done({s})")
    assert out["subtasks"] == ["research A", "research B"]
    assert out["final"] == "combined answer"
    synth_prompt = llm.requests[1]["messages"][0]["content"]
    assert "compare A and B" in synth_prompt and "done(research B)" in synth_prompt
    assert llm.requests[1]["system"] == g.SYNTH_SYSTEM


def test_orchestrator_synthesiser_sees_results_in_subtask_order():
    def worker(s):
        time.sleep(0.05 if s == "a" else 0.0)  # "a" finishes last
        return s.upper()

    llm = FakeLLM([text('["a", "b", "c"]'), text("ok")])
    run_orchestrator(llm, worker)
    prompt = llm.requests[1]["messages"][0]["content"]
    assert prompt.index("A") < prompt.index("B") < prompt.rindex("C")
    assert prompt.index("Subtask 1: a\nA") >= 0


def test_orchestrator_runs_workers_in_parallel():
    running, peak, lock = 0, 0, threading.Lock()

    def worker(s):
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.05)
        with lock:
            running -= 1
        return s

    run_orchestrator(FakeLLM([text('["a", "b", "c"]'), text("ok")]), worker)
    assert peak >= 2, "workers ran one at a time"


def test_orchestrator_caps_subtasks():
    llm = FakeLLM([text('["1","2","3","4","5","6","7"]'), text("ok")])
    out = run_orchestrator(llm, str, max_subtasks=3)
    assert len(out["subtasks"]) == 3 and len(out["results"]) == 3


def test_orchestrator_survives_a_failing_worker():
    def worker(s):
        if s == "bad":
            raise RuntimeError("rate limited")
        return "fine"

    out = run_orchestrator(FakeLLM([text('["good", "bad"]'), text("partial answer")]), worker)
    assert sorted(out["results"]) == [(0, "fine"), (1, "[worker failed: RuntimeError: rate limited]")]
    assert out["errors"] == ["bad: rate limited"]
    assert out["final"] == "partial answer"


@pytest.mark.parametrize("plan", ['{"tasks": ["a"]}', "[]", "[1, 2]", "no json here"])
def test_orchestrator_rejects_bad_plans(plan):
    with pytest.raises(ValueError):
        run_orchestrator(FakeLLM([text(plan)]), str)


# ---------------------------------------------------------------- refine

def run_refine(llm, **kw):
    rounds = kw.pop("max_rounds", 3)
    graph = g.build_refine_graph(llm, max_rounds=rounds)
    return graph.invoke({"task": "write a haiku", "criteria": "5-7-5 syllables"}, **kw)


def test_refine_approved_first_round():
    llm = FakeLLM([text("draft 1"), text('{"approved": true, "feedback": ""}')])
    out = run_refine(llm)
    assert (out["draft"], out["round"], out["approved"]) == ("draft 1", 1, True)
    assert llm.calls == 2
    assert llm.requests[1]["system"] == g.CRITIC_SYSTEM
    assert "5-7-5" in llm.requests[1]["messages"][0]["content"]


def test_refine_revises_with_feedback_until_approved():
    llm = FakeLLM([
        text("draft 1"), text('{"approved": false, "feedback": "too long"}'),
        text("draft 2"), text('{"approved": true, "feedback": "good"}'),
    ])
    out = run_refine(llm)
    assert (out["draft"], out["round"], out["approved"]) == ("draft 2", 2, True)
    revise_prompt = llm.requests[2]["messages"][0]["content"]
    assert "too long" in revise_prompt and "draft 1" in revise_prompt
    assert out["history"] == [("draft 1", "too long"), ("draft 2", "good")]


def test_refine_gives_up_after_max_rounds_without_a_wasted_revision():
    no = text('{"approved": false, "feedback": "meh"}')
    llm = FakeLLM([text("d1"), no, text("d2"), no])
    out = run_refine(llm, max_rounds=2)
    assert (out["draft"], out["round"], out["approved"]) == ("d2", 2, False)
    assert llm.calls == 4


def test_refine_unreadable_critic_is_not_approval():
    llm = FakeLLM([text("d1"), text("Looks great to me!")])
    assert run_refine(llm, max_rounds=1)["approved"] is False


def test_refine_graph_draws_the_loop():
    """The point of a graph: the cycle is data you can inspect, not a hidden while-loop."""
    edges = {(e.source, e.target) for e in g.build_refine_graph(FakeLLM()).get_graph().edges}
    assert ("revise", "critique") in edges and ("critique", "revise") in edges
