"""Each pattern against the real model, with the call count and token cost of each.

    uv run python modules/05-orchestration/demo.py            # all four
    uv run python modules/05-orchestration/demo.py route      # just one
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.llm import AnthropicLLM
from lab.testing import load

p = load(__file__, "patterns")


def cost(llm):
    return f"[{llm.calls} calls, {llm.usage['input_tokens'] + llm.usage['output_tokens']:,} tokens]"


def demo_chain():
    llm = AnthropicLLM()
    out = p.chain(llm, [
        ("List 3 key points about the topic as bullets. Nothing else.", lambda s: s.count("-") + s.count("•") >= 3),
        ("Turn these bullets into one tight paragraph for a busy executive.", None),
    ], "Why do AI agent projects fail in production?")
    print("CHAIN", cost(llm), "\n", out[-1], "\n")


def demo_route():
    cheap = AnthropicLLM()
    handlers = {
        "refund": lambda q: "→ refund workflow (deterministic code, no LLM needed)",
        "product_question": lambda q: "→ product-docs agent",
        "complaint": lambda q: "→ human support queue",
    }
    for q in ["I want my money back for order 1182", "Does the jacket come in XL?", "Your courier threw my parcel!"]:
        chosen, out = p.route(cheap, q, handlers, fallback="complaint")
        print(f"ROUTE {q!r:45} {chosen:18} {out}")
    print(cost(cheap), "\n")


def demo_orchestrate():
    llm = AnthropicLLM()
    worker_llm = AnthropicLLM()
    worker = lambda sub: p.ask(worker_llm, "Answer in at most 3 sentences.", sub, max_tokens=300)
    r = p.orchestrate(llm, "Compare MCP, function calling and browser automation as ways to give an agent "
                           "access to a SaaS tool. Cover setup effort, reliability and security.", worker)
    print("ORCHESTRATE subtasks:", r.subtasks)
    print(f"  planner+synth {cost(llm)}  workers {cost(worker_llm)}\n", r.final[:1200], "\n")


def demo_refine():
    llm = AnthropicLLM()
    r = p.evaluate_optimize(llm, "Write a LinkedIn post (max 80 words) announcing I finished building my first AI agent from scratch.",
                            "Max 80 words. No hashtags. No emojis. No clichés like 'excited to share' or 'game-changer'. "
                            "Mentions one concrete thing learned.")
    print(f"REFINE approved={r.approved} rounds={r.rounds} {cost(llm)}")
    for i, (_, fb) in enumerate(r.history, 1):
        print(f"  round {i} feedback: {fb[:150]}")
    print("\n", r.final)


if __name__ == "__main__":
    demos = {"chain": demo_chain, "route": demo_route, "orchestrate": demo_orchestrate, "refine": demo_refine}
    for name in sys.argv[1:] or demos:
        demos[name]()
