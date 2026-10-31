# Agent or not? A 10-minute screen

Use this before building anything. If most answers fall in the left column, build a workflow, or skip AI entirely.

| Question | Workflow / no AI | Agent |
|---|---|---|
| Can you write the steps down in advance? | Yes, the same every time | No, they depend on what's found along the way |
| How many distinct paths are there? | A few, enumerable | Too many to enumerate |
| Cost of one wrong action | High or irreversible (payments, deletions, emails to customers) | Low, or a human reviews before anything takes effect |
| Can you check the output automatically? | — | Yes. If not, you can't evaluate it, so you can't improve it. |
| Volume × time saved per task | Low: automation won't pay back | High enough to cover tokens, building and upkeep |
| Latency tolerance | Needs to be under a second | Seconds to minutes are fine |
| Data access | Data isn't reachable via API or MCP | Tools exist, or can be built (Module 03) |

## The four numbers to estimate before you build

1. **Tasks per month**: ______
2. **Human minutes per task today**: ______
3. **Expected cost per task** (tokens × price, from a prototype eval run): ______
4. **Acceptable failure rate**, and what a failure costs: ______

If (2) × your hourly rate × (1) isn't clearly bigger than (3) × (1) plus build and maintenance cost, stop.

## Autonomy levels: pick the lowest one that works

| Level | The agent… | Example |
|---|---|---|
| 0 | Suggests; a human does everything | Drafts a reply in the side panel |
| 1 | Acts after approval for each action | `needs_approval()` from Module 03 |
| 2 | Acts alone on reversible actions, asks for irreversible ones | Labels and drafts emails, asks before sending |
| 3 | Acts alone; humans audit samples | Ticket triage with weekly review of a sample |
