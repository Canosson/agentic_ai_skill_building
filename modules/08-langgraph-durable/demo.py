"""Human approval, crash recovery and tracing against the real model.

    uv run python modules/08-langgraph-durable/demo.py            # all three
    uv run python modules/08-langgraph-durable/demo.py approval   # just one
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from lab.llm import AnthropicLLM
from lab.testing import load

d = load(__file__, "durable")


def cost(llm):
    return f"[{llm.calls} calls, {llm.usage['input_tokens'] + llm.usage['output_tokens']:,} tokens]"


def demo_approval():
    llm = AnthropicLLM()
    graph = d.build_approval_graph(llm, lambda text: print(f"  >>> SENT: {text}"), InMemorySaver())
    first = d.trace_run(graph, {"ticket": "I was charged twice for order 1182. Please fix this."}, "demo")
    print("paused at:", first.nodes, "interrupted =", first.interrupted)
    print("DRAFT FOR REVIEW:\n ", first.state["draft"])
    answer = input("\nApprove? [y/N/edit text] ").strip()
    if answer.lower() in ("y", "yes"):
        decision = {"approved": True}
    elif answer.lower() in ("", "n", "no"):
        decision = {"approved": False}
    else:
        decision = {"approved": True, "edited": answer}
    second = d.trace_run(graph, Command(resume=decision), "demo")
    print("resumed:", second.nodes, "->", second.state["outcome"], cost(llm))


def demo_recovery():
    attempts = {"n": 0}

    def flaky_publish(v):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ConnectionError("503 from upstream")
        return v + " | published"

    def log(name):
        def step(v):
            print(f"  running {name}")
            return v + f" | {name}"
        return step

    graph = d.build_pipeline([("fetch", log("fetch")), ("summarise", log("summarise")),
                              ("publish", flaky_publish)], InMemorySaver())
    out = d.run_with_resume(graph, {"value": "start"}, "demo", retry_on=(ConnectionError,))
    print("result:", out["value"], "\n(note: fetch and summarise each ran once)")


def demo_trace():
    llm = AnthropicLLM()
    graph = d.build_approval_graph(llm, lambda t: None, InMemorySaver())
    t1 = d.trace_run(graph, {"ticket": "Where is my parcel?"}, "trace")
    t2 = d.trace_run(graph, Command(resume={"approved": False}), "trace")
    print("call 1 nodes:", t1.nodes, "interrupted:", t1.interrupted)
    print("call 2 nodes:", t2.nodes, "outcome:", t2.state["outcome"], cost(llm))


if __name__ == "__main__":
    demos = {"approval": demo_approval, "recovery": demo_recovery, "trace": demo_trace}
    for name in sys.argv[1:] or demos:
        demos[name]()
