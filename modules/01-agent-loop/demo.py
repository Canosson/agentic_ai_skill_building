"""Run YOUR agent loop against the real model, with two toy tools and a trace.

    uv run python modules/01-agent-loop/demo.py "What is 1234*5678, and what day is it?"
    LAB_SOLUTION=1 uv run python modules/01-agent-loop/demo.py   # reference loop
"""

import ast
import datetime as dt
import operator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.llm import AnthropicLLM
from lab.testing import load

agent = load(__file__, "agent")

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}


def calculator(expression: str) -> str:
    """Safe arithmetic evaluator (no eval())."""
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp):
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError(f"unsupported expression: {ast.dump(n)}")
    return str(ev(ast.parse(expression, mode="eval").body))


def today() -> str:
    return dt.date.today().strftime("%A %d %B %Y")


TOOLS = [
    {"name": "calculator", "description": "Evaluate an arithmetic expression like '12*(3+4)'.",
     "input_schema": {"type": "object", "properties": {"expression": {"type": "string"}},
                      "required": ["expression"]}},
    {"name": "today", "description": "Get today's date.",
     "input_schema": {"type": "object", "properties": {}}},
]


def trace(kind, data):
    if kind == "model":
        for b in data.content:
            if b["type"] == "text" and b["text"].strip():
                print(f"  model  > {b['text'].strip()[:200]}")
            elif b["type"] == "tool_use":
                print(f"  call   > {b['name']}({b['input']})")
    else:
        flag = " [ERROR]" if data["is_error"] else ""
        print(f"  result < {data['output'][:200]}{flag}")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is 1234*5678, and what day of the week is it?"
    llm = AnthropicLLM()
    print(f"\nQ: {question}\n")
    r = agent.run_agent(llm, question, TOOLS, {"calculator": calculator, "today": today}, on_event=trace)
    print(f"\nA: {r.final_text}")
    print(f"\nturns={r.turns}  stopped={r.stopped_reason}  tokens={llm.usage}")
