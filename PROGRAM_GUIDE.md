# Program Guide

How to start, how to run the material, what the goal is, and how to get there.

If you only want the commands, the [README](README.md) has a short quick start. This guide explains the reasoning behind the course and how to work through it.

---

## 1. The goal

By the end of this course you should be able to do two things:

1. **Build.** Write the core parts of an agent yourself, without a framework: the agent loop, a defensive tool registry, context management, an MCP server, an eval harness, and the common orchestration patterns.
2. **Decide.** Judge agent projects like a technical lead. That means deciding when an agent is the right tool (and when a plain workflow or no AI at all is better), estimating cost and return, choosing an autonomy level, and defending a build-vs-framework choice with numbers.

The course is **build-first**. You won't read about agents and then forget them. You implement the pieces that every framework (LangGraph, CrewAI, the agent SDKs) is made of. After that, frameworks stop being magic: they are the loop you wrote, plus extra features.

### What you will have at the end

| Outcome | Evidence |
|---|---|
| A working agent loop and tool registry | Green tests on your code, modules 01 and 02 |
| An MCP server used from your own loop and from Claude Desktop/Code | Module 03 demo and host integration |
| An eval harness that detects regressions and flakiness | Saved baselines and `--compare` output, module 04 |
| The four orchestration patterns, with measured cost for each | Journal entries, module 05 |
| An orchestration architecture designed and linted as data | Workflow JSON and linter, module 06 |
| The same patterns as LangGraph graphs, with human approval, crash recovery and traces | Green tests and journal entries, modules 07–08 |
| A real agent for your own work, a framework comparison, and a decision memo | Capstone, module 09 |
| A skills matrix where every level has proof behind it | `progress/skills-matrix.md` |

---

## 2. How the course is structured

### The path

| # | Module | You build | Time |
|---|---|---|---|
| 00 | Setup | One real model call, with its cost | 30 min |
| 01 | Agent loop | The loop that every framework wraps | 2–4 h |
| 02 | Tools and context | Schema generation, a defensive tool registry, context trimming | 3–5 h |
| 03 | MCP | Your own MCP server, used from your loop and from Claude Desktop/Code | 3–4 h |
| 04 | Evals | An eval harness with judges, trials and regression detection | 4–6 h |
| 05 | Orchestration | Chain, router, orchestrator-workers, evaluator-optimizer | 3–5 h |
| 06 | n8n: orchestration architecture | A workflow linter and a ticket-router design: where intelligence belongs, and what each path costs | 3–4 h |
| 07 | LangGraph: state graphs | The Module 05 patterns rebuilt as graphs: state, conditional edges, fan-out, cycles | 3–5 h |
| 08 | LangGraph: durable and supervised | Human approval, crash recovery and run traces with checkpointing | 3–4 h |
| 09 | Capstone | A real agent, a framework bake-off, a decision memo | 2–3 weeks |

Do the modules **in order**. Each one uses ideas from the one before. Modules 00–08 take roughly 25–38 hours of focused work. The capstone is the long one.

### Every module has the same shape

- `README.md`: the concept, what to build, a **Done when** checklist, and a **Strategy brief**.
- **Starter files** with numbered `TODO(NN-x)` markers. This is where you write code.
- `test_*.py`: offline tests that run against a scripted `FakeLLM`. They are free, deterministic and need no API key.
- `demo.py` (module 04 uses `run.py`): your code running against the real model.
- `solution/`: a reference implementation. **Look only after your tests are green.**

### Two tracks in every module

- **Technical track:** make the tests pass, then run the experiments listed under "Done when". The experiments, where you break things on purpose and measure, are where most of the learning happens. Don't skip them.
- **Strategic track:** answer the Strategy brief questions in `progress/journal.md`. These are the questions a manager or stakeholder would ask. Write real answers, in your own words, with numbers where you have them.

### Repository layout

```
lab/            shared code: llm.py (model interface + FakeLLM), loop.py (reference loop, spoiler),
                testing.py, status.py
modules/        00–09, the curriculum
strategy/       decision tools: agent-or-not.md screen, decision-memo-template.md
resources/      reading list mapped to modules
progress/       journal.md and skills-matrix.md (yours to fill in)
CLAUDE.md       instructions that turn Claude into your tutor (see section 6)
```

> **Spoiler warning:** `lab/loop.py` and every `solution/` folder contain finished answers. Don't open them until the matching module's tests pass.

---

## 3. Getting started

### Prerequisites

