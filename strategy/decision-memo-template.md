# Decision memo: <agent name>

**Decision requested:** <ship v1 / ship v2 / don't ship / pilot with N users>
**Author / date:**

## 1. Problem and value (≤ 5 lines)
Who has the problem, how often, and what it costs today. Use the numbers from `agent-or-not.md`.

## 2. What we built
One paragraph and one diagram. Autonomy level (0–3) and why.

## 3. Evidence

| | v1 (own code) | v2 (<framework>) |
|---|---|---|
| Eval pass rate (n = ) | | |
| pass^3 (consistency) | | |
| Cost per task | | |
| p50 turns / latency | | |
| Lines of code | | |
| Hours to build | | |

The most important failure cases, and what they mean:

## 4. Risks and mitigations
Prompt injection, wrong irreversible actions, data exposure, vendor lock-in, cost blow-ups. Give one line each, with a mitigation.

## 5. Recommendation
The decision, the main reason in one sentence, and what would change your mind.

## 6. If approved: next 30 days
How eval cases will be collected from production, who reviews failures, and the kill criteria.
