# 05 · Orchestration and multi-agent (3–5 h)

**Goal:** learn the handful of patterns behind "multi-agent systems", and above all **when not to use them**. Most production systems that work are *workflows* (code decides the steps) with a little agency where it pays off.

## The spectrum

```
 more predictable, cheaper                                      more flexible, pricier, harder to eval
 ─────────────────────────────────────────────────────────────────────────────────────────────►
 single call → chain → routing → orchestrator-workers → evaluator-optimizer → autonomous agent (01)
```

Start at the left, and move right only when an eval shows you need to.

## Build (`patterns.py`)

| TODO | Pattern | Use when |
|---|---|---|
| 05-a | `chain`: fixed steps with gates | The task splits into known steps |
| 05-b | `route`: classify, then dispatch | Inputs fall into clear categories that need different handling |
| 05-c | `orchestrate`: plan → parallel workers → synthesise | Subtasks can't be known in advance, and they're independent |
| 05-d | `evaluate_optimize`: draft → critique → revise | There are clear criteria, and feedback measurably improves the output |

```bash
uv run pytest modules/05-orchestration -x
uv run python modules/05-orchestration/demo.py          # prints calls and tokens for each pattern
```

## Done when

- [ ] Tests green on your code
- [ ] You've run the demo and recorded the **calls and tokens** for each pattern in your journal
- [ ] **Cost experiment:** answer the orchestrator's question with one plain `ask()` call. Compare quality (judge it yourself) against cost. Was orchestration worth it here?
- [ ] **Eval it:** pick one pattern and write 5 eval cases for it, reusing your Module 04 harness

## Key ideas

- **Multi-agent multiplies tokens.** Every worker re-reads its context, and the synthesiser reads everything. Expect roughly N times the cost.
- **Parallel is for independent work.** If subtasks depend on each other, a chain is simpler and more reliable.
- **Routing is often the best investment.** Sending a refund request to deterministic code (no model at all) beats any agent.
- **Critics need criteria.** "Make it better" loops forever, while "max 80 words, no hashtags" converges.

## Strategy brief → `progress/journal.md`

1. A vendor pitches "a team of 12 AI agents" for your process. What three questions expose whether that's needed or just theatre?
2. Draw your current job as a flow. Which steps are a *chain*, which are *routing*, and where (if anywhere) would real agency pay for itself?
