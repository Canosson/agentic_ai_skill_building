"""Run the eval suite against the Module 01 calculator/date agent, using the real model.

    uv run python modules/04-evals/run.py --save baseline
    uv run python modules/04-evals/run.py --system "You are terse. Never use tools." --save no-tools
    uv run python modules/04-evals/run.py --compare baseline no-tools
    uv run python modules/04-evals/run.py --trials 3 --save baseline-x3     # consistency
    uv run python modules/04-evals/run.py --model claude-sonnet-5-5 --save sonnet

Results are saved in modules/04-evals/results/<name>.json
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `lab` imports without PYTHONPATH

from lab.llm import AnthropicLLM
from lab.loop import DEFAULT_SYSTEM, run_agent
from lab.testing import load

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
ev = load(__file__, "evals")

_spec = importlib.util.spec_from_file_location("m01_demo", HERE.parent / "01-agent-loop" / "demo.py")
m01 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m01)
IMPLS = {"calculator": m01.calculator, "today": m01.today}


def make_agent(model: str | None, system: str):
    def agent_fn(question: str) -> "ev.Trial":
        llm = AnthropicLLM(model)
        r = run_agent(llm, question, m01.TOOLS, IMPLS, system=system, max_turns=6)
        return ev.Trial(output=r.final_text, tool_calls=[n for n, _ in r.tool_calls],
                        turns=r.turns, tokens=llm.usage["input_tokens"] + llm.usage["output_tokens"])
    return agent_fn


def print_report(rep, name):
    print(f"\n{'case':<16}{'pass':>6}{'trials':>8}   failed checks / notes")
    print("-" * 72)
    for r in rep.results:
        failed = [k for k, v in r.checks.items() if not v]
        note = (r.notes[-1] if r.notes else "")[:60]
        print(f"{r.case_id:<16}{'✓' if r.passed else '✗':>6}{f'{r.trials_passed}/{r.trials}':>8}   "
              f"{', '.join(failed) or ''} {note if not r.passed else ''}")
    print(f"\n[{name}] pass rate {rep.pass_rate:.0%} · mean turns {rep.mean_turns:.2f} · tokens {rep.total_tokens:,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default=DEFAULT_SYSTEM)
    ap.add_argument("--model", default=None)
    ap.add_argument("--judge-model", default=None, help="defaults to the same model")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--only", nargs="*", help="case ids to run")
    ap.add_argument("--save", metavar="NAME")
    ap.add_argument("--compare", nargs=2, metavar=("BASELINE", "CANDIDATE"))
    a = ap.parse_args()

    if a.compare:
        base, cand = (ev.Report.from_dict(json.loads((RESULTS / f"{n}.json").read_text())) for n in a.compare)
        diff = ev.compare(base, cand)
        print(json.dumps(diff, indent=2))
        print(f"\n{a.compare[0]}: {base.pass_rate:.0%}, {base.total_tokens:,} tokens   "
              f"{a.compare[1]}: {cand.pass_rate:.0%}, {cand.total_tokens:,} tokens")
        return

    cases = ev.load_cases(HERE / "cases.jsonl")
    if a.only:
        cases = [c for c in cases if c.id in a.only]
    rep = ev.run_eval(make_agent(a.model, a.system), cases,
                      judge_llm=AnthropicLLM(a.judge_model or a.model), trials=a.trials)
    print_report(rep, a.save or "run")
    if a.save:
        RESULTS.mkdir(exist_ok=True)
        out = {**rep.to_dict(), "config": {"system": a.system, "model": a.model, "trials": a.trials}}
        (RESULTS / f"{a.save}.json").write_text(json.dumps(out, indent=2))
        print(f"saved → {RESULTS / (a.save + '.json')}")


if __name__ == "__main__":
    main()
