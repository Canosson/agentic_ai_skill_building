import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from lab.llm import FakeLLM, text
from lab.testing import load

d = load(__file__, "durable")


# ---------------------------------------------------------------- human approval

@pytest.fixture
def approval():
    sent: list[str] = []
    llm = FakeLLM([text("Sorry about the double charge, refunding now.")])
    graph = d.build_approval_graph(llm, sent.append, InMemorySaver())
    return graph, llm, sent


def test_graph_pauses_for_review_and_does_not_send(approval):
    graph, llm, sent = approval
    result = graph.invoke({"ticket": "charged twice"}, d.thread("t1"))
    assert sent == []
    interrupts = result["__interrupt__"]
    assert interrupts[0].value == {"draft": "Sorry about the double charge, refunding now."}
    assert graph.get_state(d.thread("t1")).next == ("review",)


def test_approval_sends_the_draft(approval):
    graph, llm, sent = approval
    graph.invoke({"ticket": "charged twice"}, d.thread("t1"))
    out = graph.invoke(Command(resume={"approved": True}), d.thread("t1"))
    assert sent == ["Sorry about the double charge, refunding now."]
    assert out["outcome"] == "sent"


def test_human_edit_wins_over_the_draft(approval):
    graph, llm, sent = approval
    graph.invoke({"ticket": "charged twice"}, d.thread("t1"))
    graph.invoke(Command(resume={"approved": True, "edited": "Hi, refund issued."}), d.thread("t1"))
    assert sent == ["Hi, refund issued."]


def test_rejection_sends_nothing(approval):
    graph, llm, sent = approval
    graph.invoke({"ticket": "charged twice"}, d.thread("t1"))
    out = graph.invoke(Command(resume={"approved": False}), d.thread("t1"))
    assert sent == []
    assert out["outcome"] == "rejected"


@pytest.mark.parametrize("decision", [{}, {"approved": "yes"}, {"approved": None}])
def test_anything_but_an_explicit_true_is_a_rejection(approval, decision):
    graph, llm, sent = approval
    graph.invoke({"ticket": "x"}, d.thread("t1"))
    graph.invoke(Command(resume=decision), d.thread("t1"))
    assert sent == []


def test_resuming_does_not_call_the_model_again(approval):
    """The node containing interrupt() restarts on resume. The model call must live in its own node."""
    graph, llm, sent = approval
    graph.invoke({"ticket": "x"}, d.thread("t1"))
    graph.invoke(Command(resume={"approved": True}), d.thread("t1"))
    assert llm.calls == 1


def test_threads_are_independent():
    sent: list[str] = []
    llm = FakeLLM([text("reply A"), text("reply B")])
    graph = d.build_approval_graph(llm, sent.append, InMemorySaver())
    graph.invoke({"ticket": "a"}, d.thread("A"))
    graph.invoke({"ticket": "b"}, d.thread("B"))
    graph.invoke(Command(resume={"approved": True}), d.thread("B"))
    assert sent == ["reply B"]
    assert graph.get_state(d.thread("A")).next == ("review",)


# ---------------------------------------------------------------- crash recovery

def make_flaky(fail_times: int, exc=RuntimeError):
    state = {"calls": 0}

    def flaky(v):
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc("upstream 503")
        return v + "-flaky"

    return flaky, state


def test_resume_skips_steps_that_already_succeeded():
    runs = {"fetch": 0, "publish": 0}

    def fetch(v):
        runs["fetch"] += 1
        return v + "-fetched"

    def publish(v):
        runs["publish"] += 1
        return v + "-published"

    flaky, _ = make_flaky(1)
    graph = d.build_pipeline([("fetch", fetch), ("flaky", flaky), ("publish", publish)], InMemorySaver())
    out = d.run_with_resume(graph, {"value": "x"}, "t1")
    assert out["value"] == "x-fetched-flaky-published"
    assert runs == {"fetch": 1, "publish": 1}, "completed steps must not run again after a crash"


def test_failed_run_leaves_a_checkpoint_pointing_at_the_failed_step():
    flaky, _ = make_flaky(1)
    graph = d.build_pipeline([("a", lambda v: v + "a"), ("flaky", flaky)], InMemorySaver())
    with pytest.raises(RuntimeError):
        graph.invoke({"value": ""}, d.thread("t1"))
    snapshot = graph.get_state(d.thread("t1"))
    assert snapshot.next == ("flaky",)
    assert snapshot.values["value"] == "a"


def test_run_with_resume_gives_up_after_max_attempts():
    flaky, state = make_flaky(99)
    graph = d.build_pipeline([("flaky", flaky)], InMemorySaver())
    with pytest.raises(RuntimeError):
        d.run_with_resume(graph, {"value": ""}, "t1", max_attempts=3)
    assert state["calls"] == 3


def test_run_with_resume_does_not_retry_errors_it_was_not_told_to():
    flaky, state = make_flaky(99, exc=ValueError)
    graph = d.build_pipeline([("flaky", flaky)], InMemorySaver())
    with pytest.raises(ValueError):
        d.run_with_resume(graph, {"value": ""}, "t1", max_attempts=5, retry_on=(ConnectionError,))
    assert state["calls"] == 1


# ---------------------------------------------------------------- traceability

def test_trace_lists_nodes_in_order_and_flags_interrupts(approval):
    graph, llm, sent = approval
    first = d.trace_run(graph, {"ticket": "x"}, "t1")
    assert first.nodes == ["draft"]
    assert first.interrupted is True
    assert first.state["draft"].startswith("Sorry")

    second = d.trace_run(graph, Command(resume={"approved": True}), "t1")
    assert second.nodes == ["review", "send"]
    assert second.interrupted is False
    assert second.state["outcome"] == "sent"


def test_trace_of_a_rejected_run_never_visits_send(approval):
    graph, llm, sent = approval
    d.trace_run(graph, {"ticket": "x"}, "t1")
    trace = d.trace_run(graph, Command(resume={"approved": False}), "t1")
    assert "send" not in trace.nodes and trace.nodes[-1] == "reject"
