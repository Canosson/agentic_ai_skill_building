# 04 · Evals (4–6 h): the module that matters most

**Goal:** stop judging agents by how they feel. An eval suite turns "it seemed better" into "pass rate went from 75% to 92%, with 0 regressions and 18% fewer tokens".

Most people learning agents skip this part, and it's why most agent demos never become products. A prompt change, a model upgrade or a new tool can silently break cases that used to work. Without evals you only find out from users.

## Build (`evals.py`)

| TODO | What | Why it matters |
|---|---|---|
| 04-a | Deterministic checks | Cheap, fast and exact. Use them wherever you can. |
| 04-b | `llm_judge` | For qualities a string match can't check. It must **fail closed**. |
| 04-c | `grade` | Typos in the dataset must raise errors, not pass silently |
| 04-d | `run_eval` | Multiple trials, crash tolerance, cost tracking |
| 04-e | `compare` | Regression detection, which is the whole point |

```bash
uv run pytest modules/04-evals -x
```

## Use it (real model, ~$0.05 per run on Haiku)

```bash
uv run python modules/04-evals/run.py --save baseline
uv run python modules/04-evals/run.py --system "Answer from memory. Never use tools." --save no-tools
uv run python modules/04-evals/run.py --compare baseline no-tools
uv run python modules/04-evals/run.py --trials 3 --save baseline-x3
```

## Done when

- [ ] Tests green on your code
- [ ] You have a saved `baseline`, and have **improved** on it with a system-prompt change that `compare` shows has zero regressions
- [ ] You've run `--trials 3` and found at least one case that is *flaky* (passes sometimes)
- [ ] You've added **5 cases of your own** to `cases.jsonl`, including at least one the current agent fails
- [ ] **Judge audit:** read 5 judge verdicts by hand. Did you disagree with any? Write down which ones and why.

## Key ideas

- **Write the evals before the feature.** The eval set *is* your spec.
- **Look at the failures, not the score.** A pass rate is a summary. The fixes come from reading individual failures.
- **pass^k beats pass@1.** An agent that passes 1 in 3 runs isn't "working".
- **The judge is a model too.** Check it against your own judgement, keep its rubrics narrow, and prefer deterministic checks.
- **Cost and turns are metrics too.** A 2% gain for 3× the tokens is often a bad trade.

## Strategy brief → `progress/journal.md`

1. A stakeholder asks "is the agent ready to launch?" Write the three-line answer you could give *only* because you have evals.
2. Where should eval cases come from once an agent is in production? Who should own the dataset?
3. A new model is released that's 40% cheaper. What exact process would you run before switching?
