"""Reference solution: n8n workflows as data, with an architecture linter."""

from __future__ import annotations

import uuid
from typing import Any

Workflow = dict[str, Any]
Node = dict[str, Any]

TRIGGER_TYPES = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.errorTrigger",
}
HTTP_TYPE = "n8n-nodes-base.httpRequest"
SWITCH_TYPE = "n8n-nodes-base.switch"
GATE_TYPE = "n8n-nodes-base.wait"
AGENT_TYPE = "@n8n/n8n-nodes-langchain.agent"
LLM_TYPES = {AGENT_TYPE, "@n8n/n8n-nodes-langchain.textClassifier"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def empty_workflow(name: str) -> Workflow:
    return {"name": name, "nodes": [], "connections": {}, "settings": {}}


def is_write(node: Node) -> bool:
    return node["type"] == HTTP_TYPE and str(node["parameters"].get("method", "GET")).upper() in WRITE_METHODS


def successors(workflow: Workflow, name: str) -> list[str]:
    outputs = workflow["connections"].get(name, {}).get("main", [])
    return [link["node"] for output in outputs for link in output]


# ---------------------------------------------------------------- 06-a builders

def make_node(name: str, type: str, parameters: dict | None = None, position: tuple[int, int] = (0, 0),
              **settings: Any) -> Node:
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, name)),
        "name": name,
        "type": type,
        "typeVersion": 1,
        "position": list(position),
        "parameters": dict(parameters or {}),
        **settings,
    }


def add_node(workflow: Workflow, node: Node) -> Workflow:
    if any(n["name"] == node["name"] for n in workflow["nodes"]):
        raise ValueError(f"duplicate node name: {node['name']!r}")
    return {**workflow, "nodes": [*workflow["nodes"], node]}


def connect(workflow: Workflow, src: str, dst: str, output: int = 0) -> Workflow:
    names = {n["name"] for n in workflow["nodes"]}
    for name in (src, dst):
        if name not in names:
            raise ValueError(f"unknown node: {name!r}")
    outputs = [list(o) for o in workflow["connections"].get(src, {}).get("main", [])]
    while len(outputs) <= output:
        outputs.append([])
    outputs[output].append({"node": dst, "type": "main", "index": 0})
    connections = {**workflow["connections"], src: {**workflow["connections"].get(src, {}), "main": outputs}}
    return {**workflow, "connections": connections}


# ---------------------------------------------------------------- 06-b paths

def paths(workflow: Workflow) -> list[list[str]]:
    nodes = {n["name"] for n in workflow["nodes"]}
    found: list[list[str]] = []

    def walk(name: str, trail: list[str]) -> None:
        if name in trail:
            raise ValueError(f"cycle at {name!r}")
        trail = [*trail, name]
        nxt = [t for t in successors(workflow, name) if t in nodes]
        if not nxt:
            found.append(trail)
        for t in nxt:
            walk(t, trail)

    for n in workflow["nodes"]:
        if n["type"] in TRIGGER_TYPES:
            walk(n["name"], [])
    return found


def llm_calls(workflow: Workflow, path: list[str]) -> int:
    types = {n["name"]: n["type"] for n in workflow["nodes"]}
    return sum(1 for name in path if types[name] in LLM_TYPES)


# ---------------------------------------------------------------- 06-c validate

def validate(workflow: Workflow) -> list[str]:
    problems: list[str] = []
    nodes = {n["name"]: n for n in workflow["nodes"]}
    triggers = [n["name"] for n in workflow["nodes"] if n["type"] in TRIGGER_TYPES]

    if not triggers:
        problems.append("no trigger node")

    for src, outs in workflow["connections"].items():
        for output in outs.get("main", []):
            for link in output:
                if src not in nodes or link["node"] not in nodes:
                    problems.append(f"dangling connection: {src} -> {link['node']}")

    reachable, queue = set(triggers), list(triggers)
    while queue:
        for t in successors(workflow, queue.pop()):
            if t in nodes and t not in reachable:
                reachable.add(t)
                queue.append(t)
    problems += [f"unreachable node: {name}" for name in nodes if name not in reachable]

    if not workflow.get("settings", {}).get("errorWorkflow"):
        problems.append("missing errorWorkflow")

    for node in workflow["nodes"]:
        if is_write(node) and node.get("onError") != "continueErrorOutput":
            problems.append(f"unhandled write failure: {node['name']}")
        if node["type"] == SWITCH_TYPE and node["parameters"].get("options", {}).get("fallbackOutput") in (None, "none"):
            problems.append(f"switch without fallback: {node['name']}")

    try:
        all_paths = paths(workflow)
    except ValueError as e:
        problems.append(f"cycle: {e}")
        return problems

    ungated: list[str] = []
    for path in all_paths:
        pending = None
        for name in path:
            node = nodes[name]
            if node["type"] == AGENT_TYPE:
                pending = name
            elif node["type"] == GATE_TYPE:
                pending = None
            elif is_write(node) and pending:
                msg = f"ungated write: {pending} -> {name}"
                if msg not in ungated:
                    ungated.append(msg)
    return problems + ungated


# ---------------------------------------------------------------- 06-d the design

def ticket_router_workflow() -> Workflow:
    wf = empty_workflow("Ticket router")
    wf = {**wf, "settings": {"errorWorkflow": "ops-error-handler"}}
    specs = [
        make_node("Ticket In", "n8n-nodes-base.webhook", {"httpMethod": "POST", "path": "ticket"}, (0, 200)),
        make_node("Classify ticket", "@n8n/n8n-nodes-langchain.textClassifier",
                  {"categories": "refund, product_question, complaint"}, (220, 200)),
        make_node("Route", SWITCH_TYPE, {"options": {"fallbackOutput": "extra"}}, (440, 200)),
        make_node("Issue refund", HTTP_TYPE, {"method": "POST", "url": "https://shop.example/refunds"},
                  (700, 40), onError="continueErrorOutput"),
        make_node("Answer agent", AGENT_TYPE, {"text": "={{ $json.ticket }}"}, (700, 200)),
        make_node("Approve reply", GATE_TYPE, {"resume": "webhook"}, (920, 200)),
        make_node("Send reply", HTTP_TYPE, {"method": "POST", "url": "https://mail.example/send"},
                  (1140, 200), onError="continueErrorOutput"),
        make_node("Human queue", HTTP_TYPE, {"method": "POST", "url": "https://queue.example/tickets"},
                  (700, 360), onError="continueErrorOutput"),
        make_node("Alert ops", "n8n-nodes-base.slack", {"channel": "#ops-alerts"}, (1380, 360)),
    ]
    for node in specs:
        wf = add_node(wf, node)
    edges = [
        ("Ticket In", "Classify ticket", 0), ("Classify ticket", "Route", 0),
        ("Route", "Issue refund", 0), ("Route", "Answer agent", 1),
        ("Route", "Human queue", 2), ("Route", "Human queue", 3),
        ("Answer agent", "Approve reply", 0), ("Approve reply", "Send reply", 0),
        ("Issue refund", "Alert ops", 1), ("Send reply", "Alert ops", 1), ("Human queue", "Alert ops", 1),
    ]
    for src, dst, output in edges:
        wf = connect(wf, src, dst, output)
    return wf