- A computer with a terminal (macOS, Linux, or Windows with WSL).
- Basic Python: functions, classes, type hints, running a script.
- An Anthropic API key, created at <https://platform.claude.com>. You need it from module 00 step 5 onward; the tests don't need it.
- Optional but recommended: Claude Code or Claude Cowork, opened on this folder, to use as a tutor.

You don't need to install Python yourself. `uv` fetches a suitable version (3.11 or newer).

### Setup, step by step

**1. Install uv** (a fast Python package and version manager). Once per machine:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Install the dependencies.** From the repo root:

```bash
uv sync
```

This creates a `.venv` and installs `anthropic`, `mcp` (the 2.x SDK) and `pytest`.

**3. Add your API key:**

```bash
cp .env.example .env
```

Open `.env` and paste your key over `sk-ant-...`. The file is git-ignored, so it won't be committed. The same file sets `LAB_MODEL`, the model all demos use. It defaults to Haiku because it is cheap and fast enough for learning. Switch to a larger model only when an exercise needs more reasoning.

**4. Set a spend limit.** In the Claude Console, set a monthly limit. Modules 00–08 together should cost only a few dollars on Haiku, but a limit protects you from mistakes such as a runaway loop.

**5. Check the progress board:**

```bash
uv run python -m lab.status
```

It lists each module with tests passed, total tests, and a status: `todo`, `started` or `DONE`. Use it at any time to see where you stand.

**6. Start module 00.** Open `modules/00-setup/README.md` and follow it. It ends with your first real model call and a printed token count and cost.

---

## 4. How to work through a module

Use this loop for every module from 01 onward.

1. **Read the module README** top to bottom before touching code. Understand the concept and the "Done when" list.
2. **Run the tests and watch them fail:**
   ```bash
   uv run pytest modules/01-agent-loop -x
   ```
   `-x` stops at the first failure, so you work on one thing at a time.
3. **Implement one `TODO` at a time.** Read the failing test first. It tells you exactly what behaviour is expected, including the edge cases.
4. **Get the tests green.** Don't change the tests to make them pass; fix your code.
5. **Run the demo against the real model** and read the trace. You are now seeing your code behave with a real model. Note tokens and cost.
6. **Do the "Done when" experiments.** Break the system on purpose, change one variable, measure the difference, and write the numbers in `progress/journal.md`.
7. **Answer the Strategy brief** in the journal.
8. **Only now, compare with the reference** (`solution/` and `lab/loop.py`). Note one thing the reference does differently and why.
9. **Update `progress/skills-matrix.md`**, but only with evidence (see section 7).

### Commands you will use all the time

```bash
uv run python -m lab.status                   # progress board across all modules
uv run pytest modules/NN-name -x              # test YOUR code, stop at first failure
uv run pytest modules/NN-name -q              # quieter summary
uv run python modules/NN-name/demo.py "..."   # run your code against the real model
LAB_SOLUTION=1 uv run pytest modules/NN-name  # test the REFERENCE solution instead of your code
```

`LAB_SOLUTION=1` points the tests at the `solution/` folder instead of your files. Use it to confirm the lab itself works on your machine, not to peek at answers.

### If you get stuck

Escalate in this order, and stop at the first step that unblocks you:

1. **Re-read the failing test.** Ask what it is checking and why.
2. **Re-read the module's concept section.** Most blockers are a missing idea, not missing syntax.
3. **Ask for a hint** (from your tutor, see section 6): first a question, then the concept, then pseudocode for the single stuck step.
4. **Look at the solution** last, and only for the one `TODO` you're stuck on. Then close it and rewrite it from memory.

Struggling for a while before looking is not wasted time. It is the learning.

---

## 5. What each module teaches

A short tour, so you know why each module exists.

**00 · Setup.** You make one real model call and see tokens in and out, plus cost. You also learn why every test in the lab runs without an API key: a `FakeLLM` stands in for the model behind a single `LLM` interface. That same interface is why a company can swap model vendors without rewriting its code.

**01 · Agent loop.** An agent is a model in a loop: on each turn it either answers or asks to use a tool, and your code feeds the tool result back. You implement `execute_tool` (never crash) and `run_agent` (the loop, with a turn limit). Then you break it three ways: a turn limit that's too low, a tool that always fails, a tool with a misleading description. Common bugs the tests catch: sending tool results as separate messages, losing the assistant's `tool_use` turn, letting a tool exception kill the run, having no turn limit.

