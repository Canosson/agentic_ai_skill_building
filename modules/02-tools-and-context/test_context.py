import copy

from lab.testing import load

c = load(__file__, "context")


def conversation(n_tool_rounds: int, payload: str = "data") -> list[dict]:
    msgs = [{"role": "user", "content": "original task"}]
    for i in range(n_tool_rounds):
        msgs.append({"role": "assistant", "content": [
            {"type": "tool_use", "id": f"t{i}", "name": "fetch", "input": {"i": i}}]})
        msgs.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "content": f"{payload}-{i}"}]})
    return msgs


def count_messages(msgs):  # a fake token counter: 1 "token" per message
    return len(msgs)


def assert_valid(msgs):
    assert msgs[0]["role"] == "user"
    for a, b in zip(msgs, msgs[1:]):
        assert a["role"] != b["role"], "roles must alternate"
    open_ids = set()
    for m in msgs:
        for blk in m["content"] if isinstance(m["content"], list) else []:
            if blk["type"] == "tool_use":
                open_ids.add(blk["id"])
            if blk["type"] == "tool_result":
                assert blk["tool_use_id"] in open_ids, "orphaned tool_result"


# ---------------------------------------------------------------- trim_history

def test_trim_noop_when_under_budget():
    msgs = conversation(2)
    assert c.trim_history(msgs, budget=100, count=count_messages) == msgs


def test_trim_keeps_first_message_and_most_recent_turns():
    msgs = conversation(5)  # 11 messages
    out = c.trim_history(msgs, budget=5, count=count_messages)
    assert len(out) <= 5
    assert out[0] == msgs[0]
    assert out[-1] == msgs[-1]
    assert_valid(out)


def test_trim_never_orphans_tool_results_for_any_budget():
    msgs = conversation(6)
    for budget in range(1, 15):
        assert_valid(c.trim_history(msgs, budget=budget, count=count_messages))


def test_trim_never_goes_below_three_messages():
    out = c.trim_history(conversation(4), budget=1, count=count_messages)
    assert len(out) == 3


def test_trim_does_not_mutate_input():
    msgs = conversation(5)
    before = copy.deepcopy(msgs)
    c.trim_history(msgs, budget=3, count=count_messages)
    assert msgs == before


def test_trim_with_default_estimator():
    msgs = conversation(20, payload="y" * 400)
    out = c.trim_history(msgs, budget=1000)
    assert c.estimate_tokens(out) <= 1000
    assert_valid(out)


# ---------------------------------------------------------------- compact_tool_results

def test_compact_shrinks_old_results_keeps_recent():
    msgs = conversation(4, payload="z" * 500)
    out = c.compact_tool_results(msgs, keep_last=2, max_chars=10)
    results = [m["content"][0]["content"] for m in out if m["role"] == "user" and isinstance(m["content"], list)]
    assert results[0].startswith("z" * 10 + "...[compacted, 502 chars originally]")
    assert results[1].startswith("z" * 10 + "...[compacted")
    assert results[2] == msgs[6]["content"][0]["content"]  # untouched
    assert results[3] == msgs[8]["content"][0]["content"]
    assert_valid(out)


def test_compact_leaves_short_results_and_input_alone():
    msgs = conversation(4)
    before = copy.deepcopy(msgs)
    assert c.compact_tool_results(msgs, keep_last=1, max_chars=200) == msgs
    assert msgs == before
