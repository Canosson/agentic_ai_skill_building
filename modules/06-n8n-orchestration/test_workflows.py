import copy
import json

import pytest

from lab.testing import load

w = load(__file__, "workflows")


def wf_of(*nodes, edges=(), settings=None):
    wf = w.empty_workflow("t")
    wf = {**wf, "settings": settings if settings is not None else {"errorWorkflow": "err"}}
    for n in nodes:
        wf = w.add_node(wf, n)
    for e in edges:
        wf = w.connect(wf, *e)
    return wf


def trigger(name="In"):
    return w.make_node(name, "n8n-nodes-base.webhook")


def write(name, **kw):
    return w.make_node(name, w.HTTP_TYPE, {"method": "POST"}, **({"onError": "continueErrorOutput"} | kw))


def agent(name="Agent"):
    return w.make_node(name, w.AGENT_TYPE)


def gate(name="Approve"):
    return w.make_node(name, w.GATE_TYPE)


# ---------------------------------------------------------------- 06-a builders

def test_make_node_has_the_fields_n8n_expects():
    n = w.make_node("Fetch", w.HTTP_TYPE, {"url": "x"}, (10, 20), onError="continueErrorOutput")
    assert n["name"] == "Fetch" and n["type"] == w.HTTP_TYPE
    assert n["position"] == [10, 20] and n["parameters"] == {"url": "x"}
    assert isinstance(n["typeVersion"], (int, float)) and n["id"]
    assert n["onError"] == "continueErrorOutput"


def test_node_ids_are_stable_so_diffs_stay_small():
    assert w.make_node("A", "t")["id"] == w.make_node("A", "t")["id"]
    assert w.make_node("A", "t")["id"] != w.make_node("B", "t")["id"]


def test_add_node_does_not_mutate_and_rejects_duplicates():
    base = w.empty_workflow("t")
    snapshot = copy.deepcopy(base)
    new = w.add_node(base, trigger())
    assert base == snapshot and len(new["nodes"]) == 1
    with pytest.raises(ValueError):
        w.add_node(new, trigger())


def test_connect_builds_n8n_connection_structure():
    wf = wf_of(trigger(), agent(), edges=[("In", "Agent")])
    assert wf["connections"] == {"In": {"main": [[{"node": "Agent", "type": "main", "index": 0}]]}}


def test_connect_pads_outputs_and_supports_fan_out():
    wf = wf_of(trigger(), agent("A"), agent("B"), agent("C"),
               edges=[("In", "A", 2), ("In", "B", 2), ("In", "C", 0)])
    main = wf["connections"]["In"]["main"]
    assert [[l["node"] for l in out] for out in main] == [["C"], [], ["A", "B"]]


def test_connect_does_not_mutate_and_checks_names():
    base = wf_of(trigger(), agent())
    snapshot = copy.deepcopy(base)
    w.connect(base, "In", "Agent")
    assert base == snapshot
    with pytest.raises(ValueError):
        w.connect(base, "In", "Nope")
    with pytest.raises(ValueError):
        w.connect(base, "Nope", "Agent")


# ---------------------------------------------------------------- 06-b paths

def test_paths_follow_every_branch_to_a_leaf():
    wf = wf_of(trigger(), agent("A"), agent("B"), agent("C"),
               edges=[("In", "A"), ("A", "B"), ("A", "C")])
    assert sorted(w.paths(wf)) == [["In", "A", "B"], ["In", "A", "C"]]


def test_paths_reject_cycles():
    wf = wf_of(trigger(), agent("A"), agent("B"), edges=[("In", "A"), ("A", "B"), ("B", "A")])
    with pytest.raises(ValueError, match="cycle"):
        w.paths(wf)


def test_llm_calls_counts_agent_and_classifier_nodes_only():
    wf = wf_of(trigger(), w.make_node("Cls", "@n8n/n8n-nodes-langchain.textClassifier"), agent(), write("W"),
               edges=[("In", "Cls"), ("Cls", "Agent"), ("Agent", "W")])
    assert w.llm_calls(wf, ["In", "Cls", "Agent", "W"]) == 2
    assert w.llm_calls(wf, ["In", "W"]) == 0


# ---------------------------------------------------------------- 06-c validate

def test_a_sound_workflow_has_no_problems():
    wf = wf_of(trigger(), write("Send"), edges=[("In", "Send")])
    assert w.validate(wf) == []


def test_flags_missing_trigger():
    assert any("no trigger" in p for p in w.validate(wf_of(agent())))


