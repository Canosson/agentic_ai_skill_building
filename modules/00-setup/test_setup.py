"""Offline checks that the lab harness works. No API key needed."""

import pytest

from lab.llm import FakeLLM, text, tool_call


def test_fake_llm_replays_script_and_records_requests():
    llm = FakeLLM([tool_call("clock"), text("It is noon.")])
    first = llm.complete(system="s", messages=[{"role": "user", "content": "time?"}])
    assert first.stop_reason == "tool_use"
    assert first.tool_calls[0]["name"] == "clock"
    second = llm.complete(system="s", messages=[])
    assert second.text == "It is noon."
    assert llm.calls == 2
    assert llm.requests[0]["messages"][0]["content"] == "time?"


def test_fake_llm_complains_when_called_too_often():
    llm = FakeLLM([text("only one")])
    llm.complete(system="", messages=[])
    with pytest.raises(AssertionError, match="ran out"):
        llm.complete(system="", messages=[])


def test_sdk_installed():
    import anthropic  # noqa: F401
    import mcp  # noqa: F401
