# 09 · Capstone: a real agent, a framework decision, and a memo (2–3 weeks)

**Goal:** prove the skill on a problem from your own work, then make, and defend, the build-vs-framework decision the way a technical lead would.

## The brief

1. **Pick a real problem.** It should be something you or someone you work with does repeatedly, with a clear "good" outcome. Candidates from the tools you already have connected:
   - Shopify: an agent that answers "why did sales drop last week?" from store data
   - Notion and Gmail: triage incoming requests into a Notion database, drafting replies for approval
   - Make: an agent that decides *which* scenario to trigger, with deterministic workflows doing the work
2. **Write the eval set first.** At least 20 cases in `capstone/cases.jsonl`, including about 5 where the right behaviour is to refuse, ask, or hand over to a human.
3. **Build v1 with your own lab code:** the loop, registry or MCP, and a pattern from 05. Record the baseline pass rate, cost per task and p50 turns.
4. **Build v2 with one framework**, chosen on purpose. Run the *same* evals.
5. **Write the decision memo** with `strategy/decision-memo-template.md`. Ship v1 or v2, and defend the choice with numbers.

## Choosing the framework

[Guessing] The landscape moves quickly, so check each option's current status before you choose. Today's main contenders, by what they're good at:

| If you need… | Look at |
|---|---|
| The loop and tools that power Claude Code, file and shell access, subagents | Claude Agent SDK |
| Explicit, inspectable state machines and durable long-running flows | LangGraph (you already built the basics in Modules 07–08) |
| Type-safe agents with validated, structured outputs | Pydantic AI |
| A Microsoft/Azure stack (successor to AutoGen) | Microsoft Agent Framework |
| Fast prototyping of role-based multi-agent crews | CrewAI |
| Lightweight agents with batteries included (formerly Phidata) | Agno |
| A provider-neutral SDK with handoffs and guardrails | OpenAI Agents SDK |

Judge each one on: lines of code vs v1, eval pass rate, cost per task, how easy failures are to debug, and lock-in.

## Done when

- [ ] The eval set exists and was committed **before** v1 was built
- [ ] v1 and v2 have numbers from the same eval run
- [ ] The memo is written, and you've presented it to one real person who could say no
- [ ] `progress/skills-matrix.md` updated, with evidence links

## Strategy brief

This module *is* the strategy brief. The memo is the deliverable.
