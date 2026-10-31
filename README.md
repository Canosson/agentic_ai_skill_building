<h1 align="center">Agentic Skill Builder</h1>

<p align="center">
  <a href="docs/media/teaser.mp4" title="Watch the 24-second teaser (MP4)">
    <img src="docs/media/teaser.gif" alt="Animated teaser: Stop reading about agents. Build them. Ten modules, then Build, Break, Measure. Tests run offline for $0, modules 00 to 08 cost a few dollars, and the capstone takes 2 to 3 weeks." width="800">
  </a>
</p>

<p align="center">
  <b>Stop reading about agents. Build them.</b><br>
  10 modules · offline tests · a few dollars total · one capstone you can defend
</p>

<p align="center">
  <a href="docs/media/teaser.mp4">▶ Teaser (24 s)</a> ·
  <a href="docs/media/onboarding.mp4">▶ Welcome &amp; onboarding (24 s)</a> ·
  <a href="PROGRAM_GUIDE.md">Program guide</a> ·
  <a href="modules/00-setup/README.md">Start module 00</a>
</p>

---

A build-first training environment for agentic AI. You won't read about agents here. You'll build the parts every agent framework is made of, test them, break them on purpose, and measure them, then make decisions about them like a technical lead.

> Origin: this started from [Canosson/Agentic-AI](https://github.com/Canosson/Agentic-AI), a ProjectPro link list. Its useful links are triaged and mapped to modules in [`resources/reading-list.md`](resources/reading-list.md). Everything else here is new.

## Quick start

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # once
uv sync                                             # installs Python deps
cp .env.example .env                                # add your Anthropic API key
uv run python -m lab.status                         # your progress board
```

Then open [`modules/00-setup/README.md`](modules/00-setup/README.md). For the full walkthrough (goal, how to run each module, tutoring, troubleshooting), read [`PROGRAM_GUIDE.md`](PROGRAM_GUIDE.md).

## The path

| # | Module | You build | Time |
|---|---|---|---|
| 00 | [Setup](modules/00-setup) | One real model call, with its cost | 30 min |
| 01 | [Agent loop](modules/01-agent-loop) | The loop that every framework wraps | 2–4 h |
| 02 | [Tools and context](modules/02-tools-and-context) | Schema generation, a defensive tool registry, context trimming | 3–5 h |
| 03 | [MCP](modules/03-mcp) | Your own MCP server, used from your loop **and** from Claude Desktop/Code | 3–4 h |
| 04 | [Evals](modules/04-evals) | An eval harness with judges, trials and regression detection | 4–6 h |
| 05 | [Orchestration](modules/05-orchestration) | Chain, router, orchestrator-workers, evaluator-optimizer | 3–5 h |
| 06 | [n8n: orchestration architecture](modules/06-n8n-orchestration) | A workflow linter and a ticket-router design: where intelligence belongs, and what each path costs | 3–4 h |
| 07 | [LangGraph: state graphs](modules/07-langgraph-graphs) | The Module 05 patterns rebuilt as graphs: state, conditional edges, fan-out, cycles | 3–5 h |
| 08 | [LangGraph: durable and supervised](modules/08-langgraph-durable) | Human approval, crash recovery and run traces with checkpointing | 3–4 h |
| 09 | [Capstone](modules/09-capstone) | A real agent for your work, a framework bake-off, a decision memo | 2–3 wks |

Each module has the same structure:

- `README.md`: the concept, what to build, a **Done when** checklist, and a **Strategy brief**
- starter files with numbered `TODO(NN-x)`s
- `test_*.py`: offline tests that run against a scripted `FakeLLM`, so they're free and deterministic and need no API key
- `demo.py`: your code against the real model
- `solution/`: a reference. Look only after your tests are green.

```bash
uv run pytest modules/01-agent-loop -x                  # test YOUR code
LAB_SOLUTION=1 uv run pytest modules/01-agent-loop      # test the reference solution
```

## Two tracks, every module

- **Technical:** make the tests pass, then run the experiments in "Done when". The experiments are where the learning happens.
- **Strategic:** answer the strategy brief in [`progress/journal.md`](progress/journal.md). Use [`strategy/agent-or-not.md`](strategy/agent-or-not.md) before building anything real, and [`strategy/decision-memo-template.md`](strategy/decision-memo-template.md) for the capstone.

Track progress honestly in [`progress/skills-matrix.md`](progress/skills-matrix.md): no evidence, no level.

## Cost

All tests are offline. Demos and eval runs default to Haiku (`LAB_MODEL` in `.env`). Modules 00–08 together should cost a few dollars at most. Set a spend limit in the Claude Console anyway.

## Using Claude as your tutor

`CLAUDE.md` tells Claude (in Cowork or Claude Code, opened on this folder) to coach rather than solve: it asks questions, reviews your code against the tests, and updates your skills matrix. Ask it to "review my 01" or "quiz me on module 02".

## Layout

```
lab/            shared code: llm.py (model seam + FakeLLM), loop.py (reference loop, spoiler),
                testing.py, status.py
modules/        00–09, the curriculum
strategy/       decision tools for the strategic track
resources/      triaged reading list
progress/       journal + skills matrix (yours to fill in)
```

## License

The code and course material are released under the [MIT License](LICENSE).

## Credits

Music in the teaser and onboarding videos: "Happy Beats / Business Moves" (Vol. 12) by Sascha Ende, [ende.app](https://ende.app/en), licensed under [CC BY 4.0](https://ende.app/en/standard-license). Music: Sascha Ende, ende.app (CC BY 4.0). The track is not covered by the MIT License.
