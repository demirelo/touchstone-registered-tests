"""Every ruling in rep-launcher-notes.md quotes the plan sentence it rests on, verbatim (lesson 2026-11-19: two rulings
overrode plan text; a ruling that cannot quote the plan is a plan amendment for review, not a ruling)."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def ruling_problems(notes: str, plan: str) -> list:
    sec = notes.split("## Rulings", 1)[1].split("\n## ", 1)[0] if "## Rulings" in notes else ""
    items = re.split(r"\n(?=\d+\. )", "\n" + sec)
    out, plan_n = [], _norm(plan)
    for it in [i for i in items if re.match(r"\d+\. ", i.strip())]:
        n = it.strip().split(".", 1)[0]
        quotes = re.findall(r'Plan: "([^"]+)"', it)
        if not quotes:
            out.append(f"ruling {n}: no quoted plan text")
        out += [f"ruling {n}: quote not in the plan: {q[:60]}" for q in quotes if _norm(q) not in plan_n]
    if not items or not any(re.match(r"\d+\. ", i.strip()) for i in items):
        out.append("no rulings section")
    return out


def test_every_ruling_quotes_the_plan():
    probs = ruling_problems((HERE / "rep-launcher-notes.md").read_text(), (HERE / "replication-plan.md").read_text())
    assert not probs, probs


def test_the_check_fails_on_a_ruling_without_a_quote_or_with_a_wrong_one():
    plan = "The gate is the first p = 0.05 cell."
    assert ruling_problems("## Rulings\n\n1. **x** no quote.\n", plan) == ["ruling 1: no quoted plan text"]
    assert ruling_problems('## Rulings\n\n1. **x** Plan: "the first flagged cell"\n', plan)[0].startswith("ruling 1: quote not in the plan")
    assert ruling_problems('## Rulings\n\n1. **x** Plan: "first p = 0.05\n   cell"\n', plan) == []
