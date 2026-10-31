"""Your first real model call. Run: uv run python modules/00-setup/hello.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.llm import AnthropicLLM

# Rough USD per million tokens for the default model (Haiku 5.5). Check current pricing
# at https://platform.claude.com/docs/en/about-claude/pricing and update if it changed.
PRICE_IN, PRICE_OUT = 0.10, 0.50

llm = AnthropicLLM()
resp = llm.complete(
    system="You are a concise tutor.",
    messages=[{"role": "user", "content": "In two sentences: what makes software an 'agent'?"}],
    max_tokens=200,
)

print(f"model:        {llm.model}")
print(f"stop_reason:  {resp.stop_reason}")
print(f"reply:        {resp.text}\n")
i, o = resp.usage["input_tokens"], resp.usage["output_tokens"]
print(f"tokens:       {i} in / {o} out")
print(f"est. cost:    ${(i * PRICE_IN + o * PRICE_OUT) / 1e6:.6f}")
print("\nRaw content blocks (this is the protocol your agent loop will handle):")
print(resp.content)
