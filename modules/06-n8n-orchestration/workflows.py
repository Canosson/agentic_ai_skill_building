"""Module 06: n8n as an architecture lens. Design a workflow as data, then lint it.

n8n workflows are JSON: a list of `nodes` and a `connections` map. That makes them testable
like any other data structure, which is how you stop a low-code diagram from becoming an
unreviewed production system. You'll build:

  1. small immutable builders for n8n workflow JSON
  2. path analysis (every route from a trigger to a leaf, and what each route costs in model calls)
  3. a linter that enforces the architecture rules from Module 05 and the strategy folder
  4. a real design: a support-ticket router that passes your own linter

No n8n instance is needed for the tests. Run one locally to see your design on a canvas (README).

    uv run pytest modules/06-n8n-orchestration -x
    uv run python modules/06-n8n-orchestration/demo.py

Format reference: https://docs.n8n.io/ (node settings: `onError`, Switch `options.fallbackOutput`,
Wait node, Error Trigger, workflow `settings.errorWorkflow`)
"""

from __future__ import annotations

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
GATE_TYPE = "n8n-nodes-base.wait"                    # pauses until a human (or system) calls back
AGENT_TYPE = "@n8n/n8n-nodes-langchain.agent"
LLM_TYPES = {AGENT_TYPE, "@n8n/n8n-nodes-langchain.textClassifier"}   # nodes that call a model
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def empty_workflow(name: str) -> Workflow:
    return {"name": name, "nodes": [], "connections": {}, "settings": {}}


def is_write(node: Node) -> bool:
    """An HTTP Request with a mutating method. These change the outside world."""
    return node["type"] == HTTP_TYPE and str(node["parameters"].get("method", "GET")).upper() in WRITE_METHODS


def successors(workflow: Workflow, name: str) -> list[str]:
    """Names of nodes directly after `name`, across all of its outputs."""
    outputs = workflow["connections"].get(name, {}).get("main", [])
    return [link["node"] for output in outputs for link in output]


# ---------------------------------------------------------------- 06-a builders

def make_node(name: str, type: str, parameters: dict | None = None, position: tuple[int, int] = (0, 0),
              **settings: Any) -> Node:
    """An n8n node: {"id", "name", "type", "typeVersion": 1, "position": [x, y], "parameters": {...}}
    plus any extra keyword settings merged in at the top level (e.g. onError="continueErrorOutput").

    The id must be stable for the same name (use uuid.uuid5) so re-exporting a workflow doesn't
    churn your git diff. Copy `parameters` rather than keeping the caller's dict.
    """
    # TODO(06-a)
    raise NotImplementedError


def add_node(workflow: Workflow, node: Node) -> Workflow:
    """Return a NEW workflow with the node appended. The input must not change.
    A node name that already exists -> ValueError (names are how n8n connections refer to nodes)."""
    # TODO(06-a)
    raise NotImplementedError


def connect(workflow: Workflow, src: str, dst: str, output: int = 0) -> Workflow:
    """Return a NEW workflow with src's output number `output` wired to dst.

    n8n stores it as:
        connections[src]["main"][output] = [{"node": dst, "type": "main", "index": 0}, ...]
    `main` is a list with one entry per output; pad with [] if `output` is beyond the end (a Switch
    wired only on output 2 still needs entries 0 and 1). Connecting twice on the same output appends,
    which is how one output fans out to several nodes. Unknown src or dst -> ValueError.
    Do not mutate the input workflow, including nested lists.
    """
    # TODO(06-a)
    raise NotImplementedError


# ---------------------------------------------------------------- 06-b paths

def paths(workflow: Workflow) -> list[list[str]]:
    """Every route from a trigger node to a node with no successors, as lists of node names.

    Follow all outputs. Branches produce separate paths. A cycle -> ValueError mentioning "cycle".
    (Ignore connection targets that are not real nodes.)
    """
    # TODO(06-b)
    raise NotImplementedError


def llm_calls(workflow: Workflow, path: list[str]) -> int:
    """How many nodes on this path call a model (types in LLM_TYPES). This is the cost of the path."""
    # TODO(06-b)
    raise NotImplementedError


# ---------------------------------------------------------------- 06-c validate

def validate(workflow: Workflow) -> list[str]:
    """Return a list of problems (empty = sound). Use exactly these messages (tests look for them):

      "no trigger node"                          no node whose type is in TRIGGER_TYPES
      "dangling connection: A -> B"              a connection whose source or target isn't a node
      "unreachable node: X"                      not reachable from any trigger
      "missing errorWorkflow"                    settings.errorWorkflow is absent/empty
      "unhandled write failure: X"               a write node (is_write) without onError == "continueErrorOutput"
      "switch without fallback: X"               a Switch whose parameters["options"]["fallbackOutput"] is missing or "none"
      "ungated write: AGENT -> WRITE"            on some path, an agent node is followed by a write node
                                                 with no GATE_TYPE (Wait) node in between
      "cycle: ..."                               paths() raised; report it, don't crash

    Why these rules: an agent's output is untrusted text. Letting it drive a POST without a human
    in between is how a prompt-injected ticket issues a refund. A write whose failure goes nowhere
    loses data silently. A Switch without a fallback drops anything the classifier didn't expect.
    """
    # TODO(06-c)
    raise NotImplementedError


# ---------------------------------------------------------------- 06-d the design

def ticket_router_workflow() -> Workflow:
    """Design a support-ticket router that passes validate() and these architecture decisions:

      Ticket In (webhook)  ->  Classify ticket (textClassifier, ONE model call)  ->  Route (Switch)
        output 0  refund            -> Issue refund (HTTP POST, plain code, NO agent)
        output 1  product question  -> Answer agent (AGENT) -> Approve reply (Wait) -> Send reply (HTTP POST)
        output 2  complaint         -> Human queue (HTTP POST)
        output 3  fallback ("extra"): anything the classifier didn't expect -> Human queue
      Every write node routes its error output (output 1) to "Alert ops" (a Slack node).
      Set settings.errorWorkflow to "ops-error-handler".

    Use the exact node names above (tests look them up). The Switch needs
    parameters={"options": {"fallbackOutput": "extra"}}, which is what creates output 3.
    Build it with make_node / add_node / connect so every step stays immutable.

    Before you code, decide on paper why the refund path has no agent and why the unknown-ticket
    path ends at a human. Those two decisions are the architecture. The JSON is just the record.
    """
    # TODO(06-d)
    raise NotImplementedError
