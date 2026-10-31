# 08 · LangGraph: durable and supervised (3–4 h)

**Goal:** learn the three reasons to reach for a graph runtime instead of your own loop: **pause for a human**, **resume after a crash**, and **trace what ran**. If your agent needs none of these, you probably don't need LangGraph. This module gives you the evidence to say so.

> Prerequisite: Module 07 (state, nodes, edges) and Module 04 (evals).

## The one idea

A **checkpointer** saves the graph's state after every node, keyed by a `thread_id`. Everything else follows from it:

```
invoke(input, thread A) ──► draft ──► review ──╳ interrupt()  ── state saved ──► process can exit
invoke(Command(resume=answer), thread A) ──► review (restarts, interrupt() returns answer) ──► send ──► END
```

Tests use `InMemorySaver`. In production you'd swap in a SQLite or Postgres saver with the same API (and the state survives the process dying, which memory doesn't).

## Build (`durable.py`)

| TODO | You build | The lesson |
|---|---|---|
| 08-a | `build_approval_graph` | `interrupt()` + `Command(resume=…)`; fail closed; why the model call and the send must not share a node with `interrupt()` |
| 08-b | `build_pipeline`, `run_with_resume` | Resume from the last checkpoint with `invoke(None, config)`; completed steps don't re-run |
| 08-c | `trace_run` | `stream_mode="updates"`: the trajectory of nodes, ready to assert on in evals |

```bash
uv run pytest modules/08-langgraph-durable -x
uv run python modules/08-langgraph-durable/demo.py          # approval is interactive: you play the human
```

## Done when

- [ ] Tests green on your code
- [ ] **Break it on purpose:** move the `ask(...)` call into the `review` node, above `interrupt()`. Run the tests and record which one fails and how many model calls a single approval now costs.
- [ ] **Idempotency:** `run_with_resume` retries a step that raised. If that step were "send email" and the failure happened *after* the email went out, what happens? Write down how you'd make `send` safe to repeat (idempotency key, check-before-send).
- [ ] **Eval it:** add 5 cases to your Module 04 harness that assert on `trace_run(...).nodes`, e.g. "a rejected draft never visits `send`" and "`send` is never reached without `review`". Use a **unique `thread_id` per eval case**, or state from one case leaks into the next.
- [ ] Run `demo.py approval` and note the real draft, your decision and the cost

## Key ideas

- **Resume re-runs the interrupted node from the top.** Put side effects *after* `interrupt()`, and expensive calls in an earlier node.
- **Fail closed.** `approved is True`, not "truthy". A human typing "yes" in the wrong field should not trigger a refund.
- **Checkpoints make retries cheap, not safe.** Resuming skips finished nodes, but the failed node may have half-completed. Side effects need idempotency.
- **A trace is a test oracle.** Asserting on the path catches policy violations that a correct-looking final answer hides.
- **Memory is not durability.** `InMemorySaver` dies with the process. Say so in any design that promises "resumable".

## Strategy brief → `progress/journal.md`

1. Pick one real action in your job that an agent should *never* do without sign-off (refund, publish, price change, email to a client). Where exactly would the `interrupt` sit, who answers it, and what happens if nobody does for 3 days?
2. Compare your design with n8n's Wait node (Module 06). When would you pick each for the approval step, and what does each cost you in lock-in and operations?