def test_flags_dangling_connections():
    wf = wf_of(trigger(), agent())
    wf = {**wf, "connections": {"In": {"main": [[{"node": "Ghost", "type": "main", "index": 0}]]}}}
    assert any("dangling connection" in p and "Ghost" in p for p in w.validate(wf))


def test_flags_unreachable_nodes():
    wf = wf_of(trigger(), agent("Orphan"))
    assert "unreachable node: Orphan" in w.validate(wf)


def test_flags_missing_error_workflow():
    wf = wf_of(trigger(), settings={})
    assert "missing errorWorkflow" in w.validate(wf)


def test_flags_write_nodes_whose_failure_goes_nowhere():
    wf = wf_of(trigger(), w.make_node("Send", w.HTTP_TYPE, {"method": "POST"}), edges=[("In", "Send")])
    assert "unhandled write failure: Send" in w.validate(wf)


def test_reads_do_not_need_error_branches():
    wf = wf_of(trigger(), w.make_node("Get", w.HTTP_TYPE, {"method": "GET"}), edges=[("In", "Get")])
    assert w.validate(wf) == []


def test_flags_switch_without_fallback():
    sw = w.make_node("Route", w.SWITCH_TYPE, {"options": {}})
    assert "switch without fallback: Route" in w.validate(wf_of(trigger(), sw, edges=[("In", "Route")]))


def test_flags_agent_output_reaching_a_write_without_a_gate():
    wf = wf_of(trigger(), agent(), write("Send"), edges=[("In", "Agent"), ("Agent", "Send")])
    assert "ungated write: Agent -> Send" in w.validate(wf)


def test_a_wait_node_gates_the_write():
    wf = wf_of(trigger(), agent(), gate(), write("Send"),
               edges=[("In", "Agent"), ("Agent", "Approve"), ("Approve", "Send")])
    assert w.validate(wf) == []


def test_a_write_far_downstream_of_an_agent_is_still_ungated():
    wf = wf_of(trigger(), agent(), w.make_node("Fmt", "n8n-nodes-base.set"), write("Send"),
               edges=[("In", "Agent"), ("Agent", "Fmt"), ("Fmt", "Send")])
    assert "ungated write: Agent -> Send" in w.validate(wf)


def test_the_gate_only_protects_its_own_branch():
    wf = wf_of(trigger(), agent(), gate(), write("Safe"), write("Risky"),
               edges=[("In", "Agent"), ("Agent", "Approve"), ("Approve", "Safe"), ("Agent", "Risky")])
    assert w.validate(wf) == ["ungated write: Agent -> Risky"]


def test_cycles_are_reported_not_raised():
    wf = wf_of(trigger(), agent("A"), edges=[("In", "A"), ("A", "A")])
    assert any("cycle" in p for p in w.validate(wf))


# ---------------------------------------------------------------- 06-d the design

@pytest.fixture(scope="module")
def router():
    return w.ticket_router_workflow()


def test_router_passes_your_own_linter(router):
    assert w.validate(router) == []


def test_router_is_valid_json_you_could_import(router):
    assert json.loads(json.dumps(router)) == router
    assert {"name", "nodes", "connections", "settings"} <= set(router)


def test_router_has_one_entry_point_and_a_fallback_route(router):
    triggers = [n for n in router["nodes"] if n["type"] in w.TRIGGER_TYPES]
    assert len(triggers) == 1
    route = next(n for n in router["nodes"] if n["type"] == w.SWITCH_TYPE)
    assert route["parameters"]["options"]["fallbackOutput"] == "extra"
    assert len(router["connections"][route["name"]]["main"]) == 4  # 3 categories + fallback


def test_refunds_are_deterministic_code_with_exactly_one_model_call(router):
    """Module 05's lesson: sending a refund to plain code beats any agent."""
    types = {n["name"]: n["type"] for n in router["nodes"]}
    refund_paths = [p for p in w.paths(router) if "Issue refund" in p]
    assert refund_paths
    for p in refund_paths:
        assert w.AGENT_TYPE not in [types[n] for n in p]
        assert w.llm_calls(router, p) == 1  # only the classifier


def test_every_agent_path_goes_through_a_human_gate(router):
    types = {n["name"]: n["type"] for n in router["nodes"]}
    agent_paths = [p for p in w.paths(router) if any(types[n] == w.AGENT_TYPE for n in p)]
    assert agent_paths
    for p in agent_paths:
        assert any(types[n] == w.GATE_TYPE for n in p)


def test_unknown_tickets_land_with_a_human(router):
    route = next(n for n in router["nodes"] if n["type"] == w.SWITCH_TYPE)["name"]
    fallback_targets = [l["node"] for l in router["connections"][route]["main"][-1]]
    assert fallback_targets == ["Human queue"]
