"""The four graphs against the real model. Prints each graph's shape, calls and tokens.

    uv run python modules/07-langgraph-graphs/demo.py            # all four
    uv run python modules/07-langgraph-graphs/demo.py refine     # just one
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.llm import AnthropicLLM
from lab.testing import load

g = load(__file__, "graphs")


def cost(llm):
    return f"[{llm.calls} calls, {llm.usage['input_tokens'] + llm.usage['output_tokens']:,} tokens]"


def show(graph):
    print(graph.get_graph().draw_mermaid())


def demo_chain():
    llm = AnthropicLLM()
    graph = g.build_chain_graph(llm, [
        ("List 3 key points about the topic as bullets. Nothing else.", lambda s: s.count("-") + s.count("•") >= 3),
        ("Turn these bullets into one tight paragraph for a busy executive.", None),
    ])
    out = graph.invoke({"current": "Why do AI agent projects fail in production?", "outputs": [], "error": None})
    show(graph)
    print("CHAIN", cost(llm), out["error"] or "", "\n", out["outputs"][-1], "\n")


def demo_route():
    llm = AnthropicLLM()
    handlers = {
        "refund": lambda q: "→ refund workflow (deterministic code, no LLM needed)",
        "product_question": lambda q: "→ product-docs agent",
        "complaint": lambda q: "→ human support queue",
    }
    graph = g.build_router_graph(llm, handlers, fallback="complaint")
    show(graph)
    for q in ["I want my money back for order 1182", "Does the jacket come in XL?", "Your courier threw my parcel!"]:
        out = graph.invoke({"query": q})
        print(f"ROUTE {q!r:45} {out['category']:18} {out['answer']}")
    print(cost(llm), "\n")


def demo_orchestrate():
    llm, worker_llm = AnthropicLLM(), AnthropicLLM()
    worker = lambda sub: g.ask(worker_llm, "Answer in at most 3 sentences.", sub, max_tokens=300)
    graph = g.build_orchestrator_graph(llm, worker)
    show(graph)
    out = graph.invoke({"task": "Compare MCP, function calling and browser automation as ways to give an agent "
                                "access to a SaaS tool. Cover setup effort, reliability and security."})
    print("ORCHESTRATE subtasks:", out["subtasks"])
    print(f"  planner+synth {cost(llm)}  workers {cost(worker_llm)}\n", out["final"][:1200], "\n")


def demo_refine():
    llm = AnthropicLLM()
    graph = g.build_refine_graph(llm)
    show(graph)
    out = graph.invoke({
        "task": "Write a LinkedIn post (max 80 words) announcing I finished building my first AI agent from scratch.",
        "criteria": "Max 80 words. No hashtags. No emojis. No clichés like 'excited to share' or 'game-changer'. "
                    "Mentions one concrete thing learned.",
    })
    print(f"REFINE approved={out['approved']} rounds={out['round']} {cost(llm)}")
    for i, (_, fb) in enumerate(out["history"], 1):
        print(f"  round {i} feedback: {fb[:150]}")
    print("\n", out["draft"])


if __name__ == "__main__":
    demos = {"chain": demo_chain, "route": demo_route, "orchestrate": demo_orchestrate, "refine": demo_refine}
    for name in sys.argv[1:] or demos:
        demos[name]()
