# 00 · Setup (30 min)

**Goal:** a working environment and one real model call, with its token count and cost in front of you.

## Steps

1. Install [uv](https://docs.astral.sh/uv/) (Python package and version manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. From the repo root, install everything. uv fetches a suitable Python version if you don't have one.
   ```bash
   uv sync
   ```
3. Create an API key at <https://platform.claude.com> → API keys, then:
   ```bash
   cp .env.example .env    # paste your key into .env
   ```
   Set a monthly spend limit in the console. Everything in modules 01–05 together should cost well under $5 on Haiku.
4. Check the offline harness (no key needed):
   ```bash
   uv run pytest modules/00-setup
   ```
5. Make your first real call:
   ```bash
   uv run python modules/00-setup/hello.py
   ```

## Done when

- [ ] `uv run pytest modules/00-setup` is green
- [ ] `hello.py` prints a reply, the token counts and an estimated cost
- [ ] You can explain why every test in this lab runs **without** an API key (read `lab/llm.py`, the `FakeLLM` class)

## Strategy brief → write your answers in `progress/journal.md`

1. A model call is billed by tokens in *and* out. In an agent loop, the whole conversation is re-sent on every turn. What does that do to cost as a task gets longer?
2. Why would a team put a single interface (`LLM`) between all its code and the model vendor? What is that worth in a negotiation, or when a new model comes out?
