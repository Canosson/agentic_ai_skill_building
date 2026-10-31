"""Module 01 tests. Read each test name: together they are the spec for an agent loop."""

from lab.llm import FakeLLM, text, tool_call, tool_calls
from lab.testing import load

agent = load(__file__, "agent")

ADD_TOOL = {
    "name": "add",
    "description": "Add two integers.",
    "input_schema": {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    },
}
IMPLS = {"add": lambda a, b: a + b}


# ---------------------------------------------------------------- execute_tool


def test_execute_tool_returns_string_output_unchanged():
    assert agent.execute_tool("echo", {"s": "hi"}, {"echo": lambda s: s}) == ("hi", False)


def test_execute_tool_json_encodes_non_strings():
    content, is_error = agent.execute_tool("add", {"a": 2, "b": 3}, IMPLS)
    assert (content, is_error) == ("5", False)
    content, _ = agent.execute_tool("info", {}, {"info": lambda: {"ok": True}})
    assert content == '{"ok": true}'


def test_execute_tool_unknown_tool_is_an_error_that_lists_available_tools():
    content, is_error = agent.execute_tool("subtract", {}, IMPLS)
    assert is_error is True
    assert "add" in content


def test_execute_tool_catches_exceptions_and_reports_them():
    def boom():
        raise ValueError("bad input")

    content, is_error = agent.execute_tool("boom", {}, {"boom": boom})
    assert is_error is True
    assert "ValueError" in content and "bad input" in content


# ---------------------------------------------------------------- run_agent


def test_no_tools_needed_one_call_returns_text():
    llm = FakeLLM([text("Hello!")])
    r = agent.run_agent(llm, "hi")
    assert r.final_text == "Hello!"
    assert r.turns == 1
    assert r.stopped_reason == "end_turn"
    assert llm.requests[0]["messages"] == [{"role": "user", "content": "hi"}]


def test_tools_are_passed_to_the_model():
    llm = FakeLLM([text("ok")])
    agent.run_agent(llm, "hi", [ADD_TOOL], IMPLS)
    assert llm.requests[0]["tools"] == [ADD_TOOL]


def test_single_tool_call_round_trip():
    llm = FakeLLM([tool_call("add", {"a": 2, "b": 3}, id="t1"), text("2 + 3 = 5")])
    r = agent.run_agent(llm, "what is 2+3?", [ADD_TOOL], IMPLS)

    assert r.final_text == "2 + 3 = 5"
    assert r.turns == 2
    assert r.tool_calls == [("add", {"a": 2, "b": 3})]

    second_request = llm.requests[1]["messages"]
    assert [m["role"] for m in second_request] == ["user", "assistant", "user"]
    assert second_request[1]["content"][0]["type"] == "tool_use"  # assistant turn kept verbatim
    assert second_request[2]["content"] == [{"type": "tool_result", "tool_use_id": "t1", "content": "5"}]


def test_parallel_tool_calls_all_results_in_one_user_message_in_order():
    llm = FakeLLM([
        tool_calls([("add", {"a": 1, "b": 1}, "x"), ("add", {"a": 2, "b": 2}, "y")]),
        text("2 and 4"),
    ])
    agent.run_agent(llm, "two sums", [ADD_TOOL], IMPLS)
    last = llm.requests[1]["messages"][-1]
    assert last["role"] == "user"
    assert [(b["tool_use_id"], b["content"]) for b in last["content"]] == [("x", "2"), ("y", "4")]


def test_tool_error_goes_back_to_model_flagged_and_loop_continues():
    def flaky(**_):
        raise TimeoutError("upstream timed out")

    llm = FakeLLM([tool_call("flaky", {}, id="f1"), text("Sorry, the service is down.")])
    r = agent.run_agent(llm, "go", [], {"flaky": flaky})
    result_block = llm.requests[1]["messages"][-1]["content"][0]
    assert result_block["tool_use_id"] == "f1"
    assert result_block["is_error"] is True
    assert "upstream timed out" in result_block["content"]
    assert r.final_text == "Sorry, the service is down."


def test_successful_tool_result_has_no_is_error_flag():
    llm = FakeLLM([tool_call("add", {"a": 1, "b": 2}), text("3")])
    agent.run_agent(llm, "go", [ADD_TOOL], IMPLS)
    assert "is_error" not in llm.requests[1]["messages"][-1]["content"][0]


def test_multi_step_chain():
    llm = FakeLLM([
        tool_call("add", {"a": 1, "b": 2}),
        tool_call("add", {"a": 3, "b": 4}),
        text("done"),
    ])
    r = agent.run_agent(llm, "chain", [ADD_TOOL], IMPLS)
    assert r.turns == 3
    assert len(r.tool_calls) == 2
    assert len(r.messages) == 6  # user, (assistant, user) x2, assistant


def test_max_turns_stops_a_runaway_agent():
    llm = FakeLLM(default=tool_call("add", {"a": 1, "b": 1}))
    r = agent.run_agent(llm, "loop forever", [ADD_TOOL], IMPLS, max_turns=3)
    assert llm.calls == 3
    assert r.stopped_reason == "max_turns"


def test_system_prompt_is_sent():
    llm = FakeLLM([text("ok")])
    agent.run_agent(llm, "hi", system="You are a pirate.")
    assert llm.requests[0]["system"] == "You are a pirate."