**02 · Tools and context.** Most agent failures are tool and context failures, not model failures. Part A: you build schema generation from Python type hints, docstring parsing, and a registry with validation, helpful errors and output truncation. This is what every `@tool` decorator does. Part B: you manage the context window with `trim_history` and `compact_tool_results`. Key ideas: errors are instructions to the model, truncate and say you did, fewer and better tools beat many overlapping ones.

**03 · MCP.** You write an MCP server (a small notes tool) once and use it from your own loop, Claude Desktop and Claude Code. The server owns the capability; the host owns the policy (which tools are allowed, when to ask a human). You implement the `needs_approval` risk defaults and run a prompt-injection experiment, which the module calls the most important lesson in it.

**04 · Evals.** The module the course considers most important. You build deterministic checks, an LLM judge that fails closed, strict grading, multi-trial runs, and a `compare` function that detects regressions. Then you use it on a real agent: save a baseline, improve it, prove there are no regressions, and find a flaky case with `--trials 3`. Key ideas: write the evals before the feature, read failures not scores, `pass^k` beats `pass@1`, cost and turns are metrics too.

**05 · Orchestration.** You build four patterns: chain, router, orchestrator-workers, evaluator-optimizer. You measure calls and tokens for each, then try the same task with one plain call to see whether orchestration was worth it. Key idea: multi-agent multiplies tokens, so use it only when an eval shows it pays off.

**06 · n8n: orchestration architecture.** You design before you code. n8n workflows are JSON, so you build small immutable builders for that JSON, analyse every path from trigger to leaf (and how many model calls each path costs), and write a linter that enforces architecture rules: an agent's output must pass a human gate before any write, every write needs an error path, every Switch needs a fallback. Then you design a support-ticket router that passes your own linter. No n8n install is needed for the tests; you can import the exported JSON into a local n8n to see it on a canvas. Key idea: most of a good agent system is not an agent.

**07 · LangGraph: state graphs.** You rebuild the four Module 05 patterns as LangGraph graphs: typed state, nodes that return partial updates, conditional edges, `Send` fan-out with a reducer, and a refine loop with a provable exit. The model calls are identical to Module 05; what changes is that control flow becomes data you can draw and test. You measure what the framework adds (and costs) against your own plain-Python version.

**08 · LangGraph: durable and supervised.** The three reasons to use a graph runtime instead of your own loop: pause for a human (`interrupt` and `Command(resume=...)`), resume after a crash from the last checkpoint instead of re-running everything, and trace which nodes ran so evals can assert on the trajectory. Key ideas: a resumed node restarts from its first line, so side effects go after the interrupt; fail closed on approvals; checkpoints make retries cheap, not safe.

**09 · Capstone.** You pick a real problem from your own work and run the full process: write at least 20 eval cases first (about 5 where the right behaviour is to refuse, ask or hand over to a human), build v1 with your own lab code, build v2 with one framework, run the same evals on both, and write a decision memo. You present the memo to a real person who could say no.

---

## 6. Using Claude as your tutor

`CLAUDE.md` configures Claude (in Claude Code or Cowork, opened on this folder) to **coach, not solve**. It will:

- Refuse to write solutions into your starter files unless you explicitly say "show me the solution" for a specific `TODO`.
- Give hints in escalating order: a question pointing at the failing test, then the concept, then pseudocode, then the solution only on request.
- Push back when your approach is wrong, instead of agreeing to be polite.
- Point out token and cost figures whenever you run demos or evals.

Useful prompts:

| Say this | What happens |
|---|---|
| `Review my 01` | Claude runs the module's tests, reads your code and gives at most three findings, ranked: correctness first, then robustness, then style. It compares with the reference only after the tests pass. |
| `Quiz me on 02` | Five questions, one at a time, mixing protocol details, failure modes and one strategy question. Each answer is graded honestly. |
| `I'm stuck on TODO 02-d` | A hint at the first level of the escalation ladder. |
| `Show me the solution for 03-f` | Only now will Claude show the answer for that one `TODO`. |

When a module is done (all tests green and the experiments recorded in the journal), Claude proposes updates to your skills matrix with evidence links.

You can complete the course without a tutor. The tests and README checklists are enough. The tutor mainly adds faster feedback.

---

## 7. Tracking progress honestly

Two files record your learning. Both start blank.

### `progress/journal.md`

One entry per session, kept short. Experiments, numbers and surprises matter more than summaries. Use the template:

```
## YYYY-MM-DD · Module NN
**Did:**
**Numbers:** (tests passing, turns, tokens, pass rate…)
**Broke on purpose / surprised me:**
**Strategy brief answers:**
**Next session:**
```

