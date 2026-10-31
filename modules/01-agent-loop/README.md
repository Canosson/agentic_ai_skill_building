# 01 · The agent loop (2–4 h)

**Goal:** write the loop that every agent framework wraps. Once you've done it yourself, LangGraph, CrewAI and the agent SDKs stop being magic. They're this loop plus extra features.

## The idea

An agent is a model running in a loop. On each turn it either answers or asks to use a tool, and your code feeds the tool's result back in:

```
user message ─► model ─► stop_reason == "tool_use"? ──no──► final answer
                  ▲                │ yes
                  │                ▼
                  └── tool_result ◄─ run the tool(s)
```

That's the whole pattern. Everything hard about agents (reliability, cost, safety, evaluation) comes from what goes *into* this loop, which is the subject of modules 02–05.

## Build

Open `agent.py` and implement two functions:

| TODO | What | Tests |
|---|---|---|
| 01-a | `execute_tool`: run one tool and never crash | 4 |
| 01-b | `run_agent`: the loop | 9 |

Work test-first:

```bash
uv run pytest modules/01-agent-loop -x      # -x = stop at first failure
```

Then run it against the real model and watch the trace:

```bash
uv run python modules/01-agent-loop/demo.py "What is 1234*5678, and what day is it?"
```

## Done when

- [ ] All 13 tests pass on **your** code
- [ ] The demo answers correctly, and you can point to each turn in the trace
- [ ] You've broken it on purpose three ways and written down what happened:
  1. Set `max_turns=1` and ask a question that needs a tool
  2. Make `calculator` raise for every input. Does the model recover or give up?
  3. Give `today` a deliberately misleading description. Does the model still call it?
- [ ] Only now: compare your loop with `lab/loop.py` and note one difference

## Things people get wrong here (the tests catch most of them)

- Sending tool results as separate user messages instead of one message containing all of them
- Losing the assistant's `tool_use` turn, which makes the API reject the next call
- Letting a tool exception kill the run. The model is often better at recovering than your error handler.
- No turn limit. A confused agent loops until it runs out of budget.

## Strategy brief → `progress/journal.md`

1. Your loop has `max_turns`. What would a *cost* limit look like, and who in a company should set it?
2. Error experiment 2: if the model "recovers" by making up an answer when the tool fails, is that better or worse than giving up? What does your answer imply for customer-facing agents?
3. In a sentence each: what does a framework add on top of this loop, and what does it cost you?
