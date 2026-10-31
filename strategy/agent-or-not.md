# Agent or not? A 10-minute screen

Use this before building anything. It has two steps: first tag the bottleneck with its type (which methodology applies), then, only if it's Type 4, run the agent screen.

## Step 1: Tag every bottleneck with its type

There are four types of system implementation. **You implement them in order**, because each one is the foundation of the next.

| Type | Name | What it is | Examples |
|---|---|---|---|
| 1 | Work (normal business functions) | The job done by hand, with a process around it | SOPs, training, hiring, marketing, fulfilling by hand |
| 2 | Memory | Data you'd bet a decision on | CRM, databases, project management |
| 3 | Automation | Duplicate yourself with rules | If this, then that; scheduled jobs; fixed-step workflows |
| 4 | AI agent | A whole job off your plate | An agent with tools, a goal and a defined autonomy level |

**How to tag a bottleneck.** Walk the questions in order and stop at the first "no". That is the type you build.

1. **Is the work itself defined?** Can someone other than you do it from a written SOP? If no, it's **Type 1**: write the SOP, train, hire, do it by hand until it's repeatable. You can't automate a process that doesn't exist yet.
2. **Is the data it depends on trustworthy and in one place?** Would you bet a decision on it? If no, it's **Type 2**: build the CRM, database or tracker first. Automation and agents on top of bad data produce confident, wrong output.
3. **Can fixed rules do it?** Are the steps the same every time, with few enumerable paths? If yes, it's **Type 3**: build a rules-based automation. It's cheaper, faster and more predictable than an agent.
4. **Otherwise, it's Type 4.** The work is repeatable and the data is sound, but the steps depend on what's found along the way. Continue to Step 2.

Notes:

- A bottleneck often hides several types. Tag each one separately and build the lowest type first.
- Skipping ahead is the common failure. An agent that sits on top of an undocumented process and a messy CRM will not fix the bottleneck. It will make it harder to see.
- Record the tag next to the bottleneck in `progress/journal.md` so the choice is visible and reviewable.

## Step 2: The agent screen (Type 4 only)

If most answers fall in the left column, build a workflow (Type 3), or skip AI entirely.

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