### `progress/skills-matrix.md`

You rate yourself 0–3 on each technical and strategic skill, **only with evidence**: a passing test, a saved eval result, a journal entry.

| Level | Meaning |
|---|---|
| 0 | Never done (also the level for anything without evidence) |
| 1 | Done with the solution open |
| 2 | Done alone |
| 3 | Done alone and taught or explained to someone |

No evidence, no level. If you can't link to proof, the rating stays at 0. This keeps the matrix useful as a real picture of what you can do.

### How you know a module is done

A module counts as **DONE** when:

1. All its tests pass on your code (`lab.status` shows `DONE`).
2. The "Done when" experiments are recorded in the journal with numbers.
3. You've answered the Strategy brief.

---

## 8. Costs and safety

- **All tests are offline and free.** They use `FakeLLM`.
- **Demos and eval runs call the real API.** They default to Haiku (`LAB_MODEL` in `.env`). A single eval run is around $0.05.
- **Cost is a learning target, not a side effect.** In every demo, note the tokens and cost per task. Module 00 asks you why cost grows as tasks get longer: the whole conversation is re-sent on every turn.
- **Set a spend limit** in the Claude Console before running anything.
- **Never commit `.env`.** It's git-ignored already, but check before you share your work.
- **Never give an agent a dangerous tool without an approval step** while you're learning. Modules 02 and 03 cover which tools are dangerous (cost, irreversibility, reaching outside people) and why a hard check in code beats "the system prompt says don't".

---

## 9. Troubleshooting

| Problem | What to try |
|---|---|
| `uv: command not found` after install | Open a new terminal, or add uv's install directory to your PATH. |
| `uv sync` fails on Python version | The project needs Python 3.11 or newer. `uv` normally downloads one itself; check your network and rerun. |
| Demo fails with an authentication error | Confirm `.env` exists in the repo root and contains your real key, with no quotes or extra spaces. |
| Tests fail on import in module 03 | The lab pins MCP Python SDK **2.x**. Older tutorials use `from mcp.server.fastmcp import FastMCP`; in 2.x the class is `MCPServer` in `mcp.server.mcpserver`. Run `uv sync` again. |
| Claude Desktop doesn't start your MCP server | Replace `"uv"` in the config with the full path from `which uv`, because desktop apps don't always see your shell's PATH. Also check that the repo path in the config is absolute and correct. |
| Claude Code MCP command fails | Keep the quotes around the repo path (important if it contains spaces) and use your real absolute path. |
| `lab.status` shows `todo` for a module you started | It shows `started` once any test passes and `DONE` once all pass. It always tests **your** code, not the solution. |
| Tests pass with `LAB_SOLUTION=1` but not without | That's expected until you've implemented the `TODO`s. It confirms the lab works on your machine. |

---

## 10. Reading list and strategy tools

- **`resources/reading-list.md`** maps articles and docs to modules. The rule: **build first, read second.** Read an item after the module's tests are green, so you compare someone else's approach with your own instead of absorbing it passively. Primary sources (Anthropic engineering posts, the tool-use docs, the MCP spec) come first; third-party articles are marked Keep, Skim or Skip.
- **`strategy/agent-or-not.md`** is a 10-minute screen to use before building anything real. If most answers land in the "workflow / no AI" column, build a workflow or skip AI. It also asks for four numbers to estimate (tasks per month, human minutes per task, expected cost per task, acceptable failure rate) and defines autonomy levels, with the advice to pick the lowest one that works.
- **`strategy/decision-memo-template.md`** is the template for the capstone memo: problem and value, what you built, evidence table (v1 vs v2), risks and mitigations, and the decision requested.

---

## 11. Suggested pacing

| Week | Focus |
|---|---|
| 1 | Modules 00 and 01. Get the environment working and write the loop. |
| 2 | Module 02, then module 03. |
| 3 | Module 04 (give it the most time) and module 05. |
| 4 | Modules 06 and 07: n8n architecture, then LangGraph graphs. |
| 5 | Module 08: LangGraph durable and supervised. |
| 6–8 | Capstone: choose the problem, write the evals first, build v1, build v2, write the memo. |

Short, regular sessions beat long, rare ones. Aim for 3–5 hours a week and write a journal entry at the end of every session.

---

## 12. A final piece of advice

The tests tell you whether your code works. The experiments tell you whether you understand it. The strategy briefs tell you whether you can use it to make decisions. Doing only the first is easy and teaches the least. The course is designed so that the second and third are where you become someone who can lead agent projects, not just build them.
